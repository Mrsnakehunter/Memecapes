#!/usr/bin/env python3
"""Road surfaces (v3): town streets are paved by how important the place is; country roads stay dirt.

  cobblestone   every town centre: Castle Gigachad and Gigachad Town (the capital) with the King's Road down to Wow
                Landing, Stonks City, Diamond Hands, Moon Landing, HODL Heights, Chad Falls, a small market square in Wow
                Landing, and Rugpull Ridge with stones missing and moss (it got rugged). Froggo's Pond stays swamp mud.
  concrete      Wall St. only, with kerb stones and straight edges (a modern street).
  grey dirt     around every paved area, blending into the normal tan dirt roads.

v3 (after research on height-based blending and on how real squares are paved):
  - Road edges everywhere are drawn per pixel from a small map of the road tiles (texture RM): wavy, natural edges with
    grass tufts poking into the dirt, instead of blurry tile-shaped smudges. The old vertex-colour blend is undone
    exactly (same triangle interpolation as the mesh), so nothing else in the ground colour changes.
  - Cobbles are lit in 3D: each stone has a bevelled edge lit by the sun, a rough top, joints filled with dark dirt and
    moss, and random sizes, shades and hues (grey, blue-grey, warm tan).
  - Height blending where paving ends: dirt fills the joints first, then stones sink into the dirt with only their tops
    showing, then a few loose stones, then grey dirt, then dirt. Edges wobble but every plaza stays round.
  - A collar of big pale flagstones and one ring of edge stones around every paved town's fountain.
  - Patches where dirt has washed over the stones, moss near grass, loose pebbles on country dirt roads.
  - Rain: stones and dirt darken and shine, puddles collect on dirt and reflect the sky. Detail fades in the distance
    so far-off plazas do not shimmer.
How it works: every ground vertex carries how paved it is (0..1) and which material, in the length of its normal
(whole part = material + 1, fraction = 0.45 x paved). The vertex colour turns from tan to grey with it.
Texture RM ((W+1) x (H+1), unit 5): R = road tile, G = water tile, B = grey amount at that corner, A = concrete tile.
The minimap and world map show paved streets in grey.
Run from the repo root after patch_partner.py:  python3 tools/patch_roads.py
"""
import re

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


def glsl(s):
    """GLSL written readably below -> one line for the JS string (drops // comments and line breaks)."""
    out = []
    for line in s.split('\n'):
        line = re.sub(r'//.*$', '', line).strip()
        if line:
            out.append(line)
    s = ''.join(out)
    assert "'" not in s and '\\' not in s
    return s


