// Pit launch-day load test (Nov 8). Each runner plays USERS people browsing pit.memecapes.com the way the app does:
// wallet check every 15 s (getBalance + 2 token-account reads through /api/rpc), a coin sheet every 15 s, the home
// lists every 20 s, a page load now and then. Read-only: nothing is signed or sent. Prints one ::notice summary.
const BASE = process.env.BASE || "https://pit.memecapes.com";
const USERS = +(process.env.USERS || 15), SECS = +(process.env.SECS || 180), JOB = process.env.JOB || "0";
const ORIGIN = { Origin: BASE, "Content-Type": "application/json", "User-Agent": "memecapes-loadtest" };
const WALLETS = ["HDRqzAgzwrt2cYSNCgWd4y8xC4tKY2WqQ8ULWH55VAGc", "7N9TfSooUszxHqUUZg4vNiM3YYu4KRcYbmivbQXeNWtr", "5nvSdkcmBvnBYabbd4zgp4WyS6ZmCDhyLEFhv9f68ASR", "Ag1czHf4tQ78gfWBUXByjKKcr2CYqKRYpJw8PZ6XWdHk", "CYQBdjfA7LdNVreD2K4RjJtgYa3a1SgBRqD895kpuQ2h"];
const MINTS = ["DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"];
const T = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", T22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";
const stats = {};
const pick = (a) => a[Math.floor(Math.random() * a.length)];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function hit(name, url, init) {
  const t = Date.now();
  let code = "ERR";
  try { const r = await fetch(url, { ...init, signal: AbortSignal.timeout(20000) }); code = String(r.status); await r.arrayBuffer(); } catch (e) { code = e.name === "TimeoutError" ? "TIMEOUT" : "ERR"; }
  const s = (stats[name] ??= { n: 0, codes: {}, ms: [] });
  s.n++; s.codes[code] = (s.codes[code] || 0) + 1; s.ms.push(Date.now() - t);
}
const rpc = (method, params) => hit("rpc " + method, `${BASE}/api/rpc`, { method: "POST", headers: ORIGIN, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }) });
async function user(i, end) {
  await sleep(Math.random() * 15000); // people arrive spread out
  const w = pick(WALLETS);
  let k = 0;
  while (Date.now() < end) {
    const jobs = [rpc("getBalance", [w]), rpc("getParsedTokenAccountsByOwner", [w, { programId: T }, { encoding: "jsonParsed" }]), rpc("getParsedTokenAccountsByOwner", [w, { programId: T22 }, { encoding: "jsonParsed" }]), hit("token sheet", `${BASE}/api/token/${pick(MINTS)}`)];
    if (k % 4 === 0) jobs.push(hit("discover new", `${BASE}/api/discover?list=new`), hit("trending", `${BASE}/api/trending`));
    if (k % 8 === 0) jobs.push(hit("home page", `${BASE}/`));
    await Promise.all(jobs);
    k++;
    await sleep(15000 + Math.random() * 2000);
  }
}
const end = Date.now() + SECS * 1000;
await Promise.all(Array.from({ length: USERS }, (_, i) => user(i, end)));
const lines = Object.entries(stats).map(([name, s]) => {
  const ms = s.ms.sort((a, b) => a - b), p = (q) => ms[Math.min(ms.length - 1, Math.floor(q * ms.length))];
  return `${name}: ${s.n} reqs, codes ${JSON.stringify(s.codes)}, p50 ${p(0.5)} ms, p95 ${p(0.95)} ms, max ${ms[ms.length - 1]} ms`;
});
console.log(`::notice title=job ${JOB} (${USERS} users, ${SECS}s)::${lines.join("%0A")}`);
