#!/usr/bin/env python3
"""Shores: natural water edges instead of square tile walls.

Before: every water tile was a box (bed at -0.72, straight brown walls up to the ground, flat water at -0.25), so
rivers, lakes and the sea had sharp square edges and stair-step corners.

Now (from research on terrain shorelines and depth-faded water):
  - A smooth shore field: tile centres are water (1) or land (0), joined by a Catmull-Rom curve (so a one-tile river
    keeps its width and corners become curves), with a little noise right at the edge so shores wobble naturally.
    Tile centres never change side, so nothing about walking or fishing changes.
  - The ground near water is a gentle bank: land slopes down into the water and the river bed keeps going down,
    deeper the further from land. The flat water surface meets that slope, which draws the shoreline.
    Tiles next to water are built from 4x4 smaller squares so the shoreline is a smooth curve.
  - Colours: a sand bank where land meets water, darker wet sand at the waterline, a sandy bed in the shallows
    fading to dark mud in deep water.
  - Water: see-through and turquoise in the shallows, deep blue further out (depth fade), a soft foam line along
    the shore and small waves washing in. Wave motion fades out at the shore so the edge doesn't flicker.
Run from the repo root after the other patches:  python3 tools/patch_water.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


SHORE = r"""
// ---- shores (tools/patch_water.py): a smooth water field, a sloping bank and a deepening bed
let BRS=null;const isWT=(x,y)=>tile[y][x]==1||(BRS!==null&&BRS[y*W+x]===1);   // bridge tiles count as water for the ground (the river runs under them)
const WLV=-.25,SAND=[.74,.66,.47],WETS=[.5,.44,.31],BED1=[.6,.55,.4],BED2=[.2,.28,.26];let SHT=null,SHD=null;
function shInit(){if(SHT)return;SHT=new Float32Array(W*H);SHD=new Float32Array(W*H);const Q=[];
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const k=y*W+x,w=isWT(x,y);SHT[k]=w?1:0;SHD[k]=w?1e9:0;if(!w)Q.push(k)}
 for(let qi=0;qi<Q.length;qi++){const k=Q[qi],x=k%W,y=(k/W)|0,d=SHD[k];for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++){if(!i&&!j)continue;const xx=x+i,yy=y+j;if(xx<0||yy<0||xx>=W||yy>=H)continue;const kk=yy*W+xx,nd=d+(i&&j?1.41:1);if(nd<SHD[kk]-.01){SHD[kk]=nd;Q.push(kk)}}}}
const shT=(x,y,A)=>A[(y<0?0:y>=H?H-1:y)*W+(x<0?0:x>=W?W-1:x)];
const shN=(x,z)=>{const ix=Math.floor(x),iz=Math.floor(z),fx=x-ix,fz=z-iz,u=fx*fx*(3-2*fx),v=fz*fz*(3-2*fz),a=hh(ix,iz),b=hh(ix+1,iz),c=hh(ix,iz+1),d=hh(ix+1,iz+1);return a+(b-a)*u+(c-a)*v+(a-b-c+d)*u*v};
const crw=t=>[((-t+2)*t-1)*t/2,((3*t-5)*t*t+2)/2,((-3*t+4)*t+1)*t/2,(t-1)*t*t/2];
const sst=(a,b,v)=>{v=Math.max(0,Math.min(1,(v-a)/(b-a)));return v*v*(3-2*v)};
function shF(X,Z){shInit();const fx=X-.5,fz=Z-.5,ix=Math.floor(fx),iz=Math.floor(fz),wx=crw(fx-ix),wz=crw(fz-iz);let s=0;
 for(let j=0;j<4;j++){let r=0;for(let i=0;i<4;i++)r+=wx[i]*shT(ix-1+i,iz-1+j,SHT);s+=wz[j]*r}
 if(s>.02&&s<.98)s+=(shN(X*.45+3.1,Z*.45+7.7)-.5)*.32*(1-Math.abs(2*s-1));return Math.max(0,Math.min(1,s))}
