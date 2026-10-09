#!/usr/bin/env python3
"""Swap the procedural houses for Meshy building models where a model exists.

Run from the repo root AFTER patch_gigachad_town.py:  python3 tools/patch_bld_models.py
Re-run any time new models/b_*.json files are added (it rebuilds the BLDK table).

* models/b_<key>.json are static building models made by tools/glb2mdl.py.
* Gigachad Town buildings map by role (tavern, bank, store, chapel, smith, barracks, kitchen, houses).
* Other towns map their houses to that town's house set (cycled), when models exist.
* A building with a model is drawn as a model (with the castle-style see-through) instead of
  the code-built house. Collision footprints are unchanged.
"""
import base64, glob, json, os, re
import numpy as np

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()

# ---- 1. table of available building models and their half extents
BLDK = {}
for f in sorted(glob.glob('models/b_*.json')):
    k = os.path.basename(f)[:-5]
    d = json.load(open(f))
    v = np.frombuffer(base64.b64decode(d['vb']), np.int16).reshape(-1, 3) / 1000
    BLDK[k] = [round(float(np.abs(v[:, 0]).max()), 3), round(float(np.abs(v[:, 2]).max()), 3), round(float(v[:, 1].max()), 3)]
print('building models:', ', '.join(BLDK) or '(none)')
BH = {'b_tavern': 5.4, 'b_bank': 4.4, 'b_store': 4.8, 'b_barracks': 4.0, 'b_kitchen': 4.2, 'b_chapel': 6.5, 'b_smith': 4.2, 'b_houseA': 5, 'b_houseB': 4.0, 'b_houseC': 5, 'b_houseD': 4.6, 'b_church': 6.5, 'b_windmill': 7.5, 'b_shrine': 3.6, 'b_rowA': 6, 'b_rowB': 6.5, 'b_exchange': 7, 'b_clock': 11, 'b_dhhall': 5, 'b_dhspire': 12, 'b_dhyard': 2.6, 'b_dhhouse': 5.5, 'b_monastery': 5.5, 'b_belltower': 10, 'b_hhcottage': 4.4, 'b_boarded': 4.4, 'b_manor': 7.5, 'b_crypt': 4, 'b_dome': 5.5, 'b_antenna': 12, 'b_gantry': 12, 'b_mlhab': 2.4, 'b_villa': 3.8, 'b_colosseum': 8, 'b_bath': 5.5, 'b_wlstore': 4.8, 'b_cottageA': 4.6, 'b_cottageB': 4.6, 'b_cottageC': 4.6, 'b_stiltA': 5, 'b_stiltB': 5, 'b_fishshack': 4.4, 'b_logcabin': 4.0, 'b_lodge': 4.6}
for i in range(8):
    BH['b_bk_t%d' % i] = 5.2
    if i: BH['b_sh_t%d' % i] = 4.8
# town building sets (houses cycle; landmarks, bank and shop get one lot each)
TOWNH = {0: ['b_cottageB', 'b_cottageC', 'b_cottageA'], 1: ['b_stiltA', 'b_stiltB', 'b_fishshack'], 2: ['b_rowA', 'b_rowB'], 3: ['b_dhhouse'], 4: ['b_boarded'], 5: ['b_hhcottage', 'b_logcabin', 'b_lodge'], 6: ['b_mlhab'], 7: ['b_villa']}
TOWNL = {0: ['b_church', 'b_windmill'], 1: ['b_shrine'], 2: ['b_exchange', 'b_clock'], 3: ['b_dhhall', 'b_dhspire', 'b_dhyard'], 4: ['b_manor', 'b_crypt'], 5: ['b_monastery', 'b_belltower'], 6: ['b_dome', 'b_antenna', 'b_gantry'], 7: ['b_colosseum', 'b_bath']}
TOWNS = {0: 'b_wlstore', **{i: 'b_sh_t%d' % i for i in range(1, 8)}}
TOWNB = {i: 'b_bk_t%d' % i for i in range(8)}
# house heights: every house in a town set is the same height so the street reads evenly
HOUSE_H = {k: 4.5 for ks in TOWNH.values() for k in ks}
HOUSE_H.update({'b_stiltA': 5, 'b_stiltB': 5, 'b_mlhab': 3.0, 'b_villa': 4.2, 'b_rowA': 5.5, 'b_rowB': 5.5, 'b_dhhouse': 5})
LOTS = {}
for i in range(8):
    hs = [k for k in TOWNH[i] if k in BLDK]
    if not hs: continue
    LOTS[i] = {'lm': [[k, BH[k]] for k in TOWNL[i] if k in BLDK], 'bank': TOWNB[i] if TOWNB[i] in BLDK else None,
               'shop': TOWNS[i] if TOWNS[i] in BLDK else None, 'hs': [[k, HOUSE_H.get(k, 4.5)] for k in hs], 'water': 1 if i == 1 else 0}
