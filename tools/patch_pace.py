#!/usr/bin/env python3
"""Calmer, real-speed movement for monsters and bots (Albert, Oct 16: "the NPCs and the bots are running around really
fast, movements super sped up").

Measured before (20 game-seconds, virtual clock): strolling monsters idled, then surged to 2.7 tiles/s to catch up with
their tile (faster than a player walks, 1.67), and their walk cycle played 1.7x faster than a player's at the same speed
(1 clip-second per tile; the player's natural cycle covers 1.67 tiles per second). Bots sprinted (3.33 tiles/s) on 70%
of their longer walks, even just wandering around town.

After: strolling monsters step every other tick (an amble, ~0.8 tiles/s) and glide at a steady pace (catch-up capped at
1.4x instead of 3x); chasing monsters keep one tile a tick. Walk cycles play at the player's rate for the distance
covered. Bots walk; only a long trip may be a jog now and then, and town (social) bots never run.

Run late in the build (after patch_wanderers, patch_npcfight and patch_trees):  python3 tools/patch_pace.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# follow(): optional catch-up range (the player and pets keep the old one)
rep("function follow(e,dt,br){const tr=e.tr||(e.tr=[]);",
    "function follow(e,dt,br,lo,hi,dv){const tr=e.tr||(e.tr=[]);")
rep("const want=br*Math.min(3,Math.max(.6,D/1.3));",
    "const want=br*Math.min(hi||3,Math.max(lo||.6,D/(dv||1.3)));")

# strolling: one step every other tick, and remember when the monster last strolled
rep("function mobRoam(gb){if(gb.rw>tickN)return[0,0];",
    "function mobRoam(gb){if(gb.rw>tickN)return[0,0];gb.rs=tickN;if(tickN%2)return[0,0];")

# monsters glide at the pace their tile moves: ~0.83 tiles/s strolling, 1.67 chasing, catch-up at most 1.4x
rep("const fm=follow(gb,dt,.9);",
    "const fm=follow(gb,dt,tickN-(gb.rs==null?-99:gb.rs)<=2?.83:1.667,.7,1.4,1.2);")

# walk cycle at the player's rate: 0.6 clip-seconds per tile (was 1)
rep("if(d)return['Walking',(gb.ph||0)/4];", "if(d)return['Walking',(gb.ph||0)/4*.6];")
rep("mcl=='Idle'?now/1000:(gb.ph||0)/4", "mcl=='Idle'?now/1000:(gb.ph||0)/4*.6")

# bots: walk. A long trip (25+ tiles) is a jog a third of the time; town bots never run.
rep("if(o.run==null)o.run=o.path.length>10&&o.R()<.7;",
    "if(o.run==null)o.run=o.role!='social'&&o.path.length>24&&o.R()<.33;")

open(PATH, 'w', encoding='utf-8').write(h)
print('Pace patch applied.')
