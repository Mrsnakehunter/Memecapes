'use strict';
// Friends and private messages.
//
// A player adds another by name. The other side gets a request (in game at once, or at their next sign-in) and
// accepts or declines; adding someone who already asked you accepts. Friends see each other come online and go
// offline, and can send private messages: delivered at once when the other is online, otherwise kept (the last
// KEEP per pair, for DAYS days) and shown at their next sign-in. Messages go through the same word filter and
// rate limit as public chat; ignoring someone also drops their messages and requests; a blocked word is never sent.
// Admin: `/pmlog <name>` is on purpose NOT here: private messages are private. Reports still attach recent chat.
module.exports = function friends({ db, now, say, online, cleanChat, findOnline, byName }) {
  const KEEP = 200, DAYS = 30, MAX_FRIENDS = 200;
  db.exec(`CREATE TABLE IF NOT EXISTS friends(uid INT, fid INT, t INT, ok INT DEFAULT 0, PRIMARY KEY(uid,fid));
    CREATE TABLE IF NOT EXISTS pms(id INTEGER PRIMARY KEY, t INT, f INT, u INT, text TEXT, seen INT DEFAULT 0);
    CREATE INDEX IF NOT EXISTS pms_u ON pms(u, seen);`);
  const Q = {
    get: db.prepare('SELECT * FROM friends WHERE uid=? AND fid=?'),
    put: db.prepare('INSERT OR REPLACE INTO friends(uid,fid,t,ok) VALUES(?,?,?,?)'),
    del: db.prepare('DELETE FROM friends WHERE (uid=? AND fid=?) OR (uid=? AND fid=?)'),
    mine: db.prepare('SELECT f.fid id, f.ok, u.name, u.last FROM friends f JOIN users u ON u.id=f.fid WHERE f.uid=? ORDER BY u.name COLLATE NOCASE'),
    reqs: db.prepare('SELECT f.uid id, u.name, f.t FROM friends f JOIN users u ON u.id=f.uid WHERE f.fid=? AND f.ok=0 AND NOT EXISTS (SELECT 1 FROM friends g WHERE g.uid=f.fid AND g.fid=f.uid) ORDER BY f.t DESC'),
    count: db.prepare('SELECT COUNT(*) n FROM friends WHERE uid=?'),
    pm: db.prepare('INSERT INTO pms(t,f,u,text,seen) VALUES(?,?,?,?,?)'),
    unread: db.prepare('SELECT p.id,p.t,p.f,u.name,p.text FROM pms p JOIN users u ON u.id=p.f WHERE p.u=? AND p.seen=0 ORDER BY p.id'),
    markSeen: db.prepare('UPDATE pms SET seen=1 WHERE u=? AND seen=0'),
    hist: db.prepare('SELECT p.t,p.f,p.text FROM pms p WHERE (p.f=? AND p.u=?) OR (p.f=? AND p.u=?) ORDER BY p.id DESC LIMIT 60'),
    trimPair: db.prepare(`DELETE FROM pms WHERE ((f=? AND u=?) OR (f=? AND u=?)) AND id NOT IN
      (SELECT id FROM pms WHERE ((f=? AND u=?) OR (f=? AND u=?)) ORDER BY id DESC LIMIT ${KEEP})`),
    trimOld: db.prepare('DELETE FROM pms WHERE t<?'),
  };
  const isFriend = (a, b) => { const r = Q.get.get(a, b), s = Q.get.get(b, a); return !!(r && s); };   // both rows = accepted
  const nameOf = (uid) => { const u = byName.id(uid); return u ? u.name : ''; };

  function listFor(c) {
    const rows = Q.mine.all(c.uid), out = [];
    for (const r of rows) {
      const back = Q.get.get(r.id, c.uid);
      const o = online.get(r.id);
      out.push({ name: r.name, ok: back ? 1 : 0, on: o ? 1 : 0, last: back ? (o ? 0 : r.last) : 0 });   // ok 0 = I asked, still waiting
    }
    return out;
  }
  function sendList(c) { if (c && c.uid) c.send({ t: 'friends', list: listFor(c), reqs: Q.reqs.all(c.uid).map(r => r.name) }); }
  function tellFriends(c, on) {
    for (const r of Q.mine.all(c.uid)) { const o = online.get(r.id); if (o && isFriend(c.uid, r.id)) o.send({ t: 'fon', name: c.name, on: on ? 1 : 0 }); }
  }

  const H = {
    friends(c) { if (c.uid) sendList(c); },
    friendAdd(c, m) {
      if (!c.uid) return;
      const name = String(m.name || '').replace(/[^A-Za-z0-9_]/g, '').slice(0, 12), u = name && byName.name(name);
      if (!u) return say(c, 'No player called ' + (name || 'that') + '.', '#c00');
      if (u.id === c.uid) return say(c, 'That is you.', '#c00');
      if (isFriend(c.uid, u.id)) return say(c, u.name + ' is already your friend.', '#a60');
      if (Q.get.get(c.uid, u.id)) return say(c, 'You already asked ' + u.name + '. Waiting for them.', '#a60');
      if (Q.count.get(c.uid).n >= MAX_FRIENDS) return say(c, 'Your friends list is full.', '#c00');
      const o = online.get(u.id);
      if (o && o.ignore.has(c.uid)) return say(c, 'Friend request sent to ' + u.name + '.', '#0a0');   // ignored: they never see it, you never know
      Q.put.run(c.uid, u.id, now(), 0);
      if (Q.get.get(u.id, c.uid)) {   // they asked first: that is an accept
        say(c, 'You and ' + u.name + ' are friends now.', '#0a0'); if (o) say(o, c.name + ' accepted your friend request.', '#0a0');
        sendList(c); sendList(o); if (o) { o.send({ t: 'fon', name: c.name, on: 1 }); c.send({ t: 'fon', name: u.name, on: 1 }); }
        return;
      }
      say(c, 'Friend request sent to ' + u.name + '.', '#0a0'); sendList(c);
      if (o) { say(o, c.name + ' wants to be your friend.', '#a60'); sendList(o); }
    },
    friendYes(c, m) {   // same as adding back
      if (!c.uid) return;
      const name = String(m.name || '').replace(/[^A-Za-z0-9_]/g, ''), u = name && byName.name(name);
      if (!u || !Q.get.get(u.id, c.uid)) return say(c, 'No friend request from ' + (name || 'them') + '.', '#c00');
      H.friendAdd(c, { name });
    },
    friendNo(c, m) {
      if (!c.uid) return;
      const name = String(m.name || '').replace(/[^A-Za-z0-9_]/g, ''), u = name && byName.name(name);
      if (!u) return;
      const was = isFriend(c.uid, u.id);
      Q.del.run(c.uid, u.id, u.id, c.uid);
      say(c, was ? u.name + ' was removed from your friends.' : 'Request from ' + u.name + ' declined.', '#a60');
      sendList(c); const o = online.get(u.id); if (o) { if (was) o.send({ t: 'fon', name: c.name, on: 0, gone: 1 }); sendList(o); }
    },
    pm(c, m) {
      if (!c.uid) return;
      const name = String(m.name || '').replace(/[^A-Za-z0-9_]/g, ''), u = name && byName.name(name);
      if (!u || u.id === c.uid) return say(c, 'No player called ' + (name || 'that') + '.', '#c00');
      if (!isFriend(c.uid, u.id)) return say(c, 'You can only message friends. Add ' + u.name + ' first.', '#c00');
      const me = byName.id(c.uid); if (me && me.muted_until > now()) return say(c, 'You are muted.', '#c00');
      if (now() - (c.lastPm || 0) < 800) return say(c, 'Slow down a little.', '#c00');
      const text = cleanChat(String(m.text || '')); if (!text) return;
      c.lastPm = now();
      const o = online.get(u.id), dropped = o && o.ignore.has(c.uid);
      if (!dropped) Q.pm.run(now(), c.uid, u.id, text, o ? 1 : 0);
      if (Math.random() < .05) { Q.trimPair.run(c.uid, u.id, u.id, c.uid, c.uid, u.id, u.id, c.uid); Q.trimOld.run(now() - DAYS * 864e5); }
      c.send({ t: 'pm', from: c.name, to: u.name, text, t0: now(), mine: 1 });
      if (o && !dropped) o.send({ t: 'pm', from: c.name, to: u.name, text, t0: now() });
    },
    pmHist(c, m) {
      if (!c.uid) return;
      const name = String(m.name || '').replace(/[^A-Za-z0-9_]/g, ''), u = name && byName.name(name);
      if (!u) return;
      const rows = Q.hist.all(c.uid, u.id, u.id, c.uid).reverse();
      c.send({ t: 'pmHist', name: u.name, lines: rows.map(r => ({ t0: r.t, mine: r.f === c.uid ? 1 : 0, text: r.text })) });
    },
  };
  return {
    H,
    onSignIn(c) {   // friends list, then anything that arrived while away
      sendList(c); tellFriends(c, true);
      const un = Q.unread.all(c.uid);
      if (un.length) { for (const r of un) c.send({ t: 'pm', from: r.name, to: c.name, text: r.text, t0: r.t, late: 1 }); Q.markSeen.run(c.uid); }
    },
    onLeave(c) { if (c.uid) tellFriends(c, false); },
    isFriend,
  };
};
