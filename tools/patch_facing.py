#!/usr/bin/env python3
"""Every building faces its street, and every town has welcome signs where its roads come in.

Albert (photo of Gigachad Town): the general store and the house next to it faced the castle wall, the shopkeeper
and his crates stood behind them, and the town sign stood in a dead corner. Same problem elsewhere.

What was wrong:
  - Gigachad Town's lots were given compass directions the wrong way round (the "S" turn faces north here), so the
    north row faced the castle wall and the south row faced the fields.
  - In the meme towns every lot faced the town centre, even when a busy street ran along another side.
  - Two models have their door on a side (chapel: +x, houseD: -x), so even a correct lot turned them sideways.
  - Town signs were dropped at a random spot 9-14 tiles from the centre, at a random angle.

Now, after the world is laid out (nothing random is re-rolled, so the rest of the world stays put):
  - Each building looks at the four sides of its lot and turns its front to the side with the most road right next
    to it. Facing the town centre counts a little extra, facing away from it (onto no real street) counts against,
    and facing the castle wall is never allowed. A quarter turn is only made when the model still fits
    its lot (it may shrink up to 22%); otherwise it turns round, or stays. The shop/bank counter, the shopkeeper,
    and the crates by the door all move with the front, and the doorstep is paved onto the street.
  - Models whose door is not on their front (+z) side get their own turn (MOFF).
  - Signs: each town gets a sign at the edge of town on every real road in (a road that keeps going out into the
    country), at most 4, beside the road, facing travellers walking in. Gigachad Town gets its herald sign at its
    gate roads; roads into the castle courtyard get none.
Run from the repo root after the other world patches:  python3 tools/patch_facing.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


PASS = r"""
// ---- buildings face their street; town signs at the town entrances (tools/patch_facing.py)
const MOFF={b_chapel:-Math.PI/2,b_houseD:Math.PI/2};
{const isRoad=(x,y)=>ok(x,y)&&tile[y][x]==2,D4=[[0,1],[0,-1],[1,0],[-1,0]];
 const TC=TW.map(t=>[t.cx,t.cy]).concat([[(GT.x0+GT.x1)/2,(GT.y0+GT.y1)/2]]);
 const ctr=o=>{let b=TC[0],bd=1e9;for(const c of TC){const d=Math.hypot(o.cx-c[0],o.cz-c[1]);if(d<bd){bd=d;b=c}}return b};
 const score=(o,dx,dy)=>{let s=0;for(let k=1;k<=3;k++){const wgt=4-k;if(dy){const y=dy>0?o.y+o.fh-1+k:o.y-k;for(let i=o.x;i<o.x+o.fw;i++)if(isRoad(i,y))s+=wgt}else{const x=dx>0?o.x+o.fw-1+k:o.x-k;for(let j=o.y;j<o.y+o.fh;j++)if(isRoad(x,j))s+=wgt}}return s};
 const fitSc=(o,yw)=>{if(!o.mk)return Math.abs(Math.sin(yw-o.ry))>.5?0:1;const e=BLDK[o.mk];if(!e)return 1;const q=Math.abs(Math.sin(yw+(MOFF[o.mk]||0)))>.5,wx=(q?e[1]:e[0])*o.msc,wz=(q?e[0]:e[1])*o.msc;return Math.min(1,(o.fw+.25)/(2*wx),(o.fh+.25)/(2*wz))};
 for(const o of HS.concat(SB)){if(o.fw==null)continue;const c=ctr(o);if(Math.hypot(o.cx-c[0],o.cz-c[1])>45)continue;
  const cur=[Math.round(Math.sin(o.ry)),Math.round(Math.cos(o.ry))],tc=[c[0]-o.cx,c[1]-o.cz],tl=Math.hypot(tc[0],tc[1])||1;
  const C=D4.map(([dx,dy])=>{const r=score(o,dx,dy),dt=(dx*tc[0]+dy*tc[1])/tl,mx=Math.round(o.cx+dx*((dx?o.fw:o.fh)/2+3)),my=Math.round(o.cz+dy*((dx?o.fw:o.fh)/2+3));
   const s=r+(dt>.5?3:dt<-.5&&r<20?-6:0)-(inCastle(mx,my,1)?100:0);return{dx,dy,s,yw:Math.atan2(dx,dy)}}).sort((a,b)=>b.s-a.s);
  const now=C.find(k=>k.dx==cur[0]&&k.dy==cur[1]);
  for(const k of C){if(k===now||k.s<now.s+4||k.s<now.s*1.3)break;const f=fitSc(o,k.yw);if(f<.78)continue;
   const dist=k.dx?o.fw/2:o.fh/2,nx=o.cx+k.dx*(dist+.5),nz=o.cz+k.dy*(dist+.5),nt=[Math.floor(nx),Math.floor(nz)];
   const bo=ok(nt[0],nt[1])?ob[nt[1]][nt[0]]:null;if(bo&&bo.nm&&XO.includes(bo)){let mv=null;for(let r=1;r<=3&&!mv;r++)for(let dy=-r;dy<=r&&!mv;dy++)for(let dx=-r;dx<=r;dx++){const x=nt[0]+dx,y=nt[1]+dy;if(Math.max(Math.abs(dx),Math.abs(dy))!=r||!isRoad(x,y)||ob[y][x]||HS.concat(SB).some(q=>q.nt&&q.nt[0]==x&&q.nt[1]==y))continue;mv=[x,y];break}if(mv){ob[nt[1]][nt[0]]=null;bo.x=mv[0];bo.y=mv[1];ob[mv[1]][mv[0]]=bo}}
   if(!ok(nt[0],nt[1])||tile[nt[1]][nt[0]]==1||(ob[nt[1]][nt[0]]&&!(o.k&&ob[nt[1]][nt[0]].k==o.k)))continue;
   if(o.k){const p=o.nt,po=ob[p[1]][p[0]];if(po&&po.k==o.k)ob[p[1]][p[0]]=null;put(nt[0],nt[1],o.k)}
   o.ry=k.yw;if(o.mk)o.msc*=f;o.nx=nx;o.nz=nz;o.nt=nt;
   for(let s=0;s<4;s++){const x=nt[0]+k.dx*s,y=nt[1]+k.dy*s;if(!ok(x,y)||tile[y][x]==1)break;if(s&&tile[y][x]==2)break;if(s&&ob[y][x])break;tile[y][x]=2}
   break}}
 // ---- town signs: one at each real road into town
 const old=PR.signs.splice(0);old.forEach(a=>{const x=Math.floor(a[0]),y=Math.floor(a[1]);if(ob[y]&&ob[y][x]&&ob[y][x].k=='bld')ob[y][x]=null});
 const gtd=(x,y)=>Math.hypot(Math.max(GT.x0-x,0,x-GT.x1),Math.max(GT.y0-y,0,y-GT.y1)),owner=(x,y)=>{let b=-1,bd=gtd(x,y);TW.forEach((t,i)=>{const d=Math.hypot(x-t.cx,y-t.cy);if(d<bd){bd=d;b=i}});return b};
 const towns=TW.map((t,ti)=>{let R=10;HS.concat(SB).forEach(o=>{const d=Math.hypot(o.cx-t.cx,o.cz-t.cy);if(d<38&&owner(o.cx,o.cz)==ti)R=Math.max(R,d)});R=Math.min(R+3,36);return{n:t.n,cx:t.cx,cy:t.cy,inside:(x,y)=>Math.hypot(x-t.cx,y-t.cy)<R&&owner(x,y)==ti}});
 towns.unshift({n:'Gigachad Town',cx:(GT.x0+GT.x1)/2,cy:(GT.y0+GT.y1)/2,inside:(x,y)=>inGT(x,y,0)||inCastle(x,y,0)});
 for(const t of towns){const ent=[];
  for(let y=Math.floor(t.cy)-45;y<=t.cy+45;y++)for(let x=Math.floor(t.cx)-45;x<=t.cx+45;x++){if(!isRoad(x,y)||t.inside(x,y)||inCastle(x,y,1))continue;if(!D4.some(([dx,dy])=>t.inside(x+dx,y+dy)&&isRoad(x+dx,y+dy)))continue;ent.push([x,y])}
  const cl=[];for(const e of ent){const c=cl.find(c=>c.some(p=>Math.abs(p[0]-e[0])+Math.abs(p[1]-e[1])<=3));if(c)c.push(e);else cl.push([e])}
  const roads=[];for(const c of cl){const s=c[0],seen=new Set([s[1]*W+s[0]]),q=[s];let far=0;for(let i=0;i<q.length&&i<3000;i++){const[x,y]=q[i];far=Math.max(far,Math.hypot(x-t.cx,y-t.cy));for(const[dx,dy]of D4){const nx=x+dx,ny=y+dy,kk=ny*W+nx;if(seen.has(kk)||!isRoad(nx,ny)||t.inside(nx,ny))continue;seen.add(kk);q.push([nx,ny])}}
   const m=c[Math.floor(c.length/2)];roads.push({x:m[0],y:m[1],far,n:q.length,a:Math.atan2(m[1]-t.cy,m[0]-t.cx)})}
  roads.sort((a,b)=>b.far-a.far);const pick=[];
  for(const r of roads){if(r.n<25&&r.far<Math.hypot(r.x-t.cx,r.y-t.cy)+18)continue;if(pick.some(p=>Math.abs(Math.atan2(Math.sin(p.a-r.a),Math.cos(p.a-r.a)))<.7))continue;pick.push(r);if(pick.length>=4)break}
  for(const r of pick){const ox=r.x-t.cx,oy=r.y-t.cy,ol=Math.hypot(ox,oy)||1,ux=ox/ol,uy=oy/ol;let best=null,bs=-1e9;
   for(let dy=-3;dy<=3;dy++)for(let dx=-3;dx<=3;dx++){const x=r.x+dx,y=r.y+dy;if(!ok(x,y)||tile[y][x]!=0||ob[y][x]||t.inside(x,y)||inCastle(x,y,1))continue;
    let adj=0;for(const[ax,ay]of D4)if(isRoad(x+ax,y+ay))adj++;if(!adj)continue;let busy=false;for(const o of HS.concat(SB))if(o.nt&&Math.abs(o.nt[0]-x)<=1&&Math.abs(o.nt[1]-y)<=1)busy=true;if(busy)continue;
    const s=-Math.hypot(dx,dy)-(adj>1?2:0);if(s>bs){bs=s;best=[x,y]}}
   if(best&&!PR.signs.some(q=>q[2]!=t.n&&Math.hypot(q[0]-best[0]-.5,q[1]-best[1]-.5)<7)){solidRect(best[0],best[1],1,1);PR.signs.push([best[0]+.5,best[1]+.5,t.n,Math.atan2(ux,uy)])}}}
}
"""

# after the whole world is laid out (towns, roads between towns, bridges), before the models are listed
ANCHOR = "const CKIT=(()=>{"
rep(ANCHOR, PASS.strip('\n') + "\n" + ANCHOR)

# draw: model door offsets, and signs at their own angle
rep("HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});",
    "HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry+(MOFF[o.mk]||0),o.msc])});")
rep("L.push([k,a[0],a[1],((a[0]*5+a[1]*3)|0)%4*1.5708+.6,2.2/BLDK[k][2]])",
    "L.push([k,a[0],a[1],a[3]!=null?a[3]:((a[0]*5+a[1]*3)|0)%4*1.5708+.6,2.2/BLDK[k][2]])")

open(PATH, 'w', encoding='utf-8').write(h)
print('facing patch applied')
