#!/usr/bin/env python3
"""Ranger and mage gear, the Archery and Magic shops, and a Crafting skill (Albert, Nov 1: "an archery and magic shop
... some things bought, some made or crafted or quested; the armour for the mage and the ranger should be different
sets than the ones we have, same tier stuff"; his picks: 9 sets each, a new Crafting skill, top tiers like melee).

  Ranger sets  ra01..ra80 (Ranged level 1/10/20..80): light leathers, Ranged accuracy bonus + some Defence.
  Mage sets    ma01..ma80 (Magic level 1/10/20..80): robes, Magic accuracy + spell damage bonus + a little Defence.
  Staffs       st10..st80 next to the Paper Staff (tools/mkstaff.py makes all nine), Magic level to wield.
  Where from   tier 1 and 10: bought (Archery / Magic shop); 10-40 bows, staffs and 10-30 armour: made with Crafting
               at the shop's workbench; Lv40 armour: a trial (quest) from the shop keeper; Lv50: Ratio Knight drop;
               Lv60/70/80: Ratio Lord drops; Lv80 can't be traded.
  Crafting     new skill (cr): fletch arrows and bows from logs + bars, stitch ranger leathers from hides, sew robes
               from cloth, write spell scrolls on paper. Hides drop from beasts, cloth from people-like monsters,
               paper and cloth are also sold at the Magic shop.
  3D bodies    models/ra_lvNN.json / ma_lvNN.json, picked up when they exist (made from Meshy like the melee sets);
               until then the set works as an item and you keep your normal body.
Run after patch_styles.py:  python3 tools/patch_classes.py
"""
import os
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


TIERS = [1, 10, 20, 30, 40, 50, 60, 70, 80]
RNAME = ['Paper Scout', 'Copper Coin Ranger', 'HODL Iron Hide', 'Bull Run Leathers', 'Gold Rush Tracker',
         'Diamond Hands Stalker', 'Whale Hunter', 'Moonforged Ranger', 'Legend of the Meme Ranger']
MNAME = ['Paper Robes', 'Copper Coin Robes', 'HODL Iron Mystic', 'Bull Market Robes', 'Gold Rush Sorcerer',
         'Diamond Hands Arcanist', 'Whale Tide Robes', 'Moonforged Mage', 'Legend of the Meme Archmage']
SNAME = ['Paper Staff', 'Copper Coin Staff', 'HODL Iron Staff', 'Bull Steel Staff', 'Gold Rush Staff',
         'Diamond Hands Staff', 'Whale Staff', 'Moonforged Staff', 'Legendary Meme Staff']
COL = ['#d8cdb0', '#c87533', '#6f747c', '#c9ced6', '#e0b545', '#8fd3ff', '#1f6b78', '#dfe6f5', '#b01830']
RCOL = ['#a89a7a', '#8a5a32', '#4a4c52', '#8a6a40', '#2f6a3a', '#cfe6ff', '#1f4a6a', '#2a3a6a', '#a01828']
MCOL = ['#b8b0a0', '#7a4a2a', '#3a3a40', '#8a2a2a', '#5a2a8a', '#e6f2ff', '#1f5a6a', '#1e2650', '#a01828']
REX = ['Patched cloth and folded paper. Light on the feet.', 'Brown leather with copper coin studs.',
       'Dark studded leather. Stubborn as iron.', 'Polished leather with steel inlays and little horns.',
       'Green leather trimmed in gold. Made for treasure hunters.', 'Pale leather set with crystal diamonds.',
       'Sea-leather with fin guards. Hunts the biggest fish.', 'Midnight leather with silver moons.',
       'Crimson and gold. The most feared archer outfit in the game.']
MEX = ['A robe of folded paper and tape. It still casts.', 'Brown robes with copper coin buttons.',
       'Charcoal robes with iron clasps.', 'Red and steel robes. Only goes up.', 'Purple robes stitched with gold.',
       'White robes set with crystal diamonds.', 'Teal robes that move like the tide.',
       'Midnight robes covered in silver moons and stars.', 'Crimson and gold. The most feared mage outfit in the game.']
SEX = ['Rolled-up paper with a spark at the end. It casts.', 'A copper staff with a coin-bright orb.',
       'Dark iron with a cold blue light.', 'Bright steel with a red flame orb.', 'Purple wood bound in gold.',
       'A staff of pure diamond. It never lets go of a spell.', 'Deep-sea steel with a glowing tide orb.',
       'Moonlit silver. Glows when it is late.', 'Crimson and gold. The most feared staff in the game.']
