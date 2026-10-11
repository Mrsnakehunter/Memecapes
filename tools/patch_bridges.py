#!/usr/bin/env python3
"""Bridges: one proper bridge per crossing, built to be remembered.

Before: a bridge appeared wherever a wandering road happened to step onto water, so rivers had clusters of tiny
plank bridges (three side by side at Wow Landing, a road running down the middle of the river) and one decorative
hump bridge stood on dry land at HODL Heights.

Now:
  - Planning (once, when the world is made): bridge tiles are grouped into clusters. Each cluster gets its best
    straight crossing (the shortest straight run over the water with dry land at both ends, up to 9 tiles).
    Crossings close together (within 16 tiles) are merged: the one on the main road nearest a town is kept.
    Leftover bridge tiles turn back into water, unless removing them would cut off land you could reach before
    (checked with a walk over the whole map): then they come back as a timber boardwalk.
    Anything left standing on tiles that became water (lamps, signs) is removed. The decorative bridge on dry land
    at HODL Heights is gone.
  - Stone bridges: an arched deck you walk over (the walking height follows the arch), stone parapets with caps,
    a real arch over the water with a ring of light and dark arch stones and a gold MemeCapes coin on the keystone,
    spandrel walls, wing walls into the banks, a central pier with cutwaters on long spans, tall end posts with
    stone balls, crimson and gold pennants, and real lamps at two corners that light up at night.
  - Timber bridges near Froggo's Pond and for short hops: plank decks with gaps, beams, posts into the water,
    handrails and cross braces, swamp lanterns.
  - Boardwalks (only where needed to keep land reachable): plank walkways on posts with rails along the water.
  - The river keeps flowing under every bridge (the shore patch treats bridge tiles as water).
Run from the repo root after patch_water.py:  python3 tools/patch_bridges.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


PLAN = r"""
// ---- bridges (tools/patch_bridges.py): plan one good crossing per spot, keep land reachable
const BRG=[],BWK=[];
(function bridgePlan(){
 const N_=W*H,isB=new Uint8Array(N_);BR.forEach(([x,y])=>isB[y*W+x]=1);
 const land=(x,y)=>ok(x,y)&&tile[y][x]!=1&&!isB[y*W+x];
 const seen=new Uint8Array(N_),CL=[];
 for(const [x0,y0] of BR){const k0=y0*W+x0;if(seen[k0])continue;const c=[],st=[[x0,y0]];seen[k0]=1;
  while(st.length){const [x,y]=st.pop();c.push([x,y]);for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++){const xx=x+i,yy=y+j;if(!ok(xx,yy))continue;const kk=yy*W+xx;if(isB[kk]&&!seen[kk]){seen[kk]=1;st.push([xx,yy])}}}CL.push({t:c})}
 const span=(x,y,dx,dy)=>{let a=0,b=0;while(a<13&&ok(x-dx*(a+1),y-dy*(a+1))&&!land(x-dx*(a+1),y-dy*(a+1)))a++;while(b<13&&ok(x+dx*(b+1),y+dy*(b+1))&&!land(x+dx*(b+1),y+dy*(b+1)))b++;
  const sx=x-dx*a,sy=y-dy*a,n=a+b+1;if(n>12||!land(sx-dx,sy-dy)||!land(sx+dx*n,sy+dy*n))return null;return{x:sx,y:sy,dx,dy,n}};
 const twn=(x,y)=>Math.min(...TW.map(t=>Math.hypot(x-t.cx,y-t.cy)),Math.hypot(x-CA.gx,y-(CA.y+CA.h)));
 for(const c of CL){let best=null;const cx=c.t.reduce((a,p)=>a+p[0],0)/c.t.length,cy=c.t.reduce((a,p)=>a+p[1],0)/c.t.length;
  for(const [x,y] of c.t)for(const [dx,dy] of [[1,0],[0,1]]){const s=span(x,y,dx,dy);if(!s)continue;const mx=s.x+dx*s.n/2,my=s.y+dy*s.n/2,sc=s.n+.15*Math.hypot(mx-cx,my-cy);if(!best||sc<best.sc){best=s;s.sc=sc;s.mx=mx;s.my=my}}
  c.s=best;c.keep=0;c.bw=0}
 // merge crossings that sit close together: keep the one nearest a town
 const rds=(x,y)=>{let k=0;for(let j=-2;j<=2;j++)for(let i=-2;i<=2;i++)if(land(x+i,y+j)&&tile[y+j][x+i]==2)k++;return k};
 for(const c of CL)if(c.s){const s=c.s;c.sc=twn(s.mx,s.my)+.6*s.n-.8*Math.min(rds(s.x-s.dx,s.y-s.dy),rds(s.x+s.dx*s.n,s.y+s.dy*s.n))}
 const grp=CL.filter(c=>c.s).sort((a,b)=>a.sc-b.sc);
 for(const c of grp){if(grp.some(o=>o.keep&&Math.hypot(o.s.mx-c.s.mx,o.s.my-c.s.my)<16))continue;c.keep=1}
 for(const c of CL)if(!c.s)c.bw=1;   // no straight crossing: a boardwalk keeps it
 // walk the map: anything reachable before must stay reachable
 const reach=pass=>{const R=new Uint8Array(N_),sx=CA.gx,sy=CA.y+CA.h+2,Q=[sy*W+sx];R[Q[0]]=1;for(let qi=0;qi<Q.length;qi++){const k=Q[qi],x=k%W,y=(k/W)|0;for(const [i,j] of [[1,0],[-1,0],[0,1],[0,-1]]){const xx=x+i,yy=y+j;if(!ok(xx,yy))continue;const kk=yy*W+xx;if(!R[kk]&&pass(xx,yy)){R[kk]=1;Q.push(kk)}}}return R};
 const R0=reach((x,y)=>tile[y][x]!=1);
 const plan=()=>{const P=new Uint8Array(N_);for(const c of CL){if(c.bw)c.t.forEach(([x,y])=>P[y*W+x]=1);else if(c.keep)for(let i=0;i<c.s.n;i++)P[(c.s.y+c.s.dy*i)*W+c.s.x+c.s.dx*i]=1}return P};
 for(let it=0;it<60;it++){const P=plan(),R1=reach((x,y)=>land(x,y)||P[y*W+x]);let lost=-1;
  for(let k=0;k<N_&&lost<0;k++)if(R0[k]&&!R1[k]&&!isB[k])lost=k;if(lost<0)break;
  const lx=lost%W,ly=(lost/W)|0;let bc=null,bd=1e9;for(const c of CL){if(c.bw||c.keep&&!c.s)continue;for(const [x,y] of c.t){const d=Math.hypot(x-lx,y-ly);if(d<bd&&!(c.keep&&c.bw)){bd=d;bc=c}}}
  if(!bc)break;if(bc.s&&!bc.keep)bc.keep=1;else bc.bw=1}
 // apply: unused bridge tiles become water again, kept crossings become bridges
 const P=plan();BR.length=0;BRS=new Uint8Array(N_);
 for(const c of CL)for(const [x,y] of c.t)if(!P[y*W+x])tile[y][x]=1;
 for(const c of CL){if(c.bw){c.t.forEach(([x,y])=>{tile[y][x]=2;BRS[y*W+x]=1;BR.push([x,y]);BWK.push([x,y])})}
  else if(c.keep){const s=c.s;for(let i=0;i<s.n;i++){const x=s.x+s.dx*i,y=s.y+s.dy*i;tile[y][x]=2;BRS[y*W+x]=1;BR.push([x,y])}
   const e0=[s.x,s.y],e1=[s.x+s.dx*s.n,s.y+s.dy*s.n];const hb=Math.max(0,HG[e0[1]*HW+e0[0]],HG[e1[1]*HW+e1[0]]);
   const style=(Math.hypot(s.mx-TW[1].cx,s.my-TW[1].cy)<45||s.n<=2)?1:0,rise=style?Math.min(.55,.08*s.n+.12):Math.min(1.05,.13*s.n+.17);
   const b={x:s.x,y:s.y,dx:s.dx,dy:s.dy,n:s.n,base:hb,rise,style};BRG.push(b);
   for(let i=0;i<=s.n;i++){const hv=hb+rise*Math.sin(Math.PI*i/s.n),vx=s.x+s.dx*i,vy=s.y+s.dy*i;HG[vy*HW+vx]=hv;HG[(vy+s.dx)*HW+vx+s.dy]=hv}
   const dw=style?.75:.9,o=s.dx?[[s.x-.25,s.y+.5-dw-.15],[s.x+s.n+.25,s.y+.5+dw+.15]]:[[s.x+.5-dw-.15,s.y-.25],[s.x+.5+dw+.15,s.y+s.n+.25]];o.forEach(p=>PR.lamps.push([p[0],p[1]]))}}
 for(const [x,y] of BWK)for(const [i,j] of [[0,0],[1,0],[0,1],[1,1]]){const k=(y+j)*HW+x+i;HG[k]=Math.max(HG[k],.12)}
 // nothing left standing in the water
 const dry=a=>{const x=Math.floor(a[0]),y=Math.floor(a[1]);return !ok(x,y)||tile[y][x]!=1};
 ['lamps','signs','stalls','wells','booths','npcs','guards','fount','forges','ranges'].forEach(k=>{if(Array.isArray(PR[k]))PR[k]=PR[k].filter(dry)});
 for(let i=XO.length-1;i>=0;i--)if(!dry([XO[i].x,XO[i].y]))XO.splice(i,1);
 // the decorative bridge on dry land (not a crossing) goes
 for(let i=DECO.length-1;i>=0;i--)if(DECO[i][0]=='b_hbridge'){const d=DECO[i];for(let y=Math.floor(d[2]-3);y<=d[2]+3;y++)for(let x=Math.floor(d[1]-3);x<=d[1]+3;x++)if(ok(x,y)&&ob[y][x]&&ob[y][x].k=='bld')ob[y][x]=null;DECO.splice(i,1)}
})();
"""
rep("const CKIT=(()=>{", PLAN + "const CKIT=(()=>{")

# the road map for the ground shader: bridge tiles are water underneath, not road
rep("a[k]=t==2?255:0;a[k+1]=t==1?255:0;", "const bw=t>=0&&isWT(x,y);a[k]=t==2&&!bw?255:0;a[k+1]=bw?255:0;")

# chunk lists: bridges by their middle, boardwalk tiles where they are
rep("BR.forEach(a=>obl(a[0],a[1]).br.push(a));",
    "BRG.forEach(b=>{const o=obl(b.x+b.dx*b.n/2,b.y+b.dy*b.n/2);(o.bg||(o.bg=[])).push(b)});BWK.forEach(a=>{const o=obl(a[0],a[1]);(o.bw||(o.bw=[])).push(a)});")

DRAW = r"""
// ---- drawing bridges: oriented boxes (with outlines) and quads
function obox(c,U,V,N,a,b,d,cl){if(typeof cl=='string')cl=col(cl);if(OUT&&!INH&&Math.min(a,b,d)>OUT){INH=1;const b0=buf,i0=bi;buf=HB;bi=hi;obox(c,U,V,N,a+OUT,b+OUT,d+OUT,OUTC);hi=bi;buf=b0;bi=i0;INH=0}
 for(const [A,B,C,ha,hb,hc] of [[U,V,N,a,b,d],[V,N,U,b,d,a],[N,U,V,d,a,b]])for(const s of [1,-1]){const P=(i,j)=>[c[0]+A[0]*ha*s+B[0]*hb*i+C[0]*hc*j,c[1]+A[1]*ha*s+B[1]*hb*i+C[1]*hc*j,c[2]+A[2]*ha*s+B[2]*hb*i+C[2]*hc*j],q=[P(-1,-1),P(1,-1),P(1,1),P(-1,1)];
  [0,1,2,0,2,3].forEach(k=>pv(q[k][0],q[k][1],q[k][2],A[0]*s,A[1]*s,A[2]*s,cl))}}