TABLE = 'const BLDK=' + json.dumps(BLDK, separators=(',', ':')) + ';const BH=' + json.dumps(BH, separators=(',', ':')) + ',LOTS=' + json.dumps(LOTS, separators=(',', ':')) + ';' 

if 'const BLDK=' in h:  # re-run: just refresh the table
    h = re.sub(r'const BLDK=(window\.BLDK=)?\{[^;]*\};const BH=\{[^;]*\};', lambda m: TABLE.replace('const BLDK=', 'const BLDK=' + (m.group(1) or '')), h, count=1)
    open(PATH, 'w', encoding='utf-8').write(h)
    print('BLDK table refreshed.')
    raise SystemExit


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- 1b. town generator: one lot per building, sized from its model (so the model fits its footprint)
# each town rolls its own dice, so a tweak to one town never reshuffles the others (or the countryside)
rep("TW.forEach(t=>{const cx=t.cx,cy=t.cy;", TABLE + "\nTW.forEach(t=>{const cx=t.cx,cy=t.cy;const TI=TW.indexOf(t),LT=LOTS[TI]||null,M=LT?2:1;sd=1013+TI*7919;")
rep("if(free(x,y,1,1)){put(x,y,'chest');PR.chest=[x+.5,y+.5]}}});\nconst CA={x:CASTLE.x", "if(free(x,y,1,1)){put(x,y,'chest');PR.chest=[x+.5,y+.5]}}});sd=424242;\nconst CA={x:CASTLE.x")
# roads never run through a building footprint (the door paths wander toward the town centre)
rep("const mark=(x,y)=>{if(ok(x,y)){if(tile[y][x]==1)BR.push([x,y]);tile[y][x]=2}};", "const mark=(x,y)=>{if(ok(x,y)&&!ob[y][x]){if(tile[y][x]==1)BR.push([x,y]);tile[y][x]=2}};")
rep("for(let j=y-1;j<y+fh+1&&g;j++)for(let i=x-1;i<x+fw+1;i++){if(!ok(i,j)||tile[j][i]==1||ob[j][i]){g=false;break}",
    "for(let j=y-M;j<y+fh+M&&g;j++)for(let i=x-M;i<x+fw+M;i++){if(!ok(i,j)||(tile[j][i]==1&&!(LT&&LT.water))||ob[j][i]||(LT&&i>=CASTLE.x-10&&i<=CASTLE.x+CASTLE.w+13&&j>=CASTLE.y+CASTLE.h-8&&j<=CASTLE.y+CASTLE.h+32)||(LT&&Math.abs(i-300)<=3&&Math.abs(j-296)<=3)){g=false;break}")
rep("fx=ccx+dvx*(dist+.5),fz=ccz+dvz*(dist+.5);\nsolidRect(x,y,fw,fh);", "fx=ccx+dvx*(dist+.5),fz=ccz+dvz*(dist+.5);if(tile[Math.floor(fz)][Math.floor(fx)]==1)continue;\nsolidRect(x,y,fw,fh);")
OLD_HOUSES = ("[['shop'],['bank']].forEach(([k])=>{const s=spot(3,2,10,16,true);if(s){s.k=k;put(s.nt[0],s.nt[1],k);SB.push(s);wind(s.nt[0],s.nt[1]+ (Math.cos(s.ry)>.5?1:0),cx,cy,0,true)}});\n"
    "const SZ=[[3,2],[3,2],[4,2],[3,3],[4,3],[3,2]];\n"
    "for(let i=0;i<30;i++){const [w,d]=SZ[Math.floor(R()*SZ.length)],h=spot(w,d,9+R()*4,33,false);if(!h)continue;h.rc=ROOFS[Math.floor(R()*ROOFS.length)];h.wc=WALLS[Math.floor(R()*WALLS.length)];h.door=(R()<.5?-1:1)*(w>3?.9:.6);h.chim=R()<.7;h.i=HS.length;HS.push(h);\n"
    "wind(h.nt[0],h.nt[1],cx,cy,0,true)}")
