#!/usr/bin/env python3
"""'Built by the Snake Hunter': the founder's page (#hunter) + a short block on the home page.

Albert (Nov 5): his story (lost everything to a project that promised a share of what was being built and never
delivered; built his own instead, in the open), everything he has finished so far, and his two YouTube channels.
Rules: the project he lost to is NOT named; no dates; only things that are LIVE (nothing "coming soon" or "next").
Layout: hero (struck-through broken promise -> "So I built all of it myself", jump buttons), story with his photo,
"What I built" (MemeCapes with real counts, snakepit, Stream and Watch, then smaller links), YouTube (only when
CHANNELS is filled), why it's in the open. Every link opens something that works today.
His photo stays OUT of the public repo until he says "make it live": HUNTER_FACE=/path/face.webp uses it; without it
the crest is the snakepit logo in a gold ring.
Idempotent: run from the repo root after editing:  [HUNTER_FACE=...] python3 tools/site/hunter_page.py
"""
import base64, os, re

P = 'index.html'
h = open(P, encoding='utf-8').read()

CHANNELS = [
    # {'name': 'Channel name', 'url': 'https://www.youtube.com/@handle', 'about': 'One line on what it is', 'uploads': 'UU...'},
]

CSS = """
/* hunter page (tools/site/hunter_page.py) */
.hn{--hn-red:#c62828;--hn-mint:#58f0a6}
.hn-hero{padding:48px 0 30px;max-width:1000px}
.hn-who{display:flex;align-items:center;gap:14px;margin-bottom:28px}
.hn-who .hn-crest{width:72px;height:72px}
.hn-who b{display:block;font-family:Cinzel,Georgia,serif;font-size:20px;color:var(--gold)}
.hn-who span{color:var(--mute);font-size:15px}
.hn-say{font-family:Cinzel,Georgia,serif;font-weight:800;line-height:1.1;margin:0;font-size:clamp(32px,5.6vw,68px);letter-spacing:-.005em}
.hn-broke{display:block;font-size:.62em;line-height:1.3;color:#cdbb98}
.hn-broke s{text-decoration:none;opacity:.75;background:linear-gradient(var(--hn-red),var(--hn-red)) no-repeat 0 56%/100% .1em;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.hn-built{display:block;color:var(--gold);margin-top:.12em}
.hn-sub{max-width:640px;font-size:19px;line-height:1.6;margin:24px 0 0}
.hn-jump{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}
.hn-jump button,.hn-jump a{font:inherit;font-weight:800;font-size:15px;padding:11px 18px;border-radius:999px;cursor:pointer;text-decoration:none;border:1px solid var(--gold2);background:rgba(34,24,14,.7);color:var(--gold)}
.hn-jump .hn-go{background:linear-gradient(180deg,#ffd877,#e8b23c);color:#2b1d05;border-color:transparent}
.hn-jump button:hover,.hn-jump a:hover,.hn-acts a:hover{filter:brightness(1.12)}
.hn a:focus-visible,.hn button:focus-visible{outline:3px solid var(--hn-mint);outline-offset:3px}
.hn-story{display:grid;grid-template-columns:240px 1fr;gap:44px;align-items:start;max-width:1000px;padding:44px 0}
.hn-photo{position:sticky;top:100px}
.hn-photo .hn-crest{width:220px;height:220px}
.hn-story h2,.hn-wall h2,.hn-why h2{margin:0 0 14px}
.hn-story p{font-size:18px;line-height:1.75;margin:0 0 18px;max-width:62ch}
.hn-turn{font-family:Cinzel,Georgia,serif;font-size:22px;color:var(--gold);line-height:1.4;margin-top:26px}
.hn-wall{padding:44px 0}
.hn-note{color:var(--mute);margin:-6px 0 26px;font-size:17px}
.hn-game{display:grid;grid-template-columns:minmax(0,290px) 1fr;border:1px solid var(--line);border-radius:22px;overflow:hidden;background:var(--panel)}
.hn-pic{background:#0d0905;min-height:320px;position:relative}
.hn-pic img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 25%;display:block}
.hn-body{padding:28px 30px}
.hn-flat{padding:0}
.hn h3{font-family:Cinzel,Georgia,serif;font-size:28px;margin:0 0 6px;color:var(--gold)}
.hn-body p,.hn-stage p,.hn-pit p{margin:0 0 18px;font-size:17px;line-height:1.6;max-width:60ch}
.hn-count{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 18px;margin:0 0 20px;padding:0;list-style:none}
.hn-count li{border-left:3px solid var(--gold2);padding:0 0 0 12px;line-height:1.3}
.hn-count b{display:block;font-family:Cinzel,Georgia,serif;font-size:30px;color:var(--txt)}
.hn-count span{color:var(--mute);font-size:15px}
.hn-also{color:var(--mute)}
.hn-acts{display:flex;flex-wrap:wrap;gap:10px}
.hn-acts a{font-weight:800;font-size:15px;padding:10px 16px;border-radius:10px;text-decoration:none;border:1px solid var(--gold2);color:var(--gold);background:rgba(20,14,8,.5)}
.hn-acts a.hn-main{background:linear-gradient(180deg,#ffd877,#e8b23c);color:#2b1d05;border-color:transparent}
.hn-pair{display:grid;grid-template-columns:1.3fr 1fr;gap:18px;margin-top:18px}
.hn-pit{border:1px solid rgba(88,240,166,.35);border-radius:22px;background:linear-gradient(160deg,#0f1a14,#0b0f0c 70%);padding:28px 30px}
.hn-pit h3{color:var(--hn-mint)}
.hn-mark{width:44px;height:44px;display:block;margin-bottom:8px}
.hn-feats{list-style:none;margin:0 0 20px;padding:0}
.hn-feats li{padding:10px 0;border-top:1px solid rgba(88,240,166,.14);font-size:16px;line-height:1.5}
.hn-feats li:first-child{border-top:0;padding-top:0}
.hn-feats b{color:#e9fff4}
.hn-pit .hn-acts a{border-color:rgba(88,240,166,.5);color:var(--hn-mint);background:transparent}
.hn-pit .hn-acts a.hn-main{background:var(--hn-mint);color:#062014}
.hn-stage{border:1px solid var(--line);border-radius:22px;background:var(--panel);padding:28px 30px;display:flex;flex-direction:column}
.hn-live{display:inline-flex;align-items:center;gap:8px;font-weight:800;font-size:14px;color:#ffd7d7;margin-bottom:12px}
.hn-live i{width:10px;height:10px;border-radius:50%;background:#ff4545;box-shadow:0 0 0 4px rgba(255,69,69,.2)}
.hn-stage .hn-acts{margin-top:auto}
.hn-gold li{border-top-color:var(--line)}
.hn-gold b{color:var(--txt)}
.hn-more{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:18px}
.hn-more a{display:block;text-decoration:none;color:var(--txt);border:1px solid var(--line);border-radius:14px;padding:16px;background:rgba(34,24,14,.6)}
.hn-more a:hover{border-color:var(--gold2)}
.hn-more b{display:block;font-size:17px;color:var(--gold);margin-bottom:4px}
.hn-more span{display:block;color:var(--mute);font-size:14.5px;line-height:1.45}
.hn-skins{display:flex!important;gap:6px;margin-top:10px}
.hn-skins img{width:40px;height:40px;border-radius:8px;display:block;background:#1a1209}
.hn-yt{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}
.hn-ch{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--panel)}
.hn-vid{position:relative;padding-top:56.25%;background:#000}
.hn-vid iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.hn-cb{padding:14px 16px}
.hn-why{max-width:760px;padding:48px 0 64px}
.hn-why p{font-size:18px;line-height:1.7;margin:0 0 24px}
.hn-crest{width:140px;height:140px;margin:0;display:block;position:relative;flex:none}
.hn-face img{width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;border:3px solid #d9a520;box-shadow:0 0 0 5px rgba(217,165,32,.16),0 0 28px rgba(88,240,166,.25)}
.hn-badge{position:absolute;right:-3px;bottom:-2px;width:34%;height:34%;filter:drop-shadow(0 2px 6px rgba(0,0,0,.6))}
.hn-home{display:grid;grid-template-columns:150px 1fr;gap:24px;align-items:center;max-width:860px;margin:0 auto;padding:22px;border:1px solid var(--line);border-radius:18px;background:var(--panel)}
.hn-home h2{margin:0 0 8px}
@media (prefers-reduced-motion:no-preference){.hn-broke s{animation:hnCut .8s cubic-bezier(.6,0,.2,1) .6s both}}
@keyframes hnCut{from{background-size:0% .1em}to{background-size:100% .1em}}
@media (max-width:900px){.hn-pair{grid-template-columns:1fr}.hn-more{grid-template-columns:repeat(2,minmax(0,1fr))}.hn-count{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:720px){.hn-story{grid-template-columns:1fr;gap:0}.hn-photo{display:none}
.hn-game{grid-template-columns:1fr}.hn-pic{min-height:0;height:300px}.hn-body,.hn-pit,.hn-stage{padding:22px 18px}.hn-flat{padding:0}
.hn-sub,.hn-story p{font-size:17px}.hn-home{grid-template-columns:1fr;text-align:center}.hn-home .hn-crest{margin:0 auto}}
@media (max-width:420px){.hn-more{grid-template-columns:1fr}}
"""

