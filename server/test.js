'use strict';
// Starts a throwaway server and runs fake players through it: accounts, saves, chat, positions, a full trade.
// Run: node test.js
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-test-'));
const PORT = 18000 + Math.floor(Math.random() * 1000);
const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, ADMIN_NAMES: 'Albert', ADMIN_KEY: 'k' }, stdio: ['ignore', 'pipe', 'inherit'] });
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

function client(name) {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000' } });
  const C = { ws, name, got: [], waiters: [] };
  ws.onmessage = e => { const m = JSON.parse(e.data); C.got.push(m); C.waiters = C.waiters.filter(w => { if (w.f(m)) { w.r(m); return false; } return true; }); };
  C.send = o => ws.send(JSON.stringify(o));
  C.next = (t, f = () => true, ms = 3000) => new Promise((r, j) => { const hit = C.got.find(m => m.t === t && f(m)); if (hit) { C.got.splice(C.got.indexOf(hit), 1); return r(hit); } const w = { f: m => m.t === t && f(m), r: m => { C.got.splice(C.got.indexOf(m), 1); r(m); } }; C.waiters.push(w); setTimeout(() => j(new Error(name + ' waited for ' + t)), ms); });
  C.open = new Promise(r => ws.onopen = r);
  return C;
}

(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  const a = client('Alice'), b = client('Bobby');
  await a.open; await b.open;
  a.send({ t: 'register', name: 'Al', pass: 'password1' }); ok((await a.next('err')).text.includes('3 to 12'), 'short name refused');
  a.send({ t: 'register', name: 'Admin_1', pass: 'password1' }); ok((await a.next('err')).text.includes('reserved'), 'reserved name refused');
  a.send({ t: 'register', name: 'Alice', pass: 'short' }); ok((await a.next('err')).text.includes('8'), 'short password refused');
  a.send({ t: 'register', name: 'Alice', pass: 'password1' }); const wa = await a.next('welcome'); ok(wa.name === 'Alice' && wa.token && wa.save === null, 'Alice registered');
  b.send({ t: 'register', name: 'alice', pass: 'password1' }); ok((await b.next('err')).text.includes('taken'), 'name taken (any case)');
  b.send({ t: 'register', name: 'Bobby', pass: 'password2' }); const wb = await b.next('welcome'); ok(wb.name === 'Bobby', 'Bobby registered');

  // saves
  const sa = { coins: 500, bank: 0, inv: ['logs', 'logs', 'shrimp', 'cape_wc'], xp: { wc: 100 } }, sb = { coins: 50, bank: 0, inv: ['ore'], xp: { mi: 10 } };
  a.send({ t: 'save', st: sa, rev: 0 }); ok((await a.next('saved')).rev === 1, 'Alice saved (rev 1)');
  b.send({ t: 'save', st: sb, rev: 0 }); ok((await b.next('saved')).rev === 1, 'Bobby saved (rev 1)');
  a.send({ t: 'save', st: sa, rev: 0 }); ok((await a.next('stale')).rev === 1, 'old save refused as stale');
  a.send({ t: 'save', st: { inv: 'x' }, rev: 1 }); ok((await a.next('err')).text.includes('refused'), 'broken save refused');

  // positions
  a.send({ t: 'pos', x: 100, y: 100, r: 0, m: 0, g: 0, c: '', lv: 10 }); b.send({ t: 'pos', x: 110, y: 104, r: 1, m: 1, g: 1, c: 'memecape', lv: 20 });
  ok((await a.next('pi', m => m.name === 'Bobby')).c === 'memecape', 'Alice learns Bobby\'s look');
  const pl = await a.next('pl', m => m.p.length > 0); ok(pl.p[0][0] === wb && true || pl.p[0][1] === 110, 'Alice sees Bobby\'s position');

  // chat
  a.send({ t: 'chat', text: 'gm <b>frens</b> shit' }); const ch = await b.next('chat'); ok(ch.name === 'Alice' && !ch.text.includes('<') && ch.text.includes('****'), 'chat delivered, cleaned and filtered: ' + ch.text);
  a.send({ t: 'chat', text: 'again' }); ok((await a.next('info')).text.includes('Slow'), 'chat slow-down');

  // trade
  a.send({ t: 'tradeReq', name: 'Bobby' }); await a.next('info'); ok((await b.next('tradeReq')).from === 'Alice', 'Bobby gets the request');
  b.send({ t: 'tradeYes', name: 'Alice' }); await a.next('tradeStart'); await b.next('tradeStart'); ok(true, 'trade opened both sides');
  a.send({ t: 'tradeOffer', items: ['cape_wc'], coins: 0 }); ok((await a.next('info')).text.includes('cannot be traded'), 'untradeable cape refused');
  a.send({ t: 'tradeOffer', items: ['logs', 'diamond'], coins: 0 }); ok((await a.next('info')).text.includes('not in your bag'), 'item she does not have refused');
  a.send({ t: 'tradeOffer', items: ['logs', 'logs'], coins: 100 }); const th = await b.next('tradeTheirs'); ok(th.items.length === 2 && th.coins === 100, 'Bobby sees Alice\'s offer');
  b.send({ t: 'tradeOffer', items: ['ore'], coins: 10 }); await a.next('tradeTheirs');
  a.send({ t: 'tradeAccept', stage: 1 }); await b.next('tradeAcc'); b.send({ t: 'tradeAccept', stage: 1 });
  await a.next('tradeStage2'); await b.next('tradeStage2'); ok(true, 'both accepted: second screen');
  a.send({ t: 'tradeAccept', stage: 2 }); b.send({ t: 'tradeAccept', stage: 2 });
  const da = await a.next('tradeDone'), db_ = await b.next('tradeDone');
  ok(da.coins === 410 && da.inv.join() === 'shrimp,cape_wc,ore' && da.rev === 2, 'Alice after trade: ' + da.coins + ' ' + da.inv.join());
  ok(db_.coins === 140 && db_.inv.join() === 'logs,logs' && db_.rev === 2, 'Bobby after trade: ' + db_.coins + ' ' + db_.inv.join());
  a.send({ t: 'save', st: sa, rev: 1 }); ok((await a.next('stale')).rev === 2, 'pre-trade save cannot undo the trade');

  // second login kicks the first; resume with token
  const a2 = client('Alice2'); await a2.open; a2.send({ t: 'resume', token: wa.token });
  ok((await a.next('kicked')).text.includes('somewhere else'), 'old session kicked');
  const w2 = await a2.next('welcome'); ok(w2.save && w2.save.coins === 410 && w2.rev === 2, 'resume returns the server save');
  a2.send({ t: 'login', name: 'Bobby', pass: 'nope' });

  // admin
  const ad = client('Albert'); await ad.open; ad.send({ t: 'register', name: 'Albert', pass: 'password3' }); ok((await ad.next('welcome')).role === 'admin', 'admin by name');
  ad.send({ t: 'chat', text: '/mute Bobby 5' }); await ad.next('info');
  b.send({ t: 'chat', text: 'hello' }); ok((await b.next('info')).text.includes('muted'), 'muted player cannot chat');
  const st = await (await fetch('http://127.0.0.1:' + PORT + '/admin/stats', { headers: { authorization: 'Bearer k' } })).json(); ok(st.accounts === 3, 'admin stats: ' + JSON.stringify(st));
  ok((await fetch('http://127.0.0.1:' + PORT + '/admin/stats')).status === 403, 'admin page locked without key');

  // bad origin
  const ev = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'https://evil.example' } });
  ok(await new Promise(r => { ev.onopen = () => r(false); ev.onerror = () => r(true); }), 'other websites cannot connect');

  console.log(fails ? fails + ' FAILED' : 'ALL PASSED');
  srv.kill(); fs.rmSync(dir, { recursive: true, force: true }); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
