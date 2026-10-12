#!/usr/bin/env python3
"""The MemeCape and the Quest cape are worn like every other cape: part of the character, moving with it.

Before, both were a stiff separate cape shape drawn behind the character, so the cape hung off one shoulder
whenever the character turned, walked or fought (Albert: "fix the cape and make it like the rest of them").
  - MemeCape: its own caped bodies, models/player_memecape.json and playerf_memecape.json (tools/mkmemecape.py):
    the medallion pattern on the cape and the gold crown on the head bone.
  - Quest cape: the caped body painted in the Quest cape's green, like the skill capes.
  - While a caped body is still loading, nothing is drawn in its place (no more stiff cape flashing up).
    The Classic (blocky) look keeps the old cape shapes.
Run from the repo root after patch_facing.py:  python3 tools/patch_memecape.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


rep("function capeBody(base,k,sk){if(CAPEM[k])return null; // the MemeCape and Quest cape keep their own hooded models\n",
    "function capeBody(base,k,sk){if(k=='memecape'){const mk='cb_'+base+'_memecape',mm=MDL[mk];if(mm&&mm.ok&&mm.tex)return mm;"
    "if(!CBP[mk]){CBP[mk]=1;fetch('models/'+base+'_memecape.json').then(r=>r.ok?r.json():Promise.reject()).then(d=>{try{regMdl(mk,d)}catch(e){}}).catch(()=>{})}return null}\n")
# no stiff fallback cape for the MemeCape / Quest cape on the 3D bodies while their caped body loads
rep("function qCape(x,z,yaw,kk){const k=kk!==undefined?kk:st.eq&&st.eq.cape;if(!k)return;",
    "function qCape(x,z,yaw,kk){const k=kk!==undefined?kk:st.eq&&st.eq.cape;if(!k)return;if(CAPEM[k]&&(kk!==undefined||st.body!==0))return;")
rep("<small>(hood and crown)</small>", "<small>(cape and crown)</small>")

open(PATH, 'w', encoding='utf-8').write(h)
print('memecape patch applied')
