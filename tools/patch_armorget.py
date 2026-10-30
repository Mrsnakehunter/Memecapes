#!/usr/bin/env python3
"""How players earn the armour sets (Albert, Oct 29: "start working on the items and the game plan to get them").

  Lv1  Paper Hands        starter pack (patch_armor.py)
  Lv10 Copper Coin        smithed: 5 bronze bars, Smithing 10
  Lv20 HODL Iron          smithed: 5 iron bars (iron ore smelted, Smithing 15), Smithing 20
  Lv30 Bull Steel         smithed: 5 steel bars (iron ore + 2 coal, Smithing 30), Smithing 30
  Lv40 Gold Rush          smithed: 5 steel bars + 5 gold nuggets, Smithing 40
  Lv50 Diamond Hands      rare drop from the Ratio Knight (level 50)
  Lv60 Whale Plate        rare drop from the Ratio Lord (level 75 boss)
  Lv70 Moonforged         rarer drop from the Ratio Lord
  Lv80 Legend of the Meme rarest drop from the Ratio Lord; cannot be traded
New ores: copper rocks give iron ore a third of the time from Mining 15; tin rocks give coal a third of the time from
Mining 30. New items: iron ore, coal, iron bar, steel bar. The forge lists every recipe with what you still need.
(The dedicated bosses in the plan replace the Ratio Lord drops when they exist.)
Run after patch_armcape.py:  python3 tools/patch_armorget.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# items (icons from the ore / bar shapes, recoloured)
rep("IC.tin=IC.ore.split('#b8642e').join('#a8b0b8');IN.tin='Tin ore';EX.tin='This needs refining.';SELL.tin=2;",
    "IC.tin=IC.ore.split('#b8642e').join('#a8b0b8');IN.tin='Tin ore';EX.tin='This needs refining.';SELL.tin=2;"
    "IC.iron=IC.ore.split('#b8642e').join('#7d6a5e');IN.iron='Iron ore';EX.iron='Heavy, dark and full of promise.';SELL.iron=4;"
    "IC.coal=IC.ore.split('#b8642e').join('#2c2c30');IN.coal='Coal';EX.coal='Burns hot. Steel needs it.';SELL.coal=3;"
    "IC.ibar=IC.bar.split('#9aa6b5').join('#7c848e');IN.ibar='Iron bar';EX.ibar='A bar of iron. Never lets go.';SELL.ibar=10;"
    "IC.sbar=IC.bar.split('#9aa6b5').join('#d2d8e0');IN.sbar='Steel bar';EX.sbar='Bright steel, ready for the anvil.';SELL.sbar=25;")
rep("bar:'Smith iron gear at a forge.',",
    "bar:'Smith iron gear or Copper Coin armour at a forge.',iron:'Smelt into an iron bar at a forge (Smithing 15), or with 2 coal into steel (Smithing 30).',"
    "coal:'Two coal and an iron ore make a steel bar at a forge.',ibar:'Smith HODL Iron armour at a forge (5 bars, Smithing 20).',sbar:'Smith Bull Steel or Gold Rush armour at a forge.',")

# mining: iron from copper rocks at Mining 15+, coal from tin rocks at Mining 30+
rep("const tn=act.o.tin;if(give(tn?'tin':'ore')){addXp('mi',17.5);skillPet(7);evn('mine');say('You manage to mine some '+(tn?'tin':'copper')+'.');",
    "const tn=act.o.tin,ml=lvl(st.xp.mi),got=tn?(ml>=30&&Math.random()<.34?'coal':'tin'):(ml>=15&&Math.random()<.34?'iron':'ore');"
    "if(give(got)){addXp('mi',got=='coal'?35:got=='iron'?30:17.5);skillPet(7);evn('mine');say('You manage to mine some '+({ore:'copper',tin:'tin',iron:'iron',coal:'coal'})[got]+'.');")

# the forge: recipes
rep("<button data-f=\"smelt\">Smelt bronze bars</button><br><br>';",
    "<button data-f=\"smelt\">Smelt bronze bars</button> <button data-f=\"smelti\">Smelt iron bars (lvl 15)</button> <button data-f=\"smelts\">Smelt steel bars (lvl 30)</button><br>"
    "<small>Iron: '+st.inv.filter(k=>k=='iron').length+' ore, '+st.inv.filter(k=>k=='ibar').length+' bars | Coal: '+st.inv.filter(k=>k=='coal').length+' | Steel bars: '+st.inv.filter(k=>k=='sbar').length+' | Gold nuggets: '+st.inv.filter(k=>k=='gold').length+'</small><br><br>';"
    "ARMREC.forEach(([k,need,lv])=>{const cnt=x=>st.inv.filter(q=>q==x).length,ok=Object.keys(need).every(x=>cnt(x)>=need[x]),txt=Object.keys(need).map(x=>need[x]+' '+IN[x].toLowerCase()+(need[x]>1?'s':'')).join(' + ');"
    "h+='<div class=\"row\"><span>'+IN[k]+' ('+txt+', lvl '+lv+')</span>'+(has(k)||eqd(k)?'<span>Owned</span>':'<button data-f=\"'+k+'\" data-a=\"1\"'+(ok&&sl>=lv?'':' disabled')+'>Smith</button>')+'</div>'});")
rep("MB.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{const f=b.dataset.f;if(f=='smelt'){",
    "MB.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{const f=b.dataset.f;"
    "if(f=='smelti'||f=='smelts'){const lv=f=='smelti'?15:30;if(lvl(st.xp.sm)<lv)return say('You need Smithing level '+lv+'.','#c00');const cnt=x=>st.inv.filter(q=>q==x).length;let n=f=='smelti'?cnt('iron'):Math.min(cnt('iron'),Math.floor(cnt('coal')/2));if(!n)return say(f=='smelti'?'You need iron ore to make an iron bar.':'You need an iron ore and 2 coal to make a steel bar.','#c00');"
    "let a=n,c=f=='smelts'?2*n:0;st.inv=st.inv.filter(k=>{if(k=='iron'&&a>0){a--;return false}if(k=='coal'&&c>0){c--;return false}return true});for(let i=0;i<n;i++)st.inv.push(f=='smelti'?'ibar':'sbar');addXp('sm',(f=='smelti'?12.5:17.5)*n);pAnim={k:'smith',t0:performance.now(),d:2400};say('You smelt '+n+(f=='smelti'?' iron bar':' steel bar')+(n>1?'s':'')+'.')}"
    "else if(b.dataset.a){const r=ARMREC.find(x=>x[0]==f);if(!r)return;const[k,need,lv]=r;if(lvl(st.xp.sm)<lv)return say('You need Smithing level '+lv+'.','#c00');const cnt=x=>st.inv.filter(q=>q==x).length;for(const x in need)if(cnt(x)<need[x])return say('You need '+need[x]+' '+IN[x].toLowerCase()+(need[x]>1?'s':'')+'.','#c00');"
    "const left={...need};st.inv=st.inv.filter(q=>{if(left[q]>0){left[q]--;return false}return true});st.inv.push(k);addXp('sm',lv*12.5);evn('smith');pAnim={k:'smith',t0:performance.now(),d:2400};say('You hammer out the '+IN[k]+'. Wear it from your bag.','#0a0')}"
    "else if(f=='smelt'){")
rep("function armKey(){", "const ARMREC=[['arm10',{bar:5},10],['arm20',{ibar:5},20],['arm30',{sbar:5},30],['arm40',{sbar:5,gold:5},40]];\nfunction armKey(){")

# drops
rep("lt:[['rshard',.35],['gold',.3],['rgem',.15],['rshield',.02],['rarmor',.006]]",
    "lt:[['rshard',.35],['gold',.3],['rgem',.15],['rshield',.02],['rarmor',.006],['arm50',.0067]]")
rep("lt:[['rshard',1],['rarmor',.05],['rshield',.1]]",
    "lt:[['rshard',1],['rarmor',.05],['rshield',.1],['arm60',.04],['arm70',.02],['arm80',.008]]")
# the Legend set cannot be traded
rep("const NOTRADE=k=>k=='coin'||", "const NOTRADE=k=>k=='coin'||k=='arm80'||")

open(PATH, 'w', encoding='utf-8').write(h)
print('armour sources patch applied')