FACE = os.environ.get('HUNTER_FACE', '')
LOGO_G = ('<path d="M20 22 C 22 30, 30 30, 40 30 L 72 30 L 26 76 L 68 76" fill="none" stroke="#58F0A6" stroke-width="11" '
          'stroke-linecap="round" stroke-linejoin="round"/><ellipse cx="76" cy="76" rx="12" ry="8" fill="#58F0A6"/>'
          '<circle cx="79" cy="74" r="2" fill="#0B0C0E"/>')
LOGO = ('<svg class="hn-badge" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="48" fill="#0B0C0E" '
        'stroke="#d9a520" stroke-width="3"/><g transform="translate(5 3) scale(.9)">' + LOGO_G + '</g></svg>')
MARK = '<svg class="hn-mark" viewBox="0 0 100 100" aria-hidden="true">' + LOGO_G + '</svg>'
if FACE and os.path.exists(FACE):
    CREST = ('<div class="hn-crest hn-face"><img src="data:image/webp;base64,' + base64.b64encode(open(FACE, 'rb').read()).decode()
             + '" alt="The Snake Hunter">' + LOGO + '</div>')
else:
    CREST = ('<svg class="hn-crest" viewBox="0 0 150 150" aria-hidden="true"><circle cx="75" cy="75" r="68" fill="#13201a" '
             'stroke="#d9a520" stroke-width="3"/><g transform="translate(25 25)">' + LOGO_G + '</g></svg>')