NEW_HOUSES = ("const mkLot=(k,Ht,minD,maxD,allowPath)=>{const e=BLDK[k];if(!e)return null;const s=Math.min(Ht/Math.max(.2,e[2]),11.6/(2*Math.max(e[0],e[1]))),w=Math.max(3,Math.ceil(2*e[0]*s+.3)),d=Math.max(2,Math.ceil(2*e[1]*s+.3)),o=spot(w,d,minD,maxD,allowPath);if(o){o.mk=k;o.msc=s}return o};"
    "const addH=(h)=>{h.rc=ROOFS[Math.floor(R()*ROOFS.length)];h.wc=WALLS[Math.floor(R()*WALLS.length)];h.door=(R()<.5?-1:1)*.9;h.chim=R()<.7;h.i=HS.length;HS.push(h);wind(h.nt[0],h.nt[1],cx,cy,0,true)};"
    "if(LT){[['bank',LT.bank],['shop',LT.shop]].forEach(([k,mk])=>{const H=k=='bank'?5.2:4.8,s=mk?(mkLot(mk,H,9,18,false)||mkLot(mk,H,8,24,true)):spot(3,2,10,16,true);if(s){s.k=k;put(s.nt[0],s.nt[1],k);SB.push(s);wind(s.nt[0],s.nt[1]+(Math.cos(s.ry)>.5?1:0),cx,cy,0,true)}});"
    "LT.lm.forEach(([k,Ht])=>{const h=mkLot(k,Ht,12,24,false)||mkLot(k,Ht,10,30,false);if(h){h.lm=1;addH(h);h.chim=false}});"
    "let hn=0;for(let i=0;i<120;i++){const [k,Ht]=LT.hs[hn%LT.hs.length],h=mkLot(k,Ht,10+R()*4,34,false);if(!h)continue;hn++;addH(h)}}"
    "else{" + OLD_HOUSES + "}")
rep(OLD_HOUSES, NEW_HOUSES)

# ---- 1c. Gigachad Town: re-lay the hand-placed town with lots sized from the models
GT_OLD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gt_old_segment.txt'), encoding='utf-8').read()
GT_NEW = "// ---- buildings on lots sized from their models (2-tile gaps), roads around them\nconst gset=(r,k,Ht)=>{const e=BLDK[k];if(e){r.mk=k;r.msc=Ht/Math.max(.2,e[2])}};const gsb=(k,x,y,w,d,ry,mdl,Ht)=>{const s=mk(x,y,w,d,ry);s.k=k;put(s.nt[0],s.nt[1],k);SB.push(s);gset(s,mdl,Ht)};const ghs=(x,y,w,d,ry,kind,mdl,Ht)=>{const r=hs(x,y,w,d,ry,'#cfc8b0','#5a5a6a',kind,0,0);gset(r,mdl,Ht)};\nghs(g-21,Y+3,10,5,S,'barracks','b_barracks',3.5);gsb('bank',g-9,Y+1,9,7,S,'b_bank',4.0);gsb('shop',g+4,Y+3,6,5,S,'b_store',4.8);ghs(g+12,Y+1,5,7,S,'tavern','b_tavern',5.4);ghs(g+19,Y+3,6,5,S,'','b_houseC',4.8);ghs(g-21,Y+11,10,10,E,'kitchen','b_kitchen',2.6);ghs(g+14,Y+10,7,6,Wd,'chapel','b_chapel',6.5);ghs(g+15,Y+19,4,5,Wd,'','b_houseA',4.8);ghs(g-19,Y+26,6,6,N,'smith','b_smith',4.4);ghs(g-11,Y+25,8,7,N,'','b_houseB',4.4);ghs(g+5,Y+25,6,7,N,'','b_houseD',4.6);ghs(g+13,Y+27,6,5,N,'','b_houseC',4.8);ghs(g+21,Y+27,4,5,N,'','b_houseA',4.8);\nput(g-9,Y+20,'forge');PR.forges.push([g-8.5,Y+20.5]);put(g-10,Y+12,'range');PR.ranges.push([g-9.5,Y+12.5]);solidRect(g+5,Y+13,1,1);PR.wells.push([g+5.5,Y+13.5]);[[g-7,Y+12],[g-7,Y+18],[g+7,Y+12],[g+7,Y+18]].forEach(([x,y])=>{solidRect(x,y,2,1);PR.stalls.push([x+1,y+.5])});[[g-1,Y+9],[g+3,Y+9],[g-1,Y+16],[g+3,Y+16],[g-1,Y+24],[g+3,Y+24],[g-1,Y+31],[g+3,Y+31],[g-11,Y+9],[g+12,Y+9],[g-11,Y+22],[g+12,Y+22]].forEach(([x,y])=>{if(ok(x,y)&&!ob[y][x])PR.lamps.push([x+.5,y+.5])});for(let y=Y+10;y<=Y+22;y++)for(let x=GT.x1-4;x<=GT.x1-1;x++)if(!ob[y][x]&&tile[y][x]==0&&(x-GT.x1)%5!=0)PR.crops.push([x,y,(x+y)%2]);solidRect(g+5,Y+1,1,1);PR.signs.push([g+5.5,Y+1.5,'Gigachad Town'])}"
rep(GT_OLD, GT_NEW)
rep("pave(g-2,Y,g+4,Y+3);pave(g,Y,g+2,GT.y1);pave(GT.x0+1,Y+4,g+19,Y+4);pave(g-11,Y+5,g+12,Y+16);pave(GT.x0,Y+10,g-12,Y+11);pave(g+13,Y+10,GT.x1,Y+11);pave(GT.x0+1,Y+17,GT.x1-1,Y+17);",
    "pave(g-2,Y,g+4,Y+2);pave(g,Y,g+2,GT.y1);pave(GT.x0,Y+8,GT.x1,Y+9);pave(g-11,Y+10,g+12,Y+22);pave(GT.x0,Y+23,GT.x1,Y+24);")
