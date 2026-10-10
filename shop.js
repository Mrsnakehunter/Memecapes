/* The MemeCapes shop: ads, sponsored monsters, custom capes and items, paid in SOL, USDC or $CAPES.
   The buyer pays from their own wallet; this page only checks the payment on the blockchain (read-only)
   and builds the order message to send to MemeCapes. */
(function () {
  var C = window.MC_CONFIG || {}, P = window.MCPAY, root = document.getElementById('shopapp');
  if (!root || !P) return;
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var open = P.isAddr(C.shopWallet), sol = 0, cur = null;
  var coins = function () {
    var c = [['SOL', null], ['USDC', C.usdcMint]];
    if (P.isAddr(C.capesMint) && C.capesUsd > 0) c.push(['$CAPES', C.capesMint]);
    return c;
  };
  var amountFor = function (it, ccy) {
    if (ccy === 'USDC') return +it.usd.toFixed(2);
    if (ccy === '$CAPES') return Math.ceil(it.usd / C.capesUsd);
    return +(it.usd / (sol || C.solUsdFallback || 150)).toFixed(4);
  };
  var contact = function () {
    return C.contactEmail ? '<a href="mailto:' + esc(C.contactEmail) + '">' + esc(C.contactEmail) + '</a>' : '<a href="https://x.com/' + esc(C.xHandle || 'Mrsnakebaby') + '" target="_blank" rel="noopener">@' + esc(C.xHandle || 'Mrsnakebaby') + ' on X</a>';
  };
  function list() {
    root.innerHTML = (open ? '' : '<div class="warn"><b>The shop opens soon.</b> Payments are switched off until the official MemeCapes wallet address is posted here. Never pay an address you got anywhere else.</div>')
      + '<div class="grid g2">' + (C.shop || []).map(function (it) {
        return '<div class="card shopc"><h3>' + esc(it.name) + '</h3><p class="mute">' + esc(it.text) + '</p><div class="price"><b>$' + it.usd + '</b>' + (it.days ? ' <span class="mute">for ' + it.days + ' days</span>' : '') + '</div>'
          + '<button class="btn gold" data-buy="' + esc(it.id) + '"' + (open ? '' : ' disabled') + '>' + (open ? 'Buy' : 'Coming soon') + '</button></div>';
      }).join('') + '</div><p class="mute" style="margin-top:14px">Questions before you buy? ' + contact() + '. By buying you agree to the <a href="#terms">Terms</a>, including the shop section.</p>';
    root.querySelectorAll('[data-buy]').forEach(function (b) { b.onclick = function () { buy(b.dataset.buy); }; });
  }
  function buy(id) {
    var it = (C.shop || []).find(function (x) { return x.id === id; }); if (!it) return;
    cur = { it: it, ccy: 'USDC', code: 'MC-' + Math.random().toString(36).slice(2, 7).toUpperCase() };
    draw();
  }
  function draw() {
    var it = cur.it, mint = coins().find(function (c) { return c[0] === cur.ccy; })[1], amt = amountFor(it, cur.ccy);
    cur.amt = amt; cur.mint = mint;
    root.innerHTML = '<div class="card shopbuy"><button class="btn ghost" id="sback">Back to the shop</button><h2>' + esc(it.name) + '</h2><p class="mute">' + esc(it.text) + '</p>'
      + '<h3>1. Pick how you pay</h3><div class="ccy">' + coins().map(function (c) { return '<button class="btn ' + (c[0] === cur.ccy ? 'gold' : 'ghost') + '" data-ccy="' + c[0] + '">' + c[0] + '</button>'; }).join('') + '</div>'
      + '<h3>2. Send exactly this from your own wallet</h3><div class="payto"><div class="amt">' + amt + ' ' + esc(cur.ccy) + '</div>' + (cur.ccy === 'SOL' ? '<div class="mute">$' + it.usd + ' at about $' + Math.round(sol || C.solUsdFallback) + ' per SOL</div>' : '')
      + '<div class="addr"><code id="saddr">' + esc(C.shopWallet) + '</code><button class="btn ghost" id="scopy">Copy address</button></div>'
      + '<a class="btn gold" href="' + esc(P.payLink(C.shopWallet, amt, mint, 'MemeCapes', cur.code)) + '">Open in my wallet</a>'
      + '<p class="mute">Check the address in your wallet matches <b>' + esc(C.shopWallet.slice(0, 4) + '...' + C.shopWallet.slice(-4)) + '</b> before you approve. Payments can\'t be reversed. We will never ask for your seed phrase.</p></div>'
      + '<h3>3. Tell us what you want</h3><label class="fld">Your X handle or email<input id="swho" placeholder="@yourname"></label><label class="fld">Design notes (colours, name, link to your art)<textarea id="snote" rows="3"></textarea></label>'
      + '<h3>4. Paste your transaction signature</h3><p class="mute">After paying, copy the transaction ID (signature) from your wallet\'s activity and paste it here.</p>'
      + '<label class="fld"><input id="ssig" placeholder="e.g. 5h3k...9Qz"></label><button class="btn gold" id="scheck">Check my payment</button><div id="sres"></div></div>';
    document.getElementById('sback').onclick = list;
    root.querySelectorAll('[data-ccy]').forEach(function (b) { b.onclick = function () { cur.ccy = b.dataset.ccy; draw(); }; });
    document.getElementById('scopy').onclick = function () { try { navigator.clipboard.writeText(C.shopWallet); this.textContent = 'Copied'; } catch (e) {} };
    document.getElementById('scheck').onclick = check;
  }
  function check() {
    var out = document.getElementById('sres'), sig = document.getElementById('ssig').value.trim();
    out.innerHTML = '<p class="mute">Checking the blockchain...</p>';
    P.verify({ sig: sig, to: C.shopWallet, mint: cur.mint, min: cur.amt * (cur.ccy === 'SOL' ? 0.97 : 1), maxAgeDays: 7, label: cur.ccy }).then(function (r) {
      if (!r.ok) { out.innerHTML = '<div class="warn">' + esc(r.err) + '</div>'; return; }
      var who = document.getElementById('swho').value.trim(), note = document.getElementById('snote').value.trim();
      var msg = 'MemeCapes order ' + cur.code + '\nItem: ' + cur.it.name + '\nPaid: ' + r.amount + ' ' + cur.ccy + '\nFrom wallet: ' + r.from + '\nTransaction: ' + sig + '\nContact: ' + who + '\nNotes: ' + note;
      out.innerHTML = '<div class="ok"><b>Payment found: ' + r.amount + ' ' + esc(cur.ccy) + '.</b> Last step: send us this order so we can make your ' + esc(cur.it.name.toLowerCase()) + '.</div><pre class="order">' + esc(msg) + '</pre>'
        + '<div class="ccy">' + (C.contactEmail ? '<a class="btn gold" href="mailto:' + esc(C.contactEmail) + '?subject=' + encodeURIComponent('MemeCapes order ' + cur.code) + '&body=' + encodeURIComponent(msg) + '">Email the order</a>' : '')
        + '<a class="btn ' + (C.contactEmail ? 'ghost' : 'gold') + '" href="https://x.com/' + esc(C.xHandle || 'Mrsnakebaby') + '" target="_blank" rel="noopener">Send it on X</a><button class="btn ghost" id="scopyo">Copy the order</button></div>';
      document.getElementById('scopyo').onclick = function () { try { navigator.clipboard.writeText(msg); this.textContent = 'Copied'; } catch (e) {} };
    });
  }
  P.solUsd().then(function (v) { sol = v; if (cur) draw(); });
  list();
})();
