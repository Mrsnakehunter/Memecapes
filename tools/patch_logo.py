#!/usr/bin/env python3
"""In-game logo button (next to the zoom +/-): use the MemeCapes cape-with-faces medallion (tools/art/logo.png).
Run from the repo root:  python3 tools/patch_logo.py
"""
import base64, re
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()
logo = 'data:image/png;base64,' + base64.b64encode(open('tools/art/logo.png', 'rb').read()).decode()
h, n = re.subn(r'"logo": "data:image/png;base64,[A-Za-z0-9+/=]+"', '"logo": "' + logo + '"', h)
assert n == 1, n
open(PATH, 'w', encoding='utf-8').write(h)
print('logo patch applied')