function shD(X,Z){shInit();const fx=X-.5,fz=Z-.5,ix=Math.floor(fx),iz=Math.floor(fz),u=fx-ix,v=fz-iz,a=shT(ix,iz,SHD),b=shT(ix+1,iz,SHD),c=shT(ix,iz+1,SHD),d=shT(ix+1,iz+1,SHD);return a+(b-a)*u+(c-a)*v+(a-b-c+d)*u*v}
function shH(X,Z,F){if(F<.5){const h0=hgt(X,Z);return h0+(WLV+.05-h0)*sst(.1,.5,F)}return WLV+.05-.36*sst(.5,1,F)-.5*Math.max(0,Math.min(1,(shD(X,Z)-.6)/3.4))}
const shG=(X,Z)=>shH(X,Z,shF(X,Z));
function shNrm(X,Z){const e=.2,hx=shG(X+e,Z)-shG(X-e,Z),hz=shG(X,Z+e)-shG(X,Z-e),l=Math.hypot(hx,2*e,hz);return[-hx/l,2*e/l,-hz/l]}
const mix3=(a,b,k)=>[a[0]+(b[0]-a[0])*k,a[1]+(b[1]-a[1])*k,a[2]+(b[2]-a[2])*k];
function shCol(base,X,Z,F,hv){const d=WLV-hv;
 if(F>=.5||!base)return mix3(d<.02?mix3(SAND,WETS,sst(-.08,.02,d)):BED1,BED2,sst(.02,.75,d));
 const s=sst(.16,.46,F+(shN(X*1.3+7,Z*1.3)-.5)*.16),w=sst(.4,.52,F);return mix3(mix3(base,SAND,s*.9),WETS,w*.8)}
