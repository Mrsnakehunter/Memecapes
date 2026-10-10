'use strict';
// MemeCapes game server: accounts, cloud saves, live players, chat, player trades.
// No packages to install: plain Node.js 22+ (built-in SQLite, built-in crypto, a small WebSocket layer below).
// Run:  node server.js        Settings come from environment variables (see README.md in this folder).

const http = require('http');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
process.removeAllListeners('warning'); // hide the "SQLite is experimental" notice
const { DatabaseSync } = require('node:sqlite');

const PORT = +process.env.PORT || 8080;
const DATA = process.env.DATA_DIR || path.join(__dirname, 'data');
const ADMIN_KEY = process.env.ADMIN_KEY || '';
const ADMINS = (process.env.ADMIN_NAMES || '').toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
const ORIGINS = (process.env.ALLOWED_ORIGINS || 'https://memecapes.com,https://www.memecapes.com,http://localhost:8000,http://127.0.0.1:8000').split(',').map(s => s.trim());
const MAX_SAVE = 900 * 1024;          // bytes of save JSON
const MAX_FRAME = 1024 * 1024;        // biggest WebSocket message accepted
const VIEW = 48;                      // tiles: you see players this close
const BAG = 35;                       // bag slots (the coin stack takes one)

fs.mkdirSync(path.join(DATA, 'backups'), { recursive: true });
const db = new DatabaseSync(path.join(DATA, 'memecapes.db'));
db.exec(`PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE COLLATE NOCASE, salt TEXT, hash TEXT, created INT, last INT,
  role TEXT DEFAULT '', banned INT DEFAULT 0, muted_until INT DEFAULT 0, save TEXT, rev INT DEFAULT 0, save_t INT DEFAULT 0, prev TEXT, iron INT DEFAULT 0, ip TEXT);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, uid INT, created INT, last INT);
CREATE TABLE IF NOT EXISTS flags(id INTEGER PRIMARY KEY, uid INT, t INT, kind TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, uid INT, target TEXT, t INT, why TEXT, chat TEXT);
CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY, t INT, a INT, b INT, a_gave TEXT, b_gave TEXT);
CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, t INT, uid INT, name TEXT, text TEXT);`);
const Q = {
  byName: db.prepare('SELECT * FROM users WHERE name=?'),
  byId: db.prepare('SELECT * FROM users WHERE id=?'),
  add: db.prepare('INSERT INTO users(name,salt,hash,created,last,iron,ip) VALUES(?,?,?,?,?,?,?)'),
  seen: db.prepare('UPDATE users SET last=?, ip=? WHERE id=?'),
  save: db.prepare('UPDATE users SET prev=save, save=?, rev=rev+1, save_t=? WHERE id=? AND rev=?'),
  setSave: db.prepare('UPDATE users SET save=?, rev=?, save_t=? WHERE id=?'),
  rollback: db.prepare('UPDATE users SET save=prev, rev=rev+1 WHERE id=? AND prev IS NOT NULL'),
  setRole: db.prepare('UPDATE users SET role=? WHERE id=?'),
  ban: db.prepare('UPDATE users SET banned=? WHERE id=?'),
  mute: db.prepare('UPDATE users SET muted_until=? WHERE id=?'),
  del: db.prepare('DELETE FROM users WHERE id=?'),
  sesAdd: db.prepare('INSERT INTO sessions(token,uid,created,last) VALUES(?,?,?,?)'),
  ses: db.prepare('SELECT * FROM sessions WHERE token=?'),
  sesSeen: db.prepare('UPDATE sessions SET last=? WHERE token=?'),
  sesDel: db.prepare('DELETE FROM sessions WHERE token=?'),
  sesDelUser: db.prepare('DELETE FROM sessions WHERE uid=?'),
  sesOld: db.prepare('DELETE FROM sessions WHERE last<?'),
  flag: db.prepare('INSERT INTO flags(uid,t,kind,detail) VALUES(?,?,?,?)'),
  report: db.prepare('INSERT INTO reports(uid,target,t,why,chat) VALUES(?,?,?,?,?)'),
  trade: db.prepare('INSERT INTO trades(t,a,b,a_gave,b_gave) VALUES(?,?,?,?,?)'),
  chat: db.prepare('INSERT INTO chat(t,uid,name,text) VALUES(?,?,?,?)'),
  chatTrim: db.prepare('DELETE FROM chat WHERE id < (SELECT MAX(id) FROM chat) - 5000'),
  recentChat: db.prepare('SELECT name,text,t FROM chat ORDER BY id DESC LIMIT 20'),
  count: db.prepare('SELECT COUNT(*) n FROM users'),
  listFlags: db.prepare('SELECT f.t,u.name,f.kind,f.detail FROM flags f JOIN users u ON u.id=f.uid ORDER BY f.id DESC LIMIT 200'),
  listReports: db.prepare('SELECT r.t,u.name reporter,r.target,r.why,r.chat FROM reports r JOIN users u ON u.id=r.uid ORDER BY r.id DESC LIMIT 200'),
};
const now = () => Date.now();

