/* MemeCapes Launchpad: wallet + Solana plumbing for launch.html.
   Wallets: any Solana wallet that supports the Wallet Standard (Phantom, Solflare, Backpack, ...). The page never sees a
   private key. It builds a transaction, the wallet shows it to the person, and only their own signature makes it real.
   The one exception is the brand-new coin address (the "mint"): it is a fresh key made in this page, used once to sign
   the coin's creation and then thrown away.                                                                          */
window.LPC = (function () {
  'use strict';
  const L = () => window.LPCORE;
  const CFG = () => (window.MC_CONFIG && window.MC_CONFIG.launchpad) || {};
  const NET = () => (new URLSearchParams(location.search).get('net') || CFG().network || 'mainnet');   // ?net=devnet for testing
  const RPC_URL = () => NET() === 'devnet' ? (CFG().rpcDevnet || 'https://api.devnet.solana.com') : (CFG().rpc || (window.MC_CONFIG && window.MC_CONFIG.rpc) || 'https://api.mainnet-beta.solana.com');
  const CHAIN = () => 'solana:' + (NET() === 'devnet' ? 'devnet' : 'mainnet');
  let conn = null, client = null;
  function connection() { if (!conn) conn = new (L().web3.Connection)(RPC_URL(), { commitment: 'confirmed', disableRetryOnRateLimit: false }); return conn; }
  function dbc() { if (!client) client = new (L().dbc.DynamicBondingCurveClient)(connection(), 'confirmed'); return client; }

  // ---- Wallet Standard (no wallet adapter library needed)
  const wallets = [];
  const listeners = new Set();
  function reg(...ws) {
    for (const w of ws) {
      if (!w || !w.features || !w.features['standard:connect']) continue;
      if (!(w.chains || []).some(c => String(c).startsWith('solana:'))) continue;
      if (!w.features['solana:signTransaction'] && !w.features['solana:signAndSendTransaction']) continue;
      if (wallets.some(x => x.name === w.name)) continue;
      wallets.push(w);
    }
    listeners.forEach(f => { try { f(wallets) } catch (e) { } });
    return () => { };
  }
  const api = Object.freeze({ register: reg });
  try { window.addEventListener('wallet-standard:register-wallet', e => { try { e.detail(api) } catch (_) { } }); window.dispatchEvent(new CustomEvent('wallet-standard:app-ready', { detail: api })); } catch (e) { }

  let W = null, ACC = null;   // the connected wallet and account
  const onChange = new Set();
  function emit() { onChange.forEach(f => { try { f(me()) } catch (e) { } }); }
  function me() { return ACC ? { name: W.name, icon: W.icon, address: ACC.address, pubkey: new (L().web3.PublicKey)(ACC.address) } : null; }
  async function connect(name) {
    const w = wallets.find(x => x.name === name) || wallets[0];
    if (!w) throw new Error('No Solana wallet found. Install Phantom, Solflare or Backpack, then reload this page.');
    const r = await w.features['standard:connect'].connect();
    const acc = (r && r.accounts && r.accounts[0]) || w.accounts[0];
    if (!acc) throw new Error('The wallet did not share an account.');
    W = w; ACC = acc;
    try { w.features['standard:events'] && w.features['standard:events'].on('change', () => { ACC = w.accounts[0] || null; if (!ACC) W = null; emit(); }); } catch (e) { }
    try { localStorage.setItem('lp_wallet', w.name); } catch (e) { }
    emit(); return me();
  }
  async function disconnect() { try { W && W.features['standard:disconnect'] && await W.features['standard:disconnect'].disconnect(); } catch (e) { } W = null; ACC = null; try { localStorage.removeItem('lp_wallet'); } catch (e) { } emit(); }
  async function autoConnect() { let n = null; try { n = localStorage.getItem('lp_wallet'); } catch (e) { } if (!n) return null; for (let i = 0; i < 10 && !wallets.some(w => w.name === n); i++) await sleep(150); const w = wallets.find(x => x.name === n); if (!w) return null; try { const r = await w.features['standard:connect'].connect({ silent: true }); const acc = (r && r.accounts && r.accounts[0]) || w.accounts[0]; if (acc) { W = w; ACC = acc; emit(); } } catch (e) { } return me(); }
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ---- priority fee: a small tip so transactions land when the network is busy
  async function priorityIx(writable) {
    const { web3 } = L(); let micro = CFG().minPriorityMicroLamports || 20000;
    try {
      const f = await connection().getRecentPrioritizationFees({ lockedWritableAccounts: (writable || []).slice(0, 5) });
      const v = f.map(x => x.prioritizationFee).filter(x => x > 0).sort((a, b) => a - b);
      if (v.length) micro = Math.max(micro, v[Math.floor(v.length * 0.75)]);
    } catch (e) { }
    micro = Math.min(micro, CFG().maxPriorityMicroLamports || 2000000);
    return web3.ComputeBudgetProgram.setComputeUnitPrice({ microLamports: micro });
  }

  /* Sign and send one or more transactions in order (one wallet pop-up when the wallet can sign several at once).
     extraSigners: [[Keypair,...], ...] partial signers per transaction (only fresh mint keys). Returns signatures. */
  async function sendAll(txs, extraSigners, onStep) {
    if (!ACC) throw new Error('Connect a wallet first.');
    const { web3 } = L(), c = connection(), payer = new web3.PublicKey(ACC.address);
    const { blockhash, lastValidBlockHeight } = await c.getLatestBlockhash('confirmed');
    const bytes = [];
    for (let i = 0; i < txs.length; i++) {
      const tx = txs[i];
      if (!tx.instructions.some(ix => ix.programId.equals(web3.ComputeBudgetProgram.programId))) {
        const w = []; tx.instructions.forEach(ix => ix.keys.forEach(k => k.isWritable && w.push(k.pubkey)));
        tx.instructions.unshift(await priorityIx(w), web3.ComputeBudgetProgram.setComputeUnitLimit({ units: CFG().computeUnits || 400000 }));
      }
      tx.feePayer = tx.feePayer || payer; tx.recentBlockhash = blockhash;
      const ex = (extraSigners && extraSigners[i]) || [];
      if (ex.length) tx.partialSign(...ex);
      bytes.push(tx.serialize({ requireAllSignatures: false, verifySignatures: false }));
    }
    onStep && onStep('wallet');
    let signed;
    const st = W.features['solana:signTransaction'];
    if (st) {
      const out = await st.signTransaction(...bytes.map(b => ({ transaction: b, account: ACC, chain: CHAIN() })));
      signed = out.map(o => o.signedTransaction);
    } else {
      // wallet can only sign-and-send: one at a time
      const sas = W.features['solana:signAndSendTransaction'], sigs = [];
      for (const b of bytes) { const [o] = await sas.signAndSendTransaction({ transaction: b, account: ACC, chain: CHAIN() }); sigs.push(typeof o.signature === 'string' ? o.signature : bs58(o.signature)); await confirm(sigs[sigs.length - 1], lastValidBlockHeight, onStep); }
      return sigs;
    }
    const sigs = [];
    for (const raw of signed) {
      onStep && onStep('send', sigs.length);
      const sig = await c.sendRawTransaction(raw, { skipPreflight: false, preflightCommitment: 'confirmed', maxRetries: 3 });
      sigs.push(sig);
      await confirm(sig, lastValidBlockHeight, onStep, raw);
    }
    return sigs;
  }
  // poll until confirmed (no websockets); re-broadcast every few seconds while the blockhash is still valid
  async function confirm(sig, lastValid, onStep, raw) {
    const c = connection(); const t0 = Date.now();
    for (; ;) {
      const r = await c.getSignatureStatuses([sig]); const s = r && r.value && r.value[0];
      if (s && s.err) throw new Error('The transaction failed on the blockchain: ' + JSON.stringify(s.err));
      if (s && (s.confirmationStatus === 'confirmed' || s.confirmationStatus === 'finalized')) return sig;
      const h = await c.getBlockHeight('confirmed').catch(() => 0);
      if (h && lastValid && h > lastValid) throw new Error('The network was too busy and the transaction expired. Nothing was charged. Try again.');
      if (raw && Date.now() - t0 > 4000) c.sendRawTransaction(raw, { skipPreflight: true, maxRetries: 0 }).catch(() => { });
      onStep && onStep('confirm', Math.round((Date.now() - t0) / 1000));
      await sleep(1500);
    }
  }
  function bs58(u8) { const A = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'; let x = 0n; for (const b of u8) x = x * 256n + BigInt(b); let s = ''; while (x > 0n) { s = A[Number(x % 58n)] + s; x /= 58n; } for (const b of u8) { if (b) break; s = '1' + s; } return s; }

  async function solBalance(addr) { return (await connection().getBalance(new (L().web3.PublicKey)(addr))) / 1e9; }
  function explorer(kind, id) { const q = NET() === 'devnet' ? '?cluster=devnet' : ''; return 'https://solscan.io/' + (kind === 'tx' ? 'tx/' : kind === 'token' ? 'token/' : 'account/') + id + q; }

  return { NET, RPC_URL, connection, dbc, wallets: () => wallets.slice(), onWallets: f => listeners.add(f), connect, disconnect, autoConnect, me, onChange: f => onChange.add(f), sendAll, confirm, solBalance, explorer, sleep };
})();
