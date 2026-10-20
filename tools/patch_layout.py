#!/usr/bin/env python3
"""The MemeCapes screen layout (desktop, wider than 640px). Our own arrangement, not a copy of anyone's:

- One fixed velvet-and-gold column on the right. The 3D view stops at its edge, so nothing hides behind it.
- The minimap is the cape medallion: a big round map in a beaded gold ring, with the compass seal as its crown.
- Health, Prayer, Walk and Spec are four gold gauges in a straight row under the medallion; the XP bar below.
- The panel's tabs are one vertical ribbon of picture bookmarks down its left edge, so labels never overflow.
- The chat scroll gets a ribbon of filters on top: All, Game, Chat.
Phones keep the current layout. Run from the repo root after patch_voice.py:  python3 tools/patch_layout.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


G = 'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"'
ICON = {
    'inv': f'<svg viewBox="0 0 24 24" {G}><path d="M8 7c0-2 1.5-3 4-3s4 1 4 3"/><path d="M6 8h12l1.5 11a2 2 0 0 1-2 2.2H6.5a2 2 0 0 1-2-2.2z"/><path d="M9 12h6"/></svg>',
    'sk': f'<svg viewBox="0 0 24 24" {G}><path d="M4 20V13M10 20V8M16 20v-5M22 20H2"/><path d="M15 4l2 2 4-4" transform="translate(-1 2)"/></svg>',
    'eq': f'<svg viewBox="0 0 24 24" {G}><path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z"/><path d="M12 8v8M8.5 11.5h7"/></svg>',
    'qs': f'<svg viewBox="0 0 24 24" {G}><path d="M6 4h10a2 2 0 0 1 2 2v12a2 2 0 0 0 2 2H8a2 2 0 0 1-2-2z"/><path d="M6 4a2 2 0 0 0-2 2v2h2M9 9h6M9 13h6"/></svg>',
    'pot': f'<svg viewBox="0 0 24 24" {G}><circle cx="12" cy="12" r="8.5"/><path d="M14.5 9.2c-.6-.8-1.5-1.2-2.5-1.2-1.4 0-2.5.8-2.5 2s1.1 1.6 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1 0-1.9-.4-2.5-1.2M12 6.5v11"/></svg>',
    'more': f'<svg viewBox="0 0 24 24" {G}><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/><path d="M3 5h18M3 19h18"/></svg>',
}
NAMES = {'inv': 'Bag', 'sk': 'Skills', 'eq': 'Gear', 'qs': 'Quests', 'pot': '$CAPES', 'more': 'More'}
old_tabs = ('<div id="tabs"><div data-t="inv" class="on">Bag</div><div data-t="sk">Skills</div><div data-t="eq">Gear</div>'
            '<div data-t="qs">Quests</div><div data-t="pot">$CAPES</div><div data-t="more">More</div></div>')
new_tabs = '<div id="tabs">' + ''.join(
    f'<div data-t="{k}"{" class=\"on\"" if k == "inv" else ""} title="{NAMES[k]}">{ICON[k]}<span>{NAMES[k]}</span></div>' for k in NAMES) + '</div>'
rep(old_tabs, new_tabs)

# the column frame behind the HUD
rep('<canvas id="gl"></canvas>', '<canvas id="gl"></canvas><div id="col"><div id="ring"></div></div>')

# the chat ribbon: All / Game / Chat
rep('<div id="chat"><div id="clog">', '<div id="chat"><div id="crib"><button data-cf="all" class="on">All</button><button data-cf="game">Game</button><button data-cf="chat">Chat</button></div><div id="clog">')
rep("function say(t,c){chat.push('<div style=\"color:'+(c||'#000')+'\">'+t+'</div>');",
    "function say(t,c){chat.push('<div'+(c=='#1a1aa0'?' class=\"pl\"':'')+' style=\"color:'+(c||'#000')+'\">'+t+'</div>');")
rep("document.querySelectorAll('#tabs div').forEach(d=>d.onclick=",
    "document.querySelectorAll('#crib [data-cf]').forEach(b=>b.onclick=()=>{document.querySelectorAll('#crib [data-cf]').forEach(x=>x.classList.toggle('on',x===b));$('cl').className='f-'+b.dataset.cf;const L=$('clog');L.scrollTop=L.scrollHeight});"
    "document.querySelectorAll('#tabs div').forEach(d=>d.onclick=")

# on a desktop the panel never folds away (the column is always there); a phone still folds it
rep("if(pOpen&&tab==d.dataset.t)pOpen=false;", "if(pOpen&&tab==d.dataset.t&&innerWidth<=640)pOpen=false;")

# the 3D view stops at the column
rep("CW=innerWidth;CH=", "CW=(!mob&&started)?innerWidth-260:innerWidth;CH=")

# short gauge labels on a desktop (the full name is in each gauge's tooltip)
WIDE = "innerWidth>640"
rep("$('hpt').textContent='HP '+st.hp+'/'+hpMax();", "$('hpt').textContent=(" + WIDE + "?'\\u2665 ':'HP ')+st.hp+'/'+hpMax();")
rep("$('rt').textContent=(st.run?'Run ':'Walk ')+Math.floor(st.en)+'%';", "$('rt').textContent=(" + WIDE + "?(st.run?'\\u00bb ':'\\u203a '):(st.run?'Run ':'Walk '))+Math.floor(st.en)+'%';")
rep("$('prt').textContent='Prayer '+st.pp+'/'+ppMax();", "$('prt').textContent=(" + WIDE + "?'\\u2726 ':'Prayer ')+st.pp+'/'+ppMax();")
rep("$('spt').textContent='Spec '+st.spec+'%';", "$('spt').textContent=(" + WIDE + "?'\\u2694 ':'Spec ')+st.spec+'%';")
rep('<div class="orb" id="hpo" style="top:140px;cursor:pointer">', '<div class="orb" id="hpo" title="Health (tap to eat)" style="top:140px;cursor:pointer">')
rep('<div class="orb" id="pro" style="top:164px;cursor:pointer">', '<div class="orb" id="pro" title="Prayer (tap for quick prayers)" style="top:164px;cursor:pointer">')
rep('<div class="orb" style="top:188px" id="run">', '<div class="orb" style="top:188px" id="run" title="Walk / run (tap to switch)">')
rep('<div class="orb" id="spo" style="top:212px;cursor:pointer">', '<div class="orb" id="spo" title="Special attack" style="top:212px;cursor:pointer">')

CSS = r"""
/* ---- the MemeCapes layout */
#col,#crib{display:none}
#tabs svg{display:none}
#crib{gap:4px;margin:-4px -6px 4px;padding:3px 6px;background:linear-gradient(#7a1420,#4a0a12);border-bottom:1px solid #d9a520}
#crib button{font:700 10px/1 Cinzel,Georgia,serif;color:#ffe9b0;background:none;border:1px solid transparent;border-radius:10px;padding:3px 10px;cursor:pointer}
#crib button.on{background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);color:#2a1400;border-color:#6b4a06}
#cl.f-chat>div:not(.pl),#cl.f-game>.pl{display:none}
body.pre #col{display:none!important}
#xpo{display:none!important}
@media (min-width:641px){
 #crib{display:flex}
 #col{display:block;position:fixed;top:0;right:0;bottom:0;width:260px;z-index:3;background:radial-gradient(160% 40% at 50% 0%,#5a1220 0%,#3b0b14 55%,#24060c 100%);border-left:2px solid #d9a520;box-shadow:-2px 0 0 #15030a,-8px 0 24px #0009}
 #ring{position:absolute;top:23px;right:52px;width:162px;height:162px;border-radius:50%;border:5px dotted #ffd23f;box-shadow:0 0 0 3px #6b4a06,inset 0 0 0 3px #6b4a06,0 0 22px #ffd23f44;box-sizing:border-box}
 #mm{top:26px!important;right:55px!important;width:150px!important;height:150px!important;z-index:4;border:3px solid #d9a520;box-shadow:0 0 0 2px #15030a}
 #cmp{top:6px!important;right:117px!important;width:32px;height:32px;z-index:5;border-radius:50% 50% 45% 45%;box-shadow:0 0 0 2px #15030a,0 0 10px #ffd23f66;line-height:28px}
 #wmb{top:150px!important;right:200px!important;width:48px;z-index:5}
 .orb{z-index:4;width:58px!important;right:auto;top:188px!important;height:22px;line-height:20px;font-size:10px;letter-spacing:0;text-align:center}
 #hpo{right:192px!important}#pro{right:130px!important}#run{right:68px!important}#spo{right:6px!important}
 #panel{top:218px;bottom:0;right:0;height:auto!important;width:260px!important;padding:6px 6px 6px 54px;z-index:4;border:0;border-top:1px solid #d9a52066;background:linear-gradient(#2b0810,#1f0509);box-shadow:none}
 #panel.c #pc{display:block}
 #pc .g{grid-template-columns:repeat(4,1fr);gap:4px}
 #pc .s{height:auto;aspect-ratio:1}
 #pc .s svg{width:82%!important;height:82%!important}
 #pc .s small{font-size:11px}
 #panel [data-sub]{font-size:9px!important;overflow-wrap:normal!important;letter-spacing:0}
 #pc{height:100%;max-height:none!important;overflow-y:auto;overflow-x:hidden}
 #tabs{left:0;top:0;bottom:0;right:auto;width:48px;height:auto;flex-direction:column;border-top:0;border-right:1px solid #d9a52066;background:#15030a}
 #tabs div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;line-height:1!important;border-top:0!important;border-left:3px solid transparent;font-size:8px!important;padding:0 1px}
 #tabs div svg{display:block;width:22px;height:22px}
 #tabs div.on{border-left-color:#6b4a06}
 #tabs div:not(.on):hover{color:#ffe9b0;background:#d9a52018}
 #chat{bottom:0;left:0;width:min(640px,calc(100vw - 270px))!important;height:164px}
 #modal{right:260px}
 #mb{max-height:calc(100vh - 40px)}
}
"""
k = h.find('</style>', h.find('</style>') + 1)
assert k > 0
h = h[:k] + CSS + h[k:]

open(PATH, 'w', encoding='utf-8').write(h)
print('layout patch applied')