// ---------- words ----------
const BAD = (() => { try { return fs.readFileSync(path.join(__dirname, 'badwords.txt'), 'utf8').split(/\r?\n/).map(s => s.trim().toLowerCase()).filter(s => s && !s.startsWith('#')); } catch (e) { return []; } })();
const RESERVED = ['admin', 'administrator', 'mod', 'moderator', 'staff', 'system', 'server', 'memecapes', 'official', 'support', 'jagex', 'runescape'];
const squash = s => s.toLowerCase().replace(/[0@]/g, 'o').replace(/[1!|]/g, 'i').replace(/3/g, 'e').replace(/[4]/g, 'a').replace(/[5$]/g, 's').replace(/7/g, 't').replace(/[^a-z]/g, '');
// short words must match the whole word (so "grape" is fine); long ones match inside words too
const isBad = s => { const q = squash(s); return !!q && BAD.some(w => q === w || q === w + 's' || (w.length >= 5 && q.includes(w))); };
function cleanChat(t) {
  t = String(t || '').replace(/[\u0000-\u001f\u007f<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, 80);
  if (!BAD.length) return t;
  return t.split(' ').map(w => isBad(w) ? '*'.repeat(Math.min(6, w.length)) : w).join(' ');
}
function nameProblem(n) {
  if (!/^[A-Za-z0-9_]{3,12}$/.test(n)) return 'Pick a name with 3 to 12 letters, numbers or _.';
  const q = squash(n);
  if (RESERVED.some(r => q.includes(r))) return 'That name is reserved.';
  if (BAD.some(w => q.includes(w))) return 'Pick a different name.';
  return '';
}

// ---------- passwords and sessions ----------
const hashPass = (p, salt) => crypto.scryptSync(p, salt, 32).toString('hex');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
function newSession(uid) { const tok = crypto.randomBytes(32).toString('hex'); Q.sesAdd.run(sha(tok), uid, now(), now()); return tok; }

// ---------- save checks ----------
const sumXp = s => Object.values((s && s.xp) || {}).reduce((a, v) => a + (+v || 0), 0);
const wealth = s => (+((s && s.coins) || 0)) + (+((s && s.bank) || 0));
function checkSave(st) {
  if (!st || typeof st !== 'object' || Array.isArray(st)) return 'not a save';
  if (!Array.isArray(st.inv) || st.inv.length > 40) return 'bad bag';
  for (const k of ['coins', 'bank']) if (st[k] != null && !(Number.isFinite(+st[k]) && +st[k] >= 0)) return 'bad ' + k;
  if (st.xp && typeof st.xp !== 'object') return 'bad xp';
  return '';
}
function flagGains(u, prev, next) {
  if (!prev) return;
  const dt = Math.max(60, (now() - (u.save_t || now())) / 1000);
  const dw = wealth(next) - wealth(prev), dx = sumXp(next) - sumXp(prev);
  if (dw > 250000 + 4000 * dt) Q.flag.run(u.id, now(), 'coins', `+${Math.round(dw)} in ${Math.round(dt)}s`);
  if (dx > 400000 + 15000 * dt) Q.flag.run(u.id, now(), 'xp', `+${Math.round(dx)} in ${Math.round(dt)}s`);
}

// ---------- tiny WebSocket layer (RFC 6455, text frames) ----------
function wsAccept(req, socket) {
  const key = req.headers['sec-websocket-key'];
  if (!key) return socket.destroy();
  const acc = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
  socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + acc + '\r\n\r\n');
  socket.setNoDelay(true);
  const c = { socket, buf: Buffer.alloc(0), frag: [], alive: true, open: true, ip: (req.headers['x-forwarded-for'] || socket.remoteAddress || '').split(',')[0].trim(), bucket: 40, bt: now() };
  c.send = obj => { if (!c.open) return; const d = Buffer.from(JSON.stringify(obj)); let h; if (d.length < 126) h = Buffer.from([0x81, d.length]); else if (d.length < 65536) { h = Buffer.alloc(4); h[0] = 0x81; h[1] = 126; h.writeUInt16BE(d.length, 2); } else { h = Buffer.alloc(10); h[0] = 0x81; h[1] = 127; h.writeBigUInt64BE(BigInt(d.length), 2); } socket.write(Buffer.concat([h, d])); };
  c.close = () => { if (!c.open) return; c.open = false; try { socket.write(Buffer.from([0x88, 0])); } catch (e) { } socket.end(); setTimeout(() => socket.destroy(), 1000); };
  c.ping = () => { try { socket.write(Buffer.from([0x89, 0])); } catch (e) { } };
  socket.on('data', chunk => {
    c.buf = Buffer.concat([c.buf, chunk]);
    while (c.buf.length >= 2) {
      const b0 = c.buf[0], b1 = c.buf[1], op = b0 & 15, fin = b0 & 128, masked = b1 & 128;
      let len = b1 & 127, off = 2;
      if (len === 126) { if (c.buf.length < 4) return; len = c.buf.readUInt16BE(2); off = 4; }
      else if (len === 127) { if (c.buf.length < 10) return; len = Number(c.buf.readBigUInt64BE(2)); off = 10; }
      if (len > MAX_FRAME || !masked) return c.close();
      if (c.buf.length < off + 4 + len) return;
      const mask = c.buf.subarray(off, off + 4), data = Buffer.from(c.buf.subarray(off + 4, off + 4 + len));
      for (let i = 0; i < data.length; i++) data[i] ^= mask[i & 3];
      c.buf = c.buf.subarray(off + 4 + len);
      if (op === 8) return c.close();
      if (op === 9) { socket.write(Buffer.concat([Buffer.from([0x8a, data.length]), data])); continue; }
      if (op === 10) { c.alive = true; continue; }
      if (op === 1 || op === 0) {
        c.frag.push(data);
        if (fin) { const msg = Buffer.concat(c.frag).toString('utf8'); c.frag = []; if (msg.length > MAX_FRAME) return c.close(); onMessage(c, msg); }
      }
    }
  });
  socket.on('close', () => { c.open = false; onClose(c); });
  socket.on('error', () => { c.open = false; });
  onOpen(c);
}