GO = "document.getElementById('{}').scrollIntoView({{behavior:'smooth',block:'start'}})"
SKINS = ['cs_laser_eyes', 'cs_wen_lambo', 'cs_diamond_hands', 'cs_moon_night', 'sk_rocket']
PIT = 'https://pit.memecapes.com'


def page():
    yt = ytbtn = ''
    if CHANNELS:
        cards = ''
        for ch in CHANNELS:
            vid = ('<div class="hn-vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/videoseries?list='
                   + ch['uploads'] + '" title="' + ch['name'] + '" allow="encrypted-media; picture-in-picture" allowfullscreen>'
                   '</iframe></div>') if ch.get('uploads') else ''
            cards += ('<div class="hn-ch">' + vid + '<div class="hn-cb"><h3>' + ch['name'] + '</h3><p class="mute">'
                      + ch.get('about', '') + '</p><div class="hn-acts"><a href="' + ch['url']
                      + '" target="_blank" rel="noopener">Watch on YouTube</a></div></div></div>')
        yt = ('<section class="hn-wall" id="hn-yt"><h2>Watch the journey</h2><p class="hn-note">Every step on camera, '
              'from the first build to today.</p><div class="hn-yt">' + cards + '</div></section>')
        ytbtn = '<button type="button" onclick="' + GO.format('hn-yt') + '">Watch the journey</button>'
    skins = ''.join('<img src="models/skins/thumbs/' + k + '.jpg" alt="" width="40" height="40">' for k in SKINS)
    out = """<main class="pg hn" id="pg-hunter" hidden><a class="pgback" href="#home">&larr; Home</a>
<section class="hn-hero">
<div class="hn-who">CREST<div><b>The Snake Hunter</b><span>Founder of MemeCapes and snakepit</span></div></div>
<h1 class="hn-say"><span class="hn-broke"><s>They promised me a piece of what we were building.</s></span><span class="hn-built">So I built all of it myself.</span></h1>
<p class="hn-sub">I lost everything I had ever worked for to a project that never delivered. This is what I made after: a game, a trading app, a launchpad and a streaming platform. All of it is live, and all of it is out in the open.</p>
<div class="hn-jump"><button type="button" class="hn-go" onclick="GO_BUILT">See what I built</button><button type="button" onclick="GO_STORY">Read my story</button>YTBTN<a href="play.html">Play free</a></div>
</section>
<section class="hn-story" id="hn-story"><div class="hn-photo">CREST</div><div>
<h2>How it started</h2>
<p>I put everything I had into a project that promised me a piece of what we were building together. I believed in it. I gave it my time and my money, and I watched it fall apart. No product. No payout. Everything I had ever worked for, gone.</p>
<p>Most people walk away after that. I didn't. If nobody was going to build what they promised, I would build it myself, and do it where anyone can check: every official wallet public, every burn on-chain, nothing promised that isn't already working.</p>
<p>So I started building, one piece at a time, and I haven't stopped.</p>
<p class="hn-turn">The snake ate my bag once. Now I hunt it.</p>
</div></section>
<section class="hn-wall" id="hn-built"><h2>What I built</h2><p class="hn-note">Every link here opens something that works today.</p>
<article class="hn-game"><div class="hn-pic"><img src="media/loading_cape.webp" alt="A MemeCapes hero wearing the MemeCape" loading="lazy" width="510" height="950"></div>
<div class="hn-body"><h3>MemeCapes</h3><p>A free 3D MMO in your browser where the memes are the monsters. No download: play on your phone or computer, alone or with friends.</p>
<ul class="hn-count"><li><b>8</b><span>towns and Castle Gigachad</span></li><li><b>30+</b><span>meme monsters</span></li><li><b>15</b><span>skills to level 100</span></li>
<li><b>10</b><span>quests</span></li><li><b>9</b><span>armour sets and 9 swords</span></li><li><b>31</b><span>cape and weapon skins</span></li></ul>
<p class="hn-also">Plus trading between players, friends and private messages, and the MemeCape, the prize at the top of every skill.</p>
<div class="hn-acts"><a class="hn-main" href="play.html">Play free</a><a href="#bestiary">Meet the monsters</a><a href="#towns">See the towns</a></div></div></article>
<div class="hn-pair">
<article class="hn-pit">MARK<h3>snakepit</h3><p>A Solana trading app built for memecoins.</p>
<ul class="hn-feats"><li><b>Trade any coin</b> for a flat 0.4% fee, with no tiers.</li><li><b>Hatch</b>, our launchpad: launch your own coin with a sniper fee and a Snake Bite burn.</li>
<li><b>Acid Pit</b>: buy a coin and burn it in the same tap.</li><li><b>Weekly Agent Battle</b> and <b>Beat the Boss</b>: pick an AI trader and climb the board.</li>
<li><b>Your wallet</b>: make one with your email, then send, receive, or buy SOL with a card.</li></ul>
<div class="hn-acts"><a class="hn-main" href="PIT/" data-pit="/">Open snakepit</a><a href="PIT/hatch" data-pit="/hatch">Launch a coin</a></div></article>
<article class="hn-stage"><span class="hn-live"><i></i>Live streaming</span><h3>Stream and Watch</h3>
<p>Our own streaming platform, built into the launch site.</p>
<ul class="hn-feats hn-gold"><li><b>Go live</b> with a stream pass, right from your browser.</li><li><b>Keep 100%</b> of your tips and subs.</li><li><b>Chat sits beside the video</b>, and the newest coins and live trades are one tap away.</li></ul>
<div class="hn-acts"><a class="hn-main" href="launch.html#/stream">Start streaming</a><a href="launch.html#/watch">Watch now</a></div></article>
</div>
<div class="hn-more">
<a href="memesnake/"><b>MemeSnake</b><span>The AI agent that runs the crews. Watch it work live.</span></a>
<a href="#security"><b>Security</b><span>Guards on the game around the clock and a public check of every official wallet.</span></a>
<a href="#support"><b>Support</b><span>266 answers you can search, however you ask.</span></a>
<a href="#capes"><b>Skin of the Month</b><span>A new cape or weapon skin every month.</span><span class="hn-skins">SKINS</span></a>
</div></section>
YT
<section class="hn-why"><h2>Why it's all in the open</h2>
<p>I know what it costs when someone promises and doesn't deliver. So I only show what already works, every official wallet is listed in public, and every burn can be checked on-chain. If it's on this page, you can use it right now.</p>
<div class="hn-acts"><a class="hn-main" href="play.html">Play MemeCapes free</a><a href="PIT/" data-pit="/">Open snakepit</a><a href="https://t.me/memecapes" target="_blank" rel="noopener">Join the Telegram</a><a href="https://x.com/memecapes" target="_blank" rel="noopener">Follow on X</a></div>
</section>
</main>"""
    for k, v in [('GO_BUILT', GO.format('hn-built')), ('GO_STORY', GO.format('hn-story')), ('YTBTN', ytbtn), ('YT', yt),
                 ('MARK', MARK), ('SKINS', skins), ('PIT', PIT), ('CREST', CREST)]:
        out = out.replace(k, v)
    return out


