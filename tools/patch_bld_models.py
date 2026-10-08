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
TABLE = 'const BLDK=' + json.dumps(BLDK, separators=(',', ':')) + ';'

if 'const BLDK=' in h:  # re-run: just refresh the table
    h = re.sub(r'const BLDK=(window\.BLDK=)?\{[^;]*\};', lambda m: TABLE.replace('const BLDK=', 'const BLDK=' + (m.group(1) or '')), h, count=1)
    open(PATH, 'w', encoding='utf-8').write(h)
    print('BLDK table refreshed.')
    raise SystemExit


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- 2. assign model keys after the town layouts are final (just before mountains are placed)
ASSIGN = TABLE + r"""
const DECO=window.DECO=[];
{const GTK={tavern:'b_tavern',barracks:'b_barracks',smith:'b_smith',kitchen:'b_kitchen',chapel:'b_chapel'},GTH=['b_houseA','b_houseB','b_houseC','b_houseD'].filter(k=>!!BLDK[k]),
TOWNH={0:['b_cottageB','b_cottageC','b_cottageA'],1:['b_stiltA','b_stiltB','b_fishshack'],2:['b_rowA','b_rowB'],3:['b_dhhouse'],4:['b_boarded'],5:['b_hhcottage'],6:['b_mlhab'],7:['b_villa']},TOWNL={0:['b_church'],1:['b_shrine'],2:['b_exchange','b_clock'],3:['b_dhhall','b_dhspire','b_dhyard'],4:['b_manor','b_crypt'],5:['b_monastery','b_belltower'],6:['b_dome','b_antenna','b_gantry'],7:['b_colosseum','b_bath']},TOWNS={0:'b_wlstore'},has=k=>!!BLDK[k];let gi=0;const ti={};
const BH={b_tavern:5.4,b_bank:4.4,b_store:4.8,b_barracks:4.0,b_kitchen:4.2,b_chapel:6.5,b_smith:4.2,b_houseA:5,b_houseB:4.0,b_houseC:5,b_houseD:4.6,b_church:6.5,b_windmill:7.5,b_shrine:3.6,b_rowA:6,b_rowB:6.5,b_exchange:7,b_clock:11,b_dhhall:5,b_dhspire:12,b_dhyard:2.6,b_dhhouse:5.5,b_monastery:5.5,b_belltower:10,b_hhcottage:4.4,b_boarded:4.4,b_manor:7.5,b_crypt:4,b_dome:5.5,b_antenna:12,b_gantry:12,b_mlhab:2.4,b_villa:3.8,b_colosseum:8,b_bath:5.5,b_wlstore:4.8,b_cottageA:4.6,b_cottageB:4.6,b_cottageC:4.6,b_stiltA:5,b_stiltB:5,b_fishshack:4.4},
TIGHT={b_mlhab:1},fit=(o,k)=>{const e=BLDK[k];o.mk=k;const byH=(BH[k]||4.4)/Math.max(.2,e[2]),byF=(TIGHT[k]?Math.min:Math.max)(o.w/(2*e[0]),o.d/(2*e[1]));o.msc=Math.min(Math.max(byH,byF*1.05),byF*1.9)};
SB.forEach(o=>{if(inGT(o.cx,o.cz,1)){const k=o.k=='bank'?'b_bank':'b_store';if(has(k))fit(o,k)}});
HS.forEach(o=>{if(inGT(o.cx,o.cz,1)){const k=o.kind?GTK[o.kind]:GTH[gi++%Math.max(1,GTH.length)];if(k&&has(k))fit(o,k);return}
let bt=-1,bd=1e9;TW.forEach((t,i)=>{const dd=Math.hypot(o.cx-t.cx,o.cz-t.cy);if(dd<bd){bd=dd;bt=i}});const set=(TOWNH[bt]||[]).filter(has);if(set.length&&bd<40){ti[bt]=(ti[bt]||0)+1;fit(o,set[ti[bt]%set.length])}});
let dsd=91573;const drn=()=>(dsd=(dsd*16807)%2147483647)/2147483647;const deco=(k,cx,cy,n,r0,r1,Ht,fp,out)=>{if(!has(k))return;let placed=0;for(let t=0;t<Math.max(600,n*80)&&placed<n;t++){const a=drn()*6.283,rr=r0+drn()*(r1-r0),x=Math.round(cx+Math.cos(a)*rr),y=Math.round(cy+Math.sin(a)*rr);let okk=true;for(let j=y-1;j<=y+fp&&okk;j++)for(let i=x-1;i<=x+fp;i++){if(!ok(i,j)||tile[j][i]!=0||ob[j][i]||inGT(i,j,1)||inCastle(i,j,4)||(out&&inTown(i,j,4))){okk=false;break}}if(!okk)continue;solidRect(x,y,fp,fp);DECO.push([k,x+fp/2,y+fp/2,drn()*6.283,Ht/Math.max(.2,BLDK[k][2])]);placed++}};const T4=TW[4],T1=TW[1],T6=TW[6];deco('b_graves',T4.cx,T4.cy,4,6,22,1.6,2);deco('b_deadtree',T4.cx,T4.cy,6,8,30,4.5,1);deco('b_gallows',T4.cx,T4.cy,1,6,16,3.4,2);deco('b_totem',T1.cx,T1.cy,3,6,20,3.4,1);deco('b_capsule',T6.cx,T6.cy,1,14,26,1.6,2);deco('b_tent',CAMP+70,CAMP+70,8,20,60,2.2,2,1);deco('b_hbridge',TW[5].cx,TW[5].cy,1,8,30,1.6,2);const T7=TW[7];deco('b_forum',T7.cx,T7.cy,2,8,22,2.6,2);deco('b_aqueduct',T7.cx,T7.cy,2,10,30,2.4,2);deco('b_boulderL',192,192,40,25,185,2.2,2,1);deco('b_log',192,192,30,25,185,0.9,2,1);deco('b_stump',192,192,30,25,185,0.8,1,1);deco('b_moonrock',TW[6].cx,TW[6].cy,6,6,34,1.6,1);deco('b_rocksS',192,192,30,25,185,0.9,1,1);deco('b_mushroom',192,192,30,25,185,0.9,1,1);deco('b_reeds',TW[1].cx,TW[1].cy,12,4,36,1.5,1);deco('b_cactus',TW[7].cx,TW[7].cy,5,10,40,2.4,1);deco('b_snowrock',TW[5].cx,TW[5].cy,8,8,40,1.6,1);deco('b_boulderM',192,192,60,25,185,1.2,1,1);
const near=(o,i)=>Math.hypot(o.cx-TW[i].cx,o.cz-TW[i].cy);Object.entries(TOWNL).forEach(([i,ks])=>ks.forEach(k=>{if(!has(k))return;let b=null,bs=-1;HS.forEach(o=>{if(o.lm||inGT(o.cx,o.cz,1)||near(o,i)>20)return;const sc=o.w*o.d-near(o,i)*.05;if(sc>bs){bs=sc;b=o}});if(b){fit(b,k);b.lm=1}}));if(has('b_windmill')){let b=null,bd=-1;HS.forEach(o=>{const d=near(o,0);if(o.mk=='b_church'||inGT(o.cx,o.cz,1)||d>30)return;if(d>bd){bd=d;b=o}});if(b)fit(b,'b_windmill')}Object.entries(TOWNS).forEach(([i,k])=>{if(!has(k))return;SB.forEach(o=>{if(o.k=='shop'&&!inGT(o.cx,o.cz,1)&&near(o,i)<40)fit(o,k)})})}
"""
rep("for(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0",
    ASSIGN.strip('\n') + "\nfor(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0")