RAR = [0, 1, 1, 2, 2, 3, 3, 4, 4]
SELL = [4, 20, 45, 80, 130, 200, 280, 380, 500]
RDEF = [2, 4, 7, 10, 14, 19, 24, 30, 36]
MDEF = [1, 3, 5, 7, 10, 13, 17, 21, 26]
ACC = [3, 8, 14, 20, 27, 34, 42, 50, 60]        # armour accuracy bonus for its style
MDMG = [0, 2, 4, 6, 8, 10, 13, 16, 20]          # robes: extra spell damage %
SACC = [6, 10, 16, 26, 38, 52, 66, 82, 100]     # staff magic accuracy
SDMG = [0, 3, 6, 9, 12, 16, 20, 25, 30]         # staff spell damage %
nn = lambda t: f'{t:02d}'

# ---------------------------------------------------------------- items
items = ''
for i, t in enumerate(TIERS):
    items += f"ra{nn(t)}:['{RNAME[i]}','body','{RCOL[i]}','{REX[i]}',{RAR[i]},0,{SELL[i]},0,{RDEF[i]},'body'],"
    items += f"ma{nn(t)}:['{MNAME[i]}','body','{MCOL[i]}','{MEX[i]}',{RAR[i]},0,{SELL[i]},0,{MDEF[i]},'body'],"
    if t > 1:
        items += f"st{nn(t)}:['{SNAME[i]}','staff','{COL[i]}','{SEX[i]}',{RAR[i]},0,{SELL[i]},0],"
items += ("hide:['Hide','sack','#8a5a2b','A tough hide. Stitch it into ranger leathers.',0,0,3],"
          "cloth:['Cloth','sack','#8a6ab0','Soft cloth. Sew it into mage robes.',0,0,3],"
          "paper:['Paper','scroll','#f1e2b8','A blank sheet. Write a spell on it.',0,0,1],")
rep("st01:['Paper Staff','staff',", items + "st01:['Paper Staff','staff',")
rep(",st01:[2,1,5]};", ",st01:[2,1,5]," + ','.join(f"st{nn(t)}:[2,1,5]" for t in TIERS[1:]) + "};")
gv = ','.join(f"ra{nn(t)}:{SELL[i] * 8},ma{nn(t)}:{SELL[i] * 8}" + (f",st{nn(t)}:{SELL[i] * 8}" if t > 1 else '')
              for i, t in enumerate(TIERS))
rep("const GV0={coin:1,", "const GV0={coin:1," + gv + ",hide:24,cloth:24,paper:8,")
rep("const NOTRADE=k=>k=='coin'||", "const NOTRADE=k=>k=='coin'||k=='st80'||k=='ra80'||k=='ma80'||")

# ---------------------------------------------------------------- the sets as bodies (ARMS gets the skill as a 4th field)
arms = ','.join(f"ra{nn(t)}:['ra_lv{nn(t)}',{t},{1 if os.path.exists(f'models/ra_lv{nn(t)}.json') else 0},'rg'],"
                f"ma{nn(t)}:['ma_lv{nn(t)}',{t},{1 if os.path.exists(f'models/ma_lv{nn(t)}.json') else 0},'mg']" for t in TIERS)
rep("function armKey(){", "Object.assign(ARMS,{" + arms + "});\nfunction armKey(){")
rep("if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])return say('You need a Defence level of '+ARMS[k][1]+' to wear the '+IN[k]+'.','#c00');",
    "if(ARMS[k]&&lvl(st.xp[ARMS[k][3]||'def']||0)<ARMS[k][1])return say('You need a '+NM[ARMS[k][3]||'def']+' level of '+ARMS[k][1]+' to wear the '+IN[k]+'.','#c00');")
