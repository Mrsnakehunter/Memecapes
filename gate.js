/* The front door: 18+ and agreement to the Terms and Privacy Policy, before the website or the game opens.
   Remembered per browser; asked again whenever MC_CONFIG.termsVersion changes. */
(function () {
  var C = window.MC_CONFIG || {}, V = 'mc_gate_' + (C.termsVersion || '1');
  var page = (location.hash || '').slice(1);
  if (page === 'terms' || page === 'privacy') return;           // the policies themselves are always readable
  try { if (localStorage.getItem(V) === 'yes') return; } catch (e) {}
  var css = '#mcgate{position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px;background:radial-gradient(120% 90% at 50% 0%,#3b0b14ee,#0d0407f7);font:15px/1.5 Alegreya,Georgia,serif;color:#f6eedc}'
    + '#mcgate .bx{max-width:440px;width:100%;background:radial-gradient(120% 70% at 50% 0%,#5a1220,#3b0b14 48%,#24060c);border:3px solid #15030a;outline:2px solid #d9a520;box-shadow:0 0 0 5px #24060c,0 0 0 6px #6b4a06,0 24px 60px #000d;border-radius:3px;padding:22px}'
    + '#mcgate h2{margin:0 0 4px;font:900 24px Cinzel,Georgia,serif;background:linear-gradient(#fff2a8,#f2b400 55%,#c98a10);-webkit-background-clip:text;background-clip:text;color:transparent}'
    + '#mcgate p{margin:6px 0 14px;color:#d9b98a;font-size:14px}#mcgate label{display:flex;gap:10px;align-items:flex-start;margin:10px 0;cursor:pointer}'
    + '#mcgate input{width:20px;height:20px;accent-color:#f2b400;flex:none;margin-top:2px}#mcgate a{color:#ffd23f}'
    + '#mcgate .row{display:flex;gap:8px;margin-top:16px}#mcgate button{flex:1;font:700 14px Cinzel,Georgia,serif;padding:11px;border-radius:3px;cursor:pointer;border:1px solid #d9a520}'
    + '#mcgate .go{color:#2a1400;background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);border-color:#6b4a06}#mcgate .go:disabled{opacity:.4;cursor:default}'
    + '#mcgate .no{color:#ffe9b0;background:linear-gradient(#7a1420,#4a0a12)}#mcgate small{display:block;margin-top:12px;color:#b89a6a;font-size:12px}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  var d = document.createElement('div'); d.id = 'mcgate'; d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true');
  d.innerHTML = '<div class="bx"><h2>Before you enter</h2><p>MemeCapes is for adults. It talks about crypto, and the shop takes real crypto payments.</p>'
    + '<label><input type="checkbox" id="mcg18"> <span>I am 18 years old or older.</span></label>'
    + '<label><input type="checkbox" id="mcgtos"> <span>I have read and agree to the <a href="index.html#terms" target="_blank" rel="noopener">Terms of Service</a> and the <a href="index.html#privacy" target="_blank" rel="noopener">Privacy Policy</a>.</span></label>'
    + '<div class="row"><button class="no" id="mcgno">Leave</button><button class="go" id="mcggo" disabled>Enter MemeCapes</button></div>'
    + '<small>MemeCapes is a parody game. Nothing here is financial advice. Meme Coins are play money.</small></div>';
  function mount() {
    document.body.appendChild(d);
    var a = document.getElementById('mcg18'), b = document.getElementById('mcgtos'), go = document.getElementById('mcggo');
    var upd = function () { go.disabled = !(a.checked && b.checked); };
    a.onchange = upd; b.onchange = upd;
    go.onclick = function () { try { localStorage.setItem(V, 'yes'); } catch (e) {} d.remove(); };
    document.getElementById('mcgno').onclick = function () { location.href = 'https://www.google.com'; };
    a.focus();
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
