// node server/test_memesnake.js : MemeSnake live feed (key check, merging, money/key filter)
const fs = require('fs'), os = require('os'), path = require('path');
process.env.MEMESNAKE_KEY = 'k_test_123';
const DATA = fs.mkdtempSync(path.join(os.tmpdir(), 'ms-'));
const MS = require('./memesnake')({ DATA });
let pass = 0, fail = 0; const ok = (c, m) => { c ? pass++ : (fail++, console.log('FAIL', m)); };
function call(method, body, auth) {
  return new Promise((done) => {
    const { Readable } = require('stream');
    const req = Readable.from(body ? [Buffer.from(JSON.stringify(body))] : []); req.method = method; req.headers = auth ? { authorization: 'Bearer ' + auth } : {};
    MS.http(req, { writeHead() {}, end() {} }, new URL('http://x/ms/feed'), (j, code) => done({ j, code: code || 200 }));
  });
}
(async () => {
  let r = await call('GET'); ok(r.j.parts.length === 4 && r.j.log.length === 0, 'starter has 4 rooms, no log');
  r = await call('POST', { log: [{ text: 'x' }] }); ok(r.code === 401, 'no key refused');
  r = await call('POST', { log: [{ text: 'x' }] }, 'k_test_12X'); ok(r.code === 401, 'wrong key refused');
  r = await call('POST', { status: 'online', log: [{ part: 'memecapes', agent: 'Launch Control', text: 'one' }] }, 'k_test_123'); ok(r.j.ok, 'post 1');
  r = await call('POST', { status: 'online', log: [{ part: 'token', agent: 'Security Review', text: 'two' }] }, 'k_test_123');
  r = await call('GET'); ok(r.j.log.length === 2 && r.j.status === 'online', 'status + log adds, does not wipe');
  await call('POST', { parts: [{ id: 'token', status: 'working', task: 'Security review', crews: [{ name: 'Security Review', status: 'working' }] }] }, 'k_test_123');
  r = await call('GET'); ok(r.j.parts.length === 4 && r.j.parts.find(p => p.id === 'token').status === 'working', 'one room updates, others stay');
  r = await call('POST', { log: [{ text: 'Bought 2 SOL of WIF' }, { text: 'wallet 3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg' }, { text: 'fine' }] }, 'k_test_123');
  ok(r.j.notes.length === 2 && r.j.kept === 3, 'money and address entries dropped');
  r = await call('POST', { log: [{ time: '2026-10-19T00:00:00Z', text: 'dup' }, { time: '2026-10-19T00:00:00Z', text: 'dup' }] }, 'k_test_123'); ok(r.j.kept === 4, 'repeats dropped');
  r = await call('POST', { replace: true, log: [{ text: 'fresh' }] }, 'k_test_123'); ok(r.j.kept === 1, 'replace starts over');
  console.log(fail ? `${fail} failed, ${pass} passed` : `all ${pass} checks pass`); process.exit(fail ? 1 : 0);
})();
