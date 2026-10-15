#!/usr/bin/env python3
"""Real trees: Meshy tree models (models/trees.json, built by tools/treepack.py) drawn with instancing.

Run from the repo root late in the build (after patch_security):  python3 tools/patch_trees.py

How it works
* The tree pack is fetched at start. Until it arrives (or if the browser has no ANGLE_instanced_arrays)
  the old code-built trees stay. When it lands every chunk is rebuilt without them (stumps stay in
  the chunk geometry, so chopping works as before: a chopped tree is o.dep and is skipped here).
* Every frame the trees within view radius are sorted into (species, detail level) groups by distance:
  near ~1600 triangles, mid ~500, far ~160. One instanced draw per group, in the shadow pass and the
  main pass. The main pass reuses the chunk fragment shader (material 10 = per-model texture on unit 4),
  so trees get the same light, shadows, fog, lamps and rain look as everything else; the shadow pass
  reuses the chunk depth shader.
* Species come from where the tree stands (forest, graveyard, snow town, moon, Roman hills, pond...),
  size, turn and tint vary per tree, deciduous trees sway at the top. Trees never go see-through.
"""
import re

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# 1. fragment shader: material 10 = model texture with a per-tree tint (vraw.z = brightness + 4*season)
rep("else if(m>9.5){c=texture2D(mt,vraw.xy).rgb*lm;}",
    "else if(m>9.5){vec3 T=texture2D(mt,vraw.xy).rgb;float tz=vraw.z;if(tz>0.){float k=floor(tz/4.);float b=tz-4.*k;if(k>.5){float g=smoothstep(0.,.22,T.g-max(T.r,T.b)*1.02);float lu=dot(T,vec3(.3,.59,.11));vec3 tc=k>2.5?vec3(.86,.3,.16):k>1.5?vec3(.98,.84,.3):vec3(.96,.5,.14);T=mix(T,tc*(lu*1.8),g);}T*=b;}c=T*lm;}")

