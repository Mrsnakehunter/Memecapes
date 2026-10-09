#!/usr/bin/env python3
"""No flat pictures for memes: every monster and pet is a 3D model.

- Pepe, Bonk Hound, NPC Guard and Dogwifhat get 3D models (frogw, bonkb, knight, doge).
- The flat sprite fallback for monsters is off; while a model loads the blocky stand-in shows instead.
- The five dog pups use small 3D models (doge, fox, doge, bonkb, doge) instead of flat pictures.
Run from the repo root after the other patches:  python3 tools/patch_3d.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# models for the kinds that only had a picture (or nothing)
rep("'k:cult':'cult','k:doom':'doom','k:shiba':'fox'},MDLSC={",
    "'k:cult':'cult','k:doom':'doom','k:shiba':'fox','k:pepe':'frogw','k:bonk':'bonkb','k:guard':'knight','k:wif':'doge'},MSK={bonk:.62,wif:.9},MDLSC={")
# per-kind size on top of the model's own scale (a Bonk Hound is a small Bonk)
rep("qMdl(mm,x+ldx/ll*la,0,z+ldz/ll*la,gb.ry||0,MDLSC[mm.k]||1,d?'Walking':null,(gb.ph||0)/4);return}}",
    "qMdl(mm,x+ldx/ll*la,0,z+ldz/ll*la,gb.ry||0,(MDLSC[mm.k]||1)*(MSK[MT[gb.t].k]||1),d?'Walking':null,(gb.ph||0)/4);return}}")
# never draw a monster as a flat picture
rep("const zc=SZ[gb.t],mm_=mobMdl(gb.t),so=(st.orig||mm_)?null:SPR[zc.k];let hy=1.95;",
    "const zc=SZ[gb.t],mm_=mobMdl(gb.t),so=null;let hy=1.95;")
# pets: small 3D models for the pups
rep("const ps=st.orig?null:SPR[['','stick','shiba','wif','bonk','ghound'][st.pet]];\nif(ps){",
    "const ps=null,P3=st.orig?null:{1:['doge',.45],2:['fox',.45],3:['doge',.42],4:['bonkb',.34],5:['doge',.5]}[st.pet];"
    "if(P3){needMdl(P3[0]);const M3=MDL[P3[0]];if(M3&&M3.ok){qMdl(M3,PT.px+.5,0,PT.py+.5,PT.ry||0,P3[1],fp.v>.2?'Walking':null,(PT.ph||0)/4)}else dog(PT.px+.5,PT.py+.5,PT.ry,.5,st.pet==2?'#d9782e':'#e0a84a',st.pet==2?'#f6ead2':'#f3dfb0',fp.v>.2?Math.sin(PT.ph)*1.6:0,st.pet==2,0)}\nelse if(ps){")

open(PATH, 'w', encoding='utf-8').write(h)
print('3d-only patch applied')
