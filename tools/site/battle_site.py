#!/usr/bin/env python3
"""Weekly Agent Battle on memecapes.com (the battle itself lives in the Pit at <pit>/battle).

index.html: 'Battle' in the menu, a Battle line beside the cape, a home section with the live practice week (pot,
players, top 3, read from the Pit's public /api/battle/board, which allows memecapes.com), and an FAQ entry.
launch.html: 'Battle' in the top menu and the phone bar. Links carry data-pit="/battle" and get their address from
config.js `pit` at load, so moving the Pit to pit.memecapes.com needs no edit here. Idempotent: run it again any time.
"""
import os, re

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PIT0 = 'https://pit.memecapes.com'
MARK = '<!--battle-->'


def rd(p):
    return open(os.path.join(ROOT, p), encoding='utf-8').read()


def wr(p, s):
    open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)


def once(s, old, new, what):
    if new in s:
        return s
    assert s.count(old) == 1, (what, s.count(old))
    return s.replace(old, new)


# the script both pages use: point every data-pit link at the Pit from config.js
FIX = ('<script>(function(){var p=((window.MC_CONFIG||{}).pit||"' + PIT0 + '").replace(/\\/+$/,"");'
       'if(!/^https:\\/\\/[a-z0-9.-]+$/.test(p))return;'
       'document.querySelectorAll("a[data-pit]").forEach(function(a){a.href=p+a.getAttribute("data-pit")});'
       'window.__PITB=p})();</script>')

# ------------------------------------------------------------------ index.html
s = rd('index.html')
s = once(s, '<a href="launch.html">Launch</a><a href="memesnake/">AI Agent</a>',
         '<a href="launch.html">Launch</a><a href="' + PIT0 + '/battle" data-pit="/battle">Battle</a><a href="memesnake/">AI Agent</a>', 'nav')
s = once(s, '<a class="pw" href="launch.html"><b>Launch</b><span>Launch a Solana coin with fees you choose, and trade new coins.</span></a>\n',
         '<a class="pw" href="launch.html"><b>Launch</b><span>Launch a Solana coin with fees you choose, and trade new coins.</span></a>\n'
         '<a class="pw" href="' + PIT0 + '/battle" data-pit="/battle"><b>Battle</b><span>Pick an AI agent and a lucky coin. It trades all week; the best % return wins. Practice weeks are free.</span></a>\n', 'pw')