// ---------- live state ----------
const online = new Map();   // uid -> connection
const loginTries = new Map(); // ip -> [times]
let seq = 0;
const say = (c, text, color) => c.send({ t: 'info', text, color });
const pub = c => ({ id: c.uid, name: c.name, g: c.look.g | 0, c: c.look.c || '', lv: c.look.lv | 0, role: c.role || '' });
function broadcast(obj, except) { for (const o of online.values()) if (o !== except) o.send(obj); }

function onOpen(c) { c.id = ++seq; c.send({ t: 'hello', need: 'login' }); }
function onClose(c) {
  if (c.trade) tradeEnd(c.trade, c.name + ' left.');
  if (c.uid && online.get(c.uid) === c) { online.delete(c.uid); broadcast({ t: 'leave', id: c.uid }); }
}

function tooMany(ip) {
  const L = (loginTries.get(ip) || []).filter(t => now() - t < 10 * 60e3); L.push(now()); loginTries.set(ip, L);
  return L.length > 12;
}

function signIn(c, u, tok) {
  if (u.banned) { c.send({ t: 'err', text: 'This account is banned.' }); return c.close(); }
  const old = online.get(u.id);
  if (old && old !== c) { old.send({ t: 'kicked', text: 'You logged in somewhere else.' }); online.delete(u.id); old.close(); }
  c.uid = u.id; c.name = u.name; c.role = ADMINS.includes(u.name.toLowerCase()) ? 'admin' : (u.role || '');
  c.iron = !!u.iron; c.look = { g: 0, c: '', lv: 3 }; c.pos = null; c.ignore = new Set();
  online.set(u.id, c); Q.seen.run(now(), c.ip, u.id);
  let save = null; try { save = u.save ? JSON.parse(u.save) : null; } catch (e) { }
  c.send({ t: 'welcome', name: u.name, token: tok, save, rev: u.rev, role: c.role, iron: c.iron, online: online.size });
  c.send({ t: 'chatlog', lines: Q.recentChat.all().reverse() });
  for (const o of online.values()) if (o !== c && o.pos) c.send({ t: 'pi', ...pub(o) });
}