rep("if(ARMS[k]&&lvl(st.xp.def)<ARMS[k][1])continue;", "if(ARMS[k]&&lvl(st.xp[ARMS[k][3]||'def']||0)<ARMS[k][1])continue;")
rep("AMo=/^arm\\d\\d$/.test(c2[1]||'')", "AMo=/^(arm|ra|ma)\\d\\d$/.test(c2[1]||'')")
rep("if(k=='def')Object.keys(ARMS).forEach(a=>u.push([ARMS[a][1],IN[a]]));",
    "if(k=='def')Object.keys(ARMS).forEach(a=>{if(!ARMS[a][3])u.push([ARMS[a][1],IN[a]])});"
    "if(k=='rg'||k=='mg')Object.keys(ARMS).forEach(a=>{if(ARMS[a][3]==k)u.push([ARMS[a][1],IN[a]])});"
    "if(k=='cr')CRR.forEach(r=>u.push([r[2],crName(r)]));")

# staffs in the hand + Magic level to wield
rep(",w_st01:[1.6,.33,'v',22,8]});", ",w_st01:[1.6,.33,'v',22,8]," + ','.join(f"w_st{nn(t)}:[1.6,.33,'v',22,8]" for t in TIERS[1:]) + "});")
# accuracy from the armour: ranged and magic
rep("acc=hc(eA*(B[0]+64));mh=Math.floor(.5+eS", "acc=hc(eA*(B[0]+gearAcc('rg')+64));mh=Math.floor(.5+eS")
rep("acc=hc(eA*(B[0]+64));mh=Math.floor(sp[3]*(1+B[1]/100)", "acc=hc(eA*(B[0]+gearAcc('mg')+64));mh=Math.floor(sp[3]*(1+(B[1]+gearDmg())/100)")
rep("if(s=='mg'){const p=curSpell();return p?Math.floor(p[3]*(1+MST[w][1]/100)", "if(s=='mg'){const p=curSpell();return p?Math.floor(p[3]*(1+(MST[w][1]+gearDmg())/100)")
# trials count kills made with a bow or a staff
rep("if(gb.hp<=0)killMob(gb);return s=='rg'?", "if(gb.hp<=0){trialKill(mt,s);killMob(gb)}return s=='rg'?")
# drops: the top tiers ride with the melee ones
rep("['rarmor',.006],['arm50',.0067],['sw50',.0067]]", "['rarmor',.006],['arm50',.0067],['sw50',.0067],['bw50',.0067],['st50',.0067],['ra50',.0067],['ma50',.0067]]")
rep("['sw60',.04],['sw70',.02],['sw80',.008]]",
    "['sw60',.04],['sw70',.02],['sw80',.008],['bw60',.04],['bw70',.02],['bw80',.008],['st60',.04],['st70',.02],['st80',.008],"
    "['ra60',.04],['ra70',.02],['ra80',.008],['ma60',.04],['ma70',.02],['ma80',.008]]")
# skill + cape colour
rep("rg:'Ranged',mg:'Magic',hp:'Health',", "rg:'Ranged',mg:'Magic',hp:'Health',cr:'Crafting',")
rep("['str','def','pr','ag','sl','fm','fa','cn','rg','mg']", "['str','def','pr','ag','sl','fm','fa','cn','rg','mg','cr']")
rep("rg:'#2e8a4a',mg:'#3a4ad8'};\nObject.keys(CAPEC)", "rg:'#2e8a4a',mg:'#3a4ad8',cr:'#b0602a'};\nObject.keys(CAPEC)")
rep("Object.assign(SCC,{rg:'#2e8a4a',mg:'#3a4ad8'});", "Object.assign(SCC,{rg:'#2e8a4a',mg:'#3a4ad8',cr:'#b0602a'});"
    "Object.assign(SCI,{cr:'<path d=\"M5 19 15 9M15 9l3-5 2 2-5 3M4 20l2-1-1-1z\"/><path d=\"M9 5c-2 0-4 2-4 4M19 15c0 2-2 4-4 4\"/>'});"
    "Object.assign(SCW,{cr:'Fletch arrows and bows, stitch ranger leathers, sew mage robes and write spell scrolls at the Archery and Magic shops.'});")

# ---------------------------------------------------------------- NPCs: the two shops in Gigachad Town
rep("xo(...fN(CX-9,CY-4),'lpad',{ry:1.57});", "xo(...fN(CX-9,CY-4),'lpad',{ry:1.57});xo(...fN(CX+9,CY+6),'arsh',{ry:-1.57});xo(...fN(CX+9,CY-4),'mgsh',{ry:-1.57});")
rep("lpad:['Talk to','Launchpad clerk'],", "lpad:['Talk to','Launchpad clerk'],arsh:['Trade','Fern the Fletcher'],mgsh:['Trade','Mystic Moe'],")
rep("lpad:'She lists the new coins launched on memecapes.com.',",
    "lpad:'She lists the new coins launched on memecapes.com.',arsh:'She runs the Archery shop: bows, arrows, ranger leathers and a workbench.',mgsh:'He runs the Magic shop: staffs, robes, scrolls and a writing desk.',")
