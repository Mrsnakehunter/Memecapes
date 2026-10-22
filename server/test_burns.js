'use strict';
// The public burn log against a fake Solana RPC. Run: node server/test_burns.js
const http = require('http'); const assert = require('assert'); const fs = require('fs'); const os = require('os'); const path = require('path');
const MINT = 'CapesMint1111111111111111111111111111111111';
const FEE = '3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg', CREATOR = 'FNxqFAcSVnfyLdB57yoRnwjdPesKWAtnU9dGNjNMz9Ns';
const OTHER_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
const TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'burns-'));
let B, FEE_ATA, CR_ATA, supply = 1e15 - 1e14 - 5e11 - 1e11, txCalls = 0;
const sigs = {}; const txs = {};
const ix = (type, info, program = 'spl-token') => ({ program, parsed: { type, info } });
function tx(sig, ts, ixs, inner = [], logs = [], err = null) { txs[sig] = { blockTime: ts, meta: { err, innerInstructions: inner.length ? [{ index: 0, instructions: inner }] : [], logMessages: logs }, transaction: { message: { instructions: ixs } } }; }
const rpc = http.createServer((req, res) => {
  let body = ''; req.on('data', c => body += c); req.on('end', () => {
    const { method, params } = JSON.parse(body); let result = null;
    if (method === 'getTokenSupply') result = { value: { amount: String(supply), decimals: 6 } };
    if (method === 'getTokenAccountsByOwner') result = { value: [] };
    if (method === 'getSignaturesForAddress') {
      const all = (sigs[params[0]] || []).slice().sort((a, b) => b.blockTime - a.blockTime), until = params[1].until;
      const i = until ? all.findIndex(s => s.signature === until) : -1; result = i >= 0 ? all.slice(0, i) : all;
    }
    if (method === 'getTransaction') { txCalls++; result = txs[params[0]] || null; }
    res.end(JSON.stringify({ jsonrpc: '2.0', id: 1, result }));
  });
});
rpc.listen(0, async () => {
  Object.assign(process.env, { SOLANA_RPC: 'http://127.0.0.1:' + rpc.address().port, CAPES_MINT: MINT, LP_PARTNER: FEE, CAPES_CREATOR: CREATOR, BURNS_FIRST_MS: '999999999', BURNS_MS: '999999999' });
  B = require('./burns')({ DATA: dir, now: Date.now });
  FEE_ATA = B._ata(FEE, MINT, TOKEN); CR_ATA = B._ata(CREATOR, MINT, TOKEN);
  // the launch: the creator buys and burns 10% in the transaction that makes the pool (burn is an inner-free top-level ix)
  tx('launchSig', 1000, [ix('burnChecked', { mint: MINT, account: CR_ATA, authority: CREATOR, tokenAmount: { amount: '100000000000000' } })], [], ['Program log: Instruction: InitializeVirtualPoolWithSplToken']);
  // the fee wallet: a buy (no burn), then a buy-and-burn with a memo, a failed burn, a burn of another coin
  tx('buySig', 2000, [ix('transfer', { mint: MINT, source: 'x', destination: FEE_ATA, amount: '7' })]);
  tx('feeBurnSig', 3000, [ix('memo', 0, 'x')], [ix('burnChecked', { mint: MINT, account: FEE_ATA, authority: FEE, tokenAmount: { amount: '500000000000' } }), { program: 'spl-memo', parsed: 'snakepit burn' }]);
  tx('failSig', 3500, [ix('burn', { mint: MINT, account: FEE_ATA, authority: FEE, amount: '999' })], [], [], { InstructionError: [0, 'x'] });
  tx('otherMintSig', 3600, [ix('burn', { mint: OTHER_MINT, account: FEE_ATA, authority: FEE, amount: '5' })]);
  sigs[CR_ATA] = [{ signature: 'launchSig', blockTime: 1000, err: null }];
  sigs[FEE_ATA] = ['buySig', 'feeBurnSig', 'otherMintSig'].map(s => ({ signature: s, blockTime: txs[s].blockTime, err: null })).concat([{ signature: 'failSig', blockTime: 3500, err: { x: 1 } }]);

  const get = async () => { let out; await B.http({ method: 'GET' }, {}, new URL('/burns', 'http://x'), (o) => { out = o; }); return out; };
  let v = await get(); assert.strictEqual(v.on, true); assert.strictEqual(v.list.length, 0, 'nothing before the first scan');
  await B.scan(); v = await get();
  assert.strictEqual(v.list.length, 2, 'launch burn + fee burn only'); assert.strictEqual(txCalls, 4, 'failed tx never fetched');
  assert.strictEqual(v.list[0].sig, 'feeBurnSig'); assert.strictEqual(v.list[0].label, 'Fee wallet'); assert.strictEqual(v.list[0].memo, 'snakepit burn');
  assert.strictEqual(v.list[1].kind, 'launch'); assert.strictEqual(v.list[1].label, 'Creator wallet'); assert.strictEqual(v.launch, '100000000000000');
  assert.strictEqual(v.burned, String(1e14 + 5e11 + 1e11), 'total = start supply - supply now');
  assert.strictEqual(v.official, String(1e14 + 5e11)); assert.strictEqual(v.others, String(1e11), 'burns by anyone else');
  // a new burn: only it is read
  tx('feeBurn2', 5000, [ix('burn', { mint: MINT, account: FEE_ATA, authority: FEE, amount: '250' })]);
  sigs[FEE_ATA].push({ signature: 'feeBurn2', blockTime: 5000, err: null }); supply -= 250;
  await B.scan(); v = await get();
  assert.strictEqual(txCalls, 5, 'second scan reads only the new transaction'); assert.strictEqual(v.list.length, 3); assert.strictEqual(v.list[0].amount, '250');
  // survives a restart (from burns.json), and the answer never carries anything but the fields above
  delete require.cache[require.resolve('./burns')]; const B2 = require('./burns')({ DATA: dir, now: Date.now });
  let o; await B2.http({ method: 'GET' }, {}, new URL('/burns', 'http://x'), (x) => { o = x; }); assert.strictEqual(o.list.length, 3);
  assert.strictEqual(await B.http({ method: 'GET' }, {}, new URL('/other', 'http://x'), () => { }), false);
  // off without a coin
  // the real config.js carries the live coin now, so the 'off' case is checked with a mint that can't be a coin
  delete require.cache[require.resolve('./burns')]; process.env.CAPES_MINT = ''; const B3 = require('./burns')({ DATA: fs.mkdtempSync(path.join(os.tmpdir(), 'burns-')), now: Date.now, off: true });
  await B3.http({ method: 'GET' }, {}, new URL('/burns', 'http://x'), (x) => { o = x; });
  assert.strictEqual(o.on, false); assert.ok(o.wallets.some(w => w.address === FEE));
  console.log('test_burns: 20 checks passed'); rpc.close(); process.exit(0);
});
