'use strict';
// MemeSnake Live (memesnake.html): the public activity feed of MemeSnake, the AI agent that runs Mr Snake's crews.
//   GET  /ms/feed                 -> the current feed (public)
//   POST /ms/feed  (Authorization: Bearer <MEMESNAKE_KEY>)  body = the whole feed.json, or {log:[...]} to add entries
// The feed is checked against MemeSnake's own rules before it is kept: only the known parts and statuses, short text,
// no dollar amounts, nothing that looks like a wallet key or secret, the newest 50 log entries. Set MEMESNAKE_KEY on
// Render; without it nobody can post and the page shows "offline".
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

module.exports = function memesnake({ DATA }) {
  const KEY = process.env.MEMESNAKE_KEY || '';
  const FILE = path.join(DATA, 'memesnake_feed.json');
  const PARTS = ['creator', 'trading', 'memecapes'], PST = ['idle', 'working', 'done', 'blocked'], TOP = ['online', 'paused', 'offline'];
  const AGENT = ['hq', ...PARTS];
  const empty = () => ({ updated: new Date().toISOString(), status: 'offline', headline: '', parts: [], log: [] });
  let feed = empty(); try { feed = JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch (e) { }

  // text that must never go on the public page: money amounts, keys, seed phrases, long secrets
  const BAD = [/[$€£]\s?\d/, /\b\d[\d,.]*\s?(usd|usdc|usdt|sol|eth|btc|dollars?)\b/i, /\b[1-9A-HJ-NP-Za-km-z]{32,}\b/, /\b[0-9a-f]{40,}\b/i, /seed phrase|private key|mnemonic|password/i];
  const clean = (s, n) => String(s == null ? '' : s).replace(/[\u0000-\u001f<>]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, n);
  function check(t) { for (const r of BAD) if (r.test(t)) return false; return true; }
  const iso = (v) => { const d = new Date(v); return isNaN(d) ? new Date().toISOString() : d.toISOString(); };

  function entry(e, why) {
    const text = clean(e && e.text, 240), agent = clean(e && e.agent, 40);
    if (!text) { why.push('a log entry has no text'); return null; }
    if (!check(text) || !check(agent)) { why.push('dropped a log entry with a money amount or something that looks like a key: "' + text.slice(0, 40) + '…"'); return null; }
    return { time: iso(e.time), part: AGENT.includes(e.part) ? e.part : 'hq', agent: agent || 'MemeSnake', text };
  }
  function parts(list, why) {
    return (Array.isArray(list) ? list : []).filter(p => p && PARTS.includes(p.id)).slice(0, 3).map(p => {
      let task = clean(p.task, 140); if (!check(task)) { why.push('hid the ' + p.id + ' task (money amount or key)'); task = ''; }
      return { id: p.id, status: PST.includes(p.status) ? p.status : 'idle', task,
        crews: (Array.isArray(p.crews) ? p.crews : []).slice(0, 12).map(c => ({ name: clean(c && c.name, 32), status: PST.includes(c && c.status) ? c.status : 'idle' })).filter(c => c.name) };
    });
  }

  async function http(req, res, url, json) {
    if (url.pathname !== '/ms/feed') return false;
    if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' }); return res.end(); }
    if (req.method === 'GET') return json(feed);
    if (req.method !== 'POST') return json({ error: 'GET or POST' }, 405);
    const m = /^Bearer (.+)$/.exec(req.headers.authorization || '');
    if (!KEY || !m || m[1].length !== KEY.length || !crypto.timingSafeEqual(Buffer.from(m[1]), Buffer.from(KEY))) return json({ error: 'Not allowed.' }, 401);
    let b; try { b = await new Promise((ok, no) => { let n = 0; const ps = []; req.on('data', d => { n += d.length; if (n > 200e3) { no(new Error('too big')); req.destroy(); } else ps.push(d); }); req.on('end', () => { try { ok(JSON.parse(Buffer.concat(ps).toString('utf8') || '{}')); } catch (e) { no(e); } }); req.on('error', no); }); } catch (e) { return json({ error: 'Send JSON, under 200 KB.' }, 400); }
    const why = [], next = { ...feed };
    if (b.status !== undefined) next.status = TOP.includes(b.status) ? b.status : 'offline';
    if (b.headline !== undefined) { const h = clean(b.headline, 120); if (check(h)) next.headline = h; else why.push('hid the headline (money amount or key)'); }
    if (b.parts !== undefined) next.parts = parts(b.parts, why);
    if (Array.isArray(b.log)) {
      const add = b.log.slice(0, 50).map(e => entry(e, why)).filter(Boolean);
      // a whole feed.json replaces the log; {log:[...]} alone adds to it
      const base = b.parts !== undefined || b.status !== undefined ? [] : feed.log;
      const seen = new Set(), all = [...add, ...base].filter(e => { const k = e.time + e.text; if (seen.has(k)) return false; seen.add(k); return true; });
      next.log = all.sort((x, y) => y.time.localeCompare(x.time)).slice(0, 50);
    }
    next.updated = new Date().toISOString();
    feed = next; try { fs.writeFileSync(FILE, JSON.stringify(feed)); } catch (e) { }
    return json({ ok: true, kept: feed.log.length, notes: why });
  }
  return { http };
};
