'use strict';
// Friends and private messages on a throwaway server: request, accept, decline, remove, online/offline notices,
// messages delivered live and kept for later, non-friends refused, ignore drops them.   Run: node test_friends.js
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-fr-'));
const PORT = 19000 + Math.floor(Math.random() * 500);
const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, ADMIN_KEY: 'k' }, stdio: ['ignore', 'pipe', 'inherit'] });
let fails = 0, n = 0;
const ok = (c, msg) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
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
  const a = client('Alice'), b = client('Bobby'), c = client('Carol');
  await a.open; await b.open; await c.open;
  a.send({ t: 'register', name: 'Alice', pass: 'password1' }); const wa = await a.next('welcome');
  b.send({ t: 'register', name: 'Bobby', pass: 'password2' }); const wb = await b.next('welcome');
  c.send({ t: 'register', name: 'Carol', pass: 'password3' }); await c.next('welcome');
  ok((await a.next('friends')).list.length === 0, 'empty friends list at sign-in');

  a.send({ t: 'friendAdd', name: 'Nobody' }); ok((await a.next('info')).text.includes('No player'), 'unknown name refused');
  a.send({ t: 'friendAdd', name: 'Alice' }); ok((await a.next('info')).text.includes('you'), 'adding yourself refused');
  a.send({ t: 'friendAdd', name: 'bobby' }); ok((await a.next('info')).text.includes('sent'), 'request sent (any case)');
  const fa = await a.next('friends', m => m.list.length === 1); ok(fa.list[0].name === 'Bobby' && fa.list[0].ok === 0, 'Alice sees Bobby as waiting');
  ok((await b.next('info')).text.includes('wants to be your friend'), 'Bobby is told');
  const fb = await b.next('friends', m => m.reqs.length === 1); ok(fb.reqs[0] === 'Alice' && fb.list.length === 0, 'Bobby has one request, no friends yet');
  a.send({ t: 'friendAdd', name: 'Bobby' }); ok((await a.next('info')).text.includes('already asked'), 'asking twice is harmless');

  // a message before accepting is refused
  a.send({ t: 'pm', name: 'Bobby', text: 'hi' }); ok((await a.next('info')).text.includes('only message friends'), 'PM to a non-friend refused');

  b.send({ t: 'friendYes', name: 'Alice' });
  ok((await b.next('info')).text.includes('friends now'), 'Bobby accepts');
  ok((await a.next('info')).text.includes('accepted'), 'Alice is told');
  const fa2 = await a.next('friends', m => m.list.length === 1 && m.list[0].ok === 1); ok(fa2.list[0].on === 1, 'Alice sees Bobby online as a friend');
  ok((await b.next('fon', m => m.name === 'Alice')).on === 1, 'Bobby gets Alice online'); await a.next('fon', m => m.name === 'Bobby');

  // live PM both ways, cleaned
  a.send({ t: 'pm', name: 'Bobby', text: 'gm <b>fren</b> shit' }); const p1 = await b.next('pm'); ok(p1.from === 'Alice' && !p1.text.includes('<') && p1.text.includes('****'), 'PM delivered, cleaned, filtered: ' + p1.text);
  ok((await a.next('pm', m => m.mine)).to === 'Bobby', 'sender gets an echo');
  a.send({ t: 'pm', name: 'Bobby', text: 'again' }); ok((await a.next('info')).text.includes('Slow'), 'PM slow-down');
  await wait(900);
  b.send({ t: 'pm', name: 'Alice', text: 'gm back' }); ok((await a.next('pm', m => !m.mine)).text === 'gm back', 'reply delivered');
  b.send({ t: 'pmHist', name: 'Alice' }); const hh = await b.next('pmHist'); ok(hh.lines.length === 2 && hh.lines[0].mine === 0 && hh.lines[1].mine === 1, 'history in order with mine flags');

  // Carol: not a friend, cannot PM; Alice adds Carol, Carol declines
  c.send({ t: 'pm', name: 'Alice', text: 'yo' }); ok((await c.next('info')).text.includes('only message friends'), 'Carol cannot PM Alice');
  a.send({ t: 'friendAdd', name: 'Carol' }); await a.next('info'); await c.next('info');
  c.send({ t: 'friendNo', name: 'Alice' }); ok((await c.next('info')).text.includes('declined'), 'Carol declines');
  ok((await a.next('friends', m => m.list.length === 1)).list[0].name === 'Bobby', 'Alice back to one entry');

  // offline delivery: Bobby leaves, Alice writes, Bobby signs back in and gets it + an offline notice for Alice
  b.ws.close(); ok((await a.next('fon', m => m.name === 'Bobby')).on === 0, 'Alice sees Bobby go offline');
  await wait(900);
  a.send({ t: 'pm', name: 'Bobby', text: 'read this later' }); await a.next('pm', m => m.mine);
  const b2 = client('Bobby2'); await b2.open; b2.send({ t: 'login', name: 'Bobby', pass: 'password2' }); await b2.next('welcome');
  const late = await b2.next('pm'); ok(late.late === 1 && late.text === 'read this later' && late.from === 'Alice', 'kept message arrives at sign-in');
  ok((await a.next('fon', m => m.name === 'Bobby')).on === 1, 'Alice sees Bobby back online');

  // ignore drops PMs and requests from that player
  b2.send({ t: 'ignore', name: 'Alice' }); await wait(900);
  a.send({ t: 'pm', name: 'Bobby', text: 'hello?' }); await a.next('pm', m => m.mine);
  await wait(300); ok(!b2.got.some(m => m.t === 'pm' && m.text === 'hello?'), 'ignored sender\'s PM is dropped');

  // remove
  a.send({ t: 'friendNo', name: 'Bobby' }); ok((await a.next('info')).text.includes('removed'), 'friend removed');
  ok((await b2.next('friends', m => m.list.length === 0)).list.length === 0, 'both sides lose the entry');

  console.log(fails ? `\n${fails} of ${n} FAILED` : `\nall ${n} passed`);
  srv.kill(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
