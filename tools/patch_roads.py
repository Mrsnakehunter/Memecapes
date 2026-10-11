#!/usr/bin/env python3
"""Road surfaces: town streets are paved by how important the place is; country roads stay dirt.

  cobblestone   every town centre: Castle Gigachad and Gigachad Town (the capital) with the King's Road down to Wow
                Landing, Stonks City, Diamond Hands, Moon Landing, HODL Heights, Chad Falls, a small market square in Wow
                Landing, and Rugpull Ridge with stones missing (it got rugged). Froggo's Pond stays swamp mud.
  concrete      Wall St. only.
  grey dirt     a ring of grey dirt around every paved area, which then blends into the normal tan dirt roads:
                cobble -> grey dirt -> dirt, with no hard line anywhere.
The paved areas are smooth round plazas (Gigachad Town and Wall St. are rounded rectangles), not tile-shaped.
The cobbles are irregular, randomly sized stones (a Voronoi pattern drawn by the terrain shader from world position),
and they thin out one by one where a plaza ends. Nothing extra to download.
How it works: every ground vertex carries how paved it is (0..1) and which material, in the length of its normal
(whole part = material + 1, fraction = 0.45 x paved). The vertex colour turns from tan to grey with it.
The minimap and world map show paved streets in grey.
Run from the repo root after patch_partner.py:  python3 tools/patch_roads.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


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
"""
rep("const CS=32,CN=Math.ceil(W/CS),chunks={};", PAVE + "const CS=32,CN=Math.ceil(W/CS),chunks={};")
# vertex colours: road corners turn from tan to grey as they get paved (smooth, follows the round plaza)
rep("const vcol=(x,y)=>{let r=0,g=0,b=0,n=0;", "const vcol=(x,y)=>{let r=0,g=0,b=0,n=0,rd=0;")
rep("const c=tile[ty][tx]==2?PA[hh(tx,ty)>.5|0]:GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;",
    "const c=tile[ty][tx]==2?PA[hh(tx,ty)>.5|0]:GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;if(tile[ty][tx]==2)rd=1;")
rep("let c=n?[r/n,g/n,b/n]:GR[0];const hv=gh(x,y)", "let c=n?[r/n,g/n,b/n]:GR[0];if(rd)c=paveCol(c,x,y);const hv=gh(x,y)")
# every road tile carries its material, every corner how paved it is
rep("else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1);[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>pvt(x+i,gh(x+i,y+j),y+j,V[3][0],V[3][1],V[3][2],V))}",
    "else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1),pc=t==2?paveAt(x+.5,y+.5):null,mm=pc&&pc[1]>0?pc[0]+1:1;"
    "[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>{let L=1;if(mm>1){const a=paveAt(x+i,y+j);L=mm+.45*(a[0]==pc[0]?a[1]:0)}pvt(x+i,gh(x+i,y+j),y+j,V[3][0]*L,V[3][1]*L,V[3][2]*L,V)})}")
# terrain shader (pg3)
rep("varying vec3 vwp;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);",
    "varying vec3 vwp;varying float vm,ve;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);float nl=length(n);vm=floor(nl+.02)-1.;ve=clamp((nl-vm-1.)/.45,0.,1.);")
rep("varying vec2 vl;varying vec3 vwp;uniform vec3 PL[8];",
    "varying vec2 vl;varying vec3 vwp;varying float vm,ve;float hs(vec3 p){return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453);}uniform vec3 PL[8];")
PAT = (
    "vec3 pv=vec3(mix(gp,sp,sand));"   # the ground as it was: tan dirt, or grey dirt where the vertex colour is grey
    "if(vm>10.5&&vm<14.5&&ve>.5){"
    "if(vm>11.5&&vm<12.5){"           # concrete (Wall St.): big slabs, worn and stained
    "vec2 g=fract(vw*.5);float w=.022;float se=1.-min(min(smoothstep(0.,w,g.x),smoothstep(0.,w,1.-g.x)),min(smoothstep(0.,w,g.y),smoothstep(0.,w,1.-g.y)));"
    "float k=smoothstep(.62,.8,ve+.08*(d-.5));vec3 cc=vec3(.95+.12*d)*(.94+.1*hs(vec3(floor(vw*.5),3.)))*(1.-.22*se)*(.97+.06*b);pv=mix(pv,cc,k);}"
    "else{"                            # cobblestones: irregular stones (Voronoi), random sizes and shades
    "vec2 q=vw*3.5+vec2(d,b)*.45;vec2 ip=floor(q),fp=fract(q);float F1=9.,F2=9.;vec2 id=ip;"
    "for(int j=-1;j<=1;j++)for(int i=-1;i<=1;i++){vec2 g=vec2(float(i),float(j));vec2 o=vec2(hs(vec3(ip+g,1.)),hs(vec3(ip+g,2.)))*.8+.1;vec2 r=g+o-fp;float dd=dot(r,r);if(dd<F1){F2=F1;F1=dd;id=ip+g;}else if(dd<F2){F2=dd;}}"
    "F1=sqrt(F1);F2=sqrt(F2);float st=smoothstep(.04,.14,F2-F1);float hv=hs(vec3(id,7.));"
    "float keep=step(hs(vec3(id,13.)),(ve-.6)*6.5-(vm>13.5?.62:0.)+.25*(d-.5));"   # stones thin out where the plaza ends; worn cobble has gaps
    "float sg=.78+.36*hv,wm=hs(vec3(id,9.));vec3 sc=vec3(sg*(1.+.08*wm),sg*(1.+.02*wm),sg*(.9+.08*hv))*(.93+.12*d)*clamp(1.16-1.5*F1*F1,.55,1.2);"
    "pv=mix(pv,mix(pv*vec3(.6,.58,.56),sc,st),keep);}}")
rep("c*=mix(gp,sp,sand);c+=vc/max(lm,.05)*mix(gp,sp,sand)*plt(vwp,vec3(0.,1.,0.));", PAT + "c*=pv;c+=vc/max(lm,.05)*pv*plt(vwp,vec3(0.,1.,0.));")
# minimap and world map: paved streets show grey
rep("tile[y][x]==2?'#c2a066':b?", "tile[y][x]==2?['#c2a066','#c2a066','#8f887d','#b9b5ac','#a8a092'][mapSurf(x,y)]:b?", 2)
rep("t==2?(q<3?'#c9a86c':'#c2a066'):", "t==2?[q<3?'#c9a86c':'#c2a066',q<3?'#c9a86c':'#c2a066',q<3?'#979085':'#8f887d',q<3?'#c0bcb3':'#b9b5ac',q<3?'#aea697':'#a8a092'][mapSurf(x,y)]:")

open(PATH, 'w', encoding='utf-8').write(h)
print('road surfaces patch applied')
