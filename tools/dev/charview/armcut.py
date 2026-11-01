#!/usr/bin/env python3
"""Cut the chest piece out of an armour body for its bag icon: bind (A) pose, a per-vertex keep field (>0 = keep)
that the icon renderer clips per pixel, so the cuts are clean lines (neck, waist, upper arms).
usage: python3 tools/dev/charview/armcut.py arm_lv40 out.json [NECK LOW ARM AD AT XSH]"""
import json, base64, sys, numpy as np
def dec(s, t): return np.frombuffer(base64.b64decode(s), dtype=t)
def run(k, out, NECK=.07, LOW=.40, ARM=.09, AD=.12, AT=.5, XSH=0):
    d = json.load(open('/home/claude/memecapes/models/%s.json' % k))
    V = dec(d['vb'], np.int16).astype(np.float32).reshape(-1, 3) / 1000
    N = dec(d['nb'], np.int8).astype(np.float32).reshape(-1, 3) / 127
    J = dec(d['jb'], np.uint8).reshape(-1, 4); W = dec(d['wb'], np.uint8).astype(np.float32).reshape(-1, 4) / 255
    wb = np.zeros((len(V), 28), np.float32)
    for c in range(4): np.add.at(wb, (np.arange(len(V)), J[:, c]), W[:, c])
    arm = wb[:, 9:18].sum(1); legs = wb[:, 18:28].sum(1); head = wb[:, 4:8].sum(1)
    sh = np.median(V[wb[:, [8, 13]].sum(1) > .5, 1])
    y = V[:, 1]
    xs = np.abs(V[:, 0]); xsh = np.percentile(xs[(wb[:, [0, 1, 2, 3]].sum(1) > .6) & (V[:, 1] > sh - .30) & (V[:, 1] < sh - .15)], 98)
    if XSH: xsh = XSH
    f = np.minimum(sh + NECK - y, y - (sh - LOW))
    f = np.where(arm > AT, np.minimum(f, np.minimum(xsh + ARM - xs, y - (sh - AD))), f)
    f = np.minimum(f, xsh + ARM + .6 * np.maximum(0, y - (sh - .08)) - xs)  # sleeves weighted to the spine/head still go
    f = np.where(legs > .6, np.minimum(f, -.01), f)
    f = np.where((head > .5) & (y > sh), np.minimum(f, -.01), f)
    I = dec(d['ib'], np.uint16).reshape(-1, 3)
    I = I[(f[I] > -.03).any(1)]
    c = V[f > 0]; ctr = (c.max(0) + c.min(0)) / 2
    o = {'vb': base64.b64encode(np.round((V - ctr) * 1000).astype(np.int16).tobytes()).decode(), 'nb': d['nb'], 'ub': d['ub'],
         'kb': base64.b64encode(np.round(np.clip(f, -.3, .3) * 1e5).astype(np.int16).tobytes()).decode(),
         'ib': base64.b64encode(I.astype(np.uint16).tobytes()).decode(), 'tex': d['tex'], 'size': (c.max(0) - c.min(0)).tolist()}
    json.dump(o, open(out, 'w')); print(k, len(I), 'tris, size', np.round(c.max(0) - c.min(0), 3))
if __name__ == '__main__':
    a = sys.argv; run(a[1], a[2], *[float(x) for x in a[3:]])
