#!/usr/bin/env python3
"""Make the nine bows, one per armour tier (models/w_bw01.json ... w_bw80.json).

Built from simple shapes like tools/mknet.py: two recurve limbs (thick at the riser, thin at the tips, tips flicking
forward), a wrapped grip at the middle, metal caps at the tips and a straight string. Long axis = y, the grip sits at
the middle (WCFG grip .5), the limbs bow towards +z and the string runs down the -z side.
Each tier has its own colours (wood, copper, iron, steel, gold, diamond, deep teal, moon silver, crimson and gold).
usage: python3 tools/mkbow.py            (writes all nine)
"""
import base64, io, json
import numpy as np
from PIL import Image

# key: limb colour, grip colour, accent (caps, riser bands), string colour, sheen (0 wood grain .. 1 metal)
TIERS = {
    'bw01': ((214, 200, 168), (150, 118, 80), (120, 96, 64), (236, 230, 214), 0.0),    # Paper Bow: pale card
    'bw10': ((196, 112, 52), (92, 54, 30), (226, 170, 90), (230, 220, 200), 0.6),      # Copper Coin Bow
    'bw20': ((104, 110, 120), (52, 40, 32), (150, 156, 166), (220, 220, 220), 0.7),    # HODL Iron Bow
    'bw30': ((196, 202, 212), (70, 40, 30), (232, 236, 242), (240, 240, 240), 0.8),    # Bull Steel Bow
    'bw40': ((224, 178, 64), (90, 24, 24), (255, 226, 130), (250, 240, 210), 0.8),     # Gold Rush Bow
    'bw50': ((150, 214, 255), (220, 230, 240), (240, 250, 255), (255, 255, 255), 0.9), # Diamond Hands Bow
    'bw60': ((30, 104, 118), (22, 40, 60), (120, 200, 210), (210, 240, 245), 0.6),     # Whale Bow
    'bw70': ((210, 220, 240), (40, 50, 96), (160, 190, 255), (230, 236, 255), 0.8),    # Moonforged Bow
    'bw80': ((176, 24, 48), (40, 10, 14), (240, 196, 80), (255, 236, 200), 0.7),       # Legendary Meme Bow
}
S = 256


def texture(limb, grip, acc, strg, sheen, seed):
    rng = np.random.default_rng(seed)
    a = np.zeros((S, S, 3), float)
    y = np.arange(S)[:, None]; x = np.arange(64)[None, :]
    grain = 0.84 + 0.16 * np.sin(y * 0.23 + np.sin(x * 0.6) * 2.2) + rng.normal(0, .035, (S, 64))
    metal = 0.78 + 0.32 * np.cos(x / 64 * np.pi * 2) ** 2 + rng.normal(0, .02, (S, 64))
    g = grain * (1 - sheen) + metal * sheen
    a[:, 0:64] = np.array(limb) * g[..., None]
    wrap = 0.62 + 0.38 * np.abs(np.sin((y + x * 0.5) * 0.42))
    a[:, 64:128] = np.array(grip) * wrap[..., None]
    a[:, 128:192] = np.array(acc) * (0.75 + 0.35 * np.cos(x / 64 * np.pi * 2) ** 2)[..., None]
    a[:, 192:256] = np.array(strg)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


U0 = {'limb': (0, 64), 'grip': (64, 128), 'acc': (128, 192), 'str': (192, 256)}


