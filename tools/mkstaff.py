#!/usr/bin/env python3
"""Make the Paper Staff (models/w_st01.json): a rolled-up paper rod with tape bands, a paper star crown and a glowing
spark at the top. Same simple-shapes approach and format as tools/mkbow.py (long axis = y, grip low).
usage: python3 tools/mkstaff.py"""
import base64, io, json
import numpy as np
from PIL import Image
S = 256
rng = np.random.default_rng(5)
a = np.zeros((S, S, 3), float)
y = np.arange(S)[:, None]; x = np.arange(64)[None, :]
spiral = 0.86 + 0.14 * (np.sin((y * 0.9 + x * 0.35) * 0.35) > 0.6) + rng.normal(0, .03, (S, 64))
a[:, 0:64] = np.array((226, 214, 186)) * spiral[..., None]                       # paper roll with a spiral seam
a[:, 64:128] = np.array((176, 120, 60)) * (0.8 + 0.25 * np.sin(y * .5))[..., None]  # brown tape
a[:, 128:192] = np.array((240, 232, 210))                                         # star paper
a[:, 192:256] = np.array((255, 214, 70))                                          # the spark
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
U0 = {'roll': (0, 64), 'tape': (64, 128), 'star': (128, 192), 'spark': (192, 256)}
V, N, UV, I = [], [], [], []
def tube(path, r, part, seg=12):
    path = np.array(path, float); n = len(path); rs = np.broadcast_to(np.asarray(r, float), (n,)); u0, u1 = U0[part]; b = len(V)
    for i in range(n):
        t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]; t /= np.linalg.norm(t)
        e1 = np.cross(t, [1., 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(t, e1)
        for j in range(seg + 1):
            th = 2 * np.pi * j / seg; nr = np.cos(th) * e1 + np.sin(th) * e2
            V.append(path[i] + rs[i] * nr); N.append(nr); UV.append(((u0 + (u1 - u0) * j / seg + .5) / S, i / max(1, n - 1)))
    for i in range(n - 1):
        for j in range(seg):
            p = b + i * (seg + 1) + j; q = p + seg + 1; I.extend([(p, q, p + 1), (p + 1, q, q + 1)])
def sphere(c, r, part, n=10):
    u0, u1 = U0[part]; b = len(V)
    for i in range(n + 1):
        ph = np.pi * i / n
        for j in range(n + 1):
            th = 2 * np.pi * j / n; d = np.array([np.sin(ph) * np.cos(th), np.cos(ph), np.sin(ph) * np.sin(th)])
            V.append(np.array(c) + r * d); N.append(d); UV.append(((u0 + (u1 - u0) * j / n) / S, i / n))
    for i in range(n):
        for j in range(n):
            p = b + i * (n + 1) + j; q = p + n + 1; I.extend([(p, p + 1, q), (p + 1, q + 1, q)])
L = 5.6
ys = np.linspace(0, L, 12)
tube(np.c_[0.02 * np.sin(ys * 1.3), ys, 0.02 * np.cos(ys * 1.1)], np.linspace(.16, .12, 12), "roll")
for yb in (1.2, 1.9, 3.6, 4.9):
    tube([[0, yb - .07, 0], [0, yb + .07, 0]], .17 - yb * .004, "tape")
# a five-point paper star round the top, folded (each point a flat double-sided triangle) + the spark inside
C = np.array([0, L + .7, 0])
for k in range(5):
    t0 = 2 * np.pi * k / 5; t1 = t0 + np.pi / 5; t2 = t0 - np.pi / 5
    tip = C + .8 * np.array([np.cos(t0), np.sin(t0), 0]); l = C + .34 * np.array([np.cos(t1), np.sin(t1), 0]); r = C + .34 * np.array([np.cos(t2), np.sin(t2), 0])
    for zz in (.05, -.05):
        b = len(V); V.extend([C + [0, 0, zz], l, tip, r]); nz = np.sign(zz); N.extend([[0, 0, nz]] * 4)
        UV.extend([(140 / S, .5), (150 / S, .1), (180 / S, .9), (170 / S, .1)])
        I.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)] if zz < 0 else [(b, b + 2, b + 1), (b, b + 3, b + 2)])
sphere(C, .27, "spark")
tube([[0, L - .05, 0], [0, C[1] - .3, 0]], .06, 'roll', seg=8)
V = np.array(V); N = np.array(N); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9); V[:, 1] -= V[:, 1].min()
UV = np.clip(np.array(UV), 0, 1); I = np.array(I)[:, ::-1]  # outward-facing winding (counter-clockwise from outside)
bio = io.BytesIO(); img.save(bio, 'JPEG', quality=85); b64 = lambda q: base64.b64encode(q.tobytes()).decode()
json.dump({'vb': b64(np.round(V * 1000).astype(np.int16)), 'nb': b64(np.round(N * 127).astype(np.int8)),
           'ub': b64(np.round(UV * 65535).astype(np.uint16)), 'ib': b64(I.astype(np.uint16)),
           'tex': 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()}, open('models/w_st01.json', 'w'), separators=(',', ':'))
print('models/w_st01.json', len(V), 'verts', len(I), 'tris', round(float(V[:, 1].max()), 2))