SEC = MARK + '''<section class="bt rev" id="battle"><style>
.bt{padding:34px 0}.bt-in{display:grid;grid-template-columns:1.1fr 1fr;gap:26px;align-items:center;background:#0E1110;border:1px solid #2A322E;border-radius:22px;padding:28px;color:#F2F5F3;font-family:Outfit,system-ui,sans-serif}
.bt-k{font:600 12px 'JetBrains Mono',ui-monospace,monospace;letter-spacing:2px;color:#3EE07A}.bt h2{margin:6px 0 10px;font-size:clamp(28px,4.4vw,42px);line-height:1.04;letter-spacing:-1px;color:#F2F5F3;font-family:inherit}
.bt p{color:#A9B3AE;margin:0 0 14px;line-height:1.5}.bt-ag{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.bt-ag span{font-size:13px;padding:6px 11px;border-radius:999px;background:#171C1A;border:1px solid #2A322E}
.bt-go{display:inline-flex;align-items:center;justify-content:center;height:50px;padding:0 22px;border-radius:14px;background:#3EE07A;color:#0E1110;font-weight:800;text-decoration:none;font-size:16px}.bt-go:hover{background:#7BF0A6}
.bt-w{display:inline-block;margin-left:14px;color:#A9B3AE;font-size:14px}.bt-card{background:#171C1A;border-radius:18px;padding:18px;min-width:0}
.bt-row{display:flex;justify-content:space-between;gap:10px}.bt-s{font-size:12px;color:#A9B3AE}.bt-v{font:700 26px 'JetBrains Mono',ui-monospace,monospace;color:#3EE07A}.bt-v.w{color:#F2F5F3}
.bt-top{margin-top:14px;display:grid;gap:6px}.bt-p{display:flex;align-items:center;gap:10px;background:#0E1110;border-radius:12px;padding:9px 11px;font-size:14px}.bt-p b{width:24px;height:24px;flex:none;border-radius:7px;display:grid;place-items:center;font:700 12px 'JetBrains Mono',monospace;background:#F2F5F3;color:#0E1110}
.bt-p:first-child b{background:#FFB23E}.bt-p span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bt-p i{font-style:normal;font-family:'JetBrains Mono',monospace;color:#3EE07A}.bt-p i.dn{color:#FFB23E}
.bt-e{color:#7D8984;font-size:13px;margin-top:12px}.bt-f{font-size:12px;color:#7D8984;margin-top:14px}
@media(max-width:760px){.bt-in{grid-template-columns:1fr;padding:20px}.bt-w{display:block;margin:12px 0 0}}
</style><div class="bt-in"><div><div class="bt-k">WEEKLY AGENT BATTLE · IN THE PIT</div><h2>Your AI trades.<br>You call the shots.</h2>
<p>Pick an agent, pick a lucky coin from the week's board of five, and it trades for you all week. The best % return by Sunday 8pm ET wins. One BOOST a day is your move.</p>
<div class="bt-ag"><span>Turtle · plays it safe</span><span>Snake · balanced</span><span>Wild · huge swings</span></div>
<a class="bt-go" id="bt-go" href="''' + PIT0 + '''/battle" data-pit="/battle">Join free (practice)</a><a class="bt-w" href="''' + PIT0 + '''/battle/board" data-pit="/battle/board">Watch the leaderboard &rarr;</a>
<div class="bt-f" id="bt-f">Practice weeks: live prices, practice SOL. Nothing is paid in or out. Not financial advice.</div></div>
<div class="bt-card" id="bt-live" aria-live="polite"><div class="bt-row"><div><div class="bt-s" id="bt-pl">Practice pot</div><div class="bt-v" id="bt-pot">…</div></div><div style="text-align:right"><div class="bt-s" id="bt-tl">This week</div><div class="bt-v w" id="bt-t">…</div></div></div>
<div class="bt-top" id="bt-top"></div><div class="bt-e" id="bt-e">Loading the leaderboard…</div></div></div>
<script>(function(){
var P=((window.MC_CONFIG||{}).pit||"''' + PIT0 + '''").replace(/\\/+$/,"");if(!/^https:\\/\\/[a-z0-9.-]+$/.test(P))return;
var $=function(i){return document.getElementById(i)},esc=function(t){return String(t).replace(/[&<>"']/g,function(c){return"&#"+c.charCodeAt(0)+";"})};
function left(ms){if(ms<=0)return"0h 00m";var d=Math.floor(ms/864e5),h=Math.floor(ms%864e5/36e5),m=Math.floor(ms%36e5/6e4);return d?d+"d "+String(h).padStart(2,"0")+"h":h+"h "+String(m).padStart(2,"0")+"m"}
var NM={turtle:"Turtle",snake:"Snake",wild:"Wild"};
function load(){fetch(P+"/api/battle/board",{cache:"no-store"}).then(function(r){return r.json()}).then(function(d){
 if(!d||!d.configured||!d.week){$("bt-pot").textContent="Free";$("bt-t").textContent="Soon";$("bt-e").textContent="The first practice week is being set up.";return}
 var w=d.week,now=Date.now(),live=w.status==="running"&&now<w.endsAt,closed=w.status==="closed"||now>=w.endsAt;
 if(d.mode==="ticket"){$("bt-pl").textContent="This week's pot";$("bt-go").textContent="Enter for 0.2 SOL";$("bt-f").textContent="0.2 SOL ticket: 0.15 to the public pot wallet, 0.05 platform fee. Agents trade a practice stack, so nobody holds your SOL. Top 3 split 95% of the pot. 18+. Not financial advice."}
 $("bt-pot").textContent=(+w.pot||0).toFixed(2)+" SOL";
 $("bt-tl").textContent=closed?"Players":live?"Ends in":"Starts in";$("bt-t").textContent=closed?w.entrants:left((live?w.endsAt:w.startsAt)-now);
 var rows=(d.rows||[]).slice(0,3);
 $("bt-top").innerHTML=rows.map(function(r){var up=r.pnl>=0;return'<div class="bt-p"><b>'+r.rank+'</b><span>'+esc(r.name)+' · '+esc(NM[r.agent]||"")+' on '+esc(r.coin)+'</span><i class="'+(up?"":"dn")+'">'+(up?"+":"")+(+r.pnl).toFixed(1)+'%</i></div>'}).join("");
 $("bt-e").textContent=rows.length?(w.entrants+" playing this week"):(live?"No players yet. Be the first.":"Entries are open. Be the first on the board.");
}).catch(function(){$("bt-e").textContent="The leaderboard is in the Pit: tap Watch the leaderboard."})}
load();setInterval(function(){if(!document.hidden)load()},60000);
})();</script></section>
'''
if MARK not in s:
    s = once(s, '<section class="lpshow rev">', SEC + '<section class="lpshow rev">', 'section')

