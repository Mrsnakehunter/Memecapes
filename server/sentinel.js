'use strict';
// Sentinel: the always-on guard of the MemeCapes server. It runs inside the server, sees every request and connection, and
// acts on its own, at once, without waiting for a person:
//   - knows each visitor's real address (Render adds the real one to X-Forwarded-For; whatever a visitor writes there
//     themselves is ignored), and counts what each address does
//   - slows down and then blocks addresses that flood the server, guess passwords or admin keys, or probe for hacker paths
//     (/.env, /wp-admin, /.git ...): blocks start at 10 minutes and grow up to a day for repeat offenders
//   - locks an account name for 15 minutes after 8 wrong passwords, whoever tries them (stops guessing from many addresses)
//   - three modes, switched by an admin (/guard in game) or by Sentinel itself when it sees an attack:
//       normal    everything on
//       shield    new accounts, uploads, launches, posts and website ads paused; play, chat, saves and payments still work
//       lockdown  shield + new sign-ins paused; only players already in the game keep playing
//     Payments that already happened on the blockchain are always checked and counted, in every mode, so nobody loses money.
//   - watches the disk (uploads stop before the disk fills and takes the game down) and the fee wallet addresses (an alarm if
//     the address in config.js ever changes, or differs from the one set on Render)
//   - writes every event to the guard log and tells admins: in game, and on Discord/Telegram if a webhook is set on Render
//     (GUARD_WEBHOOK = a Discord or Slack webhook URL; GUARD_TG_TOKEN + GUARD_TG_CHAT = a Telegram bot and chat)
// It never reads passwords, keys or wallets' secrets, and never sends a transaction.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

