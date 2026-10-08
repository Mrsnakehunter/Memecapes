# New world layout v2: fixed towns, sea coast, northern mountains, Wildlands ditch, new river, road network.
import sys,re
src,dst=sys.argv[1],sys.argv[2]
h=open(src,encoding='utf-8').read()
def rep(old,new,cnt=1):
    global h
    n=h.count(old)
    assert n==cnt,(n,old[:100])
    h=h.replace(old,new)
# 1 towns + geography helpers
a=h.index("const TW=[{cx:CX,cy:CY,n:TN[0]}");b=h.index("const inCastle=",a)
h=h[:a]+"""const TW=[{cx:156,cy:182,n:TN[0]},{cx:246,cy:140,n:TN[1]},{cx:188,cy:258,n:TN[2]},{cx:72,cy:96,n:TN[3]},{cx:72,cy:300,n:TN[4]},{cx:226,cy:46,n:TN[5]},{cx:312,cy:318,n:TN[6]},{cx:314,cy:104,n:TN[7]}],CAMP=240,RVX=128,CASTLE={x:CX-50,y:CY-84,w:32,h:22};let curT=null;
const RIVP=[[0,150],[30,151],[66,140],[92,129],[120,126],[150,130],[185,137],[220,147],[258,155],[292,146],[326,152],[384,160]];
const RIV=y=>{let i=0;while(i<RIVP.length-2&&RIVP[i+1][0]<y)i++;const a=RIVP[i],b=RIVP[i+1],t=Math.max(0,Math.min(1,(y-a[0])/(b[0]-a[0]))),s=t*t*(3-2*t);return a[1]+(b[1]-a[1])*s+1.5*Math.sin(y/7.3)};
const COAST=y=>340+10*Math.sin(y*.045)+6*Math.sin(y*.13),SOUTH=x=>362+6*Math.sin(x*.07),SEA=(x,y)=>x>COAST(y)||(x>134&&y>SOUTH(x));
const MTNB=x=>62+10*Math.sin(x*.05)+6*Math.sin(x*.17),MTD=(x,y)=>MTNB(x)-y,SWAMP=(x,y)=>((x-246)/52)**2+((y-152)/38)**2<1,WILDX=y=>46+3*Math.sin(y*.1);
const INCAVE=(x,y)=>x>=342&&x<=370&&y>=12&&y<=40;
"""+h[b:]
# 2 water: sea + swamp pools only (no more random ponds everywhere)
rep("tile[y][x]=(e<3||(n[y][x]<.455&&!TW.some(t=>Math.hypot(x-t.cx,y-t.cy)<40)&&!inCastle(x,y,10)))?1:0",
    "tile[y][x]=(e<3||(SEA(x,y)&&!INCAVE(x,y))||(SWAMP(x,y)&&n[y][x]<.475&&!TW.some(t=>Math.hypot(x-t.cx,y-t.cy)<13)&&!inCastle(x,y,10)))?1:0")
# 3 river follows the new course from the mountains to the south sea + a mountain stream to Chad Falls + the Wildlands ditch
rep("for(let y=0;y<H;y++){const rx=Math.round(RVX+4*Math.sin(y/13)+2*Math.sin(y/5.3));for(let dx=-2;dx<=2;dx++){const x=rx+dx;if(x>3&&x<W-4&&!inCastle(x,y,6))tile[y][x]=1}}",
    "for(let y=0;y<H;y++){const rx=Math.round(RIV(y));if(y<MTNB(rx)-16)continue;for(let dx=-2;dx<=2;dx++){const x=rx+dx;if(x>3&&x<W-4&&!inCastle(x,y,6))tile[y][x]=1}}"
    "for(let s=0;s<=1;s+=.004){const x=Math.round(298+38*s+4*Math.sin(s*9)),y=Math.round(44+62*s);for(let dx=-1;dx<=1;dx++)if(ok(x+dx,y)&&!TW.some(t=>t===TW[7]&&Math.hypot(x-t.cx,y-t.cy)<12))tile[y][x+dx]=1}"
    "for(let y=64;y<H-4;y++){const x=Math.round(WILDX(y));if(TW.some(t=>Math.hypot(x-t.cx,y-t.cy)<38))continue;tile[y][x]=1;tile[y][x+1]=1}")
# 4 road network (instead of nearest-town chain)
rep("for(let i=1;i<TW.length;i++){let b=0,bd=1e9;for(let j=0;j<i;j++){const d=Math.hypot(TW[i].cx-TW[j].cx,TW[i].cy-TW[j].cy);if(d<bd){bd=d;b=j}}wind(TW[b].cx,TW[b].cy,TW[i].cx,TW[i].cy,1)}",
    "[[0,2],[2,4],[2,6],[1,7]].forEach(([a,b])=>wind(TW[a].cx,TW[a].cy,TW[b].cx,TW[b].cy,1));")
rep("wind(gx+1,Y0+h,CX,CY,1);wind(gx+1,Y0+h,RVX+12,Y0+h+8,1);wind(RVX+12,Y0+h+8,RVX-26,Y0+h+16,1);",
    "wind(gx+1,Y0+h,TW[0].cx,TW[0].cy,1);wind(gx+1,Y0+h,RVX+12,Y0+h+8,1);wind(RVX+12,Y0+h+8,RVX-26,Y0+h+16,1);wind(RVX-26,Y0+h+16,TW[3].cx,TW[3].cy,1);"
    "wind(X0+w+1,Y0+h-3,TW[1].cx,TW[1].cy,1);wind(X0+w+1,Y0+3,X0+w+6,Y0-14,0);wind(X0+w+6,Y0-14,TW[5].cx,TW[5].cy+20,0);wind(TW[3].cx,TW[3].cy-20,86,42,0);")
