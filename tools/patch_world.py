#!/usr/bin/env python3
"""The wider world: 384x384 -> 512x448. The original map is generated exactly as before and left untouched;
new sea and land are added east and south afterwards.

  Ember Coast   north-east, a volcano on its north tip, joined by a thick land bridge from the coast north of Chad Falls
  Wall St.      east, hugging the shore south of Pepe's Pond, joined by a short fat land bridge
  The Trenches  south, a peninsula below Rugpull Ridge
  Normie Island south-east, alone in the sea (portal only)
Roads (3 wide) join every new place to its nearest towns.
Run from the repo root after the other patches:  python3 tools/patch_world.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# the size can change after the original is generated
rep("const W=384,H=384,CX=192,CY=192;", "let W=384,H=384;const CX=192,CY=192,W0=384,H0=384;")
rep("const HW=W+1,HG=new Float32Array(HW*(H+1)),DWt=new Int16Array(W*H).fill(999),sm=t=>{",
    "let HW=W+1,HG=new Float32Array(HW*(H+1)),DWt=new Int16Array(W*H).fill(999);const sm=t=>{")

EXPAND = r"""
// ---- the wider world: new sea and land east and south of the untouched original
{const NW=512,NH=448;
for(let y=0;y<H0;y++)for(let x=W0;x<NW;x++){tile[y][x]=1;ob[y][x]=null}
for(let y=H0;y<NH;y++){tile[y]=[];ob[y]=[];for(let x=0;x<NW;x++){tile[y][x]=1;ob[y][x]=null}}
W=NW;H=NH;
const PRN=s=>{let v=(s*2654435761)>>>0;return()=>{v=(v*1664525+1013904223)>>>0;return v/4294967296}};
// land: only sea becomes land, and never within 3 tiles of the edge; original land, roads and objects are never touched
const land=(x,y)=>{x|=0;y|=0;if(x<3||y<3||x>=W-3||y>=H-3)return;if(tile[y][x]==1)tile[y][x]=0};
const disc=(cx,cy,r)=>{for(let y=Math.floor(cy-r);y<=cy+r;y++)for(let x=Math.floor(cx-r);x<=cx+r;x++)if((x-cx)**2+(y-cy)**2<=r*r)land(x,y)};
const blob=(cx,cy,rx,ry,wob,seed)=>{const r0=PRN(seed),ph=[r0()*6.28,r0()*6.28,r0()*6.28,r0()*6.28];const R=a=>1+wob*(.6*Math.sin(3*a+ph[0])+.45*Math.sin(5*a+ph[1])+.3*Math.sin(8*a+ph[2])+.2*Math.sin(13*a+ph[3]));
 for(let y=Math.floor(cy-ry*1.5);y<=cy+ry*1.5;y++)for(let x=Math.floor(cx-rx*1.5);x<=cx+rx*1.5;x++){const dx=(x+.5-cx)/rx,dy=(y+.5-cy)/ry,a=Math.atan2(dy,dx);if(Math.hypot(dx,dy)<=R(a))land(x,y)}};
const band=(p0,p1,width,wob,seed,steps)=>{const r0=PRN(seed),ph=r0()*6.28,ph2=r0()*6.28,dx=p1[0]-p0[0],dy=p1[1]-p0[1],L=Math.hypot(dx,dy),nx=-dy/L,ny=dx/L;
 for(let i=0;i<=steps;i++){const s=i/steps,off=wob*(Math.sin(s*2.2*Math.PI+ph)+.5*Math.sin(s*5.1*Math.PI+ph2))*Math.sin(s*Math.PI);disc(p0[0]+dx*s+nx*off,p0[1]+dy*s+ny*off,width/2*(1+.25*Math.sin(s*7+ph2)))}};
// roads: 3 wide, wandering; grass becomes road, water and objects are left alone
const roadAt=(x,y)=>{x|=0;y|=0;if(x<3||y<3||x>=W-3||y>=H-3)return;if(tile[y][x]==0&&!ob[y][x])tile[y][x]=2};
const road=(pts,wob,seed)=>{const r0=PRN(seed);for(let k=0;k+1<pts.length;k++){const a=pts[k],b=pts[k+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy),nx=-dy/L,ny=dx/L,n=Math.max(4,Math.ceil(L)),ph=r0()*6.28;
 for(let i=0;i<=n;i++){const s=i/n,off=wob*Math.sin(s*2.7*Math.PI+ph)*Math.sin(s*Math.PI),x=a[0]+dx*s+nx*off,y=a[1]+dy*s+ny*off;for(let j=-1;j<=1;j++)for(let i2=-1;i2<=1;i2++)roadAt(x+i2,y+j)}}};
// Ember Coast
band([340,78],[412,86],22,12,3,60);blob(452,84,50,62,.2,4);blob(468,52,22,18,.3,12);
// Wall St.
band([334,236],[372,230],26,10,7,40);blob(416,228,46,56,.22,8);
// the Trenches
band([92,376],[96,414],34,8,5,60);blob(96,418,40,24,.2,6);
// Normie Island
blob(462,392,18,13,.18,9);
// roads
const T=n=>{const t=TW.find(t=>t.n==n);return[t.cx,t.cy]};
road([T('Chad Falls'),[336,84],[372,80],[452,84],[466,60]],4,1);road([T('HODL Heights'),[290,60],[336,84]],4,2);
road([T("Pepe's Pond"),[300,200],[334,236],[380,232],[416,228]],4,3);road([T('Moon Landing'),[340,280],[334,236]],4,4);road([T('Chad Falls'),[330,160],[334,236]],4,5);
road([T('Rugpull Ridge'),[84,340],[92,376],[96,414]],4,6);road([T('Stonks City'),[140,330],[92,376]],4,7);
for(let y=200;y<=262;y+=9)for(let x=392;x<=440;x++)roadAt(x,y);for(let x=392;x<=442;x+=9)for(let y=194;y<=264;y++)roadAt(x,y);
// the volcano: a ring of rock around a crater
{const r0=PRN(77);for(let y=30;y<=76;y++)for(let x=444;x<=494;x++){const d=Math.hypot((x+.5-468)/22,(y+.5-52)/18);if(tile[y][x]==0&&!ob[y][x]&&d>.3&&d<.95&&r0()<.75)put(x,y,'mtn')}}
// trees on the new land
{const r0=PRN(99);for(let y=3;y<H-3;y++)for(let x=3;x<W-3;x++){if(x<W0&&y<H0)continue;if(tile[y][x]!=0||ob[y][x])continue;let nr=0;for(let j=-2;j<=2;j++)for(let i=-2;i<=2;i++){const tx=x+i,ty=y+j;if(tx>=0&&ty>=0&&tx<W&&ty<H&&tile[ty][tx]==2)nr++}
 if(nr)continue;const inWall=Math.hypot((x-416)/46,(y-228)/56)<1.05,inNormie=Math.hypot((x-462)/18,(y-392)/13)<1.1;if(inWall||inNormie)continue;if(r0()<.045){const o=put(x,y,'tree');o.i=trees.length;trees.push(o)}}}
// distance to water and heights for the whole map; the original heights are copied over unchanged
{const D2=new Int16Array(W*H).fill(999),q=[];for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(tile[y][x]==1){D2[y*W+x]=0;q.push(y*W+x)}
 for(let hq=0;hq<q.length;hq++){const c=q[hq],x=c%W,y=(c/W)|0,d=D2[c]+1;if(d>9)continue;for(const[dx,dy]of[[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=W||ny>=H)continue;const k=ny*W+nx;if(D2[k]>d){D2[k]=d;q.push(k)}}}
 const HW2=W+1,HG2=new Float32Array(HW2*(H+1));
 for(let y=0;y<=H;y++)for(let x=0;x<=W;x++){if(x<=W0&&y<=H0){HG2[y*HW2+x]=HG[y*HW+x];continue}
  const n=vnoise(x/38,y/38)*.6+vnoise(x/17+50,y/17+50)*.3+vnoise(x/7+90,y/7+90)*.1;let dw=999;for(let j=-1;j<=0;j++)for(let i=-1;i<=0;i++){const tx=x+i,ty=y+j;if(tx>=0&&ty>=0&&tx<W&&ty<H)dw=Math.min(dw,D2[ty*W+tx])}
  let hv=Math.max(0,((n-.05)/.39-.38)*7.4+(vnoise(x/2.6+7,y/2.6+7)-.25)*1.3)*sm((dw-1)/6);
  const vd=Math.hypot((x-468)/22,(y-52)/18);if(vd<1.1&&dw>1){const cone=sm((1.1-vd)/.7)*13,crater=sm((.32-vd)/.2)*8;hv=Math.max(hv,cone-crater)}
  HG2[y*HW2+x]=hv}
 HW=HW2;HG=HG2;DWt=D2}
}
"""
rep("const SP={x:CA.gx+1,y:CA.y+CA.h+2};", EXPAND + "const SP={x:CA.gx+1,y:CA.y+CA.h+2};")

# names on the map
rep("{n:'Farm',x:CA.x-8,y:CA.y+CA.h+10,c:'#9bff9b'}]);",
    "{n:'Farm',x:CA.x-8,y:CA.y+CA.h+10,c:'#9bff9b'},{n:'Ember Coast',x:452,y:92,a:1,c:'#ffb28a'},{n:'Wall St.',x:416,y:234,a:1,c:'#ffe68a'},{n:'The Trenches',x:96,y:420,a:1,c:'#d8c8a0'},{n:'Normie Island',x:462,y:394,c:'#fff0c0'}]);")

open(PATH, 'w', encoding='utf-8').write(h)
print('world patch applied: 512x448')
