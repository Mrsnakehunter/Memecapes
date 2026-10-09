#!/usr/bin/env python3
"""Held weapons and tools: draw a model in the player's hand.

Uses the per-frame hand transform stored in the player model's animation clips
('hand': 12 numbers per frame, a row-major 3x4 matrix in model space).
Run from the repo root after the other patches:
    python3 tools/patch_held.py
Weapon/tool models live in models/w_<item>.json (made with tools/glb2mdl.py,
long axis = y, grip near the bottom).
"""
import glob, json, os, sys

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- shader: optional full rotation for held items (pgM only)
rep("uniform float yaw,sc,mixf,ol,qs;varying vec2 vu;",
    "uniform float yaw,sc,mixf,ol,qs,hold;uniform mat3 HR;uniform vec3 HT;varying vec2 vu;")
rep("vec3 p=mix(pA,pB,mixf)*qs*sc;vY=p.y/max(sc,.001);vec3 n=normalize(nA);",
    "vec3 p=mix(pA,pB,mixf)*qs*sc;if(hold>.5)p=HR*p+HT;vY=p.y/max(sc,.001);vec3 n=normalize(nA);if(hold>.5)n=normalize(HR*n);")
rep("'cSh','cPa','cHa','cSk','cBo'].forEach(k=>uMd[k]=gl.getUniformLocation(pgM,k));",
    "'cSh','cPa','cHa','cSk','cBo','hold','HR','HT'].forEach(k=>uMd[k]=gl.getUniformLocation(pgM,k));")
# held items: skip in non-pgM passes (shadow map), set the hold uniforms otherwise
rep("function drawMQ(prog,U,shell){for(const q of (prog==pgSM?MQL:MQ)){let m=q.m,qa=q.a,qb=q.b;",
    "function drawMQ(prog,U,shell){for(const q of (prog==pgSM?MQL:MQ)){if(q.hr&&prog!=pgM)continue;let m=q.m,qa=q.a,qb=q.b;")
rep("gl.uniform3f(U.tr,q.x,q.y,q.z);gl.uniform1f(U.yaw,q.yaw);gl.uniform1f(U.sc,q.s);gl.uniform1f(U.mixf,q.mx);",
    "if(prog==pgM){gl.uniform1f(U.hold,q.hr?1:0);if(q.hr){gl.uniformMatrix3fv(U.HR,false,q.hr);gl.uniform3fv(U.HT,q.ht)}}gl.uniform3f(U.tr,q.x,q.y,q.z);gl.uniform1f(U.yaw,q.yaw);gl.uniform1f(U.sc,q.s);gl.uniform1f(U.mixf,q.mx);")

# ---- keep the hand track when registering animated models
rep("m.clips[c.n]={f:F,fps:c.fps}", "m.clips[c.n]={f:F,fps:c.fps,hand:c.hand,handL:c.handL}")
rep("for(const fr of wc.f){let mn=1e9,mx=-1e9;const P=fr.P;for(let i=2;i<P.length;i+=3){if(P[i]<mn)mn=P[i];if(P[i]>mx)mx=P[i]}if(mx-mn<best){best=mx-mn;m.idle=fr.g}}",
    "for(let fi=0;fi<wc.f.length;fi++){const fr=wc.f[fi];let mn=1e9,mx=-1e9;const P=fr.P;for(let i=2;i<P.length;i+=3){if(P[i]<mn)mn=P[i];if(P[i]>mx)mx=P[i]}if(mx-mn<best){best=mx-mn;m.idle=fr.g;m.idleHand=wc.hand&&wc.hand[fi];m.idleHandL=wc.handL&&wc.handL[fi]}}")

# ---- which model to hold
avail = sorted(os.path.basename(p)[:-5] for p in glob.glob('models/w_*.json'))
test = os.environ.get('HELD_TEST')  # e.g. HELD_TEST=w_test maps every weapon to that model
# per model: [total length in world units (the player is 1.7 tall), grip height as a fraction of model height]
WCFG = {'w_sword': [1.1, .16], 'w_isword': [1.1, .16], 'w_rsword': [1.15, .16], 'w_club': [.85, .1],
        'w_bbat': [.95, .1], 'w_bstaff': [1.6, .4], 'w_astaff': [1.6, .4], 'w_iscroll': [.5, .3],
        'w_axe': [.9, .12], 'w_iaxe': [.9, .12], 'w_pick': [.9, .12], 'w_ipick': [.9, .12],
        'w_rshield': [.95, .5]}  # the shield sits on the left forearm, held at its middle
