#!/usr/bin/env python3
"""Gigachad Town: smaller castle courtyard, a market town outside the gate,
and the spawn point moved just outside the gate.

Run from the repo root:  python3 tools/patch_gigachad_town.py
Applies to the play.html that already has the world map v2 patch.
Every replacement asserts an exact single match, so it fails loudly on drift.
"""
import sys

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# 1. Smaller courtyard: the castle walls end 4 tiles further north.
rep("const CA={x:CASTLE.x,y:CASTLE.y,w:CASTLE.w,h:CASTLE.h,",
    "const CA={x:CASTLE.x,y:CASTLE.y,w:CASTLE.w,h:CASTLE.h-4,")

# 2. The castle bank booth moves out to the town bank.
rep("const bx=gx+5,by=Y0+h-7;solidRect(bx,by-1,3,1);for(let i=0;i<3;i++)put(bx+i,by,'bank');"
    "PR.npcs.push([bx+1.5,by-.5,0,bx+1,by]);PR.booths.push([bx+1.5,by+.5]);",
    "")

# 3. Gigachad Town layout (no random numbers, so the rest of the world stays put).
GT_JS = r"""
// ---- Gigachad Town: market town outside the castle gate ----
const GT={x0:CA.x-6,y0:CA.y+CA.h,x1:CA.x+CA.w+9,y1:CA.y+CA.h+32},inGT=(x,y,m)=>x>=GT.x0-m&&x<=GT.x1+m&&y>=GT.y0-m&&y<=GT.y1+m,GTT={n:'Gigachad Town'};PR.crops=[];
{const g=CA.gx,Y=GT.y0,inR=(x,y)=>inGT(x,y,0),out=a=>!inGT(a[0],a[1],1);
for(let i=HS.length-1;i>=0;i--)if(inGT(HS[i].cx,HS[i].cz,1))HS.splice(i,1);for(let i=SB.length-1;i>=0;i--)if(inGT(SB[i].cx,SB[i].cz,1))SB.splice(i,1);
['wells','stalls','lamps','ranges','forges','signs','fount'].forEach(k=>{PR[k]=PR[k].filter(out)});
for(let y=GT.y0;y<=GT.y1;y++)for(let x=GT.x0;x<=GT.x1;x++){if(ob[y][x])ob[y][x]=null;if(tile[y][x]==2)tile[y][x]=0}
const pave=(x0,y0,x1,y1)=>{for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)if(ok(x,y)&&tile[y][x]!=1)tile[y][x]=2};
pave(g-2,Y,g+4,Y+3);pave(g,Y,g+2,GT.y1);pave(GT.x0+1,Y+4,g+19,Y+4);pave(g-11,Y+5,g+12,Y+16);pave(GT.x0,Y+10,g-12,Y+11);pave(g+13,Y+10,GT.x1,Y+11);pave(GT.x0+1,Y+17,GT.x1-1,Y+17);
// link each town exit to the nearest road outside the town (breadth-first, straight-line tie breaks)
const link=(sx,sy)=>{const W2=W,prev=new Int32Array(W*H).fill(-2),q=[sy*W2+sx];prev[q[0]]=-1;let hit=-1;
for(let i=0;i<q.length&&i<40000;i++){const c=q[i],x=c%W2,y=(c/W2)|0;if(tile[y][x]==2&&!inGT(x,y,1)&&Math.hypot(x-sx,y-sy)>2){hit=c;break}
for(const[dx,dy]of[[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,ny=y+dy;if(!ok(nx,ny)||inGT(nx,ny,0))continue;const k=ny*W2+nx;if(prev[k]!=-2)continue;if(tile[ny][nx]==1)continue;if(ob[ny][nx]&&ob[ny][nx].k!='tree'&&ob[ny][nx].k!='rock')continue;prev[k]=c;q.push(k)}}
if(hit<0)return;for(let c=hit;c>=0;c=prev[c]){const x=c%W2,y=(c/W2)|0;const o=ob[y][x];if(o&&(o.k=='tree'||o.k=='rock')){o.gone=1;ob[y][x]=null}if(tile[y][x]!=1)tile[y][x]=2}};
link(g+1,GT.y1+1);link(GT.x0-1,Y+10);link(GT.x1+1,Y+10);
const mk=(x,y,w,d,ry)=>{const rot=Math.abs(Math.sin(ry))>.5,fw=rot?d:w,fh=rot?w:d,dvx=Math.round(Math.sin(ry)),dvz=Math.round(Math.cos(ry)),ccx=x+fw/2,ccz=y+fh/2,dist=dvx?fw/2:fh/2,fx=ccx+dvx*(dist+.5),fz=ccz+dvz*(dist+.5);
for(let j=y;j<y+fh;j++)for(let i=x;i<x+fw;i++)tile[j][i]=0;solidRect(x,y,fw,fh);const r={x,y,fw,fh,ry,w,d,cx:ccx,cz:ccz,nx:fx,nz:fz,nt:[Math.floor(fx),Math.floor(fz)]};pave(r.nt[0],r.nt[1],r.nt[0],r.nt[1]);return r};
const shopB=(k,x,y,ry)=>{const s=mk(x,y,3,2,ry);s.k=k;put(s.nt[0],s.nt[1],k);SB.push(s)};
const N=0,S=Math.PI,E=Math.PI/2,Wd=-Math.PI/2;
const hs=(x,y,w,d,ry,wc,rc,kind,sg,chim)=>{const r=mk(x,y,w,d,ry);r.wc=wc;r.rc=rc;r.door=0;r.chim=chim==null?1:chim;r.kind=kind||'';r.sg=sg||0;r.i=HS.length;HS.push(r);return r};
// north row, along the castle wall: barracks, bank, general store, tavern (2-4 tile gaps)
shopB('bank',g-8,Y+2,N);shopB('shop',g+6,Y+2,N);
hs(g-17,Y+1,5,3,N,'#cfc8b0','#5a5a6a','barracks','#c23a3a',0);
hs(g+12,Y+1,5,3,N,'#e0c9a0','#8a4a2a','tavern','#e8b800',1);
// west: blacksmith (forge in its yard), cottage, cook's kitchen across the west street
hs(g-14,Y+5,4,3,E,'#c8c0b0','#4a4a4a','smith','#8a8a92',1);put(g-13,Y+9,'forge');put(g-12,Y+9,'forge');PR.forges.push([g-12,Y+9.5]);
hs(GT.x0+1,Y+5,4,3,N,'#e6d5a4','#b5452f');pave(GT.x0+3,Y+8,GT.x0+3,Y+9);
hs(g-14,Y+13,4,3,S,'#f0e6d0','#a83a5a','kitchen','#ffffff',1);put(g-10,Y+14,'range');PR.ranges.push([g-9.5,Y+14.5]);
hs(GT.x0+1,Y+13,4,3,S,'#d9d2c0','#3a6f8f');
// east: chapel facing the square, cottages along the east street
hs(g+13,Y+5,5,4,Wd,'#ece8dc','#3a4a7a','chapel','#ffd23f',0);
hs(g+20,Y+5,4,3,N,'#e0c9a0','#5a4a9a');pave(g+22,Y+8,g+22,Y+9);hs(g+14,Y+13,4,3,S,'#e6d5a4','#3f8f5a');hs(g+20,Y+13,4,3,S,'#d8c8a0','#b5452f');
// south: houses on the south lane, then two pairs along the main road
hs(GT.x0+1,Y+18,4,3,S,'#e6d5a4','#a0602a');hs(GT.x0+8,Y+18,4,3,S,'#d8c8a0','#3f8f5a');hs(g+12,Y+18,4,3,S,'#e6d5a4','#a83a5a');hs(g+19,Y+18,4,3,S,'#cfc8b0','#8a4a2a');
hs(g-4,Y+21,4,3,E,'#e6d5a4','#8a4a2a');hs(g-4,Y+27,4,3,E,'#cfc8b0','#3a6f8f');hs(g+4,Y+21,4,3,Wd,'#e0c9a0','#b5452f');hs(g+4,Y+27,4,3,Wd,'#d9d2c0','#5a4a9a');
// farm plots (walkable crops) in the south-west and south-east corners
for(let y=Y+23;y<=GT.y1-1;y++)for(let x=GT.x0+1;x<=GT.x0+12;x++)if(!ob[y][x]&&tile[y][x]==0&&(x-GT.x0)%5!=0)PR.crops.push([x,y,(y-Y)%2]);
for(let y=Y+23;y<=GT.y1-1;y++)for(let x=GT.x1-12;x<=GT.x1-1;x++)if(!ob[y][x]&&tile[y][x]==0&&(x-GT.x1)%5!=0)PR.crops.push([x,y,(x+y)%2]);
// market square: a well, four stalls, lamps; town sign by the gate
solidRect(g+1,Y+10,1,1);PR.wells.push([g+1.5,Y+10.5]);
[[g-7,Y+7],[g-7,Y+14],[g+7,Y+7],[g+7,Y+14]].forEach(([x,y])=>{solidRect(x,y,2,1);PR.stalls.push([x+1,y+.5])});
[[g-11,Y+5],[g+12,Y+5],[g-11,Y+16],[g+12,Y+16],[g-1,Y+20],[g+3,Y+20],[g-1,Y+26],[g+3,Y+26],[g-1,Y+31],[g+3,Y+31],[GT.x0+2,Y+11],[GT.x1-2,Y+11]].forEach(([x,y])=>{if(ok(x,y)&&!ob[y][x])PR.lamps.push([x+.5,y+.5])});
solidRect(g-3,Y+3,1,1);PR.signs.push([g-2.5,Y+3.5,'Gigachad Town'])}
"""
rep("for(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0",
    GT_JS.strip('\n') + "\nfor(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0")

