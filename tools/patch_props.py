#!/usr/bin/env python3
"""Old hand-built stand-ins swapped for the real Meshy props we already have (Albert, Nov 3: "not updated structures").

  flour sacks (white balls)        -> b_sacks
  hay nest (yellow octagon)        -> b_haystack, small
  prayer altar (purple mat + gem)  -> b_shrine
  broker / launchpad clerk desk    -> b_stall in front of them (the gold-topped box goes)
  sawmill block (box + cylinder)   -> b_stump with a b_log beside it
  wandering trader's sack          -> b_crates, small
  party chest (Gigachad Town)      -> b_chest                       (Meshy, Nov 5)
  butter churn                     -> b_churn
  Castle Agility Course            -> b_agi_log / net / ledge / gap / pipe, sized to the old obstacle's span
Each swap only happens when that model is in BLDK; otherwise the old drawing stays (website shots with models off).
Props go into the castle kit list (CKIT), so they are drawn, shadowed and culled like every other prop.
"""
P = 'play.html'
h = open(P).read()


def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (old[:80], h.count(old))
    h = h.replace(old, new)


# 1. the models, placed with the rest of the kit (after the wells)
A = "if(BLDK.b_well)PR.wells.forEach(a=>L.push(['b_well',a[0],a[1],0,.8]));"
rep(A, A + "XO.forEach(o=>{const x=o.x+.5,z=o.y+.5,r=o.ry||0,fx=Math.sin(r),fz=Math.cos(r),B=k=>BLDK[k];"
    "if(o.k=='sq_flour'&&B('b_sacks'))L.push(['b_sacks',x,z,r+.6,.5]);"
    "else if(o.k=='sq_nest'&&B('b_haystack'))L.push(['b_haystack',x,z,r+2.2,.5]);"
    "else if(o.k=='altar'&&B('b_shrine'))L.push(['b_shrine',x,z,r,.72]);"
    "else if((o.k=='ge'||o.k=='lpad')&&B('b_stall'))L.push(['b_stall',x+fx*1.5,z+fz*1.5,r,.95]);"
    "else if(o.k=='saw'&&B('b_stump')){L.push(['b_stump',x+fx*.9+fz*.8,z+fz*.9-fx*.8,r,.5]);if(B('b_log'))L.push(['b_log',x+fx*1.3-fz*.5,z+fz*1.3+fx*.5,r+1.4,.5])}"
    "else if(o.k=='trader'&&B('b_crates'))L.push(['b_crates',x+fx*.9-fz*.6,z+fz*.9+fx*.6,r+.4,.36])});")

# 2. the old drawings step aside when the model is there
rep("sq_nest:o=>{const x=o.x+.5", "sq_nest:o=>{if(BLDK.b_haystack)return;const x=o.x+.5")
rep("sq_flour:o=>{const x=o.x+.5", "sq_flour:o=>{if(BLDK.b_sacks)return;const x=o.x+.5")
rep("altar:o=>{const x=o.x+.5", "altar:o=>{if(BLDK.b_shrine)return;const x=o.x+.5")
rep("ge:o=>{person('b',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);boxR(", "ge:o=>{person('b',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);if(BLDK.b_stall)return;boxR(")
rep("trader:o=>{person('c',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);ball(", "trader:o=>{person('c',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);if(BLDK.b_crates)return;ball(")
rep("saw:o=>{person('p',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);boxR(", "saw:o=>{person('p',o.x+.5,o.y+.5,o.ry||0,1,0,0,0);if(BLDK.b_stump)return;boxR(")
# 3. the Nov 5 Meshy props: chest, churn and the five agility obstacles (same spots, spans and directions as the old drawings)
T = "else if(o.k=='trader'&&B('b_crates'))L.push(['b_crates',x+fx*.9-fz*.6,z+fz*.9+fx*.6,r+.4,.36])});"
rep(T, T + "if(PR.chest&&BLDK.b_chest)L.push(['b_chest',PR.chest[0],PR.chest[1],0,.85/BLDK.b_chest[2]]);"
    "{const AG=['b_agi_log','b_agi_net','b_agi_ledge','b_agi_gap','b_agi_pipe'],AGL=[3,1.8,2.1,2.6,2.9],AGC=[.5,0,.5,0,.55];"
    "XO.forEach(o=>{const x=o.x+.5,z=o.y+.5,e=BLDK[AG[o.ty]];"
    "if(o.k=='sq_churn'&&BLDK.b_churn)L.push(['b_churn',x,z,(o.ry||0)+.5,1.2/BLDK.b_churn[2]]);"
    "else if(o.k=='agi'&&e){const lx=e[0]>=e[1];L.push([AG[o.ty],x+AGC[o.ty],z,lx?0:Math.PI/2,o.ty==1?2.2/e[2]:AGL[o.ty]/(2*Math.max(e[0],e[1]))])}})}")
rep("sq_churn:o=>{const x=o.x+.5", "sq_churn:o=>{if(BLDK.b_churn)return;const x=o.x+.5")
rep("agi:o=>{const x=o.x+.5,z=o.y+.5,t=o.ty;", "agi:o=>{if(BLDK[['b_agi_log','b_agi_net','b_agi_ledge','b_agi_gap','b_agi_pipe'][o.ty]])return;const x=o.x+.5,z=o.y+.5,t=o.ty;")
rep("if(PR.chest&&vis(PR.chest[0],PR.chest[1],40))chestObj(", "if(PR.chest&&!BLDK.b_chest&&vis(PR.chest[0],PR.chest[1],40))chestObj(")
open(P, 'w').write(h)
print('props patched')