# 2. the tree module: programs, pack loading, species choice, per-frame gather and draw
TREES = r"""
// ===== tree pack: Meshy trees drawn with instancing (tools/patch_trees.py) =====
const TREX=gl.getExtension('ANGLE_instanced_arrays');
const TRP={on:0,sp:{},keys:[],ibuf:null,cap:0,fr:-1,grp:null};
const pgT=gl.createProgram(),pgTS=gl.createProgram(),uTR={},uTRS={};
if(TREX){const body='vec3 lp=p*.001*ib.x;float cs=cos(ia.w),sn=sin(ia.w);vec3 wp=vec3(lp.x*cs+lp.z*sn,lp.y,-lp.x*sn+lp.z*cs)+ia.xyz;float hy=clamp(lp.y/max(ib.z,.1),0.,1.);hy*=hy;float w=(sin(t*1.1+ia.x*.7+ia.z*.5)*.05+sin(t*2.3+ia.z*.9+ia.x*.4)*.02)*hy*ib.w;wp.x+=w;wp.z+=w*.6;';
const fs=p=>gl.getAttachedShaders(p).find(s=>gl.getShaderParameter(s,gl.SHADER_TYPE)==gl.FRAGMENT_SHADER);
gl.attachShader(pgT,sh(gl.VERTEX_SHADER,'attribute vec3 p,n;attribute vec2 uv;attribute vec4 ia,ib;uniform mat4 M,SM;uniform vec3 eye;uniform float lm,t;varying vec3 vc;varying float vf;varying vec3 vp;varying vec3 vn;varying vec3 vsc;varying vec2 vl;varying float vm;varying vec3 vraw;void main(){'+body+'vec3 nn=normalize(vec3(n.x*cs+n.z*sn,n.y,-n.x*sn+n.z*cs));vm=10.;vp=wp;vn=nn;vraw=vec3(uv,ib.y);gl_Position=M*vec4(wp,1.);float nd=dot(nn,normalize(vec3(.45,.8,.3)));vl=vec2(.44+.06*nn.y,.6*max(nd,0.));vc=vec3(lm);vf=distance(wp,eye);vec4 s=SM*vec4(wp+nn*(.04+.1*(1.-abs(nd))),1.);vsc=s.xyz*.5+.5;}'));
gl.attachShader(pgT,fs(pg));['p','n','uv','ia','ib'].forEach((a,i)=>gl.bindAttribLocation(pgT,i,a));gl.linkProgram(pgT);
['M','SM','eye','lm','t','fogC','tgt','ss','cutR','PL','PLn','PLs','sts','dt','sm','lt','mt'].forEach(k=>uTR[k]=gl.getUniformLocation(pgT,k));
gl.useProgram(pgT);gl.uniform1i(uTR.dt,1);gl.uniform1i(uTR.sm,2);gl.uniform1i(uTR.lt,3);gl.uniform1i(uTR.mt,4);gl.uniform1f(uTR.cutR,0);
gl.attachShader(pgTS,sh(gl.VERTEX_SHADER,'attribute vec3 p;attribute vec4 ia,ib;uniform mat4 SM;uniform float t;varying float vz;varying vec3 vraw;varying float vm;varying vec3 vwp;void main(){'+body+'gl_Position=SM*vec4(wp,1.);vz=gl_Position.z*.5+.5;vraw=vec3(0.);vm=10.;vwp=wp;}'));
gl.attachShader(pgTS,fs(pgS));gl.bindAttribLocation(pgTS,0,'p');gl.bindAttribLocation(pgTS,3,'ia');gl.bindAttribLocation(pgTS,4,'ib');gl.linkProgram(pgTS);
['SM','t','eye','tgt','cutR'].forEach(k=>uTRS[k]=gl.getUniformLocation(pgTS,k));gl.useProgram(pgTS);gl.uniform1f(uTRS.cutR,0);gl.useProgram(pg);
TRP.ibuf=gl.createBuffer();
if(!(window.MC_CONFIG&&MC_CONFIG.trees===0))fetch('models/trees.json').then(r=>r.ok?r.json():null).then(d=>{if(!d)return;const dec=(s,Tp)=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new Tp(u.buffer)};
let left=0;for(const k in d){const e=d[k],sp={h:e.h,tex:null,lod:e.lod.map(l=>{const ib=dec(l.ib,Uint16Array);return{p:mkVbo(dec(l.vb,Int16Array)),n:mkVbo(dec(l.nb,Int8Array)),uv:mkVbo(dec(l.ub,Uint16Array)),ib:mkVbo(ib,gl.ELEMENT_ARRAY_BUFFER),ni:ib.length}})};TRP.sp[k]=sp;left++;
const im=new Image();im.onload=()=>{const t=gl.createTexture();gl.activeTexture(gl.TEXTURE4);gl.bindTexture(gl.TEXTURE_2D,t);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,im);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.generateMipmap(gl.TEXTURE_2D);gl.activeTexture(gl.TEXTURE0);sp.tex=t;if(--left==0)treeStart()};im.onerror=()=>{if(--left==0)treeStart()};im.src=e.tex}}).catch(()=>{})}
function treeStart(){if(!TRP.sp.oak||!TRP.sp.pine)return;TRP.keys=Object.keys(TRP.sp);TRP.on=1;for(const k in chunks)chunks[k].od=1}
// which tree stands here: region first, then the old forest/field dice (so the world keeps its shape)
const TRH={oak:3.6,beech:4.3,maple:3.4,birch:4.1,willow:3.7,blossom:3.0,dead:3.4,pine:5.0,spruce:4.6,fir:4.2,snowspruce:4.6,cypress:4.4,alien:3.6,palm:4.2},
TRFB={beech:'oak',maple:'oak',birch:'oak',willow:'oak',blossom:'oak',dead:'oak',alien:'oak',palm:'oak',spruce:'pine',fir:'pine',snowspruce:'pine',cypress:'pine'};
function treeKind(o){const q=hh(o.x*3+7,o.y*5+11),q2=hh(o.x+31,o.y+17),hv=HSH(o.x+77,o.y+3),h3=HSH(o.x+5,o.y+41),h4=HSH(o.x+19,o.y+23),forest=(o.x<175&&o.y<215)||(o.x>260&&o.y<60),tp=forest?(q2<.55?0:q2<.85?1:2):(q2<.15?0:q2<.75?1:2);
const nt=(i,r)=>Math.hypot(o.x-TW[i].cx,o.y-TW[i].cy)<r;let sp,season=0;
if(nt(4,42))sp=h3<.7?'dead':'spruce';else if(nt(5,44))sp=h3<.7?'snowspruce':'fir';else if(nt(6,38))sp=h3<.6?'alien':'dead';else if(nt(7,40))sp=h3<.6?'cypress':h3<.8?'palm':'oak';
else if(nt(1,34)&&h3<.5)sp='willow';else if(nt(3,30)&&h3<.4)sp='blossom';else if(nt(0,30)&&h3<.25)sp='blossom';
else if(tp==0)sp=h3<.5?'pine':h3<.8?'spruce':'fir';else{sp=h3<.45?'oak':h3<.65?'beech':h3<.8?'birch':h3<.9?'maple':'oak';if(tp==1&&hv<.08)sp='birch'}
if(sp=='maple')season=3;else if(hv>.9&&(sp=='oak'||sp=='beech'))season=1;else if(sp=='birch'&&h4<.3)season=2;
if(!TRP.sp[sp]){sp=TRFB[sp]||'oak';if(!TRP.sp[sp])sp='oak'}
const e=TRP.sp[sp],big=tp==2&&!(sp=='pine'||sp=='spruce'||sp=='fir'||sp=='cypress')?1.22:1,sc=(TRH[sp]||3.6)/Math.max(.5,e.h)*(.85+.3*q)*big,sway=(sp=='pine'||sp=='spruce'||sp=='fir'||sp=='snowspruce'||sp=='cypress'||sp=='dead'||sp=='alien')?.35:1;
return{sp,yaw:q*6.283+h4*.7,sc,tint:(.84+.3*h4)+4*season,h:e.h*sc,sway}}
const TRB={};function bushList(key){if(TRB[key])return TRB[key];const L=TRB[key]=[];if(!TRP.sp.bush)return L;const th=(x,y)=>{let h=(Math.imul(x,73856093)^Math.imul(y,19349663))>>>0;h=Math.imul(h^(h>>>15),2246822519)>>>0;h=Math.imul(h^(h>>>13),3266489917)>>>0;return((h^(h>>>16))>>>0)/4294967296};const x0=(key%CN)*CS,y0=Math.floor(key/CN)*CS;
for(let y=y0;y<Math.min(H,y0+CS);y++)for(let x=x0;x<Math.min(W,x0+CS);x++){if(tile[y][x]!=0||ob[y][x])continue;const q=th(x,y);if(q<=.972||q>.985)continue;const px=x+.5+(th(x,y+99)-.5)*.6,pz=y+.5+(th(x+99,y)-.5)*.6,sd=x*977+y*13+3,s=.75+HSH(sd,sd*3)*.5,h3=HSH(sd+5,sd*7),sp=TRP.sp.bushflower&&h3<.3?'bushflower':'bush',e=TRP.sp[sp];
L.push({x:px-.5,y:pz-.5,tk:{sp,yaw:q*6.28,sc:1.15*s/Math.max(.3,e.h),tint:.9+.25*HSH(sd+9,sd),h:1.15*s,sway:.5,ty:hgt(px,pz)}})}return L}
function treeGather(VPm){if(TRP.fr===frameN)return;TRP.fr=frameN;const RAD=RADS[qt],L0=qt?9:13,L1=qt?19:27,px=P.px+.5,pz=P.py+.5,G={};let n=0;
const all=[trees];if(TRP.sp.bush){const k0=Math.max(0,Math.floor((px-RAD)/CS)),k1=Math.min(CN-1,Math.floor((px+RAD)/CS)),j0=Math.max(0,Math.floor((pz-RAD)/CS)),j1=Math.min(CN-1,Math.floor((pz+RAD)/CS));for(let j=j0;j<=j1;j++)for(let i=k0;i<=k1;i++)all.push(bushList(j*CN+i))}
for(const list of all)for(const o of list){if(o.dep||o.gone)continue;const dx=o.x+.5-px,dz=o.y+.5-pz;if(dx>RAD||dx<-RAD||dz>RAD||dz<-RAD)continue;let k=o.tk;if(!k){k=o.tk=treeKind(o);k.ty=hgt(o.x+.5,o.y+.5)}
const d=Math.hypot(dx,dz),lod=d<L0?0:d<L1?1:2,x=o.x+.5,y=k.ty+k.h*.5,z=o.y+.5,cw=VPm[3]*x+VPm[7]*y+VPm[11]*z+VPm[15],cx=VPm[0]*x+VPm[4]*y+VPm[8]*z+VPm[12],cy=VPm[1]*x+VPm[5]*y+VPm[9]*z+VPm[13],r=k.h*1.1,vis=cw>-r&&Math.abs(cx)<cw+r*3.&&Math.abs(cy)<cw+r*3.;
const g=G[k.sp]||(G[k.sp]=[[[],[]],[[],[]],[[],[]]]);g[lod][0].push(o);if(vis)g[lod][1].push(o);n++}
if(n*2>TRP.cap){TRP.cap=Math.max(512,n*3);TRP.arr=new Float32Array(TRP.cap*8)}const A=TRP.arr;let at=0;const grp=[];
for(const sp in G)for(let l=0;l<3;l++)for(let v=0;v<2;v++){const list=G[sp][l][v];if(!list.length)continue;const o0=at;for(const o of list){const k=o.tk;A[at++]=o.x+.5;A[at++]=k.ty;A[at++]=o.y+.5;A[at++]=k.yaw;A[at++]=k.sc;A[at++]=k.tint;A[at++]=k.h;A[at++]=k.sway}grp.push([sp,l,v,o0/8,list.length])}
gl.bindBuffer(gl.ARRAY_BUFFER,TRP.ibuf);gl.bufferData(gl.ARRAY_BUFFER,A.subarray(0,at),gl.DYNAMIC_DRAW);TRP.grp=grp}
function treeDraw(shadow,VPm,now){if(!TRP.on||!TREX)return;treeGather(VPm);const grp=TRP.grp;if(!grp||!grp.length)return;const t=now/1000;
if(shadow){gl.useProgram(pgTS);gl.uniformMatrix4fv(uTRS.SM,false,LMm);gl.uniform1f(uTRS.t,t);gl.uniform3f(uTRS.eye,E[0],E[1],E[2]);gl.uniform3f(uTRS.tgt,P.px+.5,hgt(P.px+.5,P.py+.5)+.9,P.py+.5)}
else{gl.useProgram(pgT);gl.uniformMatrix4fv(uTR.M,false,VPm);gl.uniformMatrix4fv(uTR.SM,false,LMm);gl.uniform3f(uTR.eye,E[0],E[1],E[2]);gl.uniform1f(uTR.lm,LMV);gl.uniform1f(uTR.t,t);gl.uniform3f(uTR.fogC,FOG[0],FOG[1],FOG[2]);gl.uniform3f(uTR.tgt,P.px+.5,hgt(P.px+.5,P.py+.5)+.9,P.py+.5);gl.uniform1f(uTR.ss,SST);gl.uniform2f(uTR.sts,1/SMS,1/SMS);gl.uniform3fv(uTR.PL,PLA);gl.uniform1f(uTR.PLn,PLN);gl.uniform1f(uTR.PLs,PLS)}
gl.enableVertexAttribArray(3);gl.enableVertexAttribArray(4);TREX.vertexAttribDivisorANGLE(3,1);TREX.vertexAttribDivisorANGLE(4,1);let cur=null;
for(const [sp,l,v,off,cnt] of grp){if(v!==(shadow?0:1))continue;const e=TRP.sp[sp],m=e.lod[shadow?Math.min(2,l+1):l];if(!m||!e.tex)continue;
if(cur!==m){cur=m;gl.bindBuffer(gl.ARRAY_BUFFER,m.p);gl.vertexAttribPointer(0,3,gl.SHORT,false,6,0);if(!shadow){gl.bindBuffer(gl.ARRAY_BUFFER,m.n);gl.vertexAttribPointer(1,3,gl.BYTE,true,3,0);gl.bindBuffer(gl.ARRAY_BUFFER,m.uv);gl.vertexAttribPointer(2,2,gl.UNSIGNED_SHORT,true,4,0);gl.activeTexture(gl.TEXTURE4);gl.bindTexture(gl.TEXTURE_2D,e.tex);gl.activeTexture(gl.TEXTURE0)}gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,m.ib)}
gl.bindBuffer(gl.ARRAY_BUFFER,TRP.ibuf);gl.vertexAttribPointer(3,4,gl.FLOAT,false,32,off*32);gl.vertexAttribPointer(4,4,gl.FLOAT,false,32,off*32+16);TREX.drawElementsInstancedANGLE(gl.TRIANGLES,m.ni,gl.UNSIGNED_SHORT,0,cnt)}
TREX.vertexAttribDivisorANGLE(3,0);TREX.vertexAttribDivisorANGLE(4,0);gl.disableVertexAttribArray(3);gl.disableVertexAttribArray(4);gl.useProgram(shadow?pgS:pg)}
"""
rep("const attr=()=>{gl.vertexAttribPointer(aP,3,gl.FLOAT,false,36,0);", TREES.strip('\n') + "\nconst attr=()=>{gl.vertexAttribPointer(aP,3,gl.FLOAT,false,36,0);")