function quad(p0,p1,p2,p3,n,cl){if(typeof cl=='string')cl=col(cl);const q=[p0,p1,p2,p3];[0,1,2,0,2,3].forEach(k=>pv(q[k][0],q[k][1],q[k][2],n[0],n[1],n[2],cl))}
const vA=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]],vS=(a,k)=>[a[0]*k,a[1]*k,a[2]*k];
function bridgeObj(b){const{x,y,dx,dy,n,base,rise,style}=b,A=[dx,0,dy],S=[dy,0,dx],UP=[0,1,0],O=dx?[x,0,y+.5]:[x+.5,0,y],YO0=YO;YO=0;
 const P=(u,hh,w)=>[O[0]+A[0]*u+S[0]*w,hh,O[2]+A[2]*u+S[2]*w],dk=u=>{const s=u/n;return s<=0||s>=1?base:base+rise*Math.sin(Math.PI*s)};
 const DW=style?1.3:1.6,T=style?.12:.24,e=.4,K=Math.ceil((n+2*e)*4),fr=(u0,u1)=>{const h0=dk(u0),h1=dk(u1),du=u1-u0,dh=h1-h0,L=Math.hypot(du,dh);return{h0,h1,L,um:(u0+u1)/2,hm:(h0+h1)/2,U:[A[0]*du/L,dh/L,A[2]*du/L],V:[-A[0]*dh/L,du/L,-A[2]*dh/L]}};
 if(!style){
  // stone: paved deck, parapets with caps
  for(let i=0;i<K;i++){const u0=-e+(n+2*e)*i/K,u1=-e+(n+2*e)*(i+1)/K,f=fr(u0,u1);MAT=1;
   obox(vA(P(f.um,f.hm,0),vS(f.V,-T/2)),f.U,f.V,S,f.L/2+.006,T/2,DW/2,i%3==0?'#8a847c':i%3==1?'#969088':'#8f8981');
   for(const sd of [-1,1]){const w=sd*(DW/2-.1);obox(vA(P(f.um,f.hm,w),vS(f.V,.24)),f.U,f.V,S,f.L/2+.006,.24,.1,i%2?'#a69d8f':'#9f9688');obox(vA(P(f.um,f.hm,w),vS(f.V,.51)),f.U,f.V,S,f.L/2+.012,.035,.13,'#c4bbad')}}
  // arches: one, or two with a pier on long spans
  const AR=n>=7?[[0,n/2-.3],[n/2+.3,n]]:[[0,n]],hs=WLV-.5;
  for(const [ua,ub] of AR){const M=Math.max(6,Math.ceil((ub-ua)*5)),crown=Math.min(dk((ua+ub)/2),dk(ua+.01),dk(ub-.01))-T-.22,top=dk((ua+ub)/2)-T-.3,hc=Math.max(hs+.45,top);
   const yi=u=>hs+(hc-hs)*Math.pow(Math.max(0,Math.sin(Math.PI*(u-ua)/(ub-ua))),.75);
   for(let i=0;i<M;i++){const a=ua+(ub-ua)*i/M,c2=ua+(ub-ua)*(i+1)/M,ya=yi(a),yb=yi(c2),da=dk(a)-T,db=dk(c2)-T;MAT=1;
    for(const sd of [-1,1]){const w=sd*DW/2;quad(P(a,ya,w),P(c2,yb,w),P(c2,db,w),P(a,da,w),vS(S,sd),i%2?'#978e82':'#91897d');
     const du=c2-a,dh=yb-ya,L=Math.hypot(du,dh),U=[A[0]*du/L,dh/L,A[2]*du/L],V=[-A[0]*dh/L,du/L,-A[2]*dh/L],key=i==Math.floor(M/2);
     obox(vA(P((a+c2)/2,(ya+yb)/2,sd*(DW/2+.035)),vS(V,.14)),U,V,S,L/2-.012,key?.2:.14,.05,key?'#e2d9c7':i%2?'#cdc4b4':'#aaa192');
     if(key){MAT=0;obox(vA(P((a+c2)/2,(ya+yb)/2,sd*(DW/2+.1)),vS(V,.17)),U,V,S,.1,.1,.02,'#ffd23f');MAT=1}}
    quad(P(a,ya,-DW/2),P(c2,yb,-DW/2),P(c2,yb,DW/2),P(a,ya,DW/2),[0,-1,0],'#6b655c')}}
  if(n>=7){const um=n/2,top=dk(um)-T,hgt_=top-(WLV-.7);MAT=1;obox(P(um,(top+WLV-.7)/2,0),A,UP,S,.32,hgt_/2,DW/2,'#8c847a');
   for(const sd of [-1,1])boxR(...P(um,0,sd*(DW/2+.1)).map((v,k)=>k==1?(WLV-.7+top)/2-.2:v),.5,hgt_-.4,.5,Math.PI/4,'#857d73')}
  // wing walls into the banks and the end posts with pennants
  for(const [ue,dir] of [[-e,-1],[n+e,1]])for(const sd of [-1,1]){const hp=base;MAT=1;
   obox(P(ue-dir*.25,(hp+WLV-.6)/2,sd*(DW/2+.12)),A,UP,S,.55,(hp-(WLV-.6))/2,.16,'#8f877b');
   const pp=P(ue,0,sd*(DW/2-.1));boxR(pp[0],hp+.48,pp[2],.34,.96,.34,0,'#a89f91');boxR(pp[0],hp+.99,pp[2],.42,.06,.42,0,'#c4bbad');ball(pp[0],hp+1.14,pp[2],.15,.15,.15,0,'#d2c9b9',8);
   if(sd==dir){MAT=2;tube([pp[0],hp+1.2,pp[2]],[pp[0],hp+2.3,pp[2]],.025,.02,'#3a2a1a',5,1);MAT=0;const fx=pp[0]+A[0]*dir*.02,fz=pp[2]+A[2]*dir*.02,t0=[fx,hp+2.25,fz],t1=[fx,hp+1.8,fz],t2=vA([fx,hp+2.02,fz],vS(A,dir*-.75));quad(t0,t1,t2,t2,S,'#b0182b');ball(pp[0],hp+2.32,pp[2],.05,.05,.05,0,'#ffd23f',5)}}}
 else{
  // timber: planks with gaps, beams, posts, handrails, cross braces
  const np=Math.ceil((n+2*e)/.2);for(let i=0;i<np;i++){const u0=-e+i*.2,u1=u0+.17,f=fr(u0,u1);MAT=2;obox(vA(P(f.um,f.hm,0),vS(f.V,-.04)),f.U,f.V,S,f.L/2,.04,DW/2,['#8a5a2b','#7a4a22','#94632f','#83552a'][i%4])}
  for(let i=0;i<K;i++){const u0=-e+(n+2*e)*i/K,u1=-e+(n+2*e)*(i+1)/K,f=fr(u0,u1);MAT=2;for(const sd of [-1,1]){obox(vA(P(f.um,f.hm,sd*DW/3),vS(f.V,-.14)),f.U,f.V,S,f.L/2+.01,.06,.06,'#5a3a1a');obox(vA(P(f.um,f.hm,sd*DW/2),vS(f.V,.72)),f.U,f.V,S,f.L/2+.01,.035,.04,'#6b4422');obox(vA(P(f.um,f.hm,sd*DW/2),vS(f.V,.38)),f.U,f.V,S,f.L/2+.01,.025,.03,'#6b4422')}}
  const posts=[];for(let u=0;u<=n+.001;u+=Math.max(1,n/Math.max(1,Math.round(n/1.5))))posts.push(u);posts.unshift(-e);posts.push(n+e);
  for(const u of posts)for(const sd of [-1,1]){const hd=dk(u),pp=P(u,0,sd*DW/2);MAT=2;tube([pp[0],u<0||u>n?hd-.3:WLV-.7,pp[2]],[pp[0],hd+.82,pp[2]],.07,.06,'#4e3218',6,1)}
  for(let i=0;i+1<posts.length;i++){const u0=posts[i],u1=posts[i+1];if(u0<0||u1>n)continue;for(const sd of [-1,1]){const a=P(u0,WLV-.1,sd*(DW/2+.02)),c2=P(u1,dk(u1)-.25,sd*(DW/2+.02)),a2=P(u0,dk(u0)-.25,sd*(DW/2+.02)),c3=P(u1,WLV-.1,sd*(DW/2+.02));MAT=2;tube(a,c2,.03,.03,'#5a3a1a',4,0);tube(a2,c3,.03,.03,'#5a3a1a',4,0)}}}
 MAT=0;YO=YO0}
