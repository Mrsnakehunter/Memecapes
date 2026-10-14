/* MemeCapes Launchpad (launch.html). Views: coins (#/), one coin (#/coin/<mint>), launch (#/launch), my coins (#/me),
   how it works (#/how), MemeCapes fee desk (#/desk, only for the launchpad fee wallet).
   Everything on-chain goes through Meteora's Dynamic Bonding Curve SDK (lp/lpcore.js) and the person's own wallet (lp/chain.js). */
(function () {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const L = window.LPCORE, { web3, dbc, BN } = L;
  const MC = window.MC_CONFIG || {}, C = MC.launchpad || {};
  const NET = LPC.NET(), DEV = NET === 'devnet';
  const PARTNER = (DEV ? C.partnerDevnet : C.partner) || '';
  const SRV = String(MC.server || '').replace(/^wss:/, 'https:').replace(/^ws:/, 'http:').replace(/\/ws$/, '');
  const SUPPLY = 1e9, DEC = 6;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const short = a => a ? a.slice(0, 4) + '…' + a.slice(-4) : '';
  const app = $('#app');
  let solUsd = MC.solUsdFallback || 150;
  try { window.MCPAY && MCPAY.solUsd().then(v => { solUsd = v; }); } catch (e) { }

  // ---------- small helpers
  function toast(t, ms) { const d = document.createElement('div'); d.className = 'toast'; d.textContent = t; document.body.appendChild(d); setTimeout(() => d.remove(), ms || 3500); }
  const usd = v => !isFinite(v) ? '-' : v >= 1e9 ? '$' + (v / 1e9).toFixed(2) + 'B' : v >= 1e6 ? '$' + (v / 1e6).toFixed(2) + 'M' : v >= 1e3 ? '$' + (v / 1e3).toFixed(1) + 'K' : '$' + v.toFixed(v < 10 ? 2 : 0);
  const sol = v => (v >= 100 ? v.toFixed(0) : v >= 1 ? v.toFixed(2) : v.toFixed(4)) + ' SOL';
  const pct = v => (v >= 10 ? v.toFixed(0) : v.toFixed(1)) + '%';
  const ago = t => { const s = (Date.now() - t) / 1000; return s < 60 ? 'just now' : s < 3600 ? Math.floor(s / 60) + 'm ago' : s < 86400 ? Math.floor(s / 3600) + 'h ago' : Math.floor(s / 86400) + 'd ago'; };
  async function api(path, body) {
    if (!SRV) throw new Error('The launchpad server is not set up yet.');
    const sep = path.includes('?') ? '&' : '?';
    const r = await fetch(SRV + path + (body ? '' : sep + 'net=' + NET), body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, net: NET }) } : {});
    const j = await r.json().catch(() => ({})); if (!r.ok || j.error) throw new Error(j.error || 'The launchpad server did not answer.'); return j;
  }
  const PK = s => new web3.PublicKey(s);
  const ps = v => (v && v.poolState) || v;            // VirtualPool wraps PoolState
  const n = b => b == null ? 0 : Number(b.toString());

  // one coin, as a struck gold coin: picture in the middle, molten ring = how close it is to graduating
  function stamp(c, prog) {
    const p = Math.max(0, Math.min(1, prog || 0)), R = 46, L2 = 2 * Math.PI * R;
    const ring = p > 0 ? `<circle cx="50" cy="50" r="${R}" fill="none" stroke="url(#mlt)" stroke-width="5" stroke-linecap="round" stroke-dasharray="${(L2 * p).toFixed(1)} ${L2.toFixed(1)}" transform="rotate(-90 50 50)"/>` : '';
    const face = c && c.image ? `<img src="${esc(c.image)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<div class="ph">${esc(((c && c.symbol) || '?').slice(0, 3))}</div>`;
    return `<div class="stamp"><svg viewBox="0 0 100 100" aria-hidden="true"><defs><linearGradient id="mlt" x1="0" x2="1"><stop offset="0" stop-color="#ff8a3d"/><stop offset="1" stop-color="#ffd23f"/></linearGradient><radialGradient id="gld" cx=".35" cy=".3"><stop offset="0" stop-color="#ffe58a"/><stop offset=".6" stop-color="#d9a520"/><stop offset="1" stop-color="#7a5310"/></radialGradient></defs>
      <circle cx="50" cy="50" r="46" fill="url(#gld)"/><circle cx="50" cy="50" r="46" fill="none" stroke="#2b1d05" stroke-opacity=".35" stroke-width="5"/>${ring}
      <circle cx="50" cy="50" r="37.5" fill="none" stroke="#7a5310" stroke-width="1.2"/></svg>${face}</div>`;
  }

  // SOL raised on the curve before a coin graduates at a given market cap (from the same curve the launch uses)
  const RAISE = {};
  function raiseFor(mcapSol) {
    if (RAISE[mcapSol] == null) { try { const sv = F.grad; const g = (C.graduation || []).find(x => x.mcapSol === mcapSol); if (g) F.grad = g.id; RAISE[mcapSol] = n(curveParams().migrationQuoteThreshold) / 1e9; F.grad = sv; } catch (e) { RAISE[mcapSol] = mcapSol * 0.2; } }
    return RAISE[mcapSol];
  }
  // ---------- live state for many coins (pools + configs fetched in batches)
  const cache = new Map();   // pool -> {pool, config, t}
  async function liveMany(coins) {
    const prog = LPC.dbc().program, need = coins.filter(c => c.pool && (!cache.has(c.pool) || Date.now() - cache.get(c.pool).t > 20000));
    for (let i = 0; i < need.length; i += 90) {
      const part = need.slice(i, i + 90);
      try {
        const pools = await prog.account.virtualPool.fetchMultiple(part.map(c => PK(c.pool)));
        const cfgKeys = [...new Set(part.map(c => c.config))];
        const cfgs = await prog.account.poolConfig.fetchMultiple(cfgKeys.map(PK));
        const cm = new Map(cfgKeys.map((k, j) => [k, cfgs[j]]));
        part.forEach((c, j) => { if (pools[j]) cache.set(c.pool, { pool: pools[j], config: cm.get(c.config), t: Date.now() }); });
      } catch (e) { console.warn('live', e); }
    }
    return coins.map(c => ({ ...c, live: cache.get(c.pool) ? stats(cache.get(c.pool)) : null }));
  }
  function stats(s) {
    const p = ps(s.pool), cfg = s.config;
    const price = Number(dbc.getPriceFromSqrtPrice(p.sqrtPrice, cfg.tokenDecimal, 9).toString());   // SOL per token
    const supply = n(cfg.postMigrationTokenSupply) ? n(cfg.postMigrationTokenSupply) / 10 ** cfg.tokenDecimal : SUPPLY;
    const raised = n(p.quoteReserve) / 1e9, goal = n(cfg.migrationQuoteThreshold) / 1e9;
    const migrated = !!p.isMigrated;
    return { price, mcapSol: price * supply, mcapUsd: price * supply * solUsd, raised, goal, prog: migrated ? 1 : goal ? Math.min(1, raised / goal) : 0, migrated, done: migrated || (goal && raised >= goal),
      creatorFee: n(p.creatorQuoteFee) / 1e9, partnerFee: n(p.partnerQuoteFee) / 1e9, volume: n(p.metrics && p.metrics.totalTradingQuoteFee) / 1e9 };
  }

  // ---------- wallet button + picker
  function drawWallet() {
    const m = LPC.me(), b = $('#wbtn');
    b.innerHTML = m ? (m.icon ? `<img src="${esc(m.icon)}" alt="">` : '') + esc(short(m.address)) : 'Connect wallet';
    $('#net').innerHTML = DEV ? '<span class="netpill" title="Solana test network: coins and SOL here have no value">Test network</span>' : '';
  }
  function pickWallet() {
    return new Promise((ok, no) => {
      const ws = LPC.wallets();
      const d = document.createElement('div'); d.className = 'modal';
      d.innerHTML = `<div class="panel" role="dialog" aria-label="Connect a wallet"><h3>Connect a wallet</h3>
        ${ws.length ? '<p class="mute small">Your wallet shows you every transaction before you approve it. MemeCapes never sees your keys.</p><div class="wl">' + ws.map(w => `<button type="button" data-w="${esc(w.name)}">${w.icon ? `<img src="${esc(w.icon)}" alt="">` : ''}${esc(w.name)}</button>`).join('') + '</div>'
          : '<p>No Solana wallet found in this browser. Install <a href="https://phantom.com" target="_blank" rel="noopener">Phantom</a>, <a href="https://solflare.com" target="_blank" rel="noopener">Solflare</a> or <a href="https://backpack.app" target="_blank" rel="noopener">Backpack</a>, then reload. On a phone, open memecapes.com/launch.html inside your wallet app\'s browser.</p>'}
        <button class="btn quiet" type="button" data-x>Close</button></div>`;
      document.body.appendChild(d);
      d.onclick = async e => {
        const w = e.target.closest('[data-w]');
        if (e.target === d || e.target.closest('[data-x]')) { d.remove(); return no(new Error('closed')); }
        if (w) { try { const m = await LPC.connect(w.dataset.w); d.remove(); ok(m); } catch (er) { toast(er.message || 'The wallet did not connect.'); } }
      };
    });
  }
  async function needWallet() { return LPC.me() || await pickWallet(); }
  $('#wbtn').onclick = async () => { if (LPC.me()) { if (confirmQuiet('Disconnect ' + short(LPC.me().address) + '?')) await LPC.disconnect(); } else pickWallet().catch(() => { }); };
  function confirmQuiet(t) { return window.confirm(t); }
  LPC.onChange(() => { drawWallet(); route(); });
  LPC.onWallets(() => { });

  // ---------- views
  const views = { home, coin, launch, me: mine, how, desk };
  function route() {
    const h = location.hash.replace(/^#\/?/, ''), [v, arg] = h.split('/');
    const name = views[v] ? v : 'home';
    $$('[data-r]').forEach(a => a.classList.toggle('on', a.dataset.r === name));
    window.scrollTo(0, 0);
    Promise.resolve(views[name](arg)).catch(e => { app.innerHTML = `<div class="empty" style="margin:30px 0">${esc(e.message || e)}</div>`; });
  }
  window.addEventListener('hashchange', route);

  // ---- home: what's new on the launchpad
  let homeTab = 'new', homeQ = '';
  async function home() {
    app.innerHTML = `<section class="hero"><div>
      <h1>Launch a coin. Keep more of the fees.</h1>
      <p class="lead">Coins launched here start on a fair bonding curve and graduate to a real pool with locked liquidity. You choose the fee, how much of it you keep, how long snipers pay extra, and who your share goes to. Then trade them while you play MemeCapes.</p>
      <div class="acts"><a class="btn gold" href="#/launch">Launch a coin</a><a class="btn line" href="#/how">How it works</a></div></div>
      <div class="panel"><table class="vs"><thead><tr><th></th><th>MemeCapes</th><th>pump.fun</th></tr></thead><tbody>
        <tr><td>Fee traders pay on the curve</td><td>You choose, ${pct(((C.feeBps || {}).min || 25) / 100)} to ${pct(((C.feeBps || {}).max || 200) / 100)} (1% by default)</td><td>1.25%</td></tr>
        <tr><td>Launcher's cut of each trade</td><td>${(((C.feeBps || {}).def || 100) / 100 * 0.8 * ((C.creatorShare || {}).def || 60) / 100).toFixed(2)}% by default, up to ${(((C.feeBps || {}).max || 200) / 100 * 0.8 * ((C.creatorShare || {}).max || 80) / 100).toFixed(2)}%</td><td>0.30%</td></tr>
        <tr><td>Sniper fee at launch</td><td>Optional, up to ${pct(((C.sniperFee || {}).maxBps || 5000) / 100)}, falling to normal over up to ${Math.round(((C.sniperFee || {}).maxSeconds || 600) / 60)} minutes</td><td>None in its fee list</td></tr>
        <tr><td>Team tokens</td><td>Locked on-chain, unlocking after graduation</td><td>Not offered</td></tr>
        <tr><td>When a coin graduates</td><td>You pick: about ${(C.graduation || []).map(g => raiseFor(g.mcapSol).toFixed(0)).join(', ')} SOL raised</td><td>About 85 SOL raised</td></tr>
        <tr><td>Play a game while you trade</td><td>Yes</td><td>No</td></tr>
      </tbody></table><p class="small mute" style="margin:8px 0 0">pump.fun figures from <a href="https://pump.fun/docs/fees" target="_blank" rel="noopener">its fee page</a>, October 2026. Both let you split your fees with up to 10 wallets.</p></div></section>
      <section><div class="tabs" role="tablist">${[['new', 'New'], ['hot', 'Almost graduated'], ['grad', 'Graduated'], ['ver', 'Verified']].map(([k, t]) => `<button class="tab${homeTab === k ? ' on' : ''}" data-t="${k}" role="tab">${t}</button>`).join('')}
        <input class="search" id="q" placeholder="Search name, ticker or address" value="${esc(homeQ)}" aria-label="Search coins"></div>
        <div id="grid" class="coins"><div class="empty" style="grid-column:1/-1">Loading coins…</div></div></section>`;
    $$('.tab').forEach(b => b.onclick = () => { homeTab = b.dataset.t; home(); });
    $('#q').oninput = e => { homeQ = e.target.value; draw(); };
    let coins = [];
    try { coins = (await api('/lp/coins?limit=150')).coins; } catch (e) { $('#grid').innerHTML = `<div class="empty" style="grid-column:1/-1">${esc(e.message)}</div>`; return; }
    const draw = () => {
      const q = homeQ.trim().toLowerCase();
      let L2 = coins.filter(c => !q || (c.name + ' ' + c.symbol + ' ' + c.mint).toLowerCase().includes(q));
      if (homeTab === 'hot') L2 = L2.filter(c => c.live && !c.live.migrated && c.live.prog >= 0.5).sort((a, b) => b.live.prog - a.live.prog);
      if (homeTab === 'grad') L2 = L2.filter(c => c.live && c.live.migrated);
      if (homeTab === 'ver') L2 = L2.filter(c => c.verified);
      $('#grid').innerHTML = L2.length ? L2.map(card).join('') : `<div class="empty" style="grid-column:1/-1">${coins.length ? 'No coins here yet.' : 'No coins launched yet. <a href="#/launch">Be the first.</a>'}</div>`;
    };
    draw();
    coins = await liveMany(coins); draw();
  }
  function card(c) {
    const s = c.live;
    return `<a class="coin" href="#/coin/${esc(c.mint)}">${stamp(c, s && s.prog)}<b>${esc(c.name)}</b><span class="tk">$${esc(c.symbol)}</span>${c.verified ? ' <span class="badge v">Verified</span>' : ''}
      <div class="mc num">${s ? usd(s.mcapUsd) : '…'}</div><div class="mute small">${s ? (s.migrated ? 'Graduated' : pct(s.prog * 100) + ' to graduation') : ''}${c.t ? ' · ' + ago(c.t) : ''}</div></a>`;
  }

  // ---- one coin
  async function coin(mint) {
    app.innerHTML = '<div class="empty" style="margin:30px 0">Loading the coin…</div>';
    const c = await api('/lp/coin/' + encodeURIComponent(mint));
    const client = LPC.dbc();
    const vp = await client.state.getPool(PK(c.pool)); if (!vp) throw new Error('This coin\'s pool was not found on Solana.');
    const cfg = await client.state.getPoolConfig(ps(vp).config);
    let meta = {}; try { meta = await (await fetch(c.uri)).json(); } catch (e) { }
    const s = stats({ pool: vp, config: cfg }), plan = (meta.memecapes || {});
    const fees = feeInfo(cfg);
    const me = LPC.me(), isCreator = me && me.address === c.creator;
    const links = [['website', 'Website'], ['twitter', 'X'], ['telegram', 'Telegram']].filter(([k]) => meta[k]).map(([k, t]) => `<a href="${esc(meta[k])}" target="_blank" rel="noopener nofollow">${t}</a>`).join(' · ');
    app.innerHTML = `<div class="cgrid"><div>
      <div class="chead">${stamp(c, s.prog)}<div><h1>${esc(c.name)}</h1><div><b>$${esc(c.symbol)}</b> ${c.verified ? '<span class="badge v" title="Checked by the MemeCapes team">Verified</span>' : ''} ${s.migrated ? '<span class="badge g">Graduated</span>' : ''} ${c.reports > 2 ? '<span class="badge r">Reported</span>' : ''}</div>
        <div class="small mute">Launched ${ago(c.t)} by <a href="${LPC.explorer('acct', c.creator)}" target="_blank" rel="noopener" class="addr">${short(c.creator)}</a>${links ? ' · ' + links : ''}</div></div></div>
      <div class="stats num"><div class="stat"><span>Market cap</span><b>${usd(s.mcapUsd)}</b></div><div class="stat"><span>Price</span><b>${s.price < 0.000001 ? s.price.toExponential(2) : s.price.toFixed(9)} SOL</b></div>
        <div class="stat"><span>Raised on the curve</span><b>${sol(s.raised)}</b></div><div class="stat"><span>Fees paid so far</span><b>${sol(s.volume)}</b></div></div>
      ${s.migrated ? '<div class="ok">This coin graduated: it trades in a Meteora pool with its liquidity locked for good.</div>' : `<div><b>${pct(s.prog * 100)}</b> of the way to graduation <span class="mute">(${sol(s.raised)} of ${sol(s.goal)})</span><div class="crucible"><i style="width:${(s.prog * 100).toFixed(1)}%"></i></div><span class="mute small">At ${sol(s.goal)} the coin moves to a Meteora pool and its liquidity is locked for good.</span></div>`}
      <div class="panel" style="margin-top:16px;padding:0;overflow:hidden"><iframe class="chart" title="Price chart" loading="lazy" src="https://dexscreener.com/solana/${esc(s.migrated ? c.mint : c.pool)}?embed=1&loadChartSettings=0&trades=0&tabs=0&info=0&chartLeftToolbar=0&chartTheme=dark&theme=dark&chartStyle=1&chartType=usd&interval=5"></iframe></div>
      ${meta.description ? `<div class="panel"><h3>About</h3><p style="white-space:pre-wrap;font-family:var(--serif)">${esc(meta.description)}</p></div>` : ''}
      <div class="panel"><h3>Fees on every trade</h3>${feeBar(fees)}<p class="small mute">${fees.sniper ? `Starts at ${pct(fees.sniper.startBps / 100)} for the first ${fees.sniper.seconds} seconds and falls to ${pct(fees.baseBps / 100)} (stops sniper bots). ` : ''}When trading is busy the fee can rise by up to a fifth to protect the price. After graduation the pool fee is ${pct(fees.postBps / 100)}.</p>
        ${plan.routes && plan.routes.length ? `<p class="small"><b>The launcher's plan for their share:</b> ${plan.routes.map(r => esc(r.pct + '% to ' + (r.label || short(r.to)))).join(', ')}.</p>` : ''}
        ${fees.team ? `<p class="small"><b>Team tokens:</b> ${pct(fees.team.pct)} of the supply, locked, unlocking over ${fees.team.days} days after graduation.</p>` : ''}</div>
      <div class="panel"><h3>Top holders</h3><div id="holders" class="small mute">Loading…</div></div>
      <div class="panel small"><dl class="kv"><dt>Coin address</dt><dd><a href="${LPC.explorer('token', c.mint)}" target="_blank" rel="noopener" class="addr">${esc(c.mint)}</a></dd><dt>Pool</dt><dd><a href="${LPC.explorer('acct', c.pool)}" target="_blank" rel="noopener" class="addr">${esc(short(c.pool))}</a></dd>
        <dt>Supply</dt><dd>${(SUPPLY).toLocaleString()} (no more can ever be made)</dd><dt>Report</dt><dd><button class="btn quiet" style="padding:4px 10px;font-size:13px" id="rep" type="button">Report this coin</button></dd></dl></div>
    </div><div class="trade"><div class="panel" id="tbox"></div>${isCreator ? '<div class="panel" id="cbox"></div>' : ''}</div></div>`;
    tradeBox(c, vp, cfg, s);
    if (isCreator) creatorBox(c, vp, cfg, plan);
    holders(c, vp);
    $('#rep').onclick = async () => { const why = prompt('What is wrong with this coin? (scam, stolen picture, impersonation, ...)'); if (!why) return; try { await api('/lp/report', { mint: c.mint, why }); toast('Thanks. The MemeCapes team will look at it.'); } catch (e) { toast(e.message); } };
  }
  function feeInfo(cfg) {
    const bf = cfg.poolFees.baseFee, cliff = n(bf.cliffFeeNumerator) / 1e7;   // bps
    let baseBps = cliff, sniper = null;
    // fee scheduler: firstFactor = number of periods, secondFactor = seconds per period, thirdFactor = reduction factor
    try { const end = dbc.calculateFeeSchedulerEndingBaseFeeBps(n(bf.cliffFeeNumerator), n(bf.firstFactor), n(bf.secondFactor), n(bf.thirdFactor), bf.baseFeeMode); if (end && end < cliff) { baseBps = end; sniper = { startBps: cliff, seconds: n(bf.firstFactor) * n(bf.secondFactor) }; } } catch (e) { }
    const cs = cfg.creatorTradingFeePercentage;
    const team = n(cfg.lockedVestingConfig.amountPerPeriod) ? { pct: (n(cfg.lockedVestingConfig.amountPerPeriod) * n(cfg.lockedVestingConfig.numberOfPeriod) + n(cfg.lockedVestingConfig.cliffUnlockAmount)) / 10 ** cfg.tokenDecimal / SUPPLY * 100, days: Math.round((n(cfg.lockedVestingConfig.cliffDurationFromMigrationTime) + n(cfg.lockedVestingConfig.frequency) * n(cfg.lockedVestingConfig.numberOfPeriod)) / 86400) } : null;
    return { baseBps, sniper, creatorShare: cs, postBps: cfg.migratedPoolFeeBps || 0, team };
  }
  // where every trade fee goes: Meteora 20%, then the launcher's share, then MemeCapes (half of which burns $CAPES)
  function feeBar(f) {
    const tot = f.baseBps / 100, met = tot * 0.2, rest = tot - met, cr = rest * f.creatorShare / 100, mc = rest - cr, burn = mc * (C.burnShare || 50) / 100;
    const w = v => (v / tot * 100).toFixed(2) + '%', lab = (v, t) => v / tot > 0.17 ? t : '';   // a label only where it fits
    return `<div class="feebar" role="img" aria-label="Where each trade fee goes"><div class="fb-c" style="width:${w(cr)}">${lab(cr, 'Launcher')}</div><div class="fb-p" style="width:${w(mc - burn)}">${lab(mc - burn, 'MemeCapes')}</div><div class="fb-b" style="width:${w(burn)}">${lab(burn, 'Burn')}</div><div class="fb-m" style="width:${w(met)}">${lab(met, 'Meteora')}</div></div>
      <div class="legend num"><i style="background:var(--gold)"></i><span>The launcher</span><b>${tot ? (cr).toFixed(3) : 0}%</b>
      <i style="background:#c9822b"></i><span>MemeCapes</span><b>${(mc - burn).toFixed(3)}%</b>
      <i class="fb-b"></i><span>Buys $CAPES and burns it</span><b>${burn.toFixed(3)}%</b>
      <i style="background:#6b5a44"></i><span>Meteora (runs the pool program)</span><b>${met.toFixed(3)}%</b>
      <span></span><span><b>Total fee on each trade</b></span><b>${tot.toFixed(2)}%</b></div>`;
  }
  async function holders(c, vp) {
    try {
      const r = await LPC.connection().getTokenLargestAccounts(PK(c.mint));
      const vault = ps(vp).baseVault.toBase58(), tot = SUPPLY * 10 ** DEC;
      const rows = await Promise.all(r.value.slice(0, 12).map(async a => {
        let owner = a.address.toBase58();
        if (owner === vault) owner = 'Bonding curve';
        else { try { const i = await LPC.connection().getParsedAccountInfo(a.address); owner = i.value.data.parsed.info.owner; } catch (e) { } }
        return `<tr><td class="addr">${owner === 'Bonding curve' ? 'Bonding curve (unsold)' : `<a href="${LPC.explorer('acct', owner)}" target="_blank" rel="noopener">${short(owner)}</a>${owner === c.creator ? ' (launcher)' : ''}`}</td><td class="num">${(n(a.amount) / tot * 100).toFixed(2)}%</td></tr>`;
      }));
      $('#holders').innerHTML = `<table class="holders">${rows.join('')}</table>`;
    } catch (e) { $('#holders').textContent = 'Could not load holders right now.'; }
  }
  function tradeBox(c, vp, cfg, s) {
    const box = $('#tbox'); let side = 'buy';
    if (s.migrated) { box.innerHTML = `<h3>Trade</h3><p>This coin graduated and now trades in its Meteora pool.</p><a class="btn gold" style="width:100%" href="https://jup.ag/swap/SOL-${esc(c.mint)}" target="_blank" rel="noopener">Trade on Jupiter</a>`; return; }
    const draw = () => {
      box.innerHTML = `<div class="seg"><button class="buy${side === 'buy' ? ' on' : ''}" type="button" data-s="buy">Buy</button><button class="sell${side === 'sell' ? ' on' : ''}" type="button" data-s="sell">Sell</button></div>
        <div class="field"><label for="amt">${side === 'buy' ? 'You pay (SOL)' : 'You sell ($' + esc(c.symbol) + ')'}</label><input class="inp num" id="amt" inputmode="decimal" placeholder="0.0" autocomplete="off">
        <div class="amt">${(side === 'buy' ? ['0.1', '0.5', '1', '5'] : ['25%', '50%', '100%']).map(v => `<button type="button" data-a="${v}">${v}${side === 'buy' ? ' SOL' : ''}</button>`).join('')}</div><div class="hint" id="bal"></div></div>
        <div class="quote num" id="qt"><div><span>You get</span><span>-</span></div></div>
        <div class="field"><label for="slip">Max price move (slippage)</label><div class="chips">${[1, 3, 5, 10].map(v => `<button type="button" class="chip${v === slip ? ' on' : ''}" data-sl="${v}">${v}%</button>`).join('')}</div></div>
        <button class="btn gold" style="width:100%" id="go" type="button">${side === 'buy' ? 'Buy' : 'Sell'} $${esc(c.symbol)}</button><div class="err" id="terr"></div>`;
      $$('[data-s]', box).forEach(b => b.onclick = () => { side = b.dataset.s; draw(); });
      $$('[data-sl]', box).forEach(b => b.onclick = () => { slip = +b.dataset.sl; draw(); });
      $$('[data-a]', box).forEach(b => b.onclick = () => { const v = b.dataset.a; if (v.endsWith('%')) { $('#amt').value = tokBal ? (tokBal * parseFloat(v) / 100).toFixed(DEC).replace(/\.?0+$/, '') : ''; } else $('#amt').value = v; quote(); });
      $('#amt').oninput = () => { clearTimeout(qt); qt = setTimeout(quote, 250); };
      $('#go').onclick = go;
      balances();
    };
    let slip = 3, qt = 0, tokBal = 0, last = null;
    async function balances() {
      const m = LPC.me(); if (!m) { $('#bal').textContent = 'Connect a wallet to trade.'; return; }
      try {
        const sb = await LPC.solBalance(m.address);
        let tb = 0; try { const r = await LPC.connection().getTokenAccountsByOwner(m.pubkey, { mint: PK(c.mint) }, 'confirmed'); for (const a of r.value) tb += Number(Buffer_readU64(a.account.data, 64)) / 10 ** DEC; } catch (e) { }
        tokBal = tb; $('#bal').textContent = `You have ${sb.toFixed(3)} SOL and ${tb.toLocaleString(undefined, { maximumFractionDigits: 0 })} $${c.symbol}.`;
      } catch (e) { }
    }
    async function quote() {
      const v = parseFloat(($('#amt').value || '').replace(',', '.')); const q = $('#qt'); last = null;
      if (!(v > 0)) { q.innerHTML = '<div><span>You get</span><span>-</span></div>'; return; }
      try {
        const amountIn = new BN(Math.floor(v * (side === 'buy' ? 1e9 : 10 ** DEC)).toString());
        const point = await dbc.getCurrentPoint(LPC.connection(), cfg.activationType);
        const fresh = await LPC.dbc().state.getPool(PK(c.pool)) || vp;
        const r = LPC.dbc().pool.swapQuote2({ virtualPool: fresh, config: cfg, swapBaseForQuote: side === 'sell', hasReferral: false, currentPoint: point, slippageBps: slip * 100, swapMode: dbc.SwapMode.ExactIn, amountIn });
        const out = n(r.outputAmount != null ? r.outputAmount : r.amountOut) / (side === 'buy' ? 10 ** DEC : 1e9);
        const fee = n(r.tradingFee != null ? r.tradingFee : (r.fee && r.fee.trading)) / 1e9;
        last = { amountIn, min: r.minimumAmountOut };
        q.innerHTML = `<div><span>You get about</span><b>${side === 'buy' ? out.toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' $' + esc(c.symbol) : sol(out)}</b></div><div><span>At least</span><span>${side === 'buy' ? (n(r.minimumAmountOut) / 10 ** DEC).toLocaleString(undefined, { maximumFractionDigits: 0 }) : sol(n(r.minimumAmountOut) / 1e9)}</span></div>${fee ? `<div><span>Fee</span><span>${sol(fee)}</span></div>` : ''}`;
      } catch (e) { q.innerHTML = `<div><span>Quote</span><span>${esc(e.message || 'not available')}</span></div>`; }
    }
    async function go() {
      $('#terr').textContent = '';
      try {
        const m = await needWallet(); await quote(); if (!last) throw new Error('Enter an amount first.');
        const btn = $('#go'); btn.disabled = true; btn.textContent = 'Check your wallet…';
        const tx = await LPC.dbc().pool.swap2({ owner: m.pubkey, pool: PK(c.pool), swapBaseForQuote: side === 'sell', referralTokenAccount: null, payer: m.pubkey, swapMode: dbc.SwapMode.ExactIn, amountIn: last.amountIn, minimumAmountOut: last.min });
        const [sig] = await LPC.sendAll([tx], null, st => { btn.textContent = st === 'wallet' ? 'Approve in your wallet…' : 'Confirming…'; });
        toast((side === 'buy' ? 'Bought' : 'Sold') + ' $' + c.symbol + '.'); cache.delete(c.pool); setTimeout(() => coin(c.mint), 600);
        console.log('trade', sig);
      } catch (e) { if (e.message !== 'closed') $('#terr').textContent = friendly(e); const b = $('#go'); if (b) { b.disabled = false; b.textContent = (side === 'buy' ? 'Buy' : 'Sell') + ' $' + c.symbol; } }
    }
    draw();
  }
  function Buffer_readU64(data, off) { const b = data instanceof Uint8Array ? data : new Uint8Array(data); let x = 0n; for (let i = 7; i >= 0; i--) x = x * 256n + BigInt(b[off + i]); return x; }
  function friendly(e) {
    const m = String((e && e.message) || e || '');
    if (/User rejected|rejected the request|declined/i.test(m)) return 'You cancelled it in your wallet. Nothing was sent.';
    if (/insufficient (lamports|funds)|0x1\b/i.test(m)) return 'Not enough SOL in your wallet for this (remember the network fee).';
    if (/slippage|ExceededSlippage|0x1771|AmountOutBelow/i.test(m)) return 'The price moved more than your slippage allows. Try again, or allow a bigger move.';
    return m.slice(0, 220);
  }

  // the launcher's own fee claim, paid out to their split in the same transaction
  function creatorBox(c, vp, cfg, plan) {
    const box = $('#cbox'); const s = stats({ pool: vp, config: cfg });
    const routes = (plan.routes || []).filter(r => r.to && r.pct > 0);
    box.innerHTML = `<h3>Your fees</h3><p>Ready to claim: <b class="num">${sol(s.creatorFee)}</b></p>
      ${routes.length ? `<p class="small mute">Claiming also pays your split in the same transaction: ${routes.map(r => esc(r.pct + '% to ' + (r.label || short(r.to)))).join(', ')}.</p>` : ''}
      <button class="btn gold" style="width:100%" id="claim" type="button" ${s.creatorFee > 0 ? '' : 'disabled'}>Claim ${sol(s.creatorFee)}</button><div class="err" id="cerr"></div>`;
    $('#claim').onclick = async () => {
      const b = $('#claim'); b.disabled = true; $('#cerr').textContent = '';
      try {
        const m = await needWallet();
        const amt = n(ps(vp).creatorQuoteFee);
        const tx = await LPC.dbc().creator.claimCreatorTradingFee({ creator: m.pubkey, payer: m.pubkey, pool: PK(c.pool), maxBaseAmount: new BN(0), maxQuoteAmount: new BN(amt.toString()) });
        for (const r of routes) { const lam = Math.floor(amt * r.pct / 100); if (lam > 0 && r.to !== m.address) tx.add(web3.SystemProgram.transfer({ fromPubkey: m.pubkey, toPubkey: PK(r.to), lamports: lam })); }
        await LPC.sendAll([tx], null, st => { b.textContent = st === 'wallet' ? 'Approve in your wallet…' : 'Confirming…'; });
        toast('Claimed.'); cache.delete(c.pool); coin(c.mint);
      } catch (e) { if (e.message !== 'closed') $('#cerr').textContent = friendly(e); b.disabled = false; b.textContent = 'Claim'; }
    };
  }

  // ---- launch a coin
  const F = { name: '', symbol: '', description: '', website: '', x: '', telegram: '', image: '', preset: 'standard',
    feeBps: (C.feeBps || {}).def || 100, share: (C.creatorShare || {}).def || 60, sniperBps: (C.sniperFee || {}).defBps || 2500, sniperSec: (C.sniperFee || {}).defSeconds || 60,
    grad: 'standard', postBps: (C.postFeeBps || {}).def || 100, teamPct: 0, teamDays: 180, devBuy: 0, routes: [] };
  const PRESETS = {
    standard: { t: 'Standard', d: '1% fee, you keep 60%', feeBps: 100, share: 60, sniperBps: 2500, sniperSec: 60 },
    creator: { t: 'Creator max', d: '2% fee, you keep 80%', feeBps: 200, share: 80, sniperBps: 5000, sniperSec: 120 },
    community: { t: 'Low fee', d: '0.5% fee for traders', feeBps: 50, share: 60, sniperBps: 2500, sniperSec: 30 },
    custom: { t: 'Custom', d: 'Set every number' },
  };
  function launch() {
    const off = !PARTNER;
    app.innerHTML = `<div class="lgrid"><form id="lf" novalidate>
      <h1 style="margin-top:6px">Launch a coin</h1>
      ${off ? '<div class="warn" style="margin-bottom:14px">Launching opens soon. You can try every setting now; the Launch button switches on when the launchpad goes live.</div>' : ''}
      ${DEV ? '<div class="warn" style="margin-bottom:14px">You are on Solana\'s test network. Coins and SOL here have no value. <button type="button" class="btn quiet" id="air" style="padding:4px 10px;font-size:13px;margin-left:6px">Get 1 free test SOL</button></div>' : ''}
      <fieldset><legend>Your coin</legend>
        <div class="pic field"><label class="drop" for="img" id="drop">${F.image ? `<img src="${F.image}" alt="">` : 'Add a picture'}</label><input type="file" id="img" accept="image/png,image/jpeg,image/webp,image/gif" hidden>
          <div class="hint">Square works best. PNG, JPEG, WebP or GIF, up to 2 MB. Only use a picture you made or have the right to use.</div></div>
        <div class="two"><div class="field"><label for="nm">Name</label><input class="inp" id="nm" maxlength="32" value="${esc(F.name)}" placeholder="Bonk Hound"></div>
          <div class="field"><label for="sy">Ticker</label><input class="inp" id="sy" maxlength="10" value="${esc(F.symbol)}" placeholder="BONKH"></div></div>
        <div class="field"><label for="ds">Description</label><textarea class="inp" id="ds" maxlength="600" placeholder="What is it, and why should anyone care?">${esc(F.description)}</textarea></div>
        <div class="two"><div class="field"><label for="ws">Website</label><input class="inp" id="ws" value="${esc(F.website)}" placeholder="https://"></div><div class="field"><label for="xx">X</label><input class="inp" id="xx" value="${esc(F.x)}" placeholder="https://x.com/..."></div></div>
        <div class="field"><label for="tg">Telegram</label><input class="inp" id="tg" value="${esc(F.telegram)}" placeholder="https://t.me/..."></div>
      </fieldset>
      <fieldset><legend>Fees</legend>
        <div class="presets">${Object.entries(PRESETS).map(([k, p]) => `<button type="button" class="preset${F.preset === k ? ' on' : ''}" data-p="${k}"><b>${p.t}</b><span>${p.d}</span></button>`).join('')}</div>
        <div class="field"><label for="fee">Trading fee on every buy and sell</label><div class="range"><input type="range" id="fee" min="${(C.feeBps || {}).min || 25}" max="${(C.feeBps || {}).max || 200}" step="5" value="${F.feeBps}"><output id="feeo"></output></div><div class="hint">Higher earns you more per trade; lower is friendlier to traders.</div></div>
        <div class="field"><label for="sh">Your share of the fee, after Meteora's 20%</label><div class="range"><input type="range" id="sh" min="${(C.creatorShare || {}).min || 50}" max="${(C.creatorShare || {}).max || 80}" step="1" value="${F.share}"><output id="sho"></output></div><div class="hint">The rest goes to MemeCapes, and half of that buys $CAPES and burns it.</div></div>
        <div class="field"><label for="sn">Sniper fee at the start</label><div class="range"><input type="range" id="sn" min="0" max="${(C.sniperFee || {}).maxBps || 5000}" step="250" value="${F.sniperBps}"><output id="sno"></output></div>
          <div class="range" style="margin-top:6px"><input type="range" id="ss" min="10" max="${(C.sniperFee || {}).maxSeconds || 600}" step="10" value="${F.sniperSec}" aria-label="How long the sniper fee lasts"><output id="sso"></output></div>
          <div class="hint">Bots that buy in the first seconds pay this fee, and it falls smoothly to your normal fee. Your own first buy pays the normal fee.</div><svg id="decay" viewBox="0 0 300 74" style="width:100%;height:auto;max-height:110px;margin-top:6px" aria-hidden="true"></svg></div>
        <div class="field"><label>Your share goes to</label><div class="routes" id="routes"></div><button type="button" class="btn quiet" id="addr" style="padding:7px 12px;font-size:14px">Add a wallet to the split</button>
          <div class="hint">Split your fees with your team, a charity or a community wallet: up to 10 wallets. Whatever is left goes to you. Your split is published on the coin's page, and paid each time you claim.</div></div>
      </fieldset>
      <fieldset><legend>Graduation</legend>
        <div class="field"><label>When the coin graduates to a real pool</label><div class="chips">${(C.graduation || []).map(g => `<button type="button" class="chip${F.grad === g.id ? ' on' : ''}" data-g="${g.id}">${esc(g.name)}: about ${raiseFor(g.mcapSol).toFixed(0)} SOL raised</button>`).join('')}</div>
          <div class="hint">At graduation the coin moves to a Meteora pool. Its liquidity is locked forever: nobody, including you and MemeCapes, can pull it.</div></div>
        <div class="field"><label for="pf">Pool fee after graduation</label><div class="range"><input type="range" id="pf" min="${(C.postFeeBps || {}).min || 25}" max="${(C.postFeeBps || {}).max || 200}" step="5" value="${F.postBps}"><output id="pfo"></output></div><div class="hint">You keep earning your share of this fee from the locked pool, for as long as people trade.</div></div>
      </fieldset>
      <fieldset><legend>Team tokens and your first buy</legend>
        <div class="field"><label for="tm">Set aside for your team</label><div class="range"><input type="range" id="tm" min="0" max="${C.teamMaxPct || 10}" step="0.5" value="${F.teamPct}"><output id="tmo"></output></div>
          <div class="range" style="margin-top:6px"><input type="range" id="td" min="30" max="720" step="30" value="${F.teamDays}" aria-label="Unlock time"><output id="tdo"></output></div>
          <div class="hint">Team tokens are locked on-chain and unlock bit by bit after graduation, so buyers can see you can't dump them.</div></div>
        <div class="field"><label for="db">Your first buy (SOL)</label><input class="inp num" id="db" inputmode="decimal" value="${F.devBuy || ''}" placeholder="0"><div class="hint">Bought in the same transaction that creates the coin, so nobody can buy before you. It shows on the coin's page.</div></div>
      </fieldset>
    </form>
    <aside class="side"><div class="panel preview" id="pv"></div><div class="panel"><h3>Where each trade fee goes</h3><div id="fb"></div></div>
      <div class="panel"><div class="sum num" id="sum"></div><button class="btn gold" style="width:100%;margin-top:14px" id="launch" type="button" ${off ? 'disabled' : ''}>Launch ${F.symbol ? '$' + esc(F.symbol) : 'my coin'}</button><div class="err" id="lerr"></div>
        <p class="small mute" style="margin-top:10px">Your wallet asks you to approve two transactions together: one sets your coin's rules, one creates the coin${F.devBuy ? ' and makes your first buy' : ''}. Nothing happens unless you approve.</p></div></aside></div>`;
    const bind = (id, k, fmt, num) => { const el = $('#' + id); const o = $('#' + id + 'o'); const up = () => { F[k] = num ? +el.value : el.value; if (o) o.textContent = fmt ? fmt(F[k]) : F[k]; refresh(); }; el.oninput = () => { if (['fee', 'sh', 'sn', 'ss'].includes(id)) F.preset = 'custom', $$('.preset').forEach(b => b.classList.toggle('on', b.dataset.p === 'custom')); up(); }; up(); };
    ['nm:name', 'sy:symbol', 'ds:description', 'ws:website', 'xx:x', 'tg:telegram'].forEach(p => { const [id, k] = p.split(':'); $('#' + id).oninput = e => { F[k] = k === 'symbol' ? e.target.value.toUpperCase().replace(/[^A-Z0-9$]/g, '') : e.target.value; if (k === 'symbol') e.target.value = F[k]; refresh(); }; });
    bind('fee', 'feeBps', v => pct(v / 100), 1); bind('sh', 'share', v => v + '%', 1); bind('sn', 'sniperBps', v => v ? pct(v / 100) : 'Off', 1); bind('ss', 'sniperSec', v => v < 120 ? v + ' s' : (v / 60).toFixed(v % 60 ? 1 : 0) + ' min', 1);
    bind('pf', 'postBps', v => pct(v / 100), 1); bind('tm', 'teamPct', v => v ? v + '%' : 'None', 1); bind('td', 'teamDays', v => v < 60 ? v + ' days' : Math.round(v / 30) + ' months', 1);
    $('#db').oninput = e => { F.devBuy = Math.max(0, parseFloat(e.target.value.replace(',', '.')) || 0); refresh(); };
    $$('.preset').forEach(b => b.onclick = () => { F.preset = b.dataset.p; const p = PRESETS[F.preset]; if (p.feeBps) Object.assign(F, { feeBps: p.feeBps, share: p.share, sniperBps: p.sniperBps, sniperSec: p.sniperSec }); launch(); });
    $$('[data-g]').forEach(b => b.onclick = () => { F.grad = b.dataset.g; $$('[data-g]').forEach(x => x.classList.toggle('on', x === b)); refresh(); });
    $('#img').onchange = e => { const f = e.target.files[0]; if (!f) return; if (f.size > 2 * 1024 * 1024) return toast('That picture is over 2 MB.'); const r = new FileReader(); r.onload = () => { F.image = r.result; $('#drop').innerHTML = `<img src="${F.image}" alt="">`; refresh(); }; r.readAsDataURL(f); };
    const drawRoutes = () => {
      $('#routes').innerHTML = F.routes.map((r, i) => `<div class="rt"><input class="inp" data-ri="${i}" data-rk="to" value="${esc(r.to)}" placeholder="Wallet address" aria-label="Wallet address"><input class="inp num" data-ri="${i}" data-rk="pct" value="${r.pct || ''}" inputmode="numeric" placeholder="%" aria-label="Percent"><button type="button" class="btn quiet" data-rd="${i}" style="padding:0" aria-label="Remove">✕</button></div>`).join('');
      $$('[data-ri]').forEach(el => el.oninput = () => { const r = F.routes[+el.dataset.ri]; r[el.dataset.rk] = el.dataset.rk === 'pct' ? Math.max(0, Math.min(100, parseInt(el.value) || 0)) : el.value.trim(); refresh(); });
      $$('[data-rd]').forEach(el => el.onclick = () => { F.routes.splice(+el.dataset.rd, 1); drawRoutes(); refresh(); });
      $('#addr').disabled = F.routes.length >= 10;
    };
    $('#addr').onclick = () => { F.routes.push({ to: '', pct: 10 }); drawRoutes(); refresh(); };
    drawRoutes();
    $('#launch').onclick = doLaunch;
    if ($('#air')) $('#air').onclick = async () => { const b = $('#air'); try { const m = await needWallet(); b.disabled = true; b.textContent = 'Asking the test network…'; await LPC.airdrop(m.address); b.textContent = 'Got 1 test SOL'; } catch (e) { b.disabled = false; b.textContent = 'Get 1 free test SOL'; if (e.message !== 'closed') toast('The test network faucet said no (it limits how often). Try faucet.solana.com.'); } };
    refresh();
  }
  function refresh() {
    if (!$('#pv')) return;
    const g = (C.graduation || []).find(x => x.id === F.grad) || { mcapSol: 400 };
    $('#pv').innerHTML = `${stamp({ image: F.image, symbol: F.symbol || '?' }, 0)}<h3>${esc(F.name || 'Your coin')}</h3><div class="mute">${F.symbol ? '$' + esc(F.symbol) : ''}</div>`;
    $('#fb').innerHTML = feeBar({ baseBps: F.feeBps, creatorShare: F.share });
    // the sniper fee curve: exponential fall from the start fee to the normal fee
    const svg = $('#decay'); if (svg) {
      const st = Math.max(F.sniperBps, F.feeBps), en = F.feeBps, pts = [];
      for (let i = 0; i <= 60; i++) { const t = i / 60, v = st > en ? en + (st - en) * Math.pow(0.02, t) : en; pts.push([10 + t * 280, 60 - (v / Math.max(st, 1)) * 50]); }
      svg.innerHTML = `<polyline points="${pts.map(p => p.map(x => x.toFixed(1)).join(',')).join(' ')}" fill="none" stroke="#ff8a3d" stroke-width="2.5"/><line x1="10" y1="60" x2="290" y2="60" stroke="#4e3a22"/><text x="10" y="70" fill="#b89a6a" font-size="9">launch</text><text x="290" y="70" fill="#b89a6a" font-size="9" text-anchor="end">${F.sniperSec}s</text><text x="14" y="${(pts[0][1] - 3).toFixed(0)}" fill="#ff8a3d" font-size="10">${pct(st / 100)}</text><text x="290" y="${(pts[60][1] - 4).toFixed(0)}" fill="#ffd23f" font-size="10" text-anchor="end">${pct(en / 100)}</text>`;
      svg.style.opacity = F.sniperBps > F.feeBps ? 1 : .35;
    }
    const routed = F.routes.reduce((a, r) => a + (r.pct || 0), 0);
    const startUsd = (C.startMcapSol || 28) * solUsd;
    $('#sum').innerHTML = `<div><span>Supply</span><b>1,000,000,000</b></div><div><span>Starting market cap</span><b>${usd(startUsd)}</b></div><div><span>Graduates at</span><b>about ${raiseFor(g.mcapSol).toFixed(0)} SOL raised (${usd(g.mcapSol * solUsd)} market cap)</b></div>
      <div><span>You earn on each trade</span><b>${(F.feeBps / 100 * 0.8 * F.share / 100).toFixed(3)}%</b></div>${routed ? `<div><span>Of that, paid to your split</span><b>${routed}%</b></div>` : ''}
      <div><span>Team tokens</span><b>${F.teamPct ? F.teamPct + '%, locked' : 'None'}</b></div><div><span>Your first buy</span><b>${F.devBuy ? sol(F.devBuy) : 'None'}</b></div>
      <div><span>Launch cost</span><b>${C.creationFeeSol ? sol(C.creationFeeSol) + ' + ' : ''}about 0.03 SOL network rent</b></div>`;
    const b = $('#launch'); if (b && PARTNER) b.textContent = 'Launch ' + (F.symbol ? '$' + F.symbol : 'my coin');
  }
  function curveParams() {
    const g = (C.graduation || []).find(x => x.id === F.grad) || { mcapSol: 400 };
    const sniper = F.sniperBps > F.feeBps;
    const cliff = Math.min(30, Math.floor(F.teamDays / 4)), days = F.teamDays - cliff;   // locked for a month (or a quarter of the time), then unlocks a little every day
    const team = F.teamPct > 0 ? { totalLockedVestingAmount: Math.floor(SUPPLY * F.teamPct / 100), numberOfVestingPeriod: days, cliffUnlockAmount: 0, totalVestingDuration: days * 86400, cliffDurationFromMigrationTime: cliff * 86400 }
      : { totalLockedVestingAmount: 0, numberOfVestingPeriod: 0, cliffUnlockAmount: 0, totalVestingDuration: 0, cliffDurationFromMigrationTime: 0 };
    const creatorLp = F.share, partnerLp = 100 - F.share;    // graduated pool: all liquidity locked for good, its fees split like the curve's
    return dbc.buildCurveWithMarketCap({
      token: { tokenType: dbc.TokenType.SPLToken, tokenBaseDecimal: dbc.TokenDecimal.SIX, tokenQuoteDecimal: dbc.TokenDecimal.NINE, tokenAuthorityOption: dbc.TokenAuthorityOption.Immutable, totalTokenSupply: SUPPLY, leftover: 0 },
      fee: { baseFeeParams: { baseFeeMode: dbc.BaseFeeMode.FeeSchedulerExponential, feeSchedulerParam: sniper ? { startingFeeBps: F.sniperBps, endingFeeBps: F.feeBps, numberOfPeriod: Math.min(F.sniperSec, 120), totalDuration: F.sniperSec } : { startingFeeBps: F.feeBps, endingFeeBps: F.feeBps, numberOfPeriod: 0, totalDuration: 0 } },
        dynamicFeeEnabled: true, collectFeeMode: dbc.CollectFeeMode.QuoteToken, creatorTradingFeePercentage: F.share, poolCreationFee: C.creationFeeSol || 0, enableFirstSwapWithMinFee: true },
      migration: { migrationOption: dbc.MigrationOption.MET_DAMM_V2, migrationFeeOption: dbc.MigrationFeeOption.Customizable, migrationFee: { feePercentage: 0, creatorFeePercentage: 0 },
        migratedPoolFee: { collectFeeMode: dbc.MigratedCollectFeeMode.QuoteToken, dynamicFee: dbc.DammV2DynamicFeeMode.Enabled, poolFeeBps: F.postBps } },
      liquidityDistribution: { partnerLiquidityPercentage: 0, creatorLiquidityPercentage: 0, partnerPermanentLockedLiquidityPercentage: partnerLp, creatorPermanentLockedLiquidityPercentage: creatorLp },
      lockedVesting: team, activationType: dbc.ActivationType.Timestamp,
      initialMarketCap: C.startMcapSol || 28, migrationMarketCap: g.mcapSol,
    });
  }
  function checkForm() {
    if (F.name.trim().length < 2) return 'Give your coin a name.';
    if (!/^[A-Z0-9$]{2,10}$/.test(F.symbol)) return 'The ticker must be 2 to 10 letters or numbers.';
    if (!F.image) return 'Add a picture.';
    const tot = F.routes.reduce((a, r) => a + (r.pct || 0), 0);
    if (tot > 100) return 'Your split adds up to more than 100%.';
    for (const r of F.routes) { try { new web3.PublicKey(r.to); } catch (e) { return 'One of the wallets in your split is not a Solana address.'; } }
    return '';
  }
  async function doLaunch() {
    const err = $('#lerr'), b = $('#launch'); err.textContent = '';
    const bad = checkForm(); if (bad) { err.textContent = bad; return; }
    let m; try { m = await needWallet(); } catch (e) { return; }
    let cfgParams; try { cfgParams = curveParams(); } catch (e) { err.textContent = 'Those settings do not make a valid curve: ' + (e.message || e); return; }
    const st = strikeOverlay(); b.disabled = true;
    try {
      st.step('Saving your picture and details…');
      const plan = { routes: F.routes.filter(r => r.to && r.pct > 0).map(r => ({ to: r.to, pct: r.pct })), launchpad: 'memecapes' };
      const up = await api('/lp/upload', { name: F.name, symbol: F.symbol, description: F.description, website: F.website, x: F.x, telegram: F.telegram, image: F.image, plan });
      const cfgKp = web3.Keypair.generate(), mintKp = web3.Keypair.generate();
      st.step('Preparing the transactions…');
      const { createConfigTx, createPoolWithFirstBuyTx } = await LPC.dbc().partner.createConfigAndPoolWithFirstBuy({
        config: cfgKp.publicKey, feeClaimer: PK(PARTNER), leftoverReceiver: PK(PARTNER), payer: m.pubkey, quoteMint: L.spl.NATIVE_MINT, ...cfgParams,
        preCreatePoolParam: { baseMint: mintKp.publicKey, name: F.name.trim(), symbol: F.symbol, uri: up.uri, poolCreator: m.pubkey },
        firstBuyParam: F.devBuy > 0 ? { buyer: m.pubkey, buyAmount: new BN(Math.floor(F.devBuy * 1e9).toString()), minimumAmountOut: new BN(1), referralTokenAccount: null } : undefined,
      });
      const sigs = await LPC.sendAll([createConfigTx, createPoolWithFirstBuyTx], [[cfgKp], [mintKp]], (s, i) => st.step(s === 'wallet' ? 'Approve both transactions in your wallet…' : s === 'send' ? 'Sending ' + (i + 1) + ' of 2…' : 'Waiting for Solana to confirm…'));
      st.step('Listing your coin…');
      let coinRow = null; try { coinRow = (await api('/lp/register', { sig: sigs[1] })).coin; } catch (e) { console.warn(e); }
      st.done({ image: F.image, symbol: F.symbol }, mintKp.publicKey.toBase58());
      F.name = F.symbol = F.description = F.image = ''; F.routes = []; F.devBuy = 0;
    } catch (e) { st.close(); b.disabled = false; err.textContent = e.message === 'closed' ? '' : friendly(e); }
  }
  function strikeOverlay() {
    const d = document.createElement('div'); d.className = 'strike'; d.innerHTML = `<div class="flash"></div>${stamp({ image: F.image, symbol: F.symbol }, 0)}<h2>Striking $${esc(F.symbol)}</h2><div class="steps" id="stp">Starting…</div>`;
    document.body.appendChild(d);
    return { step: t => { $('#stp', d).textContent = t; }, close: () => d.remove(),
      done: (c, mint) => { d.classList.add('go'); $('h2', d).textContent = '$' + c.symbol + ' is live'; $('#stp', d).innerHTML = `<a class="btn gold" href="#/coin/${mint}">Go to your coin</a>`; $('a', d).onclick = () => d.remove(); } };
  }

  // ---- my coins
  async function mine() {
    const m = LPC.me();
    if (!m) { app.innerHTML = `<div class="empty" style="margin:30px 0"><p>Connect the wallet you launched with to see your coins and claim your fees.</p><button class="btn gold" id="cw" type="button">Connect wallet</button></div>`; $('#cw').onclick = () => pickWallet().catch(() => { }); return; }
    app.innerHTML = '<h1 style="margin-top:22px">My coins</h1><div id="grid" class="coins"><div class="empty" style="grid-column:1/-1">Loading…</div></div>';
    let coins = (await api('/lp/coins?creator=' + m.address)).coins;
    coins = await liveMany(coins);
    $('#grid').innerHTML = coins.length ? coins.map(c => card(c).replace('</a>', c.live && c.live.creatorFee > 0 ? `<div class="small" style="color:var(--gold)">${sol(c.live.creatorFee)} to claim</div></a>` : '</a>')).join('') : '<div class="empty" style="grid-column:1/-1">No coins launched from this wallet yet. <a href="#/launch">Launch one.</a></div>';
    if (PARTNER && m.address === PARTNER) app.insertAdjacentHTML('afterbegin', '<p style="margin-top:14px"><a class="btn line" href="#/desk">Open the MemeCapes fee desk</a></p>');
  }

  // ---- how it works
  function how() {
    app.innerHTML = `<div style="max-width:760px;padding:22px 0;font-family:var(--serif);font-size:17.5px">
      <h1>How the launchpad works</h1>
      <h2>Launching</h2><p>You pick a name, ticker and picture, then your fees. Your wallet approves two transactions: one stores your coin's rules on Solana, the other creates the coin and, if you want, makes your first buy in the same moment, so nobody can buy before you. There are always exactly 1,000,000,000 coins and nobody can make more.</p>
      <h2>The bonding curve</h2><p>Every coin starts on a bonding curve: the price rises as people buy and falls as they sell, and there is always someone to trade with. When enough SOL is raised, the coin graduates to a Meteora pool. All of its liquidity is locked there forever. Nobody, not you and not MemeCapes, can pull it.</p>
      <h2>Fees</h2><p>Each trade pays the fee you chose. Meteora, who wrote and runs the pool program, takes 20% of it. Of the rest, you choose how much you keep (${(C.creatorShare || {}).min || 50} to ${(C.creatorShare || {}).max || 80}%). MemeCapes keeps the remainder, and half of what MemeCapes earns buys $CAPES and burns it. Every burn is posted. After graduation you keep earning your share of the pool's fees from the locked liquidity.</p>
      <h2>Snipers</h2><p>Bots love to buy a new coin in its first second. Here, the first seconds or minutes cost them a high fee that falls smoothly to your normal fee. Those fees are shared the same way, so snipers pay you.</p>
      <h2>Splitting your fees</h2><p>Add up to 10 wallets and a share for each. When you claim, the same transaction pays each of them. Your split is shown on your coin's page so buyers can see it.</p>
      <h2>Team tokens</h2><p>If you set some of the supply aside for a team, it is locked on-chain and unlocks bit by bit after graduation. Buyers can check it, so they know you can't dump it on them.</p>
      <h2>Safety</h2><p>Anyone can launch, so anyone can launch a bad coin. "Verified" means the MemeCapes team looked at the coin and the people behind it; it is not a promise about its price. Use "Report this coin" for scams or stolen pictures, and we hide coins that break the rules. Most new coins lose most of their value. Only put in what you are happy to lose.</p>
      <p><a class="btn gold" href="#/launch">Launch a coin</a></p></div>`;
  }

  // ---- MemeCapes fee desk: claim the launchpad's fees (only the fee wallet can)
  async function desk() {
    const m = LPC.me();
    if (!m || m.address !== PARTNER) { app.innerHTML = '<div class="empty" style="margin:30px 0">Only the MemeCapes launchpad fee wallet can open this page.</div>'; return; }
    app.innerHTML = '<h1 style="margin-top:22px">MemeCapes fee desk</h1><div id="dk" class="panel">Loading…</div>';
    let coins = await liveMany((await api('/lp/coins?limit=200')).coins);
    const owed = coins.filter(c => c.live && c.live.partnerFee > 0), tot = owed.reduce((a, c) => a + c.live.partnerFee, 0);
    $('#dk').innerHTML = `<p>Ready to claim from ${owed.length} coins: <b class="num">${sol(tot)}</b>. Of that, ${C.burnShare || 50}% (${sol(tot * (C.burnShare || 50) / 100)}) is for buying and burning $CAPES.</p>
      <button class="btn gold" id="cl" type="button" ${owed.length ? '' : 'disabled'}>Claim all</button><div class="err" id="derr"></div>
      <p class="small mute" style="margin-top:12px">After claiming: buy $CAPES with the burn share and burn it from this wallet, then post the burn transaction.</p>`;
    $('#cl').onclick = async () => {
      const b = $('#cl'); b.disabled = true;
      try {
        const txs = [];
        for (let i = 0; i < owed.length; i += 3) {
          const t = new web3.Transaction();
          for (const c of owed.slice(i, i + 3)) t.add(...(await LPC.dbc().partner.claimPartnerTradingFee({ pool: PK(c.pool), feeClaimer: m.pubkey, payer: m.pubkey, maxBaseAmount: new BN(0), maxQuoteAmount: new BN(Math.floor(c.live.partnerFee * 1e9).toString()) })).instructions);
          txs.push(t);
        }
        await LPC.sendAll(txs, null, s => { b.textContent = s === 'wallet' ? 'Approve in your wallet…' : 'Confirming…'; });
        toast('Claimed.'); cache.clear(); desk();
      } catch (e) { $('#derr').textContent = friendly(e); b.disabled = false; b.textContent = 'Claim all'; }
    };
  }

  drawWallet();
  LPC.autoConnect().then(drawWallet);
  route();
})();
