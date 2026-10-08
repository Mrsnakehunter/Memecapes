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
{const GTK={tavern:'b_tavern',barracks:'b_barracks',smith:'b_smith',kitchen:'b_kitchen',chapel:'b_chapel'},GTH=['b_houseA','b_houseB','b_houseC','b_houseD'].filter(k=>!!BLDK[k]),
TOWNH={0:['b_cottageB','b_cottageC','b_cottageA'],1:['b_stiltA','b_stiltB','b_fishshack'],2:['b_rowA','b_rowB']},TOWNL={0:['b_church'],1:['b_shrine'],2:['b_exchange','b_clock']},TOWNS={0:'b_wlstore'},has=k=>!!BLDK[k];let gi=0;const ti={};
const BH={b_tavern:5.4,b_bank:4.4,b_store:4.8,b_barracks:4.0,b_kitchen:4.2,b_chapel:6.5,b_smith:4.2,b_houseA:5,b_houseB:4.0,b_houseC:5,b_houseD:4.6,b_church:6.5,b_windmill:7.5,b_shrine:3.6,b_rowA:6,b_rowB:6.5,b_exchange:7,b_clock:11,b_wlstore:4.8,b_cottageA:4.6,b_cottageB:4.6,b_cottageC:4.6,b_stiltA:5,b_stiltB:5,b_fishshack:4.4},
fit=(o,k)=>{const e=BLDK[k];o.mk=k;const byH=(BH[k]||4.4)/Math.max(.2,e[2]),byF=Math.max(o.w/(2*e[0]),o.d/(2*e[1]));o.msc=Math.min(Math.max(byH,byF*1.05),byF*1.9)};
SB.forEach(o=>{if(inGT(o.cx,o.cz,1)){const k=o.k=='bank'?'b_bank':'b_store';if(has(k))fit(o,k)}});
HS.forEach(o=>{if(inGT(o.cx,o.cz,1)){const k=o.kind?GTK[o.kind]:GTH[gi++%Math.max(1,GTH.length)];if(k&&has(k))fit(o,k);return}
let bt=-1,bd=1e9;TW.forEach((t,i)=>{const dd=Math.hypot(o.cx-t.cx,o.cz-t.cy);if(dd<bd){bd=dd;bt=i}});const set=(TOWNH[bt]||[]).filter(has);if(set.length&&bd<40){ti[bt]=(ti[bt]||0)+1;fit(o,set[ti[bt]%set.length])}});
const near=(o,i)=>Math.hypot(o.cx-TW[i].cx,o.cz-TW[i].cy);Object.entries(TOWNL).forEach(([i,ks])=>ks.forEach(k=>{if(!has(k))return;let b=null,bs=-1;HS.forEach(o=>{if(o.lm||inGT(o.cx,o.cz,1)||near(o,i)>20)return;const sc=o.w*o.d-near(o,i)*.05;if(sc>bs){bs=sc;b=o}});if(b){fit(b,k);b.lm=1}}));if(has('b_windmill')){let b=null,bd=-1;HS.forEach(o=>{const d=near(o,0);if(o.mk=='b_church'||inGT(o.cx,o.cz,1)||d>30)return;if(d>bd){bd=d;b=o}});if(b)fit(b,'b_windmill')}Object.entries(TOWNS).forEach(([i,k])=>{if(!has(k))return;SB.forEach(o=>{if(o.k=='shop'&&!inGT(o.cx,o.cz,1)&&near(o,i)<40)fit(o,k)})})}
"""
rep("for(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0",
    ASSIGN.strip('\n') + "\nfor(let y=4;y<H-4;y++)for(let x=4;x<W-4;x++){if(MTD(x,y)>1&&tile[y][x]==0")

# ---- 3. chunk builder: skip the code-built house when a model stands there
rep("YO=0;for(const o of L.sb){const s=o.k=='shop';house(",
    "YO=0;for(const o of L.sb){if(o.mk)continue;const s=o.k=='shop';house(")
rep("L.w.forEach(([x,z])=>well(x,z));", "if(!BLDK.b_well)L.w.forEach(([x,z])=>well(x,z));")
rep("L.st.forEach(([x,z])=>stall(x,z));", "if(!BLDK.b_stall)L.st.forEach(([x,z])=>stall(x,z));")
rep("for(const h of L.hs){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(",
    "for(const h of L.hs){if(h.mk){if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(h.cx,h.cz,h.ry,h.w,h.d);continue}if(h.i%2==0&&!h.kind&&!inGT(h.cx,h.cz,0))fence(")

# ---- 4. draw them with the castle kit (lazy loaded, see-through when they block the camera)
rep("return L})();\nconst DYNXO=",
    "HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});if(BLDK.b_well)PR.wells.forEach(a=>L.push(['b_well',a[0],a[1],0,.8]));if(BLDK.b_stall)PR.stalls.forEach(a=>L.push(['b_stall',a[0],a[1],0,1.35]));return L})();\nconst DYNXO=")
rep("{const HX={cwall:[.95,.2],ctower:[.41,.41],cgate:[.95,.25],castle:[.95,.84]},",
    "{const HX=Object.assign({cwall:[.95,.2],ctower:[.41,.41],cgate:[.95,.25],castle:[.95,.84]},BLDK),")
rep("for(const c of CKIT){let m=MDL[c[0]],sm=null;",
    "for(const c of CKIT){if(!MDL[c[0]]&&BLDK[c[0]]){if(!vis(c[1],c[2],60))continue;needMdl(c[0])}let m=MDL[c[0]],sm=null;")

# flat models (the Meme Ring) never go see-through
rep("if(m&&m.ok&&vis(c[1],c[2],55)){let gh=false;if(started&&st.xr!==0){",
    "if(m&&m.ok&&vis(c[1],c[2],55)){let gh=false;if(started&&st.xr!==0&&!(HX[c[0]][2]!=null&&HX[c[0]][2]*c[4]<1)){")

open(PATH, 'w', encoding='utf-8').write(h)
print('Building-model patch applied.')
