#!/usr/bin/env python3
"""Move the castle models out of the game file into models/*.json.

The castle kit (castle, gate, walls, towers and their sharper versions) was written into play.html
itself: 5.7 MB of the 7 MB file. Every update made returning players download all of it again.
Now each piece is its own file in models/, fetched at start like the other models, and the browser
keeps it between updates. Writes models/castle.json, cgate.json, cwall.json, cwallhd.json,
ctower.json and ctowerhd.json (only when they changed).
Run from the repo root as the last patch:  python3 tools/patch_split.py
"""
import json, os, re

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()
pat = re.compile(r"regLater\('([a-z0-9_]+)',(\{\"vb\".*?\})\);", re.S)
n = 0
out = []
pos = 0
for m in pat.finditer(h):
    k, body = m.group(1), m.group(2)
    json.loads(body)  # must be plain JSON
    f = f'models/{k}.json'
    if not os.path.exists(f) or open(f, encoding='utf-8').read() != body:
        open(f, 'w', encoding='utf-8').write(body)
    out.append(h[pos:m.start()])
    out.append(f"setTimeout(()=>needMdl('{k}'),0);")  # after the whole script has run
    pos = m.end(); n += 1
out.append(h[pos:])
assert n == 6, n
h = ''.join(out)
open(PATH, 'w', encoding='utf-8').write(h)
print('castle kit moved to models/:', n, 'files; game file now', len(h) // 1024, 'KB')
