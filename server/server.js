'use strict';
// MemeCapes game server: accounts, cloud saves, live players, chat, player trades.
// No packages to install: plain Node.js 22+ (built-in SQLite, built-in crypto, a small WebSocket layer below).
// Run:  node server.js        Settings come from environment variables (see README.md in this folder).

const http = require('http');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
process.removeAllListeners('warning'); // hide the "SQLite is experimental" notice
const { DatabaseSync } = require('node:sqlite');

const PORT = +process.env.PORT || 8080;
const DATA = process.env.DATA_DIR || path.join(__dirname, 'data');
const ADMIN_KEY = process.env.ADMIN_KEY || '';
const ADMINS = (process.env.ADMIN_NAMES || '').toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
const ORIGINS = (process.env.ALLOWED_ORIGINS || 'https://memecapes.com,https://www.memecapes.com,http://localhost:8000,http://127.0.0.1:8000').split(',').map(s => s.trim());
const MAX_SAVE = 900 * 1024;          // bytes of save JSON
const MAX_FRAME = 1024 * 1024;        // biggest WebSocket message accepted
const VIEW = 48;                      // tiles: you see players this close
const BAG = 35;
const TRADE_LOCK_MS = +(process.env.TRADE_LOCK_MS || 2500);   // no accepting for this long after the OTHER player changes their offer                       // bag slots (the coin stack takes one)
// holder perks: hold at least HOLDER_PCT % of all $CAPES in a wallet you own = free Cape Club, and one free shop skin every HOLDER_DAYS days
const CAPES_MINT = process.env.CAPES_MINT || '';                 // empty = holder perks switched off
const RPC = process.env.SOLANA_RPC || 'https://api.mainnet-beta.solana.com';
const HOLD_PCT = +process.env.HOLDER_PCT || 1;
const HOLD_DAYS = +process.env.HOLDER_DAYS || 14;
// partners: hold at least PARTNER_PCT % for PARTNER_DAYS days = a free billboard and NPC in every town, and their own cape colour,
// for as long as they keep it. The ad shows only after an admin approves it, and comes down at the first check below PARTNER_PCT %.
const PARTNER_PCT = +process.env.PARTNER_PCT || 3;
const PARTNER_DAYS = +process.env.PARTNER_DAYS || 14;
const PARTNER_CHECK = +process.env.PARTNER_CHECK_MS || 15 * 60e3;   // how often partners' wallets are checked
const SWEEP = +process.env.SWEEP_MS || 60e3;
// burn ads: burn at least BURN_PCT % of all $CAPES (after the ad is approved) = an ad on memecapes.com for BURN_AD_DAYS days (0 = for good)
const BURN_PCT = +process.env.BURN_PCT || 1;
const BURN_AD_DAYS = process.env.BURN_AD_DAYS != null ? +process.env.BURN_AD_DAYS : 0;
const SKIN_IDS = ['sk_laser', 'sk_upaxe', 'sk_dpick', 'sk_rocket', 'sk_rug', 'sk_moon',
  'cs_green_candles', 'cs_red_candles', 'cs_laser_eyes', 'cs_diamond_hands', 'cs_moon_night', 'cs_coin_gold',
  'cs_pond_lily', 'cs_wow_plaid', 'cs_stonks_arrow', 'cs_bonk_stripes', 'cs_rug_fringe', 'cs_hodl_frost', 'cs_moon_phases', 'cs_chad_marble', 'cs_laser_grid', 'cs_shades_on', 'cs_whale_waves', 'cs_rocket_trail', 'cs_the_burn', 'cs_copium_crystal', 'cs_wen_lambo', 'cs_jungle_leaves', 'cs_up_only_rainbow', 'cs_comfy_knit', 'cs_royal_ermine'];  // same list as tools/patch_skins.py
// Skin of the Month: a wallet holding at least SOTM_PCT % of all $CAPES for SOTM_DAYS days gets that month's skin free,
// one per account per month. Month 1 of the line-up is SOTM_START (UTC). Same line-up as tools/patch_sotm.py.
const SOTM_PCT = +process.env.SOTM_PCT || 0.1;
const SOTM_DAYS = +process.env.SOTM_DAYS || 30;
const SOTM_START = process.env.SOTM_START || '2026-11';
const SOTM = ['cs_laser_grid', 'sk_candle', 'cs_pond_lily', 'cs_stonks_arrow', 'sk_banhammer', 'cs_moon_phases', 'cs_wow_plaid', 'sk_copium',
  'cs_whale_waves', 'cs_shades_on', 'sk_chonkaxe', 'cs_royal_ermine', 'cs_the_burn', 'sk_oracle', 'cs_rug_fringe', 'cs_hodl_frost', 'sk_frostfang',
  'cs_jungle_leaves', 'cs_rocket_trail', 'sk_sweeper', 'cs_wen_lambo', 'cs_chad_marble', 'sk_gascleaver', 'cs_up_only_rainbow', 'cs_bonk_stripes',
  'sk_goldrush', 'cs_copium_crystal', 'cs_comfy_knit', 'sk_bubble', 'sk_wrench'];