function boardObj(x,y){const YO0=YO;YO=0;const hd=.12,wt=(i,j)=>ok(i,j)&&tile[j][i]==1,hz=(isWT(x-1,y)?0:1)+(isWT(x+1,y)?0:1)>=(isWT(x,y-1)?0:1)+(isWT(x,y+1)?0:1);MAT=2;
 for(let k=0;k<5;k++){const o=.1+k*.2;if(hz)boxR(x+.5,hd-.04,y+o,1,.08,.17,0,['#8a5a2b','#7a4a22','#94632f','#83552a','#7f5126'][(x+y+k)%5]);else boxR(x+o,hd-.04,y+.5,.17,.08,1,0,['#8a5a2b','#7a4a22','#94632f','#83552a','#7f5126'][(x+y+k)%5])}
 for(const [i,j,ax] of [[-1,0,0],[1,0,0],[0,-1,1],[0,1,1]]){if(!wt(x+i,y+j))continue;const ex=x+.5+i*.47,ez=y+.5+j*.47;
  boxR(ex,hd+.55,ez,ax?1:.05,.05,ax?.05:1,0,'#6b4422');boxR(ex,hd+.3,ez,ax?1:.04,.04,ax?.04:1,0,'#6b4422');
  for(const s of [-1,1]){const px=ax?ex+s*.47:ex,pz=ax?ez:ez+s*.47;tube([px,WLV-.6,pz],[px,hd+.62,pz],.06,.05,'#4e3218',5,1)}}
 MAT=0;YO=YO0}
"""
OLD_DRAW = "MAT=2;for(const [x,y] of L.br){YO=hgt(x+.5,y+.5);boxR(x+.5,.09,y+.5,1,.18,1,0,(x+y)%2?'#8a5a2b':'#7a4a22');[[1,0],[-1,0],[0,1],[0,-1]].forEach(([dx,dy])=>{if(tile[y+dy]&&tile[y+dy][x+dx]==1){const ex=x+.5+dx*.46,ez=y+.5+dy*.46;boxR(ex,.62,ez,dx?.08:1,.08,dy?.08:1,0,'#5a3a1a');boxR(ex,.4,ez,dx?.1:.12,.5,dy?.1:.12,0,'#5a3a1a')}})}MAT=0;"
rep(OLD_DRAW, "if(L.bg)L.bg.forEach(bridgeObj);if(L.bw)L.bw.forEach(([x,y])=>boardObj(x,y));MAT=0;")
rep("function buildObjs(ch,key){", DRAW + "function buildObjs(ch,key){")

open(PATH, 'w', encoding='utf-8').write(h)
print('bridges patch applied')