PAVE = r"""
// ---- road surfaces (tools/patch_roads.py). A pave field gives each point how paved it is: 1 = cobbles (or concrete),
// falling through a band of grey dirt to 0 = plain dirt. Plazas are round around a town centre (radius = how important).
const PVT={'Stonks City':13,'Diamond Hands':12,'Moon Landing':12,'Chad Falls':11,'HODL Heights':11,'Rugpull Ridge':10,'Wow Landing':4.5};
const PVB=6.5;                                       // grey dirt then fade to dirt, in tiles beyond the paving
const PVWORN={'Rugpull Ridge':1};
const pvRect=(x,y,x0,y0,x1,y1)=>Math.hypot(Math.max(x0-x,0,x-x1),Math.max(y0-y,0,y-y1));   // 0 inside, distance outside
const pvSeg=(x,y,ax,ay,bx,by)=>{const vx=bx-ax,vy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*vx+(y-ay)*vy)/(vx*vx+vy*vy)));return Math.hypot(x-ax-vx*t,y-ay-vy*t)};
const pvF=d=>Math.max(0,Math.min(1,1-d/PVB));        // d = distance beyond the paved edge
function paveAt(x,y){let p=0,m=11;                     // [material, paved 0..1]; 11 cobble, 12 concrete, 14 worn cobble
 const take=(q,mm)=>{if(q>p){p=q;m=mm}};
 take(pvF(pvRect(x,y,137,106,181,160)-1.5),11);        // Castle Gigachad and Gigachad Town (rounded rectangle)
 take(pvF(pvSeg(x,y,157,160,157,178)-1.6),11);         // the King's Road down to Wow Landing
 take(pvF(pvRect(x,y,391,193,443,265)-1.5),12);        // Wall St.: concrete
 for(const t of TW){const R=PVT[t.n];if(!R)continue;take(pvF(Math.hypot(x-t.cx,y-t.cy)-R),PVWORN[t.n]?14:11)}
 return [m,p]}
const PVC=col('#8d877f'),PVK=col('#b3afa7');
const paveCol=(c,x,y)=>{const a=paveAt(x,y),g=Math.max(0,Math.min(1,(a[1]-.12)/.5)),q=a[0]==12?PVK:PVC;return[c[0]+(q[0]-c[0])*g,c[1]+(q[1]-c[1])*g,c[2]+(q[2]-c[2])*g]};
const mapSurf=(x,y)=>{if(tile[y][x]!=2)return 0;const a=paveAt(x+.5,y+.5);return a[1]>.55?(a[0]==12?3:2):a[1]>.2?4:1};   // for the maps: 2 cobble, 3 concrete, 4 grey dirt
// the road map for the terrain shader (made once, on the first frame) and the rain wetness
let RMT=null,WET=0;
function rmBind(){if(!RMT){const S=W+1,T=H+1,a=new Uint8Array(S*T*4);
  for(let y=0;y<T;y++)for(let x=0;x<S;x++){const k=(y*S+x)*4,t=x<W&&y<H?tile[y][x]:-1;a[k]=t==2?255:0;a[k+1]=t==1?255:0;
   let rd=0;for(let j=-1;j<=0;j++)for(let i=-1;i<=0;i++){const tx=x+i,ty=y+j;if(tx>=0&&ty>=0&&tx<W&&ty<H&&tile[ty][tx]==2)rd=1}
   if(rd){const p=paveAt(x,y);a[k+2]=Math.round(255*Math.max(0,Math.min(1,(p[1]-.12)/.5)))}
   if(t>=0){const p=paveAt(x+.5,y+.5);a[k+3]=p[0]==12&&p[1]>.3?255:0}}
  RMT=gl.createTexture();gl.activeTexture(gl.TEXTURE5);gl.bindTexture(gl.TEXTURE_2D,RMT);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,S,T,0,gl.RGBA,gl.UNSIGNED_BYTE,a);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  const F=[];PR.fount.forEach(([x,z])=>{const p=paveAt(x,z);if(p[1]>.9&&p[0]!=12&&F.length<36)F.push(x,z,1.62)});
  gl.uniform1i(u3RM,5);gl.uniform2f(u3RMs,S,T);gl.uniform3fv(u3FT,new Float32Array(F.length?F:[0,0,0]));gl.uniform1f(u3FTn,F.length/3)}
 gl.activeTexture(gl.TEXTURE5);gl.bindTexture(gl.TEXTURE_2D,RMT);gl.activeTexture(gl.TEXTURE0);
 WET+=((RAIN?1:0)-WET)*.006;gl.uniform1f(u3Wt,WET)}
"""
rep("const CS=32,CN=Math.ceil(W/CS),chunks={};", PAVE + "const CS=32,CN=Math.ceil(W/CS),chunks={};")
# vertex colours: road corners turn from tan to grey as they get paved (smooth, follows the round plaza)
rep("const vcol=(x,y)=>{let r=0,g=0,b=0,n=0;", "const vcol=(x,y)=>{let r=0,g=0,b=0,n=0,rd=0;")
rep("const c=tile[ty][tx]==2?PA[hh(tx,ty)>.5|0]:GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;",
    "const c=tile[ty][tx]==2?PA[hh(tx,ty)>.5|0]:GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;if(tile[ty][tx]==2)rd=1;")