def build(key):
    V, N, UV, I = [], [], [], []

    def tube(path, r, part, seg=10):
        path = np.array(path, float); n = len(path); rs = np.broadcast_to(np.asarray(r, float), (n,))
        u0, u1 = U0[part]; b = len(V)
        for i in range(n):
            t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]; t /= np.linalg.norm(t)
            a = np.array([1., 0, 0]) if abs(t[0]) < .9 else np.array([0, 0, 1.])
            e1 = np.cross(t, a); e1 /= np.linalg.norm(e1); e2 = np.cross(t, e1)
            for j in range(seg + 1):
                th = 2 * np.pi * j / seg; nr = np.cos(th) * e1 + np.sin(th) * e2
                # limbs are flat (wider across x than deep in z), like a real bow
                V.append(path[i] + rs[i] * (np.cos(th) * e1 * (1.6 if part == 'limb' else 1) + np.sin(th) * e2))
                N.append(nr); UV.append(((u0 + (u1 - u0) * j / seg + .5) / S, i / max(1, n - 1)))
        for i in range(n - 1):
            for j in range(seg):
                p = b + i * (seg + 1) + j; q = p + seg + 1
                I.extend([(p, q, p + 1), (p + 1, q, q + 1)])
        # caps at both ends
        for end in (0, n - 1):
            c = len(V); V.append(path[end]); N.append(path[end] - path[min(max(end, 1), n - 2)]); UV.append(((u0 + 8) / S, .5))
            r0 = b + end * (seg + 1)
            for j in range(seg):
                I.append((c, r0 + j + 1, r0 + j) if end == 0 else (c, r0 + j, r0 + j + 1))

    H = 3.0; h = H / 2; D = 0.42          # height, half height, how far the limbs bow forward at the grip
    u = np.linspace(-1, 1, 41)
    # limb centreline: z = D*(1-u^2) (grip forward), the last 12% of each limb flicks forward again (recurve)
    z = D * (1 - u ** 2) + 0.16 * np.clip((np.abs(u) - .86) / .14, 0, 1) ** 2
    yy = h + u * h * 0.97
    r = 0.028 + 0.05 * (1 - np.abs(u)) ** 1.3
    tube(np.c_[np.zeros_like(u), yy, z], r, 'limb')
    # riser bands + grip wrap
    g = np.linspace(-.12, .12, 6)
    tube(np.c_[np.zeros_like(g), h + g * h, D * (1 - g ** 2) + 0.0], 0.088, 'grip')
    for s in (-1, 1):
        b0 = np.linspace(.13, .17, 3) * s
        tube(np.c_[np.zeros_like(b0), h + b0 * h, D * (1 - b0 ** 2)], 0.092, 'acc', seg=10)
        t0 = np.linspace(.9, 1.0, 4) * s
        zt = D * (1 - t0 ** 2) + 0.16 * np.clip((np.abs(t0) - .86) / .14, 0, 1) ** 2
        tube(np.c_[np.zeros_like(t0), h + t0 * h * 0.97, zt], 0.036, 'acc', seg=8)
    # string: straight between the tips (where the recurve meets the limb)
    tipz = D * (1 - .97 ** 2) + 0.16 * ((.97 - .86) / .14) ** 2
    ys = np.linspace(h - h * 0.94, h + h * 0.94, 3)
    tube(np.c_[np.zeros_like(ys), ys, np.full_like(ys, tipz - 0.05)], 0.012, 'str', seg=5)

    V = np.array(V); N = np.array(N); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    V[:, 1] -= V[:, 1].min(); V[:, 2] -= (V[:, 2].min() + V[:, 2].max()) / 2
    UV = np.clip(np.array(UV), 0, 1); I = np.array(I)[:, ::-1]  # outward-facing winding (counter-clockwise from outside)
    img = texture(*TIERS[key], seed=int(key[2:]) + 7)
    bio = io.BytesIO(); img.save(bio, 'JPEG', quality=85)
    b64 = lambda a: base64.b64encode(a.tobytes()).decode()
    out = f'models/w_{key}.json'
    json.dump({'vb': b64(np.round(V * 1000).astype(np.int16)), 'nb': b64(np.round(N * 127).astype(np.int8)),
               'ub': b64(np.round(UV * 65535).astype(np.uint16)), 'ib': b64(I.astype(np.uint16)),
               'tex': 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()},
              open(out, 'w'), separators=(',', ':'))
    print(out, len(V), 'verts', len(I), 'tris')


if __name__ == '__main__':
    for k in TIERS: build(k)
