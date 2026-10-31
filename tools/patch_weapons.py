#!/usr/bin/env python3
"""A sword for every armour set (Albert, Oct 30: "each one of those armor classes need weapons to match").

Nine swords, one per set, each a Meshy model (models/w_swNN.json, from the concept pictures via image-to-3D and
tools/glb2mdl.py --orient). Stats climb with the tier; you need the Attack level of the tier to wield one.
  Lv1  Paper Cutter          starter pack, with the Paper Hands outfit
  Lv10 Copper Coin Blade     forge: 2 bronze bars, Smithing 10
  Lv20 HODL Iron Sword       forge: 3 iron bars, Smithing 20
  Lv30 Bull Steel Blade      forge: 3 steel bars, Smithing 30
  Lv40 Gold Rush Sabre       forge: 3 steel bars + 3 gold nuggets, Smithing 40
  Lv50 Diamond Hands Edge    rare drop from the Ratio Knight
  Lv60 Whale Fang            rare drop from the Ratio Lord
  Lv70 Moonforged Blade      rarer drop from the Ratio Lord
  Lv80 Legendary Meme Blade  rarest drop from the Ratio Lord; cannot be traded
The armour parade knights each hold their own tier's sword. A sword whose model isn't built yet falls back to the
iron sword's model in the hand (the item still works).
Run after patch_armordemo.py:  python3 tools/patch_weapons.py
"""
import os
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# key, name, colour, examine, rarity, sell, [accuracy, strength, speed], Attack level
SW = [
    ('sw01', 'Paper Cutter', '#d8cdb0', 'Folded, taped and slightly bent. It has seen things.', 0, 2, [3, 3, 4], 1),
    ('sw10', 'Copper Coin Blade', '#c87533', 'Copper with a coin for a pommel. Heads you win.', 1, 25, [8, 7, 4], 10),
    ('sw20', 'HODL Iron Sword', '#6f747c', 'Heavy iron with a fist on the end. It never lets go.', 1, 60, [16, 14, 4], 20),
    ('sw30', 'Bull Steel Blade', '#c9ced6', 'Bright steel, horns on the guard. Only goes up.', 2, 110, [26, 24, 4], 30),
    ('sw40', 'Gold Rush Sabre', '#e0b545', 'Gold over steel. Shiny enough to mine itself.', 2, 180, [38, 36, 4], 40),
    ('sw50', 'Diamond Hands Edge', '#8fd3ff', 'A blade of pure diamond. It does not sell.', 3, 280, [52, 50, 4], 50),
    ('sw60', 'Whale Fang', '#1f6b78', 'Deep-sea steel with a fluke for a tip. Moves markets.', 3, 400, [66, 64, 4], 60),
    ('sw70', 'Moonforged Blade', '#dfe6f5', 'Forged in moonlight. Glows when it is late.', 4, 550, [82, 80, 4], 70),
    ('sw80', 'Legendary Meme Blade', '#b01830', 'Crimson and gold. The most feared blade in the game.', 4, 800, [100, 98, 4], 80),
]
items = ''.join(f"{k}:['{n}','blade','{c}','{e}',{r},0,{s},{st[1]}]," for k, n, c, e, r, s, st, q in SW)
rep("rsword:['Ratio Blade','blade','#c77dff','Forged from pure ratio.',4,0,0,9],",
    "rsword:['Ratio Blade','blade','#c77dff','Forged from pure ratio.',4,0,0,9]," + items)
stats = ','.join(f"{k}:{st}" for k, n, c, e, r, s, st, q in SW)
rep("rsword:[65,62,4],bbat:[8,11,5]};", "rsword:[65,62,4],bbat:[8,11,5]," + stats + "};")
# shop value (so selling / trade valuation have a number)
gv = ','.join(f"{k}:{s * 8}" for k, n, c, e, r, s, st, q in SW)
rep("const GV0={coin:1,sword:40,", "const GV0={coin:1," + gv + ",sword:40,")

# Attack level to wield
wreq = ','.join(f"{k}:{q}" for k, n, c, e, r, s, st, q in SW)
rep("function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;",
    "const WREQ={" + wreq + "};\n"
    "function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;"
    "if(WREQ[k]&&lvl(st.xp.at)<WREQ[k])return say('You need an Attack level of '+WREQ[k]+' to wield the '+IN[k]+'.','#c00');")
rep("const k=st.inv[i],sl=slotOf(k);if(!sl)continue;if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])continue;",
    "const k=st.inv[i],sl=slotOf(k);if(!sl)continue;if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])continue;if(WREQ[k]&&lvl(st.xp.at)<WREQ[k])continue;")

