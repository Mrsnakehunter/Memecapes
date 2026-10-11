'use strict';
// Holder perks and partners test: a fake Solana RPC, a real ed25519 wallet key, a throwaway server with the holding period shortened
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
const SUPPLY = 1000000000n * 1000000n, BAL = {}, TXS = {};
const burnTx = (auth, amount, mint) => ({ meta: { err: null, innerInstructions: [] }, transaction: { message: { instructions: [{ program: 'spl-token', parsed: { type: 'burnChecked', info: { mint: mint || 'CapesMint1111111111111111111111111111111111', authority: auth, account: 'x', tokenAmount: { amount: String(amount) } } } }] } } });
const fakeSig = n => 'S'.repeat(80) + n;
const rpcSrv = http.createServer((req, res) => {
  let b = ''; req.on('data', d => b += d); req.on('end', () => {
    const q = JSON.parse(b); let result;
    if (q.method === 'getTokenSupply') result = { value: { amount: String(SUPPLY), decimals: 6 } };
    if (q.method === 'getTransaction') result = TXS[q.params[0]] || null;
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

const srv = spawn(process.execPath, [path.join(__dirname, 'server.js')], { env: { ...process.env, PORT, DATA_DIR: dir, CAPES_MINT: 'CapesMint1111111111111111111111111111111111', SOLANA_RPC: 'http://127.0.0.1:' + RPCPORT, HOLDER_DAYS: '0.00002', PARTNER_DAYS: '0.00004', PARTNER_CHECK_MS: '500', SWEEP_MS: '700', ADMIN_NAMES: 'Albert' }, stdio: ['ignore', 'pipe', 'inherit'] });
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

  // ---- partners: 3% for the partner period = billboard + NPC, approved by an admin, removed under 3%
  const cc = client('Carol'), ad = client('Albert'); await cc.open; await ad.open;
  cc.send({ t: 'register', name: 'Carol', pass: 'password3' }); await cc.next('welcome');
  ad.send({ t: 'register', name: 'Albert', pass: 'password4' }); await ad.next('welcome');
  const w3 = wallet(); BAL[w3.addr] = SUPPLY * 35n / 1000n;  // 3.5%
  await cc.link(w3); let pi = await cc.next('partner', m => m.over);
  ok(pi.over && !pi.eligible && !pi.live, '3.5% holder can make an ad but it is not live yet');
  const jpg = 'data:image/jpeg;base64,' + Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(200, 7)]).toString('base64');
  cc.send({ t: 'partnerSave', brand: 'Carol Coin', line: 'Hi', link: 'javascript:alert(1)', color: '#22aa44', img: jpg });
  ok((await cc.next('err')).text.includes('https://'), 'bad link refused');
  cc.send({ t: 'partnerSave', brand: 'Carol Coin', line: 'Gm from Carol Coin!', link: 'https://carolcoin.example', color: '#22aa44', img: 'data:image/png;base64,AAAA' });
  ok((await cc.next('err')).text.includes('picture'), 'non-JPEG picture refused');
  a.send({ t: 'partnerSave', brand: 'Alice', line: 'x', link: '', color: '#22aa44', img: jpg }); ok((await a.next('err')).text.includes('3%'), 'under 3% cannot send an ad');
  cc.send({ t: 'partnerSave', brand: 'Carol Coin', line: 'Gm from Carol Coin!', link: 'https://carolcoin.example', color: '#22aa44', img: jpg });
  pi = await cc.next('partner', m => m.ad); ok(pi.ad.status === 'pending' && !pi.live, 'ad saved, waiting for approval');
  ok(!!(await ad.next('info', m => m.text.includes('New partner ad from Carol'))), 'admin is told about the new ad');
  ad.send({ t: 'chat', text: '/partner view Carol' }); const rv = await ad.next('partnerReview'); ok(rv.brand === 'Carol Coin' && rv.img.startsWith('data:image/jpeg'), 'admin sees the ad and its picture');
  b.send({ t: 'chat', text: '/partner approve Carol' }); await wait(300);
  ok(!(await fetch('http://127.0.0.1:' + PORT + '/partners').then(r => r.json())).length, 'a non-admin cannot approve');
  await wait(3500);  // past the shortened partner period, then approve
  b.got = b.got.filter(m => m.t !== 'partners');
  ad.send({ t: 'chat', text: '/partner approve Carol' });
  const pl = await b.next('partners', m => m.list.length === 1); ok(pl.list[0].brand === 'Carol Coin' && pl.list[0].link === 'https://carolcoin.example', 'approved and held long enough: every player gets the ad');
  const im = await fetch('http://127.0.0.1:' + PORT + '/partners/' + pl.list[0].id + '.jpg'); ok(im.status === 200 && im.headers.get('access-control-allow-origin') === '*', 'billboard picture served to the game');
  BAL[w3.addr] = SUPPLY * 29n / 1000n;  // 2.9%
  b.got = b.got.filter(m => m.t !== 'partners');
  await b.next('partners', m => m.list.length === 0, 6000); ok(true, 'dropped below 3%: the ad is removed from the game');
  ok((await fetch('http://127.0.0.1:' + PORT + '/partners/' + pl.list[0].id + '.jpg')).status === 404, 'and its picture is no longer served');
  BAL[w3.addr] = SUPPLY * 35n / 1000n; await wait(2000);
  ok(!(await fetch('http://127.0.0.1:' + PORT + '/partners').then(r => r.json())).length, 'back above 3%: waits a full partner period again');
  await b.next('partners', m => m.list.length === 1, 9000); ok(true, 'after a new full period at 3% the ad comes back');

  // ---- website ads for burning 1%: approve first, then burn; the spot is shared by how much each burned
  const API = 'http://127.0.0.1:' + PORT, post = (path, body) => fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(async r => ({ status: r.status, ...(await r.json()) }));
  const bw = wallet(), bw2 = wallet();
  let nr = await post('/burnad/nonce', { wallet: bw.addr }); ok(nr.msg && nr.msg.includes('does not move or burn'), 'website ad: sign message says nothing is burned');
  let sr = await post('/burnad/submit', { wallet: bw.addr, sig: thief.sign(nr.msg), brand: 'Burn Bros', line: 'We burned 1%', link: 'https://burnbros.example', img: jpg });
  ok(sr.status === 400 && sr.error.includes('signature'), 'website ad: wrong wallet signature refused');
  nr = await post('/burnad/nonce', { wallet: bw.addr });
  sr = await post('/burnad/submit', { wallet: bw.addr, sig: bw.sign(nr.msg), brand: 'Burn Bros', line: 'We burned 1%', link: 'https://burnbros.example', img: jpg });
  ok(sr.ok && sr.status === 'pending', 'website ad sent, waiting for approval');
  ok(!!(await ad.next('info', m => m.text.includes('New website ad #' + sr.id))), 'admin is told about the website ad');
  TXS[fakeSig(1)] = burnTx(bw.addr, SUPPLY * 12n / 1000n);  // 1.2%
  let br = await post('/burnad/burn', { wallet: bw.addr, id: sr.id, burnSig: fakeSig(1) }); ok(br.status === 400 && br.error.includes('not approved yet'), 'cannot use a burn before the ad is approved');
  ad.send({ t: 'chat', text: '/burnad view ' + sr.id }); const bv = await ad.next('partnerReview', m => m.kind === 'burn'); ok(bv.brand === 'Burn Bros' && bv.img.startsWith('data:image/jpeg'), 'admin sees the website ad');
  ad.send({ t: 'chat', text: '/burnad approve ' + sr.id }); await ad.next('info', m => m.text.includes('approved'));
  TXS[fakeSig(2)] = burnTx(bw.addr, SUPPLY * 5n / 1000n);  // 0.5%
  br = await post('/burnad/burn', { wallet: bw.addr, id: sr.id, burnSig: fakeSig(2) }); ok(br.status === 400 && br.error.includes('under 1%'), 'a burn under 1% is refused');
  TXS[fakeSig(3)] = burnTx(bw2.addr, SUPPLY * 12n / 1000n);
  br = await post('/burnad/burn', { wallet: bw.addr, id: sr.id, burnSig: fakeSig(3) }); ok(br.status === 400 && br.error.includes('does not burn'), 'someone else\'s burn is refused');
  TXS[fakeSig(4)] = burnTx(bw.addr, SUPPLY * 12n / 1000n, 'OtherMint11111111111111111111111111111111111');
  br = await post('/burnad/burn', { wallet: bw.addr, id: sr.id, burnSig: fakeSig(4) }); ok(br.status === 400, 'burning a different token is refused');
  br = await post('/burnad/burn', { wallet: bw.addr, id: sr.id, burnSig: fakeSig(1) }); ok(br.ok && br.status === 'live', 'a 1.2% burn from the right wallet puts the ad live');
  let live = await fetch(API + '/burnads').then(r => r.json()); ok(live.length === 1 && live[0].brand === 'Burn Bros' && live[0].w === 1, 'the website gets the ad (1 share)');
  ok((await fetch(API + '/burnads/' + live[0].id + '.jpg')).status === 200, 'the website gets its picture');
  // a second burner with 2.5% gets 2 shares; the old burn can't be reused
  nr = await post('/burnad/nonce', { wallet: bw2.addr }); sr = await post('/burnad/submit', { wallet: bw2.addr, sig: bw2.sign(nr.msg), brand: 'Second', line: '', link: '', img: jpg });
  ad.send({ t: 'chat', text: '/burnad approve ' + sr.id }); await ad.next('info', m => m.text.includes('#' + sr.id));
  br = await post('/burnad/burn', { wallet: bw2.addr, id: sr.id, burnSig: fakeSig(1) }); ok(br.status === 400, 'a burn already used cannot be used again');
  TXS[fakeSig(5)] = burnTx(bw2.addr, SUPPLY * 25n / 1000n);
  br = await post('/burnad/burn', { wallet: bw2.addr, id: sr.id, burnSig: fakeSig(5) }); ok(br.ok, 'second burner live');
  live = await fetch(API + '/burnads').then(r => r.json()); ok(live.length === 2 && live.find(x => x.brand === 'Second').w === 2, 'shares follow the burn: 2.5% = 2 shares of the spot');
  const st2 = await post('/burnad/status', { wallet: bw2.addr }); ok(st2.live === 2 && st2.shares === 3 && st2.ads[0].status === 'live', 'status shows the spot is split 3 ways');

  console.log(fails ? fails + ' FAILED' : 'all holder checks passed');
  srv.kill(); rpcSrv.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); srv.kill(); rpcSrv.close(); process.exit(1); });