FAQ = ('<details><summary>What is the Weekly Agent Battle?</summary>A weekly contest in snakepit, the trading app next to the game. '
       'You pick an AI agent (Turtle plays it safe, Snake is balanced, Wild swings big), pick one lucky coin from the week\'s board of five, '
       'and the agent trades for you from Monday to Sunday 8pm ET. The best % return wins. You can change its bet size, take profit and stop loss '
       'in Advanced settings before the week starts, and press BOOST once a day. Right now every week is a practice week: live prices, practice SOL, '
       'free to join, and nothing is paid in or out. Real SOL weeks only open once the money can be held safely on-chain and the rules have had a legal review. '
       'Not financial advice: trading can lose money.</details>')
if 'What is the Weekly Agent Battle?' not in s:
    s = once(s, '<details><summary>What is the launchpad?</summary>', FAQ + '<details><summary>What is the launchpad?</summary>', 'faq')
if FIX not in s:
    s = once(s, '</body>', FIX + '</body>', 'fix')
wr('index.html', s)

# ------------------------------------------------------------------ launch.html (CSP: no inline scripts; lp/app.js fixes links)
L = rd('launch.html')
L = once(L, '<a href="#/launch" data-r="launch">Hatch</a><a href="https://pit.memecapes.com" id="tradeln">Trade</a>',
         '<a href="#/launch" data-r="launch">Hatch</a><a href="' + PIT0 + '/battle?from=memecapes" data-pit="/battle?from=memecapes">Battle</a><a href="https://pit.memecapes.com" id="tradeln">Trade</a>', 'lnav')
L = once(L, '<a href="#/launch" data-r="launch">Hatch</a></div>',
         '<a href="#/launch" data-r="launch">Hatch</a><a href="' + PIT0 + '/battle?from=memecapes" data-pit="/battle?from=memecapes">Battle</a></div>', 'lmob')
wr('launch.html', L)

A = rd('lp/app.js')
J = ('\n// Battle links (data-pit) follow config.js pit\n(() => { const p = String((window.MC_CONFIG || {}).pit || "").replace(/\\/+$/, ""); '
     'if (/^https:\\/\\/(pit\\.memecapes\\.com|snakepit-mu\\.vercel\\.app)$/.test(p)) document.querySelectorAll("a[data-pit]").forEach((a) => { a.href = p + a.getAttribute("data-pit"); }); })();\n')
if 'Battle links (data-pit)' not in A:
    A = A.rstrip('\n') + '\n' + J
wr('lp/app.js', A)
print('battle site: ok')