const H = {
  register(c, m) {
    if (c.uid) return;
    if (tooMany(c.ip)) return c.send({ t: 'err', text: 'Too many tries. Wait a few minutes.' });
    const name = String(m.name || ''), pass = String(m.pass || '');
    const np = nameProblem(name); if (np) return c.send({ t: 'err', text: np });
    if (pass.length < 8 || pass.length > 100) return c.send({ t: 'err', text: 'Use a password with at least 8 characters.' });
    if (Q.byName.get(name)) return c.send({ t: 'err', text: 'That name is taken.' });
    const salt = crypto.randomBytes(16).toString('hex');
    const r = Q.add.run(name, salt, hashPass(pass, salt), now(), now(), m.iron ? 1 : 0, c.ip);
    const u = Q.byId.get(r.lastInsertRowid);
    signIn(c, u, newSession(u.id));
  },
  login(c, m) {
    if (c.uid) return;
    if (tooMany(c.ip)) return c.send({ t: 'err', text: 'Too many tries. Wait a few minutes.' });
    const u = Q.byName.get(String(m.name || ''));
    if (!u || hashPass(String(m.pass || ''), u.salt) !== u.hash) return c.send({ t: 'err', text: 'Wrong name or password.' });
    signIn(c, u, newSession(u.id));
  },
  resume(c, m) {
    if (c.uid) return;
    const s = Q.ses.get(sha(String(m.token || '')));
    if (!s || now() - s.last > 60 * 864e5) return c.send({ t: 'err', text: 'Please log in again.', relog: 1 });
    const u = Q.byId.get(s.uid); if (!u) return c.send({ t: 'err', text: 'Please log in again.', relog: 1 });
    Q.sesSeen.run(now(), s.token);
    signIn(c, u, m.token);
  },
  logout(c, m) { Q.sesDel.run(sha(String(m.token || ''))); c.close(); },
  deleteAccount(c, m) {
    const u = c.uid && Q.byId.get(c.uid); if (!u) return;
    if (hashPass(String(m.pass || ''), u.salt) !== u.hash) return c.send({ t: 'err', text: 'Wrong password.' });
    Q.sesDelUser.run(u.id); Q.del.run(u.id); c.send({ t: 'deleted' }); c.close();
  },
  save(c, m) {
    if (!c.uid || c.trade && c.trade.stage === 3) return;
    const raw = JSON.stringify(m.st || null);
    if (raw.length > MAX_SAVE) return c.send({ t: 'err', text: 'Save too big.' });
    const bad = checkSave(m.st); if (bad) { Q.flag.run(c.uid, now(), 'save', bad); return c.send({ t: 'err', text: 'Save refused: ' + bad }); }
    const u = Q.byId.get(c.uid);
    if (+m.rev !== u.rev) return c.send({ t: 'stale', rev: u.rev });
    let prev = null; try { prev = u.save ? JSON.parse(u.save) : null; } catch (e) { }
    flagGains(u, prev, m.st);
    const r = Q.save.run(raw, now(), c.uid, u.rev);
    if (!r.changes) return c.send({ t: 'stale', rev: u.rev });
    c.send({ t: 'saved', rev: u.rev + 1 });
  },
  pull(c) { if (!c.uid) return; const u = Q.byId.get(c.uid); let save = null; try { save = JSON.parse(u.save); } catch (e) { } c.send({ t: 'resync', save, rev: u.rev }); },
  pos(c, m) {
    if (!c.uid) return;
    const x = +m.x, y = +m.y; if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    const first = !c.pos;
    c.pos = { x, y, r: +m.r || 0, m: m.m | 0, a: String(m.a || '').slice(0, 16) };
    const look = { g: m.g ? 1 : 0, c: String(m.c || '').slice(0, 24), lv: Math.max(3, Math.min(200, m.lv | 0)) };
    if (first || look.g !== c.look.g || look.c !== c.look.c || look.lv !== c.look.lv) { c.look = look; broadcast({ t: 'pi', ...pub(c) }, c); }
  },
  chat(c, m) {
    if (!c.uid) return;
    const raw = String(m.text || '');
    if (raw.startsWith('/') && c.role === 'admin') return adminCmd(c, raw);
    const u = Q.byId.get(c.uid);
    if (u.muted_until > now()) return say(c, 'You are muted for ' + Math.ceil((u.muted_until - now()) / 60e3) + ' more minutes.', '#c00');
    if (now() - (c.lastChat || 0) < 1200) return say(c, 'Slow down a little.', '#c00');
    const text = cleanChat(raw); if (!text) return;
    c.lastChat = now();
    Q.chat.run(now(), c.uid, c.name, text); if (Math.random() < .01) Q.chatTrim.run();
    for (const o of online.values()) if (!o.ignore.has(c.uid)) o.send({ t: 'chat', id: c.uid, name: c.name, text, role: c.role });
  },
  ignore(c, m) { const o = findOnline(m.name); if (!o) return; if (m.off) c.ignore.delete(o.uid); else c.ignore.add(o.uid); },
  report(c, m) {
    if (!c.uid) return;
    Q.report.run(c.uid, String(m.name || '').slice(0, 12), now(), String(m.why || '').slice(0, 200), JSON.stringify(Q.recentChat.all()));
    say(c, 'Thanks. A moderator will look at it.', '#0a0');
  },
  who(c) { c.send({ t: 'who', names: [...online.values()].map(o => o.name).sort() }); },

  // ---- trades: the server checks both offers against the saved bags and does the swap itself
  tradeReq(c, m) {
    if (!c.uid) return;
    const o = findOnline(m.name);
    if (!o || o === c) return say(c, 'That player is not online.', '#c00');
    if (c.iron || o.iron) return say(c, 'Diamond Hands players cannot trade.', '#c00');
    if (c.trade || o.trade) return say(c, (c.trade ? 'You are' : o.name + ' is') + ' already trading.', '#c00');
    if (o.ignore.has(c.uid)) return say(c, o.name + ' is not taking trades.', '#c00');
    if (o.pendingFrom === c.uid && now() - o.pendingT < 60e3) return H.tradeYes(o, { name: c.name });
    c.pendingFrom = null; o.pendingFrom = c.uid; o.pendingT = now();
    o.send({ t: 'tradeReq', from: c.name }); say(c, 'Trade request sent to ' + o.name + '.', '#0a0');
  },
  tradeYes(c, m) {
    const o = findOnline(m.name);
    if (!o || c.pendingFrom !== o.uid || now() - c.pendingT > 60e3) return say(c, 'That trade request ran out.', '#c00');
    if (c.trade || o.trade) return say(c, 'One of you is already trading.', '#c00');
    c.pendingFrom = null;
    const T = { a: o, b: c, stage: 1, off: new Map([[o.uid, { items: [], coins: 0 }], [c.uid, { items: [], coins: 0 }]]), acc: new Set(), t: now() };
    o.trade = c.trade = T;
    o.send({ t: 'tradeStart', with: c.name }); c.send({ t: 'tradeStart', with: o.name });
  },
  tradeOffer(c, m) {
    const T = c.trade; if (!T || T.stage !== 1) return;
    const items = Array.isArray(m.items) ? m.items.slice(0, 28).map(String) : [], coins = Math.max(0, Math.floor(+m.coins || 0));
    const why = offerProblem(c.uid, items, coins); if (why) return say(c, why, '#c00');
    T.off.set(c.uid, { items, coins }); T.acc.clear();
    other(T, c).send({ t: 'tradeTheirs', items, coins });
  },
  tradeAccept(c, m) {
    const T = c.trade; if (!T || (m.stage | 0) !== T.stage) return;
    T.acc.add(c.uid); other(T, c).send({ t: 'tradeAcc', stage: T.stage });
    if (T.acc.size < 2) return;
    if (T.stage === 1) { T.stage = 2; T.acc.clear(); T.a.send({ t: 'tradeStage2' }); T.b.send({ t: 'tradeStage2' }); return; }
    tradeFinish(T);
  },
  tradeCancel(c) { if (c.trade) tradeEnd(c.trade, c.name + ' declined the trade.'); },
};