# 4. Keep the town flat, and keep trees, rocks and monsters out of it.
rep("const msk=sm((d-34)/12)*sm(Math.hypot(dcx,dcy)/12)*sm((dw-1)/6);",
    "const gdx=Math.max(GT.x0-x,0,x-GT.x1-1),gdy=Math.max(GT.y0-y,0,y-GT.y1-1),msk=sm((d-34)/12)*sm(Math.hypot(dcx,dcy)/12)*sm((dw-1)/6)*sm(Math.hypot(gdx,gdy)/8);")
rep("if(tile[y][x]||ob[y][x]||inTown(x,y,0)||inCastle(x,y,4))continue;",
    "if(tile[y][x]||ob[y][x]||inTown(x,y,0)||inCastle(x,y,4)||inGT(x,y,1))continue;")
rep("for(let i=0;i<16;i++){const[x,y]=near2(SPX,SPY,6,18);",
    "for(let i=0;i<16;i++){const[x,y]=near2(GT.x1+16,GT.y0+20,3,10);")
rep("while(g<200&&(solid(x,y)||inTown(x,y,6)||inCastle(x,y,8)));",
    "while(g<200&&(solid(x,y)||inTown(x,y,6)||inCastle(x,y,8)||inGT(x,y,6)));")
rep("const LAIR=near2(92,262,0,12);mob(LAIR[0],LAIR[1],IDX.lord);",
    "const LAIR=near2(92,262,0,12);mob(LAIR[0],LAIR[1],IDX.lord);for(let i=gobs.length-1;i>=0;i--)if(inGT(gobs[i].x,gobs[i].y,3))gobs.splice(i,1);")

