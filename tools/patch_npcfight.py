#!/usr/bin/env python3
"""Monsters and NPCs hold real weapons and fight with real attack motions.

Before: no monster or NPC held anything (the Meshy characters were made empty-handed), an "attack" was the model
sliding a little towards you, a standing monster was frozen mid-stride, a killed one vanished on the spot, and the
town guards stood frozen without swords.

Now (with the motions from tools/npc_clips.py):
  - Every armed monster holds its weapon in its hand bone (the same grip code as the player's), so the weapon
    follows every swing: guards and Ratio Knights sword and shield, Bonk hounds a bat, Floki an axe, the Rage
    Goblin a spiked club, shamans and cultists staffs, and so on. Fist fighters punch and kick.
  - Each attack plays a real motion picked for the weapon: a sword slash or a stab, an overhead BONK, a punch or a
    kick, a spell cast for ranged attackers. The wind-up starts on the tick before the hit, so the blow lands on
    the same moment the hit splat appears (and a spell's bolt leaves the hand as it is thrown).
  - Monsters flinch when you hit them, and fall down when they die (then sink away), instead of vanishing.
  - Standing monsters, guards, bankers, shopkeepers and pets breathe (idle motion) instead of freezing mid-step.
  - The Bouncy Hippo's 3D model was broken (a centimetre tall: invisible); it uses its hand-built model again.
Run from the repo root after the other patches:  python3 tools/patch_npcfight.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- held weapons work for any character size
rep("function qHold(PM,x,z,yaw,clip,t,wk,left){", "function qHold(PM,x,z,yaw,clip,t,wk,left,sc,dd){")
# dd: blade tilt override (degrees) for straight weapons, so an NPC at ease holds its sword or club lowered at its side
rep("O=left?SOFF:FOFF(cf[2],cf[3]||0,cf[4]||0)", "O=left?SOFF:FOFF(cf[2],dd!=null&&cf[2]=='f'?dd:(cf[3]||0),cf[4]||0)")
rep("sP=MDLSC.player,R=[H[0]", "sP=sc||MDLSC.player,R=[H[0]")

# ---- who holds what and fights how: [right hand, left hand, attack motions]
NPCW = r"""
// ---- monsters and NPCs: weapons and attack motions (tools/patch_npcfight.py, motions from tools/npc_clips.py)
const NPCW={'k:guard':['w_isword','w_rshield',['Attack','Stab']],'k:rknight':['w_rsword','w_rshield',['Attack','Stab']],
 'k:bonk':['w_bbat',null,['Mine']],'m:bonk':['w_bbat',null,['Mine','Attack']],'k:rage':['w_club',null,['Mine','Attack']],
 'k:wojakw':['w_bbat',null,['Attack']],'m:floki':['w_iaxe',null,['Attack','Mine']],'k:shiba':['w_sword',null,['Attack','Stab']],
 'm:mog':['w_sword',null,['Attack','Stab']],'k:pepe':['w_bstaff',null,['Attack','Stab']],'k:bog':['w_bstaff',null,['Cast']],
 'k:cult':['w_astaff',null,['Cast']],'k:botcap':['w_astaff',null,['Attack','Stab']],'k:jester':['w_iscroll',null,['Attack','Kick']],
 'k:doom':[null,null,['Cast']],'m:bome':[null,null,['Cast']],'k:chad':[null,null,['Punch','Kick']],'k:giga':[null,null,['Punch','Kick']],
 'k:clout':[null,null,['Punch','Kick']],'k:spambot':[null,null,['Punch']],'k:doge':[null,null,['Punch']],'k:wif':[null,null,['Punch']],
 'k:chill':[null,null,['Punch']],'k:ghound':[null,null,['Punch','Kick']],'m:fart':[null,null,['Punch']],'m:pnut':[null,null,['Punch','Kick']],
 'm:popcat':[null,null,['Punch']],'m:slerf':[null,null,['Punch']]},
