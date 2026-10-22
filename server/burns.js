'use strict';
// The public burn log: every burn of the coin, read straight from Solana, so nobody has to take our word for it.
//   GET /burns -> { on, mint, decimals, supply0, supply, burned, official, launch, others, wallets, list, updated }
//
// Two numbers, both from the chain:
//   burned   = the starting supply minus the supply Solana reports now. It counts EVERY burn by anyone (the Snake Bite in
//              the launch transaction, the fee wallet's buy-and-burns, Acid Pit burns, website ad burns).
//   list     = each burn signed by an official wallet (the fee wallet and the creator wallet), with its transaction, so
//              each one can be opened on Solscan. Found by reading every transaction of those wallets' token accounts.
// The server only READS the chain. It holds no keys and sends nothing: every burn is signed by the wallet's owner.
//
// Settings: the coin = Render's CAPES_MINT, else `capesMint` in config.js (empty = off). Wallets = LP_PARTNER / config.js
// launchpad.partner (fee wallet), CAPES_CREATOR / config.js capesCreator, plus BURN_WALLETS (space separated).
// Starting supply = CAPES_SUPPLY0 / config.js capesSupply0 (whole tokens), default 1,000,000,000.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ALPHA = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const isAddr = (s) => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(s || '');
function b58d(s) {
  let n = 0n; for (const c of s) { const i = ALPHA.indexOf(c); if (i < 0) return null; n = n * 58n + BigInt(i); }
  const out = []; while (n > 0n) { out.unshift(Number(n & 255n)); n >>= 8n; }
  for (const c of s) { if (c !== '1') break; out.unshift(0); }
  return Buffer.from(out);
}
function b58e(buf) {
  let n = 0n; for (const b of buf) n = n * 256n + BigInt(b);
  let s = ''; while (n > 0n) { s = ALPHA[Number(n % 58n)] + s; n /= 58n; }
  for (const b of buf) { if (b !== 0) break; s = '1' + s; }
  return s;
}
// ed25519: is this 32-byte string a point on the curve? (program addresses must NOT be)
const P = 2n ** 255n - 19n, D = (-121665n * modInv(121666n)) % P;
function modPow(b, e) { let r = 1n; b %= P; if (b < 0n) b += P; while (e > 0n) { if (e & 1n) r = r * b % P; b = b * b % P; e >>= 1n; } return r; }
function modInv(a) { return modPow(((a % P) + P) % P, P - 2n); }
function onCurve(bytes) {
  const b = Buffer.from(bytes); const sign = b[31] >> 7; b[31] &= 127;
  let y = 0n; for (let i = 31; i >= 0; i--) y = (y << 8n) | BigInt(b[i]);
  if (y >= P) return false;
  const y2 = y * y % P, u = (y2 - 1n + P) % P, v = ((D + P) % P * y2 + 1n) % P;
  const x2 = u * modInv(v) % P;
  if (x2 === 0n) return sign === 0;
  return modPow(x2, (P - 1n) / 2n) === 1n;   // x² must be a square
}
const TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PhnBqCXEpPxuEb';
const ATA_PROG = 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL';
function ata(owner, mint, prog) {
  const seeds = [b58d(owner), b58d(prog), b58d(mint)], pid = b58d(ATA_PROG);
  for (let bump = 255; bump >= 0; bump--) {
    const h = crypto.createHash('sha256').update(Buffer.concat([...seeds, Buffer.from([bump]), pid, Buffer.from('ProgramDerivedAddress')])).digest();
    if (!onCurve(h)) return b58e(h);
  }
  return '';
}

