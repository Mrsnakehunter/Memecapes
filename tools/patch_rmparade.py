#!/usr/bin/env python3
"""Ranger + mage parade: a block of nine rangers (west side) and nine mages (east side) facing each other across the Castle Gigachad courtyard, behind the knights' row (preview/test pages only, like the knight
parade of patch_armordemo.py): nine rangers in their sets with the matching bow, nine mages with the matching staff.
Every few seconds one of them takes a practice shot across the courtyard: the ranger draws and looses an arrow, the mage
casts the spell of their tier (the real Shoot / Cast motions and spell effects), landing just short of the middle.
Scenery only: no chat, no trade, never counted as players. Run after patch_bow.py:  python3 tools/patch_rmparade.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""const RMPAR=['01','10','20','30','40','50','60','70','80'].flatMap((t,i)=>[['ra'+t,'w_bw'+t,'rg',i],['ma'+t,'w_st'+t,'mg',i]]);
let RMP=null;
function rmParInit(){RMP=[];const cx=CA.x+(CA.w>>1),y0=CA.y+CA.h-5;RMPAR.forEach((a,j)=>{const i=a[3],rg=a[2]=='rg',col=i%3,row=(i/3)|0;let x=rg?CA.x+3.5+col*1.5:CA.x+CA.w-4.5-col*1.5,y=y0-4+row*1.3;for(let k=0;k<6&&solid(Math.round(x),Math.round(y));k++)x+=rg?1:-1;
 RMP.push({id:'rmp'+j,k:a[0],wk:a[1],s:a[2],tier:i,nm:(ITM[a[0]]||[a[0]])[0],lv:(ARMS[a[0]]||[0,1])[1],x,y,r:rg?Math.PI/2:-Math.PI/2,cx,t0:j*1.3,next:4000+j*900,shot:0})})}
function rmParTick(now){if(!ARMDEMO||!started)return;if(!RMP){if(!CA||!TW||!TW.length||typeof ITM=='undefined')return;rmParInit()}
 for(const o of RMP){if(Math.abs(o.x-P.px)>40||Math.abs(o.y-P.py)>40){armTagDel(o);continue}
  const m=armBody(o.k);if(!m)continue;const x=o.x+.5,z=o.y+.5;YO=hgt(x,z);
  if(now>o.next){o.shot=now;o.next=now+(o.s=='rg'?6500:7500)+Math.random()*9000;const tx=o.cx+.5+(o.s=='rg'?-1.5:1.5),tz=z;
   if(o.s=='rg')setTimeout(()=>FX.arrow(x,z,tx,tz),1200);else setTimeout(()=>FX.spell(o.tier,x,z,tx,tz,1),300)}
  const el=(now-o.shot)/1000,sh=o.shot&&el<(o.s=='rg'?1.75:1.1),cl=sh?(o.s=='rg'?'Shoot':'Cast'):'Idle',t=sh?el:now/1000+o.t0;
  qMdl(m,x,0,z,o.r,MDLSC.player,cl,t,0,null,false,1);qHold(m,x,z,o.r,cl,t,o.wk,false,null,o.s=='mg'?heldTilt(cl,t,o.wk):undefined);YO=0;
  if(!ARMTAG.has(o.id)){const d=document.createElement('div');d.className='ntag';d.textContent=o.nm+' · '+(o.s=='rg'?'Ranged ':'Magic ')+o.lv;d.style.pointerEvents='none';document.body.appendChild(d);ARMTAG.set(o.id,d)}
  armTagSet(o)}}
"""
rep("function armTagSet(o){", JS + "function armTagSet(o){")
rep("armParTick(performance.now());", "armParTick(performance.now());rmParTick(performance.now());")
open(PATH, 'w', encoding='utf-8').write(h)
print('ranger + mage parade added')