function findOnline(name) { name = String(name || '').toLowerCase(); for (const o of online.values()) if (o.name.toLowerCase() === name) return o; return null; }
const other = (T, c) => T.a === c ? T.b : T.a;
const NOTRADE = k => k === 'coin' || k.startsWith('cx_') || k.startsWith('cape_') || k === 'qcape' || k.startsWith('pet') || k === 'clue' || k.startsWith('lamp');
function loadSave(uid) { const u = Q.byId.get(uid); try { return { u, st: JSON.parse(u.save) }; } catch (e) { return { u, st: null }; } }
function offerProblem(uid, items, coins) {
  const { st } = loadSave(uid);
  if (!st) return 'Your progress has not reached the server yet. Wait a few seconds and try again.';
  if (coins > (+st.coins || 0)) return 'You do not have that many Meme Coins on you.';
  const have = {}; for (const k of st.inv) have[k] = (have[k] || 0) + 1;
  for (const k of items) { if (NOTRADE(k)) return 'That item cannot be traded.'; if (!have[k]) return 'That item is not in your bag (the server copy).'; have[k]--; }
  return '';
}
function tradeEnd(T, why) {
  for (const c of [T.a, T.b]) { if (c.trade === T) { c.trade = null; c.send({ t: 'tradeCancel', why }); } }
}
function tradeFinish(T) {
  T.stage = 3;
  const A = loadSave(T.a.uid), B = loadSave(T.b.uid), oa = T.off.get(T.a.uid), ob = T.off.get(T.b.uid);
  const pa = offerProblem(T.a.uid, oa.items, oa.coins), pb = offerProblem(T.b.uid, ob.items, ob.coins);
  if (pa || pb) return tradeEnd(T, 'Trade stopped: an offer no longer matches what is in the bag.');
  const swap = (st, give, get) => {
    const rm = give.items.slice(); st.inv = st.inv.filter(k => { const i = rm.indexOf(k); if (i >= 0) { rm.splice(i, 1); return false; } return true; });
    st.coins = (+st.coins || 0) - give.coins + get.coins; get.items.forEach(k => st.inv.push(k));
  };
  const room = (st, give, get) => BAG - ((+st.coins || 0) - give.coins + get.coins > 0 ? 1 : 0) - (st.inv.length - give.items.length) >= get.items.length;
  if (!room(A.st, oa, ob) || !room(B.st, ob, oa)) return tradeEnd(T, 'Trade stopped: not enough bag space.');
  swap(A.st, oa, ob); swap(B.st, ob, oa);
  const t = now();
  db.exec('BEGIN');
  try {
    Q.setSave.run(JSON.stringify(A.st), A.u.rev + 1, t, A.u.id); Q.setSave.run(JSON.stringify(B.st), B.u.rev + 1, t, B.u.id);
    Q.trade.run(t, A.u.id, B.u.id, JSON.stringify(oa), JSON.stringify(ob)); db.exec('COMMIT');
  } catch (e) { db.exec('ROLLBACK'); return tradeEnd(T, 'Trade failed. Nothing changed.'); }
  T.a.trade = T.b.trade = null;
  T.a.send({ t: 'tradeDone', inv: A.st.inv, coins: A.st.coins, rev: A.u.rev + 1, gave: oa, got: ob });
  T.b.send({ t: 'tradeDone', inv: B.st.inv, coins: B.st.coins, rev: B.u.rev + 1, gave: ob, got: oa });
}