# 5 mountains: solid rock where you can't walk (paths, towns, castle and the cave stay open), placed before terrain relief
rep("// ---- terrain relief: rolling hills, flat towns/castle/shores ----",
    "for(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0&&!ob[y][x]&&!inTown(x,y,2)&&!inCastle(x,y,6)&&!INCAVE(x,y)&&Math.hypot(x-86,y-42)>5)put(x,y,'mtn')}\n// ---- terrain relief: rolling hills, flat towns/castle/shores ----")
rep("const msk=sm((d-34)/12)*sm(Math.hypot(dcx,dcy)/12)*sm((dw-1)/6);HG[y*HW+x]=Math.max(0,((n-.05)/.39-.38)*7.4+(vnoise(x/2.6+7,y/2.6+7)-.25)*1.3)*msk}}",
    "const msk=sm((d-34)/12)*sm(Math.hypot(dcx,dcy)/12)*sm((dw-1)/6);let mh=0;const md=MTNB(x)-y;if(md>-8&&!INCAVE(x,y)){let open=0;for(let j=-1;j<=0;j++)for(let i=-1;i<=0;i++){const tx=x+i,ty=y+j;if(tx>=0&&ty>=0&&tx<W&&ty<H&&(!ob[ty][tx]||ob[ty][tx].k!='mtn'))open++}mh=sm((md+8)/20)*(9+11*vnoise(x/11+3,y/11+3)+3*vnoise(x/3+9,y/3+9))*sm((d-30)/10)*(open?0.12:1)}HG[y*HW+x]=Math.max(Math.max(0,((n-.05)/.39-.38)*7.4+(vnoise(x/2.6+7,y/2.6+7)-.25)*1.3)*msk,mh)}}")
# 6 forests / rocks follow the new regions
rep("const f=(x<175&&y<215)||(x>260&&y<60);",
    "const f=(((x-86)/38)**2+((y-196)/58)**2<1)||(((x-84)/36)**2+((y-306)/44)**2<1)||(MTD(x,y)>-12&&MTD(x,y)<1)||SWAMP(x,y);")
rep("else if(y>235&&x<175&&R()<.07)",
    "else if(((MTD(x,y)>-14&&MTD(x,y)<1&&x<150)||Math.hypot(x-84,y-300)<26)&&R()<.07)")
# 7 Wildlands = west strip beyond the ditch
rep("return Math.hypot(x-SP.x,y-SP.y)>235?2:1}","return x<WILDX(y)?2:1}")
rep("if(Math.abs(P.x-RVX)<14)return TRK.length-2","if(Math.abs(P.x-RIV(P.y))<14)return TRK.length-2")
# 8 places and map labels
rep("const LAIR=near2(100,95,0,20)","const LAIR=near2(92,262,0,12)")
rep("{n:'Rugpull River',x:RVX,y:CY+40,c:'#8ac6ff'},{n:'Meme Camp',x:310,y:310,c:'#ff8a8a'},{n:'Whispering Forest',x:38,y:140,c:'#a8f0a8'},{n:'Copper Hills',x:120,y:350,c:'#f5c08a'},",
    "{n:'Rugpull River',x:RIV(222)-14,y:222,c:'#8ac6ff'},{n:'Meme Camp',x:262,y:292,c:'#ff8a8a'},{n:'Bear Market Woods',x:86,y:206,c:'#a8f0a8'},{n:'Copper Hills',x:104,y:76,c:'#f5c08a'},{n:'Wildlands',x:22,y:200,c:'#ff9a8a'},{n:'The Meme Sea',x:362,y:232,c:'#8ac6ff'},{n:'Copium Mountains',x:120,y:30,c:'#e0e0e8'},")
# 9 colours: mountains on the maps, snow and rock on high ground in 3D
mcol="b.k=='mtn'?(hgt(x+.5,y+.5)>13?'#e9edf0':hgt(x+.5,y+.5)>8?'#a39a8c':'#8a8173'):"
rep("b?(b.k=='tree'?'#1c5e2a'","b?("+mcol+"b.k=='tree'?'#1c5e2a'",2)
rep("if(o.k=='tree'){wx.fillStyle='#285f29';","if(o.k=='mtn'){const hv=hgt(x+.5,y+.5);wx.fillStyle=hv>13?'#e9edf0':hv>8?'#a39a8c':'#8a8173';wx.fillRect(ox+x*f,oy+y*f,f+.6,f+.6)}else if(o.k=='tree'){wx.fillStyle='#285f29';")
rep("if(rk>0)c=[c[0]+(.5-c[0])*rk,c[1]+(.47-c[1])*rk,c[2]+(.42-c[2])*rk];",
    "if(rk>0)c=[c[0]+(.5-c[0])*rk,c[1]+(.47-c[1])*rk,c[2]+(.42-c[2])*rk];if(hv>6){const mr=Math.min(1,(hv-6)/4)*.75;c=[c[0]+(.52-c[0])*mr,c[1]+(.49-c[1])*mr,c[2]+(.44-c[2])*mr]}if(hv>12.5){const sn=Math.min(1,(hv-12.5)/3);c=[c[0]+(.93-c[0])*sn,c[1]+(.95-c[1])*sn,c[2]+(.97-c[2])*sn]}")
open(dst,'w',encoding='utf-8').write(h);print('patched')
