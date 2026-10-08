#!/usr/bin/env python3
"""Item pictures: swap the drawn SVG item shapes for the painted icon sprite.

Reads icons/items.json (made with the icon sprite tool) and points IC[key] at a
cell of icons/items.webp. Items without a picture keep their old shape.
Run from the repo root after the other patches:
    python3 tools/patch_icons.py
"""
import json

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


meta = json.load(open('icons/items.json'))
c, s, w, hh = meta['cols'], meta['size'], meta['w'], meta['h']
js = ("{const IXS=" + json.dumps(meta['idx']) + ";for(const k in IXS){const i=IXS[k];"
      "IC[k]='<svg x=\"0\" y=\"0\" width=\"24\" height=\"24\" viewBox=\"'+((i%" + str(c) + ")*" + str(s) + ")+' '+(Math.floor(i/" + str(c) + ")*" + str(s) + ")+' " + str(s) + " " + str(s) + "\">"
      "<image href=\"icons/items.webp\" width=\"" + str(w) + "\" height=\"" + str(hh) + "\"/></svg>'}}")
anchor = "IC.tin=IC.ore.split('#b8642e').join('#a8b0b8');IN.tin='Tin ore';EX.tin='This needs refining.';SELL.tin=2;"
rep(anchor, anchor + js)
# a little bigger in the bag, bank and equipment slots
rep(".s svg{width:26px;height:26px}", ".s svg{width:31px;height:31px}")

open(PATH, 'w', encoding='utf-8').write(h)
print('item icons patch applied:', len(meta['idx']), 'pictures')
