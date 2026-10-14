'use strict';
// MemeCapes Watch and Stream, server side: wallet sign-in (a signed message, never a transaction), profiles, posts and
// likes, the "what's happening" feed (launches, whale buys, graduations, streams, posts), channels, go-live through
// Cloudflare Stream, chat, and tips and subscriptions that are paid wallet to wallet and only checked here.
// The server never holds anyone's money or keys.
//
//   POST /so/nonce {wallet}             -> {msg}          POST /so/login {wallet, sig} -> {token}
//   GET  /so/me                          (signed in)       POST /so/profile {name, about, x, avatar}
//   GET  /so/u/<wallet>                  profile + trading stats + posts
//   POST /so/post {text, mint, reply}    POST /so/like {post}       POST /so/follow {wallet, on}
//   GET  /so/feed?kind=all|posts|launches|whales|grads|live&mint=&wallet=&limit=
//   GET  /so/trending                    coins by the last hour, plus "right now" counters
//   GET  /st/live                        POST /st/channel {name, about, category, subSol}
//   GET  /st/ch/<wallet>                 POST /st/golive {title, category, mode, mint}   POST /st/end
//   POST /st/watch {channel}             GET /st/chat?channel=&after=    POST /st/chat {channel, text}
//   POST /st/tip {channel, sig}          POST /st/sub {channel, sig}
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