# 5. Meme Ring in the square's south-east corner; spawn just outside the gate.
rep("xo(...fN(CA.gx+5,CA.y+CA.h+3),'ring'", "xo(...fN(CA.gx+9,CA.y+CA.h+15),'ring'")
rep("const SP={x:CA.gx+1,y:CA.y+CA.h-9};", "const SP={x:CA.gx+1,y:CA.y+CA.h+3};")

# 6. Drawing: crop plots, and extras for the special buildings.
rep("bo:[],xo:[],ca:0})", "bo:[],xo:[],cr:[],ca:0})")
rep("PR.booths.forEach(a=>obl(a[0],a[1]).bo.push(a));obl(CA.x+CA.w/2,CA.y+CA.h/2).ca=1;",
    "PR.booths.forEach(a=>obl(a[0],a[1]).bo.push(a));PR.crops.forEach(a=>obl(a[0],a[1]).cr.push(a));obl(CA.x+CA.w/2,CA.y+CA.h/2).ca=1;")
rep("for(const h of L.hs){if(h.i%2==0)fence(h.cx,h.cz,h.ry,h.w,h.d);house(h.cx,h.cz,h.ry,h.w,h.d,h.wc,h.rc,h.door,0,h.chim);",
    "for(const h of L.hs){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(h.cx,h.cz,h.ry,h.w,h.d);house(h.cx,h.cz,h.ry,h.w,h.d,h.wc,h.rc,h.door,h.sg||0,h.chim);gtExtra(h);")