# 3. chunk builder: code-built trees only until the pack is in (stumps always)
rep("for(const o of L.t){YO=hgt(o.x+.5,o.y+.5);treeObj(o,LODT)}", "for(const o of L.t){if(TRP.on&&!o.dep)continue;YO=hgt(o.x+.5,o.y+.5);treeObj(o,LODT)}")
rep("else if(q>.972){bush(px,pz,q,x*977+y*13+3);MAT=5}", "else if(q>.972){if(!(TRP.on&&TRP.sp.bush))bush(px,pz,q,x*977+y*13+3);MAT=5}")

# 4. shadow pass and main pass
rep("if(DBN){gl.bindBuffer(gl.ARRAY_BUFFER,dbuf);attr();gl.drawArrays(gl.TRIANGLES,0,DBN)}if(MQL.length){",
    "if(DBN){gl.bindBuffer(gl.ARRAY_BUFFER,dbuf);attr();gl.drawArrays(gl.TRIANGLES,0,DBN)}treeDraw(1,VPm,now);if(MQL.length){")
rep("for(const ch of vcs)if(ch.on){gl.bindBuffer(gl.ARRAY_BUFFER,ch.ob);attr();gl.drawArrays(gl.TRIANGLES,0,ch.on)}\nsprQ.length=0;",
    "for(const ch of vcs)if(ch.on){gl.bindBuffer(gl.ARRAY_BUFFER,ch.ob);attr();gl.drawArrays(gl.TRIANGLES,0,ch.on)}\ntreeDraw(0,VPm,now);\nsprQ.length=0;")

open(PATH, 'w', encoding='utf-8').write(h)
print('Tree patch applied.')