rep("let c=n?[r/n,g/n,b/n]:GR[0];const hv=gh(x,y)", "let c=n?[r/n,g/n,b/n]:GR[0];if(rd)c=paveCol(c,x,y);const hv=gh(x,y)")
# every land tile carries its material, every corner how paved it is (grass tiles too, so cobbles follow the wavy road
# edge instead of stopping at a straight tile line)
rep("else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1);[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>pvt(x+i,gh(x+i,y+j),y+j,V[3][0],V[3][1],V[3][2],V))}",
    "else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1),pc=t!=1?paveAt(x+.5,y+.5):null,mm=pc&&pc[1]>0?pc[0]+1:1;"
    "[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>{let L=1;if(mm>1){const a=paveAt(x+i,y+j);L=mm+.45*(a[0]==pc[0]?a[1]:0)}pvt(x+i,gh(x+i,y+j),y+j,V[3][0]*L,V[3][1]*L,V[3][2]*L,V)})}")
# terrain shader (pg3): vertex side
rep("varying vec3 vwp;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);",
    "varying vec3 vwp;varying float vm,ve,vny;varying vec3 vv;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);float nl=length(n);vm=floor(nl+.02)-1.;ve=clamp((nl-vm-1.)/.45,0.,1.);vny=nn.y;vv=eye-p;")

DECL = glsl(r"""
varying float vm,ve,vny;varying vec3 vv;
uniform sampler2D RM;uniform vec2 RMs;uniform float wt,FTn;uniform vec3 FT[12];
float hs(vec3 p){return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453);}
vec4 rmT(vec2 w){return texture2D(RM,w/RMs);}
// how much road colour the mesh gave a corner (same weights as vcol: road 3, grass 1, water 0)
float cwt(vec2 p){vec4 t=rmT(p);float r=t.r*4.,w=t.g*4.,g=max(4.-r-w,0.);return 3.*r/max(3.*r+g,.0001);}
float cgy(vec2 p){return texture2D(RM,(p+.5)/RMs).b;}
// the mesh's own triangle interpolation of 4 corner values (0,0) (1,0) (0,1) (1,1)
float bary(vec4 v,vec2 f){return f.x+f.y<=1.?v.x+(v.y-v.x)*f.x+(v.z-v.x)*f.y:v.w+(v.z-v.w)*(1.-f.x)+(v.y-v.w)*(1.-f.y);}
// Voronoi stones: distance to the nearest joint (tiles), direction out through that joint, stone id
void vor(vec2 q,float sc,out float gw,out vec2 ow,out vec2 id,out float dc,out vec2 cd){vec2 ip=floor(q),fp=fract(q);float F1=9.,F2=9.;vec2 r1=vec2(0.),r2=vec2(1.);id=ip;
 for(int j=-1;j<=1;j++)for(int i=-1;i<=1;i++){vec2 g=vec2(float(i),float(j));vec2 o=vec2(hs(vec3(ip+g,1.)),hs(vec3(ip+g,2.)))*.76+.12;vec2 r=g+o-fp;float dd=dot(r,r);
  if(dd<F1){F2=F1;r2=r1;F1=dd;r1=r;id=ip+g;}else if(dd<F2){F2=dd;r2=r;}}
 vec2 e=r2-r1;float le=max(length(e),.0001);ow=e/le;gw=max(dot((r1+r2)*.5,ow),0.)/sc;dc=length(r1)/sc;cd=-r1/max(length(r1),.0001);}
""")
rep("varying vec2 vl;varying vec3 vwp;uniform vec3 PL[8];", "varying vec2 vl;varying vec3 vwp;" + DECL + "uniform vec3 PL[8];")