// does this tile need the smooth shore treatment? (water next to land, or land next to water)
function shEdge(x,y){const w=isWT(x,y);for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++){const xx=x+i,yy=y+j;if(xx<0||yy<0||xx>=W||yy>=H)continue;if(isWT(xx,yy)!=w)return true}return false}
"""
rep("const CS=32,CN=Math.ceil(W/CS),chunks={};", SHORE + "const CS=32,CN=Math.ceil(W/CS),chunks={};")

OLD_TILE = ("if(t==1){const q=hh(x,y),v=1+(q-.5)*.12,c=[WA[0]*v,WA[1]*v,WA[2]*v];[[0,0],[1,0],[0,1],[1,0],[1,1],[0,1]].forEach(([i,j])=>{const s=shc(x+i,y+j),m=1-s;pvt(x+i,-.72,y+j,0,1,0,[BD[0]+(BDD[0]-BD[0])*m,BD[1]+(BDD[1]-BD[1])*m,BD[2]+(BDD[2]-BD[2])*m]);WB.push(x+i,-.25,y+j,c[0],c[1],c[2],s,0,0)});\n"
            "if(x>0&&tile[y][x-1]!=1)wall(x,y,x,y+1,1,0);if(x<W-1&&tile[y][x+1]!=1)wall(x+1,y,x+1,y+1,-1,0);if(y>0&&tile[y-1][x]!=1)wall(x,y,x+1,y,0,1);if(y<H-1&&tile[y+1][x]!=1)wall(x,y+1,x+1,y+1,0,-1)}\n"
            "else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1),pc=t!=1?paveAt(x+.5,y+.5):null,mm=pc&&pc[1]>0?pc[0]+1:1;[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>{let L=1;if(mm>1){const a=paveAt(x+i,y+j);L=mm+.45*(a[0]==pc[0]?a[1]:0)}pvt(x+i,gh(x+i,y+j),y+j,V[3][0]*L,V[3][1]*L,V[3][2]*L,V)})}}")
NEW_TILE = (
    "const tw=isWT(x,y),se=shEdge(x,y),wq=hh(x,y),wv=1+(wq-.5)*.12,cw=[WA[0]*wv,WA[1]*wv,WA[2]*wv];\n"
    # open water: a deepening bed and the surface, two triangles each
    "if(tw&&!se){[[0,0],[1,0],[0,1],[1,0],[1,1],[0,1]].forEach(([i,j])=>{const X=x+i,Z=y+j,hb=shG(X,Z);pvt(X,hb,Z,0,1,0,shCol(null,X,Z,1,hb));WB.push(X,WLV,Z,cw[0],cw[1],cw[2],WLV-hb,0,0)})}\n"
    # land away from water: as before
    "else if(!se){const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1),pc=paveAt(x+.5,y+.5),mm=pc&&pc[1]>0?pc[0]+1:1;[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>{let L=1;if(mm>1){const a=paveAt(x+i,y+j);L=mm+.45*(a[0]==pc[0]?a[1]:0)}pvt(x+i,gh(x+i,y+j),y+j,V[3][0]*L,V[3][1]*L,V[3][2]*L,V)})}\n"
    # the shore: 4x4 small squares with the bank, sand and the waterline
    "else{const N=4,lnd=!tw,A=lnd?vcol(x,y):null,B=lnd?vcol(x+1,y):null,C=lnd?vcol(x,y+1):null,D=lnd?vcol(x+1,y+1):null,pc=lnd?paveAt(x+.5,y+.5):null,mm=pc&&pc[1]>0?pc[0]+1:1,G=[];\n"
    " for(let j=0;j<=N;j++)for(let i=0;i<=N;i++){const u=i/N,v=j/N,X=x+u,Z=y+v,F=shF(X,Z),hv=shH(X,Z,F),nr=shNrm(X,Z);let base=null;\n"
    "  if(lnd)base=u+v<=1?[0,1,2].map(k=>A[k]+(B[k]-A[k])*u+(C[k]-A[k])*v):[0,1,2].map(k=>D[k]+(C[k]-D[k])*(1-u)+(B[k]-D[k])*(1-v));\n"
    "  let L=1;if(lnd&&mm>1){const a=paveAt(X,Z);L=mm+.45*(a[0]==pc[0]?a[1]:0)}G.push({X,Z,h:hv,n:nr,c:shCol(base,X,Z,F,hv),L,d:WLV-hv})}\n"
    " const P_=(i,j)=>G[j*(N+1)+i],put=g=>pvt(g.X,g.h,g.Z,g.n[0]*g.L,g.n[1]*g.L,g.n[2]*g.L,g.c),wat=g=>WB.push(g.X,WLV,g.Z,cw[0],cw[1],cw[2],g.d,0,0);\n"
    " for(let j=0;j<N;j++)for(let i=0;i<N;i++){const a=P_(i,j),b=P_(i+1,j),c=P_(i,j+1),d=P_(i+1,j+1);[a,b,c,b,d,c].forEach(put);if(Math.max(a.d,b.d,c.d,d.d)>-.02)[a,b,c,b,d,c].forEach(wat)}}}")
rep(OLD_TILE, NEW_TILE)

# water surface: no wave bobbing right at the shore
rep("vec3 q=p;q.y+=sin(p.x*1.1+t*1.6)*.022+sin(p.z*1.4+t*1.1+p.x*.3)*.022;",
    "vec3 q=p;q.y+=(sin(p.x*1.1+t*1.6)*.022+sin(p.z*1.4+t*1.1+p.x*.3)*.022)*smoothstep(0.,.3,n.x);")
# water colour: shallow see-through turquoise to deep blue, foam along the shoreline, little waves washing in
rep("float fm=smoothstep(.5,.85,vsh*1.2+(texture2D(dt,vw*.7+vec2(t*.04,-t*.03)).r-.5)*.45);c=mix(c,vec3(.93,.97,1.)*lm,fm*.75);float sh=shd();c*=1.-.35*sh;c+=sp*lm*(1.-sh);float f=clamp((vf-26.)/24.,0.,1.);gl_FragColor=vec4(mix(c,fogC,f),mix(.86+.1*fr+.14*fm,1.,f));",
    "float d=vsh;if(d<0.)discard;float nz=texture2D(dt,vw*.7+vec2(t*.04,-t*.03)).r,nz2=texture2D(dt,vw*1.9-vec2(t*.03,t*.05)).g;"
    "float dp=smoothstep(0.,.6,d);c=mix(mix(vec3(.33,.7,.68)*lm,c,.3),c,dp);"
    "float edge=1.-smoothstep(0.,.045+.05*nz,d);float lap=smoothstep(.72,1.,sin(d*36.-t*1.8+nz*5.))*(1.-smoothstep(.03,.2,d))*smoothstep(.35,.6,nz2);"
    "float fm=clamp(edge*.85+lap*.6,0.,1.);c=mix(c,vec3(.95,.98,1.)*lm,fm*.8);"
    "float sh=shd();c*=1.-.35*sh;c+=sp*lm*(1.-sh)*smoothstep(0.,.15,d);float f=clamp((vf-26.)/24.,0.,1.);"
    "float al=clamp(.28+.64*smoothstep(0.,.45,d)+.1*fr,0.,1.);al=max(al,fm*.9);gl_FragColor=vec4(mix(c,fogC,f),mix(al,1.,f));")

open(PATH, 'w', encoding='utf-8').write(h)
print('shores patch applied')
