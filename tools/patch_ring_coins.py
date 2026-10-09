#!/usr/bin/env python3
"""Meme Ring (replaces the mushroom fairy ring) + Meme Coin stack icons.

Run from the repo root after patch_gigachad_town.py and patch_bld_models.py:
    python3 tools/patch_ring_coins.py
Needs models/b_memering.json (the ring platform) and tools/art/coins_sheet.png
(17 icons, 128 px each: 1..10, 25, 100, 1K, 10K, 100K, 1M, 10M+).
"""
import base64

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- Meme Ring: draw the textured platform model instead of mushrooms
# (its spot on the square is chosen in patch_bld_models.py)
rep("ring:o=>{const x=o.x+.5,z=o.y+.5;for(let i=0;i<8;i++)",
    "ring:o=>{if(window.BLDK&&BLDK.b_memering)return;const x=o.x+.5,z=o.y+.5;for(let i=0;i<8;i++)")
rep("HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});",
    "HS.concat(SB).forEach(o=>{if(o.mk)L.push([o.mk,o.cx,o.cz,o.ry,o.msc])});if(BLDK.b_memering)XO.forEach(o=>{if(o.k=='ring')L.push(['b_memering',o.x+.5,o.y+.5,0,1.55])});")
rep("ring:'A ring of mushrooms humming with fairy magic.'",
    "ring:'A ring of meme medallions humming with Clout.'")
# BLDK is a block-scoped const; expose it for the ring check above
rep("const BLDK=", "const BLDK=window.BLDK=")

# ---- Meme Coin stack icons
png = base64.b64encode(open('tools/art/coins_sheet.png', 'rb').read()).decode()
COIN_JS = ("const COINSHEET='data:image/png;base64," + png + "',"
           "COINI=n=>{const T=[25,100,1e3,1e4,1e5,1e6,1e7];let i=n<=10?Math.max(1,n|0)-1:9;for(let k=0;k<T.length;k++)if(n>=T[k])i=10+k;"
           "return '<svg x=\"0\" y=\"0\" width=\"24\" height=\"24\" viewBox=\"'+(i*128)+' 0 128 128\"><image href=\"'+COINSHEET+'\" width=\"2176\" height=\"128\"/></svg>'};")
rep("const IC={coin:'<circle cx=\"12\" cy=\"12\" r=\"8\" fill=\"#e8b800\" stroke=\"#7a5a00\" stroke-width=\"2\"/>',",
    COIN_JS + "const IC={coin:COINI(1),")
# inventory slot
rep("(k?'<svg viewBox=\"0 0 24 24\">'+IC[k]+'</svg>'+(k=='coin'?",
    "(k?'<svg viewBox=\"0 0 24 24\"'+(k=='coin'?' style=\"width:40px;height:40px\"':'')+'>'+(k=='coin'?COINI(st.coins):IC[k])+'</svg>'+(k=='coin'?")
# bank grid
rep("'><svg viewBox=\"0 0 24 24\">'+IC[e.k]+'</svg><small>'",
    "'><svg viewBox=\"0 0 24 24\"'+(e.k=='coin'?' style=\"width:36px;height:36px;margin:-5px\"':'')+'>'+(e.k=='coin'?COINI(e.n):IC[e.k])+'</svg><small>'")

open(PATH, 'w', encoding='utf-8').write(h)
print('Meme Ring + coin icons patch applied.')
