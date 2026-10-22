'use strict';
// Withdrawals against a fake Solana RPC and a throwaway server with the wait shortened to about 3 seconds:
// coins leave the bank, the 24-hour cap, the pot cap, cancel = coins back, ready = no cancel, payouts recorded only
// when the chain shows them, refuse = coins back.   Run: node test_withdraw.js
const { spawn } = require('child_process');
const http = require('http'), crypto = require('crypto'), fs = require('fs'), os = require('os'), path = require('path');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mc-wd-'));
const PORT = 19500 + Math.floor(Math.random() * 400), RPCPORT = PORT + 500;
const MINT = 'CapesMint1111111111111111111111111111111111', POT = 'PotWa11et11111111111111111111111111111111111';
let fails = 0, n = 0;
const ok = (c, msg) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + msg); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

let potUi = 150;
const TXS = {};
const rpcSrv = http.createServer((req, res) => {
  let b = ''; req.on('data', d => b += d); req.on('end', () => {
    const q = JSON.parse(b); let result = null;
    if (q.method === 'getTokenSupply') result = { value: { amount: String(1e15), decimals: 6 } };
    if (q.method === 'getTransaction') result = TXS[q.params[0]] || null;
    if (q.method === 'getTokenAccountsByOwner') {
      const ui = q.params[0] === POT ? potUi : 0;
      result = { value: ui ? [{ account: { data: { parsed: { info: { tokenAmount: { amount: String(ui * 1e6), uiAmount: ui } } } } } }] : [] };
    }
    res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ jsonrpc: '2.0', id: q.id, result }));
  });
}).listen(RPCPORT);
const payTx = (to, ui, signer) => ({ meta: { err: null, preTokenBalances: [{ mint: MINT, owner: to, uiTokenAmount: { uiAmount: 1 } }], postTokenBalances: [{ mint: MINT, owner: to, uiTokenAmount: { uiAmount: 1 + ui } }] },
  transaction: { message: { accountKeys: [{ pubkey: signer, signer: true }, { pubkey: to, signer: false }] } } });

const A58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function enc58(buf) { let x = BigInt('0x' + buf.toString('hex')), s = ''; while (x > 0n) { s = A58[Number(x % 58n)] + s; x /= 58n; } for (const y of buf) { if (y) break; s = '1' + s; } return s; }
function wallet() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  return { addr: enc58(publicKey.export({ format: 'der', type: 'spki' }).subarray(12)), sign: msg => crypto.sign(null, Buffer.from(msg, 'utf8'), privateKey).toString('base64') };
}

const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, CAPES_MINT: MINT, SOLANA_RPC: 'http://127.0.0.1:' + RPCPORT,
  POT_WALLET: POT, WITHDRAWALS: '1', WITHDRAW_DAYS: '0.00004', ADMIN_NAMES: 'Alice', HOLDER_DAYS: '14', CREWS: '0', BATTLE_CLOCK: '0' }, stdio: ['ignore', 'pipe', 'inherit'] });
function client() {
  const ws = new WebSocket('ws://127.0.0.1:' + PORT + '/ws', { headers: { origin: 'http://localhost:8000' } });
  const C = { ws, got: [], waiters: [] };
  ws.onmessage = e => { const m = JSON.parse(e.data); C.got.push(m); C.waiters = C.waiters.filter(w => { if (w.f(m)) { w.r(m); return false; } return true; }); };
  C.send = o => ws.send(JSON.stringify(o));
  C.next = (t, f = () => true, ms = 5000) => new Promise((r, j) => {
    const hit = C.got.find(m => m.t === t && f(m)); if (hit) { C.got.splice(C.got.indexOf(hit), 1); return r(hit); }
    const w = { f: m => m.t === t && f(m), r: m => { C.got.splice(C.got.indexOf(m), 1); r(m); } }; C.waiters.push(w);
    setTimeout(() => j(new Error('timeout waiting for ' + t)), ms);
  });
  C.say = (re) => C.next('info', m => re.test(m.text));
  C.open = new Promise(r => ws.onopen = r);
  C.link = async w => { C.send({ t: 'walletNonce', wallet: w.addr }); const s = await C.next('walletSign'); C.send({ t: 'walletLink', wallet: w.addr, sig: w.sign(s.msg) }); return C.next('holder', m => m.wallet === w.addr); };
  C.bank = async () => { C.send({ t: 'pull' }); return (await C.next('resync')).save.bank; };
  C.info = async () => { C.send({ t: 'wdInfo' }); return C.next('wd'); };
  return C;
}