// motion timing in seconds: [moment the blow lands, end, wind-up shown before the blow]
NCL={Attack:[.58,1.4,.58],Stab:[.5,.86,.5],Punch:[.33,1.0,.33],Kick:[.58,1.1,.58],Mine:[1.62,1.75,1.0],Cast:[.67,1.6,.6]};
function mobKey(t){const mt=MT[t];return mt.mdl?'m:'+mt.mdl:'k:'+mt.k}
function npcPick(gb){const W=NPCW[mobKey(gb.t)];if(!W)return null;const L=W[2];return L[Math.floor(Math.random()*L.length)]}
// called every tick while a monster waits to strike: start the wind-up so the blow lands on the attack tick
function mobWind(gb){const c=gb.nxC||(gb.nxC=npcPick(gb));if(!c)return;const need=Math.ceil(NCL[c][2]/.6);if(gb.cd<=need&&!gb.wound){gb.atkC=c;gb.swT=performance.now()+gb.cd*600;gb.wound=1}}
// the attack really happens now: line the blow up with this moment
function mobSwing(gb){const now=performance.now();if(gb.wound&&gb.atkC&&Math.abs(now-gb.swT)<450)gb.swT=now;else{gb.atkC=gb.nxC||npcPick(gb);gb.swT=now+180}gb.wound=0;gb.nxC=null}
// which motion and time a model monster shows right now
function npcPose(gb,mm,d,now,i){if(gb.dieT)return mm.clips.Death?['Death',Math.min((now-gb.dieT)/1000,2.1)]:null;
 const c=gb.atkC,A=c&&NCL[c],C=A&&mm.clips[c];if(C&&gb.swT){const ct=A[0]+(now-gb.swT)/1000,end=Math.min(A[1],(C.nf-1)/C.fps-.09);if(ct>=Math.max(0,A[0]-A[2])&&ct<end)return[c,ct];if(ct>=end)gb.swT=0}
 if(gb.hitT&&now-gb.hitT<560&&mm.clips.Hit)return['Hit',(now-gb.hitT)/560*1.1];
 if(d)return['Walking',(gb.ph||0)/4];return mm.clips.Idle?['Idle',now/1000+i*.37]:null}
function npcDraw(gb,mm,d,now,i,x,z){const sc=(MDLSC[mm.k]||1)*(MSK[MT[gb.t].k]||1),W=NPCW[mobKey(gb.t)],p=npcPose(gb,mm,d,now,i),cl=p?p[0]:null,t=p?p[1]:0,y0=YO;
 if(gb.dieT){const e=(now-gb.dieT)/1000;YO-=Math.max(0,e-2.5)*1.0}
 qMdl(mm,x,0,z,gb.ry||0,sc,cl,t);if(W){if(W[0]){if(cl=='Death'&&t>1.25)qDrop(mm,x,z,gb.ry||0,W[0],sc);else qHold(mm,x,z,gb.ry||0,cl,t,W[0],false,sc,npcTilt(gb,cl,t,W[0]))}if(W[1])qHold(mm,x,z,gb.ry||0,cl,t,W[1],true,sc)}YO=y0}
// swords, clubs and bats: lowered at the side while standing or walking, raised into the fighting grip during a swing
function npcTilt(gb,cl,t,wk){const A=NCL[cl],cf=WCFG[wk];if(!cf||cf[2]!='f')return null;const d0=cf[3]||0;if(!A)return cl=='Death'?d0:REST;
 const s=Math.max(0,A[0]-A[2]),b=Math.min(1,Math.max(0,(t-s)/.2),Math.max(0,(A[1]-t)/.25));return REST+(d0-REST)*b}
const REST=100;
// a fallen fighter lets go: the weapon lies flat on the ground beside the right hand (instead of standing up in the air)
function qDrop(PM,x,z,yaw,wk,sc){const WM=MDL[wk],c=PM.clips.Death;if(!WM||!WM.ok||!c||!c.hand)return;const H=c.hand[c.hand.length-1],cf=WCFG[wk]||[1,.2,'f',25],ws=cf[0]/(WHT[wk]||2),gy=cf[1]*cf[0];
 const M=[0,-sc,0, 0,0,-sc, sc,0,0],hx=H[3]*sc,hz=H[11]*sc;MQ.push({m:WM,x,y:YO,z,yaw,s:ws,a:WM.idle,b:WM.idle,mx:0,hr:new Float32Array([M[0],M[3],M[6],M[1],M[4],M[7],M[2],M[5],M[8]]),ht:new Float32Array([hx-M[1]*gy,.04*sc,hz-M[7]*gy])})}