module.exports = function burns({ DATA, now, off }) {
  const cfgText = () => { try { return fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8'); } catch (e) { return ''; } };
  const cfg = cfgText();
  const fromCfg = (k) => { const m = new RegExp('\\b' + k + ':\\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"').exec(cfg); return m ? m[1] : ''; };
  const MINT = off ? '' : process.env.CAPES_MINT || fromCfg('capesMint');
  const RPC = process.env.SOLANA_RPC || 'https://api.mainnet-beta.solana.com';
  const SUPPLY0 = BigInt(Math.round(+(process.env.CAPES_SUPPLY0 || (/\bcapesSupply0:\s*([0-9_]+)/.exec(cfg) || [])[1]?.replace(/_/g, '') || 1e9)));
  const EVERY = +(process.env.BURNS_MS || 10 * 60e3);
  const WALLETS = [];
  const add = (address, label) => { if (isAddr(address) && address !== MINT && !WALLETS.some(w => w.address === address)) WALLETS.push({ address, label }); };
  add(process.env.LP_PARTNER || fromCfg('partner'), 'Fee wallet');
  add(process.env.CAPES_CREATOR || fromCfg('capesCreator'), 'Creator wallet');
  for (const w of String(process.env.BURN_WALLETS || '').split(/[\s,]+/)) add(w, 'Official wallet');
  const FILE = path.join(DATA, 'burns.json');

  let S = { mint: MINT, accounts: {}, list: [], supply: null, decimals: null, t: 0, err: '' };
  try { const j = JSON.parse(fs.readFileSync(FILE, 'utf8')); if (j && j.mint === MINT) S = { ...S, ...j }; } catch (e) { }
  const save = () => { try { fs.writeFileSync(FILE + '.tmp', JSON.stringify(S)); fs.renameSync(FILE + '.tmp', FILE); } catch (e) { } };

  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  async function rpc(method, params) {
    for (let i = 0; ; i++) {
      const r = await fetch(RPC, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }), signal: AbortSignal.timeout(20000) });
      if (r.status === 429 && i < 3) { await wait(1500 * (i + 1)); continue; }
      const j = await r.json(); if (j.error) throw new Error(j.error.message || 'rpc error'); return j.result;
    }
  }

  // every burn of MINT in one parsed transaction, from accounts in `mine`
  function burnsIn(tx, mine) {
    const out = [], ixs = [...(tx.transaction?.message?.instructions || [])];
    for (const g of tx.meta?.innerInstructions || []) ixs.push(...(g.instructions || []));
    const memo = ixs.filter(x => x.program === 'spl-memo' && typeof x.parsed === 'string').map(x => x.parsed).join(' ').slice(0, 80);
    const launch = (tx.meta?.logMessages || []).some(l => /Instruction: InitializeVirtualPool/.test(l));
    for (const x of ixs) {
      if (x.program !== 'spl-token' && x.program !== 'spl-token-2022') continue;
      const p = x.parsed; if (!p || (p.type !== 'burn' && p.type !== 'burnChecked')) continue;
      const i = p.info || {}; if (i.mint !== MINT || !mine.has(i.account)) continue;
      const amt = String(i.tokenAmount?.amount ?? i.amount ?? '0'); if (!/^\d+$/.test(amt)) continue;
      out.push({ amount: amt, account: i.account, memo, kind: launch ? 'launch' : /acid/i.test(memo) ? 'acid' : 'burn' });
    }
    return out;
  }

  let busy = false;
  async function scan() {
    if (!MINT || busy) return; busy = true;
    try {
      const sup = await rpc('getTokenSupply', [MINT, { commitment: 'confirmed' }]);
      S.supply = String(sup.value.amount); S.decimals = sup.value.decimals | 0;
      // token accounts: the two associated ones (classic and Token-2022) plus any other the wallet holds
      for (const w of WALLETS) {
        for (const prog of [TOKEN, TOKEN22]) { const a = ata(w.address, MINT, prog); if (a && !S.accounts[a]) S.accounts[a] = { w: w.address, last: '' }; }
        try {
          const r = await rpc('getTokenAccountsByOwner', [w.address, { mint: MINT }, { encoding: 'jsonParsed', commitment: 'confirmed' }]);
          for (const x of r.value || []) if (!S.accounts[x.pubkey]) S.accounts[x.pubkey] = { w: w.address, last: '' };
        } catch (e) { }
      }
      const mine = new Set(Object.keys(S.accounts)), seen = new Set(S.list.map(b => b.sig));
      let fetched = 0;
      for (const [acct, a] of Object.entries(S.accounts)) {
        const sigs = []; let before;
        for (let page = 0; page < 10; page++) {
          const opt = { limit: 1000, commitment: 'confirmed' }; if (a.last) opt.until = a.last; if (before) opt.before = before;
          const r = await rpc('getSignaturesForAddress', [acct, opt]);
          sigs.push(...r); if (r.length < 1000) break; before = r[r.length - 1].signature;
        }
        if (!sigs.length) continue;
        let done = true;
        for (const s of sigs.slice().reverse()) {   // oldest first, so `last` only moves past what was read
          if (s.err || seen.has(s.signature)) { a.last = s.signature; continue; }
          if (fetched >= 300) { done = false; break; }   // the rest next round
          fetched++;
          const tx = await rpc('getTransaction', [s.signature, { encoding: 'jsonParsed', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]);
          if (tx && !tx.meta?.err) for (const b of burnsIn(tx, mine)) {
            const w = WALLETS.find(x => x.address === S.accounts[b.account]?.w);
            S.list.push({ sig: s.signature, ts: tx.blockTime || s.blockTime || 0, amount: b.amount, wallet: w ? w.address : '', label: w ? w.label : '', kind: b.kind, memo: b.memo });
            seen.add(s.signature);
          }
          a.last = s.signature;
          await wait(120);
        }
        if (!done) break;
      }
      S.list.sort((x, y) => y.ts - x.ts); S.list = S.list.slice(0, 1000);
      S.t = now(); S.err = '';
    } catch (e) { S.err = String(e.message || e).slice(0, 120); }
    finally { busy = false; save(); }
  }
  if (MINT) { setTimeout(scan, +(process.env.BURNS_FIRST_MS || 20e3)); setInterval(scan, EVERY); }

  const sum = (f) => S.list.filter(f).reduce((a, b) => a + BigInt(b.amount), 0n);
  function view() {
    if (!MINT) return { on: false, wallets: WALLETS };
    const dec = S.decimals, base = dec == null ? null : SUPPLY0 * 10n ** BigInt(dec);
    const burned = base != null && S.supply != null ? (base > BigInt(S.supply) ? base - BigInt(S.supply) : 0n) : null;
    const official = sum(() => true), launch = sum(b => b.kind === 'launch');
    return {
      on: true, mint: MINT, decimals: dec, supply0: base == null ? null : String(base), supply: S.supply,
      burned: burned == null ? null : String(burned), official: String(official), launch: String(launch),
      others: burned == null ? null : String(burned > official ? burned - official : 0n),
      wallets: WALLETS, list: S.list.slice(0, 100), updated: S.t || null, stale: !!S.err,
    };
  }
  async function http(req, res, url, json) {
    if (url.pathname !== '/burns' || req.method !== 'GET') return false;
    return json(view());
  }
  return { http, scan, view, _ata: ata, _burnsIn: burnsIn };
};
