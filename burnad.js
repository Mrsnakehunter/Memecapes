/* Website ads for burning $CAPEZ (the rules live on the game server, server/server.js "burn ads").
   Home page: one ad card in the page flow, styled like the site's own cards. Not sticky, no pop-up, no motion.
   Each visit shows one live ad, picked with odds = how much that project burned (1% = 1 share), so the spot
   is split between everyone who burned. The card is not shown at all when there are no ads.
   Shop page: send an ad (wallet signature, no transaction), wait for approval, then burn and paste the transaction. */
(function () {
  var C = window.MC_CONFIG || {};
  var API = (C.server || '').replace(/^ws/, 'http').replace(/\/ws\/?$/, '');
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var host = function (u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return ''; } };

  // ---- the ad spot on the home page
  var slot = document.getElementById('burnslot');
  if (slot && API) {
    fetch(API + '/burnads').then(function (r) { return r.ok ? r.json() : []; }).then(function (L) {
      if (!L || !L.length) return;
      var tot = L.reduce(function (a, x) { return a + (x.w || 1); }, 0), pick = Math.random() * tot, ad = L[0];
      for (var i = 0; i < L.length; i++) { pick -= (L[i].w || 1); if (pick < 0) { ad = L[i]; break; } }
      var h = host(ad.link);
      slot.innerHTML = '<div class="card adcard"><a class="adimg"' + (ad.link ? ' href="' + esc(ad.link) + '" target="_blank" rel="sponsored noopener noreferrer nofollow"' : '') + '><img alt="' + esc(ad.brand) + '" loading="lazy" src="' + esc(API + '/burnads/' + ad.id + '.jpg?v=' + ad.v) + '"></a>'
        + '<div class="adtxt"><span class="adlab">Sponsored · burned ' + esc(C.burnPct || 1) + '% of $CAPEZ</span><h3>' + esc(ad.brand) + '</h3>' + (ad.line ? '<p class="mute">' + esc(ad.line) + '</p>' : '')
        + (ad.link ? '<a class="btn ghost" href="' + esc(ad.link) + '" target="_blank" rel="sponsored noopener noreferrer nofollow">Visit ' + esc(h) + ' ↗</a><span class="adnote">Their site, not ours. Never enter your seed phrase anywhere.</span>' : '')
        + '<a class="adwhy" href="#shop">Your project here? Burn ' + esc(C.burnPct || 1) + '% of $CAPEZ</a></div></div>';
      slot.hidden = false;
    }).catch(function () { });
  }

  // ---- the shop: send an ad, then burn
  var root = document.getElementById('burnapp');
  if (!root) return;
  var head = '<h2 style="margin-top:34px">Burn ' + esc(C.burnPct || 1) + '% for a website ad</h2>'
    + '<p class="mute">Burn ' + esc(C.burnPct || 1) + '% of all $CAPEZ and your project gets the ad spot on the memecapes.com home page, for good. The spot is shared: each visit shows one ad, and your odds follow how much you burned (1% = 1 share, 2% = 2 shares). Burned tokens are destroyed, not sent to us.</p>'
    + '<ol class="mute burnsteps"><li>Connect your wallet and send your ad. Signing is free: it is not a transaction.</li><li>We check the ad by hand. <b>Do not burn anything yet.</b></li><li>When it says Approved, burn the amount shown with your wallet app\'s Burn option, from the same wallet.</li><li>Paste the burn\'s transaction signature here. The blockchain is checked and your ad goes up.</li></ol>';
  if (!API || !C.capesMint) { root.innerHTML = head + '<div class="warn">Opens when $CAPEZ launches. Never burn or send tokens for an ad anywhere else.</div>'; return; }
  var W = null, img = '';
  var app = function () { var w = window; return (w.phantom && w.phantom.solana) || (w.solana && w.solana.isPhantom && w.solana) || w.solflare || w.solana || null; };
  var post = function (p, b) { return fetch(API + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }).then(function (r) { return r.json(); }); };
  var out = function (t, bad) { var e = document.getElementById('bres'); if (e) e.innerHTML = '<div class="' + (bad ? 'warn' : 'ok') + '">' + t + '</div>'; };
  function draw() {
    if (!W) { root.innerHTML = head + '<button class="btn gold" id="bconn">Connect my wallet</button><div id="bres"></div>'; document.getElementById('bconn').onclick = connect; return; }
    post('/burnad/status', { wallet: W }).then(function (S) {
      var h = head + '<p class="mute">Wallet <b>' + esc(W.slice(0, 4) + '...' + W.slice(-4)) + '</b>. Right now ' + (S.live ? S.live + ' ad' + (S.live > 1 ? 's share' : ' has') + ' the spot (' + S.shares + ' share' + (S.shares > 1 ? 's' : '') + ')' : 'the spot is free') + '. ' + (S.need ? esc(C.burnPct || 1) + '% of all $CAPEZ is <b>' + esc(S.need) + ' $CAPEZ</b>.' : '') + '</p>';
      (S.ads || []).forEach(function (a) {
        h += '<div class="card" style="margin:10px 0"><b>#' + a.id + ' ' + esc(a.brand) + '</b> <span class="pill">' + esc(a.status) + '</span><br>';
        if (a.status === 'pending') h += '<span class="mute">Waiting for us to check it. Do not burn anything yet.</span>';
        else if (a.status === 'rejected') h += '<span class="mute">Not approved: ' + esc(a.note) + ' Nothing was burned.</span>';
        else if (a.status === 'live') h += '<span class="mute">Live on the home page with ' + a.shares + ' share' + (a.shares > 1 ? 's' : '') + ' of the spot.</span>';
        else if (a.status === 'approved') h += '<span>Approved. Now burn at least <b>' + esc(S.need) + ' $CAPEZ</b> from this wallet with your wallet app\'s <b>Burn</b> option (not Send). Burning is permanent and can\'t be undone or refunded.</span><label class="fld" style="margin-top:8px">Burn transaction signature<input id="bsig' + a.id + '" placeholder="e.g. 5h3k...9Qz"></label><button class="btn gold" data-burn="' + a.id + '">Check my burn</button>';
        h += '</div>';
      });
      if (!(S.ads || []).some(function (a) { return a.status === 'pending' || a.status === 'approved'; }))
        h += '<h3>New ad</h3><label class="fld">Project name<input id="bbr" maxlength="24"></label><label class="fld">One line about it<input id="bln" maxlength="90"></label><label class="fld">Link (https://...)<input id="blk" maxlength="100" placeholder="https://"></label>'
          + '<label class="fld">Picture (shown wide, 2 by 1)<input id="bim" type="file" accept="image/png,image/jpeg,image/webp"></label><canvas id="bpv" width="800" height="400" style="width:100%;max-width:420px;border-radius:12px;display:none"></canvas>'
          + '<p class="mute" style="font-size:13px">Only your own project and art. No scams, adult content, other people\'s brands or promises of profit. See the <a href="#terms">Terms</a>.</p><button class="btn gold" id="bsend">Sign and send my ad</button>';
      root.innerHTML = h + '<div id="bres"></div>';
      var f = document.getElementById('bim');
      if (f) f.onchange = function () {
        var fl = f.files[0]; if (!fl) return; var u = URL.createObjectURL(fl), im = new Image();
        im.onload = function () { var c = document.getElementById('bpv'), x = c.getContext('2d'), r = Math.max(800 / im.width, 400 / im.height), w = im.width * r, hh = im.height * r; x.fillStyle = '#1d150c'; x.fillRect(0, 0, 800, 400); x.drawImage(im, (800 - w) / 2, (400 - hh) / 2, w, hh); img = c.toDataURL('image/jpeg', .85); c.style.display = 'block'; URL.revokeObjectURL(u); };
        im.src = u;
      };
      var sb = document.getElementById('bsend'); if (sb) sb.onclick = send;
      root.querySelectorAll('[data-burn]').forEach(function (b) { b.onclick = function () { burn(+b.dataset.burn); }; });
    }).catch(function () { root.innerHTML = head + '<div class="warn">The game server is not answering. Try again in a minute.</div>'; });
  }
  function connect() {
    var p = app(); if (!p) return out('No wallet app found. Open this page inside Phantom or Solflare, or on a computer with the wallet extension.', 1);
    p.connect().then(function (c) { var pk = (c && c.publicKey) || p.publicKey; W = pk && pk.toString(); draw(); }).catch(function () { out('Your wallet did not connect.', 1); });
  }
  function send() {
    var brand = document.getElementById('bbr').value.trim(), line = document.getElementById('bln').value.trim(), link = document.getElementById('blk').value.trim();
    if (!img) return out('Add a picture.', 1);
    var p = app();
    post('/burnad/nonce', { wallet: W }).then(function (n) {
      if (!n.msg) throw new Error(n.error || 'no message');
      return p.signMessage(new TextEncoder().encode(n.msg), 'utf8');
    }).then(function (s) {
      var sig = (s && s.signature) || s, b = ''; new Uint8Array(sig).forEach(function (x) { b += String.fromCharCode(x); });
      return post('/burnad/submit', { wallet: W, sig: btoa(b), brand: brand, line: line, link: link === 'https://' ? '' : link, img: img });
    }).then(function (r) { if (r.error) return out(esc(r.error), 1); img = ''; draw(); }).catch(function (e) { out('Nothing was sent: ' + esc(e.message || 'you did not sign.'), 1); });
  }
  function burn(id) {
    var sig = (document.getElementById('bsig' + id).value || '').trim(); out('Checking the blockchain...');
    post('/burnad/burn', { wallet: W, id: id, burnSig: sig }).then(function (r) { if (r.error) return out(esc(r.error), 1); draw(); }).catch(function () { out('Could not check it. Try again in a minute.', 1); });
  }
  draw();
})();
