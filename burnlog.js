/* The public burn log on the $CAPES page (#burnlog). It shows what the game server reads from Solana (server/burns.js):
   the total burned (starting supply minus the supply now, so it counts every burn by anyone) and each burn signed by an
   official wallet, with its transaction on Solscan. Nothing here is typed in by hand. */
(function () {
  var box = document.getElementById('burnlog'); if (!box) return;
  var C = window.MC_CONFIG || {};
  var API = (C.server || '').replace(/^ws/, 'http').replace(/\/ws\/?$/, '');
  var T = '$' + (C.ticker || 'CAPES');
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var okAddr = function (s) { return /^[1-9A-HJ-NP-Za-km-z]{32,88}$/.test(s || ''); };
  // raw amount (string) -> whole tokens with commas
  function tok(raw, dec) {
    try { var n = BigInt(raw || '0'), d = BigInt(10) ** BigInt(dec || 0), w = n / d, f = Number((n % d) * 100n / d);
      var s = w.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','); return w < 1000n && f ? s + '.' + String(f).padStart(2, '0') : s; } catch (e) { return '0'; }
  }
  function pct(raw, base) { try { var b = BigInt(base || '0'); if (!b) return ''; return (Number(BigInt(raw || '0') * 100000n / b) / 1000).toFixed(2).replace(/\.?0+$/, '') + '%'; } catch (e) { return ''; } }
  var KIND = { launch: 'Snake Bite (launch)', acid: 'Acid Pit', burn: 'Buy-and-burn' };
  function day(ts) { try { return new Date(ts * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); } catch (e) { return ''; } }

  function empty(msg) {
    box.innerHTML = '<div class="bl-top"><div class="bl-big">0</div><div class="bl-sub">' + esc(T) + ' burned so far</div></div><p class="mute bl-note">' + msg + '</p>';
  }
  function draw(v) {
    if (!v || !v.on) return empty('The coin isn\'t live yet, so nothing has been burned. The moment it is, every burn shows up here with its transaction, read straight from Solana.');
    var dec = v.decimals, base = v.supply0;
    var h = '<div class="bl-top"><div class="bl-big">' + (v.burned == null ? '…' : tok(v.burned, dec)) + '</div><div class="bl-sub">' + esc(T) + ' burned' +
      (v.burned != null && base ? ' · ' + pct(v.burned, base) + ' of the starting supply' : '') + '</div></div>';
    h += '<div class="bl-split"><div><b>' + tok(v.launch, dec) + '</b><span>Snake Bite, burned in the launch transaction</span></div>' +
      '<div><b>' + tok(String(BigInt(v.official || '0') - BigInt(v.launch || '0')), dec) + '</b><span>Buy-and-burns by the fee wallet</span></div>' +
      '<div><b>' + (v.others == null ? '…' : tok(v.others, dec)) + '</b><span>Burned by anyone else (Acid Pit, ad burns, holders)</span></div></div>';
    var L = (v.list || []).filter(function (b) { return okAddr(b.sig); });
    if (L.length) {
      h += '<div class="bl-rows">' + L.slice(0, 25).map(function (b) {
        return '<a class="bl-row" href="https://solscan.io/tx/' + esc(b.sig) + '" target="_blank" rel="noopener"><span class="bl-d">' + esc(day(b.ts)) + '</span><span class="bl-k">' + esc(KIND[b.kind] || 'Burn') +
          '<small>' + esc(b.label || '') + '</small></span><span class="bl-a">' + tok(b.amount, dec) + '</span><span class="bl-x">Solscan ↗</span></a>';
      }).join('') + '</div>';
    } else h += '<p class="mute bl-note">No burns from the official wallets yet. Each one appears here with its transaction as soon as it is on-chain.</p>';
    var supplyNow = v.supply != null ? tok(v.supply, dec) : '…';
    h += '<p class="mute bl-note">Supply now: ' + supplyNow + ' ' + esc(T) + '. Check it yourself: <a href="https://solscan.io/token/' + esc(v.mint) + '" target="_blank" rel="noopener">the token on Solscan</a>' +
      (v.updated ? ' · read from Solana ' + Math.max(1, Math.round((Date.now() - v.updated) / 60000)) + ' min ago' : '') + '.</p>';
    box.innerHTML = h;
  }
  if (!API) return empty('The burn log is offline right now.');
  fetch(API + '/burns').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(draw).catch(function () {
    empty('Couldn\'t reach the burn log right now. Every burn is still public on Solana' + (okAddr(C.capesMint) ? ': <a href="https://solscan.io/token/' + esc(C.capesMint) + '" target="_blank" rel="noopener">the token on Solscan</a>' : '') + '.');
  });
})();
