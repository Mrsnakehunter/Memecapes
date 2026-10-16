'use strict';
// Attacks a throwaway server the way a hacker would and checks that Sentinel stops each one.
// Run: node test_guard.js
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path'), crypto = require('crypto');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-guard-'));
const PORT = 19000 + Math.floor(Math.random() * 1000), B = 'http://127.0.0.1:' + PORT;
const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, ADMIN_NAMES: 'Albert', ADMIN_KEY: 'k'.repeat(40), LP_NO_INDEX: '1', PROXY_HOPS: '', GUARD_WS_PER_IP: '8' }, stdio: ['ignore', 'pipe', 'pipe'] });
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
// on Render the proxy appends its own entry after the visitor's real one: "whatever-the-visitor-wrote, REAL, proxy"
const as = (ip, spoof) => ({ 'X-Forwarded-For': (spoof ? spoof + ', ' : '') + ip + ', 10.0.0.1' });
const get = async (p, h = {}) => { const r = await fetch(B + p, { headers: h }); let j = null; try { j = await r.json(); } catch (e) { } return { s: r.status, j, h: r.headers }; };
const post = async (p, o, h = {}) => { const r = await fetch(B + p, { method: 'POST', headers: { 'Content-Type': 'application/json', ...h }, body: JSON.stringify(o) }); let j = null; try { j = await r.json(); } catch (e) { } return { s: r.status, j }; };
function client(ip) {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000', ...as(ip) } });
  const C = { ws, got: [], waiters: [] };
  ws.onmessage = e => { const m = JSON.parse(e.data); C.got.push(m); C.waiters = C.waiters.filter(w => { if (w.f(m)) { w.r(m); return false; } return true; }); };
  C.send = o => ws.send(JSON.stringify(o));
  C.next = (t, f = () => true, ms = 4000) => new Promise((r, j) => { const hit = C.got.find(m => m.t === t && f(m)); if (hit) { C.got.splice(C.got.indexOf(hit), 1); return r(hit); } C.waiters.push({ f: m => m.t === t && f(m), r }); setTimeout(() => j(new Error('waited for ' + t)), ms); });
  C.open = new Promise((r, j) => { ws.onopen = () => r(true); ws.onerror = () => r(false); ws.onclose = () => r(false); });
  return C;
}
const B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const b58 = u8 => { let x = 0n; for (const b of u8) x = x * 256n + BigInt(b); let s = ''; while (x > 0n) { s = B58[Number(x % 58n)] + s; x /= 58n; } for (const b of u8) { if (b) break; s = '1' + s; } return s; };

