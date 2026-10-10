#!/usr/bin/env python3
"""Make a redeem code for something sold in the shop.

  python3 tools/mkcode.py cape "Moonlight cape" "#3a6ad9"      a custom cape in that colour
  python3 tools/mkcode.py hat "Gold top hat" "#ffd23f"         a custom hat (head slot)
  python3 tools/mkcode.py coins 5000                           Meme Coins into the bank
  python3 tools/mkcode.py item ccape                           an existing item, by its key
  python3 tools/mkcode.py skin sk_laser                        a weapon or cape skin ($2.99 in the plan)
  python3 tools/mkcode.py skin bundle sk_laser cs_moon_night ...   several skins in one code (the 4-skin bundle)

It prints the code (send it ONLY to the buyer) and one line to paste into "codes" in config.js.
The code itself is never stored in the public files, only its fingerprint (SHA-256).
"""
import hashlib, json, secrets, sys
A = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
code = 'MC-' + ''.join(secrets.choice(A) for _ in range(4)) + '-' + ''.join(secrets.choice(A) for _ in range(4))
kind = sys.argv[1] if len(sys.argv) > 1 else ''
if kind == 'coins':
    gift = {'coins': int(sys.argv[2])}
elif kind == 'item':
    gift = {'item': sys.argv[2]}
elif kind == 'skin':
    import re
    ids = sys.argv[3:] if len(sys.argv) > 2 and sys.argv[2] == 'bundle' else sys.argv[2:3]
    known = re.findall(r"\('((?:sk|cs)_\w+)'", open(__file__.replace('mkcode.py', 'patch_skins.py')).read())
    bad = [i for i in ids if i not in known]
    if not ids or bad: sys.exit('unknown skin %s; skins are: %s' % (bad, ' '.join(known)))
    gift = {'skin': ids[0]} if len(ids) == 1 else {'skins': ids}
elif kind in ('cape', 'hat'):
    gift = {'custom': {'name': sys.argv[2], 'kind': 'cape' if kind == 'cape' else 'helm', 'color': sys.argv[3] if len(sys.argv) > 3 else '#d9a520',
                       'slot': 'cape' if kind == 'cape' else 'head', 'ex': sys.argv[4] if len(sys.argv) > 4 else 'One of a kind.'}}
else:
    sys.exit(__doc__)
h = hashlib.sha256(code.encode()).hexdigest()
print('Code for the buyer:  ', code)
print('Paste into codes in config.js:')
print('    "%s": %s,' % (h, json.dumps(gift)))
