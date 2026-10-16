'use strict';
// SnakePit (pit.memecapes.com), the trading app that pairs with the game. The game never talks to the Pit directly:
// this module fetches a player's snake and the Pit's public numbers through the game server, so the Pit's /api/snake
// needs no CORS for memecapes.com and one game full of players asks the Pit at most once a minute per wallet.
//   GET /pit/snake?wallet=<address>  -> { on, snake:{segments, realized_pnl_sol, wins, losses, streak}, rank, url }
//   GET /pit/stats                   -> { on, ...the Pit's /api/public/stats }
// Where the Pit lives: Render's PIT_URL wins, otherwise `pit:` in the site's config.js. Empty = off ({on:false}).
const fs = require('fs');
const path = require('path');

module.exports = function snakepit({ tooMany }) {
  const fromCfg = () => { try { const m = /\bpit:\s*"(https:\/\/[a-z0-9.-]+)"/.exec(fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8')); return m ? m[1] : ''; } catch (e) { return ''; } };
  const URL0 = (process.env.PIT_URL || fromCfg()).replace(/\/+$/, '');
  const OK_MS = +(process.env.PIT_CACHE_MS || 60000), BAD_MS = 60000, MAX = 5000;
  const cache = new Map();   // key -> { t, v }
  const isAddr = (s) => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(s);
  const num = (v, d) => { const n = +v; return Number.isFinite(n) ? n : d; };

  function remember(k, v, ms) { if (cache.size >= MAX) cache.delete(cache.keys().next().value); cache.set(k, { t: Date.now() + ms, v }); return v; }
  async function get(p) {
    const r = await fetch(URL0 + p, { headers: { Accept: 'application/json', 'User-Agent': 'memecapes-server' }, signal: AbortSignal.timeout(6000) });
    if (!r.ok) throw new Error('pit ' + r.status);
    return r.json();
  }
  // only the fields the game shows, each one checked, so a changed or hijacked Pit can't push anything odd into the game
  function snakeOf(j, wallet) {
    const s = (j && j.snake) || {};
    return { on: true, wallet, url: URL0 + '/s/' + wallet,
      snake: { segments: Math.max(1, Math.min(100000, Math.round(num(s.segments, 3)))), realized_pnl_sol: +num(s.realized_pnl_sol, 0).toFixed(4),
        wins: Math.max(0, Math.round(num(s.wins, 0))), losses: Math.max(0, Math.round(num(s.losses, 0))), streak: Math.round(num(s.streak, 0)) },
      rank: j && Number.isFinite(+j.rank) && +j.rank > 0 ? Math.round(+j.rank) : null };
  }
  function statsOf(j) {
    const c = j && j.capes, l = j && j.longest;
    return { on: true, url: URL0, snakes: Math.max(0, Math.round(num(j && j.snakes, 0))), hatched: Math.max(0, Math.round(num(j && j.hatched, 0))),
      longest: l ? { handle: String(l.handle || '').replace(/[^\w.\-]/g, '').slice(0, 24), segments: Math.max(0, Math.round(num(l.segments, 0))) } : null,
      capes: c ? { priceUsd: num(c.priceUsd, 0), change24h: num(c.change24h, 0), marketCap: c.marketCap == null ? null : num(c.marketCap, 0) } : null,
      recent: (Array.isArray(j && j.recent) ? j.recent : []).slice(0, 5).filter(r => r && isAddr(String(r.mint))).map(r => ({ symbol: String(r.symbol || '').replace(/[^\w]/g, '').slice(0, 12), mint: String(r.mint) })) };
  }
  async function cached(key, p, shape) {
    const c = cache.get(key); if (c && c.t > Date.now()) return c.v;
    try { return remember(key, shape(await get(p)), OK_MS); }
    catch (e) { return remember(key, c ? c.v : { on: true, down: true }, BAD_MS); }   // keep the last good answer while the Pit is unreachable
  }

  async function http(req, res, url, json, ip) {
    if (!url.pathname.startsWith('/pit/') || req.method !== 'GET') return false;
    if (!URL0) return json({ on: false });
    if (url.pathname === '/pit/stats') return json(await cached('stats', '/api/public/stats', statsOf));
    if (url.pathname === '/pit/snake') {
      const w = String(url.searchParams.get('wallet') || '');
      if (!isAddr(w)) return json({ error: 'That is not a Solana wallet address.' }, 400);
      if (!cache.has('snake:' + w) && tooMany && tooMany('pit' + ip)) return json({ error: 'Too many tries. Wait a few minutes.' }, 429);
      return json(await cached('snake:' + w, '/api/snake?wallet=' + encodeURIComponent(w), (j) => snakeOf(j, w)));
    }
    return false;
  }
  return { http, url: URL0, _cache: cache };
};