# fragment, first thing: redraw where road meets grass (wavy edge + grass tufts) by undoing the vertex blend
FIX = glsl(r"""
vec3 vcc=vc;float rdz=0.;
{vec2 o=floor(vw),f=vw-o;vec4 tc=rmT(o+.5);float ny=smoothstep(.55,.8,vny);
 if(tc.g<.5&&ny>0.){
  float tv=bary(vec4(cwt(o),cwt(o+vec2(1.,0.)),cwt(o+vec2(0.,1.)),cwt(o+1.)),f);
  float gy=bary(vec4(cgy(o),cgy(o+vec2(1.,0.)),cgy(o+vec2(0.,1.)),cgy(o+1.)),f);
  vec2 wn=vec2(texture2D(dt,vw*.21+.13).r,texture2D(dt,vw*.21+.61).g)-.5;
  float tuft=texture2D(dt,vw*5.3).g-.5+.6*(texture2D(dt,vw*2.1+.4).r-.5);
  vec4 rh=rmT(vw);float rs=rmT(vw+wn*.7).r;
  rdz=mix(smoothstep(.22,.47,rs+tuft*.3),smoothstep(.47,.53,rh.r),step(.5,rh.a));float gside=(1.-rdz)*smoothstep(.02,.3,rs)*(1.-rh.a);
  vec3 G=vec3(.298,.624,.275),R=vec3(.741,.608,.384),Q=mix(vec3(.553,.529,.498),vec3(.702,.686,.655),rh.a);
  vcc=vc+(mix(G,mix(R,Q,gy),rdz)-mix(mix(G,R,tv),Q,gy))*lm*ny;vcc*=mix(vec3(1.),vec3(.93,.94,.8),gside*.7*ny);}}
vec3 c=vcc*l;
""")
rep("void main(){float sh=shd();float l=vl.x+vl.y*(1.-sh);vec3 c=vc*l;float sand",
    "void main(){float sh=shd();float l=vl.x+vl.y*(1.-sh);" + FIX + "float sand")

