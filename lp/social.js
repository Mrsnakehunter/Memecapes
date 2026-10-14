/* MemeCapes Watch and Stream (launch.html): the live tape, the feed of what's happening, posts signed by wallet,
   channels, going live from the browser (WHIP) or OBS, chat, tips and subscriptions paid wallet to wallet.
   Sign-in is a signed message, never a transaction. Video runs through Cloudflare Stream when the server has it on. */
(function () {
  'use strict';
  const A = window.LPAPP, { $, $$, esc, short, api, toast, usd, sol, pct, ago, stamp, coinFace, sparkline, needWallet, friendly, app, onLeave } = A;
  const L = window.LPCORE;
  const MC = window.MC_CONFIG || {}, C = MC.launchpad || {};

  // ---------- who's who: names and pictures people set on their profile, remembered as we see them
  const names = new Map();
  const learn = (p) => { if (p && p.wallet) names.set(p.wallet, p); };
  const nameOf = (w) => { const p = names.get(w); return p && p.name ? p.name : ''; };
  // every wallet gets its own cape: two colours and a pattern from the address itself, the same everywhere
  function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function avatar(w, cls) {
    const p = names.get(w); if (p && p.avatar) return `<img class="av ${cls || ''}" src="${esc(p.avatar)}" alt="" referrerpolicy="no-referrer">`;
    const h = hash(w || ''), h1 = h % 360, h2 = (h1 + 40 + (h >> 8) % 140) % 360, pat = (h >> 16) % 4, lt = 30 + (h >> 20) % 25;
    const c1 = `hsl(${h1} 70% ${lt}%)`, c2 = `hsl(${h2} 80% ${lt + 20}%)`;
    const pats = ['', `<path d="M20 20 L44 60 M32 18 L50 48" stroke="${c2}" stroke-width="5" opacity=".8"/>`, `<circle cx="32" cy="42" r="7" fill="${c2}"/><circle cx="22" cy="58" r="4" fill="${c2}"/><circle cx="43" cy="58" r="4" fill="${c2}"/>`, `<path d="M14 50 Q32 40 50 50 Q32 60 14 50Z" fill="${c2}"/>`];
    return `<svg class="av ${cls || ''}" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="32" fill="#1b130b"/><path d="M18 22 Q32 10 46 22 L54 60 L10 60 Z" fill="${c1}"/><path d="M24 22 Q32 16 40 22 L46 60 L18 60 Z" fill="${c2}" opacity="${pat === 0 ? .9 : .35}"/>${pats[pat]}<circle cx="32" cy="22" r="4" fill="#ffd23f"/><circle cx="32" cy="14" r="7" fill="#e8c39e"/></svg>`;
  }
  const who = (w) => `<a class="addr" href="#/u/${esc(w)}">${esc(nameOf(w) || short(w))}</a>`;

  // ---------- sign in: the wallet signs a short text; the server hands back a session for posting, chat and channels
  let tok = '', tokW = ''; try { tok = localStorage.getItem('lp_tok') || ''; tokW = localStorage.getItem('lp_tokw') || ''; } catch (e) { }
  const signed = () => { const m = LPC.me(); return !!(tok && m && m.address === tokW); };
  async function signIn() {
    const m = await needWallet(); if (tok && tokW === m.address) return m;
    const { msg } = await api('/so/nonce', { wallet: m.address });
    const sig = await LPC.signMessage(msg);
    const r = await api('/so/login', { wallet: m.address, sig });
    tok = r.token; tokW = m.address; try { localStorage.setItem('lp_tok', tok); localStorage.setItem('lp_tokw', tokW); } catch (e) { }
    learn(r); if (r.channel) myCh = r.channel; return m;
  }
  async function apiA(path, body) {
    const r = await fetch(A.SRV + path + (body ? '' : (path.includes('?') ? '&' : '?') + 'net=' + A.NET), { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json', ...(tok ? { Authorization: 'Bearer ' + tok } : {}) }, body: body ? JSON.stringify({ ...body, net: A.NET }) : undefined });
    const j = await r.json().catch(() => ({}));
    if (r.status === 401) { tok = ''; try { localStorage.removeItem('lp_tok'); } catch (e) { } }
    if (!r.ok || j.error) throw new Error(j.error || 'The server did not answer.'); return j;
  }
  async function needSign() { if (!signed()) await signIn(); }
  let myCh = null;

  // ---------- the tape: live trades running across the top of every page
  let tapeT = 0, tapeLast = '';
  async function tape() {
    clearTimeout(tapeT);
    try {
      const r = await api('/lp/trades?limit=30'); r.trades.forEach(t => t.who && learn(t.who));
      const items = r.trades.map(t => `<a class="ti" href="#/coin/${esc(t.mint)}">${coinFace(t)}<span>$${esc(t.symbol)}</span><span class="${t.buy ? 'up' : 'dn'}">${t.buy ? '+' : '−'}${t.sol.toFixed(2)} SOL</span><span class="mute">${esc(nameOf(t.trader) || short(t.trader))}</span></a>`).join('');
      const key = r.trades.map(t => t.sig).join(',');
      if (key !== tapeLast) { tapeLast = key; $('#tape .track').innerHTML = items ? items + items : '<span class="ti empty">No trades yet. The first coin launched here starts the tape.</span>'; }
    } catch (e) { $('#tape .track').innerHTML = '<span class="ti empty">The launchpad server is not reachable right now.</span>'; }
    if (tapeN++ % 3 === 0) { try { const r = await api('/st/live'); const n = r.channels.length; $$('.lvn').forEach(e => { e.textContent = n || ''; e.hidden = !n; }); } catch (e) { } }
    tapeT = setTimeout(tape, 10000);
  }
  let tapeN = 0;

  // ---------- feed cards: posts and what happened on the launchpad
  const cchip = (c) => c ? `<a class="cchip" href="#/coin/${esc(c.mint)}">${coinFace(c)}$${esc(c.symbol)}</a>` : '';
  function fcard(it) {
    if (it.who) learn(it.who);
    const head = (w) => `<div class="hd"><b>${who(w)}</b><span class="t">${ago(it.t)}</span></div>`;
    if (it.kind === 'post') {
      return `<div class="fc" data-post="${it.id}">${avatar(it.wallet)}<div><div class="hd"><b>${who(it.wallet)}</b><span class="t">${ago(it.t)}</span></div><div class="tx">${linkify(it.text)}</div>${it.coin ? `<div style="margin-bottom:6px">${cchip(it.coin)}</div>` : ''}
        <div class="acts"><button type="button" data-like="${it.id}" class="${it.liked ? 'on' : ''}">♥ <span class="num">${it.likes || ''}</span></button><button type="button" data-reply="${it.id}">Reply${it.replies ? ' <span class="num">' + it.replies + '</span>' : ''}</button></div><div class="replies" id="rp-${it.id}" hidden></div></div></div>`;
    }
    const body = {
      launch: () => `<div class="ev">⚒ Struck a new coin: ${cchip(it.coin)}${it.coin ? ` <b>${esc(it.coin.name)}</b>` : ''}</div><a class="btn sm line" href="#/coin/${esc(it.coin && it.coin.mint)}">Look at it</a>`,
      whale: () => `<div class="ev">🐋 Whale buy: <b class="big num">${sol(it.sol)}</b> of ${cchip(it.coin)}</div>`,
      grad: () => `<div class="ev">🏛 ${cchip(it.coin)} <b>graduated</b>: its liquidity is now locked for good and it trades on Jupiter.</div>`,
      live: () => `<div class="ev"><span class="badge live">LIVE</span> Went live${it.data && it.data.title ? ': <b>' + esc(it.data.title) + '</b>' : ''}${it.coin ? ', launching ' + cchip(it.coin) : ''}</div><a class="btn sm live" href="#/ch/${esc(it.wallet)}">Watch</a>`,
      tip: () => `<div class="ev">💛 Tipped <b class="num">${sol(it.sol)}</b> to <a href="#/ch/${esc(it.data && it.data.channel)}">${esc((it.data && it.data.name) || 'a streamer')}</a></div>`,
      sub: () => `<div class="ev">⭐ Subscribed to <a href="#/ch/${esc(it.data && it.data.channel)}">${esc((it.data && it.data.name) || 'a streamer')}</a> for a month</div>`,
    }[it.kind];
    if (!body) return '';
    return `<div class="fc ${it.kind === 'whale' ? 'whale' : it.kind === 'live' ? 'live' : ''}">${it.kind === 'grad' ? (it.coin ? coinFace(it.coin, 'av') : avatar('')) : avatar(it.wallet)}<div>${it.kind === 'grad' ? `<div class="hd"><b>Graduation</b><span class="t">${ago(it.t)}</span></div>` : head(it.wallet)}${body()}</div></div>`;
  }
  function linkify(t) { return esc(t).replace(/\$([A-Z0-9]{2,10})\b/g, '<b style="color:var(--gold)">$$$1</b>').replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener nofollow">$1</a>'); }
  function wireFeed(root) {
    $$('[data-like]', root).forEach(b => b.onclick = async () => { try { await needSign(); const r = await apiA('/so/like', { post: +b.dataset.like }); b.classList.toggle('on', r.post.liked); b.querySelector('span').textContent = r.post.likes || ''; } catch (e) { if (e.message !== 'closed') toast(e.message); } });
    $$('[data-reply]', root).forEach(b => b.onclick = async () => {
      const box = $('#rp-' + b.dataset.reply); box.hidden = !box.hidden; if (box.hidden) return;
      box.innerHTML = '<div class="mute small">Loading…</div>';
      try { const r = await api('/so/post/' + b.dataset.reply); box.innerHTML = r.replies.map(x => { learn(x.who); return `<div class="rp">${avatar(x.wallet, 'xs')} <b>${who(x.wallet)}</b> ${linkify(x.text)} <span class="mute small">${ago(x.t)}</span></div>`; }).join('') + `<form class="composer" style="margin:6px 0 0;padding:8px 10px"><textarea class="inp" placeholder="Reply…" maxlength="280" style="min-height:40px"></textarea><div class="row" style="grid-column:1/-1"><span class="sp"></span><button class="btn gold sm" type="submit">Reply</button></div></form>`;
        $('form', box).onsubmit = async e => { e.preventDefault(); const ta = $('textarea', box); if (!ta.value.trim()) return; try { await needSign(); await apiA('/so/post', { text: ta.value, reply: +b.dataset.reply }); b.click(); b.click(); } catch (er) { toast(er.message); } };
      } catch (e) { box.innerHTML = `<div class="mute small">${esc(e.message)}</div>`; }
    });
  }
  function composer(opts) {
    const m = LPC.me();
    return `<form class="composer" id="cmp">${m ? avatar(m.address) : avatar('')}<div><textarea placeholder="${opts.placeholder || "What's happening? Tag a coin with $TICKER"}" maxlength="280" id="cmpt"></textarea>
      <div class="row">${opts.coin ? cchip(opts.coin) : ''}<span class="cnt" id="cmpc">280</span><span class="sp"></span><button class="btn gold sm" type="submit">${m ? (signed() ? 'Post' : 'Sign in and post') : 'Connect wallet to post'}</button></div></div></form>`;
  }
  function wireComposer(mint, after) {
    const f = $('#cmp'); if (!f) return;
    $('#cmpt').oninput = () => { $('#cmpc').textContent = 280 - $('#cmpt').value.length; };
    f.onsubmit = async e => { e.preventDefault(); const t = $('#cmpt').value.trim(); if (!t) return; const b = $('button', f); b.disabled = true;
      try { await needSign(); await apiA('/so/post', { text: t, mint: mint || '' }); $('#cmpt').value = ''; toast('Posted.'); after && after(); } catch (er) { if (er.message !== 'closed') toast(friendly(er)); } b.disabled = false; };
  }

  // ---------- Watch: the floor of the exchange. Live trades on the left, streams and the feed in the middle,
  // trending coins and the day's traders on the right. Everything refreshes on its own.
  let feedKind = 'all';
  async function watch() {
    app.innerHTML = `<section class="phero watch"><div><p class="kicker">Watch</p><h1>Every trade, launch and stream, as it happens</h1>
        <p class="lead">Watch the wallets that are winning, the coins they are in, and the people streaming their launches. Post what you see; tag a coin with its $TICKER.</p><div class="now" id="now"></div></div>
        <div class="spot" id="toth"></div></section>
      <div id="featured"></div>
      <div class="wgrid3">
        <aside class="wcol wl-left"><h3 class="colh"><span class="pulse"></span>Live trades</h3><div class="ltr" id="ltr"><div class="empty" style="padding:16px">Loading…</div></div></aside>
        <div class="wcol wmid"><div class="lives" id="lives"></div><div id="cmpbox"></div>
          <div class="chips tabs" style="margin-bottom:12px">${[['all', 'Everything'], ['posts', 'Posts'], ['launches', 'Launches'], ['whales', 'Whale buys'], ['grads', 'Graduations'], ['live', 'Streams'], ['tips', 'Tips']].map(([k, t]) => `<button class="chip${feedKind === k ? ' on' : ''}" data-fk="${k}">${t}</button>`).join('')}</div>
          <div class="feed" id="feed"><div class="empty">Loading the feed…</div></div></div>
        <aside class="wcol wright"><div class="panel"><h3>Trending this hour</h3><div class="trend" id="trend">Loading…</div></div>
          <div class="panel"><h3>Top wallets today</h3><div id="ldr">Loading…</div><p class="small mute" style="margin:8px 0 0">SOL taken out minus SOL put in, on this launchpad, today. What a wallet still holds is not counted, so it is a floor, not a score.</p></div>
          <div class="panel"><h3>Channels</h3><div id="chans">Loading…</div></div></aside></div>`;
    $('#cmpbox').innerHTML = composer({}); wireComposer('', () => loadFeed());
    $$('[data-fk]').forEach(b => b.onclick = () => { feedKind = b.dataset.fk; $$('[data-fk]').forEach(x => x.classList.toggle('on', x === b)); loadFeed(); });
    ltrSeen = new Set(); ltrFirst = true;
    loadFeed(); sideBars(); lives(); liveTrades();
    const t = setInterval(() => { loadFeed(true); sideBars(); lives(); }, 15000), t2 = setInterval(liveTrades, 6000); onLeave(() => { clearInterval(t); clearInterval(t2); });
  }
  let feedKey = '';
  async function loadFeed(quiet) {
    const el = $('#feed'); if (!el) return;
    try { const r = await apiA('/so/feed?kind=' + feedKind + '&limit=60'); const key = r.items.map(i => i.id).join(',') + feedKind;
      if (key === feedKey && quiet) return; feedKey = key;
      el.innerHTML = r.items.length ? r.items.map(fcard).join('') : `<div class="empty">Nothing here yet. ${feedKind === 'posts' ? 'Write the first post.' : 'Launches, whale buys, graduations and streams show up here as they happen.'}</div>`; wireFeed(el);
    } catch (e) { if (!quiet) el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }
  // the live trades column: new trades slide in at the top; whales get a bigger card
  let ltrSeen = new Set(), ltrFirst = true;
  async function liveTrades() {
    const el = $('#ltr'); if (!el) return;
    try {
      const r = await api('/lp/trades?limit=40'); r.trades.forEach(t => t.who && learn(t.who));
      const fresh = r.trades.filter(t => !ltrSeen.has(t.sig));
      if (ltrFirst) { el.innerHTML = r.trades.length ? r.trades.map(t => trow(t, false)).join('') : '<div class="empty" style="padding:16px">No trades yet. They show up here the moment they land.</div>'; ltrFirst = false; }
      else if (fresh.length) { if ($('.empty', el)) el.innerHTML = ''; el.insertAdjacentHTML('afterbegin', fresh.reverse().map(t => trow(t, true)).join('')); while (el.children.length > 40) el.lastElementChild.remove(); }
      r.trades.forEach(t => ltrSeen.add(t.sig));
    } catch (e) { if (ltrFirst) el.innerHTML = `<div class="empty" style="padding:16px">${esc(e.message)}</div>`; }
  }
  const trow = (t, anim) => `<div class="ltrow${t.sol >= 1 ? ' whale' : ''}${anim ? ' in' : ''}">${avatar(t.trader, 'sm')}<div class="ltb"><a class="addr" href="#/u/${esc(t.trader)}">${esc(nameOf(t.trader) || short(t.trader))}</a> <span class="${t.buy ? 'up' : 'dn'}">${t.buy ? 'bought' : 'sold'}</span> <b class="num">${t.sol.toFixed(t.sol < 0.01 ? 4 : t.sol < 1 ? 3 : 2)} SOL</b><br><a class="cchip" href="#/coin/${esc(t.mint)}">${coinFace(t)}$${esc(t.symbol)}</a>${t.sol >= 1 ? ' <span class="badge g">🐋 whale</span>' : ''}</div><span class="t">${ago(t.t)}</span></div>`;
  async function sideBars() {
    try { const r = await api('/so/trending'); const n = r.now, nowEl = $('#now');
      if (nowEl) nowEl.innerHTML = `<div class="hot"><b class="num">${n.tradesHour}</b>trades this hour</div><div><b class="num">${sol(n.volumeHour)}</b>traded</div><div><b class="num">${n.launchesDay}</b>struck today</div>${n.whalesDay ? `<div><b class="num">${n.whalesDay}</b>whale buys today</div>` : ''}${n.gradsDay ? `<div><b class="num">${n.gradsDay}</b>graduated today</div>` : ''}<div class="lv"><b class="num">${n.live}</b>${n.live ? '<span class="badge live">LIVE</span> ' : ''}streaming</div>`;
      const mx = Math.max(...r.coins.map(c => c.volume), 0.0001);
      const tr = $('#trend'); if (tr) tr.innerHTML = r.coins.length ? r.coins.slice(0, 8).map((c, i) => `<a class="trow" href="#/coin/${esc(c.mint)}"><span class="rank">${i + 1}</span>${coinFace(c)}<div><b>${esc(c.name)} <span class="mute">$${esc(c.symbol)}</span></b><span class="num">${sol(c.volume)} · ${c.trades} trades · ${c.traders} wallets</span><div class="bar" style="width:${(c.volume / mx * 100).toFixed(0)}%"></div></div><span class="${c.flow >= 0 ? 'up' : 'dn'} num">${c.flow >= 0 ? '+' : ''}${c.flow.toFixed(1)}</span></a>`).join('') : '<div class="mute small">No trades in the last hour.</div>';
    } catch (e) { }
    try { const l = await api('/lp/leaders?range=day&by=wallet'); const el = $('#ldr');
      const mx = Math.max(...l.top.map(r => Math.abs(r.net)), 0.0001);
      if (el) el.innerHTML = l.top.length ? l.top.slice(0, 8).map((r, i) => `<a class="ldr" href="#/u/${esc(r.trader)}"><span class="rank">${i + 1}</span>${avatar(r.trader)}<span class="nm"><b>${esc(nameOf(r.trader) || short(r.trader))}</b><span class="mute small">${r.trades} trades · ${r.coins} coin${r.coins === 1 ? '' : 's'}${r.best ? ' · best $' + esc(r.best.symbol) : ''}</span><i class="pnl ${r.net >= 0 ? 'up' : 'dn'}" style="width:${(Math.abs(r.net) / mx * 100).toFixed(0)}%"></i></span><b class="num ${r.net >= 0 ? 'up' : 'dn'}">${r.net >= 0 ? '+' : ''}${r.net.toFixed(2)}</b></a>`).join('') : '<div class="mute small">No trades yet today.</div>';
      // trader of the hour, spotlit in the hero
      const h = await api('/lp/leaders?range=hour&by=wallet'); const top = h.top[0], sp = $('#toth');
      if (sp) sp.innerHTML = top && top.net > 0 ? `<div class="toth"><span class="kicker">Wallet of the hour</span>${avatar(top.trader, 'lg')}<a class="nm" href="#/u/${esc(top.trader)}">${esc(nameOf(top.trader) || short(top.trader))}</a><b class="num up">+${top.net.toFixed(2)} SOL</b><span class="small mute">${top.trades} trades across ${top.coins} coin${top.coins === 1 ? '' : 's'}${top.best ? ', best on ' : ''}${top.best ? `<a class="cchip" href="#/coin/${esc(top.best.mint)}">${coinFace(top.best)}$${esc(top.best.symbol)}</a>` : ''}</span><a class="btn sm line" href="#/u/${esc(top.trader)}">Watch this wallet</a></div>` : `<div class="toth quiet"><span class="kicker">Wallet of the hour</span>${avatar('', 'lg')}<span class="mute">Nobody is up this hour yet.<br>The first wallet to take SOL out shows here.</span></div>`;
    } catch (e) { }
  }
  async function lives() {
    const el = $('#lives'); if (!el) return;
    try { const r = await api('/st/live'); r.channels.forEach(c => learn(c.who)); r.all.forEach(c => learn(c.who));
      el.innerHTML = r.channels.length ? `<h3 class="colh"><span class="badge live">LIVE</span> ${r.channels.length} streaming now</h3><div class="lrail">${r.channels.map(lcard).join('')}</div>` : `<div class="golive"><div><b>Nobody is live right now.</b><span class="mute"> Stream your game, your launch or your trades; viewers tip you in SOL and you keep all of it.</span></div><a class="btn gold sm" href="#/stream">Go live</a></div>`;
      const f = $('#featured'); if (f) { const c = r.channels[0];
        if (c && f.dataset.w !== c.wallet) { f.dataset.w = c.wallet; f.innerHTML = `<div class="feat"><div id="fplayer"></div><div class="featb"><div class="fhd">${avatar(c.wallet, 'lg')}<div style="min-width:0;flex:1"><b>${esc(c.title || c.name)}</b><span class="mute small">${esc(c.name)} · ${esc(c.category || '')} · <span class="badge live">LIVE</span> ${c.viewers} watching</span></div></div>
            ${c.coin ? `<a class="fcoin" href="#/coin/${esc(c.coin.mint)}">${coinFace(c.coin, 'av')}<span><b>$${esc(c.coin.symbol)}</b><span class="mute small">launching ${esc(c.coin.name)} live</span></span><span class="btn gold sm">Buy</span></a>` : ''}
            <div class="fchat" id="fchat"><div class="mute small">Chat…</div></div><a class="btn live" href="#/ch/${esc(c.wallet)}">Open the stream and chat</a></div></div>`; embed(c, $('#fplayer')); }
        if (c) { try { const ch = await api('/st/chat?channel=' + c.wallet + '&after=0'); const box = $('#fchat'); if (box) box.innerHTML = ch.msgs.slice(-6).map(x => { learn(x.who); return `<div class="m">${avatar(x.who.wallet, 'xs')} <b>${esc(x.who.name || short(x.who.wallet))}</b> ${linkify(x.text)}</div>`; }).join('') || '<div class="mute small">No chat yet. Say hello.</div>'; } catch (e) { } }
        else if (f.dataset.w) { f.innerHTML = ''; f.dataset.w = ''; } }
      const ch = $('#chans'); if (ch) ch.innerHTML = r.all.length ? r.all.slice(0, 12).map(c => `<a class="ldr" href="#/ch/${esc(c.wallet)}">${avatar(c.wallet)}<span class="nm"><b>${esc(c.name)}</b><span class="mute small">${esc(c.category || '')}</span></span>${c.live ? '<span class="badge live">LIVE</span>' : ''}</a>`).join('') : '<div class="mute small">No channels yet. <a href="#/stream">Make yours.</a></div>';
    } catch (e) { el.innerHTML = `<div class="empty" style="padding:16px">${esc(e.message)}</div>`; }
  }
  const lcard = (c) => `<a class="lcard" href="#/ch/${esc(c.wallet)}"><div class="thumb">${c.coin ? coinFace(c.coin, 'av') : avatar(c.wallet)}<span class="badge live">LIVE</span><span class="vw">${c.viewers} watching</span></div><div class="lb">${avatar(c.wallet, 'sm')}<div style="min-width:0"><b>${esc(c.title || c.name)}</b><span>${esc(c.name)} · ${esc(c.category || '')}${c.coin ? ' · launching $' + esc(c.coin.symbol) : ''}</span></div></div></a>`;

  // ---------- Stream: go live in three steps. New streamers see what their viewers will see before they start.
  const CATS = ['MemeCapes', 'Other games', 'Launching a coin', 'Trading', 'Just chatting'];
  const FAQ = [
    ['What do I need?', 'A Solana wallet (Phantom, Solflare or Backpack) and this browser. That is all. No account, no email, no password: your wallet is your sign-in. If you already stream with OBS or Streamlabs, you can use that instead of the browser.'],
    ['How do I get paid?', 'Tips and subscriptions are sent by the viewer, from their wallet straight to yours, in SOL. They land in seconds. MemeCapes never holds the money and takes no cut.'],
    ['Can I stream from my phone?', 'Yes. Open memecapes.com/launch.html inside your wallet app\'s browser, sign in, and go live with your camera. Screen sharing works from a computer.'],
    ['Can I stream my coin launch?', 'Yes, and it is the best way to launch. Attach your coin when you go live: viewers get a buy box right under your video, and your stream shows on the coin\'s page and in the Watch feed.'],
    ['What can I stream?', 'MemeCapes, any other game, trading, launches, or just talking. Nothing that is not yours to show and nothing for under-18s. Streams that break the rules are ended and the channel is hidden.'],
    ['Does it cost anything?', 'No. Going live is free. Signing in is a signed message, not a transaction, so there is no network fee either.'],
  ];
  const mock = () => `<div class="mock" aria-hidden="true"><div class="mplayer">${avatar('MockStreamer111111111111111111111', 'lg')}<span class="badge live">LIVE</span><span class="vw">128 watching</span><div class="mcoin"><span class="ph cf">MY</span>$MYCOIN <b>Buy</b></div></div>
    <div class="mside"><div class="mchat"><div style="animation-delay:.1s"><b>Froggo</b> first</div><div style="animation-delay:.7s"><b>capeLord</b> that cape tho</div><div style="animation-delay:1.3s"><b>Dee</b> buying a bag 👀</div><div class="tip" style="animation-delay:2s">💛 <b>Dee</b> tipped <b>0.5 SOL</b></div><div style="animation-delay:2.8s"><b>Snake</b> gg</div></div><div class="mtips"><span>0.05</span><span>0.1</span><span>0.5</span><span class="on">1 SOL</span></div></div></div>`;
  async function stream() {
    const m = LPC.me(); let me = null;
    if (m && signed()) { try { me = await apiA('/so/me'); learn(me); myCh = me.channel; } catch (e) { } }
    const step1 = !!m && signed(), step2 = !!(me && me.channel), live = me && me.channel && me.channel.live;
    app.innerHTML = `<section class="phero stream"><div><p class="kicker">Stream</p><h1>Go live. Keep everything.</h1>
        <p class="lead">Stream your game, your coin launch or your trades. Viewers tip you and subscribe to you in SOL, straight to your wallet: 100% is yours, the moment it is sent. Three steps, nothing to install.</p>
        <div class="ctas">${live ? '<a class="btn live" href="#sbody">You are live: open your stream</a>' : step2 ? '<a class="btn live" href="#sbody" id="golink">Go live now</a>' : step1 ? '<button class="btn gold" id="s2" type="button">Name your channel</button>' : '<button class="btn gold" id="s1" type="button">Connect wallet and start</button>'}<a class="btn quiet" href="#faq">How it works</a></div></div>
        <div class="mockwrap"><span class="kicker">What your viewers see</span>${mock()}</div></section>
      <div class="steps3">
        <div class="step${step1 ? ' done' : ''}"><i>1</i><b>Connect your wallet</b><span class="mute small">It is your sign-in and where tips arrive. No email, no password.</span><br>${step1 ? '<span class="up">Done</span>' : '<button class="btn gold sm" id="s1b" type="button" style="margin-top:10px">Connect and sign in</button>'}</div>
        <div class="step${step2 ? ' done' : ''}"><i>2</i><b>Name your channel</b><span class="mute small">A name, a line about you, and what a month's subscription costs.</span><br>${step2 ? `<span class="up">Done: ${esc(me.channel.name)}</span>` : (step1 ? '<button class="btn gold sm" id="s2b" type="button" style="margin-top:10px">Set up my channel</button>' : '<span class="mute small">After step 1</span>')}</div>
        <div class="step${live ? ' done' : ''}"><i>3</i><b>Go live</b><span class="mute small">From this browser with your camera or screen, or from OBS with a stream key.</span><br>${live ? '<span class="badge live">You are live</span>' : (step2 ? '<button class="btn live sm" id="s3" type="button" style="margin-top:10px">Go live</button>' : '<span class="mute small">After step 2</span>')}</div>
      </div>
      <div class="earn"><div><b>100%</b>of every tip and subscription is yours, paid to your wallet the moment it's sent. No cut, no minimum, no payout day.</div><div><b>Launch live</b>attach your coin to the stream: viewers buy it right under your video, and the coin's page shows you live.</div><div><b>Seen everywhere</b>the Watch page, the coin page and the game's own launchpad clerk all show your stream the second you start.</div></div>
      <div id="sbody"></div>
      <section class="faq2" id="faq"><h2>Streaming, explained</h2>${FAQ.map(([q, a]) => `<details><summary>${q}</summary><p>${a}</p></details>`).join('')}</section>`;
    const s1 = async () => { try { await signIn(); stream(); } catch (e) { if (e.message !== 'closed') toast(friendly(e)); } };
    ['#s1', '#s1b'].forEach(s => { if ($(s)) $(s).onclick = s1; });
    ['#s2', '#s2b'].forEach(s => { if ($(s)) $(s).onclick = () => channelForm(null); });
    if ($('#s3')) $('#s3').onclick = () => { goLivePanel(me); $('#sbody').scrollIntoView({ behavior: 'smooth' }); };
    if ($('#golink')) $('#golink').onclick = () => goLivePanel(me);
    if (step2) {
      const c = me.channel;
      $('#sbody').innerHTML = `<div class="panel chpanel"><div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">${avatar(m.address, 'lg')}<div><h3 style="margin:0">${esc(c.name)} ${c.live ? '<span class="badge live">LIVE</span>' : ''}</h3><div class="mute small">${esc(c.category)} · ${c.subSol} SOL a month to subscribe · <a href="#/ch/${esc(m.address)}">your channel page</a></div></div><span class="sp"></span><button class="btn quiet sm" id="edit" type="button">Edit channel</button>${c.live ? '<button class="btn quiet sm" id="end" type="button">End stream</button>' : ''}</div>
        ${me.streaming ? '' : '<div class="warn" style="margin-top:12px">Live video is not switched on yet. Your channel, chat, tips and subscriptions already work; the video switches on as soon as MemeCapes connects its streaming service.</div>'}
        <div id="golive"></div></div>`;
      $('#edit').onclick = () => channelForm(c);
      if ($('#end')) $('#end').onclick = async () => { try { await apiA('/st/end', {}); stopPublish(); toast('Stream ended.'); stream(); } catch (e) { toast(e.message); } };
      if (c.live && pub.pc) liveControls(me); else if (!c.live) goLivePanel(me);
    }
  }
  function channelForm(c) {
    const m = LPC.me(); const d = document.createElement('div'); d.className = 'modal';
    d.innerHTML = `<form class="panel"><h3>${c ? 'Edit your channel' : 'Set up your channel'}</h3>
      <div class="field"><label>Channel name</label><input class="inp" id="chn" maxlength="24" value="${esc(c ? c.name : (nameOf(m.address) || ''))}" placeholder="Snake TV"></div>
      <div class="field"><label>About you</label><textarea class="inp" id="cha" maxlength="300" placeholder="What you stream and when">${esc(c ? c.about : '')}</textarea></div>
      <div class="field"><label>What you mostly stream</label><div class="chips" id="chc">${CATS.map(x => `<button type="button" class="chip${(c ? c.category : 'MemeCapes') === x ? ' on' : ''}" data-c="${x}">${x}</button>`).join('')}</div></div>
      <div class="field"><label>A month's subscription (SOL)</label><input class="inp num" id="chs" inputmode="decimal" value="${c ? c.subSol : 0.1}"><div class="hint">Subscribers pay this straight to your wallet. You keep all of it.</div></div>
      <div style="display:flex;gap:8px"><button class="btn gold" type="submit">Save</button><button class="btn quiet" type="button" data-x>Cancel</button></div><div class="err" id="che"></div></form>`;
    document.body.appendChild(d); let cat = c ? c.category : 'MemeCapes';
    $$('[data-c]', d).forEach(b => b.onclick = () => { cat = b.dataset.c; $$('[data-c]', d).forEach(x => x.classList.toggle('on', x === b)); });
    $('[data-x]', d).onclick = () => d.remove();
    $('form', d).onsubmit = async e => { e.preventDefault(); try { await needSign(); const r = await apiA('/st/channel', { name: $('#chn').value, about: $('#cha').value, category: cat, subSol: +$('#chs').value }); myCh = r.channel; d.remove(); toast('Channel saved.'); stream(); } catch (er) { $('#che').textContent = friendly(er); } };
  }
  async function goLivePanel(me) {
    const box = $('#golive'); if (!box) return;
    let mine = []; try { mine = (await api('/lp/coins?creator=' + LPC.me().address)).coins; } catch (e) { }
    let mode = 'browser', cat = me.channel.category, mint = '';
    box.innerHTML = `<div style="margin-top:16px;border-top:1px solid var(--line);padding-top:14px"><h3>Go live</h3>
      <div class="field"><label>Title</label><input class="inp" id="glt" maxlength="80" placeholder="Launching $MYCOIN live" value="${esc(me.channel.title || '')}"></div>
      <div class="field"><label>What is this stream?</label><div class="chips">${CATS.map(x => `<button type="button" class="chip${cat === x ? ' on' : ''}" data-gc="${x}">${x}</button>`).join('')}</div></div>
      ${mine.length ? `<div class="field"><label>Attach one of your coins (optional)</label><div class="chips"><button type="button" class="chip on" data-gm="">None</button>${mine.map(c => `<button type="button" class="chip" data-gm="${esc(c.mint)}">${coinFace(c, 'av xs')} $${esc(c.symbol)}</button>`).join('')}</div><div class="hint">Viewers get a buy box for it right under your video, and your stream shows on the coin's page.</div></div>` : ''}
      <div class="field"><label>How you stream</label><div class="chips"><button type="button" class="chip on" data-gmode="browser">From this browser</button><button type="button" class="chip" data-gmode="obs">OBS or other software</button></div>
        <div class="hint" id="glh">Your camera, or your screen for games. Nothing to install.</div></div>
      <div class="chips" id="src" style="margin-bottom:12px"><button type="button" class="chip on" data-src="screen">Share my screen</button><button type="button" class="chip" data-src="camera">Use my camera</button></div>
      <button class="btn live" id="glgo" type="button">Go live</button><div class="err" id="gle"></div></div>`;
    $$('[data-gc]', box).forEach(b => b.onclick = () => { cat = b.dataset.gc; $$('[data-gc]', box).forEach(x => x.classList.toggle('on', x === b)); });
    $$('[data-gm]', box).forEach(b => b.onclick = () => { mint = b.dataset.gm; $$('[data-gm]', box).forEach(x => x.classList.toggle('on', x === b)); });
    let src = 'screen'; $$('[data-src]', box).forEach(b => b.onclick = () => { src = b.dataset.src; $$('[data-src]', box).forEach(x => x.classList.toggle('on', x === b)); });
    $$('[data-gmode]', box).forEach(b => b.onclick = () => { mode = b.dataset.gmode; $$('[data-gmode]', box).forEach(x => x.classList.toggle('on', x === b)); $('#src').style.display = mode === 'browser' ? '' : 'none'; $('#glh').textContent = mode === 'browser' ? 'Your camera, or your screen for games. Nothing to install.' : 'You get a stream key to paste into OBS, Streamlabs or any streaming app.'; });
    $('#glgo').onclick = async () => {
      const b = $('#glgo'), err = $('#gle'); err.textContent = ''; b.disabled = true;
      try {
        let ms = null;
        if (mode === 'browser') ms = src === 'screen' ? await navigator.mediaDevices.getDisplayMedia({ video: { width: 1280, height: 720, frameRate: 30 }, audio: true }) : await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: true });
        const r = await apiA('/st/golive', { title: $('#glt').value, category: cat, mode, mint });
        if (mode === 'browser') { await publish(r.whip, ms); toast('You are live.'); }
        else { box.innerHTML = `<div class="ok">Your stream is set up. Paste these into OBS (Settings → Stream → Custom), then press Start Streaming there.</div><div class="keybox" style="margin-top:10px">Server: <code>${esc(r.rtmps.url)}</code><br>Stream key: <code id="skey">••••••••</code> <button class="btn quiet sm" type="button" id="showk">Show</button></div><p class="small mute">Keep the key private: anyone with it can stream as you.</p>`; $('#showk').onclick = () => { $('#skey').textContent = r.rtmps.streamKey; }; return; }
        stream();
      } catch (e) { b.disabled = false; err.textContent = /NotAllowed|Permission/i.test(e.name || e.message) ? 'You said no to sharing your screen or camera. Try again and allow it.' : friendly(e); }
    };
  }
  // browser go-live: WebRTC to Cloudflare's WHIP endpoint, no software needed
  const pub = { pc: null, ms: null };
  async function publish(whip, ms) {
    if (!whip) throw new Error('No stream endpoint came back.');
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.cloudflare.com:3478' }], bundlePolicy: 'max-bundle' });
    ms.getTracks().forEach(t => pc.addTransceiver(t, { direction: 'sendonly' }));
    const offer = await pc.createOffer(); await pc.setLocalDescription(offer); await iceDone(pc);
    const r = await fetch(whip, { method: 'POST', headers: { 'Content-Type': 'application/sdp' }, body: pc.localDescription.sdp });
    if (!r.ok) throw new Error('The stream service refused the connection (' + r.status + ').');
    await pc.setRemoteDescription({ type: 'answer', sdp: await r.text() });
    pub.pc = pc; pub.ms = ms; ms.getVideoTracks()[0].onended = () => { stopPublish(); apiA('/st/end', {}).catch(() => { }); toast('Screen sharing stopped, so the stream ended.'); };
  }
  function stopPublish() { try { pub.pc && pub.pc.close(); } catch (e) { } try { pub.ms && pub.ms.getTracks().forEach(t => t.stop()); } catch (e) { } pub.pc = null; pub.ms = null; }
  const iceDone = pc => new Promise(ok => { if (pc.iceGatheringState === 'complete') return ok(); const t = setTimeout(ok, 1500); pc.onicegatheringstatechange = () => { if (pc.iceGatheringState === 'complete') { clearTimeout(t); ok(); } }; });
  function liveControls(me) {
    const box = $('#golive'); if (!box) return;
    box.innerHTML = `<div style="margin-top:14px"><div class="player" style="max-width:520px"><video id="pv" autoplay muted playsinline></video><div class="over"><span class="badge live">LIVE</span><span class="vw" id="pvv">0 watching</span></div></div><p class="small mute" style="margin-top:8px">Keep this tab open while you stream. Your channel page: <a href="#/ch/${esc(LPC.me().address)}">open it in another tab</a> to see chat.</p></div>`;
    $('#pv').srcObject = pub.ms;
    const t = setInterval(async () => { try { const r = await api('/st/chat?channel=' + LPC.me().address + '&after=999999999'); if ($('#pvv')) $('#pvv').textContent = r.viewers + ' watching'; } catch (e) { } }, 10000); onLeave(() => clearInterval(t));
  }
  // playing a stream: WebRTC (WHEP) for browser streams, Cloudflare's player for OBS streams
  function embed(st, el) {
    if (!el) return; if (!st.playUrl) { el.innerHTML = `<div class="player"><div class="off">${avatar(st.wallet, 'lg')}<div>Live, but the video is not available yet.</div></div></div>`; return; }
    if (st.playKind === 'iframe') { el.innerHTML = `<div class="player"><iframe src="${esc(st.playUrl)}?autoplay=true&muted=true" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen title="Live stream"></iframe></div>`; return; }
    el.innerHTML = `<div class="player"><video autoplay playsinline muted controls></video><div class="over"><span class="badge live">LIVE</span></div></div>`;
    const v = $('video', el); const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.cloudflare.com:3478' }] });
    pc.addTransceiver('video', { direction: 'recvonly' }); pc.addTransceiver('audio', { direction: 'recvonly' });
    pc.ontrack = e => { if (!v.srcObject) v.srcObject = e.streams[0]; };
    (async () => { try { const o = await pc.createOffer(); await pc.setLocalDescription(o); await iceDone(pc); const r = await fetch(st.playUrl, { method: 'POST', headers: { 'Content-Type': 'application/sdp' }, body: pc.localDescription.sdp }); await pc.setRemoteDescription({ type: 'answer', sdp: await r.text() }); } catch (e) { el.innerHTML = `<div class="player"><div class="off">${avatar(st.wallet, 'lg')}<div>The stream could not be played right now.</div></div></div>`; } })();
    onLeave(() => { try { pc.close(); } catch (e) { } });
  }

  // ---------- a channel page: the stream, chat, tips, subscribe
  async function ch(wallet) {
    app.innerHTML = '<div class="empty" style="margin:30px 0">Opening the channel…</div>';
    const c = await apiA('/st/ch/' + encodeURIComponent(wallet)); learn(c.who); c.tips.recent.forEach(t => learn(t.who));
    const m = LPC.me(), mine = m && m.address === wallet;
    app.innerHTML = `<div class="sgrid"><div>
      <div id="player">${c.live ? '' : `<div class="player"><div class="off">${avatar(wallet, 'lg')}<div><b>${esc(c.name)}</b> is offline.</div><div class="small">Follow to hear when they go live.</div></div></div>`}</div>
      <div style="display:flex;gap:12px;align-items:center;margin:12px 0;flex-wrap:wrap">${avatar(wallet, 'lg')}<div style="min-width:0;flex:1"><h1 style="font-size:24px;margin:0">${esc(c.live && c.title ? c.title : c.name)}</h1><div class="small mute">${esc(c.name)} · ${esc(c.category || '')} · ${c.live ? `<span class="badge live">LIVE</span> ${c.viewers} watching` : 'offline'} · ${c.followers} followers · ${c.subs} subscribers</div></div>
        ${mine ? '' : `<button class="btn ${c.following ? 'quiet' : 'line'} sm" id="fol" type="button">${c.following ? 'Following' : 'Follow'}</button>`}</div>
      ${c.coin ? `<div class="panel" style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">${coinFace(c.coin, 'av')}<div><b>Launching ${esc(c.coin.name)}</b> <span class="mute">$${esc(c.coin.symbol)}</span></div><span class="sp"></span><a class="btn gold sm" href="#/coin/${esc(c.coin.mint)}">Buy on the coin page</a></div>` : ''}
      ${c.about ? `<div class="panel"><h3>About</h3><p style="white-space:pre-wrap">${linkify(c.about)}</p></div>` : ''}
      <div class="panel"><h3>Recent tips</h3>${c.tips.n ? `<p class="small mute">${c.tips.n} tips, ${sol(c.tips.sol)} in all, every one straight to the streamer.</p>` + c.tips.recent.map(t => `<div class="tiprow">${avatar(t.wallet || (t.who && t.who.wallet), 'sm')}<b>${esc((t.who && t.who.name) || short(t.who && t.who.wallet))}</b> tipped <b class="num">${sol(t.sol)}</b><span class="mute small" style="margin-left:auto">${ago(t.t)}</span></div>`).join('') : '<p class="small mute">No tips yet. Be the first.</p>'}</div>
    </div><div>
      <div class="panel chat"><h3 style="margin:0 0 8px">Chat</h3><div class="msgs" id="msgs"><div class="m sys">Welcome. Be kind; the streamer and MemeCapes can remove messages.</div></div><form id="chatf"><input class="inp" id="chati" maxlength="200" placeholder="${m ? 'Say something' : 'Connect a wallet to chat'}" autocomplete="off"><button class="btn gold sm" type="submit">Send</button></form></div>
      ${mine ? '' : `<div class="panel"><h3>Tip ${esc(c.name)}</h3><p class="small mute">Goes straight from your wallet to theirs. MemeCapes never touches it.</p><div class="tips">${[0.05, 0.1, 0.5, 1].map(v => `<button class="btn quiet sm" type="button" data-tip="${v}">${v} SOL</button>`).join('')}</div><div style="display:flex;gap:6px"><input class="inp num" id="tipc" inputmode="decimal" placeholder="Other amount"><button class="btn gold sm" type="button" id="tipgo">Tip</button></div><div class="err" id="tipe"></div>
        <h3 style="margin-top:16px">Subscribe</h3><p class="small mute">${c.subSol} SOL a month, paid once to the streamer's wallet. ${c.mySub ? '<b class="up">You are subscribed.</b>' : 'Subscribers get a star in chat.'}</p><button class="btn gold" style="width:100%" type="button" id="subgo">${c.mySub ? 'Add another month' : 'Subscribe for ' + c.subSol + ' SOL'}</button><div class="err" id="sube"></div></div>`}
    </div></div>`;
    if (c.live) embed(c, $('#player'));
    if ($('#fol')) $('#fol').onclick = async () => { try { await needSign(); const on = $('#fol').textContent.trim() !== 'Following'; await apiA('/so/follow', { wallet, on }); ch(wallet); } catch (e) { if (e.message !== 'closed') toast(e.message); } };
    const payTo = async (amount, kind) => {
      const err = $(kind === 'tip' ? '#tipe' : '#sube'); err.textContent = '';
      try { if (!(amount > 0)) throw new Error('Enter an amount.'); await needWallet(); const sig = await LPC.pay(wallet, amount, 'memecapes ' + kind + ' ' + c.name, () => { });
        await api('/st/' + kind, { channel: wallet, sig }); toast(kind === 'tip' ? 'Tipped ' + amount + ' SOL. Thank you!' : 'Subscribed. Thank you!'); ch(wallet);
      } catch (e) { if (e.message !== 'closed') err.textContent = friendly(e); }
    };
    $$('[data-tip]').forEach(b => b.onclick = () => payTo(+b.dataset.tip, 'tip'));
    if ($('#tipgo')) $('#tipgo').onclick = () => payTo(parseFloat(($('#tipc').value || '').replace(',', '.')), 'tip');
    if ($('#subgo')) $('#subgo').onclick = () => payTo(c.subSol, 'sub');
    // chat: polled every 3 s
    let after = 0; const seenIds = new Set();
    const poll = async () => { try { const r = await api('/st/chat?channel=' + wallet + '&after=' + after); const box = $('#msgs'); if (!box) return; r.msgs.forEach(x => { if (seenIds.has(x.id)) return; seenIds.add(x.id); after = Math.max(after, x.id); learn(x.who); box.insertAdjacentHTML('beforeend', `<div class="m">${avatar(x.who.wallet, 'xs')} <b>${esc(x.who.name || short(x.who.wallet))}</b> ${linkify(x.text)}</div>`); }); if (r.msgs.length) box.scrollTop = box.scrollHeight; } catch (e) { } };
    await poll(); const t = setInterval(poll, 3000); onLeave(() => clearInterval(t));
    if (c.live) { const hb = () => api('/st/watch', { channel: wallet }).catch(() => { }); hb(); const t2 = setInterval(hb, 30000); onLeave(() => clearInterval(t2)); }
    $('#chatf').onsubmit = async e => { e.preventDefault(); const t3 = $('#chati').value.trim(); if (!t3) return; try { await needSign(); await apiA('/st/chat', { channel: wallet, text: t3 }); $('#chati').value = ''; poll(); } catch (er) { if (er.message !== 'closed') toast(friendly(er)); } };
  }

  // ---------- a wallet's page: their cape, their trading, their posts
  async function u(wallet) {
    app.innerHTML = '<div class="empty" style="margin:30px 0">Loading…</div>';
    const p = await apiA('/so/u/' + encodeURIComponent(wallet)); learn(p); p.posts.forEach(x => learn(x.who));
    const m = LPC.me(), mine = m && m.address === wallet;
    app.innerHTML = `<div class="uhead">${avatar(wallet, 'lg')}<div style="flex:1;min-width:0"><h1>${esc(p.name || short(wallet))}</h1><div class="small mute">${short(wallet)} · ${p.followers} followers${p.x ? ' · <a href="' + esc(p.x) + '" target="_blank" rel="noopener nofollow">X</a>' : ''}${p.channel ? ' · <a href="#/ch/' + esc(wallet) + '">' + esc(p.channel.name) + (p.channel.live ? ' <span class="badge live">LIVE</span>' : '') + '</a>' : ''}</div>${p.about ? `<p style="margin:6px 0 0">${linkify(p.about)}</p>` : ''}</div>
      ${mine ? '<button class="btn line sm" id="pedit" type="button">Edit profile</button>' : '<button class="btn line sm" id="pfol" type="button">Follow</button>'}</div>
      <div class="stats num"><div class="stat"><span>Trades</span><b>${p.trades}</b></div><div class="stat"><span>Coins traded</span><b>${p.coins}</b></div><div class="stat"><span>SOL in</span><b>${sol(p.solIn)}</b></div><div class="stat"><span>SOL out minus in</span><b class="${p.net >= 0 ? 'up' : 'dn'}">${p.net >= 0 ? '+' : ''}${p.net.toFixed(2)}</b></div></div>
      <div class="ugrid"><div><h3>Posts and activity</h3><div class="feed" id="ufeed">Loading…</div></div><div class="panel"><h3>Recent trades</h3><div id="utr">Loading…</div></div></div>`;
    if ($('#pedit')) $('#pedit').onclick = () => profileForm(p);
    if ($('#pfol')) $('#pfol').onclick = async () => { try { await needSign(); await apiA('/so/follow', { wallet, on: true }); toast('Following.'); u(wallet); } catch (e) { if (e.message !== 'closed') toast(e.message); } };
    try { const f = await apiA('/so/feed?wallet=' + wallet + '&limit=40'); $('#ufeed').innerHTML = f.items.length ? f.items.map(fcard).join('') : '<div class="empty">Nothing yet.</div>'; wireFeed($('#ufeed')); } catch (e) { $('#ufeed').innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
    try { const r = await api('/lp/trades?limit=200'); const mineT = r.trades.filter(t => t.trader === wallet).slice(0, 25); $('#utr').innerHTML = mineT.length ? mineT.map(t => A.tradeRow(t, 1, 1)).join('') : '<div class="mute small">No trades in the latest 200.</div>'; } catch (e) { $('#utr').textContent = ''; }
  }
  function profileForm(p) {
    const d = document.createElement('div'); d.className = 'modal'; let avatarData = '';
    d.innerHTML = `<form class="panel"><h3>Your profile</h3><div class="pic field"><label class="drop" for="pimg" id="pdrop">${p.avatar ? `<img src="${esc(p.avatar)}" alt="">` : 'Picture'}</label><input type="file" id="pimg" accept="image/png,image/jpeg,image/webp" hidden><div class="hint">Optional. Without one you keep your cape.</div></div>
      <div class="field"><label>Name</label><input class="inp" id="pn" maxlength="24" value="${esc(p.name || '')}"></div><div class="field"><label>About</label><textarea class="inp" id="pa" maxlength="200">${esc(p.about || '')}</textarea></div><div class="field"><label>X link</label><input class="inp" id="px" value="${esc(p.x || '')}" placeholder="https://x.com/you"></div>
      <div style="display:flex;gap:8px"><button class="btn gold" type="submit">Save</button><button class="btn quiet" type="button" data-x>Cancel</button></div><div class="err" id="pe"></div></form>`;
    document.body.appendChild(d); $('[data-x]', d).onclick = () => d.remove();
    $('#pimg').onchange = e => { const f = e.target.files[0]; if (!f) return; if (f.size > 600 * 1024) return toast('Picture over 600 KB.'); const r = new FileReader(); r.onload = () => { avatarData = r.result; $('#pdrop').innerHTML = `<img src="${avatarData}" alt="">`; }; r.readAsDataURL(f); };
    $('form', d).onsubmit = async e => { e.preventDefault(); try { await needSign(); const r = await apiA('/so/profile', { name: $('#pn').value, about: $('#pa').value, x: $('#px').value, avatar: avatarData }); learn(r); d.remove(); toast('Saved.'); u(r.wallet); } catch (er) { $('#pe').textContent = friendly(er); } };
  }
  // posts about one coin, on its page
  function coinPosts(c, el) {
    const draw = async () => { try { const r = await apiA('/so/feed?mint=' + c.mint + '&limit=30'); el.innerHTML = `<h3>Talk about $${esc(c.symbol)}</h3>` + composer({ coin: c, placeholder: 'What do you think of $' + c.symbol + '?' }) + `<div class="feed">${r.items.length ? r.items.map(fcard).join('') : '<div class="empty">No posts about this coin yet.</div>'}</div>`; wireComposer(c.mint, draw); wireFeed(el); } catch (e) { el.innerHTML = `<h3>Talk about $${esc(c.symbol)}</h3><div class="mute small">${esc(e.message)}</div>`; } };
    draw();
  }

  Object.assign(A.views, { watch, stream, ch, u });
  A.setSocial({ avatar, nameOf, coinPosts, embed, signIn, signed });
  tape();
  LPC.onChange(() => { if (!LPC.me()) { tok = ''; try { localStorage.removeItem('lp_tok'); } catch (e) { } } });
  if (/^#\/(watch|stream|ch|u)/.test(location.hash)) A.route();
})();
