#!/usr/bin/env python3
"""The armour parade: nine knights in the castle courtyard, one per armour set, so the sets can be seen in the game.

Shown in the preview and test pages only (or anywhere with MC_CONFIG.armorDemo = 1): a row in front of the keep's
steps at Castle Gigachad, each knight in one set with a cape and a sword, standing at ease, turning to face a player
who walks up, with a name tag "Gold Rush · Defence 40". They are scenery: no chat, no trade, no level tag, never
counted as players.
Run after patch_armorget.py:  python3 tools/patch_armordemo.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""const ARMDEMO=(window.MC_CONFIG&&MC_CONFIG.armorDemo!=null)?!!MC_CONFIG.armorDemo:/preview|test/i.test(location.pathname);
const ARMPAR=[['arm01','Paper Hands',1,'ccape'],['arm10','Copper Coin',10,'qcape'],['arm20','HODL Iron',20,'memecape'],['arm30','Bull Steel',30,'ccape'],['arm40','Gold Rush',40,'memecape'],['arm50','Diamond Hands',50,'qcape'],['arm60','Whale Plate',60,'memecape'],['arm70','Moonforged',70,'ccape'],['arm80','Legend of the Meme',80,'memecape']];
let ARMP=null;const ARMTAG=new Map();
function armParInit(){ARMP=[];const cx=CA.x+(CA.w>>1),y0=CA.y+CA.h-5;ARMPAR.forEach((a,i)=>{let x=cx+(i-4)*1.6,y=y0;for(let k=0;k<6&&solid(Math.round(x),Math.round(y));k++)y+=1;ARMP.push({id:'armp'+i,k:a[0],nm:a[1],lv:a[2],cape:a[3],x,y,r:0,tr:0,t0:i*1.7})})}
function armParTick(now){if(!ARMDEMO||!started)return;if(!ARMP){if(!CA||!TW||!TW.length)return;armParInit()}
 const dt=Math.min(.1,(now-(armParTick.lt||now))/1000);armParTick.lt=now;
 for(const o of ARMP){if(Math.abs(o.x-P.px)>40||Math.abs(o.y-P.py)>40){armTagDel(o);continue}
  const dp=Math.hypot(P.px-o.x,P.py-o.y);o.tr=dp<7?Math.atan2(P.px-o.x,P.py-o.y):0;let dr=o.tr-o.r;dr=Math.atan2(Math.sin(dr),Math.cos(dr));o.r+=dr*Math.min(1,dt*6);
  const m=armBody(o.k);if(!m)continue;const x=o.x+.5,z=o.y+.5,t=now/1000+o.t0;YO=hgt(x,z);
  qMdl(m,x,0,z,o.r,MDLSC.player,'Idle',t,0,null,false,1);const AC=armCape(o.k,o.cape,null);if(AC)qMdl(AC,x,0,z,o.r,MDLSC.player,'Idle',t,0,null,false,1);
  qHold(m,x,z,o.r,'Idle',t,'w_isword',false,null,heldTilt('Idle',t,'w_isword'));YO=0;armTagSet(o)}}
function armTagSet(o){let d=ARMTAG.get(o.id);if(!d){d=document.createElement('div');d.className='ntag';d.textContent=o.nm+' · Defence '+o.lv;d.style.pointerEvents='none';document.body.appendChild(d);ARMTAG.set(o.id,d)}
 const p=[o.x+.5-E[0],2.1+hgt(o.x+.5,o.y+.5)-E[1],o.y+.5-E[2]],zz=d3(p,Fw);if(zz<=0){d.style.display='none';return}
 const sx=d3(p,Rt)/(zz*TH*asp),sy=d3(p,Up)/(zz*TH);d.style.display=(Math.abs(sx)>1.1||Math.abs(sy)>1.1||zz>30)?'none':'block';d.style.left=((sx+1)/2*CW)+'px';d.style.top=((1-sy)/2*CH)+'px'}
function armTagDel(o){const d=ARMTAG.get(o.id);if(d){d.remove();ARMTAG.delete(o.id)}}
"""
rep("function armKey(){", JS + "function armKey(){")
rep("wndTick(performance.now());", "wndTick(performance.now());armParTick(performance.now());")
open(PATH, 'w', encoding='utf-8').write(h)
print('armour parade patch applied')
