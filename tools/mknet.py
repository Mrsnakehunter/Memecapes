#!/usr/bin/env python3
"""Make the small fishing net that the character holds while fishing (models/w_net.json).

Built from simple shapes: a wooden handle, a rope-bound grip, a wooden hoop and a net bag that
hangs from the hoop. Same format as the other held models (long axis = y, grip at the bottom).
usage: python3 tools/mknet.py [models/w_net.json] [--bag -1|1]
"""
import base64, io, json, sys
import numpy as np
from PIL import Image, ImageDraw

out = next((a for a in sys.argv[1:] if a.endswith('.json')), 'models/w_net.json')
BAG = -1.0 if '--bag' not in sys.argv else float(sys.argv[sys.argv.index('--bag') + 1])

# ---- texture: 4 strips (wood, grip rope, hoop wood, net)
S = 256
img = Image.new('RGB', (S, S)); dr = ImageDraw.Draw(img)
rng = np.random.default_rng(3)
def wood(x0, x1, base):
    for x in range(x0, x1):
        for y in range(S):
            g = 0.82 + 0.18 * np.sin(y * 0.21 + np.sin(x * 0.7) * 2) + rng.normal(0, .04)
            img.putpixel((x, y), tuple(int(max(0, min(255, c * g))) for c in base))
wood(0, 64, (128, 84, 46))          # handle
for x in range(64, 128):             # rope wrap
    for y in range(S):
        g = 0.7 + 0.3 * abs(np.sin((y + x * 0.4) * 0.5))
        img.putpixel((x, y), tuple(int(c * g) for c in (196, 168, 112)))
wood(128, 192, (104, 66, 36))       # hoop
dr.rectangle([192, 0, 255, 255], fill=(52, 64, 60))   # net: dark gaps with light cord lines
for k in range(0, S, 10):
    dr.line([(192, k), (255, k + 30)], fill=(214, 200, 160), width=2)
    dr.line([(192, k + 30), (255, k)], fill=(214, 200, 160), width=2)
U0 = {'handle': (0, 64), 'rope': (64, 128), 'hoop': (128, 192), 'net': (192, 256)}

V, N, UV, I = [], [], [], []
def add(P, Nn, T, F):
    b = len(V); V.extend(P); N.extend(Nn); UV.extend(T); I.extend([[b + a, b + c, b + d] for a, c, d in F])

def tube(path, r, part, seg=10, close=False):
    """a tube along a list of points, radius r (number or list)"""
    path = np.array(path, float); n = len(path); rs = np.broadcast_to(np.asarray(r, float), (n,))
    u0, u1 = U0[part]; P, Nn, T, F = [], [], [], []
    for i in range(n):
        t = path[(i + 1) % n] - path[i - 1] if close else path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        t /= np.linalg.norm(t); a = np.array([1, 0, 0]) if abs(t[0]) < .9 else np.array([0, 0, 1])
        e1 = np.cross(t, a); e1 /= np.linalg.norm(e1); e2 = np.cross(t, e1)
        for j in range(seg + 1):
            th = 2 * np.pi * j / seg; nrm = np.cos(th) * e1 + np.sin(th) * e2
            P.append(path[i] + rs[i] * nrm); Nn.append(nrm); T.append(((u0 + (u1 - u0) * j / seg) / S, i / max(1, n - 1)))
    m = n if close else n - 1
    for i in range(m):
        for j in range(seg):
            a = i * (seg + 1) + j; b = ((i + 1) % n) * (seg + 1) + j
            F += [(a, b, a + 1), (a + 1, b, b + 1)]
    add(P, Nn, T, F)

L, R = 3.0, 0.75          # handle length, hoop radius
tube([[0, y, 0] for y in np.linspace(0, L, 8)], np.linspace(.075, .06, 8), 'handle')
tube([[0, y, 0] for y in np.linspace(0.05, 0.9, 4)], .088, 'rope')
C = np.array([0, L + R * 0.92, 0])
ring = [C + R * np.array([0, np.cos(t), np.sin(t)]) for t in np.linspace(0, 2 * np.pi, 33)[:-1]]
tube(ring, .055, 'hoop', seg=8, close=True)
# the bag: rings shrinking away from the hoop, sagging down (towards -y) as they go
P, Nn, T, F = [], [], [], []; K, M = 7, 24
for k in range(K):
    f = k / (K - 1); rr = R * (1 - 0.85 * f ** 1.4); off = BAG * 1.1 * f
    for j in range(M + 1):
        t = 2 * np.pi * j / M; d = np.array([0, np.cos(t), np.sin(t)])
        p = C + rr * d + np.array([off, -0.35 * f * f, 0]); P.append(p)
        Nn.append(d * 0.8 + np.array([BAG * 0.2, 0, 0])); T.append(((192 + 64 * j / M) / S, f))
for k in range(K - 1):
    for j in range(M):
        a = k * (M + 1) + j; b = a + M + 1
        F += [(a, b, a + 1), (a + 1, b, b + 1), (a, a + 1, b), (a + 1, b + 1, b)]  # both sides
add(P, Nn, T, F)

V = np.array(V); N = np.array(N); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
V[:, 1] -= V[:, 1].min()
UV = np.clip(np.array(UV), 0, 1); I = np.array(I)
bio = io.BytesIO(); img.save(bio, 'JPEG', quality=85)
b64 = lambda a: base64.b64encode(a.tobytes()).decode()
json.dump({'vb': b64(np.round(V * 1000).astype(np.int16)), 'nb': b64(np.round(N * 127).astype(np.int8)),
           'ub': b64(np.round(UV * 65535).astype(np.uint16)), 'ib': b64(I.astype(np.uint16)),
           'tex': 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()},
          open(out, 'w'), separators=(',', ':'))
print(out, len(V), 'verts', len(I), 'tris', 'height', round(float(V[:, 1].max()), 3))
