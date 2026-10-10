/* Read-only Solana helpers for the shop and the $CAPES deposit.
   This file never creates, signs or sends a transaction and never touches a wallet.
   It only asks a public Solana node "did this transaction happen, and what did it move?" */
window.MCPAY = (function () {
  var C = function () { return window.MC_CONFIG || {}; };
  function rpc(method, params) {
    return fetch(C().rpc || 'https://api.mainnet-beta.solana.com', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: method, params: params })
    }).then(function (r) { return r.json(); }).then(function (j) { if (j.error) throw new Error(j.error.message || 'RPC error'); return j.result; });
  }
  var B58 = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/, SIG = /^[1-9A-HJ-NP-Za-km-z]{60,100}$/;
  function solUsd() {
    return fetch('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd')
      .then(function (r) { return r.json(); }).then(function (j) { return (j.solana && j.solana.usd) || C().solUsdFallback || 150; })
      .catch(function () { return C().solUsdFallback || 150; });
  }
  /* Did transaction `sig` pay at least `min` to `to`?  mint = null for SOL, or a token mint (USDC, $CAPES).
     Resolves {ok, amount, from, when, err}. */
  function verify(o) {
    var sig = String(o.sig || '').trim();
    if (!SIG.test(sig)) return Promise.resolve({ ok: false, err: 'That does not look like a transaction signature. Copy it from your wallet\'s activity.' });
    if (!B58.test(o.to || '')) return Promise.resolve({ ok: false, err: 'The receiving address is not set yet.' });
    return rpc('getTransaction', [sig, { encoding: 'jsonParsed', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]).then(function (tx) {
      if (!tx) return { ok: false, err: 'Not found yet. Wait a few seconds after paying and try again.' };
      if (tx.meta && tx.meta.err) return { ok: false, err: 'That transaction failed on the blockchain, so nothing was paid.' };
      var keys = tx.transaction.message.accountKeys.map(function (k) { return k.pubkey || k; }), from = keys[0], amt = 0;
      if (!o.mint) {
        var i = keys.indexOf(o.to);
        if (i >= 0) amt = (tx.meta.postBalances[i] - tx.meta.preBalances[i]) / 1e9;
      } else {
        var bal = function (list) { var s = 0; (list || []).forEach(function (b) { if (b.owner === o.to && b.mint === o.mint) s += +(b.uiTokenAmount.uiAmountString || b.uiTokenAmount.uiAmount || 0); }); return s; };
        amt = bal(tx.meta.postTokenBalances) - bal(tx.meta.preTokenBalances);
      }
      var when = (tx.blockTime || 0) * 1000;
      if (amt <= 0) return { ok: false, err: 'That transaction did not send ' + (o.label || 'the payment') + ' to the MemeCapes address.', from: from };
      if (o.maxAgeDays && when && Date.now() - when > o.maxAgeDays * 864e5) return { ok: false, err: 'That payment is older than ' + o.maxAgeDays + ' days.', amount: amt, from: from };
      if (o.from && from !== o.from) return { ok: false, err: 'That payment came from a different wallet than the one on your account.', amount: amt, from: from };
      if (amt + 1e-9 < (o.min || 0)) return { ok: false, err: 'Only ' + amt + ' arrived; the price is ' + o.min + '.', amount: amt, from: from };
      return { ok: true, amount: amt, from: from, when: when };
    }).catch(function (e) { return { ok: false, err: 'Could not reach the Solana network (' + e.message + '). Try again in a minute.' }; });
  }
  /* A Solana Pay link: wallets like Phantom open it with the address and amount filled in. The buyer still approves it in their own wallet. */
  function payLink(to, amount, mint, label, memo) {
    var u = 'solana:' + to + '?amount=' + encodeURIComponent(amount);
    if (mint) u += '&spl-token=' + mint;
    if (label) u += '&label=' + encodeURIComponent(label);
    if (memo) u += '&memo=' + encodeURIComponent(memo);
    return u;
  }
  return { rpc: rpc, verify: verify, solUsd: solUsd, payLink: payLink, isAddr: function (a) { return B58.test(a || ''); } };
})();