rep("link(g+1,GT.y1+1);link(GT.x0-1,Y+10);link(GT.x1+1,Y+10);", "link(g+1,GT.y1+1);link(GT.x0-1,Y+8);link(GT.x1+1,Y+8);")
# the spawn and the ring sit on the new square
rep("const SP={x:CA.gx+1,y:CA.y+CA.h+3};", "const SP={x:CA.gx+1,y:CA.y+CA.h+2};")

# night glow and light pool sit at the lantern, not at the post's tile
rep("PR.lamps.forEach(([x,z])=>{if(Math.abs(x-P.px)<32&&Math.abs(z-P.py)<32){YO=hgt(x,z);ball(x,2.05,z,.21,.26,.21,0,[2.4,2.1,1.2],6);ball(x,.02,z,1.3,.01,1.3,0,[.95,.85,.5],8)}});",
    "PR.lamps.forEach(([x,z,yw,lk])=>{if(Math.abs(x-P.px)<32&&Math.abs(z-P.py)<32){const LO={b_lamp:[-.54,1.6,0],b_swamplamp:[-.61,1.9,.03],b_spacelamp:[0,2.41,.04]},o=LO[lk]||[0,2.05,0],c=Math.cos(yw||0),sn=Math.sin(yw||0),lx=x+o[0]*c+o[2]*sn,lz=z-o[0]*sn+o[2]*c;YO=hgt(lx,lz);ball(lx,o[1],lz,.15,.19,.15,0,[2.4,2.1,1.2],6);ball(lx,.02,lz,1.3,.01,1.3,0,[.95,.85,.5],8)}});")

# plaza props keep a tile of clear road around them (range, forge, stalls, well)
rep("if(free(x,y,1,1)){put(x,y,'range');", "if(free(x-1,y-1,3,3)){put(x,y,'range');")
rep("if(free(x,y,2,1)){put(x,y,'forge');", "if(free(x-1,y-1,4,3)){put(x,y,'forge');")
rep("if(free(x,y,1,1)){solidRect(x,y,1,1);PR.wells.push([x+.5,y+.5]);wc++}", "if(free(x-1,y-1,3,3)){solidRect(x,y,1,1);PR.wells.push([x+.5,y+.5]);wc++}")
rep("if(free(x,y,2,1)&&free(x-1,y-1,4,3)===false||!free(x,y,2,1))continue;solidRect(x,y,2,1);PR.stalls.push([x+1,y+.5]);sc++}", "if(!free(x-2,y-2,6,5))continue;solidRect(x,y,2,1);PR.stalls.push([x+1,y+.5]);sc++}")

# the Meme Ring is 3 tiles wide: give it a clear 3x3 spot
rep("xo(...fN(CA.gx+9,CA.y+CA.h+15),'ring',{nm:'Castle Gigachad'",
    "const fN3=(x,y,cx,cy)=>{for(let q=0;q<=12;q++)for(let dy=-q;dy<=q;dy++)for(let dx=-q;dx<=q;dx++){if(Math.max(Math.abs(dx),Math.abs(dy))!=q)continue;const a=x+dx,b=y+dy;let g=true;for(let j=-2;j<=2&&g;j++)for(let i=-2;i<=2;i++)if(!ok(a+i,b+j)||solid(a+i,b+j)||tile[b+j][a+i]==1||(Math.abs(a+i-cx)<=2&&Math.abs(b+j-cy)<=2)){g=false;break}if(g)return[a,b]}return fN(x,y)};"
    "xo(...fN3(CA.gx+9,CA.y+CA.h+15,CA.gx+5,CA.y+CA.h+13),'ring',{nm:'Castle Gigachad'")
