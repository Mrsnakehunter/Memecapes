#!/usr/bin/env python3
"""Real point lights for the lamp posts at night.

Up to 8 lanterns nearest the player light the ground, walls, props and characters around them
(warm colour, smooth falloff), instead of a flat disc painted on the ground.
Run from the repo root after patch_bld_models.py:  python3 tools/patch_lights.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


NL = 8
DECL = 'uniform vec3 PL[%d];uniform float PLn,PLs;' % NL
# light added to an albedo: warm lantern colour, smooth falloff over ~7 units, a little wrap so walls facing away still catch some
FN = ('vec3 plt(vec3 wp,vec3 nn){vec3 a=vec3(0.);if(PLs<=0.)return a;for(int i=0;i<%d;i++){if(float(i)>=PLn)break;vec3 d=PL[i]-wp;float r=length(d);'
      'float k=max(0.,1.-r/6.5);k*=k;float nd=.3+.7*max(0.,dot(nn,d/max(r,.001)));a+=vec3(1.,.78,.45)*(.95*k*nd);}return a*PLs;}') % NL

# ---- world geometry (pg): has world position vp and normal vn
rep("varying vec3 vc;varying float vf;varying vec3 vp;varying vec3 vn;varying vec3 vsc;varying vec2 vl;varying float vm;uniform vec3 fogC,eye,tgt;uniform float lm,ss,cutR;",
    "varying vec3 vc;varying float vf;varying vec3 vp;varying vec3 vn;varying vec3 vsc;varying vec2 vl;varying float vm;uniform vec3 fogC,eye,tgt;uniform float lm,ss,cutR;" + DECL + FN)
# ---- ground (pg3): world xz in vw; add the height
rep("varying vec3 vc;varying vec2 vw;varying float vf;varying vec3 vsc;varying vec2 vl;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);float nd=dot(nn,normalize(vec3(.45,.8,.3)));vl=vec2(.5,.5*max(nd,0.));vc=c*lm;vw=p.xz;",
    "varying vec3 vc;varying vec2 vw;varying float vf;varying vec3 vsc;varying vec2 vl;varying vec3 vwp;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);float nd=dot(nn,normalize(vec3(.45,.8,.3)));vl=vec2(.5,.5*max(nd,0.));vc=c*lm;vw=p.xz;vwp=p;")
rep("uniform sampler2D dt;uniform sampler2D sm;uniform vec3 fogC;uniform float ss;uniform vec2 sts;varying vec3 vc;varying vec2 vw;varying float vf;varying vec3 vsc;varying vec2 vl;float up(vec4 v)",
    "uniform sampler2D dt;uniform sampler2D sm;uniform vec3 fogC;uniform float ss,lm;uniform vec2 sts;varying vec3 vc;varying vec2 vw;varying float vf;varying vec3 vsc;varying vec2 vl;varying vec3 vwp;" + DECL + FN + "float up(vec4 v)")
rep("c*=mix(gp,sp,sand);float f=clamp((vf-26.)/24.,0.,1.);gl_FragColor=vec4(mix(c,fogC,f),1.);}",
    "c*=mix(gp,sp,sand);c+=vc/max(lm,.05)*mix(gp,sp,sand)*plt(vwp,vec3(0.,1.,0.));float f=clamp((vf-26.)/24.,0.,1.);gl_FragColor=vec4(mix(c,fogC,f),1.);}")
# ---- animated/static models (pgM): has vwp; pass the normal too
rep("vec3 wn=vec3(n.x*cs+n.z*sn,n.y,-n.x*sn+n.z*cs);wp+=wn*ol;vwp=wp;gl_Position=M*vec4(wp,1.);vu=uv;",
    "vec3 wn=vec3(n.x*cs+n.z*sn,n.y,-n.x*sn+n.z*cs);wp+=wn*ol;vwp=wp;vwn=wn;gl_Position=M*vec4(wp,1.);vu=uv;")
rep("varying vec2 vu;varying float vf;varying vec3 vsc;varying vec2 vl;varying vec3 vwp;varying float vY;void main(){vec3 p=mix(pA,pB,mixf)*qs*sc;",
    "varying vec2 vu;varying float vf;varying vec3 vsc;varying vec2 vl;varying vec3 vwp;varying float vY;varying vec3 vwn;void main(){vec3 p=mix(pA,pB,mixf)*qs*sc;")
rep("uniform vec3 cSh,cPa,cHa,cSk,cBo;uniform vec3 eye,tgt;uniform float cutR,gh;float m2(vec2 p)",
    "uniform vec3 cSh,cPa,cHa,cSk,cBo;uniform vec3 eye,tgt;uniform float cutR,gh;varying vec3 vwn;" + DECL + FN + "float m2(vec2 p)")
rep("float sh=shd();float l=vl.x+vl.y*(1.-sh);c*=l*lm;gl_FragColor=vec4(mix(c,fogC,f),1.);}'));\n['pA','pB','nA','uv']",
    "float sh=shd();float l=vl.x+vl.y*(1.-sh);c=c*l*lm+c*plt(vwp,vwn);gl_FragColor=vec4(mix(c,fogC,f),1.);}'));\n['pA','pB','nA','uv']")

# ---- pg's main(): find its final colour line
i = h.find("gl.attachShader(pg,sh(gl.FRAGMENT_SHADER,")
j = h.find("'));", i)
frag = h[i:j]
assert "gl_FragColor" in frag
# the pg fragment multiplies by lm somewhere; add the lamp term just before the fog mix of the main colour
k = frag.rfind("gl_FragColor=vec4(mix(")
assert k > 0, 'pg final colour not found'
# find the colour variable used in that mix
import re
m = re.match(r"gl_FragColor=vec4\(mix\((\w+),fogC,", frag[k:])
assert m, frag[k:k+80]
cvar = m.group(1)
newfrag = frag[:k] + cvar + "+=" + cvar + "/max(lm,.05)*plt(vp,vn);" + frag[k:]
h = h[:i] + newfrag + h[j:]

# ---- uniform locations
rep("uCut=gl.getUniformLocation(pg,'cutR'),uT=gl.getUniformLocation(pg,'t');",
    "uCut=gl.getUniformLocation(pg,'cutR'),uT=gl.getUniformLocation(pg,'t'),uPL=gl.getUniformLocation(pg,'PL'),uPLn=gl.getUniformLocation(pg,'PLn'),uPLs=gl.getUniformLocation(pg,'PLs');")
rep("u3Ss=gl.getUniformLocation(pg3,'ss'),u3Sts=gl.getUniformLocation(pg3,'sts');",
    "u3Ss=gl.getUniformLocation(pg3,'ss'),u3Sts=gl.getUniformLocation(pg3,'sts'),u3PL=gl.getUniformLocation(pg3,'PL'),u3PLn=gl.getUniformLocation(pg3,'PLn'),u3PLs=gl.getUniformLocation(pg3,'PLs');")
rep("'cSh','cPa','cHa','cSk','cBo'].forEach(k=>uMd[k]=gl.getUniformLocation(pgM,k));",
    "'cSh','cPa','cHa','cSk','cBo'].forEach(k=>uMd[k]=gl.getUniformLocation(pgM,k));['PL','PLn','PLs'].forEach(k=>uMd[k]=gl.getUniformLocation(pgM,k));")

# ---- per frame: nearest lanterns to the player
rep("gl.useProgram(pg);gl.uniformMatrix4fv(uM,false,VPm);gl.uniform3f(uE,E[0],E[1],E[2]);gl.uniform1f(uLm,LMV);",
    "pickLights();gl.useProgram(pg);gl.uniformMatrix4fv(uM,false,VPm);gl.uniform3f(uE,E[0],E[1],E[2]);gl.uniform1f(uLm,LMV);gl.uniform3fv(uPL,PLA);gl.uniform1f(uPLn,PLN);gl.uniform1f(uPLs,PLS);")
rep("gl.useProgram(pg3);gl.uniformMatrix4fv(u3M,false,VPm);gl.uniform3f(u3E,E[0],E[1],E[2]);gl.uniform1f(u3Lm,LMV);",
    "gl.useProgram(pg3);gl.uniformMatrix4fv(u3M,false,VPm);gl.uniform3f(u3E,E[0],E[1],E[2]);gl.uniform1f(u3Lm,LMV);gl.uniform3fv(u3PL,PLA);gl.uniform1f(u3PLn,PLN);gl.uniform1f(u3PLs,PLS);")
rep("gl.uniform3f(uMd.fogC,FOG[0],FOG[1],FOG[2]);gl.uniform1f(uMd.lm,LMV);",
    "gl.uniform3f(uMd.fogC,FOG[0],FOG[1],FOG[2]);gl.uniform1f(uMd.lm,LMV);gl.uniform3fv(uMd.PL,PLA);gl.uniform1f(uMd.PLn,PLN);gl.uniform1f(uMd.PLs,PLS);")

# ---- the lantern positions (from the lamp posts' yaw and model), and the per-frame pick
rep("PR.lamps.forEach(([x,z,yw,lk])=>{if(Math.abs(x-P.px)<32&&Math.abs(z-P.py)<32){const LO={b_lamp:[-.44,1.48,0],b_swamplamp:[-.5,1.5,.03],b_spacelamp:[0,2.2,.02]},o=LO[lk]||[0,2.05,0],c=Math.cos(yw||0),sn=Math.sin(yw||0),lx=x+o[0]*c+o[2]*sn,lz=z-o[0]*sn+o[2]*c;YO=hgt(lx,lz);ball(lx,o[1],lz,.12,.16,.12,0,[2.4,2.1,1.2],6);ball(lx,.02,lz,1.3,.01,1.3,0,[.95,.85,.5],8)}});",
    "LAMPL.forEach(([lx,ly,lz])=>{if(Math.abs(lx-P.px)<32&&Math.abs(lz-P.py)<32){YO=0;ball(lx,ly,lz,.12,.16,.12,0,[2.4,2.1,1.2],6)}});")
rep("let FOG=[.557,.796,1],LMV=1,RAIN=false;",
    "let FOG=[.557,.796,1],LMV=1,RAIN=false;const LAMPL=[],PLA=new Float32Array(%d*3);let PLN=0,PLS=0;"
    "function lampLights(){LAMPL.length=0;const LO={b_lamp:[-.44,1.48,0],b_swamplamp:[-.5,1.5,.03],b_spacelamp:[0,2.2,.02]};PR.lamps.forEach(([x,z,yw,lk])=>{const o=LO[lk]||[0,2.05,0],c=Math.cos(yw||0),sn=Math.sin(yw||0),lx=x+o[0]*c+o[2]*sn,lz=z-o[0]*sn+o[2]*c;LAMPL.push([lx,hgt(lx,lz)+o[1],lz])})}"
    "function pickLights(){if(!LAMPL.length)lampLights();PLS=Math.max(0,Math.min(1,(.85-LMV)/.4));if(PLS<=0){PLN=0;return}const near=[];for(const l of LAMPL){const d=Math.hypot(l[0]-P.px,l[2]-P.py);if(d<30)near.push([d,l])}near.sort((a,b)=>a[0]-b[0]);PLN=Math.min(%d,near.length);for(let i=0;i<PLN;i++){PLA[i*3]=near[i][1][0];PLA[i*3+1]=near[i][1][1];PLA[i*3+2]=near[i][1][2]}}" % (NL, NL))

open(PATH, 'w', encoding='utf-8').write(h)
print('point lights patch applied')
