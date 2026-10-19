// node server/test_crews.js : MemeSnake's autopilot crews with fake web answers
const fs = require('fs'), os = require('os'), path = require('path');
process.env.PIT_URL = 'https://pit.example';
const DATA = fs.mkdtempSync(path.join(os.tmpdir(), 'cr-'));
const MS = require('./memesnake')({ DATA });
let T = 1e12; const now = () => T;
const online = new Map([['a', {}], ['b', {}], ['c', {}]]);
let mode = 'normal', blocked = [];
const G = { status: () => ({ mode, blocked }) };
const answers = {
  'https://memecapes.com/': 200, 'https://memecapes.com/play.html': 200, 'https://memecapes.com/launch.html': 200, 'https://pit.example/': 200,
  'https://pit.example/api/battle/board': { configured: true, week: { status: 'running', entrants: 7 } },
  'https://pit.example/api/battle/boss': { configured: true, boss: { status: 'running', pnl: 8.64, beatenBy: 2, coin: 'WIF', trades: [{ ts: '2026-10-19T12:00:00Z', reason: 'Bought WIF with 25% of the stack: up +1.8% over the last 2 hours and still rising.' }] } },
  'https://pit.example/api/public/stats': { hatched: 0 },
  'https://pit.example/api/trending': { tokens: [{ symbol: 'MINTER', change24h: 9866.2 }, { symbol: 'mucron', change24h: 225 }, { symbol: 'CAT$ZN', change24h: -4.25 }] },
  'https://api.github.com/repos/Mrsnakehunter/Memecapes/commits?per_page=10': [{ sha: 'n1', commit: { message: 'Notes: x' } }, { sha: 's1', commit: { message: 'MemeSnake Live is connected: the page reads the live feed (feed.json as fallback)\n\nCo-Authored-By: x' } }],
};
global.fetch = async (u) => { const a = answers[u]; if (a === undefined) throw new Error('offline'); return { ok: a !== 500, status: typeof a === 'number' ? a : 200, json: async () => a }; };
const C = require('./crews')({ MS, online, G, now });
let pass = 0, fail = 0; const ok = (c, m) => { c ? pass++ : (fail++, console.log('FAIL', m)); };
const logOf = (crew) => MS.get().log.filter(e => e.agent === crew).map(e => e.text);
const crewSt = (part, crew) => MS.get().parts.find(p => p.id === part).crews.find(c => c.name === crew).status;
(async () => {
  for (const [part, crew, job] of C.plan) await C.run(part, crew, job);
  ok(MS.get().status === 'online' && MS.get().headline, 'page goes online with a headline');
  ok(/5 pages.*All loading/.test(logOf('QA Testers')[0]), 'QA all up: ' + logOf('QA Testers')[0]);
  ok(logOf('Community')[0] === '3 players are in MemeCapes right now.', 'community count');
  ok(/^Shipped: MemeSnake Live is connected: the page reads the live feed$/.test(logOf('Game Build')[0]), 'build skips Notes, trims: ' + logOf('Game Build')[0]);
  ok(logOf('Security Review')[0] === 'Shield up. All quiet.', 'security quiet');
  ok(/No coins hatched yet/.test(logOf('Launch Site')[0]), 'hatch');
  ok(logOf('Market Scouts')[0] === 'Top movers in the Pit today: MINTER +9866%, mucron +225%, CATZN -4.3%. Research only, not advice.', 'scouts: ' + logOf('Market Scouts')[0]);
  ok(logOf('Trading Bot Desk').includes('Weekly Agent Battle is trading: 7 agents entered this week. The Boss is at +8.6%, 2 beating it.'), 'battle: ' + logOf('Trading Bot Desk'));
  ok(logOf('Trading Bot Desk').some(t => t.startsWith('The Boss: Bought WIF with 25% of the stack')), 'boss move reported');
  ok(crewSt('memecapes', 'QA Testers') === 'done' && crewSt('memecapes', 'Game Build') === 'done', 'crews done');
  ok(MS.get().parts.find(p => p.id === 'memecapes').crews.length === 6, 'wing keeps all 6 crews');
  const n0 = MS.get().log.length;
  for (const [part, crew, job] of C.plan) await C.run(part, crew, job);
  ok(MS.get().log.length === n0, 'nothing new = no repeat entries');
  answers['https://pit.example/'] = 500;
  await C.run('memecapes', 'QA Testers', C.jobs.qa);
  ok(/Problem found: the Pit is not loading/.test(logOf('QA Testers')[0]) && crewSt('memecapes', 'QA Testers') === 'blocked', 'QA flags a down page');
  mode = 'shield'; await C.run('token', 'Security Review', C.jobs.security);
  ok(/shield is raised \(shield mode\)/.test(logOf('Security Review')[0]), 'security mode change');
  delete answers['https://pit.example/api/trending']; await C.run('trading', 'Market Scouts', C.jobs.scouts);
  ok(crewSt('trading', 'Market Scouts') === 'blocked', 'a failed check shows blocked');
  T += 7 * 3600e3; answers['https://pit.example/'] = 200; mode = 'normal';
  await C.run('memecapes', 'Community', C.jobs.community);
  ok(logOf('Community').length === 2, 'heartbeat after 6 h');
  // daily report: nothing before 8 pm New York, once after, never twice
  T = Date.parse('2026-10-19T18:00:00Z'); await C.jobs.report(); ok(!MS.get().log.some(e => /^Daily Snake Report/.test(e.text)), 'no report before 8 pm');
  T = Date.parse('2026-10-20T01:30:00Z'); await C.jobs.report();
  const rep = MS.get().log.filter(e => /^Daily Snake Report/.test(e.text));
  ok(rep.length === 1 && rep[0].part === 'hq' && rep[0].text.length <= 240 && /Boss is up 8\.6%/.test(rep[0].text) && /MINTER/.test(rep[0].text), 'report: ' + (rep[0] || {}).text);
  T += 3600e3; await C.jobs.report(); ok(MS.get().log.filter(e => /^Daily Snake Report/.test(e.text)).length === 1, 'one report a day');
  console.log(MS.get().log.find(e=>/^Daily/.test(e.text)).text); console.log(fail ? `${fail} failed, ${pass} passed` : `all ${pass} checks pass`); process.exit(fail ? 1 : 0);
})();
