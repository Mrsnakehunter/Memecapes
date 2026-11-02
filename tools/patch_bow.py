#!/usr/bin/env python3
"""Bows held and shot like bows (Albert, Nov 1: "why are they using the bow like a sword?" and "the string towards
the body of the character, not away").

- A bow is always held in the LEFT hand (the bow hand), upright, with its string facing the body; while shooting the
  string faces the drawing (right) hand, so the bow sits in the line of the shot. The bow's frame is built from the
  hand positions in each clip (grip tracks), not from the hand bone's twist, so it can't end up lying flat.
- A ranged attack plays the new 'Shoot' clip (tools/add_clips.py: Meshy's Archery Shot 1 + 3 = reach to the quiver,
  nock, draw to the cheek, release; 1.75 s) instead of the spell cast; the arrow leaves on the release, the hit lands
  a moment after.
Run after patch_pvp.py:  python3 tools/patch_bow.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


BOW = r"""function qHoldBow(PM,x,z,yaw,clip,t,wk,sc){needMdl(wk);const WM=MDL[wk];if(!WM||!WM.ok)return;
 const c=PM.clips[clip]||PM.clips[clip=='Running'?'Walking':'Idle'];
 const tr=k=>{if(c&&c[k]){const nf=c[k].length,ft=((t*c.fps)%nf+nf)%nf,f0=Math.floor(ft),mx=ft-f0,A=c[k][f0],B=c[k][(f0+1)%nf];return A.map((v,i)=>v+(B[i]-v)*mx)}return k=='handL'?PM.idleHandL:PM.idleHand};
 const L=tr('handL'),R=tr('hand');if(!L)return;const sP=sc||MDLSC.player,TL=[L[3],L[7],L[11]];
 // string side: toward the drawing hand while shooting, toward the body otherwise
 let d=clip=='Shoot'&&R?[R[3]-TL[0],0,R[11]-TL[2]]:[-TL[0],0,-TL[2]];let n=Math.hypot(d[0],d[2]);if(n<1e-4){d=[0,0,-1];n=1}
 const zz=[-d[0]/n,0,-d[2]/n],yy=[0,1,0],xx=[yy[1]*zz[2]-yy[2]*zz[1],yy[2]*zz[0]-yy[0]*zz[2],yy[0]*zz[1]-yy[1]*zz[0]];
 const M=[];for(let i=0;i<3;i++){M[i*3]=xx[i]*sP;M[i*3+1]=yy[i]*sP;M[i*3+2]=zz[i]*sP}
 const cf=WCFG[wk]||[1.3,.5],ws=cf[0]/(WHT[wk]||2),gy=cf[1]*cf[0]-.14,T=[TL[0]*sP,TL[1]*sP,TL[2]*sP];
 MQ.push({m:WM,x,y:YO,z,yaw,s:ws,a:WM.idle,b:WM.idle,mx:0,hr:new Float32Array([M[0],M[3],M[6],M[1],M[4],M[7],M[2],M[5],M[8]]),ht:new Float32Array([T[0]-M[1]*gy,T[1]-M[4]*gy,T[2]-M[7]*gy])})}
"""
rep("function qHold(PM,x,z,yaw,clip,t,wk,left){if(WFB[wk])wk=WFB[wk];return qHold_(",
    BOW + "function qHold(PM,x,z,yaw,clip,t,wk,left){if(WFB[wk])wk=WFB[wk];if(/^w_bw\d\d$/.test(wk))return left?undefined:qHoldBow(PM,x,z,yaw,clip,t,wk,arguments[8]);return qHold_(")
rep("const ACL={stab:['Stab','Attack'],", "const ACL={shoot:['Shoot','Cast','Attack'],stab:['Stab','Attack'],")
# a ranged attack: the bow shot, the arrow leaves on the release (1.2 s in), the hit lands after it
rep("lastCbt=tickN;castAnim();", "lastCbt=tickN;if(s=='rg')pAnim={k:'shoot',t0:performance.now(),d:1750};else castAnim();")
rep("else{PJ.push({x0:P.px+.5,z0:P.py+.5,x1:gb.px+.5,z1:gb.py+.5,t0:performance.now(),c:col,k:s});FX.arrow(P.px+.5,P.py+.5,gb.px+.5,gb.py+.5)}",
    "else setTimeout(()=>{PJ.push({x0:P.px+.5,z0:P.py+.5,x1:gb.px+.5,z1:gb.py+.5,t0:performance.now(),c:col,k:s});FX.arrow(P.px+.5,P.py+.5,gb.px+.5,gb.py+.5)},1200)")
rep("s=='mg'?(sp&&sp[0]=='Moon Beam'?820:600):390);", "s=='mg'?(sp&&sp[0]=='Moon Beam'?820:600):1600);")
# PvP shots use the same motion and timing
rep("else if(s=='rg'){pAnim={k:'stab',t0:now,d:600};FX.arrow(P.px+.5,P.py+.5,o.px+.5,o.py+.5)}",
    "else if(s=='rg'){pAnim={k:'shoot',t0:now,d:1750};setTimeout(()=>FX.arrow(P.px+.5,P.py+.5,o.px+.5,o.py+.5),1200)}")
rep("const ms=wSty()=='mg'?600:wSty()=='rg'?390:120;", "const ms=wSty()=='mg'?600:wSty()=='rg'?1600:120;")
# pose() runs for every body: it needs an entry for every pAnim key (a missing one stopped the game loop)
rep("PS.agi=f=>", "PS.shoot=f=>PS.cast(f);PS.agi=f=>")
open(PATH, 'w', encoding='utf-8').write(h)
print('patch_bow: bows held in the bow hand, Shoot motion')
