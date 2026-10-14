'use strict';
// MemeCapes Launchpad, server side: coin pictures and metadata, the list of coins launched from memecapes.com,
// reports and the "Verified" badge. The server never holds a wallet key and never sends a transaction: coins are
// created on Solana by the launcher's own wallet; the server only checks on-chain that a launch really happened.
//
//   POST /lp/upload     {name, symbol, description, website, x, telegram, image: data URL}  -> {uri, image}
//   GET  /lp/meta/<id>.json, /lp/img/<id>.<ext>   the token metadata and picture wallets and explorers read
//   POST /lp/register   {sig, net}   the launch transaction; checked on-chain, then listed
//   GET  /lp/coins?net=&sort=new|verified&limit=  the coins launched here (newest first)
//   GET  /lp/coin/<mint>?net=                      one coin
//   POST /lp/report     {mint, why}
//   admin (in game): /lp list | verify <mint> | unverify <mint> | hide <mint> | show <mint>
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const DBC = 'dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN';
const INIT_SPL = Buffer.from([140, 85, 215, 176, 102, 54, 104, 79]);   // initialize_virtual_pool_with_spl_token
const B58A = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function b58e(u8) { let x = 0n; for (const b of u8) x = x * 256n + BigInt(b); let s = ''; while (x > 0n) { s = B58A[Number(x % 58n)] + s; x /= 58n; } for (const b of u8) { if (b) break; s = '1' + s; } return s; }
function b58d(s) { let x = 0n; for (const ch of String(s)) { const i = B58A.indexOf(ch); if (i < 0) return null; x = x * 58n + BigInt(i); } const out = []; while (x > 0n) { out.unshift(Number(x & 255n)); x >>= 8n; } for (const ch of String(s)) { if (ch !== '1') break; out.unshift(0); } return Buffer.from(out); }

