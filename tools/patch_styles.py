#!/usr/bin/env python3
"""Three ways to fight from the very first minute: melee, ranged and magic (Albert, Nov 1: "people should have a chance
to use mage melee or range right off the bat"; his picks: all three in the starter pack, spells use spell items,
bows + arrows, a combat triangle).

  Skills     Ranged (rg) and Magic (mg), levels 1-100, own skill coins, Mastery capes, count toward combat level.
  Ranged     nine bows, one per armour tier (models/w_bwNN.json from tools/mkbow.py), Ranged level to wield.
             Arrows live in your quiver (Paper / Iron / Diamond); the best ones you can use are fired first.
  Magic      a staff to cast with (Paper Staff; the Bog shaman staff, Infinite scroll and Algorithm staff are now
             magic weapons too). Spells cost spell scrolls (Spark / Blast / Nova) from your scroll pouch.
             Nine spells by Magic level; pick one in the Magic tab or let the game cast the best one you can pay for.
  Range      bows reach 7 tiles, staffs 8: you stop and shoot, the monster has to come to you.
  Triangle   melee beats ranged, ranged beats magic, magic beats melee: +15% accuracy and max hit against the style
             a monster is weak to, -15% against the one it resists. Every monster's examine text says which.
  Supplies   Party Shop: Paper / Iron arrows, Spark / Blast scrolls, a spare bow and staff. Monsters drop arrows and
             scrolls (Nova scrolls only from strong monsters and bosses).
  Starter    everyone gets a Paper Bow, a Paper Staff, 150 Paper arrows and 100 Spark scrolls once.
Quiver and pouch are counts on the save (st.amo), not bag items, so they never fill the bag and can't be traded (v1).
Run after patch_mdlv.py:  python3 tools/patch_styles.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---------------------------------------------------------------- skills
rep("const NM={at:'Attack',str:'Strength',def:'Defence',hp:'Health',",
    "const NM={at:'Attack',str:'Strength',def:'Defence',rg:'Ranged',mg:'Magic',hp:'Health',")
rep(".34*(lvl(st.xp.at)+lvl(st.xp.str))",
    ".34*Math.max(lvl(st.xp.at)+lvl(st.xp.str),1.5*lvl(st.xp.rg||0),1.5*lvl(st.xp.mg||0))")
rep("['str','def','pr','ag','sl','fm','fa','cn'].forEach(k=>{if(st.xp[k]==null)st.xp[k]=0})",
    "['str','def','pr','ag','sl','fm','fa','cn','rg','mg'].forEach(k=>{if(st.xp[k]==null)st.xp[k]=0})")
rep("cn:'#c8a060'};\nObject.keys(CAPEC)", "cn:'#c8a060',rg:'#2e8a4a',mg:'#3a4ad8'};\nObject.keys(CAPEC)")

# ---------------------------------------------------------------- items
BW = [  # key, name, colour, examine, rarity, sell, Ranged level, [accuracy, ranged strength]
    ('bw01', 'Paper Bow', '#d8cdb0', 'Card, glue and a hopeful string.', 0, 2, 1, [3, 0]),
    ('bw10', 'Copper Coin Bow', '#c87533', 'Copper limbs, a coin on the grip. Heads you hit.', 1, 25, 10, [8, 4]),
    ('bw20', 'HODL Iron Bow', '#6f747c', 'Iron limbs that never bend the wrong way.', 1, 60, 20, [16, 8]),
    ('bw30', 'Bull Steel Bow', '#c9ced6', 'Bright steel. Every shot goes up and to the right.', 2, 110, 30, [26, 14]),
    ('bw40', 'Gold Rush Bow', '#e0b545', 'Gold over steel. The arrows come back richer.', 2, 180, 40, [38, 20]),
    ('bw50', 'Diamond Hands Bow', '#8fd3ff', 'A diamond bow. It never lets go of the string early.', 3, 280, 50, [52, 28]),
    ('bw60', 'Whale Bow', '#1f6b78', 'Deep-sea steel. One shot moves the whole market.', 3, 400, 60, [66, 36]),
    ('bw70', 'Moonforged Bow', '#dfe6f5', 'Strung with moonlight. Quietest bow in the game.', 4, 550, 70, [82, 46]),
    ('bw80', 'Legendary Meme Bow', '#b01830', 'Crimson and gold. The most feared bow in the game.', 4, 800, 80, [100, 58]),
]
items = ''.join(f"{k}:['{n}','bow','{c}','{e}',{r},0,{s},0]," for k, n, c, e, r, s, q, st in BW)
items += "st01:['Paper Staff','staff','#d8cdb0','Rolled-up paper with a spark at the end. It casts.',0,0,2,0],"
rep("iscroll:['Infinite scroll','scroll','#8a4aff','It never ends.',3,0,0,5],",
    "iscroll:['Infinite scroll','scroll','#8a4aff','It never ends.',3,0,0,5]," + items)
rep("sw80:[100, 98, 4]};", "sw80:[100, 98, 4]," + ','.join(f"{k}:[0,0,4]" for k, *_ in BW) + ",st01:[2,1,5]};")
rep("const GV0={coin:1,", "const GV0={coin:1," + ','.join(f"{k}:{s * 8}" for k, n, c, e, r, s, q, st in BW) + ",st01:16,")
rep("const NOTRADE=k=>k=='coin'||", "const NOTRADE=k=>k=='coin'||k=='bw80'||")
# a bow icon shape (painted pictures in icons/items3 replace it where they exist)
rep("const ICT={food:", "const ICT={bow:c=>'<path d=\"M7 3c7 3 7 15 0 18\" fill=\"none\" stroke=\"#2a1604\" stroke-width=\"4\" stroke-linecap=\"round\"/>"
    "<path d=\"M7 3c7 3 7 15 0 18\" fill=\"none\" stroke=\"'+c+'\" stroke-width=\"2.4\" stroke-linecap=\"round\"/>"
    "<path d=\"M7 3v18\" stroke=\"#f4ead2\" stroke-width=\".8\"/><rect x=\"11.2\" y=\"10\" width=\"2.6\" height=\"4\" rx=\"1\" fill=\"#5a3a1a\"/>',food:")

# in the hand: an upright bow like a staff; the Paper Staff (tools/mkstaff.py) like the other staffs
rep("},HTEST=null;", "},HTEST=null;Object.assign(WCFG,{" + ','.join(f"w_{k}:[1.3,.5,'v',6,8]" for k, *_ in BW) + ",w_st01:[1.6,.33,'v',22,8]});", 1)

# level to wield
rq = ','.join(f"{k}:['rg',{q}]" for k, n, c, e, r, s, q, st in BW) + ",st01:['mg',1],bstaff:['mg',10],iscroll:['mg',20],astaff:['mg',30]"
rep("function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;",
    "const WRQ={" + rq + "};\n"
    "function equip(i){const k=st.inv[i],sl=slotOf(k);if(!sl)return;"
    "if(WRQ[k]&&lvl(st.xp[WRQ[k][0]]||0)<WRQ[k][1])return say('You need a '+NM[WRQ[k][0]]+' level of '+WRQ[k][1]+' to wield the '+IN[k]+'.','#c00');")
rep("if(WREQ[k]&&lvl(st.xp.at)<WREQ[k])continue;",
    "if(WREQ[k]&&lvl(st.xp.at)<WREQ[k])continue;if(WRQ[k])continue;")

# ---------------------------------------------------------------- the fighting code
bst = ','.join(f"{k}:{st}" for k, n, c, e, r, s, q, st in BW)
JS = r"""
// ---- three ways to fight (tools/patch_styles.py): melee, ranged, magic + the combat triangle
const BST={""" + bst + r"""},MST={st01:[6,0],bstaff:[10,5],iscroll:[18,10],astaff:[22,15]};
const ARW=[['a1','Paper arrows',1,4,'#e8dcc0'],['a2','Iron arrows',20,12,'#9aa2ac'],['a3','Diamond arrows',50,25,'#8fd3ff']];
const SCR=[['ss','Spark scrolls','#ffd23f'],['bs','Blast scrolls','#ff7a2a'],['ns','Nova scrolls','#8fd3ff']],SCRN={ss:'Spark',bs:'Blast',ns:'Nova'};
// name, Magic level, scrolls per cast, max hit, colour, base XP, what it does
const SPL=[['Spark',1,{ss:1},3,'#ffd23f',5.5,'A little zap. Everyone starts here.'],
['Pump',10,{ss:2},6,'#58f0a6',9,'Green candles only.'],
['FOMO Blast',20,{bs:1},9,'#ff7a2a',13,'Hits before they can think.'],
['Rug Pull',30,{bs:1,ss:2},12,'#c77dff',17,'Pulls the rug: the target loses its next swing.'],
['Moon Beam',40,{bs:2},15,'#dfe6f5',21,'Straight up, straight down.'],
['Diamond Storm',50,{ns:1},19,'#8fd3ff',26,'A storm of diamonds that never sells.'],
['Whale Wave',60,{ns:1,bs:2},23,'#1fb6c8',31,'One wave moves the whole market.'],
['Moonfire',70,{ns:2},27,'#ffb3e6',36,'Fire from the far side of the moon.'],
['Legend Nova',80,{ns:2,bs:2},32,'#ff3050',42,'The loudest spell in the game.']];
const wSty=()=>{const w=bestW();return BST[w]?'rg':MST[w]?'mg':'me'},STYN={me:'Melee',rg:'Ranged',mg:'Magic'};
const rch=()=>{const s=wSty();return s=='rg'?7:s=='mg'?8:1};
const inR_=(t,R)=>!(t.x==P.x&&t.y==P.y)&&Math.max(Math.abs(t.x-P.x),Math.abs(t.y-P.y))<=R;
function pouch(){if(!st.amo||typeof st.amo!='object')st.amo={};return st.amo}
const amoN=k=>pouch()[k]|0;
function amoAdd(k,n){const a=pouch();a[k]=Math.max(0,(a[k]|0)+n);if(!a[k])delete a[k]}
const canPay=c=>Object.keys(c).every(k=>amoN(k)>=c[k]),costTx=c=>Object.keys(c).map(k=>c[k]+' '+SCRN[k]).join(' + ');
function bestArrow(){const l=lvl(st.xp.rg||0);for(let i=ARW.length-1;i>=0;i--){const a=ARW[i];if(amoN(a[0])>0&&l>=a[2])return a}return null}
function curSpell(){const l=lvl(st.xp.mg||0),i=st.spl;if(i!=null&&SPL[i]&&SPL[i][1]<=l)return canPay(SPL[i][2])?SPL[i]:null;for(let j=SPL.length-1;j>=0;j--)if(SPL[j][1]<=l&&canPay(SPL[j][2]))return SPL[j];return null}
// the triangle: a beats BEAT[a]; monsters fight with mt.fs
const BEAT={me:'rg',rg:'mg',mg:'me'};
const tri=(s,mt)=>BEAT[s]==mt.fs?1.15:BEAT[mt.fs]==s?.85:1;
MT.forEach(m=>{const mg=/Shaman|Cultist|Jester|Ghost|Wizard|Witch/.test(m.n);m.fs=mg?'mg':(m.rng||1)>1?'rg':'me';const wk=Object.keys(BEAT).find(s=>BEAT[s]==m.fs),rs=BEAT[m.fs];
 m.ex=(m.ex||'')+' '+({me:'Fights up close',rg:'Fights from range',mg:'Fights with magic'})[m.fs]+': weak to '+STYN[wk].toLowerCase()+', resists '+STYN[rs].toLowerCase()+'.'});