(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  // 1. the real address: a made-up X-Forwarded-For entry is ignored
  let r = await get('/guard/me', as('9.9.9.9', '1.2.3.4'));
  ok(r.j && r.j.ip === '9.9.9.9', 'visitor-written address ignored, real one used (' + (r.j && r.j.ip) + ')');
  ok(r.h.get('x-content-type-options') === 'nosniff' && r.h.get('x-frame-options') === 'DENY', 'security headers on every answer');
  // 2. probing for hacker paths blocks the address
  r = await get('/.env', as('6.6.6.6')); ok(r.s === 404, 'probe for /.env answered 404');
  r = await get('/health', as('6.6.6.6')); ok(r.s === 403, 'prober blocked afterwards');
  r = await get('/health', as('7.7.7.7', '6.6.6.6')); ok(r.s === 200, 'a different visitor is not blocked (even claiming the blocked address)');
  // 3. flooding
  let n429 = 0; await Promise.all([...Array(160)].map(async () => { const x = await get('/health', as('5.5.5.5')); if (x.s === 429) n429++; }));
  ok(n429 > 20, 'a flood of 160 requests gets slowed down (' + n429 + ' refused)');
  r = await get('/health', as('4.4.4.4')); ok(r.s === 200, 'normal visitors unaffected by the flood');
  // 4. password guessing: the name locks after 8 wrong tries, from any address
  const al = client('3.3.3.1'); await al.open; al.send({ t: 'register', name: 'Albert', pass: 'correct-horse-1' }); await al.next('welcome');
  const atk = client('3.3.3.2'); await atk.open;
  for (let i = 0; i < 8; i++) { atk.send({ t: 'login', name: 'Albert', pass: 'guess' + i }); await atk.next('err'); }
  const g2 = client('3.3.3.3'); await g2.open; g2.send({ t: 'login', name: 'albert', pass: 'correct-horse-1' });
  ok(/locked/.test((await g2.next('err')).text), 'after 8 wrong passwords the name is locked, even with the right password from elsewhere');
  // 5. wrong admin keys
  r = await get('/admin/stats', { Authorization: 'Bearer nope', ...as('8.8.8.1') }); ok(r.s === 403, 'wrong admin key refused');
  for (let i = 0; i < 5; i++) await get('/admin/stats', { Authorization: 'Bearer nope' + i, ...as('8.8.8.1') });
  r = await get('/health', as('8.8.8.1')); ok(r.s === 403, 'admin-key guesser blocked');
  r = await get('/admin/guard', { Authorization: 'Bearer ' + 'k'.repeat(40), ...as('8.8.8.2') }); ok(r.s === 200 && r.j.mode === 'normal' && r.j.blocked.length >= 2, 'admin sees the guard status (' + (r.j && r.j.blocked.length) + ' blocked)');
  // 6. modes: an admin switches to shield, new accounts and uploads pause, play goes on
  al.send({ t: 'chat', text: '/guard shield' }); await al.next('info', m => /SHIELD/.test(m.text));
  const nu = client('2.2.2.2'); await nu.open; nu.send({ t: 'register', name: 'Newbie', pass: 'password123' });
  ok(/paused/.test((await nu.next('err')).text), 'shield: new accounts paused');
  r = await post('/lp/upload', { name: 'Test', symbol: 'TST', image: 'data:image/png;base64,iVBORw0KGgo=' }, as('2.2.2.3')); ok(r.s === 503, 'shield: coin uploads paused');
  al.send({ t: 'chat', text: 'still playing' }); ok((await al.next('chat')).text === 'still playing', 'shield: players already in keep chatting');
  al.send({ t: 'chat', text: '/guard lockdown' }); await al.next('info', m => /LOCKDOWN/.test(m.text));
  const lg = client('2.2.2.4'); await lg.open; lg.send({ t: 'login', name: 'Albert', pass: 'correct-horse-1' }); ok(/lockdown/.test((await lg.next('err')).text), 'lockdown: new sign-ins paused');
  al.send({ t: 'chat', text: '/guard normal' }); await al.next('info', m => /NORMAL/.test(m.text));
  // 7. too many connections from one address
  const many = [...Array(9)].map(() => client('1.1.1.1')); const opened = await Promise.all(many.map(c => c.open));
  ok(opened.filter(Boolean).length === 8, 'at most 8 game connections from one address (' + opened.filter(Boolean).length + ' opened)');
  many.forEach(c => { try { c.ws.close(); } catch (e) { } });
  // 8. a devnet "payment" (free test SOL) can't buy a streamer pass
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519'); const W = b58(publicKey.export({ format: 'der', type: 'spki' }).subarray(12));
  let x = await post('/so/nonce', { wallet: W }, as('2.2.3.1'));
  x = await post('/so/login', { wallet: W, sig: crypto.sign(null, Buffer.from(x.j.msg), privateKey).toString('base64') }, as('2.2.3.1'));
  ok(!!(x.j && x.j.token), 'wallet sign-in works');
  x = await post('/st/pass', { net: 'devnet', sig: '5'.repeat(88) }, { Authorization: 'Bearer ' + x.j.token, ...as('2.2.3.1') });
  ok(x.s === 400 && /mainnet/.test(x.j.error), 'devnet payment refused for the streamer pass');
  // 9. another visitor can't cancel your wallet sign-in by asking for new messages
  const k2 = crypto.generateKeyPairSync('ed25519'), W2 = b58(k2.publicKey.export({ format: 'der', type: 'spki' }).subarray(12));
  const n1 = await post('/so/nonce', { wallet: W2 }, as('2.2.4.1')); await post('/so/nonce', { wallet: W2 }, as('2.2.4.2'));
  x = await post('/so/login', { wallet: W2, sig: crypto.sign(null, Buffer.from(n1.j.msg), k2.privateKey).toString('base64') }, as('2.2.4.1'));
  ok(!!(x.j && x.j.token), 'sign-in still works after someone else asked for a new message');
  console.log(fails ? fails + ' FAILED' : 'ALL GUARD CHECKS PASSED');
  srv.kill(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
