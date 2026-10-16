'use strict';
// SnakePit proxy: shapes answers, caches, survives a dead Pit, refuses bad wallets. Run: node server/test_pit.js
const http = require('http'); const assert = require('assert');
let hits = 0, mode = 'ok';
const pit = http.createServer((req, res) => {
  hits++;
  if (mode === 'down') { res.writeHead(500); return res.end('x'); }
  if (req.url.startsWith('/api/snake')) return res.end(JSON.stringify({ snake: { segments: 17.4, realized_pnl_sol: 0.7234567, wins: 9, losses: 3, streak: '2', evil: '<script>' }, rank: '4' }));
  if (req.url === '/api/public/stats') return res.end(JSON.stringify({ snakes: 412, hatched: 37, longest: { handle: 'mr<b>snake', segments: 118 }, capes: { priceUsd: 0.04, change24h: 18.2, marketCap: 4120000 }, recent: [{ symbol: 'VIPER!', mint: '7Ue4Sk6r2T1ZPwqHj6cB7bLwjZ9cXrYDeLRx5dTuX7qN' }, { symbol: 'BAD', mint: 'not-a-mint' }] }));
  res.writeHead(404); res.end();
});
pit.listen(0, async () => {
  process.env.PIT_URL = 'http://127.0.0.1:' + pit.address().port + '/';
  process.env.PIT_CACHE_MS = '300';
  const P = require('./snakepit')({ tooMany: () => false });
  const call = async (path) => { let out; const url = new URL(path, 'http://x'); const json = (o, s) => { out = { s: s || 200, o }; }; const r = await P.http({ method: 'GET' }, {}, url, json, '1.2.3.4'); return r === false ? false : out; };
  const W = '7Ue4Sk6r2T1ZPwqHj6cB7bLwjZ9cXrYDeLRx5dTuX7qN';
  let r = await call('/pit/snake?wallet=' + W);
  assert.strictEqual(r.s, 200); assert.strictEqual(r.o.on, true); assert.strictEqual(r.o.snake.segments, 17); assert.strictEqual(r.o.rank, 4); assert.strictEqual(r.o.snake.streak, 2);
  assert.ok(!('evil' in r.o.snake)); assert.ok(r.o.url.endsWith('/s/' + W)); assert.strictEqual(r.o.snake.realized_pnl_sol, 0.7235);
  const h1 = hits; await call('/pit/snake?wallet=' + W); assert.strictEqual(hits, h1, 'second call is cached');
  r = await call('/pit/snake?wallet=abc'); assert.strictEqual(r.s, 400);
  r = await call('/pit/stats'); assert.strictEqual(r.o.snakes, 412); assert.strictEqual(r.o.longest.handle, 'mrbsnake'); assert.strictEqual(r.o.recent.length, 1); assert.strictEqual(r.o.recent[0].symbol, 'VIPER');
  mode = 'down'; await new Promise(r => setTimeout(r, 350));
  r = await call('/pit/snake?wallet=' + W); assert.strictEqual(r.o.snake.segments, 17, 'last good answer kept while the Pit is down');
  const W2 = '3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg';
  r = await call('/pit/snake?wallet=' + W2); assert.strictEqual(r.o.down, true, 'unknown wallet while down = down flag');
  assert.strictEqual(await call('/other'), false);
  // off when nothing is configured
  delete require.cache[require.resolve('./snakepit')]; process.env.PIT_URL = ''; const P2 = require('./snakepit')({});
  if (!P2.url) { let out; await P2.http({ method: 'GET' }, {}, new URL('/pit/stats', 'http://x'), (o) => { out = o; }, ''); assert.strictEqual(out.on, false); }
  console.log('test_pit: 12 checks passed'); pit.close();
});
