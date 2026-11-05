#!/usr/bin/env python3
"""The Snake Hunter: the game's creator as an NPC in Gigachad Town (Albert, Nov 5: "maybe I'll even put me in the game").

He stands at the top of the town square, facing the square, wearing the MemeCape. Talk to him and he tells his story
in a few lines, with a link to the founder page on memecapes.com (#hunter). Until his own Meshy model exists
(models/hunter.json, made from Albert's photo), he uses the caped player body. When models/hunter.json is added it is
picked up automatically (HUNTER_MDL below).
Run from the repo root after patch_props.py:  python3 tools/patch_hunter.py
"""
import os

P = 'play.html'
h = open(P, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


HUNTER_MDL = 'hunter' if os.path.exists('models/hunter.json') else 'player_memecape3'

# 1. stand him north of the Gigachad Town fountain, facing the square (ry 0 = facing south)
rep("xo(...fN(CX-7,CY+6),'saw');", "xo(...fN(CX-7,CY+6),'saw');xo(...fN(CX-4,CY+1),'hunter',{ry:0});")
# 2. drawn like the other people in town (his model, idle motion)
rep("DYNPP={capes:'richw',", "DYNPP={hunter:'" + HUNTER_MDL + "',capes:'richw',")
if HUNTER_MDL == 'hunter':
    rep("MDLSC={player:1,", "MDLSC={hunter:1,player:1,")
# trees cleared round him and nudged off props like the other town NPCs (patch_npcspots' NK set)
rep("'capes','pt_npc']);", "'capes','pt_npc','hunter']);")
# 3. name, examine text and the talk
rep("saw:['Talk to','Sawmill operator'],", "saw:['Talk to','Sawmill operator'],hunter:['Talk to','The Snake Hunter'],")
rep("saw:'He turns logs into planks.',", "saw:'He turns logs into planks.',hunter:'The Snake Hunter. He built this whole place.',")
rep("saw:()=>sawUI(),", "saw:()=>sawUI(),hunter:()=>hunterUI(),")
JS = r"""function hunterUI(){M.style.display='flex';
 const L=['Name\'s the Snake Hunter. I built this place.','I once put everything I had into a project that promised me a piece of what we were building. It never delivered. I lost it all.','So I built my own. Out in the open, where anyone can check every step.','The snake ate my bag once. Now I hunt it.'];
 MB.innerHTML='<h2>The Snake Hunter</h2>'+L.map(t=>'<p style="font-size:13px;margin:0 0 8px">"'+t+'"</p>').join('')+'<a href="https://memecapes.com/#hunter" target="_blank" rel="noopener"><button>Read my story</button></a> <button id="x">Close</button>';
 $('x').onclick=()=>M.style.display='none'}
"""
rep("function sawUI(){", JS + "function sawUI(){")

open(P, 'w', encoding='utf-8').write(h)
print('snake hunter patched (model ' + HUNTER_MDL + ')')