PAT = glsl(r"""
vec3 pv=vec3(mix(gp,sp,sand));vec3 pv0=pv;float SP=0.;
float lod=1.-smoothstep(15.,32.,vf);
vec3 LS=vec3(.466,.828,.311);vec3 Hh=normalize(LS+normalize(vv));
float pdl=texture2D(dt,vw*.09+.33).g;float hidden=1.;
if(rdz>.01&&vm>10.5&&vm<14.5){
 float worn=step(13.5,vm);
 float nl=texture2D(dt,vw*.047+.29).r;float nm=texture2D(dt,vw*.13+.71).b;
 float pe=ve+(d-.5)*.3+(nl-.5)*.2;
 if(vm>11.5&&vm<12.5){
  // concrete (Wall St.): staggered slabs, stains, kerb stones along the straight street edge
  float row=floor(vw.y);float sx=vw.x+hs(vec3(row,4.,4.))*.7;vec2 cl=vec2(floor(sx),row);vec2 g=vec2(fract(sx),fract(vw.y));
  float jd=min(min(g.x,1.-g.x),min(g.y,1.-g.y));float jn=1.-smoothstep(.008,.026,jd);
  float stn=smoothstep(.55,.85,nm)*.12+smoothstep(.62,.9,texture2D(dt,vw*.6+.3).r)*.07;
  vec3 cc=vec3(.97,.965,.95)*(.93+.09*hs(vec3(cl,3.)))*(.96+.08*d)*(1.-stn)*(1.-.3*jn);
  float rsn=rmT(vw).r;float kb=smoothstep(.5,.52,rsn)*(1.-smoothstep(.6,.62,rsn));
  cc=mix(cc,vec3(1.06,1.05,1.03)*(.95+.05*d)*(1.-.25*(1.-smoothstep(.0,.012,min(abs(rsn-.51),abs(rsn-.61))))),kb);
  cc*=1.-.3*(smoothstep(.46,.5,rsn)-smoothstep(.5,.51,rsn));
  float k=smoothstep(.6,.8,pe);cc*=1.-.25*wt;
  pv=mix(pv,cc,k);SP=pow(max(Hh.y,0.),80.)*(.03+.45*wt)*k;hidden=1.-k;
 }else{
  float cov=clamp(smoothstep(.5,.85,pe)-smoothstep(.62,.82,nl)*.4-worn*.22,0.,1.);
  // the nearest fountain: a collar of big flagstones, then one ring of edge stones
  float fr=99.,fR=0.;vec2 fd=vec2(1.,0.);
  for(int i=0;i<12;i++){if(float(i)>=FTn)break;vec2 dv=vw-FT[i].xy;float r=length(dv);if(r<fr){fr=r;fR=FT[i].z;fd=dv/max(r,.001);}}
  float rb=fr-fR;float gw;vec2 ow,id;float sg,h1,h2,h3,dc,jx=0.;vec2 cd;vec3 tint;
  if(rb>-.3&&rb<1.45){
   cov=max(cov,smoothstep(1.6,1.3,rb));
   if(rb<1.05){vor(vw*1.85+(vec2(d,b)-.5)*.2,1.85,gw,ow,id,dc,cd);h1=hs(vec3(id,7.));h2=hs(vec3(id,9.));h3=.95;
    sg=.9+.14*h1;tint=mix(vec3(1.03,1.,.94),vec3(1.07,1.02,.9),h2);}
   else{float n=floor(6.2832*(fR+1.25)/.36);float a=(atan(fd.y,fd.x)/6.2832+.5)*n;float u=fract(a),v=(rb-1.05)/.4;
    float du=min(u,1.-u)*.36,dv2=min(v,1.-v)*.4;gw=min(du,dv2);
    ow=du<dv2?vec2(-fd.y,fd.x)*(u<.5?-1.:1.):fd*(v<.5?-1.:1.);id=vec2(floor(a),fR);dc=max(.2-gw,.0);cd=ow;jx=.008;
    h1=hs(vec3(id,1.));h2=hs(vec3(id,2.));h3=.95;sg=.76+.1*h1;tint=vec3(.97,.98,1.);}
  }else{
   vor(vw*4.+(vec2(d,b)-.5)*.25,4.,gw,ow,id,dc,cd);h1=hs(vec3(id,7.));h2=hs(vec3(id,9.));h3=hs(vec3(id,13.));
   sg=(.76+.26*h1)*(1.-.15*worn*h2);tint=mix(vec3(.96,.975,1.01),vec3(1.05,1.,.91),h2);}
  // one stone: bevelled edge lit by the sun, rough top, dirt and moss in the joints
  float jw=.007+.006*worn+jx,t=clamp(dc/max(dc+gw,.0001),0.,1.),hg=1.-t*t*t;
  vec2 dir=normalize(mix(cd,ow,t*t));float tl=1.1*t*t*smoothstep(jw*.5,jw+.02,gw);
  vec2 nz=(vec2(texture2D(dt,vw*2.9).r,texture2D(dt,vw*2.9+.5).g)-.5)*.3;
  vec3 N=normalize(vec3(dir.x*tl+nz.x,1.,dir.y*tl+nz.y));
  float lam=max(dot(N,LS),0.)/.828,ao=mix(.62,1.,smoothstep(0.,jw+.035,gw));
  vec3 stc=vec3(sg)*tint*(.9+.2*texture2D(dt,vw*4.3+h1).r)*(.95+.08*d)*mix(1.,lam,.8)*(.95+.08*hg);
  float mo=clamp(smoothstep(.5,.78,nm)*.7+worn*.45+(1.-cov)*.25,0.,1.);
  vec3 jc=mix(pv*vec3(.66,.62,.56),pv*vec3(.5,.7,.36),mo*.75);
  vec3 scol=mix(stc,jc,1.-smoothstep(jw*.4,jw+.01,gw))*ao;
  // height blend: the dirt fills the joints first, then covers the low stones, the tallest tops show longest
  float vis=smoothstep(-.05,.05,hg*.85+(h3-.5)*.45-(1.-cov)*1.2+.06);
  vec3 res=mix(pv*vec3(.95,.93,.9),scol,vis)*(1.-wt*mix(.18,.3,vis));
  vec3 avg=mix(pv,vec3(.8,.79,.78)*(.94+.1*d),cov*.75);
  pv=mix(avg,res,lod);hidden=1.-vis*cov;
  SP=pow(max(dot(N,Hh),0.),50.)*(.03+.55*wt)*vis*lod;
 }
}else if(rdz>.3&&vm<10.5){
 // loose pebbles on dirt roads
 vec2 pq=vw*3.;vec2 pi=floor(pq);float ph=hs(vec3(pi,21.));
 if(ph<.07){vec2 pcn=pi+.25+.5*vec2(hs(vec3(pi,22.)),hs(vec3(pi,23.)));vec2 dv=pq-pcn;float pr=.07+.07*hs(vec3(pi,24.)),dl=length(dv);
  float pm=(1.-smoothstep(pr*.75,pr,dl))*smoothstep(.3,.5,rdz)*lod;vec2 pn=dv/max(dl,.001)*(dl/pr)*.9;vec3 Np=normalize(vec3(pn.x,1.,pn.y));float lp=max(dot(Np,LS),0.)/.828;
  float sh2=(1.-smoothstep(pr,pr*1.5,length(dv-vec2(.45,.3)*pr*.6)))*.12*(1.-pm);
  pv=mix(pv*(1.-sh2*lod),vec3(.95+ph*2.)*vec3(.98,.96,.92)*lp*(1.-.25*wt),pm);hidden=1.-pm;}}
// rain: dirt darkens, puddles collect in the low spots and mirror the sky
if(rdz>.01){float pd=smoothstep(.64,.72,pdl-.3*(1.-rdz))*wt*hidden*rdz;
 pv*=1.-.22*wt*hidden;
 pv=mix(pv,fogC*.8/max(c,vec3(.04)),pd*.7);SP+=pow(max(Hh.y,0.),200.)*pd;
 pv=mix(pv0,pv,rdz);SP*=rdz;}
""")
rep("c*=mix(gp,sp,sand);c+=vc/max(lm,.05)*mix(gp,sp,sand)*plt(vwp,vec3(0.,1.,0.));",
    PAT + "c*=pv;c+=SP*vec3(.85,.88,.95)*lm;c+=vcc/max(lm,.05)*pv*plt(vwp,vec3(0.,1.,0.));")
