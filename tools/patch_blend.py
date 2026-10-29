#!/usr/bin/env python3
"""Smooth animation changes (Albert, Oct 29: "better and smoother transitions and walking and motions").

Before: every character snapped from one animation to the next in a single frame: standing to walking, walking to a
swing, a swing back to standing, a monster's walk to its attack. Within one animation the game already blends between
neighbouring frames on the graphics card (two pre-skinned frames and a mix value).

Now every character drawn through qMdl (the player, other players, bots, NPCs, monsters, pets) crossfades: when its
animation changes, the last pose of the old animation is blended into the new one over 0.2 s (0.11 s into or out of
an attack, so hits still land on time). It costs nothing extra on the graphics card: during the fade the two blended
frames are the old pose and the new pose instead of two neighbouring frames of one animation.

Characters are matched frame to frame by model and position (the nearest of the same model within 0.9 tiles), so no
caller had to change. Held weapons and shields blend their hand grip the same way, so they stay in the hand.

Run late in the build (after patch_carry):  python3 tools/patch_blend.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


XF = r"""let XF=[],XFN=[],XFC=null;
function xfDur(a,b){return (a&&NCL[a])||(b&&NCL[b])||a=='Hit'||b=='Hit'?110:200}
function xfBlend(m,x,z,cn,t,a,b,mx){const now=performance.now(),cur=mx<.5?a:b;let e=null,bd=.9;
 for(const q of XF){if(q.m!==m||q.used)continue;const d=Math.abs(q.x-x)+Math.abs(q.z-z);if(d<bd){bd=d;e=q}}
 const s={m,x,z,cn,t,cur,f:null};XFC=null;
 if(e){e.used=1;if(e.cn!==cn){s.f={from:e.f&&e.f.k<.5?e.f.from:e.cur,fcn:e.cn,ft:e.t,t0:now,dur:xfDur(e.cn,cn),k:0}}else if(e.f)s.f=e.f}
 XFN.push(s);
 if(s.f){const k=(now-s.f.t0)/s.f.dur;if(k<1){s.f.k=k;const kk=k*k*(3-2*k);XFC={m,x,fcn:s.f.fcn,ft:s.f.ft,k:kk};return[s.f.from,cur,kk]}s.f=null}
 return null}
function xfHand(PM,cn,t,left){const c=cn?PM.clips[cn]:null,tr=left?'handL':'hand';
 if(c&&c[tr]){const nf=c[tr].length,ft=((t*c.fps)%nf+nf)%nf,f0=Math.floor(ft),mx=ft-f0,A=c[tr][f0],B=c[tr][(f0+1)%nf];return A.map((v,i)=>v+(B[i]-v)*mx)}
 return left?PM.idleHandL:PM.idleHand}
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", XF + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){")
# qMdl: crossfade when the animation changes
rep("mx=ft-f0}MQ.push({m,x,y:y+YO,z,yaw,s,a,b,mx,cut,sm,gh,pl})}",
    "mx=ft-f0}{const cn=c?(m.clips[clip]?clip:'Walking'):'',r=xfBlend(m,x,z,cn,t,a,b,mx);if(r){a=r[0];b=r[1];mx=r[2]}}MQ.push({m,x,y:y+YO,z,yaw,s,a,b,mx,cut,sm,gh,pl})}")
# held weapons: the hand grip fades between the two animations too
rep("if(!H)return;const cf=WCFG[wk]",
    "if(XFC&&XFC.m===PM&&Math.abs(XFC.x-x)<.05){const H0=xfHand(PM,XFC.fcn,XFC.ft,left);if(H0&&H)H=H0.map((v,i)=>v+(H[i]-v)*XFC.k)}if(!H)return;const cf=WCFG[wk]")
# a new frame: last frame's characters become the ones to match against
rep("MQ.length=0;", "MQ.length=0;XF=XFN;XFN=[];")
open(PATH, 'w', encoding='utf-8').write(h)
print('animation crossfade patch applied')
