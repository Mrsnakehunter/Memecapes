// PvP for World 2: players can fight each other outside the safe zones (towns). The server keeps every fight honest:
// it checks both players are in the PvP world, close enough for the attack style, outside a safe zone, within the
// level range, not hitting faster than the attack speed, and caps the damage at what that player's saved levels allow.
// The server also keeps each fighter's PvP hitpoints, so a modified client can't ignore hits.
// v1: a PvP death sends the loser back to town with full hitpoints; nothing is dropped (kills and deaths are counted).
const fs = require('fs'), path = require('path');

module.exports = function ({ db, now, say, online, loadSave, bcastWorld }) {
  db.exec(`CREATE TABLE IF NOT EXISTS pvp (uid INTEGER PRIMARY KEY, kills INTEGER DEFAULT 0, deaths INTEGER DEFAULT 0, last INTEGER)`);
  const Q = {
    get: db.prepare('SELECT kills, deaths FROM pvp WHERE uid=?'),
    kill: db.prepare('INSERT INTO pvp(uid,kills,last) VALUES(?,1,?) ON CONFLICT(uid) DO UPDATE SET kills=kills+1,last=excluded.last'),
    death: db.prepare('INSERT INTO pvp(uid,deaths,last) VALUES(?,1,?) ON CONFLICT(uid) DO UPDATE SET deaths=deaths+1,last=excluded.last'),
    top: db.prepare('SELECT p.kills, p.deaths, u.name FROM pvp p JOIN users u ON u.id=p.uid WHERE p.kills>0 ORDER BY p.kills DESC LIMIT 10'),
  };
  // safe zones: town circles exported from the game build (tools/dev/dump_towns.py); none known = nowhere is PvP
  let SAFE = [];
  try { SAFE = JSON.parse(fs.readFileSync(path.join(__dirname, 'towns.json'), 'utf8')); } catch (e) { console.error('pvp: no towns.json, PvP is off'); }
  const isSafe = p => !SAFE.length || SAFE.some(t => (p.x - t.x) ** 2 + (p.y - t.y) ** 2 <= t.r * t.r);
  const PVP_WORLD = 2, LEVEL_GAP = 15, REACH = { at: 1.6, rg: 8.5, mg: 9.5 }, SPEED = { at: 2200, rg: 2200, mg: 2800 };

  const XT = [0]; { const K = 2e7 / (99 * Math.pow(1.095, 99)); for (let l = 2; l <= 100; l++) XT.push(Math.round(K * (l - 1) * Math.pow(1.095, l - 1))); XT[99] = 2e7; }
  const lvl = x => { let l = 1; while (l < 100 && x >= XT[l]) l++; return l; };
  function stats(uid) {
    const { st } = loadSave(uid); const xp = (st && st.xp) || {};
    const L = k => lvl(+xp[k] || 0);
    const cb = Math.max(Math.floor(.28 * (L('def') + L('hp')) + .34 * (L('at') + L('str')) + .1 * L('pr') + .08 * L('ag')),
      Math.floor(.28 * (L('def') + L('hp')) + .51 * L('rg')), Math.floor(.28 * (L('def') + L('hp')) + .51 * L('mg')));
    return { hp: Math.max(10, L('hp')), cb, max: { at: L('str'), rg: L('rg'), mg: L('mg') } };
  }
  // the most a hit can be at this level with the best gear that level can wear (+2 slack): same shape as the game's max hit
  const cap = l => Math.floor(.5 + (l + 11) * (64 + 20 + 1.2 * l) / 640) + 2;
  const fighter = c => {
    if (!c.pv || now() - c.pv.t > 120e3) { const s = stats(c.uid); c.pv = { hp: s.hp, max: s.hp, cb: s.cb, lv: s.max, t: now(), last: 0, eat: 0, hitBy: new Map() }; }
    return c.pv;
  };
  // hitpoints come back slowly between fights (1 every 6 s)
  setInterval(() => { for (const c of online.values()) if (c.pv && c.pv.hp < c.pv.max && now() - c.pv.t > 6e3) { c.pv.hp++; } }, 6e3);

  const H = {
    pvpHit(c, m) {
      if (!c.uid || c.world !== PVP_WORLD) return;
      const o = online.get(+m.id); const s = REACH[m.s] ? m.s : 'at';
      if (!o || o === c || o.world !== PVP_WORLD || !c.pos || !o.pos) return;
      const why = (() => {
        if (isSafe(c.pos)) return 'You are in a safe zone. Leave town to fight players.';
        if (isSafe(o.pos)) return o.name + ' is in a safe zone.';
        const d = Math.max(Math.abs(c.pos.x - o.pos.x), Math.abs(c.pos.y - o.pos.y));
        if (d > REACH[s]) return 'Too far away.';
        const A = fighter(c), B = fighter(o);
        if (Math.abs(A.cb - B.cb) > LEVEL_GAP) return 'Your combat levels are too far apart (' + A.cb + ' and ' + B.cb + '). PvP is within ' + LEVEL_GAP + ' levels.';
        if (now() - A.last < SPEED[s] - 250) return 'busy';
        return '';
      })();
      if (why) { if (why !== 'busy') say(c, why, '#c00'); return c.send({ t: 'pvpNo', id: o.uid }); }
      const A = c.pv, B = o.pv;
      const dmg = Math.max(0, Math.min(cap(A.lv[s] || 1), Math.floor(+m.d || 0), B.hp));
      A.last = now(); A.t = now(); B.t = now(); B.hp -= dmg; B.hitBy.set(c.uid, now());
      o.send({ t: 'pvpHit', id: c.uid, name: c.name, d: dmg, s, hp: B.hp, max: B.max });
      c.send({ t: 'pvpAck', id: o.uid, d: dmg, hp: B.hp, max: B.max });
      bcastWorld(PVP_WORLD, { t: 'pvpFx', a: c.uid, b: o.uid, d: dmg, s }, null);
      if (B.hp <= 0) {
        const t = now(); Q.kill.run(c.uid, t); Q.death.run(o.uid, t);
        o.pv = null; c.pv.t = t;
        o.send({ t: 'pvpDead', by: c.name });
        c.send({ t: 'pvpWin', name: o.name });
        bcastWorld(PVP_WORLD, { t: 'notice', text: c.name + ' defeated ' + o.name + ' in PvP.' });
      }
    },
    pvpEat(c, m) {   // food eaten mid-fight: the game's own heal, at most one bite per 1.5 s
      if (!c.uid || !c.pv) return;
      if (now() - c.pv.eat < 1500) return;
      c.pv.eat = now(); c.pv.hp = Math.min(c.pv.max, c.pv.hp + Math.max(0, Math.min(25, m.h | 0)));
      c.send({ t: 'pvpHp', hp: c.pv.hp, max: c.pv.max });
    },
    pvpTop(c) { c.send({ t: 'pvpTop', list: Q.top.all(), me: c.uid ? (Q.get.get(c.uid) || { kills: 0, deaths: 0 }) : null }); },
  };
  return { H, isSafe, safe: () => SAFE, cap };
};