rep("L.w.forEach(([x,z])=>well(x,z));",
    "L.w.forEach(([x,z])=>well(x,z));if(L.cr.length){MAT=2;for(const[x,y,t]of L.cr){boxR(x+.5,.05,y+.5,.92,.1,.92,0,'#6b4a2a');MAT=0;for(let k=0;k<3;k++)cone(x+.2+k*.3,.08,y+.5,.09,t?.42:.3,k,t?'#d9b45a':'#4a9a3a',4);MAT=2}MAT=0}")
rep("function flowers(x,z,s){",
    "function gtExtra(h){if(!h.kind)return;const P=(a,c)=>L2(h.cx,h.cz,h.ry,a,c);"
    "if(h.kind=='chapel'){const p=P(0,-h.d/2+.9);MAT=7;boxR(p[0],2.7,p[1],1.5,5.4,1.5,h.ry,h.wc);MAT=3;cone(p[0],5.4,p[1],1.2,2.3,h.ry+.785,h.rc,4);MAT=0;ball(p[0],4.5,p[1],.3,.34,.3,0,'#ffd23f',6);boxR(p[0],4.5,p[1],1.55,.08,.2,h.ry,'#3a2210')}"
    "else if(h.kind=='barracks'){[-1,1].forEach(s=>{const p=P(s*(h.w/2+.4),h.d/2+.6);MAT=2;tube([p[0],0,p[1]],[p[0],3.3,p[1]],.06,.05,'#5a3a1a',5,1);MAT=0;const f=P(s*(h.w/2+.4)+.45,h.d/2+.6);boxR(f[0],2.9,f[1],.9,.6,.05,h.ry,'#c23a3a');ball(f[0],2.9,f[1],.14,.14,.06,h.ry,'#ffd23f',6)});"
    "[-1,1].forEach(s=>{const p=P(s*1.2,h.d/2+1.8);MAT=2;tube([p[0],0,p[1]],[p[0],1.3,p[1]],.07,.07,'#8a5a2b',5,1);boxR(p[0],1.0,p[1],.7,.1,.1,h.ry,'#8a5a2b');MAT=0;ball(p[0],1.45,p[1],.17,.17,.17,0,'#d9b45a',6)})}"
    "else if(h.kind=='tavern'){const a=P(h.w/2+.5,h.d/2+.5),b=P(h.w/2+.5,h.d/2+1.2),c=P(-h.w/2-.4,h.d/2+.6);barrel(a[0],a[1]);barrel(b[0],b[1]);crate(c[0],c[1],h.ry)}"
    "else if(h.kind=='smith'){const a=P(-h.w/2-.4,h.d/2+.5);crate(a[0],a[1],h.ry)}"
    "else if(h.kind=='kitchen'){const a=P(-h.w/2-.4,h.d/2+.5),b=P(-h.w/2-.4,h.d/2+1.2);barrel(a[0],a[1]);crate(b[0],b[1],h.ry)}MAT=0}\n"
    "function flowers(x,z,s){")

# 6b. "You enter Gigachad Town" message, and the town is a safe zone.
rep("{let it=null;for(const t of TW)if(Math.hypot(P.x-t.cx,P.y-t.cy)<34)it=t;",
    "{let it=null;for(const t of TW)if(Math.hypot(P.x-t.cx,P.y-t.cy)<34)it=t;if(inGT(P.x,P.y,0))it=GTT;")
rep("function zoneAt(x,y){if(inCastle(x,y,14)||", "function zoneAt(x,y){if(inCastle(x,y,14)||inGT(x,y,4)||")

# 7. World map label.
rep("{n:'Castle Gigachad',x:CA.x+16,y:CA.y+11,a:1,c:'#dfe6ff'},",
    "{n:'Castle Gigachad',x:CA.x+16,y:CA.y+11,a:1,c:'#dfe6ff'},{n:'Gigachad Town',x:CA.gx+1,y:GT.y0+22,a:1},")

open(PATH, 'w', encoding='utf-8').write(h)
print('Gigachad Town patch applied.')
