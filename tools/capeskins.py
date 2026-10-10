#!/usr/bin/env python3
"""Make the cape skins: a pattern painted onto the cape of each caped body.

The pattern is laid out in the cape's own 3D space (across the back and down its length), not in
texture space, so it reads as one picture even though the texture is cut into pieces. The cape's
folds and shading are kept: each texel's brightness multiplies the pattern.
Writes models/skins/<skin>_m.jpg and <skin>_f.jpg (one per caped body) and a back-view preview of
each in /tmp/capeskin_<skin>.png when --preview is given.
usage: python3 tools/capeskins.py [--preview]
"""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
BODIES = {'m': 'models/player_cape.json', 'f': 'models/playerf_cape.json'}


def load(p):
    d = json.load(open(p))
    V = np.frombuffer(base64.b64decode(d['vb']), np.int16).reshape(-1, 3) / 1000.
    U = np.frombuffer(base64.b64decode(d['ub']), np.uint16).reshape(-1, 2) / 65535.
    I = np.frombuffer(base64.b64decode(d['ib']), np.uint16).reshape(-1, 3).astype(int)
    tex = np.asarray(Image.open(io.BytesIO(base64.b64decode(d['tex'].split(',')[1]))).convert('RGB').resize((S, S))).astype(float)
    cm = np.asarray(Image.open(io.BytesIO(base64.b64decode(d['cm'].split(',')[1]))).convert('L').resize((S, S), Image.NEAREST))
    return d, V, U, I, tex, cm


def posmap(V, U, I):
    """for every texel, the 3D point of the model it paints (x across, y up)"""
    pm = np.full((S, S, 3), np.nan)
    for t in I:
        uv = U[t] * S; p = V[t]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
        if x1 < x0 or y1 < y0: continue
        (ax, ay), (bx, by), (cx, cy) = uv
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        w2 = 1 - w0 - w1
        ins = (w0 >= -.02) & (w1 >= -.02) & (w2 >= -.02)
        P = w0[..., None] * p[0] + w1[..., None] * p[1] + w2[..., None] * p[2]
        yy, xx = ys[ins].astype(int), xs[ins].astype(int)
        pm[yy, xx] = P[ins]
    # fill the thin gaps along texture seams from neighbouring texels
    for _ in range(4):
        miss = np.isnan(pm[..., 0])
        if not miss.any(): break
        acc = np.zeros_like(pm); cnt = np.zeros((S, S, 1))
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sh = np.roll(np.roll(pm, dy, 0), dx, 1); ok = ~np.isnan(sh[..., :1])
            acc += np.where(ok, sh, 0); cnt += ok
        fill = miss & (cnt[..., 0] > 0)
        pm[fill] = acc[fill] / cnt[fill]
    return pm


# ---- patterns: f(u, v) -> rgb, u = across the back (-1..1), v = down the cape (0 top .. 1 bottom)
def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def candles(u, v, up):
    base = hexc('#0d1f14') if up else hexc('#1f0c0e')
    body = hexc('#2fd25a') if up else hexc('#e0303a')
    out = np.tile(base, u.shape + (1,))
    n = 7; col = np.floor((u + 1) / 2 * n); fx = ((u + 1) / 2 * n) % 1
    # each column's candle sits higher (or lower) than the last: a staircase chart
    step = (col / n) if up else (1 - col / n)
    mid = .78 - step * .6 + .06 * np.sin(col * 2.1)
    h = .16 + .05 * np.cos(col * 3.3)
    inbody = (np.abs(fx - .5) < .28) & (np.abs(v - mid) < h / 2)
    wick = (np.abs(fx - .5) < .05) & (np.abs(v - mid) < h / 2 + .07)
    grid = (np.abs(((v * 10) % 1) - .5) > .48)
    out[grid] = out[grid] * .6 + body * .1
    out[wick] = body * .8
    out[inbody] = body
    return out


def laser(u, v):
    out = np.tile(hexc('#140608'), u.shape + (1,))
    for s in (-1, 1):  # two beams crossing in an X
        d = np.abs((u * s) - (v * 1.6 - .8)) / math.sqrt(1 + 1.6 ** 2)
        glow = np.exp(-(d / .05) ** 2)[..., None]; core = np.exp(-(d / .012) ** 2)[..., None]
        out = out * (1 - glow * .9) + hexc('#ff2020') * glow * .9
        out = out * (1 - core) + hexc('#ffd0c0') * core
    return out


