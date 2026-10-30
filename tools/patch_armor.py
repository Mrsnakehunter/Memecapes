#!/usr/bin/env python3
"""Armour sets you can wear: nine full outfits (Defence 1, 10, 20 ... 80), each a real 3D body.

Wearing a set (Body slot) swaps your character's whole 3D body for that armour's model (models/arm_lvNN.json, made
from Meshy with tools/glb2rig.py --rig28 + tools/armor_clips.py), with every motion, held weapon and shield working as
before. Other players see it too: the armour rides along in the 'c' look field as '@armNN'.
  - ARMS: item key -> [model key, Defence level needed]. Sets whose model isn't built yet still work as items (stats,
    level, wear/remove) and you simply keep your normal body until the model exists.
  - A cape is not drawn over armour yet (capes are part of the caped bodies); it stays equipped.
Run from the repo root after patch_memecape.py:  python3 tools/patch_armor.py
"""
import os
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# name, colour, examine, rarity, sell, armour bonus, Defence level
SETS = [
    ('arm01', 'Paper Hands outfit', '#c9b48a', 'Patched cloth, rope and a brave heart.', 0, 4, 2, 1),
    ('arm10', 'Copper Coin armour', '#c87533', 'Hammered copper with coin rivets.', 1, 20, 5, 10),
    ('arm20', 'HODL Iron armour', '#6f747c', 'Heavy iron. Never lets go.', 1, 45, 9, 20),
    ('arm30', 'Bull Steel armour', '#c9ced6', 'Bright steel with little bull horns.', 2, 80, 13, 30),
    ('arm40', 'Gold Rush armour', '#e0b545', 'Steel plate trimmed in gold, a red tabard.', 2, 130, 18, 40),
    ('arm50', 'Diamond Hands armour', '#8fd3ff', 'Faceted crystal plates set in silver.', 3, 200, 24, 50),
    ('arm60', 'Whale Plate armour', '#1f6b78', 'Ocean plate with whale-fin shoulders.', 3, 280, 30, 60),
    ('arm70', 'Moonforged armour', '#dfe6f5', 'Silver-white plate that glows like the moon.', 4, 380, 37, 70),
    ('arm80', 'Legend of the Meme armour', '#1a1408', 'Black and gold. The most feared set in the game.', 4, 500, 45, 80),
]
items = ''.join(f"{k}:['{n}','body','{c}','{e}',{r},0,{s},0,{a},'body']," for k, n, c, e, r, s, a, q in SETS)
rep("sbody:['Steel breastplate'", items + "sbody:['Steel breastplate'")

built = {k: os.path.exists(f'models/arm_lv{k[3:]}.json') for k, *_ in SETS}
arms = ','.join(f"{k}:['arm_lv{k[3:]}',{q},{1 if built[k] else 0}]" for k, n, c, e, r, s, a, q in SETS)
helpers = ("const ARMS={" + arms + "};\n"
           "function armKey(){const k=st.eq&&st.eq.body;return k&&ARMS[k]?k:null}\n"
           "function armBody(k){const a=k&&ARMS[k];if(!a||!a[2])return null;needMdl(a[0]);const m=MDL[a[0]];return m&&m.ok&&m.tex?m:null}\n")
rep("function needMdl(k){", helpers + "function needMdl(k){")

# Defence level to wear a set
rep("function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;",
    "function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;"
    "if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])return say('You need a Defence level of '+ARMS[k][1]+' to wear the '+IN[k]+'.','#c00');")
rep("const k=st.inv[i],sl=slotOf(k);if(!sl)continue;const cur=st.eq[sl]",
    "const k=st.inv[i],sl=slotOf(k);if(!sl)continue;if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])continue;const cur=st.eq[sl]")

# your own character: the armour body wins over the plain / caped body
rep("const PM=CBM||((MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player),PC=PM&&",
    "const ARMB=st.body!==0?armBody(armKey()):null,PM=ARMB||CBM||((MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player),PC=PM&&")

# other players: send '@armNN' after the cape, and draw it
rep("cc=((st.eq&&st.eq.cape)||'')+(cs&&st.eq&&st.eq.cape?':'+cs:''),",
    "cc=((st.eq&&st.eq.cape)||'')+(cs&&st.eq&&st.eq.cape?':'+cs:'')+(armKey()?'@'+armKey():''),")
rep("const cp=String(inf.c||'').split(':'),ck=cp[0],csk=cp[1]&&/^cs_[a-z0-9_]+$/.test(cp[1])?cp[1]:null,CBo=ck?capeBody(K,ck,csk):null,PMo=CBo||",
    "const c2=String(inf.c||'').split('@'),cp=c2[0].split(':'),ck=cp[0],csk=cp[1]&&/^cs_[a-z0-9_]+$/.test(cp[1])?cp[1]:null,AMo=/^arm\\d\\d$/.test(c2[1]||'')?armBody(c2[1]):null,CBo=!AMo&&ck?capeBody(K,ck,csk):null,PMo=AMo||CBo||")

# Paper Hands is in the starter pack (Albert, until the tutorial island exists): new players get it worn by autoEquip,
# players who already had their kit get it once in the bag
rep("say('Your bag holds a bronze sword, axe, pickaxe, tinderbox, a small fishing net and some bread.','#a60')}",
    "say('Your bag holds a bronze sword, axe, pickaxe, tinderbox, a small fishing net, some bread and the Paper Hands outfit.','#a60')}"
    "if(!st.kitArm){st.kitArm=1;if(!has('arm01')&&!eqd('arm01')&&cap()>0){st.inv.push('arm01');if(st.eqDone)say('New: the Paper Hands outfit is in your bag. Tap it and choose Wear.','#a60')}}")

open(PATH, 'w', encoding='utf-8').write(h)
print('armor patch applied; models built:', [k for k in built if built[k]])
