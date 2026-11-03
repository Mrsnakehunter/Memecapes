'use strict';
// Worlds + PvP on a throwaway server: players only see their own world, fights only in World 2, outside towns,
// within reach and level range, at attack speed, damage capped by saved levels, server-kept hitpoints, a kill.
// Run: node test_pvp.js
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-pvp-'));
const PORT = 19500 + Math.floor(Math.random() * 400);
const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, ADMIN_KEY: 'k', PVP_LOOT_OWN: '4000', PVP_LOOT_END: '60000' }, stdio: ['ignore', 'pipe', 'inherit'] });
let fails = 0, n = 0;
const ok = (c, msg) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
function client(name) {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000' } });
  const C = { ws, name, got: [], waiters: [] };
  ws.onmessage = e => { const m = JSON.parse(e.data); C.got.push(m); C.waiters = C.waiters.filter(w => { if (w.f(m)) { w.r(m); return false; } return true; }); };
  C.send = o => ws.send(JSON.stringify(o));
  C.next = (t, f = () => true, ms = 3000) => new Promise((r, j) => { const hit = C.got.find(m => m.t === t && f(m)); if (hit) { C.got.splice(C.got.indexOf(hit), 1); return r(hit); } const w = { f: m => m.t === t && f(m), r: m => { C.got.splice(C.got.indexOf(m), 1); r(m); } }; C.waiters.push(w); setTimeout(() => j(new Error(name + ' waited for ' + t)), ms); });
  C.none = async (t, ms = 700) => { await wait(ms); return !C.got.some(m => m.t === t); };
  C.open = new Promise(r => ws.onopen = r);
  return C;
}
const XP = l => { const K = 2e7 / (99 * Math.pow(1.095, 99)); return Math.round(K * (l - 1) * Math.pow(1.095, l - 1)) + 1; };
const save = (C, rev, lv, more) => { C.send({ t: 'save', rev, st: { v: 1, inv: [], coins: 0, ...(more || {}), xp: { at: XP(lv), str: XP(lv), def: XP(lv), hp: XP(lv) } } }); return C.next('saved'); };
(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  const a = client('Alice'), b = client('Bobby'), c = client('Carol');
  await a.open; await b.open; await c.open;
  a.send({ t: 'register', name: 'Alice', pass: 'password1', world: 2 }); const wa = await a.next('welcome');
  b.send({ t: 'register', name: 'Bobby', pass: 'password2', world: 2 }); const wb = await b.next('welcome');
  c.send({ t: 'register', name: 'Carol', pass: 'password3', world: 1 }); const wc = await c.next('welcome');
  ok(wa.world === 2 && wc.world === 1, 'welcome says the world');
  ok(wc.worlds[2] === 2 && wc.worlds[1] === 1, 'world counts: ' + JSON.stringify(wc.worlds));
  const wl = await (await fetch('http://127.0.0.1:' + PORT + '/worlds')).json();
  ok(wl.worlds.length === 2 && wl.worlds[1].pvp && wl.worlds[1].online === 2, '/worlds lists both worlds');
  await save(a, wa.rev, 40); await save(b, wb.rev, 40); await save(c, wc.rev, 40);

  // positions: Alice + Bobby in the wild (outside every town), Carol at the same spot in World 1
  for (const C of [a, b, c]) C.send({ t: 'pos', x: 120 + (C === b ? 1 : 0), y: 230, r: 0, lv: 40 });
  const pa = await a.next('pl', m => m.p.length > 0); ok(pa.p.length === 1 && pa.n === 2, 'Alice sees only Bobby (her world)');
  const pc = await c.next('pl'); ok(pc.p.length === 0 && pc.n === 1, 'Carol sees nobody (World 1 alone)');
  a.send({ t: 'chat', text: 'hello pvp' }); await b.next('chat'); ok(await c.none('chat'), 'chat stays in its world');
  a.send({ t: 'tradeReq', name: 'Carol' }); ok((await a.next('info')).text.includes('same world'), 'no trades across worlds');

  // a hit: capped at what level 40 can do
  a.send({ t: 'pvpHit', id: 2, s: 'at', d: 999 }); const h1 = await b.next('pvpHit'); const ack = await a.next('pvpAck');
  ok(h1.d > 0 && h1.d < 25 && ack.d === h1.d, 'damage capped by level: ' + h1.d);
  ok(h1.hp === h1.max - h1.d && h1.max === 40, 'server keeps hitpoints: ' + h1.hp + '/' + h1.max);
  a.send({ t: 'pvpHit', id: 2, s: 'at', d: 5 }); ok((await a.next('pvpNo')) && await b.none('pvpHit', 300), 'too fast: refused');
  // reach
  a.send({ t: 'pos', x: 126, y: 230, r: 0, lv: 40 }); await wait(250);
  a.send({ t: 'pvpHit', id: 2, s: 'at', d: 5 }); ok((await a.next('info')).text.includes('far'), 'melee out of reach refused');
  await wait(2000);
  a.send({ t: 'pvpHit', id: 2, s: 'rg', d: 5 }); ok((await b.next('pvpHit')).s === 'rg', 'ranged reaches 5 tiles');
  // safe zone
  b.send({ t: 'pos', x: 156, y: 182, r: 0, lv: 40 }); await wait(250); await wait(2000);
  a.send({ t: 'pos', x: 150, y: 140, r: 0, lv: 40 }); await wait(250);
  a.send({ t: 'pvpHit', id: 2, s: 'mg', d: 5 }); ok((await a.next('info')).text.includes('safe zone'), 'no fights in town');
  // World 1 never fights
  c.send({ t: 'pvpHit', id: 1, s: 'at', d: 5 }); ok(await a.none('pvpHit', 400) && await c.none('pvpAck', 1), 'World 1 cannot fight');
  // eating heals, capped
  b.send({ t: 'pvpEat', h: 99 }); const hp = await b.next('pvpHp'); ok(hp.hp <= hp.max && hp.hp > h1.hp, 'food heals within max: ' + hp.hp);

  // a level 3 can't be attacked by level 40
  const d = client('Dan'); await d.open; d.send({ t: 'register', name: 'Danny', pass: 'password4', world: 2 }); const wd = await d.next('welcome');
  await save(d, wd.rev, 3); d.send({ t: 'pos', x: 120, y: 231, r: 0, lv: 3 });
  a.send({ t: 'pos', x: 120, y: 230, r: 0, lv: 40 }); await wait(2600);
  a.send({ t: 'pvpHit', id: 4, s: 'at', d: 1 }); ok((await a.next('info')).text.includes('too far apart'), 'level range protects new players');

  // fight to the end: Bobby carries tradeable things, worn gear, coins and some untradeables
  const bs = await save(b, wb.rev + 1, 40, { inv: ['sw20', 'fish', 'cape_at', 'pet_cat'], eq: { weapon: 'sw10', body: 'arm80', cape: 'cape_at' }, coins: 500 });
  b.send({ t: 'pos', x: 121, y: 230, r: 0, lv: 40 }); await wait(300);
  let dead = null;
  for (let i = 0; i < 40 && !dead; i++) {
    a.send({ t: 'pvpHit', id: 2, s: 'at', d: 999 }); await wait(2000);
    dead = b.got.find(m => m.t === 'pvpDead');
  }
  ok(dead && dead.by === 'Alice', 'Bobby is defeated');
  ok(!!(await a.next('pvpWin')), 'Alice is told she won');
  ok(dead && JSON.stringify(dead.inv) === '["cape_at","pet_cat"]' && dead.coins === 0, 'loser keeps only untradeables: ' + JSON.stringify(dead && dead.inv));
  ok(dead && dead.eq && dead.eq.body === 'arm80' && dead.eq.cape === 'cape_at' && !dead.eq.weapon && dead.rev === bs.rev + 1, 'worn gear dropped, untradeable armour kept');
  b.send({ t: 'pull' }); const rs = await b.next('resync'); ok(rs.save.inv.length === 2 && rs.save.coins === 0, 'the server copy is emptied too');
  const pile = await a.next('pvpPile'); ok(pile.n === 4 && pile.from === 'Bobby' && !pile.open, 'loot pile appears: ' + pile.n + ' things');
  ok(await c.none('pvpPile', 50), 'World 1 never sees PvP loot');
  d.send({ t: 'pos', x: 121, y: 231, r: 0, lv: 3 }); await wait(250);
  d.send({ t: 'pvpLoot', id: pile.id }); ok((await d.next('info')).text.includes('belongs to Alice'), 'only the killer loots at first');
  a.send({ t: 'pos', x: 126, y: 230, r: 0, lv: 40 }); await wait(250);
  a.send({ t: 'pvpLoot', id: pile.id }); ok((await a.next('info')).text.includes('closer'), 'must stand at the pile');
  a.send({ t: 'pos', x: 121, y: 230, r: 0, lv: 40 }); await wait(250);
  a.send({ t: 'pvpLoot', id: pile.id }); const lg = await a.next('lootGot');
  ok(lg.coins === 500 && ['sw20', 'fish', 'sw10'].every(k => lg.inv.includes(k)) && lg.left === 0, 'killer takes everything: ' + JSON.stringify(lg.inv));
  ok(!!(await d.next('pvpPileGone')), 'an empty pile disappears for everyone');
  a.send({ t: 'pvpTop' }); const top = await a.next('pvpTop'); ok(top.list[0].name === 'Alice' && top.me.kills === 1, 'kills counted');
  console.log(fails ? `${fails} of ${n} FAILED` : `all ${n} passed`);
  srv.kill(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
