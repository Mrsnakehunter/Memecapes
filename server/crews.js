// MemeSnake's crews on autopilot: small free programs (no AI model, no paid service) that do real checks on a timer
// and report to the MemeSnake Live page (memecapes.com/memesnake) through the feed in memesnake.js.
// Every report is real data from this server, the website, the Pit or GitHub. Nothing here trades, posts on social
// media, or touches a wallet. CREWS=0 on Render switches them all off.
//
//   QA Testers        (MemeCapes)  are the website, the game, the launch page and the Pit up?
//   Community         (MemeCapes)  how many real players are online (bots are drawn in the browser, never counted)
//   Game Build        (MemeCapes)  what was just shipped (new commits on the public repo)
//   Security Review   (Token Mint) the shield's mode and whether it turned anyone away
//   Launch Site       (Token Mint) coins hatched in the Pit
//   Market Scouts     (Trading)    the Pit's top movers right now (research only)
//   Trading Bot Desk  (Trading)    the Weekly Agent Battle: agents entered this week

const fs = require('fs'), path = require('path');

module.exports = function crews({ MS, online, G, now }) {
  if (process.env.CREWS === '0') return { off: true };
  const SITE = 'https://memecapes.com';
  const PIT = (process.env.PIT_URL || (() => { try { return (/pit:\s*"([^"]*)"/.exec(fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8')) || [])[1] || ''; } catch (e) { return ''; } })()).replace(/\/+$/, '');
  const REPO = 'Mrsnakehunter/Memecapes';
  const HEART = 6 * 3600e3;            // a crew with nothing new still reports in this often
  const last = new Map();              // crew -> { key, at }

  async function get(url, ms = 12000) {
    const r = await fetch(url, { signal: AbortSignal.timeout(ms), headers: { 'User-Agent': 'MemeSnake-crews' }, redirect: 'follow' });
    return r;
  }
  async function getJson(url) { const r = await get(url); if (!r.ok) throw new Error(String(r.status)); return r.json(); }

  // set one crew's status (the whole wing is sent, as the feed expects) and optionally add a log line
  function report(part, crew, status, text, key) {
    const cur = (MS.get().parts || []).find(p => p.id === part);
    if (!cur) return;
    const crews = cur.crews.map(c => c.name === crew ? { ...c, status } : c);
    const busy = crews.some(c => c.status === 'working' || c.status === 'blocked');
    const upd = { parts: [{ id: part, status: crews.some(c => c.status === 'blocked') ? 'blocked' : busy ? 'working' : 'done', task: cur.task, crews }] };
    const f = MS.get();
    if (f.status !== 'online') upd.status = 'online';
    if (!f.headline) upd.headline = 'Crews on autopilot: checking the site, security, the market and new builds.';
    if (text) {
      const k = key || text, l = last.get(crew);
      if (!l || l.key !== k || now() - l.at > HEART) { upd.log = [{ part, agent: crew, text }]; last.set(crew, { key: k, at: now() }); }
    }
    MS.apply(upd);
  }

  async function run(part, crew, job) {
    report(part, crew, 'working');
    try {
      const r = await job();
      if (r) report(part, crew, r.status || 'done', r.text, r.key);
      else report(part, crew, 'done');
    } catch (e) {
      report(part, crew, 'blocked', 'Could not finish its check this round. It tries again soon.', 'err');
    }
  }

  const jobs = {
    async qa() {
      const pages = [['the website', SITE + '/'], ['the game', SITE + '/play.html'], ['the launch page', SITE + '/launch.html']];
      if (PIT) pages.push(['the Pit', PIT + '/'], ['the Battle board', PIT + '/api/battle/board']);
      const down = [];
      for (const [name, url] of pages) { try { const r = await get(url); if (!r.ok) down.push(name); } catch (e) { down.push(name); } }
      if (down.length) return { status: 'blocked', text: 'Problem found: ' + down.join(', ') + (down.length > 1 ? ' are' : ' is') + " not loading. Flagged for Mr Snake.", key: 'down:' + down.join() };
      return { text: 'Checked ' + pages.length + ' pages: ' + pages.map(p => p[0]).join(', ') + '. All loading.', key: 'up' };
    },
    async community() {
      const n = online.size;
      if (!n) return null;
      const band = n < 5 ? n : n < 20 ? Math.floor(n / 5) * 5 : Math.floor(n / 10) * 10;
      return { text: n === 1 ? '1 player is in MemeCapes right now.' : n + ' players are in MemeCapes right now.', key: 'n' + band };
    },
    async build() {
      const list = await getJson('https://api.github.com/repos/' + REPO + '/commits?per_page=10');
      const ships = list.map(c => ({ sha: c.sha, msg: String(c.commit.message || '').split('\n')[0] }))
        .filter(c => !/^(notes|merge|revert)\b/i.test(c.msg));
      if (!ships.length) return null;
      const top = ships[0], seen = last.get('Game Build');
      if (seen && seen.key === top.sha) return null;
      const msg = top.msg.replace(/\s*\(.*?\)\s*/g, ' ').replace(/\s+/g, ' ').trim();
      return { text: 'Shipped: ' + (msg.length > 200 ? msg.slice(0, 197) + '…' : msg), key: top.sha };
    },
    async security() {
      const s = G.status();
      const blocked = (s.blocked || []).length;
      if (s.mode !== 'normal') return { status: 'working', text: 'The shield is raised (' + s.mode + ' mode). Watching closely.', key: 'mode:' + s.mode };
      return { text: blocked ? 'Shield up. Turned away suspicious traffic; everything else is running normally.' : 'Shield up. All quiet.', key: blocked ? 'busy' : 'quiet' };
    },
    async hatch() {
      if (!PIT) return null;
      const j = await getJson(PIT + '/api/public/stats');
      const h = Number(j.hatched) || 0;
      return { text: h ? (h === 1 ? '1 coin has hatched in the Pit so far.' : h + ' coins have hatched in the Pit so far.') : 'Launch site is open in the Pit. No coins hatched yet.', key: 'h' + h };
    },
    async scouts() {
      if (!PIT) return null;
      const j = await getJson(PIT + '/api/trending');
      const t = (j.tokens || []).filter(x => x && x.symbol && Number.isFinite(x.change24h)).slice(0, 3);
      if (!t.length) return null;
      const pct = v => (v >= 0 ? '+' : '') + (Math.abs(v) >= 100 ? Math.round(v) : v.toFixed(1)) + '%';
      return { text: 'Top movers in the Pit today: ' + t.map(x => String(x.symbol).replace(/[^A-Za-z0-9]/g, '').slice(0, 12) + ' ' + pct(x.change24h)).join(', ') + '. Research only, not advice.', key: t.map(x => x.symbol).join() };
    },
    async battle() {
      if (!PIT) return null;
      const j = await getJson(PIT + '/api/battle/board');
      if (!j.configured || !j.week) return null;
      const n = Number(j.week.entrants) || 0, st = j.week.status;
      const what = st === 'open' ? 'signing up' : st === 'running' ? 'trading' : 'finished';
      return { text: 'Weekly Agent Battle is ' + what + ': ' + (n === 1 ? '1 agent' : n + ' agents') + ' entered this week.', key: st + n };
    },
  };

  const plan = [
    ['memecapes', 'QA Testers', jobs.qa, 30],
    ['memecapes', 'Community', jobs.community, 60],
    ['memecapes', 'Game Build', jobs.build, 60],
    ['token', 'Security Review', jobs.security, 60],
    ['token', 'Launch Site', jobs.hatch, 120],
    ['trading', 'Market Scouts', jobs.scouts, 120],
    ['trading', 'Trading Bot Desk', jobs.battle, 120],
  ];
  plan.forEach(([part, crew, job, mins], i) => {
    setTimeout(() => { run(part, crew, job); setInterval(() => run(part, crew, job), mins * 60e3); }, 60e3 + i * 20e3);
  });
  return { jobs, run, plan };
};