function castAnim(){pAnim={k:'cast',t0:performance.now(),d:900};pAnim.d=aDur('cast',900,2000)}
function rgAtk(gb,mt,s){const cs=st.cs||0,w=bestW();let acc,mh,col,sp=null,ar=null;
 const hc=A=>{const D=((mt.def||1)+(tickN<(gb.defT||0)?(gb.defB||0):0)+9)*64;return A>D?1-(D+2)/(2*(A+1)):A/(2*(D+1))};
 if(s=='rg'){ar=bestArrow();if(!ar){act=null;say(ARW.some(a=>amoN(a[0])>0)?'You need a higher Ranged level for the arrows in your quiver.':'Your quiver is empty. Buy arrows at the Party Shop.','#c00');return 1}
  const B=BST[w],l=lvl(st.xp.rg||0),eA=l+(cs==0?3:cs==3?1:0)+8,eS=l+(cs==1?3:cs==3?1:0)+8;acc=hc(eA*(B[0]+64));mh=Math.floor(.5+eS*(B[1]+ar[3]+64)/640);amoAdd(ar[0],-1);col=ar[4];
  if(amoN(ar[0])==10)say('Only 10 '+ar[1]+' left in your quiver.','#c60')}
 else{sp=curSpell();if(!sp){act=null;const c=st.spl!=null&&SPL[st.spl];say(c&&c[1]<=lvl(st.xp.mg||0)?'Not enough scrolls for '+c[0]+' ('+costTx(c[2])+'). Pick another spell in the Magic tab, or buy scrolls at the Party Shop.':'You have no spell scrolls. Buy Spark scrolls at the Party Shop.','#c00');return 1}
  const B=MST[w],l=lvl(st.xp.mg||0),eA=l+(cs==0?3:cs==3?1:0)+8;acc=hc(eA*(B[0]+64));mh=Math.floor(sp[3]*(1+B[1]/100)+(cs==1?1:0));for(const k in sp[2])amoAdd(k,-sp[2][k]);col=sp[4]}
 const T=tri(s,mt);acc=Math.min(1,acc*T);mh=Math.max(1,Math.floor(mh*T));lastCbt=tickN;castAnim();
 let d=Math.random()<acc?Math.floor(Math.random()*(mh+1)):0;
 if(d>0&&(mt.sp=='ratio'||mt.sp=='boss')){const ky=s+cs;gb.same=gb.ls===ky?(gb.same||0)+1:0;gb.ls=ky;if(gb.same>=3){d=Math.max(1,Math.floor(d*.25));if(gb.same==3){gb.ratiod=1;bubble(gb,"RATIO'D");say(mt.n+' is resisting your '+STYN[s]+' '+STY[cs]+' style. Switch style or weapon!','#c00')}}}
 d=Math.min(d,gb.hp);gb.hp-=d;
 PJ.push({x0:P.px+.5,z0:P.py+.5,x1:gb.px+.5,z1:gb.py+.5,t0:performance.now(),c:col,k:s});
 setTimeout(()=>{fl(gb.x,gb.y,d,d?'#d22':'#39f');if(d)gb.hitT=performance.now()},390);
 const sk=s=='rg'?'rg':'mg';if(sp)addXp('mg',cs==2?sp[5]/2:sp[5]);
 if(d){if(cs==2){addXp(sk,2*d);addXp('def',2*d)}else addXp(sk,(s=='rg'?4:2)*d);addXp('hp',1.33*d)}
 if(sp&&sp[0]=='Rug Pull'&&d>0)gb.cd=(gb.cd||0)+2;
 if(gb.hp<=0)killMob(gb);return s=='rg'?(cs==1?3:4):5}
