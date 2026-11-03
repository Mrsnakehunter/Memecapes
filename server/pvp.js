// PvP for World 2: players can fight each other outside the safe zones (towns). The server keeps every fight honest:
// it checks both players are in the PvP world, close enough for the attack style, outside a safe zone, within the
// level range, not hitting faster than the attack speed, and caps the damage at what that player's saved levels allow.
// The server also keeps each fighter's PvP hitpoints, so a modified client can't ignore hits.
// A PvP death (Albert, Nov 3: "players need to lose all items"): the server empties the loser's bag, worn gear and
// Meme Coins into a loot pile where they fell. Untradeable things (capes, skins, pets, clues, lamps, the level-80 sets)
// stay with the loser, because they can never change hands. The killer has the pile to themselves for LOOT_OWN ms, then
// anyone in the PvP world may take from it until LOOT_END ms, then it is gone. Everything happens in the server's copy
// of the saves (like a trade), so a modified game can't keep its items.
const fs = require('fs'), path = require('path');

module.exports = function ({ db, now, say, online, loadSave, bcastWorld, setSave, notrade, BAG }) {
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

  const LOOT_OWN = +process.env.PVP_LOOT_OWN || 60e3, LOOT_END = +process.env.PVP_LOOT_END || 120e3;
  const KEEP = k => notrade(k) || /^(st|ra|ma|bw|arm|sw)80$/.test(k);
  const PILES = new Map(); let pileN = 0;
  const pubPile = p => ({ id: p.id, x: p.x, y: p.y, n: p.items.length + (p.coins > 0 ? 1 : 0), from: p.from, own: p.owner, open: now() - p.t > LOOT_OWN });
  function dropAll(o, killer) {   // -> what the loser keeps, after saving; null if there is no server copy yet
    const L = loadSave(o.uid); if (!L.st || !L.u) return null;
    const st = L.st, items = [], keep = [];
    for (const k of st.inv || []) (KEEP(k) ? keep : items).push(k);
    const eq = {}; for (const [sl, k] of Object.entries(st.eq || {})) { if (!k) continue; if (KEEP(k)) eq[sl] = k; else items.push(k); }
    const coins = Math.max(0, Math.floor(+st.coins || 0));
    st.inv = keep; st.eq = eq; st.coins = 0;
    const rev = L.u.rev + 1; setSave(JSON.stringify(st), rev, now(), L.u.id);
    if (items.length || coins) {
      const p = { id: ++pileN, x: Math.round(o.pos.x), y: Math.round(o.pos.y), items, coins, owner: killer.uid, ownerName: killer.name, from: o.name, t: now() };
      PILES.set(p.id, p); bcastWorld(PVP_WORLD, { t: 'pvpPile', ...pubPile(p) }, null);
    }
    return { inv: st.inv, eq: st.eq, coins: 0, rev, lost: items.length + (coins ? 1 : 0) };
  }
  setInterval(() => {
    for (const p of PILES.values()) {
      if (now() - p.t > LOOT_END) { PILES.delete(p.id); bcastWorld(PVP_WORLD, { t: 'pvpPileGone', id: p.id }, null); }
      else if (!p.opened && now() - p.t > LOOT_OWN) { p.opened = 1; bcastWorld(PVP_WORLD, { t: 'pvpPile', ...pubPile(p) }, null); }
    }
  }, 2e3).unref?.();

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
        const kept = dropAll(o, c);
        o.send({ t: 'pvpDead', by: c.name, ...(kept || {}) });
        c.send({ t: 'pvpWin', name: o.name, loot: kept ? kept.lost : 0 });
        bcastWorld(PVP_WORLD, { t: 'notice', text: c.name + ' defeated ' + o.name + ' in PvP.' });
      }
    },
    pvpEat(c, m) {   // food eaten mid-fight: the game's own heal, at most one bite per 1.5 s
      if (!c.uid || !c.pv) return;
      if (now() - c.pv.eat < 1500) return;
      c.pv.eat = now(); c.pv.hp = Math.min(c.pv.max, c.pv.hp + Math.max(0, Math.min(25, m.h | 0)));
      c.send({ t: 'pvpHp', hp: c.pv.hp, max: c.pv.max });
    },
    pvpPiles(c) { if (c.world === PVP_WORLD) for (const p of PILES.values()) c.send({ t: 'pvpPile', ...pubPile(p) }); },
    pvpLoot(c, m) {
      if (!c.uid || c.world !== PVP_WORLD || !c.pos) return;
      const p = PILES.get(+m.id); if (!p) return c.send({ t: 'pvpPileGone', id: +m.id });
      if (Math.max(Math.abs(c.pos.x - p.x), Math.abs(c.pos.y - p.y)) > 1.6) return say(c, 'Get closer to the loot.', '#c00');
      if (p.owner !== c.uid && now() - p.t <= LOOT_OWN) return say(c, 'This loot belongs to ' + p.ownerName + ' for a little longer.', '#c00');
      const L = loadSave(c.uid); if (!L.st) return say(c, 'Your progress has not reached the server yet. Try again in a few seconds.', '#c00');
      const st = L.st; st.inv = st.inv || [];
      const got = [];
      if (p.coins > 0) { st.coins = (+st.coins || 0) + p.coins; got.push(p.coins + ' Meme Coins'); p.coins = 0; }
      let room = BAG - st.inv.length - ((+st.coins || 0) > 0 ? 1 : 0);
      while (room > 0 && p.items.length) { st.inv.push(p.items.shift()); room--; got.push(1); }
      if (!got.length) return say(c, 'Your bag is full.', '#c00');
      const rev = L.u.rev + 1; setSave(JSON.stringify(st), rev, now(), L.u.id);
      c.send({ t: 'lootGot', inv: st.inv, coins: st.coins, rev, n: got.length, left: p.items.length });
      if (!p.items.length && !p.coins) { PILES.delete(p.id); bcastWorld(PVP_WORLD, { t: 'pvpPileGone', id: p.id }, null); }
      else bcastWorld(PVP_WORLD, { t: 'pvpPile', ...pubPile(p) }, null);
    },
    pvpTop(c) { c.send({ t: 'pvpTop', list: Q.top.all(), me: c.uid ? (Q.get.get(c.uid) || { kills: 0, deaths: 0 }) : null }); },
  };
  return { H, isSafe, safe: () => SAFE, cap, PILES };
};