HOME = ('<section id="hn-home"><div class="hn-home rev">' + CREST + '<div>'
        '<h2>Built by the Snake Hunter</h2><p class="mute">He lost everything to a project that never delivered. '
        'So he built his own: a game, a trading app, a launchpad and a streaming platform, all live.</p>'
        '<a class="btn ghost" href="#hunter">Read his story</a></div></div></section>\n')

# strip an earlier run, then add everything again
h = re.sub(r'\n/\* hunter page \(tools/site/hunter_page.py\) \*/.*?(?=\n/\*|\n</style>)', '', h, count=1, flags=re.S)
h = re.sub(r'<main class="pg[^"]*" id="pg-hunter" hidden>.*?</main>', '', h, count=1, flags=re.S)
h = re.sub(r'<section id="hn-home">.*?</section>\n', '', h, count=1, flags=re.S)
h = h.replace('<a href="#hunter">Snake Hunter</a>', '')

assert h.count('</style>') >= 1
i = h.find('</style>')
h = h[:i] + CSS + h[i:]
A = '<main class="pg" id="pg-security" hidden>'
assert h.count(A) == 1
pg = page()
assert not re.search(r'\b(GO_|YTBTN|SKINS|CREST)\b', pg)
h = h.replace(A, pg + '\n' + A)
B = '<section><div class="final rev"><h2>Bonk is waiting in the forest.</h2>'
assert h.count(B) == 1
h = h.replace(B, HOME + B)
N = '<a href="#support">Support</a>'
assert h.count(N) == 1
h = h.replace(N, '<a href="#hunter">Snake Hunter</a>' + N)
T = "security:'Security',support:'Support'}"
assert h.count(T) == 1 or "hunter:'Snake Hunter'" in h
h = h.replace(T, "security:'Security',support:'Support',hunter:'Snake Hunter'}")
plain = re.sub(r'data:[^"\')]+', '', pg + HOME)
assert not re.search(r'\b20[23]\d\b', plain), 'no dates on this page'
assert not re.search(r'(?i)coming soon|in progress|still building|planned', plain), 'only live things on this page'
open(P, 'w', encoding='utf-8').write(h)
print('hunter page written;', len(CHANNELS), 'channels; photo' if FACE else '; logo crest')