module.exports = function sentinel({ db, DATA, now }) {
  // proxies append to X-Forwarded-For after the visitor's own entry. By default the visitor is the right-most address that is
  // not a private/internal one (the proxies' own hops are internal); PROXY_HOPS on Render fixes the count instead.
  const HOPS = process.env.PROXY_HOPS != null && process.env.PROXY_HOPS !== '' ? +process.env.PROXY_HOPS : -1;
  // Render sits behind Cloudflare: its edge addresses are proxies too, never the visitor (www.cloudflare.com/ips)
  const CF4 = ['173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22', '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
    '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13', '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22'].map(c => { const [a, n] = c.split('/'); return [v4(a), +n]; });
  const CF6 = ['2400:cb00:', '2606:4700:', '2803:f800:', '2405:b500:', '2405:8100:', '2a06:98c', '2a06:98d', '2a06:98e', '2a06:98f', '2c0f:f248:'];
  function v4(a) { const p = String(a).split('.'); return p.length === 4 && p.every(x => /^\d{1,3}$/.test(x)) ? ((+p[0] << 24) >>> 0) + (+p[1] << 16) + (+p[2] << 8) + +p[3] : -1; }
  function isCF(ip) {
    if (ip.includes(':')) return CF6.some(p => ip.toLowerCase().startsWith(p));
    const x = v4(ip); if (x < 0) return false;
    return CF4.some(([a, n]) => n === 0 || (x >>> (32 - n)) === (a >>> (32 - n)));
  }
  const PRIVATE = /^(10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.|::1$|f[cd][0-9a-f]{2}:|fe80:)/i;
  db.exec(`CREATE TABLE IF NOT EXISTS guard_events(id INTEGER PRIMARY KEY, t INT, kind TEXT, ip TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS guard_state(k TEXT PRIMARY KEY, v TEXT);`);
  const Q = {
    ev: db.prepare('INSERT INTO guard_events(t,kind,ip,detail) VALUES(?,?,?,?)'),
    evTrim: db.prepare('DELETE FROM guard_events WHERE id < (SELECT MAX(id) FROM guard_events) - 5000'),
    evList: db.prepare('SELECT t,kind,ip,detail FROM guard_events ORDER BY id DESC LIMIT ?'),
    get: db.prepare('SELECT v FROM guard_state WHERE k=?'),
    set: db.prepare('INSERT INTO guard_state(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v'),
  };
  const sget = (k, d) => { const r = Q.get.get(k); return r ? r.v : d; };
  const sset = (k, v) => Q.set.run(k, String(v));

  // ---------- the visitor's real address ----------
  function ipOf(req) {
    const L = String(req.headers['x-forwarded-for'] || '').split(',').map(s => s.trim()).filter(Boolean);
    const sock = (req.socket && req.socket.remoteAddress) || '';
    if (!L.length) return sock.replace(/^::ffff:/, '');
    const C = L.map(x => x.replace(/^::ffff:/, ''));
    if (HOPS >= 0) return C[Math.max(0, C.length - 1 - HOPS)];
    for (let i = C.length - 1; i >= 0; i--) if (!PRIVATE.test(C[i]) && !isCF(C[i])) return C[i];
    return C[0];
  }

  // ---------- alerts ----------
  let tellAdmins = () => { };
  const lastAlert = new Map();
  function alert(key, text, every = 10 * 60e3) {
    if (now() - (lastAlert.get(key) || 0) < every) return;
    lastAlert.set(key, now());
    console.log('[sentinel] ' + text);
    try { tellAdmins('[Sentinel] ' + text); } catch (e) { }
    const wh = process.env.GUARD_WEBHOOK, tg = process.env.GUARD_TG_TOKEN, chat = process.env.GUARD_TG_CHAT, msg = 'MemeCapes Sentinel: ' + text;
    if (wh) fetch(wh, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: msg, text: msg }), signal: AbortSignal.timeout(8000) }).catch(() => { });
    if (tg && chat) fetch('https://api.telegram.org/bot' + tg + '/sendMessage', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chat, text: msg }), signal: AbortSignal.timeout(8000) }).catch(() => { });
  }
  function log(kind, ip, detail) { try { Q.ev.run(now(), kind, ip || '', String(detail || '').slice(0, 300)); if (Math.random() < .02) Q.evTrim.run(); } catch (e) { } }

  // ---------- modes ----------
  const MODES = ['normal', 'shield', 'lockdown'];
  let mode = MODES.includes(sget('mode')) ? sget('mode') : 'normal', modeBy = sget('modeBy', ''), autoUntil = +sget('autoUntil', 0);
  function setMode(m, by, mins) {
    if (!MODES.includes(m)) return false;
    const was = mode; mode = m; modeBy = by; autoUntil = mins ? now() + mins * 60e3 : 0;
    sset('mode', m); sset('modeBy', by); sset('autoUntil', autoUntil);
    log('mode', '', was + ' -> ' + m + ' by ' + by);
    if (was !== m) alert('mode', 'Mode is now ' + m.toUpperCase() + ' (' + by + ').' + (m === 'normal' ? '' : ' ' + DESC[m]), 0);
    return true;
  }
  const DESC = { normal: 'Everything is on.', shield: 'New accounts, uploads, launches, posts and website ads are paused. Play, chat, saves and payments still work.',
    lockdown: 'Shield, plus no new sign-ins: only players already in the game keep playing.' };
  // what each mode allows. Payments already sent on-chain ('pay') are always allowed.
  function allow(kind) {
    if (kind === 'pay') return true;
    if (kind === 'upload' && diskLow) return false;
    if (mode === 'normal') return true;
    if (['register', 'upload', 'launch', 'post', 'ad', 'profile', 'golive'].includes(kind)) return false;
    if (mode === 'lockdown' && ['login', 'wallet-login'].includes(kind)) return false;
    return true;
  }
  const pausedMsg = () => mode === 'lockdown' ? 'MemeCapes is in lockdown for a short while to keep everyone safe. Please try again later.'
    : 'This is paused for a short while to keep everyone safe. Please try again later.';

  // ---------- per-address counting, slowing and blocking ----------
  const A = new Map();   // ip -> {get, post, gt, pt, strikes:[t], conns, blockedUntil, blocks, why}
  const rec = (ip) => { let r = A.get(ip); if (!r) { r = { get: 120, post: 20, gt: now(), pt: now(), strikes: [], conns: 0, blockedUntil: 0, blocks: 0, why: '' }; A.set(ip, r); } return r; };
  const ALLOW = new Set(String(process.env.GUARD_ALLOW || '').split(',').map(s => s.trim()).filter(Boolean));
  function blocked(ip) { const r = A.get(ip); return !!(r && r.blockedUntil > now() && !ALLOW.has(ip)); }
  let blocksRecent = [];
  function block(ip, why, mins) {
    if (!ip || ALLOW.has(ip)) return;
    const r = rec(ip); r.blocks++;
    const m = mins || Math.min(24 * 60, 10 * Math.pow(6, r.blocks - 1));   // 10 min, 1 h, 6 h, then a day
    r.blockedUntil = now() + m * 60e3; r.why = why; r.strikes = [];
    log('block', ip, why + ' (' + m + ' min)');
    blocksRecent.push(now()); blocksRecent = blocksRecent.filter(t => now() - t < 10 * 60e3);
    if (blocksRecent.length >= 25 && mode === 'normal') { setMode('shield', 'Sentinel: ' + blocksRecent.length + ' addresses blocked in 10 minutes', 30); }
    else alert('block:' + why.split(' ')[0], 'Blocked ' + ip + ' for ' + m + ' min: ' + why + '.', 5 * 60e3);
  }
  function strike(ip, why, weight = 1) {
    if (!ip || ALLOW.has(ip)) return;
    const r = rec(ip); for (let i = 0; i < weight; i++) r.strikes.push(now());
    r.strikes = r.strikes.filter(t => now() - t < 5 * 60e3);
    if (r.strikes.length >= 30) block(ip, why);
  }
  // hacker probes: paths no MemeCapes page ever asks for
  const TRAP = /(^|\/)(\.env|\.git|\.aws|\.ssh|\.htaccess|\.DS_Store|wp-admin|wp-login|wp-content|wp-includes|xmlrpc\.php|phpmyadmin|pma|cgi-bin|actuator|server-status|vendor\/phpunit|boaform|HNAP1|owa|autodiscover|config\.json|backup\.(zip|sql|tar)|db\.sql|\.php)(\/|$|\?)/i;
  // every HTTP request comes here first. Returns false (and answers) when the request is refused.
  function http(req, res) {
    const ip = ipOf(req); req.ip = ip;
    if (blocked(ip)) { res.writeHead(403, { 'Content-Type': 'text/plain' }); res.end('Blocked for a while. If this is a mistake, wait and try again.'); return false; }
    if (TRAP.test(req.url || '')) { block(ip, 'probed ' + String(req.url).slice(0, 60), 60); res.writeHead(404); res.end(); return false; }
    const r = rec(ip), t = now();
    if (req.method === 'POST') { r.post = Math.min(20, r.post + (t - r.pt) / 1000 * 1); r.pt = t; if (--r.post < 0) { strike(ip, 'too many requests (POST)', 2); res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Retry-After': '10' }); res.end('{"error":"Slow down a little."}'); return false; } }
    else { r.get = Math.min(120, r.get + (t - r.gt) / 1000 * 20); r.gt = t; if (--r.get < 0) { strike(ip, 'too many requests'); res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Retry-After': '5' }); res.end('{"error":"Slow down a little."}'); return false; } }
    return true;
  }
  // security headers on every answer from the server
  function headers(res) {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    res.setHeader('Cross-Origin-Resource-Policy', 'cross-origin');
    res.setHeader('Content-Security-Policy', "default-src 'none'; img-src 'self'; frame-ancestors 'none'");
  }
  // WebSocket connections: at most WS_PER_IP at once from one address
  const WS_PER_IP = +process.env.GUARD_WS_PER_IP || 8;
  function wsOpen(req) {
    const ip = ipOf(req);
    if (blocked(ip)) return null;
    const r = rec(ip); if (r.conns >= WS_PER_IP) { strike(ip, 'too many connections', 3); return null; }
    r.conns++; return ip;
  }
  function wsClose(ip) { const r = A.get(ip); if (r && r.conns > 0) r.conns--; }

  // ---------- password guessing ----------
  const fails = new Map();   // name -> [t]
  function loginLocked(name) { const L = (fails.get(String(name).toLowerCase()) || []).filter(t => now() - t < 15 * 60e3); return L.length >= 8; }
  function loginFail(name, ip) {
    const k = String(name).toLowerCase(), L = (fails.get(k) || []).filter(t => now() - t < 15 * 60e3); L.push(now()); fails.set(k, L);
    strike(ip, 'wrong passwords', 3);
    if (L.length === 8) { log('lock', ip, 'account ' + k + ' locked 15 min after 8 wrong passwords'); alert('lock:' + k, 'Someone is guessing the password of "' + k + '". The name is locked for 15 minutes.'); }
    if (fails.size > 20000) fails.clear();
  }
  function loginOk(name) { fails.delete(String(name).toLowerCase()); }
  // the admin key: compared in constant time; a wrong key is a heavy strike (5 wrong = blocked)
  function adminKeyOk(req, key) {
    const got = Buffer.from(String(req.headers.authorization || '')), want = Buffer.from('Bearer ' + key);
    const ok = !!key && got.length === want.length && crypto.timingSafeEqual(got, want);
    if (!ok) { const ip = ipOf(req); log('admin-key', ip, 'wrong admin key on ' + String(req.url).slice(0, 40)); strike(ip, 'wrong admin key', 6); alert('adminkey', 'Wrong admin key tried from ' + ip + '.', 30 * 60e3); }
    return ok;
  }

  // ---------- disk and fee wallet watch ----------
  let diskLow = false, diskPct = 100;
  function diskCheck() {
    try {
      const s = fs.statfsSync(DATA); diskPct = Math.round(s.bavail / s.blocks * 1000) / 10;
      const low = diskPct < 12;
      if (low && !diskLow) { log('disk', '', diskPct + '% free'); alert('disk', 'The server disk is almost full (' + diskPct + '% free). Uploads are paused until there is room.', 0); }
      if (!low && diskLow) log('disk', '', 'ok again: ' + diskPct + '% free');
      diskLow = low;
    } catch (e) { }
  }
  function walletWatch() {
    try {
      const cfg = fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8');
      const addr = k => { const m = new RegExp(k + ':\\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"').exec(cfg); return m ? m[1] : ''; };
      const cur = JSON.stringify({ partner: addr('partner'), partnerDevnet: addr('partnerDevnet'), streamPassWallet: addr('streamPassWallet') });
      const was = sget('wallets', '');
      if (was && was !== cur) { log('wallets', '', 'config.js wallets changed: ' + was + ' -> ' + cur); alert('wallets', 'The wallet addresses in config.js CHANGED: was ' + was + ', now ' + cur + '. If you did not change them, go to lockdown (/guard lockdown) and check GitHub now.', 0); }
      sset('wallets', cur);
      const env = process.env.LP_PARTNER, p = addr('partner');
      if (env && p && env !== p) alert('wallets-env', 'The fee wallet on Render (LP_PARTNER) and the one in config.js are different. The server uses Render\'s. Check which is right.', 6 * 3600e3);
    } catch (e) { }
  }
  diskCheck(); walletWatch();
  setInterval(() => {
    diskCheck();
    if (autoUntil && now() > autoUntil && mode !== 'normal' && /^Sentinel/.test(modeBy)) setMode('normal', 'Sentinel: the attack stopped', 0);
    for (const [ip, r] of A) if (r.blockedUntil < now() && !r.conns && !r.strikes.length && now() - Math.max(r.gt, r.pt) > 30 * 60e3) A.delete(ip);
  }, 60e3);

  // ---------- status, and the /guard command for admins in game ----------
  function status() {
    const bl = [...A.entries()].filter(([, r]) => r.blockedUntil > now()).map(([ip, r]) => ({ ip, until: r.blockedUntil, why: r.why }));
    return { mode, modeBy, autoUntil, about: DESC[mode], diskFreePct: diskPct, diskLow, blocked: bl, tracked: A.size, lockedNames: [...fails.entries()].filter(([k]) => loginLocked(k)).map(([k]) => k), events: Q.evList.all(40) };
  }
  function cmd(say, c, arg, rest) {
    const a = String(arg || 'status');
    if (MODES.includes(a)) { setMode(a, 'admin ' + c.name, 0); return say(c, 'Mode: ' + a.toUpperCase() + '. ' + DESC[a], '#0a0'); }
    if (a === 'block') { const ip = String(rest || '').trim(); if (!ip) return say(c, 'Usage: /guard block <ip>', '#a60'); block(ip, 'blocked by admin ' + c.name, 24 * 60); return say(c, ip + ' blocked for a day.', '#0a0'); }
    if (a === 'unblock') { const ip = String(rest || '').trim(); const r = A.get(ip); if (r) { r.blockedUntil = 0; r.strikes = []; r.blocks = 0; } log('unblock', ip, 'by admin ' + c.name); return say(c, ip + ' unblocked.', '#0a0'); }
    if (a === 'log') { const L = Q.evList.all(12); return say(c, L.length ? L.map(e => new Date(e.t).toISOString().slice(5, 16).replace('T', ' ') + ' ' + e.kind + ' ' + (e.ip || '') + ' ' + e.detail).join(' | ') : 'Nothing in the guard log yet.', '#a60'); }
    const s = status();
    say(c, 'Sentinel: mode ' + s.mode.toUpperCase() + (s.modeBy ? ' (' + s.modeBy + ')' : '') + '. Blocked now: ' + s.blocked.length + '. Disk free: ' + s.diskFreePct + '%. Locked names: ' + (s.lockedNames.join(', ') || 'none') + '. Commands: /guard normal|shield|lockdown|log|block <ip>|unblock <ip>', '#a60');
  }
  return { ipOf, http, headers, wsOpen, wsClose, allow, pausedMsg, loginLocked, loginFail, loginOk, adminKeyOk, strike, block, blocked, status, cmd, log, alert,
    setMode, mode: () => mode, setTellAdmins: f => { tellAdmins = f; } };
};