rep("TW.forEach((t,i)=>xo(...fN(t.cx+4,t.cy+5),'ring',{nm:t.n,code:rc[i]}))",
    "TW.forEach((t,i)=>xo(...fN3(t.cx+5,t.cy+6,t.cx,t.cy),'ring',{nm:t.n,code:rc[i]}))")

# ---- 2. assign model keys after the town layouts are final (just before mountains are placed)
ASSIGN = r"""
const DECO=window.DECO=[];
{const GTK={tavern:'b_tavern',barracks:'b_barracks',smith:'b_smith',kitchen:'b_kitchen',chapel:'b_chapel'},GTH=['b_houseA','b_houseB','b_houseC','b_houseD'].filter(k=>!!BLDK[k]),
TOWNH={0:['b_cottageB','b_cottageC','b_cottageA'],1:['b_stiltA','b_stiltB','b_fishshack'],2:['b_rowA','b_rowB'],3:['b_dhhouse'],4:['b_boarded'],5:['b_hhcottage','b_logcabin','b_lodge'],6:['b_mlhab'],7:['b_villa']},TOWNL={0:['b_church'],1:['b_shrine'],2:['b_exchange','b_clock'],3:['b_dhhall','b_dhspire','b_dhyard'],4:['b_manor','b_crypt'],5:['b_monastery','b_belltower'],6:['b_dome','b_antenna','b_gantry'],7:['b_colosseum','b_bath']},TOWNS={0:'b_wlstore',1:'b_sh_t1',2:'b_sh_t2',3:'b_sh_t3',4:'b_sh_t4',5:'b_sh_t5',6:'b_sh_t6',7:'b_sh_t7'},TOWNB={0:'b_bk_t0',1:'b_bk_t1',2:'b_bk_t2',3:'b_bk_t3',4:'b_bk_t4',5:'b_bk_t5',6:'b_bk_t6',7:'b_bk_t7'},has=k=>!!BLDK[k];let gi=0;const ti={};
const TIGHT={b_mlhab:1},fit=(o,k)=>{const e=BLDK[k];o.mk=k;const byH=(BH[k]||4.4)/Math.max(.2,e[2]),byF=(TIGHT[k]?Math.min:Math.max)(o.w/(2*e[0]),o.d/(2*e[1]));o.msc=Math.min(Math.max(byH,byF*1.05),byF*1.9)};
SB.forEach(o=>{if(inGT(o.cx,o.cz,1)&&!o.mk){const k=o.k=='bank'?'b_bank':'b_store';if(has(k))fit(o,k)}});
HS.forEach(o=>{if(inGT(o.cx,o.cz,1)){if(o.mk)return;const k=o.kind?GTK[o.kind]:GTH[gi++%Math.max(1,GTH.length)];if(k&&has(k))fit(o,k);return}
if(o.mk)return;let bt=-1,bd=1e9;TW.forEach((t,i)=>{const dd=Math.hypot(o.cx-t.cx,o.cz-t.cy);if(dd<bd){bd=dd;bt=i}});const set=(TOWNH[bt]||[]).filter(has);if(set.length&&bd<40){ti[bt]=(ti[bt]||0)+1;fit(o,set[ti[bt]%set.length])}});
let dsd=91573;const drn=()=>(dsd=(dsd*16807)%2147483647)/2147483647;const deco=(k,cx,cy,n,r0,r1,Ht,fp,out,gt)=>{if(!has(k))return;{const e=BLDK[k],sc=Ht/Math.max(.2,e[2]);fp=Math.max(fp,Math.ceil(2*Math.max(e[0],e[1])*sc-.2))}let placed=0;for(let t=0;t<Math.max(600,n*80)&&placed<n;t++){const a=drn()*6.283,rr=r0+drn()*(r1-r0),x=Math.round(cx+Math.cos(a)*rr),y=Math.round(cy+Math.sin(a)*rr);let okk=true;for(let j=y-1;j<=y+fp&&okk;j++)for(let i=x-1;i<=x+fp;i++){if(!ok(i,j)||tile[j][i]!=0||ob[j][i]||(!gt&&inGT(i,j,1))||inCastle(i,j,4)||(out&&inTown(i,j,4))||(Math.abs(i-300)<=3&&Math.abs(j-296)<=3)){okk=false;break}}if(!okk)continue;solidRect(x,y,fp,fp);DECO.push([k,x+fp/2,y+fp/2,drn()*6.283,Ht/Math.max(.2,BLDK[k][2])]);placed++}};const T4=TW[4],T1=TW[1],T6=TW[6];deco('b_graves',T4.cx,T4.cy,4,6,22,1.6,2);deco('b_deadtree',T4.cx,T4.cy,6,8,30,4.5,1);deco('b_gallows',T4.cx,T4.cy,1,6,16,3.4,2);deco('b_totem',T1.cx,T1.cy,3,6,20,3.4,1);deco('b_capsule',T6.cx,T6.cy,1,14,26,1.6,2);deco('b_tent',CAMP+70,CAMP+70,8,20,60,2.2,2,1);deco('b_hbridge',TW[5].cx,TW[5].cy,1,8,30,1.6,2);const T7=TW[7];deco('b_forum',T7.cx,T7.cy,2,8,22,2.6,2);deco('b_aqueduct',T7.cx,T7.cy,2,10,30,2.4,2);deco('b_boulderL',192,192,40,25,185,2.2,2,1);deco('b_log',192,192,30,25,185,0.9,2,1);deco('b_stump',192,192,30,25,185,0.8,1,1);deco('b_moonrock',TW[6].cx,TW[6].cy,6,6,34,1.6,1);deco('b_rocksS',192,192,30,25,185,0.9,1,1);deco('b_mushroom',192,192,30,25,185,0.9,1,1);deco('b_reeds',TW[1].cx,TW[1].cy,12,4,36,1.5,1);deco('b_cactus',TW[7].cx,TW[7].cy,5,10,40,2.4,1);deco('b_snowrock',TW[5].cx,TW[5].cy,8,8,40,1.6,1);deco('b_boulderM',192,192,60,25,185,1.2,1,1);deco('b_campfire',CAMP+70,CAMP+70,2,6,40,1.3,2,1);deco('b_roundtent',CAMP+70,CAMP+70,3,12,55,2.8,2,1);deco('b_sacks',CAMP+70,CAMP+70,3,8,50,1.0,1,1);deco('b_sacks',TW[0].cx,TW[0].cy,3,5,16,1.0,1);deco('b_plinth',TW[2].cx,TW[2].cy,2,5,16,1.5,1);deco('b_plinth',T7.cx,T7.cy,2,5,16,1.5,1);deco('b_scarecrow',134,131,1,3,6,2.2,1,0,1);deco('b_lander',T6.cx,T6.cy,1,10,24,3.0,2);deco('b_crater',T6.cx,T6.cy,4,8,36,0.7,2);deco('b_minecart',300,297,1,3,7,1.3,1);deco('b_timber',300,297,1,3,7,2.4,1);deco('b_minecart',104,76,2,3,16,1.3,1);deco('b_timber',104,76,1,3,14,2.4,1);deco('b_vspire',T4.cx,T4.cy,1,8,20,6,2);deco('b_dwgate',120,71,1,0,6,2.8,3);DECO.forEach(d=>{if(d[0]=='b_dwgate')d[3]=0});if(has('b_lily')){let n=0;for(let t=0;t<1500&&n<16;t++){const a=drn()*6.283,rr=2+drn()*34,x=Math.round(T1.cx+Math.cos(a)*rr),y=Math.round(T1.cy+Math.sin(a)*rr);if(!ok(x,y)||tile[y][x]!=1||ob[y][x])continue;if(DECO.some(q=>q[0]=='b_lily'&&Math.hypot(q[1]-x,q[2]-y)<2.5))continue;DECO.push(['b_lily',x+.5,y+.5,drn()*6.283,.7,40,null,-.1]);n++}}deco('b_haystack',134,131,2,4,9,1.7,2,0,1);deco('b_haystack',174,205,3,4,11,1.7,2);deco('b_scarecrow',174,205,1,5,10,2.2,1);deco('b_column',T7.cx,T7.cy,4,8,26,2.6,1);deco('b_brokenwall',T7.cx,T7.cy,2,10,28,1.6,2);deco('b_brokenwall',192,192,8,25,185,1.6,2,1);deco('b_column',192,192,4,25,185,2.4,1,1);
const near=(o,i)=>Math.hypot(o.cx-TW[i].cx,o.cz-TW[i].cy);Object.entries(TOWNL).forEach(([i,ks])=>ks.forEach(k=>{if(!has(k)||LOTS[i])return;let b=null,bs=-1;HS.forEach(o=>{if(o.lm||inGT(o.cx,o.cz,1)||near(o,i)>20)return;const sc=o.w*o.d-near(o,i)*.05;if(sc>bs){bs=sc;b=o}});if(b){fit(b,k);b.lm=1}}));if(has('b_windmill')&&!LOTS[0]){let b=null,bd=-1;HS.forEach(o=>{const d=near(o,0);if(o.mk=='b_church'||inGT(o.cx,o.cz,1)||d>30)return;if(d>bd){bd=d;b=o}});if(b)fit(b,'b_windmill')}Object.entries(TOWNS).forEach(([i,k])=>{if(!has(k))return;SB.forEach(o=>{if(o.k=='shop'&&!o.mk&&!inGT(o.cx,o.cz,1)&&near(o,i)<40)fit(o,k)})});Object.entries(TOWNB).forEach(([i,k])=>{if(!has(k))return;SB.forEach(o=>{if(o.k=='bank'&&!o.mk&&!inGT(o.cx,o.cz,1)&&near(o,i)<40)fit(o,k)})})}
"""
rep("for(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0",
    ASSIGN.strip('\n') + "\nfor(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0")