# ---- 3. chunk builder: skip the code-built house when a model stands there
rep("YO=0;for(const o of L.sb){const s=o.k=='shop';house(",
    "YO=0;for(const o of L.sb){if(o.mk)continue;const s=o.k=='shop';house(")
rep("L.w.forEach(([x,z])=>well(x,z));", "if(!BLDK.b_well)L.w.forEach(([x,z])=>well(x,z));")
rep("L.st.forEach(([x,z])=>stall(x,z));", "if(!BLDK.b_stall)L.st.forEach(([x,z])=>stall(x,z));")
rep("L.lp.forEach(([x,z])=>lamp(x,z));", "if(!BLDK.b_lamp)L.lp.forEach(([x,z])=>lamp(x,z));")
rep("PR.fount.forEach(([x,z])=>vis(x,z,40)&&fountain(x,z,now));", "if(!BLDK.b_fountain)PR.fount.forEach(([x,z])=>vis(x,z,40)&&fountain(x,z,now));")
rep("for(const h of L.hs){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(",
    "for(const h of L.hs){if(h.mk){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(h.cx,h.cz,h.ry,h.w,h.d);continue}if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(")

# ---- 4. draw them with the castle kit (lazy loaded, see-through when they block the camera)
rep("return L})();\nconst DYNXO=",
    "HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});if(BLDK.b_well)PR.wells.forEach(a=>L.push(['b_well',a[0],a[1],0,.8]));if(BLDK.b_stall)PR.stalls.forEach(a=>L.push(['b_stall',a[0],a[1],0,1.35]));if(BLDK.b_fountain)PR.fount.forEach(a=>L.push(['b_fountain',a[0],a[1],0,1.75]));if(BLDK.b_lamp)PR.lamps.forEach(a=>{let k='b_lamp';const nt=i=>Math.hypot(a[0]-TW[i].cx,a[1]-TW[i].cy)<40;if(nt(1)&&BLDK.b_swamplamp)k='b_swamplamp';else if(nt(6)&&BLDK.b_spacelamp)k='b_spacelamp';L.push([k,a[0],a[1],((a[0]*7+a[1]*3)|0)%4*1.5708,2.6/BLDK[k][2]])});if(BLDK.b_crates)SB.forEach(o=>{if(o.k!='shop'||!o.mk)return;const c=Math.cos(o.ry),sn=Math.sin(o.ry);L.push(['b_crates',o.nx+c*1.7,o.nz-sn*1.7,o.ry,.7])});DECO.forEach(d=>L.push(d));rocks.forEach(o=>{const k=o.tin?'b_tin':'b_copper';if(BLDK[k])L.push([k,o.x+.5,o.y+.5,((o.x*3+o.y)%6)*1.05,.75,30,o])});return L})();\nconst DYNXO=")
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
