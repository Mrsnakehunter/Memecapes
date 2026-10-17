'use strict';
// "Link with snakepit": the game registers a one-time code, the Pit signs the link message with the player's wallet
// (an email sign-in wallet works the same as Phantom) and posts it here. Run: node test_plink.js
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path'), crypto = require('crypto');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-plink-'));
const PORT = 19000 + Math.floor(Math.random() * 900);
const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir }, stdio: ['ignore', 'pipe', 'inherit'] });
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const b58 = (buf) => { let n = BigInt('0x' + Buffer.from(buf).toString('hex')), s = ''; while (n > 0n) { s = B58[Number(n % 58n)] + s; n /= 58n; } for (const x of buf) { if (x) break; s = '1' + s; } return s; };
function keypair() { const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519'); const raw = publicKey.export({ format: 'der', type: 'spki' }).subarray(-32); return { addr: b58(raw), sign: (msg) => crypto.sign(null, Buffer.from(msg), privateKey).toString('base64') }; }
function client() {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000' } });
  const C = { ws, got: [] }; ws.onmessage = e => C.got.push(JSON.parse(e.data));
  C.send = o => ws.send(JSON.stringify(o));
  C.next = async (t, ms = 4000) => { const end = Date.now() + ms; while (Date.now() < end) { const i = C.got.findIndex(m => m.t === t); if (i >= 0) return C.got.splice(i, 1)[0]; await wait(30); } throw new Error('no ' + t); };
  C.open = new Promise(r => ws.onopen = r); return C;
}
const H = 'http://127.0.0.1:' + PORT;
(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  const a = client(), b = client(); await a.open; await b.open;
  a.send({ t: 'register', name: 'Snakey', pass: 'password1' }); await a.next('welcome');
  b.send({ t: 'register', name: 'Other1', pass: 'password1' }); await b.next('welcome');
  const code = crypto.randomBytes(12).toString('hex'), kp = keypair();
  a.send({ t: 'pitLinkStart', code }); await wait(200);
  let r = await fetch(H + '/plink/msg?code=' + code + '&wallet=' + kp.addr); let j = await r.json();
  ok(r.ok && j.account === 'Snakey' && j.msg.includes(kp.addr) && j.msg.includes(code), 'the Pit gets the message to sign, with the account name');
  ok((await fetch(H + '/plink/msg?code=' + 'f'.repeat(24) + '&wallet=' + kp.addr)).status === 404, 'an unknown code is refused');
  const bad = keypair();
  r = await fetch(H + '/plink', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, wallet: kp.addr, sig: bad.sign(j.msg) }) });
  ok(r.status === 400, 'a signature from another wallet is refused');
  r = await fetch(H + '/plink', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, wallet: kp.addr, sig: kp.sign(j.msg) }) }); j = await r.json();
  ok(r.ok && j.ok && j.account === 'Snakey', 'a good signature links the wallet');
  await wait(300); const h = a.got.filter(m => m.t === 'holder').pop() || {}; ok(h.wallet === kp.addr, 'the game is told at once (holder message carries the wallet)');
  r = await fetch(H + '/plink', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, wallet: kp.addr, sig: kp.sign(j.msg || 'x') }) });
  ok(r.status === 404, 'a code works once');
  // the same wallet cannot be linked to a second account
  const code2 = crypto.randomBytes(12).toString('hex');
  b.send({ t: 'pitLinkStart', code: code2 }); await wait(200);
  j = await (await fetch(H + '/plink/msg?code=' + code2 + '&wallet=' + kp.addr)).json();
  r = await fetch(H + '/plink', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: code2, wallet: kp.addr, sig: kp.sign(j.msg) }) });
  ok(r.status === 409, 'a wallet already linked to another account is refused');
  b.send({ t: 'pitLinkStart', code: 'not-a-code' }); await wait(100);
  ok((await fetch(H + '/plink/msg?code=not-a-code&wallet=' + kp.addr)).status === 404, 'a malformed code is never registered');
  a.ws.close(); b.ws.close(); srv.kill(); fs.rmSync(dir, { recursive: true, force: true });
  console.log(fails ? fails + ' FAILED' : 'test_plink: all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