module.exports = function social({ db, now, tooMany, sigOk, say, online, rpc, b58d, PUBLIC, IMG_DIR, coinGet, netOf }) {
  const WHALE = +process.env.LP_WHALE_SOL || 1;                      // a buy this big (SOL) is a "whale buy" in the feed
  const CF = { acct: process.env.CF_ACCOUNT_ID || '', token: process.env.CF_STREAM_TOKEN || '', code: process.env.CF_CUSTOMER_CODE || '' };
  const STREAMING = !!(CF.acct && CF.token);
  const MEMO = 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr';
  // the streamer pass: a flat monthly fee, paid in SOL from the streamer's wallet to the MemeCapes wallet below,
  // checked on-chain like a tip. The price in USD and the wallet come from the site's config.js (Render env wins).
  const cfgNum = (k, d) => { try { const m = new RegExp(k + ':\\s*([0-9.]+)').exec(fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8')); return m ? +m[1] : d; } catch (e) { return d; } };
  const cfgStr = (k) => { try { const m = new RegExp(k + ':\\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"').exec(fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8')); return m ? m[1] : ''; } catch (e) { return ''; } };
  const PASS = { usd: process.env.STREAM_PASS_USD != null ? +process.env.STREAM_PASS_USD : cfgNum('streamPassUsd', 20), days: cfgNum('streamPassDays', 30), to: process.env.STREAM_PASS_WALLET || cfgStr('streamPassWallet') || process.env.LP_PARTNER || cfgStr('partner') };
  console.log('streamer pass: $' + PASS.usd + ' for ' + PASS.days + ' days -> ' + (PASS.to || 'no wallet set (streaming free)'));
  let solUsd = { v: 0, t: 0 };
  async function solPrice() {
    if (now() - solUsd.t < 60e3 && solUsd.v) return solUsd.v;
    try { const j = await (await fetch('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd', { signal: AbortSignal.timeout(8000) })).json(); if (j.solana && j.solana.usd > 1) solUsd = { v: j.solana.usd, t: now() }; } catch (e) { }
    return solUsd.v || cfgNum('solUsdFallback', 150);
  }
  const quotes = new Map();   // wallet -> {sol, t}: the SOL amount we showed, honoured for 15 minutes

  db.exec(`CREATE TABLE IF NOT EXISTS so_sessions(token TEXT PRIMARY KEY, wallet TEXT, t INT);
CREATE TABLE IF NOT EXISTS so_profiles(wallet TEXT PRIMARY KEY, name TEXT, about TEXT, x TEXT, avatar TEXT, t INT);
CREATE TABLE IF NOT EXISTS so_posts(id INTEGER PRIMARY KEY, wallet TEXT, text TEXT, mint TEXT, reply INT DEFAULT 0, t INT, likes INT DEFAULT 0, replies INT DEFAULT 0, hidden INT DEFAULT 0);
CREATE INDEX IF NOT EXISTS so_posts_t ON so_posts(t);
CREATE TABLE IF NOT EXISTS so_likes(post INT, wallet TEXT, PRIMARY KEY(post, wallet));
CREATE TABLE IF NOT EXISTS so_follows(wallet TEXT, target TEXT, PRIMARY KEY(wallet, target));
CREATE TABLE IF NOT EXISTS so_events(id INTEGER PRIMARY KEY, kind TEXT, mint TEXT, net TEXT, wallet TEXT, sol REAL, data TEXT, t INT);
CREATE INDEX IF NOT EXISTS so_events_t ON so_events(net, t);
CREATE TABLE IF NOT EXISTS so_channels(wallet TEXT PRIMARY KEY, name TEXT, about TEXT, category TEXT, subSol REAL DEFAULT 0.1, live INT DEFAULT 0, title TEXT, mode TEXT,
  playKind TEXT, playUrl TEXT, cfUid TEXT, mint TEXT, startedAt INT, t INT, hidden INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS so_chat(id INTEGER PRIMARY KEY, channel TEXT, wallet TEXT, text TEXT, t INT);
CREATE INDEX IF NOT EXISTS so_chat_c ON so_chat(channel, id);
CREATE TABLE IF NOT EXISTS so_tips(sig TEXT PRIMARY KEY, channel TEXT, wallet TEXT, sol REAL, t INT);
CREATE TABLE IF NOT EXISTS so_subs(channel TEXT, wallet TEXT, until INT, sig TEXT, sol REAL, PRIMARY KEY(channel, wallet));
CREATE TABLE IF NOT EXISTS so_pass(wallet TEXT PRIMARY KEY, until INT, t INT);
CREATE TABLE IF NOT EXISTS so_pass_pay(sig TEXT PRIMARY KEY, wallet TEXT, sol REAL, usd REAL, days INT, t INT);`);
  const Q = {
    sesAdd: db.prepare('INSERT INTO so_sessions(token,wallet,t) VALUES(?,?,?)'), sesGet: db.prepare('SELECT wallet FROM so_sessions WHERE token=? AND t>?'),
    profGet: db.prepare('SELECT * FROM so_profiles WHERE wallet=?'),
    profSet: db.prepare('INSERT INTO so_profiles(wallet,name,about,x,avatar,t) VALUES(?,?,?,?,?,?) ON CONFLICT(wallet) DO UPDATE SET name=excluded.name,about=excluded.about,x=excluded.x,avatar=COALESCE(excluded.avatar,so_profiles.avatar),t=excluded.t'),
    postAdd: db.prepare('INSERT INTO so_posts(wallet,text,mint,reply,t) VALUES(?,?,?,?,?)'), postGet: db.prepare('SELECT * FROM so_posts WHERE id=?'),
    postReplies: db.prepare('UPDATE so_posts SET replies=replies+1 WHERE id=?'),
    postsFeed: db.prepare('SELECT * FROM so_posts WHERE hidden=0 AND reply=0 AND (?1 IS NULL OR mint=?1) AND (?2 IS NULL OR wallet=?2) ORDER BY t DESC LIMIT ?3'),
    postsReply: db.prepare('SELECT * FROM so_posts WHERE reply=? AND hidden=0 ORDER BY t LIMIT 50'),
    postsByIp: db.prepare('SELECT COUNT(*) n FROM so_posts WHERE wallet=? AND t>?'),
    likeAdd: db.prepare('INSERT OR IGNORE INTO so_likes(post,wallet) VALUES(?,?)'), likeDel: db.prepare('DELETE FROM so_likes WHERE post=? AND wallet=?'),
    likeHas: db.prepare('SELECT 1 FROM so_likes WHERE post=? AND wallet=?'), likeN: db.prepare('UPDATE so_posts SET likes=(SELECT COUNT(*) FROM so_likes WHERE post=?1) WHERE id=?1'),
    folAdd: db.prepare('INSERT OR IGNORE INTO so_follows(wallet,target) VALUES(?,?)'), folDel: db.prepare('DELETE FROM so_follows WHERE wallet=? AND target=?'),
    folOf: db.prepare('SELECT target FROM so_follows WHERE wallet=?'), folN: db.prepare('SELECT COUNT(*) n FROM so_follows WHERE target=?'),
    evAdd: db.prepare('INSERT INTO so_events(kind,mint,net,wallet,sol,data,t) VALUES(?,?,?,?,?,?,?)'),
    evFeed: db.prepare('SELECT * FROM so_events WHERE net=? AND (?2 IS NULL OR kind=?2) AND (?3 IS NULL OR mint=?3) AND (?4 IS NULL OR wallet=?4) ORDER BY t DESC LIMIT ?5'),
    evSince: db.prepare('SELECT kind, COUNT(*) n FROM so_events WHERE net=? AND t>? GROUP BY kind'),
    chGet: db.prepare('SELECT * FROM so_channels WHERE wallet=?'), chLive: db.prepare('SELECT * FROM so_channels WHERE live=1 AND hidden=0 ORDER BY startedAt DESC'),
    chByMint: db.prepare('SELECT * FROM so_channels WHERE live=1 AND hidden=0 AND mint=?'),
    chSet: db.prepare('INSERT INTO so_channels(wallet,name,about,category,subSol,t) VALUES(?,?,?,?,?,?) ON CONFLICT(wallet) DO UPDATE SET name=excluded.name,about=excluded.about,category=excluded.category,subSol=excluded.subSol'),
    chLiveSet: db.prepare('UPDATE so_channels SET live=1,title=?,category=?,mode=?,playKind=?,playUrl=?,cfUid=?,mint=?,startedAt=? WHERE wallet=?'),
    chEnd: db.prepare('UPDATE so_channels SET live=0,playUrl=NULL,cfUid=NULL,mint=NULL WHERE wallet=?'),
    chAll: db.prepare('SELECT wallet,name,category,live FROM so_channels WHERE hidden=0 ORDER BY live DESC, t DESC LIMIT 60'),
    chatAdd: db.prepare('INSERT INTO so_chat(channel,wallet,text,t) VALUES(?,?,?,?)'), chatGet: db.prepare('SELECT * FROM so_chat WHERE channel=? AND id>? ORDER BY id LIMIT 80'),
    tipAdd: db.prepare('INSERT OR IGNORE INTO so_tips(sig,channel,wallet,sol,t) VALUES(?,?,?,?,?)'), tipsOf: db.prepare('SELECT wallet,sol,t FROM so_tips WHERE channel=? ORDER BY t DESC LIMIT 20'),
    tipSum: db.prepare('SELECT COALESCE(SUM(sol),0) s, COUNT(*) n FROM so_tips WHERE channel=?'), tipSig: db.prepare('SELECT 1 FROM so_tips WHERE sig=?'),
    subSet: db.prepare('INSERT INTO so_subs(channel,wallet,until,sig,sol) VALUES(?,?,?,?,?) ON CONFLICT(channel,wallet) DO UPDATE SET until=excluded.until,sig=excluded.sig,sol=excluded.sol'),
    subN: db.prepare('SELECT COUNT(*) n FROM so_subs WHERE channel=? AND until>?'), subHas: db.prepare('SELECT until FROM so_subs WHERE channel=? AND wallet=? AND until>?'), subSig: db.prepare('SELECT 1 FROM so_subs WHERE sig=?'),
    passGet: db.prepare('SELECT until FROM so_pass WHERE wallet=?'), passSet: db.prepare('INSERT INTO so_pass(wallet,until,t) VALUES(?,?,?) ON CONFLICT(wallet) DO UPDATE SET until=excluded.until,t=excluded.t'),
    passPay: db.prepare('INSERT INTO so_pass_pay(sig,wallet,sol,usd,days,t) VALUES(?,?,?,?,?,?)'), passSig: db.prepare('SELECT 1 FROM so_pass_pay WHERE sig=?'),
    trStats: db.prepare('SELECT COUNT(*) n, COUNT(DISTINCT mint) coins, SUM(CASE WHEN buy=1 THEN sol ELSE 0 END) sin, SUM(CASE WHEN buy=0 THEN sol ELSE 0 END) sout FROM lp_trades WHERE trader=? AND net=?'),
    trHour: db.prepare('SELECT COUNT(*) n, COUNT(DISTINCT trader) w, COALESCE(SUM(sol),0) v FROM lp_trades WHERE net=? AND t>?'),
    trTrend: db.prepare(`SELECT tr.mint, c.name, c.symbol, c.image, COUNT(*) n, COUNT(DISTINCT tr.trader) w, SUM(tr.sol) v, SUM(CASE WHEN buy=1 THEN sol ELSE -sol END) flow
      FROM lp_trades tr JOIN lp_coins c ON c.mint=tr.mint AND c.net=tr.net WHERE tr.net=? AND tr.t>? AND c.hidden=0 GROUP BY tr.mint ORDER BY v DESC LIMIT 12`),
    coinsNew: db.prepare('SELECT COUNT(*) n FROM lp_coins WHERE net=? AND t>? AND hidden=0'),
  };
  const nonces = new Map(), watchers = new Map();   // wallet -> {msg, t};  channel -> Map(ip -> t)
  const clean = (s, n) => String(s == null ? '' : s).replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, n);
  const isW = w => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(w || '') && (b58d(w) || []).length === 32;
  const link = (s) => { s = String(s || '').trim(); return /^https:\/\/[a-z0-9.-]+\.[a-z]{2,}(\/[^\s<>"']*)?$/i.test(s) ? s.slice(0, 200) : ''; };
  const body = (req, max) => new Promise((ok, no) => { let n = 0; const parts = []; req.on('data', d => { n += d.length; if (n > max) { no(new Error('too big')); req.destroy(); } else parts.push(d); }); req.on('end', () => { try { ok(JSON.parse(Buffer.concat(parts).toString('utf8') || '{}')); } catch (e) { no(e); } }); req.on('error', no); });
  const who = (req) => { const m = /^Bearer ([a-f0-9]{48})$/.exec(req.headers.authorization || ''); const r = m && Q.sesGet.get(m[1], now() - 30 * 864e5); return r ? r.wallet : ''; };
  const prof = (w) => { const p = Q.profGet.get(w) || {}; return { wallet: w, name: p.name || '', about: p.about || '', x: p.x || '', avatar: p.avatar || '' }; };
  const chPub = (c) => c ? { wallet: c.wallet, name: c.name, about: c.about, category: c.category, subSol: c.subSol, live: !!c.live, title: c.title, mode: c.mode, playKind: c.playKind, playUrl: c.playUrl, mint: c.mint, startedAt: c.startedAt, viewers: viewersOf(c.wallet) } : null;
  const passUntil = (w) => { const r = Q.passGet.get(w); return r ? r.until : 0; };
  const passOn = (w) => !PASS.to || PASS.usd <= 0 || passUntil(w) > now();   // no wallet or $0 = streaming is free
  function viewersOf(ch) { const m = watchers.get(ch); if (!m) return 0; const cut = now() - 70e3; for (const [k, t] of m) if (t < cut) m.delete(k); return m.size; }
  function coinOf(mint, net) { const c = mint && coinGet.get(mint, net); return c ? { mint: c.mint, name: c.name, symbol: c.symbol, image: c.image } : null; }

  // the feed's raw material: launchpad.js calls this for launches, whale buys and graduations; streams and tips add their own
  function event(e) { try { Q.evAdd.run(e.kind, e.mint || '', e.net || 'mainnet', e.wallet || '', e.sol || 0, e.data ? JSON.stringify(e.data) : '', e.t || now()); } catch (er) { } }

  async function cfCreate(name) {
    const r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${CF.acct}/stream/live_inputs`, { method: 'POST', headers: { Authorization: 'Bearer ' + CF.token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ meta: { name }, recording: { mode: 'automatic', timeoutSeconds: 30 }, deleteRecordingAfterDays: 7 }), signal: AbortSignal.timeout(15000) });
    const j = await r.json(); if (!j.success) throw new Error((j.errors && j.errors[0] && j.errors[0].message) || 'Cloudflare said no');
    return j.result;
  }
  async function cfDelete(uid) { try { await fetch(`https://api.cloudflare.com/client/v4/accounts/${CF.acct}/stream/live_inputs/${uid}`, { method: 'DELETE', headers: { Authorization: 'Bearer ' + CF.token }, signal: AbortSignal.timeout(10000) }); } catch (e) { } }
  // a payment to a channel: the signer sent at least `min` SOL to the channel wallet, with our memo, in a confirmed transaction
  async function checkPay(net, sig, to, min) {
    const tx = await rpc(net, 'getTransaction', [sig, { encoding: 'jsonParsed', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]);
    if (!tx) return { err: 'Not found yet. Wait a few seconds and try again.' };
    if (tx.meta && tx.meta.err) return { err: 'That transaction failed, so nothing was paid.' };
    const keys = tx.transaction.message.accountKeys.map(k => k.pubkey || k), i = keys.indexOf(to);
    if (i < 0) return { err: 'That transaction did not pay this channel.' };
    const sol = (tx.meta.postBalances[i] - tx.meta.preBalances[i]) / 1e9;
    if (sol < min - 1e-9) return { err: 'That payment is under ' + min + ' SOL.' };
    const memoOk = (tx.transaction.message.instructions || []).some(x => (x.program === 'spl-memo' || x.programId === MEMO) && /memecapes/i.test(typeof x.parsed === 'string' ? x.parsed : JSON.stringify(x.parsed || '')));
    return { sol, from: keys[0], memoOk, t: (tx.blockTime || 0) * 1000 };
  }

  async function http(req, res, url, json) {
    const p = url.pathname, ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
    const net = url.searchParams.get('net') === 'devnet' ? 'devnet' : 'mainnet';
    if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' }); return res.end(); }
    let m; const me = who(req);
    // ---- reads
    if (req.method === 'GET') {
      if (p === '/so/me') { if (!me) return json({ error: 'Sign in first.' }, 401); return json({ ...prof(me), channel: chPub(Q.chGet.get(me)), following: Q.folOf.all(me).map(r => r.target), streaming: STREAMING, pass: { usd: PASS.usd, days: PASS.days, until: passUntil(me), active: passOn(me), needed: !!(PASS.to && PASS.usd > 0) } }); }
      if (p === '/st/pass') {   // the price now, in SOL, for this wallet (honoured for 15 minutes)
        if (!me) return json({ error: 'Sign in first.' }, 401);
        if (!PASS.to || PASS.usd <= 0) return json({ needed: false, active: true, usd: 0, days: PASS.days, until: 0 });
        const price = await solPrice(), sol = Math.ceil(PASS.usd / price * 1e4) / 1e4; quotes.set(me, { sol, t: now() });
        return json({ needed: true, usd: PASS.usd, days: PASS.days, sol, solUsd: price, to: PASS.to, until: passUntil(me), active: passOn(me) });
      }
      if ((m = /^\/so\/u\/([1-9A-HJ-NP-Za-km-z]{32,44})$/.exec(p))) {
        const w = m[1], s = Q.trStats.get(w, net) || {};
        return json({ ...prof(w), channel: chPub(Q.chGet.get(w)), followers: Q.folN.get(w).n, trades: s.n | 0, coins: s.coins | 0, solIn: (s.sin || 0) / 1e9, solOut: (s.sout || 0) / 1e9, net: ((s.sout || 0) - (s.sin || 0)) / 1e9,
          posts: Q.postsFeed.all(null, w, 30).map(x => postPub(x, me)) });
      }
      if (p === '/so/feed') {
        const kind = url.searchParams.get('kind') || 'all', mint = url.searchParams.get('mint') || null, wallet = url.searchParams.get('wallet') || null, lim = Math.min(80, +url.searchParams.get('limit') || 40);
        const evKind = { launches: 'launch', whales: 'whale', grads: 'grad', live: 'live', tips: 'tip' }[kind] || null;
        let items = [];
        if (kind === 'all' || kind === 'posts') items.push(...Q.postsFeed.all(mint, wallet, lim).map(x => postPub(x, me)));
        if (kind !== 'posts') items.push(...Q.evFeed.all(net, evKind, mint, wallet, lim).map(e => ({ id: 'e' + e.id, kind: e.kind, t: e.t, wallet: e.wallet, who: e.wallet ? prof(e.wallet) : null, sol: e.sol, coin: coinOf(e.mint, net), data: e.data ? JSON.parse(e.data) : null })));
        items.sort((a, b) => b.t - a.t);
        return json({ items: items.slice(0, lim) });
      }
      if ((m = /^\/so\/post\/(\d+)$/.exec(p))) { const r = Q.postGet.get(+m[1]); if (!r || r.hidden) return json({ error: 'not found' }, 404); return json({ post: postPub(r, me), replies: Q.postsReply.all(r.id).map(x => postPub(x, me)) }); }
      if (p === '/so/trending') {
        const h = now() - 3600e3, tr = Q.trHour.get(net, h) || {}, ev = Object.fromEntries(Q.evSince.all(net, now() - 864e5).map(r => [r.kind, r.n]));
        return json({ coins: Q.trTrend.all(net, h).map(r => ({ mint: r.mint, name: r.name, symbol: r.symbol, image: r.image, trades: r.n, traders: r.w, volume: r.v / 1e9, flow: r.flow / 1e9 })),
          now: { tradesHour: tr.n | 0, tradersHour: tr.w | 0, volumeHour: (tr.v || 0) / 1e9, launchesDay: Q.coinsNew.get(net, now() - 864e5).n, whalesDay: ev.whale | 0, gradsDay: ev.grad | 0, live: Q.chLive.all().length } });
      }
      if (p === '/st/live') return json({ channels: Q.chLive.all().map(c => ({ ...chPub(c), who: prof(c.wallet), coin: coinOf(c.mint, net) })), all: Q.chAll.all().map(c => ({ wallet: c.wallet, name: c.name, category: c.category, live: !!c.live, who: prof(c.wallet) })), streaming: STREAMING });
      if ((m = /^\/st\/ch\/([1-9A-HJ-NP-Za-km-z]{32,44})$/.exec(p))) {
        const c = Q.chGet.get(m[1]); if (!c || c.hidden) return json({ error: 'No channel at that wallet yet.' }, 404);
        const ts = Q.tipSum.get(c.wallet);
        return json({ ...chPub(c), who: prof(c.wallet), coin: coinOf(c.mint, net), followers: Q.folN.get(c.wallet).n, subs: Q.subN.get(c.wallet, now()).n, tips: { sol: ts.s, n: ts.n, recent: Q.tipsOf.all(c.wallet).map(t => ({ who: prof(t.wallet), sol: t.sol, t: t.t })) },
          mySub: me ? !!Q.subHas.get(c.wallet, me, now()) : false, following: me ? Q.folOf.all(me).some(r => r.target === c.wallet) : false });
      }
      if (p === '/st/chat') { const ch = String(url.searchParams.get('channel') || ''); if (!isW(ch)) return json({ error: 'bad channel' }, 400); return json({ msgs: Q.chatGet.all(ch, +url.searchParams.get('after') || 0).map(x => ({ id: x.id, who: prof(x.wallet), text: x.text, t: x.t })), viewers: viewersOf(ch) }); }
      return false;
    }
    if (req.method !== 'POST') return false;
    let b; try { b = await body(req, 1.5 * 1024 * 1024); } catch (e) { return json({ error: 'Too big.' }, 400); }
    const bnet = b.net === 'devnet' ? 'devnet' : 'mainnet';
    // ---- sign in: sign a short message in your wallet (not a transaction; nothing moves)
    if (p === '/so/nonce') {
      const w = String(b.wallet || ''); if (!isW(w)) return json({ error: 'That is not a Solana wallet address.' }, 400);
      if (tooMany('son' + ip)) return json({ error: 'Too many tries. Wait a few minutes.' }, 429);
      const msg = 'Sign in to MemeCapes\n\nWallet: ' + w + '\nCode: ' + crypto.randomBytes(8).toString('hex') + '\nTime: ' + new Date().toISOString() + '\n\nThis is not a transaction. Nothing leaves your wallet.';
      nonces.set(w, { msg, t: now() }); return json({ msg });
    }
    if (p === '/so/login') {
      const w = String(b.wallet || ''), n = nonces.get(w);
      if (!n || now() - n.t > 10 * 60e3 || !sigOk(w, n.msg, b.sig)) return json({ error: 'The signature did not match. Try signing in again.' }, 400);
      nonces.delete(w); const token = crypto.randomBytes(24).toString('hex'); Q.sesAdd.run(token, w, now());
      return json({ token, wallet: w, ...prof(w), channel: chPub(Q.chGet.get(w)) });
    }
    if (p === '/st/watch') { const ch = String(b.channel || ''); if (!isW(ch)) return json({ error: 'bad channel' }, 400); if (!watchers.has(ch)) watchers.set(ch, new Map()); watchers.get(ch).set(ip, now()); return json({ viewers: viewersOf(ch) }); }
    // ---- payments to a channel: checked on-chain, recorded, never routed through us
    if (p === '/st/tip' || p === '/st/sub') {
      const ch = Q.chGet.get(String(b.channel || '')); if (!ch) return json({ error: 'No such channel.' }, 404);
      const sig = String(b.sig || '').trim(); if (!/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(sig)) return json({ error: 'Bad transaction signature.' }, 400);
      if (Q.tipSig.get(sig) || Q.subSig.get(sig)) return json({ error: 'That payment was already counted.' }, 400);
      let v; try { v = await checkPay(bnet, sig, ch.wallet, p === '/st/sub' ? ch.subSol : 0.0001); } catch (e) { return json({ error: 'Could not reach the blockchain. Try again in a minute.' }, 502); }
      if (v.err) return json({ error: v.err }, 400);
      if (p === '/st/tip') { Q.tipAdd.run(sig, ch.wallet, v.from, v.sol, now()); event({ kind: 'tip', net: bnet, wallet: v.from, sol: v.sol, data: { channel: ch.wallet, name: ch.name } }); return json({ ok: true, sol: v.sol }); }
      const until = Math.max(now(), (Q.subHas.get(ch.wallet, v.from, now()) || {}).until || 0) + 30 * 864e5; Q.subSet.run(ch.wallet, v.from, until, sig, v.sol);
      event({ kind: 'sub', net: bnet, wallet: v.from, sol: v.sol, data: { channel: ch.wallet, name: ch.name } }); return json({ ok: true, until });
    }
    if (!me) return json({ error: 'Sign in with your wallet first.' }, 401);
    // ---- signed-in writes
    if (p === '/so/profile') {
      let avatar = null; const mm = /^data:(image\/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)$/.exec(String(b.avatar || ''));
      if (mm) { const raw = Buffer.from(mm[2], 'base64'); if (raw.length > 600 * 1024) return json({ error: 'Picture too big (600 KB max).' }, 400); const ext = mm[1] === 'image/png' ? 'png' : mm[1] === 'image/webp' ? 'webp' : 'jpg', id = crypto.randomBytes(12).toString('hex'); fs.writeFileSync(path.join(IMG_DIR, id + '.' + ext), raw); avatar = PUBLIC + '/lp/img/' + id + '.' + ext; }
      Q.profSet.run(me, clean(b.name, 24), clean(b.about, 200), link(b.x), avatar, now()); return json(prof(me));
    }
    if (p === '/so/post') {
      if (tooMany('sop' + me) || Q.postsByIp.get(me, now() - 3600e3).n >= 30) return json({ error: 'Slow down: 30 posts an hour.' }, 429);
      const text = clean(b.text, 280); if (text.length < 1) return json({ error: 'Write something first.' }, 400);
      const mint = b.mint && coinGet.get(String(b.mint), bnet) ? String(b.mint) : '', reply = (+b.reply > 0 && Q.postGet.get(+b.reply)) ? +b.reply : 0;
      const r = Q.postAdd.run(me, text, mint, reply, now()); if (reply) Q.postReplies.run(reply);
      return json({ post: postPub(Q.postGet.get(r.lastInsertRowid), me) });
    }
    if (p === '/so/like') { const id = +b.post; if (!Q.postGet.get(id)) return json({ error: 'not found' }, 404); if (Q.likeHas.get(id, me)) Q.likeDel.run(id, me); else Q.likeAdd.run(id, me); Q.likeN.run(id); return json({ post: postPub(Q.postGet.get(id), me) }); }
    if (p === '/so/follow') { const w = String(b.wallet || ''); if (!isW(w) || w === me) return json({ error: 'bad wallet' }, 400); if (b.on === false) Q.folDel.run(me, w); else Q.folAdd.run(me, w); return json({ ok: true, followers: Q.folN.get(w).n }); }
    if (p === '/st/channel') {
      const name = clean(b.name, 24); if (name.length < 2) return json({ error: 'Give your channel a name.' }, 400);
      const subSol = Math.max(0.01, Math.min(10, +b.subSol || 0.1));
      Q.chSet.run(me, name, clean(b.about, 300), clean(b.category, 24) || 'MemeCapes', subSol, now()); return json({ channel: chPub(Q.chGet.get(me)) });
    }
    if (p === '/st/pass') {
      if (!PASS.to || PASS.usd <= 0) return json({ ok: true, until: 0, active: true });
      const sig = String(b.sig || '').trim(); if (!/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(sig)) return json({ error: 'Bad transaction signature.' }, 400);
      if (Q.passSig.get(sig)) return json({ error: 'That payment was already counted.' }, 400);
      const q = quotes.get(me); const minSol = q && now() - q.t < 15 * 60e3 ? q.sol * 0.985 : Math.ceil(PASS.usd / await solPrice() * 1e4) / 1e4 * 0.985;
      let v; try { v = await checkPay(bnet, sig, PASS.to, minSol); } catch (e) { return json({ error: 'Could not reach the blockchain. Try again in a minute.' }, 502); }
      if (v.err) return json({ error: v.err }, 400);
      if (v.from !== me) return json({ error: 'That payment came from a different wallet than the one you are signed in with.' }, 400);
      const until = Math.max(now(), passUntil(me)) + PASS.days * 864e5;
      Q.passPay.run(sig, me, v.sol, PASS.usd, PASS.days, now()); Q.passSet.run(me, until, now()); quotes.delete(me);
      return json({ ok: true, until, active: true });
    }
    if (p === '/st/golive') {
      const c = Q.chGet.get(me); if (!c) return json({ error: 'Set up your channel first.' }, 400);
      if (!passOn(me)) return json({ error: 'You need a streamer pass to go live: $' + PASS.usd + ' for ' + PASS.days + ' days, paid from your wallet.', pass: true }, 402);
      if (!STREAMING) return json({ error: 'Live video is not switched on yet. Your channel is saved; you will be able to go live as soon as it is.' }, 503);
      const mode = b.mode === 'obs' ? 'obs' : 'browser', mint = b.mint && coinGet.get(String(b.mint), bnet) ? String(b.mint) : null;
      let inp; try { inp = await cfCreate(c.name + ' ' + now()); } catch (e) { return json({ error: 'Could not start the stream: ' + e.message }, 502); }
      const playKind = mode === 'obs' ? 'iframe' : 'whep', playUrl = mode === 'obs' ? `https://customer-${CF.code}.cloudflarestream.com/${inp.uid}/iframe` : (inp.webRTCPlayback && inp.webRTCPlayback.url) || '';
      if (c.cfUid) cfDelete(c.cfUid);
      Q.chLiveSet.run(clean(b.title, 80) || c.name + ' is live', clean(b.category, 24) || c.category, mode, playKind, playUrl, inp.uid, mint, now(), me);
      event({ kind: 'live', net: bnet, wallet: me, mint: mint || '', data: { name: c.name, title: clean(b.title, 80) } });
      return json({ ok: true, whip: inp.webRTC && inp.webRTC.url, rtmps: inp.rtmps, channel: chPub(Q.chGet.get(me)) });
    }
    if (p === '/st/end') { const c = Q.chGet.get(me); if (c && c.cfUid) cfDelete(c.cfUid); Q.chEnd.run(me); return json({ ok: true }); }
    if (p === '/st/chat') {
      const ch = String(b.channel || ''), text = clean(b.text, 200); if (!isW(ch) || !text) return json({ error: 'bad' }, 400);
      if (tooMany('soc' + me)) return json({ error: 'Slow down.' }, 429);
      const r = Q.chatAdd.run(ch, me, text, now()); return json({ id: Number(r.lastInsertRowid) });
    }
    return json({ error: 'not found' }, 404);
  }
  function postPub(r, me) { return { id: r.id, kind: 'post', t: r.t, wallet: r.wallet, who: prof(r.wallet), text: r.text, coin: r.mint ? coinOf(r.mint, netOf ? netOf() : 'mainnet') : null, likes: r.likes, replies: r.replies, reply: r.reply, liked: me ? !!Q.likeHas.get(r.id, me) : false }; }
  function cmd(c, arg, id) {
    if (arg === 'hidepost') { db.prepare('UPDATE so_posts SET hidden=1 WHERE id=?').run(+id); return say(c, 'Post hidden.', '#0a0'); }
    if (arg === 'endstream') { const ch = Q.chGet.get(String(id)); if (ch && ch.cfUid) cfDelete(ch.cfUid); Q.chEnd.run(String(id)); return say(c, 'Stream ended.', '#0a0'); }
    if (arg === 'hidechannel') { db.prepare('UPDATE so_channels SET hidden=1, live=0 WHERE wallet=?').run(String(id)); return say(c, 'Channel hidden.', '#0a0'); }
    if (arg === 'pass') { const [w, d] = String(id || '').split(/\s+/); if (!isW(w)) return say(c, 'Usage: /watch pass <wallet> [days]', '#a60'); const until = Math.max(now(), passUntil(w)) + (+d || PASS.days) * 864e5; Q.passSet.run(w, until, now()); return say(c, 'Streamer pass for ' + w.slice(0, 6) + '… until ' + new Date(until).toISOString().slice(0, 10) + '.', '#0a0'); }
    say(c, 'Usage: /watch hidepost <id>, /watch endstream <wallet>, /watch hidechannel <wallet>, /watch pass <wallet> [days]', '#a60');
  }
  return { http, event, cmd, streaming: STREAMING, liveForMint: (mint) => Q.chByMint.all(mint).map(chPub) };
};
