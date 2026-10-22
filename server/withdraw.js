'use strict';
// Withdrawals: Meme Coins out of the game as real $PIT, with a waiting period.
//
// A signed-in player asks at any bank to withdraw N $PIT (whole tokens). The Meme Coins (N x rate) leave their
// bank at once, and the request waits WITHDRAW_DAYS (30) days. During the wait the player can cancel and gets the
// coins back, and a moderator can hold or refuse a request (refused = coins back). When the wait is over the
// request is "ready" and is paid from the public pot wallet to the wallet linked to the account (proven by a
// signature, holder perks). The owner of the pot wallet signs the payouts himself: this server holds no keys and
// sends nothing. A payout is recorded only after the server has read it on-chain (`/withdraw paid <id> <tx>`).
//
// Limits: at most WITHDRAW_DAY_MAX $PIT per account in any 24 hours, at least WITHDRAW_MIN, and never more in
// total waiting than the pot wallet holds right now (read from Solana), so every request is covered.
// Settings: WITHDRAW_DAYS, WITHDRAW_DAY_MAX, WITHDRAW_MIN, POT_WALLET (else config.js potWallet), withdrawalsOpen
// and capesToMemeCoins in config.js. Off (with the reason) while the token, the pot wallet or the switch is missing.
const fs = require('fs');
const path = require('path');

