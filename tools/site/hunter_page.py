#!/usr/bin/env python3
"""'Built by the Snake Hunter': the founder's story page (#hunter) + a short block on the home page.

Albert (Nov 5): his lore (lost everything to a project that promised a share of what was being built and never
delivered; built his own instead, in the open) and his two YouTube channels, so people can see how far he has come.
The project he lost to is NOT named (on purpose). No dates anywhere (house rule for public copy).
Channels: fill CHANNELS below (name, url, optional uploads playlist id 'UU...' for an embedded player) and rerun;
with none filled the channel section stays hidden.
Idempotent: run from the repo root after editing:  python3 tools/site/hunter_page.py
"""
import json, re

P = 'index.html'
h = open(P, encoding='utf-8').read()

CHANNELS = [
    # {'name': 'Channel name', 'url': 'https://www.youtube.com/@handle', 'about': 'One line on what it is', 'uploads': 'UU...'},
]

CSS = """
/* hunter page (tools/site/hunter_page.py) */
.hn-hero{position:relative;text-align:center;padding:46px 0 10px}
.hn-hero h1{margin:14px 0 10px}
.hn-hero .lead{max-width:700px;margin:0 auto}
.hn-crest{width:140px;height:140px;margin:0 auto 4px;display:block;filter:drop-shadow(0 0 26px rgba(88,240,166,.35))}
.hn-lore{max-width:720px;margin:8px auto 0;font-size:18px;line-height:1.7}
.hn-lore p{margin:0 0 16px}
.hn-lore .hn-last{font-family:Cinzel,Georgia,serif;font-size:22px;color:var(--gold);text-align:center;margin-top:26px}
.hn-tl{max-width:760px;margin:0 auto;position:relative;padding-left:26px}
.hn-tl:before{content:"";position:absolute;left:8px;top:6px;bottom:6px;width:2px;background:linear-gradient(var(--red),var(--gold),#58F0A6)}
.hn-st{position:relative;margin:0 0 18px;padding:14px 16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
.hn-st:before{content:"";position:absolute;left:-24px;top:18px;width:12px;height:12px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 3px var(--bg)}
.hn-st.hn-fall:before{background:var(--red)}
.hn-st.hn-next:before{background:#58F0A6}
.hn-st small{display:block;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);font-size:11px;margin-bottom:4px}
.hn-st b{font-size:17px}
.hn-st p{margin:6px 0 0}
.hn-yt{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;max-width:960px;margin:0 auto}
.hn-ch{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--panel)}
.hn-ch .hn-vid{position:relative;padding-top:56.25%;background:#000}
.hn-ch iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.hn-ch .hn-body{padding:14px 16px}
.hn-ch h3{margin:0 0 4px}
.hn-links{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:10px}
.hn-home{display:grid;grid-template-columns:160px 1fr;gap:22px;align-items:center;max-width:860px;margin:0 auto;padding:22px;border:1px solid var(--line);border-radius:18px;background:radial-gradient(120% 90% at 0% 0%,rgba(88,240,166,.10),transparent 60%),var(--panel)}
.hn-home .hn-crest{width:150px;height:150px;margin:0}
.hn-home h2{margin:0 0 8px}
@media (max-width:640px){.hn-home{grid-template-columns:1fr;text-align:center}.hn-home .hn-crest{margin:0 auto}.hn-lore{font-size:16px}}
"""

CREST = ('<svg class="hn-crest" viewBox="0 0 150 150" aria-hidden="true"><defs><radialGradient id="hng" cx=".5" cy=".4" r=".7">'
         '<stop offset="0" stop-color="#1f3a2c"/><stop offset="1" stop-color="#0b0c0e"/></radialGradient></defs>'
         '<circle cx="75" cy="75" r="68" fill="url(#hng)" stroke="#d9a520" stroke-width="3"/>'
         '<circle cx="75" cy="75" r="60" fill="none" stroke="#d9a520" stroke-width="1" stroke-dasharray="3 6" opacity=".6"/>'
         '<g transform="translate(25 25)"><path d="M20 22 C 22 30, 30 30, 40 30 L 72 30 L 26 76 L 68 76" fill="none" stroke="#58F0A6" '
         'stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/><ellipse cx="76" cy="76" rx="12" ry="8" fill="#58F0A6"/>'
         '<circle cx="79" cy="74" r="2" fill="#0B0C0E"/></g></svg>')

STEPS = [
    ('hn-fall', 'The fall', 'Everything, gone',
     'I put everything I had into a project that promised me a piece of what we were building together. It never delivered.'),
    ('', 'The decision', 'Build it myself',
     'No more waiting on promises. If nobody would build it, I would, in the open, where anyone can check every step.'),
    ('', 'The world', 'MemeCapes',
     'A free browser MMO where the memes are the monsters: towns, quests, skills to level 100, trading, friends and the MemeCape to earn.'),
    ('', 'The den', 'snakepit',
     'A trading app with a flat, low fee, coin launches with a Sniper Shield and Snake Bite burns, and MemeSnake, the AI that runs the crews.'),
    ('', 'The armoury', 'Gearing up',
     'Nine armour sets with swords to match, capes worn over armour, and a skin every month.'),
    ('hn-next', 'Next', 'Still building',
     'Ranged and Magic, a PvP world and our own launchpad. Every part goes live only when it really works.'),
]


