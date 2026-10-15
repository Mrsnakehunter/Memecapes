#!/usr/bin/env python3
"""Security hardening for the game page.
- esc() now also escapes quotes, so a name or text can never break out of an HTML attribute.
- Chat colours from the server must be a plain #colour, so nothing else can be slipped into the style attribute.
Run from the repo root after patch_lookalike.py:  python3 tools/patch_security.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


rep("const CTI=$('cti'),esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');",
    "const CTI=$('cti'),esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;');")
rep("function say(t,c){chat.push('<div'+(c=='#1a1aa0'?' class=\"pl\"':'')+' style=\"color:'+(c||'#000')+'\">'+t+'</div>');",
    "function say(t,c){c=/^#[0-9a-fA-F]{3,8}$/.test(c||'')?c:'#000';chat.push('<div'+(c=='#1a1aa0'?' class=\"pl\"':'')+' style=\"color:'+c+'\">'+t+'</div>');")
open(PATH, 'w', encoding='utf-8').write(h)
print('security patch applied')
