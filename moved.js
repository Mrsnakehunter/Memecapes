/* The day MemeCapes goes on under a new name: one screen at the front of the site that says where it went.
   Off until config.js `moved.url` is set (an https address). Nothing is taken down: the coin's page, the burn log,
   the lock and the official wallets stay at their addresses, and this screen links to them. The rest of the home
   page, and the game, are still there below it. */
(function () {
  var C = window.MC_CONFIG || {}, m = C.moved || {};
  if (!m.url || !/^https:\/\//.test(m.url)) return;
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var link = function (u) { return /^https:\/\//.test(u || "") ? esc(u) : ""; };
  var name = esc(m.name || "our new home"), tick = esc(C.ticker || "CAPES"), x = link(m.x), tg = link(m.telegram);

  var css = document.createElement("style");
  css.textContent =
    ".mv{min-height:100vh;min-height:100svh;display:flex;align-items:center;justify-content:center;padding:96px 20px 120px}" +
    ".mv-in{max-width:680px;text-align:center}" +
    ".mv-k{margin:0 0 14px;color:var(--mute);font-size:15px}" +
    ".mv-h{margin:0;font-family:Cinzel,Georgia,serif;font-size:clamp(34px,7vw,64px);line-height:1.08;color:var(--txt);text-wrap:balance}" +
    ".mv-h b{color:var(--gold);font-weight:inherit}" +
    ".mv-p{margin:18px auto 28px;max-width:520px;color:var(--parch2);font-size:18px;line-height:1.5}" +
    ".mv-go{display:inline-block;font-size:19px;padding:15px 30px}" +
    ".mv-l{margin:34px auto 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:10px;max-width:520px}" +
    ".mv-l a{display:block;padding:13px 16px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--txt);text-decoration:none;font-size:16px}" +
    ".mv-l a:hover,.mv-l a:focus-visible{border-color:var(--gold2)}" +
    ".mv-s{margin:26px auto 0;max-width:520px;color:var(--mute);font-size:14px;line-height:1.5}";
  document.head.appendChild(css);

  function build() {
    var home = document.getElementById("pg-home");
    if (!home || document.getElementById("mv")) return;
    var s = document.createElement("section");
    s.className = "mv";
    s.id = "mv";
    s.innerHTML =
      '<div class="mv-in">' +
      '<p class="mv-k">MemeCapes has moved</p>' +
      '<h1 class="mv-h">MemeCapes is now <b>' + name + "</b></h1>" +
      '<p class="mv-p">Same team, new name. The trading app that started here has its own home now.</p>' +
      '<a class="btn gold glow mv-go" href="' + esc(m.url) + '" rel="noopener">Go to ' + name + "</a>" +
      '<ul class="mv-l">' +
      '<li><a href="#token">The $' + tick + " record: its page, the burn log, the lock and the official wallets</a></li>" +
      '<li><a href="play.html">Keep playing the game, free in your browser</a></li>' +
      (x ? '<li><a href="' + x + '" rel="noopener">' + name + " on X</a></li>" : "") +
      (tg ? '<li><a href="' + tg + '" rel="noopener">' + name + " on Telegram</a></li>" : "") +
      "</ul>" +
      '<p class="mv-s">Nothing from before was taken down. Every post and every on-chain record is where it was.</p>' +
      "</div>";
    home.insertBefore(s, home.firstChild);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