// drops: arrows and scrolls go straight into the quiver / pouch
function pouchDrop(mt){const lv=mt.lv||1,got=[],R=(a,b)=>a+Math.floor(Math.random()*(b-a+1)),g=(k,n,nm)=>{amoAdd(k,n);got.push(n+' '+nm)};
 if(mt.boss||mt.sp=='boss'){g('ns',R(5,12),'Nova scrolls');g('bs',R(10,20),'Blast scrolls');g('a3',R(10,25),'Diamond arrows')}
 else{if(lv>=4&&Math.random()<.22)g('a1',R(5,15),'Paper arrows');if(lv>=4&&Math.random()<.18)g('ss',R(4,10),'Spark scrolls');
  if(lv>=20&&Math.random()<.12)g('a2',R(4,12),'Iron arrows');if(lv>=18&&Math.random()<.1)g('bs',R(2,6),'Blast scrolls');
  if(lv>=40&&Math.random()<.04)g('a3',R(3,8),'Diamond arrows');if(lv>=40&&Math.random()<.035)g('ns',R(1,3),'Nova scrolls')}
 if(got.length)say('Loot: '+got.join(', ')+' (in your quiver and scroll pouch).','#a60')}
// the Party Shop: supplies sold in bundles
const SHA=[['a1',50,20],['a2',50,150],['ss',50,25],['bs',25,200]],SHN={a1:'Paper arrows',a2:'Iron arrows',a3:'Diamond arrows',ss:'Spark scrolls',bs:'Blast scrolls',ns:'Nova scrolls'};
function amoIco(k){const c={a1:'#e8dcc0',a2:'#9aa2ac',a3:'#8fd3ff',ss:'#ffd23f',bs:'#ff7a2a',ns:'#8fd3ff'}[k];return k[0]=='a'?'<svg viewBox="0 0 24 24" class="fsI"><path d="M4 20 18 6" stroke="#5a3a1a" stroke-width="2"/><path d="M18 6l-4 .5L17.5 10z" fill="'+c+'" stroke="#2a1604" stroke-width=".6"/><path d="M4 20l1-4 2 2zM6 18l-1-4 2 2" fill="#f4ead2"/></svg>':'<svg viewBox="0 0 24 24" class="fsI"><rect x="5" y="4" width="14" height="16" rx="2" fill="#f1e2b8" stroke="#5a3a1a"/><rect x="4" y="3" width="16" height="3" rx="1.5" fill="#c9a060" stroke="#5a3a1a"/><rect x="4" y="18" width="16" height="3" rx="1.5" fill="#c9a060" stroke="#5a3a1a"/><circle cx="12" cy="12" r="3.4" fill="'+c+'" stroke="#2a1604" stroke-width=".6"/></svg>'}
function SHPA(){return '<div class="fsH">Arrows and spell scrolls <small>(go straight into your quiver and scroll pouch)</small></div>'+SHA.map(([k,n,p],i)=>'<div class="row"><span>'+amoIco(k)+n+' '+SHN[k]+' <small>(you have '+amoN(k)+')</small></span><button data-amb="'+i+'">'+p+' Meme Coins</button></div>').join('')+'<br>'}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-amb]');if(!b)return;const [k,n,p]=SHA[+b.dataset.amb];if(st.coins<p)return say('You need '+p+' Meme Coins for that.','#c00');burn(p,SHN[k]);amoAdd(k,n);say('You buy '+n+' '+SHN[k]+'.','#0a0');ui();save();modal('shop')},true);
// Gear tab: fighting style, quiver and pouch
function PCH(){const s=wSty(),l=s=='rg'?lvl(st.xp.rg||0):s=='mg'?lvl(st.xp.mg||0):0,sp=s=='mg'?curSpell():null,ar=s=='rg'?bestArrow():null;
 let t='<div class="fsP"><div class="fsH">Fighting style: <b>'+STYN[s]+'</b>'+(s!='me'?' <small>· reach '+rch()+' tiles</small>':'')+'</div>';
 if(s=='rg')t+='<div class="fsL">'+(ar?'Firing '+ar[1]+' · max hit '+Math.floor(.5+(l+8+(st.cs==1?3:st.cs==3?1:0))*(BST[bestW()][1]+ar[3]+64)/640):'<span style="color:#ff8080">No arrows you can use</span>')+'</div>';
 if(s=='mg')t+='<div class="fsL">'+(sp?'Casting '+sp[0]+' · max hit '+Math.floor(sp[3]*(1+MST[bestW()][1]/100)):'<span style="color:#ff8080">No spell you can pay for</span>')+' · <a href="#" data-sub="magic" class="fsA">spells</a></div>';
 if(s=='me')t+='<div class="fsL">Wield a bow for Ranged or a staff for Magic.</div>';
 t+='<div class="fsQ">'+ARW.concat(SCR).map(a=>'<span title="'+(SHN[a[0]])+'">'+amoIco(a[0])+'<b>'+amoN(a[0])+'</b></span>').join('')+'</div><div class="fsL" style="opacity:.75">Melee beats Ranged · Ranged beats Magic · Magic beats Melee. Examine a monster to see what it is weak to.</div></div>';return t}