# uniforms and the per-frame bind
rep("u3PLs=gl.getUniformLocation(pg3,'PLs');",
    "u3PLs=gl.getUniformLocation(pg3,'PLs'),u3RM=gl.getUniformLocation(pg3,'RM'),u3RMs=gl.getUniformLocation(pg3,'RMs'),u3Wt=gl.getUniformLocation(pg3,'wt'),u3FT=gl.getUniformLocation(pg3,'FT'),u3FTn=gl.getUniformLocation(pg3,'FTn');")
rep("gl.useProgram(pg3);gl.uniformMatrix4fv(u3M,false,VPm);", "gl.useProgram(pg3);rmBind();gl.uniformMatrix4fv(u3M,false,VPm);")
# minimap and world map: paved streets show grey
rep("tile[y][x]==2?'#c2a066':b?", "tile[y][x]==2?['#c2a066','#c2a066','#8f887d','#b9b5ac','#a8a092'][mapSurf(x,y)]:b?", 2)
rep("t==2?(q<3?'#c9a86c':'#c2a066'):", "t==2?[q<3?'#c9a86c':'#c2a066',q<3?'#c9a86c':'#c2a066',q<3?'#979085':'#8f887d',q<3?'#c0bcb3':'#b9b5ac',q<3?'#aea697':'#a8a092'][mapSurf(x,y)]:")

open(PATH, 'w', encoding='utf-8').write(h)
print('road surfaces patch applied')