# ---- 3. chunk builder: skip the code-built house when a model stands there
rep("YO=0;for(const o of L.sb){const s=o.k=='shop';house(",
    "YO=0;for(const o of L.sb){if(o.mk)continue;const s=o.k=='shop';house(")
rep("L.w.forEach(([x,z])=>well(x,z));", "if(!BLDK.b_well)L.w.forEach(([x,z])=>well(x,z));")
rep("L.st.forEach(([x,z])=>stall(x,z));", "if(!BLDK.b_stall)L.st.forEach(([x,z])=>stall(x,z));")
rep("L.lp.forEach(([x,z])=>lamp(x,z));", "if(!BLDK.b_lamp)L.lp.forEach(([x,z])=>lamp(x,z));")
rep("L.sg.forEach(([x,z])=>signObj(x,z));", "if(!BLDK.b_signpost)L.sg.forEach(([x,z])=>signObj(x,z));")
rep("cave:o=>{const x=o.x+.5,z=o.y+.5;boxR(x-.7", "cave:o=>{if(BLDK.b_cavemouth)return;const x=o.x+.5,z=o.y+.5;boxR(x-.7")
rep("YO=hgt(c[1],c[2]);qMdl(m,c[1],0,c[2]", "YO=c[7]!=null?c[7]:hgt(c[1],c[2]);qMdl(m,c[1],0,c[2]")
rep("PR.ranges.forEach(([x,z])=>vis(x,z,40)&&rangeObj(x,z,now));PR.forges.forEach(([x,z])=>vis(x,z,40)&&forgeObj(x,z,now));", "if(!BLDK.b_range)PR.ranges.forEach(([x,z])=>vis(x,z,40)&&rangeObj(x,z,now));if(!BLDK.b_forge)PR.forges.forEach(([x,z])=>vis(x,z,40)&&forgeObj(x,z,now));")
rep("PR.fount.forEach(([x,z])=>vis(x,z,40)&&fountain(x,z,now));", "if(!BLDK.b_fountain)PR.fount.forEach(([x,z])=>vis(x,z,40)&&fountain(x,z,now));")
rep("for(const h of L.hs){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(",
    "for(const h of L.hs){if(h.mk){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(h.cx,h.cz,h.ry,h.w,h.d);continue}if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(")

