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
CREATE TABLE IF NOT EXISTS lp_reports(mint TEXT, net TEXT, ip TEXT, why TEXT, t INT);
CREATE TABLE IF NOT EXISTS lp_trades(sig TEXT, ix INT, mint TEXT, net TEXT, trader TEXT, buy INT, sol INT, tokens INT, fee INT, t INT, PRIMARY KEY(sig, ix));
CREATE INDEX IF NOT EXISTS lp_trades_mint ON lp_trades(mint, net, t);
CREATE INDEX IF NOT EXISTS lp_trades_t ON lp_trades(net, t);
CREATE TABLE IF NOT EXISTS lp_cursor(mint TEXT, net TEXT, last TEXT, PRIMARY KEY(mint, net));`);
  for (const sql of ['ALTER TABLE lp_trades ADD COLUMN slot INT', 'ALTER TABLE lp_coins ADD COLUMN slot INT']) { try { db.exec(sql); } catch (e) { } }
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
    allCoins: db.prepare('SELECT mint,net,pool FROM lp_coins WHERE hidden=0 ORDER BY t DESC LIMIT 400'),
    curGet: db.prepare('SELECT last FROM lp_cursor WHERE mint=? AND net=?'),
    curSet: db.prepare('INSERT INTO lp_cursor(mint,net,last) VALUES(?,?,?) ON CONFLICT(mint,net) DO UPDATE SET last=excluded.last'),
    trAdd: db.prepare('INSERT OR IGNORE INTO lp_trades(sig,ix,mint,net,trader,buy,sol,tokens,fee,t,slot) VALUES(?,?,?,?,?,?,?,?,?,?,?)'),
    trEarly: db.prepare('SELECT trader, buy, tokens, slot, sol FROM lp_trades WHERE mint=? AND net=? ORDER BY slot, t'),
    coinSlot: db.prepare('UPDATE lp_coins SET slot=? WHERE mint=? AND net=? AND slot IS NULL'),
    trCoin: db.prepare('SELECT * FROM lp_trades WHERE mint=? AND net=? ORDER BY t DESC LIMIT ?'),
    trFeed: db.prepare('SELECT tr.*, c.name, c.symbol, c.image FROM lp_trades tr JOIN lp_coins c ON c.mint=tr.mint AND c.net=tr.net WHERE tr.net=? AND c.hidden=0 ORDER BY tr.t DESC LIMIT ?'),
    // every wallet's SOL in and out per coin since a time: what they put in, what they took out, tokens still held
    trFlows: db.prepare(`SELECT tr.trader, tr.mint, c.name, c.symbol, c.image, SUM(CASE WHEN buy=1 THEN sol ELSE 0 END) sol_in, SUM(CASE WHEN buy=0 THEN sol ELSE 0 END) sol_out,
      SUM(CASE WHEN buy=1 THEN tokens ELSE -tokens END) held, COUNT(*) n FROM lp_trades tr JOIN lp_coins c ON c.mint=tr.mint AND c.net=tr.net
      WHERE tr.net=? AND tr.t>? AND c.hidden=0 GROUP BY tr.trader, tr.mint`),
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
      return { mint, pool, config, creator, name, symbol, uri, slot: tx.slot || 0, t: (tx.blockTime || Math.floor(now() / 1000)) * 1000 };
    }
    return { err: 'That transaction did not create a coin on the bonding curve.' };
  }

  // ---- trade feed: read each coin's swaps from the chain (the bonding-curve program's EvtSwap2 event) every 20 s
  const EVT_TAG = Buffer.from([0xe4, 0x45, 0xa5, 0x2e, 0x51, 0xcb, 0x9a, 0x1d]), EVT_SWAP2 = Buffer.from([189, 66, 51, 168, 38, 80, 117, 153]);
  const SWAP_IX = [Buffer.from([248, 198, 158, 145, 225, 117, 135, 200]), Buffer.from([65, 75, 63, 76, 235, 91, 91, 136])];
  const u64 = (d, o) => Number(d.readBigUInt64LE(o));
  function tradesIn(tx) {
    const msg = tx.transaction.message, keys = [...msg.accountKeys, ...((tx.meta.loadedAddresses || {}).writable || []), ...((tx.meta.loadedAddresses || {}).readonly || [])];
    const all = [...msg.instructions, ...((tx.meta && tx.meta.innerInstructions) || []).flatMap(x => x.instructions || [])];
    const payers = all.filter(i => keys[i.programIdIndex] === DBC).map(i => ({ d: b58d(i.data), a: i.accounts })).filter(x => x.d && SWAP_IX.some(s => x.d.subarray(0, 8).equals(s))).map(x => keys[x.a[9]]);
    const out = []; let k = 0;
    for (const i of all) {
      if (keys[i.programIdIndex] !== DBC) continue;
      const d = b58d(i.data); if (!d || d.length < 16 + 179 || !d.subarray(0, 8).equals(EVT_TAG) || !d.subarray(8, 16).equals(EVT_SWAP2)) continue;
      const e = d.subarray(16), buy = e[64] === 1;   // trade_direction 1 = SOL in, coin out
      out.push({ pool: b58e(e.subarray(0, 32)), buy, sol: buy ? u64(e, 83) : u64(e, 107), tokens: buy ? u64(e, 107) : u64(e, 83), fee: u64(e, 131), t: u64(e, 171) * 1000, trader: payers[k] || keys[0] });
      k++;
    }
    return out;
  }
  let indexing = false;
  async function indexTrades() {
    if (indexing) return; indexing = true;
    try {
      for (const c of Q.allCoins.all()) {
        const cur = Q.curGet.get(c.mint, c.net);
        let sigs; try { sigs = await rpc(c.net, 'getSignaturesForAddress', [c.pool, { limit: 100, ...(cur && cur.last ? { until: cur.last } : {}), commitment: 'confirmed' }]); } catch (e) { continue; }
        if (!sigs || !sigs.length) continue;
        for (const s of sigs.slice().reverse()) {
          if (s.err) continue;
          let tx; try { tx = await rpc(c.net, 'getTransaction', [s.signature, { encoding: 'json', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]); } catch (e) { break; }
          if (!tx) continue;
          tradesIn(tx).filter(x => x.pool === c.pool).forEach((x, i) => Q.trAdd.run(s.signature, i, c.mint, c.net, x.trader, x.buy ? 1 : 0, x.sol, x.tokens, x.fee, x.t || (s.blockTime || 0) * 1000, s.slot || tx.slot || 0));
        }
        Q.curSet.run(c.mint, c.net, sigs[0].signature);
      }
    } catch (e) { console.error('lp index', e.message); } finally { indexing = false; }
  }
  if (!process.env.LP_NO_INDEX) { setInterval(indexTrades, +process.env.LP_INDEX_MS || 20000); setTimeout(indexTrades, 5000); }
  const trPub = r => ({ sig: r.sig, mint: r.mint, trader: r.trader, buy: !!r.buy, sol: r.sol / 1e9, tokens: r.tokens / 1e6, t: r.t, name: r.name, symbol: r.symbol, image: r.image });

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
    if (p === '/lp/early' && req.method === 'GET') {
      const c = Q.coinGet.get(String(url.searchParams.get('mint') || ''), net); if (!c) return json({ error: 'not found' }, 404);
      const rows = Q.trEarly.all(c.mint, net); if (!rows.length) return json({ known: false });
      const s0 = c.slot || rows[0].slot, SUP = 1e9 * 1e6, w = new Map();
      for (const r of rows) { const e = w.get(r.trader) || { first: r.slot, bought: 0, held: 0 }; if (r.buy) e.bought += r.tokens; e.held += r.buy ? r.tokens : -r.tokens; w.set(r.trader, e); }
      const pick = f => [...w.entries()].filter(([a, e]) => a !== c.creator && f(e.first - s0));
      const sum = (L, k) => L.reduce((a, [, e]) => a + Math.max(0, e[k]), 0) / SUP * 100;
      const bundle = pick(d => d <= 0), snipe = pick(d => d > 0 && d <= 3), dev = w.get(c.creator);
      return json({ known: true, launchSlot: s0, dev: dev ? { bought: dev.bought / SUP * 100, held: Math.max(0, dev.held) / SUP * 100 } : null,
        bundled: { wallets: bundle.length, boughtPct: sum(bundle, 'bought'), heldPct: sum(bundle, 'held') },
        snipers: { wallets: snipe.length, boughtPct: sum(snipe, 'bought'), heldPct: sum(snipe, 'held') } });
    }
    if (p === '/lp/trades' && req.method === 'GET') {
      const lim = Math.max(1, Math.min(200, +url.searchParams.get('limit') || 50)), mint = url.searchParams.get('mint');
      return json({ trades: (mint ? Q.trCoin.all(String(mint), net, lim) : Q.trFeed.all(net, lim)).map(trPub) });
    }
    // who is up and who is down: SOL taken out minus SOL put in, per wallet per coin (tokens still held listed separately)
    if (p === '/lp/leaders' && req.method === 'GET') {
      const since = now() - (url.searchParams.get('range') === 'week' ? 7 : 1) * 864e5;
      const rows = Q.trFlows.all(net, since).map(r => ({ trader: r.trader, mint: r.mint, name: r.name, symbol: r.symbol, image: r.image, solIn: r.sol_in / 1e9, solOut: r.sol_out / 1e9, net: (r.sol_out - r.sol_in) / 1e9, held: Math.max(0, r.held) / 1e6, trades: r.n }));
      rows.sort((a, b) => b.net - a.net);
      return json({ top: rows.slice(0, 25), bottom: rows.slice(-10).reverse(), since });
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
      Q.coinAdd.run(v.mint, bnet, v.pool, v.config, v.creator, clean(v.name, 32), clean(v.symbol, 10), v.uri.slice(0, 200), image, sig, v.t); Q.coinSlot.run(v.slot, v.mint, bnet);
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
