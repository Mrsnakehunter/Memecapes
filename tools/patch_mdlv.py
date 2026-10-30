#!/usr/bin/env python3
"""Versioned player bodies: this build loads models/player2.json (and playerf2, player_cape2, playerf_cape2,
player_memecape2, playerf_memecape2) instead of the old files.

The model files are shared by the live game (play.html) and the preview (preview.html). A change that alters the
motions baked into the player bodies (the sword carry, tools/carry_bake.py) would break the live build if it
overwrote models/player.json, so a new build that needs new bodies uses new file names. MDLV maps a model key to
its current file; bump it here when the bodies change again, and delete the old files once the build has shipped.
Run late in the build (after patch_memecape.py and patch_armor.py):  python3 tools/patch_mdlv.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


rep("function needMdl(k){",
    "const MDLV={player:'player2',playerf:'playerf2',player_cape:'player_cape2',playerf_cape:'playerf_cape2',player_memecape:'player_memecape2',playerf_memecape:'playerf_memecape2'};"
    "const mpath=k=>'models/'+(MDLV[k]||k)+'.json';\nfunction needMdl(k){")
rep("fetch('models/'+k+'.json')", "fetch(mpath(k))")
rep("fetch('models/'+src+'.json')", "fetch(mpath(src))", 2)   # caped bodies + armour capes
rep("fetch('models/'+base+'_memecape.json')", "fetch(mpath(base+'_memecape'))")
open(PATH, 'w', encoding='utf-8').write(h)
print('model version patch applied')
