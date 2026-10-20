#!/usr/bin/env python3
"""Token plan C in the game's words: the player pot is not bought at launch.

The bank exchange stays a demo until the public pot (ecosystem) wallet holds real $CAPES, bought over time with
game income. Its note now says so, instead of "until $CAPES launches" (launch alone no longer opens it).
Run from the repo root after patch_memecape.py:  python3 tools/patch_tokenplan.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


rep("Demo values until $CAPES launches.",
    "Demo values for now: real $CAPES payouts open once the public pot wallet is funded.")
open(PATH, 'w', encoding='utf-8').write(h)
print('token plan patch applied')