def page():
    st = ''.join(f'<div class="hn-st {c}"><small>{a}</small><b>{b}</b><p class="mute">{t}</p></div>' for c, a, b, t in STEPS)
    yt = ''
    if CHANNELS:
        cards = ''
        for ch in CHANNELS:
            vid = (f'<div class="hn-vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/videoseries?list={ch["uploads"]}" '
                   f'title="{ch["name"]}" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>') if ch.get('uploads') else ''
            cards += (f'<div class="hn-ch">{vid}<div class="hn-body"><h3>{ch["name"]}</h3><p class="mute">{ch.get("about", "")}</p>'
                      f'<a class="btn ghost" href="{ch["url"]}" target="_blank" rel="noopener">Watch on YouTube</a></div></div>')
        yt = ('<section><div class="sec-title"><h2>Watch the journey</h2></div><p class="lead" style="text-align:center">'
              'Two channels, from the first steps to now. See for yourself how far it has come.</p>'
              f'<div class="hn-yt">{cards}</div></section>')
    return f'''<main class="pg" id="pg-hunter" hidden><a class="pgback" href="#home">&larr; Home</a>
<section class="hn-hero">{CREST}<span class="pill gold">The founder</span><h1>Built by the Snake Hunter</h1>
<p class="lead">MemeCapes and snakepit are made by one person who learned the hard way what a broken promise costs.</p></section>
<section><div class="hn-lore">
<p>I put everything I had into a project that promised me a piece of what we were building together. I believed in it. I gave it my time and my money, and I watched it fall apart. No product. No payout. Everything I had ever worked for, gone.</p>
<p>Most people walk away after that. I didn't. If nobody was going to build what they promised, I would build it myself, and do it in the open: every official wallet public, every burn on-chain, nothing promised that isn't already live.</p>
<p>That is how MemeCapes and snakepit were born. A game and a trading den, built by someone who has been on the losing side and refuses to put anyone else there.</p>
<p class="hn-last">The snake ate my bag once. Now I hunt it.</p>
</div></section>
<section><div class="sec-title"><h2>How far it has come</h2></div><div class="hn-tl">{st}</div></section>
{yt}
<section><div class="hn-links"><a class="btn gold glow" href="play.html">Play MemeCapes free</a><a class="btn ghost" href="https://pit.memecapes.com/" data-pit="/">Open snakepit</a><a class="btn ghost" href="https://t.me/memecapes" target="_blank" rel="noopener">Telegram</a><a class="btn ghost" href="https://x.com/memecapes" target="_blank" rel="noopener">X</a></div></section>
</main>'''


HOME = (f'<section id="hn-home"><div class="hn-home rev">{CREST}<div><span class="pill gold">The founder</span>'
        '<h2>Built by the Snake Hunter</h2><p class="mute">He lost everything to a project that never delivered. '
        'So he built his own, in the open, where anyone can check every step.</p>'
        '<a class="btn ghost" href="#hunter">Read his story</a></div></div></section>\n')

# strip an earlier run, then add everything again
h = re.sub(r'\n/\* hunter page \(tools/site/hunter_page.py\) \*/.*?(?=\n/\*|\n</style>)', '', h, count=1, flags=re.S)
h = re.sub(r'<main class="pg" id="pg-hunter" hidden>.*?</main>', '', h, count=1, flags=re.S)
h = re.sub(r'<section id="hn-home">.*?</section>\n', '', h, count=1, flags=re.S)
h = h.replace('<a href="#hunter">Snake Hunter</a>', '')

assert h.count('</style>') >= 1
i = h.find('</style>')
h = h[:i] + CSS + h[i:]
A = '<main class="pg" id="pg-security" hidden>'
assert h.count(A) == 1
h = h.replace(A, page() + '\n' + A)
B = '<section><div class="final rev"><h2>Bonk is waiting in the forest.</h2>'
assert h.count(B) == 1
h = h.replace(B, HOME + B)
N = '<a href="#support">Support</a>'
assert h.count(N) == 1
h = h.replace(N, '<a href="#hunter">Snake Hunter</a>' + N)
T = "security:'Security',support:'Support'}"
assert h.count(T) == 1 or "hunter:'Snake Hunter'" in h
h = h.replace(T, "security:'Security',support:'Support',hunter:'Snake Hunter'}")
assert not re.search(r'\b20[23]\d\b', re.sub(r'data:[^"\')]+', '', page() + HOME)), 'no dates on this page'
open(P, 'w', encoding='utf-8').write(h)
print('hunter page written;', len(CHANNELS), 'channels')