function sotmNow(t) {
  const d = new Date(t || now()), [y, m] = SOTM_START.split('-').map(Number), i = (d.getUTCFullYear() - y) * 12 + d.getUTCMonth() - (m - 1);
  const id = i >= 0 && i < SOTM.length ? SOTM[i] : '';
  return { n: i + 1, key: d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0'), skin: SKIN_IDS.includes(id) ? id : '' };  // a skin not made yet = none this month
}

fs.mkdirSync(path.join(DATA, 'backups'), { recursive: true });
const db = new DatabaseSync(path.join(DATA, 'memecapes.db'));
db.exec(`PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE COLLATE NOCASE, salt TEXT, hash TEXT, created INT, last INT,
  role TEXT DEFAULT '', banned INT DEFAULT 0, muted_until INT DEFAULT 0, save TEXT, rev INT DEFAULT 0, save_t INT DEFAULT 0, prev TEXT, iron INT DEFAULT 0, ip TEXT);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, uid INT, created INT, last INT);
CREATE TABLE IF NOT EXISTS flags(id INTEGER PRIMARY KEY, uid INT, t INT, kind TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, uid INT, target TEXT, t INT, why TEXT, chat TEXT);
CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY, t INT, a INT, b INT, a_gave TEXT, b_gave TEXT);
CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, t INT, uid INT, name TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS wallets(uid INTEGER PRIMARY KEY, wallet TEXT UNIQUE, linked INT, since INT DEFAULT 0, checked INT DEFAULT 0, due INT DEFAULT 0,
  ok INT DEFAULT 0, pct REAL DEFAULT 0, claimed INT DEFAULT 0, claims INT DEFAULT 0, err TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS partners(uid INTEGER PRIMARY KEY, brand TEXT, line TEXT, link TEXT, color TEXT, g INT DEFAULT 0, img TEXT,
  status TEXT DEFAULT 'pending', note TEXT DEFAULT '', updated INT, approved INT DEFAULT 0);`);
try { db.exec('ALTER TABLE wallets ADD COLUMN since3 INT DEFAULT 0'); } catch (e) { }
try { db.exec('ALTER TABLE wallets ADD COLUMN sinceM INT DEFAULT 0'); } catch (e) { }  // when the wallet last reached SOTM_PCT %
db.exec('CREATE TABLE IF NOT EXISTS sotm(uid INT, month TEXT, skin TEXT, t INT, PRIMARY KEY(uid, month))');  // Skin of the Month claims (per account, kept after unlinking)
db.exec(`CREATE TABLE IF NOT EXISTS burnads(id INTEGER PRIMARY KEY, wallet TEXT, brand TEXT, line TEXT, link TEXT, img TEXT, status TEXT DEFAULT 'pending',
  note TEXT DEFAULT '', created INT, approved INT DEFAULT 0, burn_sig TEXT UNIQUE, burned TEXT DEFAULT '', live_at INT DEFAULT 0, ends INT DEFAULT 0);`);
try { db.exec('ALTER TABLE burnads ADD COLUMN shares INT DEFAULT 1'); } catch (e) { }  // how many whole BURN_PCT %s were burned = share of the ad spot  // when the wallet last reached PARTNER_PCT %
const Q = {
  byName: db.prepare('SELECT * FROM users WHERE name=?'),
  byId: db.prepare('SELECT * FROM users WHERE id=?'),
  add: db.prepare('INSERT INTO users(name,salt,hash,created,last,iron,ip) VALUES(?,?,?,?,?,?,?)'),
  seen: db.prepare('UPDATE users SET last=?, ip=? WHERE id=?'),
  save: db.prepare('UPDATE users SET prev=save, save=?, rev=rev+1, save_t=? WHERE id=? AND rev=?'),
  setSave: db.prepare('UPDATE users SET save=?, rev=?, save_t=? WHERE id=?'),
  rollback: db.prepare('UPDATE users SET save=prev, rev=rev+1 WHERE id=? AND prev IS NOT NULL'),
  setRole: db.prepare('UPDATE users SET role=? WHERE id=?'),
  ban: db.prepare('UPDATE users SET banned=? WHERE id=?'),
  mute: db.prepare('UPDATE users SET muted_until=? WHERE id=?'),
  del: db.prepare('DELETE FROM users WHERE id=?'),
  sesAdd: db.prepare('INSERT INTO sessions(token,uid,created,last) VALUES(?,?,?,?)'),
  ses: db.prepare('SELECT * FROM sessions WHERE token=?'),
  sesSeen: db.prepare('UPDATE sessions SET last=? WHERE token=?'),
  sesDel: db.prepare('DELETE FROM sessions WHERE token=?'),
  sesDelUser: db.prepare('DELETE FROM sessions WHERE uid=?'),
  sesOld: db.prepare('DELETE FROM sessions WHERE last<?'),
  flag: db.prepare('INSERT INTO flags(uid,t,kind,detail) VALUES(?,?,?,?)'),
  report: db.prepare('INSERT INTO reports(uid,target,t,why,chat) VALUES(?,?,?,?,?)'),
  trade: db.prepare('INSERT INTO trades(t,a,b,a_gave,b_gave) VALUES(?,?,?,?,?)'),
  chat: db.prepare('INSERT INTO chat(t,uid,name,text) VALUES(?,?,?,?)'),
  chatTrim: db.prepare('DELETE FROM chat WHERE id < (SELECT MAX(id) FROM chat) - 5000'),
  recentChat: db.prepare('SELECT name,text,t FROM chat ORDER BY id DESC LIMIT 20'),
  count: db.prepare('SELECT COUNT(*) n FROM users'),
  listFlags: db.prepare('SELECT f.t,u.name,f.kind,f.detail FROM flags f JOIN users u ON u.id=f.uid ORDER BY f.id DESC LIMIT 200'),
  listReports: db.prepare('SELECT r.t,u.name reporter,r.target,r.why,r.chat FROM reports r JOIN users u ON u.id=r.uid ORDER BY r.id DESC LIMIT 200'),
  wal: db.prepare('SELECT * FROM wallets WHERE uid=?'),
  walBy: db.prepare('SELECT * FROM wallets WHERE wallet=?'),
  walSet: db.prepare('INSERT OR REPLACE INTO wallets(uid,wallet,linked,since,checked,due,ok,pct,claimed,claims,err) VALUES(?,?,?,0,0,0,0,0,?,?,\'\')'),
  walDel: db.prepare('DELETE FROM wallets WHERE uid=?'),
  walCheck: db.prepare('UPDATE wallets SET since=?, since3=?, sinceM=?, checked=?, due=?, ok=?, pct=?, err=? WHERE uid=?'),
  sotmGet: db.prepare('SELECT * FROM sotm WHERE uid=? AND month=?'),
  sotmAdd: db.prepare('INSERT INTO sotm(uid,month,skin,t) VALUES(?,?,?,?)'),
  ptGet: db.prepare('SELECT * FROM partners WHERE uid=?'),
  ptSet: db.prepare(`INSERT INTO partners(uid,brand,line,link,color,g,img,status,note,updated) VALUES(?,?,?,?,?,?,?,'pending','',?)
    ON CONFLICT(uid) DO UPDATE SET brand=excluded.brand,line=excluded.line,link=excluded.link,color=excluded.color,g=excluded.g,img=excluded.img,status='pending',note='',updated=excluded.updated`),
  ptStatus: db.prepare('UPDATE partners SET status=?, note=?, approved=? WHERE uid=?'),
  ptDel: db.prepare('DELETE FROM partners WHERE uid=?'),
  baAdd: db.prepare('INSERT INTO burnads(wallet,brand,line,link,img,status,created) VALUES(?,?,?,?,?,\'pending\',?)'),
  baGet: db.prepare('SELECT * FROM burnads WHERE id=?'),
  baByWallet: db.prepare('SELECT id,brand,line,link,status,note,created,burned,live_at,ends,shares FROM burnads WHERE wallet=? ORDER BY id DESC LIMIT 10'),
  baOpen: db.prepare("SELECT COUNT(*) n FROM burnads WHERE wallet=? AND status IN ('pending','approved')"),
  baStatus: db.prepare('UPDATE burnads SET status=?, note=?, approved=? WHERE id=?'),
  baLive: db.prepare("UPDATE burnads SET status='live', burn_sig=?, burned=?, live_at=?, ends=?, shares=? WHERE id=? AND status='approved'"),
  baBySig: db.prepare('SELECT id FROM burnads WHERE burn_sig=?'),
  baDel: db.prepare('DELETE FROM burnads WHERE id=?'),
  baAll: db.prepare('SELECT id,wallet,brand,line,link,status,note,created,burned,live_at,ends FROM burnads ORDER BY id DESC LIMIT 200'),
  baShow: db.prepare("SELECT id,brand,line,link,live_at,shares FROM burnads WHERE status='live' AND (ends=0 OR ends>?) ORDER BY live_at"),
  ptAll: db.prepare('SELECT p.uid,p.brand,p.line,p.link,p.color,p.g,p.status,p.note,p.updated,u.name,w.pct,w.since3 FROM partners p JOIN users u ON u.id=p.uid LEFT JOIN wallets w ON w.uid=p.uid ORDER BY p.uid'),
  walErr: db.prepare('UPDATE wallets SET due=?, err=? WHERE uid=?'),
  walClaim: db.prepare('UPDATE wallets SET claimed=?, claims=claims+1 WHERE uid=?'),
  walDue: db.prepare('SELECT * FROM wallets WHERE due<? ORDER BY due LIMIT 20'),
  walList: db.prepare('SELECT u.name,w.wallet,w.ok,w.pct,w.since,w.checked,w.claims,w.err FROM wallets w JOIN users u ON u.id=w.uid ORDER BY w.pct DESC'),
};
const now = () => Date.now();
// ---------- Sentinel (server/sentinel.js): the always-on guard: real addresses, flood and guess blocking, modes, alerts ----------
const G = require('./sentinel')({ db, DATA, now });

// ---------- words ----------
const BAD = (() => { try { return fs.readFileSync(path.join(__dirname, 'badwords.txt'), 'utf8').split(/\r?\n/).map(s => s.trim().toLowerCase()).filter(s => s && !s.startsWith('#')); } catch (e) { return []; } })();
const RESERVED = ['admin', 'administrator', 'mod', 'moderator', 'staff', 'system', 'server', 'memecapes', 'official', 'support', 'jagex', 'runescape'];
const squash = s => s.toLowerCase().replace(/[0@]/g, 'o').replace(/[1!|]/g, 'i').replace(/3/g, 'e').replace(/[4]/g, 'a').replace(/[5$]/g, 's').replace(/7/g, 't').replace(/[^a-z]/g, '');
// short words must match the whole word (so "grape" is fine); long ones match inside words too
const isBad = s => { const q = squash(s); return !!q && BAD.some(w => q === w || q === w + 's' || (w.length >= 5 && q.includes(w))); };
function cleanChat(t) {
  t = String(t || '').replace(/[\u0000-\u001f\u007f<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, 80);
  if (!BAD.length) return t;
  return t.split(' ').map(w => isBad(w) ? '*'.repeat(Math.min(6, w.length)) : w).join(' ');
}
function nameProblem(n) {
  if (!/^[A-Za-z0-9_]{3,12}$/.test(n)) return 'Pick a name with 3 to 12 letters, numbers or _.';
  const q = squash(n);
  if (RESERVED.some(r => q.includes(r))) return 'That name is reserved.';
  if (BAD.some(w => q.includes(w))) return 'Pick a different name.';
  return '';
}

// ---------- passwords and sessions ----------
const hashPass = (p, salt) => crypto.scryptSync(p, salt, 32).toString('hex');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const passOk = (p, u) => { const a = Buffer.from(hashPass(p, u.salt), 'hex'), b = Buffer.from(String(u.hash || ''), 'hex'); return a.length === b.length && crypto.timingSafeEqual(a, b); };
function newSession(uid) { const tok = crypto.randomBytes(32).toString('hex'); Q.sesAdd.run(sha(tok), uid, now(), now()); return tok; }

// ---------- save checks ----------
const sumXp = s => Object.values((s && s.xp) || {}).reduce((a, v) => a + (+v || 0), 0);
const wealth = s => (+((s && s.coins) || 0)) + (+((s && s.bank) || 0));
function checkSave(st) {
  if (!st || typeof st !== 'object' || Array.isArray(st)) return 'not a save';
  if (!Array.isArray(st.inv) || st.inv.length > 40) return 'bad bag';
  for (const k of ['coins', 'bank']) if (st[k] != null && !(Number.isFinite(+st[k]) && +st[k] >= 0)) return 'bad ' + k;
  if (st.xp && typeof st.xp !== 'object') return 'bad xp';
  return '';
}
function flagGains(u, prev, next) {
  if (!prev) return;
  const dt = Math.max(60, (now() - (u.save_t || now())) / 1000);
  const dw = wealth(next) - wealth(prev), dx = sumXp(next) - sumXp(prev);
  if (dw > 250000 + 4000 * dt) Q.flag.run(u.id, now(), 'coins', `+${Math.round(dw)} in ${Math.round(dt)}s`);
  if (dx > 400000 + 15000 * dt) Q.flag.run(u.id, now(), 'xp', `+${Math.round(dx)} in ${Math.round(dt)}s`);
}

// ---------- tiny WebSocket layer (RFC 6455, text frames) ----------
function wsAccept(req, socket, ip) {
  const key = req.headers['sec-websocket-key'];
  if (!key) { G.wsClose(ip); return socket.destroy(); }
  const acc = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
  socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + acc + '\r\n\r\n');
  socket.setNoDelay(true);
  const c = { socket, buf: Buffer.alloc(0), frag: [], fragN: 0, alive: true, open: true, ip, bucket: 40, bt: now() };
  setTimeout(() => { if (c.open && !c.uid) c.close(); }, 120e3);   // sign in within two minutes or the connection closes
  c.send = obj => { if (!c.open) return; const d = Buffer.from(JSON.stringify(obj)); let h; if (d.length < 126) h = Buffer.from([0x81, d.length]); else if (d.length < 65536) { h = Buffer.alloc(4); h[0] = 0x81; h[1] = 126; h.writeUInt16BE(d.length, 2); } else { h = Buffer.alloc(10); h[0] = 0x81; h[1] = 127; h.writeBigUInt64BE(BigInt(d.length), 2); } socket.write(Buffer.concat([h, d])); };
  c.close = () => { if (!c.open) return; c.open = false; try { socket.write(Buffer.from([0x88, 0])); } catch (e) { } socket.end(); setTimeout(() => socket.destroy(), 1000); };
  c.ping = () => { try { socket.write(Buffer.from([0x89, 0])); } catch (e) { } };
  socket.on('data', chunk => {
    c.buf = Buffer.concat([c.buf, chunk]);
    while (c.buf.length >= 2) {
      const b0 = c.buf[0], b1 = c.buf[1], op = b0 & 15, fin = b0 & 128, masked = b1 & 128;
      let len = b1 & 127, off = 2;
      if (len === 126) { if (c.buf.length < 4) return; len = c.buf.readUInt16BE(2); off = 4; }
      else if (len === 127) { if (c.buf.length < 10) return; len = Number(c.buf.readBigUInt64BE(2)); off = 10; }
      if (len > MAX_FRAME || !masked) { G.strike(c.ip, 'bad websocket frame', 5); return c.close(); }
      if (c.buf.length < off + 4 + len) return;
      const mask = c.buf.subarray(off, off + 4), data = Buffer.from(c.buf.subarray(off + 4, off + 4 + len));
      for (let i = 0; i < data.length; i++) data[i] ^= mask[i & 3];
      c.buf = c.buf.subarray(off + 4 + len);
      if (op === 8) return c.close();
      if (op === 9) { socket.write(Buffer.concat([Buffer.from([0x8a, data.length]), data])); continue; }
      if (op === 10) { c.alive = true; continue; }
      if (op === 1 || op === 0) {
        c.frag.push(data); c.fragN += data.length; if (c.fragN > MAX_FRAME) { G.strike(c.ip, 'oversized websocket message', 5); return c.close(); }
        if (fin) { const msg = Buffer.concat(c.frag).toString('utf8'); c.frag = []; c.fragN = 0; if (msg.length > MAX_FRAME) return c.close(); onMessage(c, msg); }
      }
    }
  });
  socket.on('close', () => { c.open = false; G.wsClose(ip); onClose(c); });
  socket.on('error', () => { c.open = false; });
  onOpen(c);
}

// ---------- live state ----------
const online = new Map();   // uid -> connection
const loginTries = new Map(); // ip -> [times]
let seq = 0;
const say = (c, text, color) => c.send({ t: 'info', text, color });
const pub = c => ({ id: c.uid, name: c.name, g: c.look.g | 0, c: c.look.c || '', lv: c.look.lv | 0, role: c.role || '' });
function broadcast(obj, except) { for (const o of online.values()) if (o !== except) o.send(obj); }

function onOpen(c) { c.id = ++seq; c.send({ t: 'hello', need: 'login' }); }
function onClose(c) {
  if (c.trade) tradeEnd(c.trade, c.name + ' left.');
  if (c.uid && online.get(c.uid) === c) { online.delete(c.uid); broadcast({ t: 'leave', id: c.uid }); }
}

function tooMany(ip) {
  const L = (loginTries.get(ip) || []).filter(t => now() - t < 10 * 60e3); L.push(now()); loginTries.set(ip, L);
  return L.length > 12;
}

function signIn(c, u, tok) {
  if (u.banned) { c.send({ t: 'err', text: 'This account is banned.' }); return c.close(); }
  const old = online.get(u.id);
  if (old && old !== c) { old.send({ t: 'kicked', text: 'You logged in somewhere else.' }); online.delete(u.id); old.close(); }
  c.uid = u.id; c.name = u.name; c.role = ADMINS.includes(u.name.toLowerCase()) ? 'admin' : (u.role || '');
  c.iron = !!u.iron; c.look = { g: 0, c: '', lv: 3 }; c.pos = null; c.ignore = new Set();
  online.set(u.id, c); Q.seen.run(now(), c.ip, u.id);
  let save = null; try { save = u.save ? JSON.parse(u.save) : null; } catch (e) { }
  c.send({ t: 'welcome', name: u.name, token: tok, save, rev: u.rev, role: c.role, iron: c.iron, online: online.size });
  c.send({ t: 'chatlog', lines: Q.recentChat.all().reverse() });
  for (const o of online.values()) if (o !== c && o.pos) c.send({ t: 'pi', ...pub(o) });
  const w = CAPES_MINT && Q.wal.get(u.id);  // holder perks: a fresh balance check at every login
  if (w) holderCheck(w).then(() => { c.send(holderInfo(u.id)); c.send(partnerInfo(u.id)); }); else { c.send(holderInfo(u.id)); c.send(partnerInfo(u.id)); }
  c.send({ t: 'partners', list: partnersLive() });
}

const H = {
  register(c, m) {
    if (c.uid) return;
    if (!G.allow('register')) return c.send({ t: 'err', text: G.pausedMsg() });
    if (tooMany(c.ip)) return c.send({ t: 'err', text: 'Too many tries. Wait a few minutes.' });
    const name = String(m.name || ''), pass = String(m.pass || '');
    const np = nameProblem(name); if (np) return c.send({ t: 'err', text: np });
    if (pass.length < 8 || pass.length > 100) return c.send({ t: 'err', text: 'Use a password with at least 8 characters.' });
    if (Q.byName.get(name)) return c.send({ t: 'err', text: 'That name is taken.' });
    const salt = crypto.randomBytes(16).toString('hex');
    const r = Q.add.run(name, salt, hashPass(pass, salt), now(), now(), m.iron ? 1 : 0, c.ip);
    const u = Q.byId.get(r.lastInsertRowid);
    signIn(c, u, newSession(u.id));
  },
  login(c, m) {
    if (c.uid) return;
    if (!G.allow('login')) return c.send({ t: 'err', text: G.pausedMsg() });
    if (tooMany(c.ip)) return c.send({ t: 'err', text: 'Too many tries. Wait a few minutes.' });
    const name = String(m.name || '').slice(0, 40);
    if (G.loginLocked(name)) return c.send({ t: 'err', text: 'Too many wrong passwords for this name. It is locked for 15 minutes.' });
    const u = Q.byName.get(name);
    if (!u || !passOk(String(m.pass || ''), u)) { G.loginFail(name, c.ip); return c.send({ t: 'err', text: 'Wrong name or password.' }); }
    G.loginOk(name); signIn(c, u, newSession(u.id));
  },
  resume(c, m) {
    if (c.uid) return;
    const s = Q.ses.get(sha(String(m.token || '')));
    if (!s || now() - s.last > 60 * 864e5) return c.send({ t: 'err', text: 'Please log in again.', relog: 1 });
    const u = Q.byId.get(s.uid); if (!u) return c.send({ t: 'err', text: 'Please log in again.', relog: 1 });
    Q.sesSeen.run(now(), s.token);
    signIn(c, u, m.token);
  },
  logout(c, m) { Q.sesDel.run(sha(String(m.token || ''))); c.close(); },
  deleteAccount(c, m) {
    const u = c.uid && Q.byId.get(c.uid); if (!u) return;
    if (G.loginLocked(u.name)) return c.send({ t: 'err', text: 'Too many wrong passwords. Wait 15 minutes.' });
    if (!passOk(String(m.pass || ''), u)) { G.loginFail(u.name, c.ip); return c.send({ t: 'err', text: 'Wrong password.' }); }
    Q.sesDelUser.run(u.id); Q.walDel.run(u.id); Q.ptDel.run(u.id); Q.del.run(u.id); partnersMaybeChanged(); c.send({ t: 'deleted' }); c.close();
  },
  save(c, m) {
    if (!c.uid || c.trade && c.trade.stage === 3) return;
    const raw = JSON.stringify(m.st || null);
    if (raw.length > MAX_SAVE) return c.send({ t: 'err', text: 'Save too big.' });
    const bad = checkSave(m.st); if (bad) { Q.flag.run(c.uid, now(), 'save', bad); return c.send({ t: 'err', text: 'Save refused: ' + bad }); }
    const u = Q.byId.get(c.uid);
    if (+m.rev !== u.rev) return c.send({ t: 'stale', rev: u.rev });
    let prev = null; try { prev = u.save ? JSON.parse(u.save) : null; } catch (e) { }
    flagGains(u, prev, m.st);
    const r = Q.save.run(raw, now(), c.uid, u.rev);
    if (!r.changes) return c.send({ t: 'stale', rev: u.rev });
    c.send({ t: 'saved', rev: u.rev + 1 });
  },
  pull(c) { if (!c.uid) return; const u = Q.byId.get(c.uid); let save = null; try { save = JSON.parse(u.save); } catch (e) { } c.send({ t: 'resync', save, rev: u.rev }); },
  pos(c, m) {
    if (!c.uid) return;
    const x = +m.x, y = +m.y; if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    const first = !c.pos;
    c.pos = { x, y, r: +m.r || 0, m: m.m | 0, a: String(m.a || '').slice(0, 48) };
    const look = { g: m.g ? 1 : 0, c: String(m.c || '').slice(0, 48), lv: Math.max(3, Math.min(200, m.lv | 0)) };
    if (first || look.g !== c.look.g || look.c !== c.look.c || look.lv !== c.look.lv) { c.look = look; broadcast({ t: 'pi', ...pub(c) }, c); }
  },
  chat(c, m) {
    if (!c.uid) return;
    const raw = String(m.text || '');
    if (raw.startsWith('/') && c.role === 'admin') return adminCmd(c, raw);
    const u = Q.byId.get(c.uid);
    if (u.muted_until > now()) return say(c, 'You are muted for ' + Math.ceil((u.muted_until - now()) / 60e3) + ' more minutes.', '#c00');
    if (now() - (c.lastChat || 0) < 1200) return say(c, 'Slow down a little.', '#c00');
    const text = cleanChat(raw); if (!text) return;
    c.lastChat = now();
    Q.chat.run(now(), c.uid, c.name, text); if (Math.random() < .01) Q.chatTrim.run();
    for (const o of online.values()) if (!o.ignore.has(c.uid)) o.send({ t: 'chat', id: c.uid, name: c.name, text, role: c.role });
  },
  ignore(c, m) { const o = findOnline(m.name); if (!o) return; if (m.off) c.ignore.delete(o.uid); else c.ignore.add(o.uid); },
  report(c, m) {
    if (!c.uid) return;
    Q.report.run(c.uid, String(m.name || '').slice(0, 12), now(), String(m.why || '').slice(0, 200), JSON.stringify(Q.recentChat.all()));
    say(c, 'Thanks. A moderator will look at it.', '#0a0');
  },
  who(c) { c.send({ t: 'who', names: [...online.values()].map(o => o.name).sort() }); },

  // ---- trades: the server checks both offers against the saved bags and does the swap itself
  tradeReq(c, m) {
    if (!c.uid) return;
    const o = findOnline(m.name);
    if (!o || o === c) return say(c, 'That player is not online.', '#c00');
    if (c.iron || o.iron) return say(c, 'Diamond Hands players cannot trade.', '#c00');
    if (c.trade || o.trade) return say(c, (c.trade ? 'You are' : o.name + ' is') + ' already trading.', '#c00');
    if (o.ignore.has(c.uid)) return say(c, o.name + ' is not taking trades.', '#c00');
    if (o.pendingFrom === c.uid && now() - o.pendingT < 60e3) return H.tradeYes(o, { name: c.name });
    c.pendingFrom = null; o.pendingFrom = c.uid; o.pendingT = now();
    o.send({ t: 'tradeReq', from: c.name }); say(c, 'Trade request sent to ' + o.name + '.', '#0a0');
  },
  tradeYes(c, m) {
    const o = findOnline(m.name);
    if (!o || c.pendingFrom !== o.uid || now() - c.pendingT > 60e3) return say(c, 'That trade request ran out.', '#c00');
    if (c.trade || o.trade) return say(c, 'One of you is already trading.', '#c00');
    c.pendingFrom = null;
    const T = { a: o, b: c, stage: 1, off: new Map([[o.uid, { items: [], coins: 0 }], [c.uid, { items: [], coins: 0 }]]), acc: new Set(), t: now(), ver: 0, chg: 0 };
    o.trade = c.trade = T;
    o.send({ t: 'tradeStart', with: c.name }); c.send({ t: 'tradeStart', with: o.name });
  },
  tradeOffer(c, m) {
    const T = c.trade; if (!T || T.stage !== 1) return;
    const items = Array.isArray(m.items) ? m.items.slice(0, BAG).map(String) : [], coins = Math.max(0, Math.floor(+m.coins || 0));
    const why = offerProblem(c.uid, items, coins); if (why) { const was = T.off.get(c.uid); c.send({ t: 'tradeVer', ver: T.ver, bad: 1, items: was.items, coins: was.coins }); return say(c, why, '#c00'); }
    // every change gets a new version number: an accept only counts for the exact offer that player was looking at
    T.off.set(c.uid, { items, coins }); T.acc.clear(); T.ver++; T.chg = now(); T.chgBy = c.uid;
    other(T, c).send({ t: 'tradeTheirs', items, coins, ver: T.ver }); c.send({ t: 'tradeVer', ver: T.ver });
  },
  tradeAccept(c, m) {
    const T = c.trade; if (!T || (m.stage | 0) !== T.stage) return;
    if ((m.ver | 0) !== T.ver) return c.send({ t: 'tradeNoAcc', why: 'The offer changed. Check it again, then accept.' });
    if (T.chgBy !== c.uid && now() - T.chg < TRADE_LOCK_MS) return c.send({ t: 'tradeNoAcc', why: 'The offer just changed. Take a moment to check it, then accept.' });
    T.acc.add(c.uid); other(T, c).send({ t: 'tradeAcc', stage: T.stage });
    if (T.acc.size < 2) return;
    if (T.stage === 1) { T.stage = 2; T.acc.clear(); T.a.send({ t: 'tradeStage2' }); T.b.send({ t: 'tradeStage2' }); return; }
    tradeFinish(T);
  },
  tradeCancel(c) { if (c.trade) tradeEnd(c.trade, c.name + ' declined the trade.'); },
};

function findOnline(name) { name = String(name || '').toLowerCase(); for (const o of online.values()) if (o.name.toLowerCase() === name) return o; return null; }
const other = (T, c) => T.a === c ? T.b : T.a;
const NOTRADE = k => k === 'coin' || k.startsWith('cx_') || k.startsWith('cape_') || k === 'qcape' || k.startsWith('pet') || k === 'clue' || k.startsWith('lamp');
function loadSave(uid) { const u = Q.byId.get(uid); try { return { u, st: JSON.parse(u.save) }; } catch (e) { return { u, st: null }; } }
function offerProblem(uid, items, coins) {
  const { st } = loadSave(uid);
  if (!st) return 'Your progress has not reached the server yet. Wait a few seconds and try again.';
  if (coins > (+st.coins || 0)) return 'You do not have that many Meme Coins on you.';
  const have = {}; for (const k of st.inv) have[k] = (have[k] || 0) + 1;
  for (const k of items) { if (NOTRADE(k)) return 'That item cannot be traded.'; if (!have[k]) return 'That item is not in your bag (the server copy).'; have[k]--; }
  return '';
}
function tradeEnd(T, why) {
  for (const c of [T.a, T.b]) { if (c.trade === T) { c.trade = null; c.send({ t: 'tradeCancel', why }); } }
}
function tradeFinish(T) {
  T.stage = 3;
  const A = loadSave(T.a.uid), B = loadSave(T.b.uid), oa = T.off.get(T.a.uid), ob = T.off.get(T.b.uid);
  const pa = offerProblem(T.a.uid, oa.items, oa.coins), pb = offerProblem(T.b.uid, ob.items, ob.coins);
  if (pa || pb) return tradeEnd(T, 'Trade stopped: an offer no longer matches what is in the bag.');
  const swap = (st, give, get) => {
    const rm = give.items.slice(); st.inv = st.inv.filter(k => { const i = rm.indexOf(k); if (i >= 0) { rm.splice(i, 1); return false; } return true; });
    st.coins = (+st.coins || 0) - give.coins + get.coins; get.items.forEach(k => st.inv.push(k));
  };
  const room = (st, give, get) => BAG - ((+st.coins || 0) - give.coins + get.coins > 0 ? 1 : 0) - (st.inv.length - give.items.length) >= get.items.length;
  if (!room(A.st, oa, ob) || !room(B.st, ob, oa)) return tradeEnd(T, 'Trade stopped: not enough bag space.');
  swap(A.st, oa, ob); swap(B.st, ob, oa);
  const t = now();
  db.exec('BEGIN');
  try {
    Q.setSave.run(JSON.stringify(A.st), A.u.rev + 1, t, A.u.id); Q.setSave.run(JSON.stringify(B.st), B.u.rev + 1, t, B.u.id);
    Q.trade.run(t, A.u.id, B.u.id, JSON.stringify(oa), JSON.stringify(ob)); db.exec('COMMIT');
  } catch (e) { db.exec('ROLLBACK'); return tradeEnd(T, 'Trade failed. Nothing changed.'); }
  T.a.trade = T.b.trade = null;
  T.a.send({ t: 'tradeDone', inv: A.st.inv, coins: A.st.coins, rev: A.u.rev + 1, gave: oa, got: ob });
  T.b.send({ t: 'tradeDone', inv: B.st.inv, coins: B.st.coins, rev: B.u.rev + 1, gave: ob, got: oa });
}

// ---------- holder perks ----------
// The player proves the wallet is theirs by signing a short message in their wallet app (free: no transaction, nothing moves).
// The server then reads the wallet's $CAPES balance from the blockchain itself, at link time, at every login and once a day
// at a random hour. Perks need the balance to stay at HOLDER_PCT % or more at every check:
//   Cape Club membership: while the last check passed.
//   One free shop skin: after HOLDER_DAYS days of holding without a failed check, then again every HOLDER_DAYS days.
// Passing the same tokens between wallets does not multiply the skins: a failed check restarts that wallet's count.
const B58A = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function b58(s) {
  s = String(s || ''); if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(s)) return null;
  let n = 0n; for (const ch of s) n = n * 58n + BigInt(B58A.indexOf(ch));
  const out = []; while (n > 0n) { out.unshift(Number(n & 255n)); n >>= 8n; }
  for (const ch of s) { if (ch !== '1') break; out.unshift(0); }
  return Buffer.from(out);
}
const SPKI_ED = Buffer.from('302a300506032b6570032100', 'hex');
function sigOk(wallet, msg, sigB64) {
  const pk = b58(wallet); if (!pk || pk.length !== 32) return false;
  try {
    const key = crypto.createPublicKey({ key: Buffer.concat([SPKI_ED, pk]), format: 'der', type: 'spki' });
    const sig = Buffer.from(String(sigB64 || ''), 'base64'); if (sig.length !== 64) return false;
    return crypto.verify(null, Buffer.from(msg, 'utf8'), key, sig);
  } catch (e) { return false; }
}
async function rpc(method, params) {
  const r = await fetch(RPC, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }), signal: AbortSignal.timeout(15000) });
  const j = await r.json(); if (j.error) throw new Error(j.error.message || 'rpc error'); return j.result;
}
let supplyC = { t: 0, v: 0n };
async function capesSupply(fresh) {
  if (!fresh && supplyC.v && now() - supplyC.t < 3600e3) return supplyC.v;
  const r = await rpc('getTokenSupply', [CAPES_MINT]); supplyC = { t: now(), v: BigInt(r.value.amount), d: r.value.decimals | 0 }; return supplyC.v;
}
async function capesBalance(w) {
  const r = await rpc('getTokenAccountsByOwner', [w, { mint: CAPES_MINT }, { encoding: 'jsonParsed', commitment: 'confirmed' }]);
  return r.value.reduce((a, x) => a + BigInt(x.account.data.parsed.info.tokenAmount.amount), 0n);
}
const nextDue = () => now() + 18 * 3600e3 + Math.floor(Math.random() * 12 * 3600e3);  // 18 to 30 hours, so nobody can time a check
async function holderCheck(row) {
  try {
    const [s, b] = await Promise.all([capesSupply(), capesBalance(row.wallet)]);
    const pct = s > 0n ? Number(b * 1000000n / s) / 10000 : 0, ok = pct >= HOLD_PCT;
    const cur = Q.wal.get(row.uid); if (!cur || cur.wallet !== row.wallet) return null;  // unlinked meanwhile
    // a gap of more than 3 days without a check (server down) also restarts the count: we can't vouch for it
    const fresh = now() - cur.checked < 3 * 864e5, p3 = pct >= PARTNER_PCT;
    const since = ok ? (cur.ok && cur.since && fresh ? cur.since : now()) : 0;
    const since3 = p3 ? (cur.since3 && fresh ? cur.since3 : now()) : 0;
    const sinceM = pct >= SOTM_PCT ? (cur.sinceM && fresh ? cur.sinceM : now()) : 0;
    // partners (and anyone close to the line) are checked every 15 minutes, so an ad comes down soon after the balance drops
    const due = pct >= PARTNER_PCT * 0.8 || Q.ptGet.get(row.uid) ? now() + PARTNER_CHECK : nextDue();
    Q.walCheck.run(since, since3, sinceM, now(), due, ok ? 1 : 0, pct, '', row.uid);
    setTimeout(partnersMaybeChanged, 0);
  } catch (e) { Q.walErr.run(now() + 3600e3, String(e.message || e).slice(0, 120), row.uid); }
  return Q.wal.get(row.uid);
}
function holderInfo(uid) {
  const w = Q.wal.get(uid), d = HOLD_DAYS * 864e5;
  const S = sotmNow(), md = SOTM_DAYS * 864e5, got = S.skin ? !!Q.sotmGet.get(uid, S.key) : false;
  const base = { t: 'holder', on: !!CAPES_MINT, need: HOLD_PCT, days: HOLD_DAYS, sotm: S.skin, sotmN: S.n, sotmNeed: SOTM_PCT, sotmDays: SOTM_DAYS, sotmGot: got };
  if (!w) return base;
  const mAt = w.sinceM ? w.sinceM + md : 0;
  const ready = w.ok && w.since ? Math.max(w.since + d, (w.claimed || 0) + d) : 0;
  return { ...base, wallet: w.wallet, pct: w.pct, member: !!w.ok, checked: w.checked, held: w.ok && w.since ? now() - w.since : 0,
    claimAt: ready, canClaim: !!w.ok && ready > 0 && now() >= ready, claims: w.claims, err: w.err || '',
    sotmOk: !!w.sinceM, sotmAt: mAt, canSotm: !!S.skin && !got && mAt > 0 && now() >= mAt };
}
Object.assign(H, {
  holderInfo(c) { if (c.uid) c.send(holderInfo(c.uid)); },
  walletNonce(c, m) {
    if (!c.uid) return;
    if (!CAPES_MINT) return say(c, 'Holder perks open when $CAPES launches.', '#a60');
    const w = String(m.wallet || ''); const pk = b58(w); if (!pk || pk.length !== 32) return c.send({ t: 'err', text: 'That is not a Solana wallet address.' });
    c.walletMsg = { w, msg: 'MemeCapes: prove this wallet is yours.\n\nAccount: ' + c.name + '\nWallet: ' + w + '\nCode: ' + crypto.randomBytes(8).toString('hex') +
      '\n\nSigning this is free. It is not a transaction and it does not move any tokens.' };
    c.send({ t: 'walletSign', wallet: w, msg: c.walletMsg.msg });
  },
  async walletLink(c, m) {
    if (!c.uid || !c.walletMsg || c.walletMsg.w !== m.wallet) return;
    const { w, msg } = c.walletMsg; c.walletMsg = null;
    if (!sigOk(w, msg, m.sig)) return c.send({ t: 'err', text: 'The signature did not match that wallet. Nothing was linked.' });
    const other = Q.walBy.get(w);
    if (other && other.uid !== c.uid) return c.send({ t: 'err', text: 'That wallet is linked to another MemeCapes account. Unlink it there first.' });
    const old = Q.wal.get(c.uid);
    if (!(old && old.wallet === w)) Q.walSet.run(c.uid, w, now(), old ? old.claimed : 0, old ? old.claims : 0);  // the skin timer belongs to the account
    say(c, 'Wallet linked. Checking your $CAPES...', '#0a0');
    await holderCheck(Q.wal.get(c.uid)); c.send(holderInfo(c.uid)); c.send(partnerInfo(c.uid));
  },
  walletUnlink(c) { if (!c.uid) return; Q.walDel.run(c.uid); say(c, 'Wallet unlinked.', '#a60'); c.send(holderInfo(c.uid)); c.send(partnerInfo(c.uid)); partnersMaybeChanged(); },
  async holderClaim(c, m) {
    if (!c.uid || c.claiming) return;
    const skin = String(m.skin || ''); if (!SKIN_IDS.includes(skin)) return;
    let info = holderInfo(c.uid); if (!info.canClaim) return say(c, 'Your free skin is not ready yet.', '#c00');
    c.claiming = 1;
    try {
      await holderCheck(Q.wal.get(c.uid)); info = holderInfo(c.uid);  // one fresh look at the balance right now
      if (!info.canClaim) { c.send(info); return say(c, 'Your wallet is below ' + HOLD_PCT + '% of $CAPES now, so the free skin is on hold.', '#c00'); }
      const { u, st } = loadSave(c.uid); if (!st) return say(c, 'Your progress has not reached the server yet. Try again in a few seconds.', '#c00');
      st.skins = Array.isArray(st.skins) ? st.skins : []; if (st.skins.includes(skin)) return say(c, 'You already own that skin. Pick another.', '#c00');
      st.skins.push(skin);
      db.exec('BEGIN');
      try { Q.setSave.run(JSON.stringify(st), u.rev + 1, now(), u.id); Q.walClaim.run(now(), c.uid); db.exec('COMMIT'); }
      catch (e) { db.exec('ROLLBACK'); return say(c, 'That did not work. Nothing changed.', '#c00'); }
      c.send({ t: 'skinGift', skin, skins: st.skins, rev: u.rev + 1 }); c.send(holderInfo(c.uid));
    } finally { c.claiming = 0; }
  },
  async holderSotm(c) {   // Skin of the Month: free for SOTM_PCT % holders after SOTM_DAYS days, once per account per month
    if (!c.uid || c.claiming) return;
    let info = holderInfo(c.uid); if (!info.sotm) return say(c, 'There is no Skin of the Month right now.', '#c00');
    if (info.sotmGot) return say(c, "You already took this month's skin.", '#c00');
    if (!info.canSotm) return say(c, "This month's free skin is not ready for you yet.", '#c00');
    c.claiming = 1;
    try {
      await holderCheck(Q.wal.get(c.uid)); info = holderInfo(c.uid);  // one fresh look at the balance right now
      if (!info.canSotm) { c.send(info); return say(c, 'Your wallet is below ' + SOTM_PCT + "% of $CAPES now, so this month's skin is on hold.", '#c00'); }
      const { u, st } = loadSave(c.uid); if (!st) return say(c, 'Your progress has not reached the server yet. Try again in a few seconds.', '#c00');
      st.skins = Array.isArray(st.skins) ? st.skins : []; if (st.skins.includes(info.sotm)) return say(c, 'You already own this skin.', '#c00');
      st.skins.push(info.sotm);
      db.exec('BEGIN');
      try { Q.setSave.run(JSON.stringify(st), u.rev + 1, now(), u.id); Q.sotmAdd.run(c.uid, sotmNow().key, info.sotm, now()); db.exec('COMMIT'); }
      catch (e) { db.exec('ROLLBACK'); return say(c, 'That did not work. Nothing changed.', '#c00'); }
      c.send({ t: 'skinGift', skin: info.sotm, skins: st.skins, rev: u.rev + 1 }); c.send(holderInfo(c.uid));
    } finally { c.claiming = 0; }
  },
});