module.exports = function launchpad({ db, DATA, now, tooMany, say, online, base }) {
  const PARTNER = process.env.LP_PARTNER || '';                 // the MemeCapes launchpad fee wallet (public address); empty = registrations off
  const PARTNER_DEV = process.env.LP_PARTNER_DEVNET || PARTNER;
  const CREATOR_MAX = +process.env.LP_CREATOR_MAX || 80;      // most a launcher can keep, in % of the fee after Meteora's cut (same as config.js)
  const RPCS = { mainnet: process.env.SOLANA_RPC || 'https://api.mainnet-beta.solana.com', devnet: process.env.SOLANA_RPC_DEVNET || 'https://api.devnet.solana.com' };
  const PUBLIC = (process.env.PUBLIC_URL || base || 'https://memecapes-server.onrender.com').replace(/\/$/, '');
  const IMG_DIR = path.join(DATA, 'lp');
  fs.mkdirSync(IMG_DIR, { recursive: true });

  db.exec(`CREATE TABLE IF NOT EXISTS lp_meta(id TEXT PRIMARY KEY, json TEXT, img TEXT, ip TEXT, t INT);
CREATE TABLE IF NOT EXISTS lp_coins(mint TEXT, net TEXT, pool TEXT, config TEXT, creator TEXT, name TEXT, symbol TEXT, uri TEXT, image TEXT,
  sig TEXT UNIQUE, t INT, verified INT DEFAULT 0, hidden INT DEFAULT 0, reports INT DEFAULT 0, PRIMARY KEY(mint, net));
CREATE TABLE IF NOT EXISTS lp_reports(mint TEXT, net TEXT, ip TEXT, why TEXT, t INT);`);
  const Q = {
    metaAdd: db.prepare('INSERT INTO lp_meta(id,json,img,ip,t) VALUES(?,?,?,?,?)'),
    metaGet: db.prepare('SELECT * FROM lp_meta WHERE id=?'),
    metaByIp: db.prepare('SELECT COUNT(*) n FROM lp_meta WHERE ip=? AND t>?'),
    coinAdd: db.prepare('INSERT OR IGNORE INTO lp_coins(mint,net,pool,config,creator,name,symbol,uri,image,sig,t) VALUES(?,?,?,?,?,?,?,?,?,?,?)'),
    coinGet: db.prepare('SELECT * FROM lp_coins WHERE mint=? AND net=?'),
    coinsNew: db.prepare('SELECT * FROM lp_coins WHERE net=? AND hidden=0 ORDER BY t DESC LIMIT ?'),
    coinsVer: db.prepare('SELECT * FROM lp_coins WHERE net=? AND hidden=0 AND verified=1 ORDER BY t DESC LIMIT ?'),
    coinsBy: db.prepare('SELECT * FROM lp_coins WHERE net=? AND creator=? ORDER BY t DESC LIMIT 100'),
    coinSet: (col) => db.prepare(`UPDATE lp_coins SET ${col}=? WHERE mint=?`),
    repAdd: db.prepare('INSERT INTO lp_reports(mint,net,ip,why,t) VALUES(?,?,?,?,?)'),
    repSeen: db.prepare('SELECT COUNT(*) n FROM lp_reports WHERE mint=? AND ip=?'),
    repInc: db.prepare('UPDATE lp_coins SET reports=reports+1 WHERE mint=? AND net=?'),
    list: db.prepare('SELECT mint,net,name,symbol,verified,hidden,reports,t FROM lp_coins ORDER BY t DESC LIMIT 30'),
  };
  const SET = { verified: Q.coinSet('verified'), hidden: Q.coinSet('hidden') };

  async function rpc(net, method, params) {
    const r = await fetch(RPCS[net] || RPCS.mainnet, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }), signal: AbortSignal.timeout(15000) });
    const j = await r.json(); if (j.error) throw new Error(j.error.message || 'rpc error'); return j.result;
  }
  const clean = (s, n) => String(s == null ? '' : s).replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, n);
  const link = (s) => { s = String(s || '').trim(); return /^https:\/\/[a-z0-9.-]+\.[a-z]{2,}(\/[^\s<>"']*)?$/i.test(s) ? s.slice(0, 200) : ''; };
  const pub = (r) => ({ mint: r.mint, pool: r.pool, config: r.config, creator: r.creator, name: r.name, symbol: r.symbol, uri: r.uri, image: r.image, t: r.t, verified: !!r.verified, reports: r.reports | 0, net: r.net });
  const body = (req, max) => new Promise((ok, no) => { let n = 0; const parts = []; req.on('data', d => { n += d.length; if (n > max) { no(new Error('too big')); req.destroy(); } else parts.push(d); }); req.on('end', () => { try { ok(JSON.parse(Buffer.concat(parts).toString('utf8') || '{}')); } catch (e) { no(e); } }); req.on('error', no); });
  const IMG = { 'image/png': ['png', b => b[0] === 0x89 && b[1] === 0x50], 'image/jpeg': ['jpg', b => b[0] === 0xff && b[1] === 0xd8], 'image/webp': ['webp', b => b.slice(8, 12).toString() === 'WEBP'], 'image/gif': ['gif', b => b.slice(0, 3).toString() === 'GIF'] };

  // check a launch on-chain: the transaction ran the bonding-curve "create pool" instruction, with a config whose fee
  // wallet is ours (so the coin was launched through memecapes.com and its fees follow the published split)
  async function verifyLaunch(net, sig) {
    const tx = await rpc(net, 'getTransaction', [sig, { encoding: 'json', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]);
    if (!tx) return { err: 'That launch was not found on the blockchain yet. Wait a few seconds and try again.' };
    if (tx.meta && tx.meta.err) return { err: 'That transaction failed.' };
    const msg = tx.transaction.message, keys = [...msg.accountKeys, ...((tx.meta.loadedAddresses || {}).writable || []), ...((tx.meta.loadedAddresses || {}).readonly || [])];
    for (const ix of msg.instructions) {
      if (keys[ix.programIdIndex] !== DBC) continue;
      const data = b58d(ix.data); if (!data || !data.subarray(0, 8).equals(INIT_SPL)) continue;
      const a = ix.accounts.map(i => keys[i]);   // config, pool_authority, creator, base_mint, quote_mint, pool, ...
      const [config, , creator, mint, , pool] = a;
      const ci = await rpc(net, 'getAccountInfo', [config, { encoding: 'base64', commitment: 'confirmed' }]);
      const cd = ci && ci.value && Buffer.from(ci.value.data[0], 'base64');
      if (!cd || ci.value.owner !== DBC) return { err: 'The coin\'s config was not found.' };
      const feeClaimer = b58e(cd.subarray(40, 72)), want = net === 'devnet' ? PARTNER_DEV : PARTNER;
      if (!want || feeClaimer !== want) return { err: 'That coin was not launched through the MemeCapes launchpad.' };
      // the published fee split: the launcher's share of the trading fee (offset 245 of the config) stays within the limit
      if (cd.length < 1048 || cd[245] > CREATOR_MAX) return { err: 'That coin\'s fee split is outside what the MemeCapes launchpad allows.' };
      // name, symbol and uri are the first three borsh strings of the instruction's params
      let o = 8; const str = () => { const n = data.readUInt32LE(o); o += 4; const s = data.subarray(o, o + n).toString('utf8'); o += n; return s; };
      const name = str(), symbol = str(), uri = str();
      return { mint, pool, config, creator, name, symbol, uri, t: (tx.blockTime || Math.floor(now() / 1000)) * 1000 };
    }
    return { err: 'That transaction did not create a coin on the bonding curve.' };
  }

  async function http(req, res, url, json) {
    const p = url.pathname, ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
    const net = url.searchParams.get('net') === 'devnet' ? 'devnet' : 'mainnet';
    if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET', 'Access-Control-Allow-Headers': 'Content-Type' }); return res.end(); }
    let m;
    if ((m = /^\/lp\/meta\/([a-f0-9]{24})\.json$/.exec(p))) {
      const r = Q.metaGet.get(m[1]); if (!r) return json({ error: 'not found' }, 404);
      res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=31536000, immutable' }); return res.end(r.json);
    }
    if ((m = /^\/lp\/img\/([a-f0-9]{24})\.(png|jpg|webp|gif)$/.exec(p))) {
      const f = path.join(IMG_DIR, m[1] + '.' + m[2]); if (!fs.existsSync(f)) return json({ error: 'not found' }, 404);
      const type = Object.keys(IMG).find(k => IMG[k][0] === m[2]);
      res.writeHead(200, { 'Content-Type': type, 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=31536000, immutable' }); return fs.createReadStream(f).pipe(res);
    }
    if (p === '/lp/coins' && req.method === 'GET') {
      const lim = Math.max(1, Math.min(200, +url.searchParams.get('limit') || 60));
      const rows = url.searchParams.get('sort') === 'verified' ? Q.coinsVer.all(net, lim) : url.searchParams.get('creator') ? Q.coinsBy.all(net, String(url.searchParams.get('creator'))) : Q.coinsNew.all(net, lim);
      return json({ coins: rows.map(pub), partner: net === 'devnet' ? PARTNER_DEV : PARTNER });
    }
    if ((m = /^\/lp\/coin\/([1-9A-HJ-NP-Za-km-z]{32,44})$/.exec(p))) { const r = Q.coinGet.get(m[1], net); return r && !r.hidden ? json(pub(r)) : json({ error: 'not found' }, 404); }
    if (req.method !== 'POST') return false;
    let b; try { b = await body(req, 3 * 1024 * 1024); } catch (e) { return json({ error: 'That is too big. Pictures up to 2 MB.' }, 400); }
    const bnet = b.net === 'devnet' ? 'devnet' : 'mainnet';
    if (p === '/lp/upload') {
      if (tooMany('lpu' + ip) || Q.metaByIp.get(ip, now() - 3600e3).n >= 30) return json({ error: 'Too many uploads. Wait a while.' }, 429);
      const name = clean(b.name, 32), symbol = clean(b.symbol, 10).replace(/\s/g, '').toUpperCase();
      if (name.length < 2) return json({ error: 'Give your coin a name (2 to 32 letters).' }, 400);
      if (!/^[A-Z0-9$]{2,10}$/.test(symbol)) return json({ error: 'The ticker must be 2 to 10 letters or numbers.' }, 400);
      const mm = /^data:(image\/(?:png|jpeg|webp|gif));base64,([A-Za-z0-9+/=]+)$/.exec(String(b.image || ''));
      if (!mm) return json({ error: 'Add a picture (PNG, JPEG, WebP or GIF).' }, 400);
      const raw = Buffer.from(mm[2], 'base64'), t = IMG[mm[1]];
      if (raw.length > 2 * 1024 * 1024 || !t[1](raw)) return json({ error: 'That picture could not be used. PNG, JPEG, WebP or GIF up to 2 MB.' }, 400);
      const id = crypto.randomBytes(12).toString('hex'), image = PUBLIC + '/lp/img/' + id + '.' + t[0];
      fs.writeFileSync(path.join(IMG_DIR, id + '.' + t[0]), raw);
      const meta = { name, symbol, description: clean(b.description, 600), image, showName: true, createdOn: 'https://memecapes.com/launch.html',
        website: link(b.website), twitter: link(b.x), telegram: link(b.telegram),
        properties: { files: [{ uri: image, type: mm[1] }], category: 'image' } };
      Object.keys(meta).forEach(k => meta[k] === '' && delete meta[k]);
      // the launcher's published plan for their share of the fees: up to 10 wallets and a % each (paid by the page on every claim)
      const routes = (Array.isArray(b.plan && b.plan.routes) ? b.plan.routes : []).slice(0, 10)
        .map(r => ({ to: String(r.to || '').trim(), pct: Math.floor(+r.pct || 0) }))
        .filter(r => r.pct > 0 && r.pct <= 100 && (b58d(r.to) || []).length === 32);
      if (routes.reduce((a, r) => a + r.pct, 0) > 100) return json({ error: 'Your split adds up to more than 100%.' }, 400);
      meta.memecapes = { launchpad: 'MemeCapes', routes };
      const js = JSON.stringify(meta); Q.metaAdd.run(id, js, image, ip, now());
      return json({ uri: PUBLIC + '/lp/meta/' + id + '.json', image });
    }
    if (p === '/lp/register') {
      const sig = String(b.sig || '').trim(); if (!/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(sig)) return json({ error: 'Bad transaction signature.' }, 400);
      if (tooMany('lpr' + ip)) return json({ error: 'Too many tries. Wait a few minutes.' }, 429);
      let v = null; for (let i = 0; i < 4; i++) { try { v = await verifyLaunch(bnet, sig); } catch (e) { v = { err: 'Could not reach the blockchain.' }; } if (!/not found|reach/.test(v.err || '')) break; await new Promise(r => setTimeout(r, 2500)); }
      if (v.err) return json({ error: v.err }, 400);
      let image = ''; try { const mm2 = /\/lp\/meta\/([a-f0-9]{24})\.json$/.exec(v.uri); const r = mm2 && Q.metaGet.get(mm2[1]); image = r ? r.img : ''; } catch (e) { }
      Q.coinAdd.run(v.mint, bnet, v.pool, v.config, v.creator, clean(v.name, 32), clean(v.symbol, 10), v.uri.slice(0, 200), image, sig, v.t);
      for (const o of online.values()) if (o.role === 'admin') say(o, 'New launchpad coin: ' + clean(v.name, 32) + ' ($' + clean(v.symbol, 10) + ')' + (bnet === 'devnet' ? ' [devnet]' : ''), '#c80');
      return json({ ok: true, coin: pub(Q.coinGet.get(v.mint, bnet)) });
    }
    if (p === '/lp/report') {
      const mint = String(b.mint || ''); const r = Q.coinGet.get(mint, bnet); if (!r) return json({ error: 'not found' }, 404);
      if (Q.repSeen.get(mint, ip).n) return json({ ok: true });
      Q.repAdd.run(mint, bnet, ip, clean(b.why, 300), now()); Q.repInc.run(mint, bnet);
      for (const o of online.values()) if (o.role === 'admin') say(o, 'Launchpad report on ' + r.name + ': ' + clean(b.why, 120), '#c00');
      return json({ ok: true });
    }
    return json({ error: 'not found' }, 404);
  }

  function cmd(c, arg, mint) {
    if (!arg || arg === 'list') { const L = Q.list.all(); return say(c, L.length ? 'Launchpad: ' + L.map(r => r.name + ' $' + r.symbol + (r.verified ? ' ✓' : '') + (r.hidden ? ' (hidden)' : '') + (r.reports ? ' [' + r.reports + ' reports]' : '') + (r.net === 'devnet' ? ' [dev]' : '') + ' ' + r.mint.slice(0, 6)).join('; ') : 'No launchpad coins yet.', '#a60'); }
    const full = Q.list.all().find(r => r.mint.startsWith(mint || '-'));
    if (!full) return say(c, 'Usage: /lp list, /lp verify <mint start>, /lp unverify ..., /lp hide ..., /lp show ...', '#a60');
    if (arg === 'verify') SET.verified.run(1, full.mint); else if (arg === 'unverify') SET.verified.run(0, full.mint);
    else if (arg === 'hide') SET.hidden.run(1, full.mint); else if (arg === 'show') SET.hidden.run(0, full.mint);
    else return say(c, 'Usage: /lp list, /lp verify <mint start>, /lp unverify ..., /lp hide ..., /lp show ...', '#a60');
    say(c, full.name + ': ' + arg + ' done.', '#0a0');
  }
  return { http, cmd };
};