module.exports = function withdraw({ db, now, say, loadSave, setSave, walOf, rpc, CAPES_MINT, flagCount }) {
  const cfg = (() => { try { return fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8'); } catch (e) { return ''; } })();
  const cfgAddr = (k) => { const m = new RegExp('\\b' + k + ':\\s*"([1-9A-HJ-NP-Za-km-z]{32,44})"').exec(cfg); return m ? m[1] : ''; };
  const cfgNum = (k, d) => { const m = new RegExp('\\b' + k + ':\\s*([0-9.]+)').exec(cfg); return m ? +m[1] : d; };
  const DAYS = +(process.env.WITHDRAW_DAYS || 30);
  const DAY_MAX = +(process.env.WITHDRAW_DAY_MAX || 100);
  const MIN = +(process.env.WITHDRAW_MIN || 1);
  const RATE = Math.max(1, Math.round(+(process.env.WITHDRAW_RATE || cfgNum('capesToMemeCoins', 100))));
  const POT = process.env.POT_WALLET || cfgAddr('potWallet');
  const SWITCH = process.env.WITHDRAWALS != null ? process.env.WITHDRAWALS === '1' : /\bwithdrawalsOpen:\s*true/.test(cfg);
  const DAY = 864e5;

  db.exec(`CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY, uid INT, wallet TEXT, coins INT, capes INT, t INT, due INT,
    status TEXT DEFAULT 'waiting', note TEXT DEFAULT '', paid_sig TEXT, paid_t INT DEFAULT 0)`);
  const Q = {
    add: db.prepare('INSERT INTO withdrawals(uid,wallet,coins,capes,t,due) VALUES(?,?,?,?,?,?)'),
    get: db.prepare('SELECT * FROM withdrawals WHERE id=?'),
    mine: db.prepare('SELECT id,wallet,coins,capes,t,due,status,note,paid_sig FROM withdrawals WHERE uid=? ORDER BY id DESC LIMIT 20'),
    day: db.prepare("SELECT COALESCE(SUM(capes),0) n FROM withdrawals WHERE uid=? AND t>? AND status!='cancelled' AND status!='refused'"),
    owed: db.prepare("SELECT COALESCE(SUM(capes),0) n FROM withdrawals WHERE status IN ('waiting','held')"),
    set: db.prepare('UPDATE withdrawals SET status=?, note=? WHERE id=?'),
    paid: db.prepare("UPDATE withdrawals SET status='paid', paid_sig=?, paid_t=? WHERE id=?"),
    bySig: db.prepare('SELECT id FROM withdrawals WHERE paid_sig=?'),
    list: db.prepare("SELECT w.id,w.uid,u.name,w.wallet,w.capes,w.t,w.due,w.status,w.note FROM withdrawals w JOIN users u ON u.id=w.uid WHERE w.status IN ('waiting','held') ORDER BY w.due LIMIT 200"),
    stats: db.prepare("SELECT status, COUNT(*) n, COALESCE(SUM(capes),0) capes FROM withdrawals GROUP BY status"),
  };

  // the pot wallet's $PIT (whole tokens), read from Solana, cached 5 minutes
  let pot = { t: 0, v: null };
  async function potNow(fresh) {
    if (!fresh && pot.v != null && now() - pot.t < 5 * 60e3) return pot.v;
    const r = await rpc('getTokenAccountsByOwner', [POT, { mint: CAPES_MINT }, { encoding: 'jsonParsed', commitment: 'confirmed' }]);
    const v = (r.value || []).reduce((a, x) => a + (+x.account.data.parsed.info.tokenAmount.uiAmount || 0), 0);
    pot = { t: now(), v: Math.floor(v) }; return pot.v;
  }
  const why = () => !CAPES_MINT ? 'Opens when the token launches.' : !POT ? 'Opens when the pot wallet is set.' : !SWITCH ? 'Withdrawals are paused right now.' : '';
  const status = (r) => r.status === 'waiting' && r.due <= now() ? 'ready' : r.status;

  async function info(uid) {
    const off = why(), w = walOf(uid);
    let room = null, potV = null;
    if (!off) { try { potV = await potNow(); room = Math.max(0, potV - Q.owed.get().n); } catch (e) { } }
    const used = Q.day.get(uid, now() - DAY).n;
    return { t: 'wd', open: !off, why: off, days: DAYS, rate: RATE, dayMax: DAY_MAX, min: MIN, dayLeft: Math.max(0, DAY_MAX - used),
      pot: potV, room, potWallet: POT, wallet: w ? w.wallet : '',
      list: Q.mine.all(uid).map(r => ({ id: r.id, capes: r.capes, coins: r.coins, t: r.t, due: r.due, status: status(r), note: r.note, sig: r.paid_sig || '' })) };
  }

  const busy = new Set();
  const H = {
    async wdInfo(c) { if (c.uid) c.send(await info(c.uid)); },
    async withdraw(c, m) {
      if (!c.uid || busy.has(c.uid)) return;
      busy.add(c.uid);
      try {
        const off = why(); if (off) return say(c, off, '#a60');
        const n = Math.floor(+m.capes);
        if (!(n >= MIN)) return say(c, 'Withdraw at least ' + MIN + ' $PIT.', '#c00');
        const w = walOf(c.uid); if (!w) return say(c, 'Link your wallet first (Holder perks, just above). Withdrawals are paid to that wallet.', '#c00');
        const used = Q.day.get(c.uid, now() - DAY).n;
        if (used + n > DAY_MAX) return say(c, 'You can withdraw ' + DAY_MAX + ' $PIT in any 24 hours. ' + Math.max(0, DAY_MAX - used) + ' left right now.', '#c00');
        let room; try { room = (await potNow(true)) - Q.owed.get().n; } catch (e) { return say(c, 'Could not read the pot wallet right now. Nothing changed. Try again in a minute.', '#c00'); }
        if (n > room) return say(c, room > 0 ? 'The pot can cover ' + room + ' more $PIT right now. Try a smaller amount.' : 'The pot is fully booked right now. Nothing changed. Try again later.', '#c00');
        const { u, st } = loadSave(c.uid); if (!st) return say(c, 'Your progress has not reached the server yet. Try again in a few seconds.', '#c00');
        const coins = n * RATE, bank = Math.floor(+st.bank || 0);
        if (bank < coins) return say(c, 'You need ' + coins.toLocaleString() + ' Meme Coins in your bank for ' + n + ' $PIT.', '#c00');
        st.bank = bank - coins;
        let id;
        db.exec('BEGIN');
        try { setSave(JSON.stringify(st), u.rev + 1, now(), u.id); id = Q.add.run(c.uid, w.wallet, coins, n, now(), now() + DAYS * DAY).lastInsertRowid; db.exec('COMMIT'); }
        catch (e) { db.exec('ROLLBACK'); return say(c, 'That did not work. Nothing changed.', '#c00'); }
        c.send({ t: 'wdBank', delta: -coins, rev: u.rev + 1 });
        say(c, 'Withdrawal #' + id + ': ' + n + ' $PIT to ' + w.wallet.slice(0, 4) + '...' + w.wallet.slice(-4) + ', paid from the pot wallet after ' + DAYS + ' days. You can cancel until then.', '#0a0');
        c.send(await info(c.uid));
      } finally { busy.delete(c.uid); }
    },
    async withdrawCancel(c, m) {
      if (!c.uid || busy.has(c.uid)) return;
      busy.add(c.uid);
      try {
        const r = Q.get.get(+m.id); if (!r || r.uid !== c.uid) return;
        if (r.status !== 'waiting' && r.status !== 'held') return say(c, 'That withdrawal can no longer be cancelled.', '#c00');
        if (r.status === 'waiting' && r.due <= now()) return say(c, 'That withdrawal is ready and in the payout queue, so it can no longer be cancelled.', '#c00');
        const { u, st } = loadSave(c.uid); if (!st) return say(c, 'Your progress has not reached the server yet. Try again in a few seconds.', '#c00');
        st.bank = Math.floor(+st.bank || 0) + r.coins;
        db.exec('BEGIN');
        try { setSave(JSON.stringify(st), u.rev + 1, now(), u.id); Q.set.run('cancelled', 'cancelled by the player', r.id); db.exec('COMMIT'); }
        catch (e) { db.exec('ROLLBACK'); return say(c, 'That did not work. Nothing changed.', '#c00'); }
        c.send({ t: 'wdBank', delta: r.coins, rev: u.rev + 1 });
        say(c, 'Withdrawal #' + r.id + ' cancelled. ' + r.coins.toLocaleString() + ' Meme Coins are back in your bank.', '#0a0');
        c.send(await info(c.uid));
      } finally { busy.delete(c.uid); }
    },
  };

  // a payout counts only when the transaction on Solana moved at least that many $PIT into the player's wallet
  async function checkPaid(r, sig) {
    const tx = await rpc('getTransaction', [sig, { encoding: 'jsonParsed', maxSupportedTransactionVersion: 0, commitment: 'confirmed' }]);
    if (!tx || tx.meta?.err) return 'That transaction was not found on Solana, or it failed.';
    const bal = (L) => (L || []).filter(b => b.mint === CAPES_MINT && b.owner === r.wallet).reduce((a, b) => a + (+b.uiTokenAmount.uiAmount || 0), 0);
    const got = bal(tx.meta.postTokenBalances) - bal(tx.meta.preTokenBalances);
    if (got + 1e-9 < r.capes) return 'That transaction gave ' + r.wallet.slice(0, 4) + '... ' + got + ' $PIT, not ' + r.capes + '.';
    const keys = (tx.transaction?.message?.accountKeys || []).filter(k => k.signer).map(k => k.pubkey);
    if (POT && !keys.includes(POT)) return 'That transaction was not signed by the pot wallet.';
    return '';
  }

  // moderators: /withdraw list | hold <id> <why> | release <id> | refuse <id> <why> | paid <id> <tx>
  async function cmd(c, name, rest, online) {
    const [sub, a, ...more] = String(rest || '').split(' '), note = more.join(' ').slice(0, 120);
    const r = a ? Q.get.get(+a) : null;
    const back = (row, why) => {   // refused: the coins go back to the player's bank
      const { u, st } = loadSave(row.uid); if (!st) return false;
      st.bank = Math.floor(+st.bank || 0) + row.coins;
      setSave(JSON.stringify(st), u.rev + 1, now(), u.id); Q.set.run('refused', why, row.id);
      const o = online.get(row.uid); if (o) { o.send({ t: 'wdBank', delta: row.coins, rev: u.rev + 1 }); say(o, 'Withdrawal #' + row.id + ' was refused: ' + why + ' Your ' + row.coins.toLocaleString() + ' Meme Coins are back in your bank.', '#c00'); }
      return true;
    };
    if (sub === 'list' || !sub) {
      const L = Q.list.all(); if (!L.length) return say(c, 'No withdrawals waiting.');
      return say(c, L.slice(0, 25).map(x => '#' + x.id + ' ' + x.name + ' ' + x.capes + ' $PIT ' + (x.status === 'held' ? 'HELD' : x.due <= now() ? 'READY' : 'in ' + Math.ceil((x.due - now()) / DAY) + 'd') + (flagCount(x.uid) ? ' (' + flagCount(x.uid) + ' flags)' : '')).join(' | '));
    }
    if (!r) return say(c, 'No withdrawal #' + a + '.', '#c00');
    if (sub === 'hold') { if (r.status !== 'waiting') return say(c, 'Only a waiting one can be held.', '#c00'); Q.set.run('held', note || 'under review', r.id); return say(c, '#' + r.id + ' held.'); }
    if (sub === 'release') { if (r.status !== 'held') return say(c, 'It is not held.', '#c00'); Q.set.run('waiting', '', r.id); return say(c, '#' + r.id + ' released.'); }
    if (sub === 'refuse') { if (r.status !== 'waiting' && r.status !== 'held') return say(c, 'It is not open.', '#c00'); db.exec('BEGIN'); try { back(r, note || 'it broke the rules.'); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); return say(c, 'That did not work.', '#c00'); } return say(c, '#' + r.id + ' refused, coins returned.'); }
    if (sub === 'paid') {
      const sig = more[0] || '';
      if (!/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(sig)) return say(c, 'Usage: /withdraw paid <id> <transaction>', '#c00');
      if (r.status !== 'waiting' && r.status !== 'held') return say(c, 'It is not open.', '#c00');
      if (Q.bySig.get(sig)) return say(c, 'That transaction is already recorded for another withdrawal.', '#c00');
      let bad; try { bad = await checkPaid(r, sig); } catch (e) { bad = 'Could not read Solana right now. Try again.'; }
      if (bad) return say(c, bad, '#c00');
      Q.paid.run(sig, now(), r.id);
      const o = online.get(r.uid); if (o) say(o, 'Withdrawal #' + r.id + ' is paid: ' + r.capes + ' $PIT are in your wallet.', '#0a0');
      return say(c, '#' + r.id + ' recorded as paid.');
    }
    return say(c, 'Usage: /withdraw list | hold <id> <why> | release <id> | refuse <id> <why> | paid <id> <tx>', '#c00');
  }

  // public numbers, so anyone can see what is waiting and what was paid
  async function http(req, res, url, json) {
    if (url.pathname !== '/withdrawals' || req.method !== 'GET') return false;
    const s = {}; for (const x of Q.stats.all()) s[x.status] = { count: x.n, capes: x.capes };
    let potV = null; if (!why()) { try { potV = await potNow(); } catch (e) { } }
    return json({ open: !why(), why: why(), days: DAYS, rate: RATE, dayMax: DAY_MAX, potWallet: POT, pot: potV,
      waiting: { count: (s.waiting?.count || 0) + (s.held?.count || 0), capes: (s.waiting?.capes || 0) + (s.held?.capes || 0) },
      paid: s.paid || { count: 0, capes: 0 } });
  }
  return { H, cmd, http, info, _potSet: (v) => { pot = { t: now(), v }; } };
};