// town guards: sword and shield, standing at ease
function guardDraw(a){const M=MDL.knight,cl=idleCl(M),t=performance.now()/1000+a[0]*.71+a[1]*.37;qMdl(M,a[0],0,a[1],a[2]||0,MDLSC.knight,cl,t);qHold(M,a[0],a[1],a[2]||0,cl,t,'w_isword',false,MDLSC.knight,REST);qHold(M,a[0],a[1],a[2]||0,cl,t,'w_rshield',true,MDLSC.knight)}
// a breathing idle for NPCs that just stand there
function idleCl(m){return m&&m.clips&&m.clips.Idle?'Idle':null}
"""
rep("function mobDraw(gb,d,now,i,lod){", NPCW.strip() + "\nfunction mobDraw(gb,d,now,i,lod){")

# ---- monster drawing: real motions when the model has them (old lunge kept for the rest)
rep("{const mm=mobMdl(gb.t);if(mm){const la=", "{const mm=mobMdl(gb.t);if(mm&&mm.clips.Idle){npcDraw(gb,mm,d,now,i,x,z);return}if(mm){const la=")

# ---- tick: wind up before the attack tick; the attack lines up the blow
rep("if(inR&&hos&&!dieT&&!(gb.stunT>tickN)){if(--gb.cd<=0)mobAttack(gb,mt,cd)}",
    "if(!inR||!hos)gb.wound=0;if(inR&&hos&&!dieT&&!(gb.stunT>tickN)){if(--gb.cd<=0)mobAttack(gb,mt,cd);else mobWind(gb)}")
rep("function mobAttack(gb,mt,cd){const sp=mt.sp;gb.atkT=performance.now();",
    "function mobAttack(gb,mt,cd){const sp=mt.sp;gb.atkT=performance.now();const sw0=gb.wound,st0=gb.swT;gb.wound=0;gb.swT=0;")
rep("gb.cd=spd;if((mt.rng||1)>1)PJ.push(", "gb.wound=sw0;gb.swT=st0;mobSwing(gb);gb.cd=spd;if((mt.rng||1)>1)PJ.push(")

# ---- idle monsters stroll: walk a few tiles to a spot near home, stop, look around, go again (was: a random
#      single step about every 5 seconds, so they looked frozen)
rep("else if(Math.random()<.35){if(Math.random()<.5)mx=Math.floor(Math.random()*3)-1;else my=Math.floor(Math.random()*3)-1}",
    "else{const s_=mobRoam(gb);mx=s_[0];my=s_[1]}")
rep("function mobKey(t){", "function mobRoam(gb){if(gb.rw>tickN)return[0,0];if(!gb.rt){if(Math.random()<.35){gb.rw=tickN+2+Math.floor(Math.random()*6);return[0,0]}const a=Math.random()*6.283,r=2+Math.random()*4.5;gb.rt=[Math.round(gb.hx+Math.cos(a)*r),Math.round(gb.hy+Math.sin(a)*r)]}"+
 "const dx=Math.sign(gb.rt[0]-gb.x),dy=Math.sign(gb.rt[1]-gb.y);if(!dx&&!dy){gb.rt=null;gb.rw=tickN+3+Math.floor(Math.random()*8);return[0,0]}"+
 "let mx=0,my=0;if(dx&&(!dy||Math.random()<.5))mx=dx;else my=dy;if(solid(gb.x+mx,gb.y+my)){if(mx&&dy&&!solid(gb.x,gb.y+dy)){mx=0;my=dy}else if(my&&dx&&!solid(gb.x+dx,gb.y)){my=0;mx=dx}else{gb.rt=null;gb.rw=tickN+3;return[0,0]}}"+
 "if(Math.hypot(gb.x+mx-gb.hx,gb.y+my-gb.hy)>=8){gb.rt=null;return[0,0]}return[mx,my]}\nfunction mobKey(t){")

# ---- flinch when hit, fall when killed
rep("d=Math.min(d,gb.hp);gb.hp-=d;fl(gb.x,gb.y,d,d?'#d22':'#39f');",
    "d=Math.min(d,gb.hp);gb.hp-=d;if(d>0)gb.hitT=performance.now();fl(gb.x,gb.y,d,d?'#d22':'#39f');")
rep("o.hp-=dd;o.prov=1;", "o.hp-=dd;o.prov=1;if(dd>0)o.hitT=performance.now();")
rep("function killMob(gb){const mt=MT[gb.t];gb.dead=tickN+",
    "function killMob(gb){const mt=MT[gb.t];gb.dieT=performance.now();gb.swT=0;gb.wound=0;gb.dead=tickN+")
rep("gobs.forEach((gb,i)=>{if(gb.dead)return;",
    "gobs.forEach((gb,i)=>{if(gb.dead){if(gb.dieT&&now-gb.dieT<3400){const mm=mobMdl(gb.t);if(mm&&mm.clips.Death&&Math.hypot(gb.px-P.px,gb.py-P.py)<26){YO=hgt(gb.px+.5,gb.py+.5);npcDraw(gb,mm,0,now,i,gb.px+.5,gb.py+.5);YO=0}else if(now-gb.dieT<900&&Math.hypot(gb.px-P.px,gb.py-P.py)<26){YO=hgt(gb.px+.5,gb.py+.5)-(now-gb.dieT)/900*1.8;mobDraw(gb,0,now,i,false);YO=0}}return}if(gb.dieT)gb.dieT=0;")

# ---- guards: sword and shield, standing at ease
rep("qMdl(MDL.knight,a[0],0,a[1],a[2]||0,MDLSC.knight,null,0)",
    "guardDraw(a)")
# ---- bankers, shopkeepers and the other town NPCs breathe
rep("qMdl(MDL[mk],a[0],0,a[1],a[2]||0,MDLSC[mk],null,0)", "qMdl(MDL[mk],a[0],0,a[1],a[2]||0,MDLSC[mk],idleCl(MDL[mk]),performance.now()/1000+a[0]*.53)")
rep("qMdl(MDL[mk],o.nx,0,o.nz,o.ry,MDLSC[mk],null,0)", "qMdl(MDL[mk],o.nx,0,o.nz,o.ry,MDLSC[mk],idleCl(MDL[mk]),performance.now()/1000+o.nx*.53)")
rep("qMdl(MDL[k],o.x+.5,0,o.y+.5,o.ry||0,MDLSC[k]||1,null,0)", "qMdl(MDL[k],o.x+.5,0,o.y+.5,o.ry||0,MDLSC[k]||1,idleCl(MDL[k]),performance.now()/1000+o.x*.53)")
rep("qMdl(MDL[k],o.x+.5,0,o.y+.5,o.ry||0,MDLSC[k],null,0)", "qMdl(MDL[k],o.x+.5,0,o.y+.5,o.ry||0,MDLSC[k],idleCl(MDL[k]),performance.now()/1000+o.x*.53)")
# the genie floats; the chef and the rich man breathe
rep("qMdl(MDL[rk],x,0,z,ry,MDLSC[rk],null,0)", "qMdl(MDL[rk],x,rk=='genie'?.12+Math.sin(performance.now()/700)*.08:0,z,ry,MDLSC[rk],idleCl(MDL[rk]),performance.now()/1000)")
rep("qMdl(MDL.hexfrog,f.x,0,f.z,f.yaw,MDLSC.hexfrog,moving?'Walking':null,f.at)",
    "qMdl(MDL.hexfrog,f.x,0,f.z,f.yaw,MDLSC.hexfrog,moving?'Walking':idleCl(MDL.hexfrog),moving?f.at:performance.now()/1000)")
# pets
rep("qMdl(M3,PT.px+.5,0,PT.py+.5,PT.ry||0,P3[1],fp.v>.2?'Walking':null,(PT.ph||0)/4)",
    "qMdl(M3,PT.px+.5,0,PT.py+.5,PT.ry||0,P3[1],fp.v>.2?'Walking':idleCl(M3),fp.v>.2?(PT.ph||0)/4:performance.now()/1000)")

# ---- the player's own sword, club or bat: lowered at the side when not swinging (the same at-ease grip)
rep("function qHeld(PM,x,z,yaw,clip,t){if(clip=='Death'&&t>1.3)return;const wk=heldKey();if(wk)qHold(PM,x,z,yaw,clip,t,wk,false);",
    "function qHeld(PM,x,z,yaw,clip,t){if(clip=='Death'&&t>1.3)return;const wk=heldKey();if(wk)qHold(PM,x,z,yaw,clip,t,wk,false,null,heldTilt(clip,t,wk));")
rep("function idleCl(m){", "function heldTilt(cl,t,wk){const cf=WCFG[wk];if(!cf||cf[2]!='f')return null;if(!cl||cl=='Idle'||cl=='Walking'||cl=='Running'||cl=='Hit')return REST;if(NCL[cl])return REST+((cf[3]||0)-REST)*Math.min(1,t/.15);return null}\nfunction idleCl(m){")

# ---- the hippo's 3D model is broken (1 cm tall): use the hand-built hippo
rep("'m:moodeng':'moodeng',", "")

open(PATH, 'w', encoding='utf-8').write(h)
print('npc fight patch applied')