// ---------- partners (3% holders) ----------
const PD = () => PARTNER_DAYS * 864e5;
function partnerState(uid) {
  const w = Q.wal.get(uid), p = Q.ptGet.get(uid);
  const over = !!(w && w.pct >= PARTNER_PCT && w.since3), held = over ? now() - w.since3 : 0;
  return { w, p, over, held, eligible: over && held >= PD(), live: !!(p && p.status === 'approved' && over && held >= PD()), at: over ? w.since3 + PD() : 0 };
}
function partnerInfo(uid) {
  const S = partnerState(uid), p = S.p;
  return { t: 'partner', on: !!CAPES_MINT, need: PARTNER_PCT, days: PARTNER_DAYS, over: S.over, eligible: S.eligible, live: S.live, liveAt: S.at, id: uid,
    ad: p ? { brand: p.brand, line: p.line, link: p.link, color: p.color, g: p.g, status: p.status, note: p.note, v: p.updated } : null };
}
function partnersLive() {
  return Q.ptAll.all().filter(r => r.status === 'approved' && partnerState(r.uid).live)
    .map(r => ({ id: r.uid, brand: r.brand, line: r.line, link: r.link, color: r.color, g: r.g, v: r.updated }));
}
let ptLast = '[]';
function partnersMaybeChanged() {
  const L = partnersLive(), j = JSON.stringify(L); if (j === ptLast) return;
  const before = new Set(JSON.parse(ptLast).map(x => x.id)); ptLast = j;
  for (const x of L) if (!before.has(x.id)) console.log('partner live', x.id, x.brand);
  for (const id of before) if (!L.some(x => x.id === id)) console.log('partner removed', id);
  broadcast({ t: 'partners', list: L });
  for (const o of online.values()) if (Q.ptGet.get(o.uid) || before.has(o.uid)) o.send(partnerInfo(o.uid));
}
const clean1 = (t, n) => cleanChat(String(t || '')).slice(0, n);
function partnerSave(c, m) {
  if (!c.uid) return;
  if (!CAPES_MINT) return say(c, 'Partner ads open when $CAPES launches.', '#a60');
  if (!G.allow('ad')) return c.send({ t: 'err', text: G.pausedMsg() });
  const S = partnerState(c.uid); if (!S.over) return c.send({ t: 'err', text: 'Partner ads need a linked wallet holding at least ' + PARTNER_PCT + '% of $CAPES.' });
  const brand = clean1(m.brand, 24), line = clean1(m.line, 80), link = String(m.link || '').trim().slice(0, 100), color = String(m.color || '');
  if (brand.length < 2) return c.send({ t: 'err', text: 'Give your project a name (2 to 24 letters).' });
  if (link && !/^https:\/\/[a-z0-9.-]+\.[a-z]{2,}(\/[^\s<>"']*)?$/i.test(link)) return c.send({ t: 'err', text: 'The link must start with https:// and be a normal web address.' });
  if (!/^#[0-9a-f]{6}$/i.test(color)) return c.send({ t: 'err', text: 'Pick a cape colour.' });
  const im = String(m.img || ''), mm = /^data:image\/jpeg;base64,([A-Za-z0-9+/=]+)$/.exec(im);
  if (!mm) return c.send({ t: 'err', text: 'Add a picture for the billboard.' });
  const raw = Buffer.from(mm[1], 'base64'); if (raw.length > 300 * 1024 || raw[0] !== 0xff || raw[1] !== 0xd8) return c.send({ t: 'err', text: 'That picture could not be used. Try a smaller JPEG or PNG.' });
  Q.ptSet.run(c.uid, brand, line, link, color, m.g ? 1 : 0, raw.toString('base64'), now());
  c.send(partnerInfo(c.uid)); say(c, 'Thanks! Your ad is waiting for approval. It goes live once it is approved and you have held ' + PARTNER_PCT + '% for ' + PARTNER_DAYS + ' days.', '#0a0');
  for (const o of online.values()) if (o.role === 'admin') say(o, 'New partner ad from ' + c.name + ' (' + brand + '). Look at it with /partner view ' + c.name, '#c80');
  partnersMaybeChanged();
}
function partnerCmd(c, name, arg, rest) {
  if (!name || name === 'list') {
    const L = Q.ptAll.all(); if (!L.length) return say(c, 'No partner ads yet.', '#a60');
    return say(c, 'Partner ads: ' + L.map(r => r.name + ' (' + r.brand + ', ' + r.status + (partnerState(r.uid).live ? ', LIVE' : '') + ', ' + (r.pct || 0) + '%)').join('; '), '#a60');
  }
  const u = Q.byName.get(arg ? arg : ''), p = u && Q.ptGet.get(u.id);
  if (!p) return say(c, 'Usage: /partner list, /partner view Name, /partner approve Name, /partner reject Name reason, /partner remove Name', '#a60');
  const S = partnerState(u.id), note = rest.split(' ').slice(2).join(' ').slice(0, 120);
  if (name === 'view') return c.send({ t: 'partnerReview', name: u.name, brand: p.brand, line: p.line, link: p.link, color: p.color, g: p.g, status: p.status, pct: S.w ? S.w.pct : 0, heldDays: Math.floor(S.held / 864e5), img: 'data:image/jpeg;base64,' + p.img });
  if (name === 'approve') Q.ptStatus.run('approved', '', now(), u.id);
  else if (name === 'reject') Q.ptStatus.run('rejected', note || 'Please change the ad and send it again.', 0, u.id);
  else if (name === 'remove') Q.ptDel.run(u.id);
  else return say(c, 'Usage: /partner list, /partner view Name, /partner approve Name, /partner reject Name reason, /partner remove Name', '#a60');
  say(c, u.name + "'s ad: " + name + (name === 'approve' && !S.eligible ? 'd. It goes live when they have held ' + PARTNER_PCT + '% for ' + PARTNER_DAYS + ' days.' : name === 'approve' ? 'd and live.' : 'ed.'), '#0a0');
  const o = online.get(u.id); if (o) { o.send(partnerInfo(u.id)); if (name === 'reject') say(o, 'Your partner ad was not approved: ' + (note || 'please change it and send it again.'), '#c00'); }
  partnersMaybeChanged();
}
Object.assign(H, {
  partnerInfo(c) { if (c.uid) c.send(partnerInfo(c.uid)); },
  partnerSave,
});

// ---------- burn ads (website) ----------
// 1. On memecapes.com the buyer connects their wallet and signs a free message (proves the wallet is theirs), and sends the ad.
// 2. An admin approves it in game (/burnad view 7, /burnad approve 7). Nothing is burned before that, so a refused ad costs nothing.
// 3. The buyer burns BURN_PCT % of all $CAPES from that same wallet and pastes the transaction. The server reads it from the
//    blockchain: a real burn (supply goes down) of the $CAPES mint, signed by that wallet, big enough, never used before. Then it's live.
const baNonce = new Map();  // wallet -> { msg, t }
function baMsg(w) {
  const m = 'MemeCapes: prove this wallet is yours to send a website ad.\n\nWallet: ' + w + '\nCode: ' + crypto.randomBytes(8).toString('hex') +
    '\n\nSigning this is free. It is not a transaction and it does not move or burn any tokens.';
  if (baNonce.size > 2000) baNonce.clear();
  baNonce.set(w, { msg: m, t: now() }); return m;
}
function baProof(w, sig) {  // the signed message must be the latest one we gave this wallet, under 15 minutes old
  const n = baNonce.get(w); if (!n || now() - n.t > 15 * 60e3) return false;
  return sigOk(w, n.msg, sig);
}
// one ad spot on the website, shared: each page view shows one live ad, picked with odds = its shares / all shares
const baPub = r => ({ id: r.id, brand: r.brand, line: r.line, link: r.link, v: r.live_at, w: Math.max(1, r.shares | 0) });
const baNeed = async () => { const s = await capesSupply(); return s * BigInt(Math.round(BURN_PCT * 10000)) / 1000000n; };  // tokens (base units) for BURN_PCT %
async function baCheckBurn(w, sig) {
  const tx = await rpc('getTransaction', [sig, { encoding: 'jsonParsed', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]);
  if (!tx) return { err: 'That transaction was not found yet. Wait a minute and try again.' };
  if (tx.meta && tx.meta.err) return { err: 'That transaction failed on the blockchain.' };
  const ins = [...(tx.transaction.message.instructions || []), ...((tx.meta && tx.meta.innerInstructions) || []).flatMap(x => x.instructions || [])];
  let burned = 0n;
  for (const i of ins) {
    const t = i.parsed && i.parsed.type, info = i.parsed && i.parsed.info;
    if (!/^spl-token/.test(i.program || '') || !(t === 'burn' || t === 'burnChecked') || !info) continue;
    if (info.mint !== CAPES_MINT || info.authority !== w) continue;
    burned += BigInt(t === 'burnChecked' ? info.tokenAmount.amount : info.amount);
  }
  if (!burned) return { err: 'That transaction does not burn $CAPES from your wallet. Use your wallet app\'s Burn option (not a send).' };
  const s = await capesSupply(true), before = s + burned;  // supply now has the burn taken out
  if (burned * 1000000n < before * BigInt(Math.round(BURN_PCT * 10000))) return { err: 'That burn is under ' + BURN_PCT + '% of all $CAPES.' };
  const shares = Number(burned * 1000000n / (before * BigInt(Math.round(BURN_PCT * 10000))));  // whole BURN_PCT %s burned
  return { burned, shares: Math.max(1, shares) };
}
function baBody(req, max) {
  return new Promise((ok, no) => { let n = 0; const parts = []; req.on('data', d => { n += d.length; if (n > max) { no(new Error('too big')); req.destroy(); } else parts.push(d); });
    req.on('end', () => { try { ok(JSON.parse(Buffer.concat(parts).toString('utf8') || '{}')); } catch (e) { no(e); } }); req.on('error', no); });
}
async function baHttp(req, res, url, json) {
  if (url.pathname === '/burnads' && req.method === 'GET') return json(Q.baShow.all(now()).map(baPub));
  const im = /^\/burnads\/(\d+)\.jpg$/.exec(url.pathname);
  if (im) {
    const r = Q.baGet.get(+im[1]); if (!r || r.status !== 'live' || (r.ends && r.ends < now())) return json({ error: 'not found' }, 404);
    res.writeHead(200, { 'Content-Type': 'image/jpeg', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=600' }); return res.end(Buffer.from(r.img, 'base64'));
  }
  if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET', 'Access-Control-Allow-Headers': 'Content-Type' }); return res.end(); }
  if (req.method !== 'POST' || !url.pathname.startsWith('/burnad/')) return false;
  if (!CAPES_MINT) return json({ error: 'Website ads open when $CAPES launches.' }, 400);
  let m; try { m = await baBody(req, 600 * 1024); } catch (e) { return json({ error: 'Bad request.' }, 400); }
  const w = String(m.wallet || ''); const pk = b58(w); if (!pk || pk.length !== 32) return json({ error: 'That is not a Solana wallet address.' }, 400);
  const ip = req.ip || G.ipOf(req);
  if (url.pathname === '/burnad/submit' && !G.allow('ad')) return json({ error: G.pausedMsg() }, 503);
  if (url.pathname === '/burnad/nonce') { if (tooMany('ba' + ip)) return json({ error: 'Too many tries. Wait a few minutes.' }, 429); return json({ msg: baMsg(w) }); }
  if (url.pathname === '/burnad/status') {
    let need = ''; try { const n = await baNeed(), d = BigInt(supplyC.d || 0), q = 10n ** d; need = (n / q + (n % q ? 1n : 0n)).toLocaleString('en-US'); } catch (e) { }  // whole tokens, rounded up
    const live = Q.baShow.all(now()); return json({ pct: BURN_PCT, days: BURN_AD_DAYS, need, live: live.length, shares: live.reduce((a, r) => a + Math.max(1, r.shares | 0), 0), ads: Q.baByWallet.all(w) });
  }
  if (url.pathname === '/burnad/submit') {
    if (!baProof(w, m.sig)) return json({ error: 'The wallet signature did not match. Connect your wallet and try again.' }, 400);
    baNonce.delete(w);
    if (Q.baOpen.get(w).n >= 2) return json({ error: 'This wallet already has an ad waiting. Finish that one first.' }, 400);
    const brand = clean1(m.brand, 24), line = clean1(m.line, 90), link = String(m.link || '').trim().slice(0, 100);
    if (brand.length < 2) return json({ error: 'Give your project a name (2 to 24 letters).' }, 400);
    if (link && !/^https:\/\/[a-z0-9.-]+\.[a-z]{2,}(\/[^\s<>"']*)?$/i.test(link)) return json({ error: 'The link must start with https:// and be a normal web address.' }, 400);
    const mm = /^data:image\/jpeg;base64,([A-Za-z0-9+/=]+)$/.exec(String(m.img || '')); if (!mm) return json({ error: 'Add a picture for the ad.' }, 400);
    const raw = Buffer.from(mm[1], 'base64'); if (raw.length > 400 * 1024 || raw[0] !== 0xff || raw[1] !== 0xd8) return json({ error: 'That picture could not be used. Try a smaller JPEG or PNG.' }, 400);
    const r = Q.baAdd.run(w, brand, line, link, raw.toString('base64'), now());
    for (const o of online.values()) if (o.role === 'admin') say(o, 'New website ad #' + r.lastInsertRowid + ' (' + brand + '). Look at it with /burnad view ' + r.lastInsertRowid, '#c80');
    return json({ ok: true, id: Number(r.lastInsertRowid), status: 'pending' });
  }
  if (url.pathname === '/burnad/burn') {
    const r = Q.baGet.get(+m.id); if (!r || r.wallet !== w) return json({ error: 'No ad with that number for this wallet.' }, 404);
    if (r.status === 'live') return json({ ok: true, status: 'live' });
    if (r.status !== 'approved') return json({ error: r.status === 'pending' ? 'Your ad is not approved yet. Do not burn anything until it is.' : 'This ad was not approved.' }, 400);
    const sig = String(m.burnSig || '').trim(); if (!/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(sig)) return json({ error: 'Paste the transaction signature of your burn.' }, 400);
    if (Q.baBySig.get(sig)) return json({ error: 'That burn was already used for an ad.' }, 400);
    let v; try { v = await baCheckBurn(w, sig); } catch (e) { return json({ error: 'Could not reach the blockchain. Try again in a minute.' }, 502); }
    if (v.err) return json({ error: v.err }, 400);
    const ends = BURN_AD_DAYS > 0 ? now() + BURN_AD_DAYS * 864e5 : 0;
    try { Q.baLive.run(sig, String(v.burned), now(), ends, v.shares, r.id); } catch (e) { return json({ error: 'That burn was already used for an ad.' }, 400); }
    console.log('burn ad live', r.id, r.brand, String(v.burned));
    return json({ ok: true, status: 'live' });
  }
  return json({ error: 'not found' }, 404);
}
function burnadCmd(c, name, arg, rest) {
  const usage = () => say(c, 'Usage: /burnad list, /burnad view 7, /burnad approve 7, /burnad reject 7 reason, /burnad remove 7', '#a60');
  if (!name || name === 'list') { const L = Q.baAll.all(); return say(c, L.length ? 'Website ads: ' + L.map(r => '#' + r.id + ' ' + r.brand + ' (' + r.status + ')').join('; ') : 'No website ads yet.', '#a60'); }
  const r = Q.baGet.get(+arg); if (!r) return usage();
  if (name === 'view') return c.send({ t: 'partnerReview', kind: 'burn', id: r.id, name: '#' + r.id, brand: r.brand, line: r.line, link: r.link, status: r.status, wallet: r.wallet, img: 'data:image/jpeg;base64,' + r.img });
  const note = rest.split(' ').slice(2).join(' ').slice(0, 120);
  if (name === 'approve') { if (r.status !== 'pending') return say(c, 'Ad #' + r.id + ' is ' + r.status + '.', '#c00'); Q.baStatus.run('approved', '', now(), r.id); }
  else if (name === 'reject') Q.baStatus.run('rejected', note || 'Please change the ad and send it again.', 0, r.id);
  else if (name === 'remove') Q.baDel.run(r.id);
  else return usage();
  say(c, 'Website ad #' + r.id + ': ' + name + (name === 'approve' ? 'd. The buyer can burn now; it goes live when the burn checks out.' : name === 'reject' ? 'ed. Nothing was burned.' : 'd.'), '#0a0');
}
// once a day at a random hour, every linked wallet is checked again (up to 20 a minute); partners every 15 minutes
let walBusy = false;
setInterval(async () => {
  if (!CAPES_MINT || walBusy) return; walBusy = true;
  try { for (const row of Q.walDue.all(now())) { await holderCheck(row); const o = online.get(row.uid); if (o) o.send(holderInfo(row.uid)); } partnersMaybeChanged(); } finally { walBusy = false; }
}, SWEEP);

function adminCmd(c, raw) {
  const [cmd, name, arg] = raw.slice(1).split(' '); const rest = raw.split(' ').slice(1).join(' ');
  const u = name && Q.byName.get(name);
  const o = u && online.get(u.id);
  switch (cmd) {
    case 'announce': return broadcast({ t: 'notice', text: cleanChat(rest) });
    case 'mute': if (!u) break; Q.mute.run(now() + (+arg || 60) * 60e3, u.id); return say(c, name + ' muted for ' + (+arg || 60) + ' min.');
    case 'unmute': if (!u) break; Q.mute.run(0, u.id); return say(c, name + ' unmuted.');
    case 'ban': if (!u) break; Q.ban.run(1, u.id); Q.sesDelUser.run(u.id); if (o) { o.send({ t: 'kicked', text: 'You are banned.' }); o.close(); } return say(c, name + ' banned.');
    case 'unban': if (!u) break; Q.ban.run(0, u.id); return say(c, name + ' unbanned.');
    case 'kick': if (!o) break; o.send({ t: 'kicked', text: 'A moderator removed you from the game.' }); o.close(); return say(c, name + ' kicked.');
    case 'rollback': if (!u) break; Q.rollback.run(u.id); if (o) { o.send({ t: 'kicked', text: 'Your progress was restored by a moderator. Log in again.' }); o.close(); } return say(c, name + ' rolled back one save.');
    case 'partner': return partnerCmd(c, name, arg, rest);
    case 'burnad': return burnadCmd(c, name, arg, rest);
    case 'lp': return LP.cmd(c, name, arg);
    case 'watch': return LP.social.cmd(c, name, rest.split(' ').slice(1).join(' ').trim());
    case 'guard': return G.cmd(say, c, name, rest.split(' ').slice(1).join(' ').trim());
    case 'mod': if (!u) break; Q.setRole.run(arg === 'off' ? '' : 'mod', u.id); return say(c, name + (arg === 'off' ? ' is no longer a mod.' : ' is now a mod.'));
  }
  say(c, 'Commands: /announce text, /mute name minutes, /unmute name, /ban name, /unban name, /kick name, /rollback name, /partner list, /burnad list, /guard', '#a60');
}

function onMessage(c, msg) {
  const t = now(); c.bucket = Math.min(40, c.bucket + (t - c.bt) / 1000 * 25); c.bt = t;
  if (--c.bucket < 0) { G.strike(c.ip, 'websocket flood', 10); return c.close(); }
  let m; try { m = JSON.parse(msg); } catch (e) { return; }
  const f = m && H[m.t]; if (!f) return;
  try { const r = f(c, m); if (r && r.catch) r.catch(e => console.error('handler', m.t, e)); } catch (e) { console.error('handler', m.t, e); }
}

// ---------- ticks: positions 5 times a second, pings, cleanup, daily backup ----------
setInterval(() => {
  const all = [...online.values()].filter(o => o.pos);
  for (const c of online.values()) {
    if (!c.pos) continue;
    const p = [];
    for (const o of all) if (o !== c && Math.abs(o.pos.x - c.pos.x) <= VIEW && Math.abs(o.pos.y - c.pos.y) <= VIEW) p.push([o.uid, Math.round(o.pos.x * 100) / 100, Math.round(o.pos.y * 100) / 100, Math.round(o.pos.r * 100) / 100, o.pos.m, o.pos.a]);
    c.send({ t: 'pl', p, n: online.size });
  }
}, 200);
setInterval(() => {
  for (const c of online.values()) { if (!c.alive) { c.close(); continue; } c.alive = false; c.ping(); }
  for (const o of online.values()) if (o.trade && now() - o.trade.t > 15 * 60e3) tradeEnd(o.trade, 'The trade timed out.');
}, 25e3);
function backup() {
  const d = new Date().toISOString().slice(0, 10), f = path.join(DATA, 'backups', d + '.db');
  if (fs.existsSync(f)) return;
  try { db.exec(`VACUUM INTO '${f.replace(/'/g, "''")}'`); } catch (e) { console.error('backup', e); }
  const L = fs.readdirSync(path.join(DATA, 'backups')).filter(n => n.endsWith('.db')).sort();
  while (L.length > 14) fs.unlinkSync(path.join(DATA, 'backups', L.shift()));
  Q.sesOld.run(now() - 90 * 864e5);
}
setInterval(backup, 3600e3); setTimeout(backup, 5000);

// ---------- Launchpad (server/launchpad.js): coin pictures, metadata and the list of coins launched on memecapes.com ----------
const LP = require('./launchpad')({ db, DATA, now, tooMany, say, online, sigOk, base: process.env.RENDER_EXTERNAL_URL, G });
G.setTellAdmins(text => { for (const o of online.values()) if (o.role === 'admin') say(o, text, '#c80'); });
// ---------- MemeSnake Live (server/memesnake.js): the AI agent's public activity feed ----------
const MS = require('./memesnake')({ DATA });

// ---------- HTTP: health check, admin pages, WebSocket upgrade ----------
const server = http.createServer(async (req, res) => {
  G.headers(res);
  if (!G.http(req, res)) return;   // blocked, probing or flooding: Sentinel already answered
  let url; try { url = new URL(req.url, 'http://x'); } catch (e) { res.writeHead(400); return res.end(); }
  const json = (o, s) => { res.writeHead(s || 200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }); res.end(JSON.stringify(o, null, 1)); };
  if (url.pathname.startsWith('/lp/') || url.pathname.startsWith('/so/') || url.pathname.startsWith('/st/')) { try { if (await LP.http(req, res, url, json) !== false) return; } catch (e) { console.error('lp', e); return json({ error: 'Server error.' }, 500); } }
  if (url.pathname === '/ms/feed') { try { if (await MS.http(req, res, url, json) !== false) return; } catch (e) { console.error('ms', e); return json({ error: 'Server error.' }, 500); } }
  if (url.pathname.startsWith('/burnad')) { try { if (await baHttp(req, res, url, json) !== false) return; } catch (e) { console.error('burnad', e); return json({ error: 'Server error.' }, 500); } }
  if (url.pathname === '/' || url.pathname === '/health') return json({ ok: true, online: online.size, mode: G.mode() });
  if (url.pathname === '/guard/me') {   // your own address as the server sees it (and what the proxies sent), for checking the setup
    if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'X-Forwarded-For' }); return res.end(); }
    return json({ ip: req.ip, hops: String(req.headers['x-forwarded-for'] || '').split(',').length });
  }
  if (url.pathname === '/partners') return json(partnersLive());
  const pm = /^\/partners\/(\d+)\.jpg$/.exec(url.pathname);
  if (pm) {
    const id = +pm[1], p = Q.ptGet.get(id);
    if (!p || p.status !== 'approved' || !partnerState(id).live) return json({ error: 'not found' }, 404);
    res.writeHead(200, { 'Content-Type': 'image/jpeg', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=300' }); return res.end(Buffer.from(p.img, 'base64'));
  }
  if (url.pathname.startsWith('/admin/')) {
    if (!G.adminKeyOk(req, ADMIN_KEY)) return json({ error: 'no' }, 403);
    if (url.pathname === '/admin/guard') return json(G.status());
    if (url.pathname === '/admin/guard/mode' && req.method === 'POST') return json({ ok: G.setMode(String(url.searchParams.get('to') || ''), 'admin key', 0), mode: G.mode() });
    if (url.pathname === '/admin/stats') return json({ online: online.size, accounts: Q.count.get().n, names: [...online.values()].map(o => o.name) });
    if (url.pathname === '/admin/flags') return json(Q.listFlags.all());
    if (url.pathname === '/admin/reports') return json(Q.listReports.all());
    if (url.pathname === '/admin/holders') return json(Q.walList.all());
    if (url.pathname === '/admin/burnads') return json(Q.baAll.all());
    if (url.pathname === '/admin/partners') return json(Q.ptAll.all().map(r => ({ ...r, live: partnerState(r.uid).live })));
    if (url.pathname === '/admin/backup') { const f = path.join(DATA, 'backups', 'download.db'); try { fs.rmSync(f, { force: true }); db.exec(`VACUUM INTO '${f.replace(/'/g, "''")}'`); } catch (e) { return json({ error: String(e) }, 500); } res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Disposition': 'attachment; filename=memecapes.db' }); return fs.createReadStream(f).pipe(res); }
  }
  json({ error: 'not found' }, 404);
});
server.on('upgrade', (req, socket) => {
  const origin = req.headers.origin || '';
  let pth = ''; try { pth = new URL(req.url, 'http://x').pathname; } catch (e) { }
  if (pth !== '/ws' || (origin && !ORIGINS.includes(origin))) { socket.write('HTTP/1.1 403 Forbidden\r\n\r\n'); return socket.destroy(); }
  const ip = G.wsOpen(req); if (!ip) { socket.write('HTTP/1.1 429 Too Many Requests\r\n\r\n'); return socket.destroy(); }
  wsAccept(req, socket, ip);
});
server.listen(PORT, () => console.log('MemeCapes server on port ' + PORT + ', data in ' + DATA));
const stop = () => { try { db.close(); } catch (e) { } process.exit(0); };
process.on('SIGTERM', stop); process.on('SIGINT', stop);
