#!/usr/bin/env python3
"""Make the nine staffs, one per tier (models/w_st01.json ... w_st80.json): a rod with bands, a five-point star crown
and a glowing orb at the top, coloured per tier (paper, copper, iron, steel, gold, diamond, teal, moon, crimson).
Same simple-shapes approach and format as tools/mkbow.py (long axis = y, grip low).
usage: python3 tools/mkstaff.py            (writes all nine)"""
import base64, io, json
import numpy as np
from PIL import Image
# rod, bands, star, orb
TIERS = {'st01': ((226, 214, 186), (176, 120, 60), (240, 232, 210), (255, 214, 70)),
         'st10': ((150, 95, 55), (210, 125, 60), (214, 140, 70), (255, 170, 80)),
         'st20': ((70, 72, 78), (130, 134, 142), (110, 114, 122), (160, 200, 255)),
         'st30': ((200, 204, 212), (160, 40, 40), (230, 234, 240), (255, 90, 70)),
         'st40': ((110, 50, 140), (235, 185, 70), (250, 210, 90), (255, 232, 120)),
         'st50': ((232, 240, 250), (190, 200, 215), (170, 225, 255), (205, 242, 255)),
         'st60': ((30, 104, 118), (205, 222, 230), (60, 170, 190), (120, 240, 255)),
         'st70': ((40, 50, 96), (210, 220, 240), (220, 228, 250), (255, 190, 240)),
         'st80': ((150, 20, 40), (240, 196, 80), (240, 196, 80), (255, 60, 80))}
S = 256
def build(key):
    ROD, BAND, STAR, ORB = TIERS[key]
    rng = np.random.default_rng(5)
    a = np.zeros((S, S, 3), float)
    y = np.arange(S)[:, None]; x = np.arange(64)[None, :]
    spiral = 0.86 + 0.14 * (np.sin((y * 0.9 + x * 0.35) * 0.35) > 0.6) + rng.normal(0, .03, (S, 64))
    a[:, 0:64] = np.array(ROD) * spiral[..., None]                       # paper roll with a spiral seam
    a[:, 64:128] = np.array(BAND) * (0.8 + 0.25 * np.sin(y * .5))[..., None]  # brown tape
    a[:, 128:192] = np.array(STAR)                                         # star paper
    a[:, 192:256] = np.array(ORB)                                          # the spark
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
               'tex': 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()}, open(f'models/w_{key}.json', 'w'), separators=(',', ':'))
    print(f'models/w_{key}.json', len(V), 'verts', len(I), 'tris', round(float(V[:, 1].max()), 2))


if __name__ == '__main__':
    for k in TIERS: build(k)