# ---- 4. draw them with the castle kit (lazy loaded, see-through when they block the camera)
rep("return L})();\nconst DYNXO=",
    "const lampYaw=a=>{const x0=Math.floor(a[0]),y0=Math.floor(a[1]);let pd=99,py=null;PR.lamps.forEach(b=>{if(b===a)return;const dx=b[0]-a[0],dy=b[1]-a[1],ad=Math.abs(dx),ady=Math.abs(dy);let d=99,yw=0;if(ady<=1&&ad>=2&&ad<=6){d=ad;yw=dx>0?Math.PI:0}else if(ad<=1&&ady>=2&&ady<=6){d=ady;yw=dy>0?Math.PI/2:-Math.PI/2}if(d<pd){pd=d;py=yw}});if(py!==null)return py;let best=0,bs=-1;for(const [dx,dy,yw] of [[1,0,Math.PI],[-1,0,0],[0,-1,-Math.PI/2],[0,1,Math.PI/2]]){let n=0;for(let s=1;s<=3;s++){const x=x0+dx*s,y=y0+dy*s;if(ok(x,y)&&tile[y][x]==2&&!ob[y][x])n++;else break}if(n>bs){bs=n;best=yw}}return best};"
    "HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});if(BLDK.b_well)PR.wells.forEach(a=>L.push(['b_well',a[0],a[1],0,.8]));if(BLDK.b_stall)PR.stalls.forEach(a=>L.push(['b_stall',a[0],a[1],0,1.35]));if(BLDK.b_fountain)PR.fount.forEach(a=>L.push(['b_fountain',a[0],a[1],0,1.75]));if(BLDK.b_lamp)PR.lamps.forEach(a=>{let k='b_lamp';const nt=i=>Math.hypot(a[0]-TW[i].cx,a[1]-TW[i].cy)<40;if(nt(1)&&BLDK.b_swamplamp)k='b_swamplamp';else if(nt(6)&&BLDK.b_spacelamp)k='b_spacelamp';const yw=lampYaw(a);a[2]=yw;a[3]=k;L.push([k,a[0],a[1],yw,2.6/BLDK[k][2]])});if(BLDK.b_crates)SB.forEach(o=>{if(o.k!='shop'||!o.mk)return;const c=Math.cos(o.ry),sn=Math.sin(o.ry);L.push(['b_crates',o.nx+c*1.7,o.nz-sn*1.7,o.ry,.7])});if(BLDK.b_forge)PR.forges.forEach(a=>L.push(['b_forge',a[0],a[1],0,2.1/(2*BLDK.b_forge[0])]));if(BLDK.b_range)PR.ranges.forEach(a=>L.push(['b_range',a[0],a[1],0,1.1/(2*BLDK.b_range[0])]));if(BLDK.b_cavemouth)XO.forEach(o=>{if(o.k=='cave')L.push(['b_cavemouth',o.x+.5,o.y+.3,0,2])});if(BLDK.b_signpost)PR.signs.forEach(a=>{const k=a[2]=='Gigachad Town'&&BLDK.b_herald?'b_herald':'b_signpost';L.push([k,a[0],a[1],((a[0]*5+a[1]*3)|0)%4*1.5708+.6,2.2/BLDK[k][2]])});if(BLDK.b_dock){const dk=[];fish.forEach(f=>{if(f.gone||dk.some(q=>Math.hypot(q[0]-f.x,q[1]-f.y)<9))return;for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const sx=f.x-dx,sy=f.y-dy;if(ok(sx,sy)&&tile[sy][sx]==0&&!ob[sy][sx]){dk.push([f.x,f.y]);L.push(['b_dock',sx+.5+dx*.55,sy+.5+dy*.55,Math.atan2(-dy,dx),.9]);break}}})}DECO.forEach(d=>L.push(d));rocks.forEach(o=>{const k=o.tin?'b_tin':'b_copper';if(BLDK[k])L.push([k,o.x+.5,o.y+.5,((o.x*3+o.y)%6)*1.05,.75,30,o])});return L})();\nconst DYNXO=")