def diamonds(u, v):
    a = (u * 3 + v * 4.5); b = (u * 3 - v * 4.5)
    fa, fb = a % 1, b % 1
    edge = np.minimum(np.minimum(fa, 1 - fa), np.minimum(fb, 1 - fb))
    shade = (.75 + .25 * np.sin((fa - fb) * math.pi))[..., None]
    out = hexc('#3a8fb8') * shade
    out[edge < .04] = hexc('#d8f2ff')
    glint = (np.abs(fa - .3) < .05) & (np.abs(fb - .3) < .05)
    out[glint] = hexc('#ffffff')
    return out


def moon(u, v):
    out = np.tile(hexc('#0b1638'), u.shape + (1,))
    out = out * (1 - .35 * v[..., None]) + hexc('#2a1a5a') * .35 * v[..., None]
    rng = np.random.default_rng(7)
    for _ in range(140):
        cx, cy, r = rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(.006, .016)
        m = (u - cx) ** 2 + ((v - cy) * 1.8) ** 2 < r * r
        out[m] = hexc('#fff6d0')
    c1 = (u - .05) ** 2 + ((v - .28) * 1.8) ** 2 < .2 ** 2
    c2 = (u - .14) ** 2 + ((v - .24) * 1.8) ** 2 < .17 ** 2
    out[c1 & ~c2] = hexc('#ffe9a0')
    return out


def coins(u, v):
    out = np.tile(hexc('#7a5208'), u.shape + (1,))
    gx, gy = u * 3.2, v * 6
    row = np.floor(gy); fx = (gx + .5 * (row % 2)) % 1; fy = gy % 1
    d = np.hypot(fx - .5, (fy - .5))
    coin = d < .42
    out[coin] = hexc('#f2c14e')
    out[(d < .42) & (d > .36)] = hexc('#b8860b')
    eyes = (np.hypot(np.abs(fx - .5) - .12, fy - .42) < .045)
    smile = (np.abs(np.hypot(fx - .5, fy - .5) - .2) < .03) & (fy > .55)
    out[coin & (eyes | smile)] = hexc('#6a4406')
    return out


SKINS = {'green_candles': lambda u, v: candles(u, v, True), 'red_candles': lambda u, v: candles(u, v, False),
         'laser_eyes': laser, 'diamond_hands': diamonds, 'moon_night': moon, 'coin_gold': coins}


def make(body, path, preview):
    d, V, U, I, tex, cm = load(path)
    pm = posmap(V, U, I)
    hi, lo = tex.max(2), tex.min(2)
    grey = (hi - lo < 45) & (hi > 70)
    sel = (cm > 200) | ((cm > 60) & grey)
    sel &= ~np.isnan(pm[..., 0])
    P = pm[sel]
    # cape space: across = x, down = y (top of the cape = 0)
    x0, x1 = np.percentile(P[:, 0], [2, 98]); y0, y1 = np.percentile(P[:, 1], [2, 98])
    u = np.clip(-(P[:, 0] - (x0 + x1) / 2) / ((x1 - x0) / 2), -1.2, 1.2)  # seen from behind, left to right
    v = np.clip((y1 - P[:, 1]) / (y1 - y0), -.1, 1.1)
    lum = tex[sel].mean(1); g = np.clip(lum / np.percentile(lum, 70), .35, 1.25)[:, None]
    for name, fn in SKINS.items():
        out = tex.copy()
        out[sel] = np.clip(fn(u, v) * g, 0, 255)
        im = Image.fromarray(out.astype(np.uint8))
        im.save(f'models/skins/{name}_{body}.jpg', quality=86)
        if preview:
            d2 = dict(d); bio = io.BytesIO(); im.save(bio, 'JPEG', quality=86)
            d2['tex'] = 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()
            d2.pop('an', None); json.dump(d2, open(f'/tmp/cs_{name}_{body}.json', 'w'))
        print(body, name, 'done')


if __name__ == '__main__':
    for b, p in BODIES.items():
        make(b, p, '--preview' in sys.argv)