(async () => {
  await new Promise(r => srv.stdout.on('data', d => { if (String(d).includes('port')) r(); }));
  const a = client(), b = client(); await a.open; await b.open;
  a.send({ t: 'register', name: 'Alice', pass: 'password1' }); await a.next('welcome');
  b.send({ t: 'register', name: 'Bobby', pass: 'password2' }); await b.next('welcome');
  a.send({ t: 'save', st: { coins: 0, bank: 20000, inv: [], xp: {} }, rev: 0 }); await a.next('saved');
  b.send({ t: 'save', st: { coins: 0, bank: 300, inv: [], xp: {} }, rev: 0 }); await b.next('saved');

  let i = await a.info();
  ok(i.open && i.days > 0 && i.rate === 100 && i.dayMax === 100 && i.room === 150, 'open, rate 100, 100 a day, room = what the pot holds');
  a.send({ t: 'withdraw', capes: 10 }); ok(!!(await a.say(/Link your wallet first/)), 'no linked wallet: refused');
  const w1 = wallet(), w2 = wallet(); await a.link(w1); await b.link(w2);

  a.send({ t: 'withdraw', capes: 0 }); ok(!!(await a.say(/at least 1/)), 'zero refused');
  a.send({ t: 'withdraw', capes: 50 }); const d1 = await a.next('wdBank');
  ok(d1.delta === -5000, 'the coins leave the bank (50 x 100)');
  i = await a.next('wd'); ok(i.list.length === 1 && i.list[0].status === 'waiting' && i.list[0].due > Date.now(), 'request #1 waiting with a due date');
  ok(await a.bank() === 15000, 'server save: bank 15,000');
  a.send({ t: 'withdraw', capes: 60 }); ok(!!(await a.say(/in any 24 hours\. 50 left/)), '24-hour cap: 50 + 60 > 100 refused');
  a.send({ t: 'withdraw', capes: 50 }); await a.next('wdBank'); i = await a.next('wd');
  ok(i.dayLeft === 0 && i.room === 50, 'second 50 ok: nothing left today, pot room 50');
  a.send({ t: 'withdraw', capes: 1 }); ok(!!(await a.say(/0 left right now/)), 'day used up');

  b.send({ t: 'withdraw', capes: 5 }); ok(!!(await b.say(/You need 500 Meme Coins/)), 'not enough in the bank: refused, nothing taken');
  b.send({ t: 'save', st: { coins: 0, bank: 9000, inv: [], xp: {} }, rev: (await (async () => { b.send({ t: 'pull' }); return (await b.next('resync')).rev; })()) }); await b.next('saved');
  b.send({ t: 'withdraw', capes: 60 }); ok(!!(await b.say(/pot can cover 50 more/)), 'pot cap: only what the pot holds can be waiting');
  b.send({ t: 'withdraw', capes: 50 }); await b.next('wdBank'); i = await b.next('wd'); ok(i.room === 0, 'pot fully booked');
  potUi = 200;   // the pot grows

  // cancel during the wait: coins come back
  i = await a.info(); const first = i.list.find(x => x.capes === 50 && x.status === 'waiting');
  a.send({ t: 'withdrawCancel', id: first.id }); const d2 = await a.next('wdBank'); i = await a.next('wd');
  ok(d2.delta === 5000 && i.list.find(x => x.id === first.id).status === 'cancelled', 'cancel: 5,000 Meme Coins back, status cancelled');
  ok(await a.bank() === 15000, 'server save after cancel: 15,000');
  i = await a.info(); ok(i.dayLeft === 50, 'a cancelled request frees the 24-hour cap');

  // after the wait: ready, can't be cancelled
  await wait(3800);
  i = await a.info(); const second = i.list.find(x => x.status === 'ready');
  ok(!!second, 'after the wait the request is ready');
  a.send({ t: 'withdrawCancel', id: second.id }); ok(!!(await a.say(/payout queue/)), 'a ready request cannot be cancelled');

  // payouts: only what the chain shows, signed by the pot wallet
  TXS['T'.repeat(87) + 'a'] = payTx(w1.addr, 10, POT);
  TXS['T'.repeat(87) + 'b'] = payTx(w1.addr, 50, 'SomeoneE1se1111111111111111111111111111111');
  TXS['T'.repeat(87) + 'c'] = payTx(w1.addr, 50, POT);
  a.send({ t: 'chat', text: '/withdraw list' }); ok(!!(await a.say(/READY/)), '/withdraw list shows READY');
  a.send({ t: 'chat', text: '/withdraw paid ' + second.id + ' ' + 'T'.repeat(87) + 'a' }); ok(!!(await a.say(/not 50/)), 'too small a payment is not recorded');
  a.send({ t: 'chat', text: '/withdraw paid ' + second.id + ' ' + 'T'.repeat(87) + 'b' }); ok(!!(await a.say(/not signed by the pot wallet/)), 'a payment from another wallet is not recorded');
  a.send({ t: 'chat', text: '/withdraw paid ' + second.id + ' ' + 'T'.repeat(87) + 'c' }); ok(!!(await a.say(/is paid/)), 'the player is told it is paid');
  i = await a.info(); ok(i.list.find(x => x.id === second.id).status === 'paid', 'status paid');
  a.send({ t: 'chat', text: '/withdraw paid ' + second.id + ' ' + 'T'.repeat(87) + 'c' }); ok(!!(await a.say(/not open/)), 'cannot be paid twice');

  // refuse: coins back to the player
  i = await b.info(); const bobs = i.list[0];
  a.send({ t: 'chat', text: '/withdraw refuse ' + bobs.id + ' farming bots.' });
  const d3 = await b.next('wdBank'); ok(d3.delta === 5000, 'refused: the coins go back');
  ok(!!(await b.say(/refused: farming bots/)), 'the player is told why');

  // public numbers
  const pub = await (await fetch('http://127.0.0.1:' + PORT + '/withdrawals')).json();
  ok(pub.open && pub.paid.count === 1 && pub.paid.capes === 50 && pub.pot >= 150 && pub.days > 0, 'GET /withdrawals: open, 1 paid (50), pot shown');
  // a non-admin can't run the command
  b.send({ t: 'chat', text: '/withdraw list' }); await wait(500);
  ok(!b.got.some(m => m.t === 'info' && /READY|No withdrawals/.test(m.text)), 'players cannot use /withdraw');

  console.log(fails ? fails + ' FAILED' : 'all ' + n + ' withdrawal checks pass');
  srv.kill(); rpcSrv.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); process.exit(1); });