rep("{const HX={cwall:[.95,.2],ctower:[.41,.41],cgate:[.95,.25],castle:[.95,.84]},",
    "{const HX=Object.assign({cwall:[.95,.2],ctower:[.41,.41],cgate:[.95,.25],castle:[.95,.84]},BLDK),")
rep("for(const c of CKIT){let m=MDL[c[0]],sm=null;",
    "for(const c of CKIT){if(c[6]&&c[6].dep)continue;if(!MDL[c[0]]&&BLDK[c[0]]){if(!vis(c[1],c[2],c[5]||60))continue;needMdl(c[0])}let m=MDL[c[0]],sm=null;")
rep("for(const o of L.r){const dep=o.dep,", "for(const o of L.r){if(!o.dep&&BLDK[o.tin?'b_tin':'b_copper'])continue;const dep=o.dep,")

# flat models (the Meme Ring) never go see-through
rep("if(m&&m.ok&&vis(c[1],c[2],55)){let gh=false;if(started&&st.xr!==0){",
    "if(m&&m.ok&&vis(c[1],c[2],c[5]||55)){let gh=false;if(started&&st.xr!==0&&!(HX[c[0]][2]!=null&&HX[c[0]][2]*c[4]<1.3)){")

open(PATH, 'w', encoding='utf-8').write(h)
print('Building-model patch applied.')