function adminCmd(c, raw) {
  const [cmd, name, arg] = raw.slice(1).split(' '); const rest = raw.split(' ').slice(1).join(' ');
  const u = name && Q.byName.get(name);
  const o = u && online.get(u.id);
  switch (cmd) {
    case 'announce': return broadcast({ t: 'notice', text: cleanChat(rest) });
    case 'mute': if (!u) break; Q.mute.run(now() + (+arg || 60) * 60e3, u.id); return say(c, name + ' muted for ' + (+arg || 60) + ' min.');
    case 'unmute': if (!u) break; Q.mute.run(0, u.id); return say(c, name + ' unmuted.');
    case 'ban': if (!u) break; Q.ban.run(1, u.id); Q.sesDelUser.run(u.id); if (o) { o.send({ t: 'kicked', text: 'You are banned.' }); o.close(); } return say(c, name + ' banned.');
    case 'unban': if (!u) break; Q.ban.run(0, u.id); return say(c, name + ' unbanned.');
    case 'kick': if (!o) break; o.send({ t: 'kicked', text: 'A moderator removed you from the game.' }); o.close(); return say(c, name + ' kicked.');
    case 'rollback': if (!u) break; Q.rollback.run(u.id); if (o) { o.send({ t: 'kicked', text: 'Your progress was restored by a moderator. Log in again.' }); o.close(); } return say(c, name + ' rolled back one save.');
    case 'mod': if (!u) break; Q.setRole.run(arg === 'off' ? '' : 'mod', u.id); return say(c, name + (arg === 'off' ? ' is no longer a mod.' : ' is now a mod.'));
  }
  say(c, 'Commands: /announce text, /mute name minutes, /unmute name, /ban name, /unban name, /kick name, /rollback name', '#a60');
}