import base64
WHT = {}
for k in avail:
    import numpy as np
    d = json.load(open(f'models/{k}.json')); v = np.frombuffer(base64.b64decode(d['vb']), np.int16).reshape(-1, 3) / 1000
    WHT[k] = round(float(v[:, 1].max()), 3)
HELD_JS = ("const WAV=new Set(" + json.dumps(avail) + "),WHT=" + json.dumps(WHT) + ",WCFG=" + json.dumps(WCFG) + ",HTEST=" + json.dumps(test) + ";"
    "window.HOFF=window.HOFF||[1,0,0,0,-1,0,0,0,-1];window.SOFF=window.SOFF||[0,0,1,0,-1,0,1,0,0];"
    "function heldKey(){let k=st.eq&&st.eq.weapon;if(act&&act.k=='tree')k=has('iaxe')?'iaxe':has('axe')?'axe':k;else if(act&&act.k=='rock')k=has('ipick')?'ipick':has('pick')?'pick':k;"
    "if(!k)return null;if(HTEST)return HTEST;const w='w_'+k;return WAV.has(w)?w:null}"
    "function shieldKey(){const k=st.eq&&st.eq.shield;if(!k)return null;const w='w_'+k;return WAV.has(w)?w:null}"
    "function qHold(PM,x,z,yaw,clip,t,wk,left){needMdl(wk);const WM=MDL[wk];if(!WM||!WM.ok)return;"
    "const c=PM.clips[clip]||PM.clips[clip=='Running'?'Walking':null],tr=left?'handL':'hand';let H=left?PM.idleHandL:PM.idleHand;"
    "if(c&&c[tr]){const nf=c[tr].length,ft=(t*c.fps)%nf,f0=Math.floor(ft),mx=ft-f0,A=c[tr][f0],B=c[tr][(f0+1)%nf];H=A.map((v,i)=>v+(B[i]-v)*mx)}if(!H)return;"
    "const sP=MDLSC.player,O=left?SOFF:HOFF,R=[H[0],H[1],H[2],H[4],H[5],H[6],H[8],H[9],H[10]],T=[H[3]*sP,H[7]*sP,H[11]*sP];"
    "const M=[0,0,0,0,0,0,0,0,0];for(let i=0;i<3;i++)for(let j=0;j<3;j++){let s=0;for(let k=0;k<3;k++)s+=R[i*3+k]*O[k*3+j];M[i*3+j]=s*sP}"
    "const cf=WCFG[wk]||[1,.2],ws=cf[0]/(WHT[wk]||2),gy=cf[1]*cf[0];"
    "const ht=[T[0]-M[1]*gy,T[1]-M[4]*gy,T[2]-M[7]*gy];"
    "MQ.push({m:WM,x,y:YO,z,yaw,s:ws,a:WM.idle,b:WM.idle,mx:0,hr:new Float32Array([M[0],M[3],M[6],M[1],M[4],M[7],M[2],M[5],M[8]]),ht:new Float32Array(ht)})}"
    "function qHeld(PM,x,z,yaw,clip,t){const wk=heldKey();if(wk)qHold(PM,x,z,yaw,clip,t,wk,false);const sk=shieldKey();if(sk)qHold(PM,x,z,yaw,clip,t,sk,true)}\n")
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", HELD_JS + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){")
rep("qMdl(PM,P.px+.5+Math.sin(pry)*la,0,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),MDLSC.player,mvg?(pspd>2.4?'Running':'Walking'):null,now/1000,0,null,false,1)}",
    "qMdl(PM,P.px+.5+Math.sin(pry)*la,0,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),MDLSC.player,mvg?(pspd>2.4?'Running':'Walking'):null,now/1000,0,null,false,1);"
    "qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),mvg?(pspd>2.4?'Running':'Walking'):null,now/1000)}")

open(PATH, 'w', encoding='utf-8').write(h)
print('held items patch applied; models:', ', '.join(avail) or '(none)', '| test:', test)
