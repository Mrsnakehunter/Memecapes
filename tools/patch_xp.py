#!/usr/bin/env python3
"""XP curve: level 99 takes 20,000,000 XP (same shape of curve, scaled up).
Run from the repo root as part of the build:  python3 tools/patch_xp.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()
old = "const XT=[0];{let p=0;for(let l=1;l<99;l++){p+=Math.floor(l+300*Math.pow(2,l/7));XT.push(Math.floor(p/4))}}"
new = "const XT=[0];{let p=0;for(let l=1;l<99;l++){p+=Math.floor(l+300*Math.pow(2,l/7));XT.push(Math.floor(p/2.6068862))}}"
assert h.count(old) == 1, 'XP table anchor not found'
h = h.replace(old, new)
open(PATH, 'w', encoding='utf-8').write(h)
print('xp patch applied: level 99 = 20,000,000 xp')