# in the hand: model config (same carry as the other swords, a little longer up the tiers); unbuilt models -> iron sword
built = {k: os.path.exists(f'models/w_{k}.json') for k, *_ in SW}
# [length in world units, grip height as a fraction of the model, carry, tilt, swing] (grip = between pommel and guard, measured)
WC = {'sw01': [.95, .17], 'sw10': [1.0, .18], 'sw20': [1.1, .14], 'sw30': [1.1, .2], 'sw40': [1.1, .15], 'sw50': [1.15, .19],
      'sw60': [1.3, .17], 'sw70': [1.2, .2], 'sw80': [1.25, .17]}
cfg = ','.join(f"w_{k}:[{WC[k][0]},{WC[k][1]},'f',25,20]" for k, *_ in SW)
rep("},HTEST=null;", "},HTEST=null;Object.assign(WCFG,{" + cfg + "});"
    "const WFB={" + ','.join(f"w_{k}:'w_isword'" for k in built if not built[k]) + "};")
rep("if(!k)return null;if(HTEST)return HTEST;const w='w_'+k,sw=skinW(k);return sw&&WAV.has(sw)?sw:WAV.has(w)?w:null}",
    "if(!k)return null;if(HTEST)return HTEST;const w='w_'+k,sw=skinW(k);return sw&&WAV.has(sw)?sw:WAV.has(w)?w:WFB[w]||null}")
# other players (netDraw) and the parade go through qHold with a weapon key: map unbuilt ones there too
rep("function qHold(PM,x,z,yaw,clip,t,wk,left", "function qHold(PM,x,z,yaw,clip,t,wk,left){if(WFB[wk])wk=WFB[wk];return qHold_(PM,x,z,yaw,clip,t,wk,left,...[].slice.call(arguments,8))}\nfunction qHold_(PM,x,z,yaw,clip,t,wk,left")

# the forge: weapon recipes next to the armour ones
rep("const ARMREC=[['arm10',{bar:5},10],['arm20',{ibar:5},20],['arm30',{sbar:5},30],['arm40',{sbar:5,gold:5},40]];",
    "const ARMREC=[['arm10',{bar:5},10],['sw10',{bar:2},10],['arm20',{ibar:5},20],['sw20',{ibar:3},20],['arm30',{sbar:5},30],['sw30',{sbar:3},30],['arm40',{sbar:5,gold:5},40],['sw40',{sbar:3,gold:3},40]];")
rep("say('You hammer out the '+IN[k]+'. Wear it from your bag.','#0a0')}",
    "say('You hammer out the '+IN[k]+'. '+(WST[k]?'Wield':'Wear')+' it from your bag.','#0a0')}")
# starter pack: the Paper Cutter comes with the Paper Hands outfit
rep("if(!st.kitArm){st.kitArm=1;if(!has('arm01')&&!eqd('arm01')&&cap()>0){st.inv.push('arm01');",
    "if(!st.kitSw){st.kitSw=1;if(!has('sw01')&&!eqd('sw01')&&cap()>0)st.inv.push('sw01')}"
    "if(!st.kitArm){st.kitArm=1;if(!has('arm01')&&!eqd('arm01')&&cap()>0){st.inv.push('arm01');")
# drops
rep("['rarmor',.006],['arm50',.0067]]", "['rarmor',.006],['arm50',.0067],['sw50',.0067]]")
rep("['arm60',.04],['arm70',.02],['arm80',.008]]", "['arm60',.04],['arm70',.02],['arm80',.008],['sw60',.04],['sw70',.02],['sw80',.008]]")
rep("const NOTRADE=k=>k=='coin'||k=='arm80'||", "const NOTRADE=k=>k=='coin'||k=='arm80'||k=='sw80'||")

# the parade: each knight holds his own tier's sword
rep("ARMP.push({id:'armp'+i,k:a[0],nm:a[1],lv:a[2],cape:a[3],x,y,r:0,tr:0,t0:i*1.7})",
    "ARMP.push({id:'armp'+i,k:a[0],nm:a[1],lv:a[2],cape:a[3],wk:'w_sw'+a[0].slice(3),x,y,r:0,tr:0,t0:i*1.7})")
rep("qHold(m,x,z,o.r,'Idle',t,'w_isword',false,null,heldTilt('Idle',t,'w_isword'));",
    "qHold(m,x,z,o.r,'Idle',t,o.wk,false,null,heldTilt('Idle',t,o.wk));")

open(PATH, 'w', encoding='utf-8').write(h)
print('weapons patch applied; models built:', [k for k in built if built[k]])
