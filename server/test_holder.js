'use strict';
// Holder perks test: a fake Solana RPC, a real ed25519 wallet key, a throwaway server with the holding period shortened
// to about 2 seconds. Checks signing, the 1% line, the free skin timer, and that tokens passed to a second wallet
// do not give a second free skin straight away.   Run: node test_holder.js
const { spawn } = require('child_process');
const http = require('http'), crypto = require('crypto'), fs = require('fs'), os = require('os'), path = require('path');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-hold-'));
const PORT = 19000 + Math.floor(Math.random() * 500), RPCPORT = PORT + 600;
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

// ---- fake chain: total supply 1,000,000,000 (6 decimals); balances by wallet
const SUPPLY = 1000000000n * 1000000n, BAL = {};
const rpcSrv = http.createServer((req, res) => {
  let b = ''; req.on('data', d => b += d); req.on('end', () => {
    const q = JSON.parse(b); let result;
    if (q.method === 'getTokenSupply') result = { value: { amount: String(SUPPLY), decimals: 6 } };
    if (q.method === 'getTokenAccountsByOwner') { const a = BAL[q.params[0]] || 0n; result = { value: a ? [{ account: { data: { parsed: { info: { tokenAmount: { amount: String(a) } } } } } }] : [] }; }
    res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ jsonrpc: '2.0', id: q.id, result }));
  });
}).listen(RPCPORT);

const A58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function enc58(buf) { let n = BigInt('0x' + buf.toString('hex')), s = ''; while (n > 0n) { s = A58[Number(n % 58n)] + s; n /= 58n; } for (const x of buf) { if (x) break; s = '1' + s; } return s; }
function wallet() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const raw = publicKey.export({ format: 'der', type: 'spki' }).subarray(12);
  return { addr: enc58(raw), sign: msg => crypto.sign(null, Buffer.from(msg, 'utf8'), privateKey).toString('base64') };
}

const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, CAPES_MINT: 'CapesMint1111111111111111111111111111111111', SOLANA_RPC: 'http://127.0.0.1:' + RPCPORT, HOLDER_DAYS: '0.00002' }, stdio: ['ignore', 'pipe', 'inherit'] });
function client(name) {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000' } });
  const C = { ws, name, got: [], waiters: [] };
  ws.onmessage = e => { const m = JSON.parse(e.data); C.got.push(m); C.waiters = C.waiters.filter(w => { if (w.f(m)) { w.r(m); return false; } return true; }); };
  C.send = o => ws.send(JSON.stringify(o));
  C.next = (t, f = () => true, ms = 4000) => new Promise((r, j) => { const hit = C.got.find(m => m.t === t && f(m)); if (hit) { C.got.splice(C.got.indexOf(hit), 1); return r(hit); } C.waiters.push({ f: m => m.t === t && f(m), r: m => { C.got.splice(C.got.indexOf(m), 1); r(m); } }); setTimeout(() => j(new Error(name + ' waited for ' + t)), ms); });
  C.open = new Promise(r => ws.onopen = r);
  C.link = async w => { C.send({ t: 'walletNonce', wallet: w.addr }); const s = await C.next('walletSign'); C.send({ t: 'walletLink', wallet: w.addr, sig: w.sign(s.msg) }); return C.next('holder', m => m.wallet === w.addr); };
  return C;
}

(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  const a = client('Alice'), b = client('Bobby'); await a.open; await b.open;
  a.send({ t: 'register', name: 'Alice', pass: 'password1' }); await a.next('welcome'); ok(!(await a.next('holder')).wallet, 'login sends holder info (no wallet yet)');
  b.send({ t: 'register', name: 'Bobby', pass: 'password2' }); await b.next('welcome'); await b.next('holder');
  a.send({ t: 'save', st: { coins: 0, bank: 0, inv: [], xp: {} }, rev: 0 }); await a.next('saved');
  b.send({ t: 'save', st: { coins: 0, bank: 0, inv: [], xp: {} }, rev: 0 }); await b.next('saved');

  const w1 = wallet(), w2 = wallet(), thief = wallet();
  BAL[w1.addr] = SUPPLY / 200n;  // 0.5%
  // a wrong signature (someone else's wallet address, signed with a different key) is refused
  a.send({ t: 'walletNonce', wallet: w1.addr }); const s0 = await a.next('walletSign');
  ok(s0.msg.includes('not a transaction') && s0.msg.includes('Alice'), 'sign message says it is free and names the account');
  a.send({ t: 'walletLink', wallet: w1.addr, sig: thief.sign(s0.msg) }); ok((await a.next('err')).text.includes('did not match'), 'signature from another key refused');

  let h = await a.link(w1); ok(h.pct === 0.5 && !h.member && !h.canClaim, 'linked with 0.5%: no perks');
  BAL[w1.addr] = SUPPLY / 100n;  // 1%
  a.send({ t: 'walletUnlink' }); await a.next('holder'); h = await a.link(w1); ok(h.pct === 1 && h.member && !h.canClaim, 'at 1%: Cape Club on, free skin not ready yet');
  a.send({ t: 'holderClaim', skin: 'sk_laser' }); ok(!!(await a.next('info', m => m.text.includes('not ready'))), 'claim before the holding period refused');
  b.send({ t: 'walletNonce', wallet: w1.addr }); const sb = await b.next('walletSign'); b.send({ t: 'walletLink', wallet: w1.addr, sig: w1.sign(sb.msg) });
  ok((await b.next('err')).text.includes('another MemeCapes account'), 'one wallet cannot serve two accounts');

  await wait(2200);
  a.send({ t: 'holderInfo' }); h = await a.next('holder'); ok(h.canClaim, 'after the holding period the free skin is ready');
  a.send({ t: 'holderClaim', skin: 'nope' }); a.send({ t: 'holderClaim', skin: 'sk_laser' });
  const g = await a.next('skinGift'); ok(g.skin === 'sk_laser' && g.skins.includes('sk_laser') && g.rev === 2, 'free skin added to the saved progress');
  h = await a.next('holder'); ok(!h.canClaim && h.claims === 1, 'next free skin waits another period');
  a.send({ t: 'holderClaim', skin: 'sk_moon' }); ok(!!(await a.next('info', m => m.text.includes('not ready'))), 'no second skin in the same period');

  // Alice passes her tokens to Bobby's wallet: her membership ends at the next check, his skin needs its own full period
  BAL[w1.addr] = 0n; BAL[w2.addr] = SUPPLY / 100n;
  h = await b.link(w2); ok(h.member && !h.canClaim, 'tokens moved to a new wallet: Cape Club yes, free skin not straight away');
  a.send({ t: 'walletUnlink' }); await a.next('holder'); h = await a.link(w1); ok(!h.member && h.pct === 0, 'the emptied wallet loses its perks');
  b.send({ t: 'holderClaim', skin: 'sk_moon' }); ok(!!(await b.next('info', m => m.text.includes('not ready'))), 'second wallet must hold for the full period too');

  console.log(fails ? fails + ' FAILED' : 'all holder checks passed');
  srv.kill(); rpcSrv.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); rpcSrv.close(); process.exit(1); });