function onMessage(c, msg) {
  const t = now(); c.bucket = Math.min(40, c.bucket + (t - c.bt) / 1000 * 25); c.bt = t;
  if (--c.bucket < 0) return c.close();
  let m; try { m = JSON.parse(msg); } catch (e) { return; }
  const f = m && H[m.t]; if (!f) return;
  try { f(c, m); } catch (e) { console.error('handler', m.t, e); }
}

// ---------- ticks: positions 5 times a second, pings, cleanup, daily backup ----------
setInterval(() => {
  const all = [...online.values()].filter(o => o.pos);
  for (const c of online.values()) {
    if (!c.pos) continue;
    const p = [];
    for (const o of all) if (o !== c && Math.abs(o.pos.x - c.pos.x) <= VIEW && Math.abs(o.pos.y - c.pos.y) <= VIEW) p.push([o.uid, Math.round(o.pos.x * 100) / 100, Math.round(o.pos.y * 100) / 100, Math.round(o.pos.r * 100) / 100, o.pos.m, o.pos.a]);
    c.send({ t: 'pl', p, n: online.size });
  }
}, 200);
setInterval(() => {
  for (const c of online.values()) { if (!c.alive) { c.close(); continue; } c.alive = false; c.ping(); }
  for (const o of online.values()) if (o.trade && now() - o.trade.t > 15 * 60e3) tradeEnd(o.trade, 'The trade timed out.');
}, 25e3);
function backup() {
  const d = new Date().toISOString().slice(0, 10), f = path.join(DATA, 'backups', d + '.db');
  if (fs.existsSync(f)) return;
  try { db.exec(`VACUUM INTO '${f.replace(/'/g, "''")}'`); } catch (e) { console.error('backup', e); }
  const L = fs.readdirSync(path.join(DATA, 'backups')).filter(n => n.endsWith('.db')).sort();
  while (L.length > 14) fs.unlinkSync(path.join(DATA, 'backups', L.shift()));
  Q.sesOld.run(now() - 90 * 864e5);
}
setInterval(backup, 3600e3); setTimeout(backup, 5000);

// ---------- HTTP: health check, admin pages, WebSocket upgrade ----------
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o, s) => { res.writeHead(s || 200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }); res.end(JSON.stringify(o, null, 1)); };
  if (url.pathname === '/' || url.pathname === '/health') return json({ ok: true, online: online.size });
  if (url.pathname.startsWith('/admin/')) {
    if (!ADMIN_KEY || req.headers.authorization !== 'Bearer ' + ADMIN_KEY) return json({ error: 'no' }, 403);
    if (url.pathname === '/admin/stats') return json({ online: online.size, accounts: Q.count.get().n, names: [...online.values()].map(o => o.name) });
    if (url.pathname === '/admin/flags') return json(Q.listFlags.all());
    if (url.pathname === '/admin/reports') return json(Q.listReports.all());
    if (url.pathname === '/admin/backup') { const f = path.join(DATA, 'backups', 'download.db'); try { fs.rmSync(f, { force: true }); db.exec(`VACUUM INTO '${f.replace(/'/g, "''")}'`); } catch (e) { return json({ error: String(e) }, 500); } res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Disposition': 'attachment; filename=memecapes.db' }); return fs.createReadStream(f).pipe(res); }
  }
  json({ error: 'not found' }, 404);
});
server.on('upgrade', (req, socket) => {
  const origin = req.headers.origin || '';
  if (new URL(req.url, 'http://x').pathname !== '/ws' || (origin && !ORIGINS.includes(origin))) { socket.write('HTTP/1.1 403 Forbidden\r\n\r\n'); return socket.destroy(); }
  wsAccept(req, socket);
});
server.listen(PORT, () => console.log('MemeCapes server on port ' + PORT + ', data in ' + DATA));
const stop = () => { try { db.close(); } catch (e) { } process.exit(0); };
process.on('SIGTERM', stop); process.on('SIGINT', stop);