rep("lpad:()=>lpUI(),", "lpad:()=>lpUI(),arsh:()=>gsOpen('r'),mgsh:()=>gsOpen('m'),")
rep("lpad:'richw'}", "lpad:'richw',arsh:'trader',mgsh:'genie'}")

T = lambda t: nn(t)
JS = r"""
// ---- ranger + mage gear, the Archery and Magic shops, Crafting (tools/patch_classes.py)
Object.assign(MST,{""" + ','.join(f"st{T(t)}:[{SACC[i]},{SDMG[i]}]" for i, t in enumerate(TIERS) if t > 1) + r"""});
Object.assign(WRQ,{""" + ','.join(f"st{T(t)}:['mg',{t}]" for t in TIERS if t > 1) + r"""});
const GACC={""" + ','.join(f"ra{T(t)}:{ACC[i]},ma{T(t)}:{ACC[i]}" for i, t in enumerate(TIERS)) + r"""},GDMG={""" + ','.join(f"ma{T(t)}:{MDMG[i]}" for i, t in enumerate(TIERS)) + r"""};
const gearAcc=s=>{const b=st.eq&&st.eq.body;return b&&ARMS[b]&&ARMS[b][3]==s?GACC[b]||0:0},gearDmg=()=>{const b=st.eq&&st.eq.body;return b&&ARMS[b]&&ARMS[b][3]=='mg'?GDMG[b]||0:0};
// where hides and cloth come from
MT.forEach(m=>{m.lt=m.lt||[];if(/Hound|Doge|Shib|cat|Hippo|Squirrel|Frog|Fox|Bonk|Floki|Wif|Slerf|Mog|Goat|Bull|Pnut|Moo/i.test(m.n))m.lt.push(['hide',.22]);
 if(/Wojak|Guard|Chad|Bandit|Cultist|Jester|Shaman|Knight|Goblin|Scroller|Captain/i.test(m.n))m.lt.push(['cloth',.2])});
// recipes: [made, materials, Crafting level, XP, how many (arrows and scrolls go to the quiver / pouch), shop]
const CRR=[['a1',{logs:1},1,8,15,'r'],['bw10',{logs:2,bar:1},10,40,1,'r'],['ra10',{hide:3,bar:1},12,45,1,'r'],['a2',{logs:1,ibar:1},20,20,15,'r'],
 ['bw20',{logs:3,ibar:2},20,70,1,'r'],['ra20',{hide:4,ibar:2},22,80,1,'r'],['bw30',{logs:3,sbar:2},30,110,1,'r'],['ra30',{hide:5,sbar:2},32,120,1,'r'],
 ['bw40',{logs:4,sbar:2,gold:2},40,160,1,'r'],['a3',{logs:1,rgem:1},50,40,15,'r'],
 ['ss',{paper:1},1,6,10,'m'],['st10',{logs:2,bar:1},10,40,1,'m'],['ma10',{cloth:3,bar:1},12,45,1,'m'],['bs',{paper:2,gold:1},20,25,5,'m'],
 ['st20',{logs:3,ibar:2},20,70,1,'m'],['ma20',{cloth:4,ibar:2},22,80,1,'m'],['st30',{logs:3,sbar:2},30,110,1,'m'],['ma30',{cloth:5,sbar:2},32,120,1,'m'],
 ['st40',{logs:4,sbar:2,gold:2},40,160,1,'m']];
const crName=r=>(r[4]>1?r[4]+' ':'')+(SHN[r[0]]||IN[r[0]]),bagN=k=>st.inv.filter(x=>x==k).length;
// what each shop sells: [item or supply, price, how many]
const GSB={r:[['bw01',30],['bw10',400],['ra01',40],['ra10',500],['a1',20,50],['a2',150,50]],
 m:[['st01',30],['st10',400],['ma01',40],['ma10',500],['paper',10,10],['cloth',12,1],['ss',25,50],['bs',200,25]]};
// the trials that give the Lv40 sets
const TRL={r:{n:'The Gold Rush Trail',k:'ra40',sk:'rg',need:{gold:5,hide:6},who:'Fern'},m:{n:'The Golden Tome',k:'ma40',sk:'mg',need:{gold:5,cloth:6},who:'Moe'}};
const trl=w=>{st.trl=st.trl||{};return st.trl[w]=st.trl[w]||{s:0,k:0}};
function trialKill(mt,s){const w=s=='rg'?'r':s=='mg'?'m':null;if(!w)return;const t=trl(w);if(t.s==1&&(mt.lv||1)>=20){t.k++;if(t.k==30)say(TRL[w].n+': 30 kills done. Bring the materials to '+TRL[w].who+'.','#a60')}}
let GSKD='r',GSTB='buy';window.gsRe=()=>{if(M.style.display!='none'&&MB.querySelector('.gsW'))gsDraw()};
function gsOpen(w){GSKD=w;GSTB='buy';M.style.display='flex';MB.onclick=null;MB.className='gsx';gsDraw()}
function gsRow(ico,name,sub,btn){return '<div class="gsR"><span class="gsI">'+ico+'</span><span class="gsN"><b>'+name+'</b>'+(sub?'<small>'+sub+'</small>':'')+'</span>'+btn+'</div>'}
const gsIco=k=>SHN[k]&&!IC[k]?amoIco(k):'<svg viewBox="0 0 24 24">'+(IC[k]||'')+'</svg>';
function gsDraw(){const w=GSKD,R=w=='r',cl=lvl(st.xp.cr||0);
 let t='<h2>'+(R?'Archery shop':'Magic shop')+'</h2><p class="gsP">'+(R?'"Bows, arrows and ranger leathers. Buy the basics, make the rest at my workbench."':'"Staffs, robes and spell scrolls. Buy the basics, make the rest at my writing desk."')+' <small>Crafting '+cl+'</small></p>'
  +'<div class="gsT">'+[['buy','Buy'],['make',R?'Workbench':'Writing desk'],['trial','Trial']].map(([k,n])=>'<button data-gst="'+k+'" class="'+(GSTB==k?'on':'')+'">'+n+'</button>').join('')+'</div>';
 if(GSTB=='buy')t+=GSB[w].map(([k,p,n],i)=>{const sup=!!SHN[k],have=sup?amoN(k):bagN(k)+(eqd(k)?1:0);return gsRow(gsIco(k),(n>1?n+' ':'')+(SHN[k]||IN[k]),(WRQ[k]?NM[WRQ[k][0]]+' '+WRQ[k][1]+' · ':ARMS[k]?NM[ARMS[k][3]||'def']+' '+ARMS[k][1]+' · ':'')+'you have '+have,'<button data-gsb="'+i+'">'+p+' MC</button>')}).join('');
 if(GSTB=='make')t+=CRR.filter(r=>r[5]==w).map(r=>{const ok=cl>=r[2],mats=Object.keys(r[1]).map(m=>{const n=bagN(m);return '<span class="'+(n>=r[1][m]?'':'gsM')+'">'+r[1][m]+' '+(IN[m]||m)+'</span>'}).join(' + ');
  return gsRow(gsIco(r[0]),crName(r),'Crafting '+r[2]+' · '+mats,ok?'<button data-gsm="'+CRR.indexOf(r)+'">Make</button>':'<span class="gsL">Level '+r[2]+'</span>')}).join('')
  +'<p class="gsP"><small>'+(R?'Hides drop from beasts. Bars come from the forge, logs from trees.':'Paper and cloth are sold here; cloth also drops from people-like monsters. Gold nuggets come from Ratio Knights and gold rocks.')+'</small></p>';
 if(GSTB=='trial'){const T=TRL[w],s=trl(w),L=lvl(st.xp[T.sk]||0),need=Object.keys(T.need).map(m=>T.need[m]+' '+IN[m]+' ('+bagN(m)+')').join(', ');
  t+='<div class="gsQ"><h3>'+T.n+'</h3>'+(s.s==2?'<p>Done. You earned the '+IN[T.k]+'.</p>':s.s==0?'<p>"Prove yourself and I will give you the '+IN[T.k]+'. Defeat 30 monsters of level 20 or higher with '+(R?'a bow':'a staff')+', then bring me '+need+'."</p><p><small>Needs '+NM[T.sk]+' 40 (you have '+L+').</small></p>'+(L>=40?'<button data-gtr="start">Start the trial</button>':'')
   :'<p>Kills with '+(R?'a bow':'a staff')+': <b>'+Math.min(30,s.k)+' / 30</b><br>Bring: '+need+'</p><button data-gtr="hand">Hand in</button>')+'</div>'}
 MB.innerHTML='<div class="gsW">'+t+'<br><button id="x">Close</button></div>';$('x').onclick=()=>M.style.display='none'}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.gsW [data-gst],.gsW [data-gsb],.gsW [data-gsm],.gsW [data-gtr]');if(!b)return;e.stopPropagation();const d=b.dataset,w=GSKD;
 if(d.gst){GSTB=d.gst;return gsDraw()}
 if(d.gsb!=null){const [k,p,n]=GSB[w][+d.gsb];if(st.coins<p)return say('You need '+p+' Meme Coins for that.','#c00');if(SHN[k]){burn(p,SHN[k]);amoAdd(k,n);say('You buy '+n+' '+SHN[k]+'.','#0a0')}
  else{const c=n||1;if(cap()<c)return say('Your bag is too full.','#c00');burn(p,IN[k]);for(let i=0;i<c;i++)st.inv.push(k);say('You buy '+(c>1?c+' ':'the ')+IN[k]+'.','#0a0')}ui();save();return gsDraw()}
 if(d.gsm!=null){const r=CRR[+d.gsm];if(lvl(st.xp.cr||0)<r[2])return say('You need a Crafting level of '+r[2]+'.','#c00');for(const m in r[1])if(bagN(m)<r[1][m])return say('You need '+r[1][m]+' '+(IN[m]||m)+'.','#c00');
  const sup=!!SHN[r[0]];if(!sup&&cap()<=0)return say('Your bag is too full.','#c00');for(const m in r[1])for(let i=0;i<r[1][m];i++)st.inv.splice(st.inv.indexOf(m),1);
  if(sup)amoAdd(r[0],r[4]);else st.inv.push(r[0]);addXp('cr',r[3]);say('You make '+crName(r)+'.','#0a0');ui();save();return gsDraw()}
 if(d.gtr){const T=TRL[w],s=trl(w);if(d.gtr=='start'){s.s=1;s.k=0;say(T.n+' started: defeat 30 monsters of level 20+ with '+(w=='r'?'a bow':'a staff')+'.','#a60')}
  else{if(s.k<30)return say('You still need '+(30-s.k)+' more kills.','#c00');for(const m in T.need)if(bagN(m)<T.need[m])return say('You need '+T.need[m]+' '+IN[m]+'.','#c00');if(cap()<=0)return say('Your bag is too full.','#c00');
   for(const m in T.need)for(let i=0;i<T.need[m];i++)st.inv.splice(st.inv.indexOf(m),1);st.inv.push(T.k);s.s=2;clog(T.k);say(T.n+' complete! '+T.who+' gives you the '+IN[T.k]+'.','#0a0')}
  ui();save();return gsDraw()}},true);
"""
CSS = r"""
#mb.gsx{max-width:560px}
#mb .gsP{font-size:13px;margin:0 0 8px}#mb .gsP small{color:#c9b58f}
.gsT{display:flex;gap:4px;margin:0 0 8px}.gsT button{flex:1}.gsT button.on{box-shadow:0 0 0 2px #ffd23f}
.gsR{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #fff1}
.gsI{flex:0 0 36px;height:36px;display:flex;align-items:center;justify-content:center}.gsI>svg{width:34px;height:34px}
.gsN{flex:1;min-width:0;font-size:13px}.gsN small{display:block;font-size:11px;color:#c9b58f}
.gsM{color:#ff8a8a}.gsL{font-size:11px;color:#888}
.gsQ{padding:8px;border:1px solid #d9a52055;border-radius:7px;background:#1a0408aa;font-size:13px}.gsQ h3{margin:0 0 4px;font:700 15px Cinzel,Georgia,serif;color:#ffd23f}
"""
i = h.index("</style>"); h = h[:i] + CSS + h[i:]
rep("function doAct(){", JS + "function doAct(){")

open(PATH, 'w', encoding='utf-8').write(h)
print('classes patch applied: ranger + mage sets, Archery + Magic shops, Crafting')
