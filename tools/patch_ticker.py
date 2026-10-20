#!/usr/bin/env python3
"""Last build step: show the token as $<config.js ticker> in the game (the base and older patches say $CAPES)."""
import re
cfg = open('config.js').read()
t = (re.search(r'ticker:\s*"([A-Z0-9]{2,10})"', cfg) or [None, 'CAPES'])[1]
if t != 'CAPES':
    h = open('play.html').read()
    n = h.count('$CAPES') + h.count('$capes')
    h = h.replace('$CAPES', '$' + t).replace('$capes', '$' + t.lower())
    open('play.html', 'w').write(h)
    print('ticker:', n, 'mentions ->', '$' + t)
else:
    print('ticker: unchanged')