// Magic tab: the spell book
function MGH(){const l=lvl(st.xp.mg||0),cur=curSpell(),w=bestW();
 let t='<div class="fsH">Spell book <small>· Magic '+l+(MST[w]?'':' · <span style="color:#ff8080">wield a staff to cast</span>')+'</small></div><div class="fsQ" style="margin-bottom:6px">'+SCR.map(a=>'<span>'+amoIco(a[0])+'<b>'+amoN(a[0])+'</b> '+SCRN[a[0]]+'</span>').join('')+'</div><div class="fsG">';
 SPL.forEach((p,i)=>{const lk=p[1]>l,on=st.spl===i||(st.spl==null&&cur===p);t+='<button class="fsS'+(lk?' lk':'')+(on?' on':'')+(lk||canPay(p[2])?'':' poor')+'" data-spl="'+i+'" style="--c:'+p[4]+'"'+(lk?' disabled':'')+'><i></i><b>'+p[0]+'</b><small>'+(lk?'Magic '+p[1]:'max '+p[3]+' · '+costTx(p[2]))+'</small></button>'});
 return t+'</div><div class="fsL" style="margin:6px 0 10px">'+(st.spl==null?'Auto: casts the best spell you have scrolls for. Tap a spell to always cast it.':'Always casting '+SPL[st.spl][0]+'. <a href="#" data-spl="auto" class="fsA">Back to auto</a>')+'</div>'}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-spl]');if(!b)return;e.preventDefault();e.stopPropagation();const v=b.dataset.spl;st.spl=v=='auto'||st.spl===+v?null:+v;if(st.spl!=null)say('You will cast '+SPL[st.spl][0]+'. '+SPL[st.spl][6],'#a60');save();renderPanel()},true);
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a.fsA[data-sub]');if(!a)return;e.preventDefault();e.stopPropagation();tab='more';SUB='magic';renderPanel()},true);
"""
CSS = r"""
.fsP{margin-top:8px;padding:7px;border:1px solid #d9a52055;border-radius:7px;background:linear-gradient(180deg,#2a0a10,#1a0408);font-size:11px;color:#f6eedc}
.fsH{font:700 12px Cinzel,Georgia,serif;color:#ffd23f;margin:2px 0 4px}.fsH small{font:11px Alegreya,Georgia,serif;color:#c9b58f}.fsH b{color:#fff}
.fsL{color:#d9c8a8;font-size:11px;margin:2px 0}.fsA{color:#ffd23f}
.fsQ{display:flex;flex-wrap:wrap;gap:4px 10px;margin:5px 0}.fsQ span{display:inline-flex;align-items:center;gap:2px;font-size:11px;color:#d9c8a8}.fsQ b{color:#fff}
.fsI{width:20px;height:20px;vertical-align:middle;margin-right:3px}
.fsG{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.fsS{--c:#ffd23f;position:relative;display:flex;flex-direction:column;align-items:center;gap:1px;padding:7px 2px 5px!important;font-size:10px!important;line-height:1.15;border-radius:6px!important}
.fsS i{width:22px;height:22px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff 0,var(--c) 40%,color-mix(in srgb,var(--c) 45%,#000) 100%);box-shadow:0 0 10px var(--c),inset 0 0 0 1px #0008;margin-bottom:2px}
.fsS b{font:700 10px Cinzel,Georgia,serif}.fsS small{font-size:9px;opacity:.85}
.fsS.on{box-shadow:0 0 0 2px #ffd23f,0 0 12px #ffd23f88!important}
.fsS.lk{opacity:.45;filter:grayscale(.7)}.fsS.lk i{box-shadow:none}.fsS.poor small{color:#ff9a9a}
.fsT{margin-top:6px}
"""
i = h.index("</style>"); h = h[:i] + CSS + h[i:]
rep("function doAct(){", JS + "function doAct(){")

# reach: stop at bow / spell range instead of walking up next to the monster
rep("if(tg){if(adj(tg,P))return false;const p=bfs((x,y)=>Math.abs(x-tg.x)+Math.abs(y-tg.y)==1);",
    "if(tg){const R_=act.k=='gob'?rch():1;if(R_>1?inR_(tg,R_):adj(tg,P))return false;const p=bfs(R_>1?(x,y)=>!(x==tg.x&&y==tg.y)&&Math.max(Math.abs(x-tg.x),Math.abs(y-tg.y))<=R_:(x,y)=>Math.abs(x-tg.x)+Math.abs(y-tg.y)==1);")
rep("else if(adj(tg,P))doAct()", "else if(act.k=='gob'&&rch()>1?inR_(tg,rch()):adj(tg,P))doAct()")
# the attack: bows and staffs shoot, everything else swings (now with the triangle too)
rep("if(k=='gob'){const gb=act.ref,mt=MT[gb.t];gb.prov=1;hitT=performance.now();if(--atkCd>0)return;",
    "if(k=='gob'){const gb=act.ref,mt=MT[gb.t];gb.prov=1;hitT=performance.now();if(--atkCd>0)return;{const s_=wSty();if(s_!='me'){atkCd=rgAtk(gb,mt,s_);return}}")
rep("let acc2=acc,mh2=mh,hits=1;", "const T_=tri('me',mt);let acc2=Math.min(1,acc*T_),mh2=Math.floor(mh*T_),hits=1;")
# flying arrows and spells (the monsters' projectile list)
rep("ball(x,hgt(x,z)+1.1+Math.sin(f*Math.PI)*.7,z,.14,.14,.14,0,q.c,6)}",
    "if(q.k=='rg'){ball(x,hgt(x,z)+1.25+Math.sin(f*Math.PI)*.4,z,.05,.05,.42,Math.atan2(q.x1-q.x0,q.z1-q.z0),q.c,6)}"
    "else if(q.k=='mg'){const y_=hgt(x,z)+1.3+Math.sin(f*Math.PI)*.25;ball(x,y_,z,.2,.2,.2,0,q.c,8);for(let j=1;j<4;j++){const g=Math.max(0,f-j*.07),xx=q.x0+(q.x1-q.x0)*g,zz=q.z0+(q.z1-q.z0)*g,r=.14-.03*j;ball(xx,y_,zz,r,r,r,0,q.c,8)}}"
    "else ball(x,hgt(x,z)+1.1+Math.sin(f*Math.PI)*.7,z,.14,.14,.14,0,q.c,6)}")
# the cast motion (the blocky body uses its punch pose)
rep("home:['Cast'],", "home:['Cast'],cast:['Cast','Punch','Attack'],")
rep("const PS={\n", "const PS={\ncast:f=>PS.punch(f),\n")

# UI hooks
rep("function EQH(){return EQH0()+", "function EQH(){return EQH0()+PCH()+")
rep("if(SUB=='magic'){const left=", "if(SUB=='magic'){h+=MGH();const left=")
rep("h+='<br>Sell for Meme Coins: gathered goods", "h+=SHPA();h+='<br>Sell for Meme Coins: gathered goods")
rep("['sword',40],['cake',5]", "['sword',40],['bw01',30],['st01',30],['cake',5]")
rep("say(msg+'.','#a60');let lost=0;", "say(msg+'.','#a60');pouchDrop(mt);let lost=0;")

# starter pack: a bow, a staff, arrows and scrolls for everyone, once
rep("if(!st.kitSw){st.kitSw=1;",
    "if(!st.kitRM){st.kitRM=1;['bw01','st01'].forEach(k=>{if(!has(k)&&!eqd(k)&&cap()>0)st.inv.push(k)});amoAdd('a1',150);amoAdd('ss',100);"
    "if(st.eqDone)say('New: Ranged and Magic! A Paper Bow, a Paper Staff, 150 arrows and 100 Spark scrolls are yours. Wield the bow or the staff from your bag.','#a60')}"
    "if(!st.kitSw){st.kitSw=1;")

# skill coins for the two new skills
rep("let scSel=null;const SCUP={};",
    "Object.assign(SCC,{rg:'#2e8a4a',mg:'#3a4ad8'});"
    "Object.assign(SCI,{rg:'<path d=\"M7 3c8 3 8 15 0 18M7 3v18M5 12h14m0 0-3-2.5M19 12l-3 2.5\"/>',"
    "mg:'<path d=\"M6 20 15 11M15 11l1-4 2 2-4 1zM18 3l.7 1.6L20.3 5.3l-1.6.7L18 7.6l-.7-1.6-1.6-.7 1.6-.7zM8 6l.5 1 1 .5-1 .5L8 9l-.5-1-1-.5 1-.5z\"/>'});"
    "Object.assign(SCW,{rg:'Shoot from 7 tiles away. Better bows and arrows as you level.',mg:'Cast from 8 tiles away with a staff and spell scrolls. New spells as you level.'});"
    "let scSel=null;const SCUP={};")
rep("if(k=='cn')Object.values(FURN)",
    "if(k=='rg'){Object.keys(WRQ).forEach(w=>{if(WRQ[w][0]=='rg')u.push([WRQ[w][1],IN[w]])});ARW.forEach(a=>u.push([a[2],a[1]]))}"
    "if(k=='mg'){SPL.forEach(p=>u.push([p[1],p[0]+' spell']));Object.keys(WRQ).forEach(w=>{if(WRQ[w][0]=='mg')u.push([WRQ[w][1],IN[w]])})}"
    "if(k=='cn')Object.values(FURN)")

open(PATH, 'w', encoding='utf-8').write(h)
print('styles patch applied: melee, ranged, magic')
