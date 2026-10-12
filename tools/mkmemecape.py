#!/usr/bin/env python3
"""The MemeCape on the caped bodies, like every other cape (models/player_memecape.json, playerf_memecape.json).

Before, the MemeCape (and the Quest cape) were a separate stiff cape shape drawn behind the character: it did not
move with the body, so it hung off one shoulder when the character turned, walked or swung. Every other cape is
part of the character (the caped bodies made in Meshy) and moves with it.

Now the MemeCape is the caped body too:
  - the MemeCape pattern is laid out in the cape's own 3D space (so it reads as one picture although the texture
    is cut into pieces): red velvet with faint gold embroidery, the MemeCapes coin under the collar, staggered rows
    of gold-framed medallions with the game's own meme characters (tools/art/memecape), a gold border down both
    edges and along the hem; the cape's folds and shading are kept (each texel's brightness multiplies it);
  - the inside of the cape is dark red velvet;
  - the gold crown is part of the model, on the head bone, so it stays on the head through every motion.
usage: python3 tools/mkmemecape.py [--preview]       (run from the repo root)
"""
import base64, io, json, math, sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'tools')
from capeskins import load, posmap, S

BODIES = {'player': 'models/player_cape.json', 'playerf': 'models/playerf_cape.json'}
HEAD = 5   # head bone of the caped bodies (22-bone rig)


ART = 'tools/art/memecape'
# the game's own meme characters, one per medallion (portraits cut from their 3D renders)
FACES = ['bonk', 'shibe', 'popcat', 'froggo', 'mog_coin', 'floki', 'bouncy_hippo', 'gigachad', 'fartcoin', 'slerf',
         'nutty_the_squirrel', 'book_of_meme', 'golden_hound', 'lamp_genie', 'brainrot_jester', 'shiba_inu',
         'the_frozen_shibe', 'rich_wojak', 'snack_shibe']
BACKS = [(28, 92, 120), (92, 40, 128), (196, 98, 22), (26, 110, 64), (30, 64, 140), (150, 30, 40), (20, 120, 120),
         (120, 90, 20), (70, 30, 90)]


def medallions():
    """128 px round medallion faces on jewel-coloured enamel"""
    out = []
    yy, xx = np.mgrid[0:128, 0:128]; rr = np.hypot(xx - 63.5, yy - 63.5) / 64
    for i, n in enumerate(FACES):
        im = np.asarray(Image.open(f'{ART}/{n}.png').convert('RGBA')).astype(float)
        bc = np.array(BACKS[i % len(BACKS)], float)
        bg = bc[None, None] * (1.15 - .45 * rr[..., None])           # enamel, lighter in the middle
        a = im[..., 3:4] / 255
        rgb = im[..., :3]
        dark = (rgb.max(2, keepdims=True) < 26) & (a > .5)          # black studio backgrounds count as background
        a = np.where(dark, 0, a)
        out.append(rgb * a + bg * (1 - a))
    logo = np.asarray(Image.open(f'{ART}/_logo.png').convert('RGBA').resize((128, 128), Image.LANCZOS)).astype(float)
    la = logo[..., 3:4] / 255
    logo = logo[..., :3] * la + np.array([120, 14, 26.]) * (1 - la)
    return out, logo


def pattern(X, Y, u, v, top, half):
    """the MemeCape: red velvet, gold-framed medallions in staggered rows, the MemeCapes coin at the top,
    a gold embroidered border. X, Y in metres (X from the cape's middle, seen from behind +X is on the left)."""
    faces, logo = medallions()
    n = len(X)
    # velvet with a faint gold diamond embroidery
    out = np.zeros((n, 3)) + np.array([150., 18, 34]) * (1 - .35 * v)[:, None]
    q1, q2 = (X * 26 + Y * 26) % 1, (X * 26 - Y * 26) % 1
    emb = (np.minimum(np.minimum(q1, 1 - q1), np.minimum(q2, 1 - q2)) < .05)
    out[emb] = out[emb] * .7 + np.array([214., 168, 60]) * .3
    R, RING = .066, .011
    def disc(cx, cy, r, img):
        dx, dy = -(X - cx), (cy - Y)                                # image x runs left to right seen from behind
        d = np.hypot(dx, dy)
        ring = (d < r + RING) & (d >= r)
        t = (d[ring] - r) / RING
        gold = np.array([255., 222, 110])[None] * (1 - t)[:, None] + np.array([150., 98, 14])[None] * t[:, None]
        out[ring] = gold
        rim = (d < r + RING + .0035) & (d >= r + RING)
        out[rim] = np.array([70., 40, 6])
        ins = d < r
        px = np.clip((dx[ins] / r + 1) / 2 * 127, 0, 127).astype(int)
        py = np.clip((dy[ins] / r + 1) / 2 * 127, 0, 127).astype(int)
        out[ins] = img[py, px]
    # the MemeCapes coin, bigger, just below the collar
    yl = top - .2
    disc(0, yl, .085, logo)
    # staggered rows of medallions under it
    k = 0
    dxs, dys = .16, .145
    for row in range(12):
        cy = yl - .155 - row * dys
        off = (row % 2) * dxs / 2
        for col in range(-4, 5):
            cx = col * dxs + off
            # only where the whole medallion fits inside the border at that height
            hw = np.interp(cy, *half)
            if abs(cx) + R + RING + .02 > hw * .86 or cy - R < Y.min() + .07: continue
            disc(cx, cy, R, faces[k % len(faces)]); k += 1
    # gold embroidered border down both edges and along the hem
    edge = np.maximum(np.abs(u), 0)
    side = edge > .9; hem = v > .955
    bd = side | hem
    tt = np.where(side, (edge - .9) / .1, (v - .955) / .045)
    out[bd] = np.array([236., 186, 64]) * (1 - .35 * np.abs(np.sin(tt[bd] * 9)))[:, None]
    inner = ((edge > .875) & (edge <= .9) & ~hem) | ((v > .945) & (v <= .955) & ~side)
    out[inner] = np.array([90., 50, 8])
    return out, k


def crown(V, J, W, top):
    """a gold crown ring around the head: points in bind space, all on the head bone"""
    dom = J[np.arange(len(J)), W.argmax(1)]
    hd = V[dom == HEAD]
    yb = top - 0.115
    band = hd[np.abs(hd[:, 1] - (yb + .03)) < .02]
    cx, cz = (band[:, 0].min() + band[:, 0].max()) / 2, (band[:, 2].min() + band[:, 2].max()) / 2
    # the ring fits round the head; the back of the hair sticks out further than the face, so use percentiles
    rx = (np.percentile(band[:, 0], 99) - np.percentile(band[:, 0], 1)) / 2 + .016
    rz = (np.percentile(band[:, 2], 97) - np.percentile(band[:, 2], 3)) / 2 + .012
    H = .05; P, N, UVc, I = [], [], [], []
    def add(p, n, uv): P.append(p); N.append(n); UVc.append(uv); return len(P) - 1
    n = 36
    for side in (1, -1):          # outside and inside of the band
        base = len(P)
        for i in range(n + 1):
            a = i / n * 2 * math.pi; s, c = math.sin(a), math.cos(a)
            for j, y in enumerate((yb, yb + H)):
                k = 1 + (.04 if side > 0 else 0)
                add([cx + rx * k * s, y, cz + rz * k * c], [side * s, 0, side * c], (i / n, j))
        for i in range(n):
            a0, a1, b0, b1 = base + i * 2, base + i * 2 + 1, base + i * 2 + 2, base + i * 2 + 3
            I += ([a0, b0, b1, a0, b1, a1] if side > 0 else [a0, b1, b0, a0, a1, b1])
    # rim on top of the band
    base = len(P)
    for i in range(n + 1):
        a = i / n * 2 * math.pi; s, c = math.sin(a), math.cos(a)
        add([cx + rx * 1.04 * s, yb + H, cz + rz * 1.04 * c], [0, 1, 0], (i / n, .9))
        add([cx + rx * s, yb + H, cz + rz * c], [0, 1, 0], (i / n, .9))
    for i in range(n):
        a0, a1, b0, b1 = base + i * 2, base + i * 2 + 1, base + i * 2 + 2, base + i * 2 + 3
        I += [a0, b1, b0, a0, a1, b1]
    # 6 points with a ball on each (one point straight over the face)
    for k in range(6):
        am = k / 6 * 2 * math.pi; a0, a1 = am - .3, am + .3
        p0 = [cx + rx * 1.02 * math.sin(a0), yb + H, cz + rz * 1.02 * math.cos(a0)]
        p1 = [cx + rx * 1.02 * math.sin(a1), yb + H, cz + rz * 1.02 * math.cos(a1)]
        tip = [cx + rx * 1.06 * math.sin(am), yb + H + .055, cz + rz * 1.06 * math.cos(am)]
        nn = [math.sin(am), .35, math.cos(am)]
        i0, i1, i2 = add(p0, nn, (.3, .9)), add(p1, nn, (.7, .9)), add(tip, nn, (.5, 1.))
        I += [i0, i1, i2, i0, i2, i1]
        ball = [tip[0], tip[1] + .009, tip[2]]; bb = len(P)
        for j in range(4):
            for i in range(8):
                th = j / 3 * math.pi; ph = i / 8 * 2 * math.pi
                q = [math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)]
                add([ball[0] + q[0] * .011, ball[1] + q[1] * .011, ball[2] + q[2] * .011], q, (.5, 2.))  # 2 = gem
        for j in range(3):
            for i in range(8):
                a, b = bb + j * 8 + i, bb + j * 8 + (i + 1) % 8
                I += [a, b, b + 8, a, b + 8, a + 8]
    # a red jewel on the front of the band, over the face
    f = [cx, yb + H * .5, cz + rz * 1.05 + .004]; bb = len(P)
    for j in range(4):
        for i in range(8):
            th = j / 3 * math.pi; ph = i / 8 * 2 * math.pi
            q = [math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)]
            add([f[0] + q[0] * .014, f[1] + q[1] * .014, f[2] + q[2] * .007], q, (.5, 3.))   # 3 = ruby
    for j in range(3):
        for i in range(8):
            a, b = bb + j * 8 + i, bb + j * 8 + (i + 1) % 8
            I += [a, b, b + 8, a, b + 8, a + 8]
    return np.array(P), np.array(N, float), np.array(UVc, float), np.array(I, int)


def free_block(pm, size):
    """a square of the texture no triangle uses (pm is NaN there), for the crown's gold"""
    free = np.isnan(pm[..., 0]).astype(np.int32)
    ii = np.pad(free.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    n = size + 4
    tot = ii[n:, n:] - ii[:-n, n:] - ii[n:, :-n] + ii[:-n, :-n]
    ys, xs = np.nonzero(tot == n * n)
    if not len(ys): return None
    return int(xs[0]) + 2, int(ys[0]) + 2


def make(base, path, preview):
    d, V, U, I, tex, cm = load(path)
    Nn = np.frombuffer(base64.b64decode(d['nb']), np.int8).reshape(-1, 3) / 127.
    pm = posmap(V, U, I); nm = posmap(Nn, U, I)
    hi, lo = tex.max(2), tex.min(2)
    sel = ((cm > 200) | ((cm > 60) & (hi - lo < 45) & (hi > 70))) & ~np.isnan(pm[..., 0])
    P, Nt = pm[sel], nm[sel]
    y0, y1 = np.percentile(P[:, 1], [1.5, 99.5])
    v = np.clip((y1 - P[:, 1]) / (y1 - y0), 0, 1)
    # the cape's width at each height: map its own left and right edge onto the painting's
    nb = 48; bi = np.clip((v * nb).astype(int), 0, nb - 1)
    XL = np.zeros(nb); XR = np.zeros(nb)
    for b in range(nb):
        xs = P[bi == b, 0]
        if len(xs) < 20: xs = P[np.abs(bi - b) <= 3, 0]
        XL[b], XR[b] = np.percentile(xs, [1, 99])
    k = np.ones(5) / 5; XL = np.convolve(np.pad(XL, 2, mode='edge'), k, 'valid'); XR = np.convolve(np.pad(XR, 2, mode='edge'), k, 'valid')
    xc = (XL[bi] + XR[bi]) / 2
    u = np.clip(-(P[:, 0] - xc) / ((XR[bi] - XL[bi]) / 2), -1, 1)   # seen from behind, left to right
    ys = y1 - (np.arange(nb) + .5) / nb * (y1 - y0)                    # cape half-width at each height (for layout)
    half = (ys[::-1], ((XR - XL) / 2)[::-1])
    col, nmed = pattern(P[:, 0] - xc, P[:, 1], u, v, y1, half)
    print(base, 'medallions', nmed)
    lum = tex[sel].mean(1); g = np.clip(lum / np.percentile(lum, 70), .45, 1.2)[:, None]
    inner = Nt[:, 2] > .35          # faces the body: the lining
    lining = np.array([92., 12., 24.]) * (.75 + .25 * (1 - v))[:, None]
    out = tex.copy()
    px = np.where(inner[:, None], lining, col * (.5 + .5 * g))
    out[sel] = np.clip(px, 0, 255)
    # crown gold and jewels in a free corner of the texture
    m = {'V': V}
    J = np.frombuffer(base64.b64decode(d['jb']), np.uint8).reshape(-1, 4).astype(int)
    W = np.frombuffer(base64.b64decode(d['wb']), np.uint8).reshape(-1, 4).astype(float)
    CP, CN, CUV, CI = crown(V, J, W, V[:, 1].max())
    fb = free_block(pm, 32); assert fb, 'no free texture block for the crown'
    bx, by = fb
    for yy in range(20):         # gold, light at the top of the band, darker below, one engraved line
        t = yy / 19
        gcol = np.array([250, 214, 96]) * (1 - t) + np.array([168, 112, 18]) * t
        if yy == 10: gcol = gcol * .8
        out[by + yy, bx:bx + 32] = gcol
    out[by + 20:by + 26, bx:bx + 32] = [255, 236, 150]      # bright gold (balls on the points)
    out[by + 26:by + 32, bx:bx + 32] = [200, 16, 40]        # ruby
    def cuv(t):
        u_, v_ = t
        if v_ >= 3: return (bx + 16) / S, (by + 29.5) / S
        if v_ >= 2: return (bx + 16) / S, (by + 23) / S
        return (bx + 2 + u_ * 28) / S, (by + 1 + (1 - min(v_, 1)) * 17) / S
    CUVt = np.array([cuv(t) for t in CUV])
    nv = len(V)
    V2 = np.vstack([V, CP]); N2 = np.vstack([Nn, CN / np.maximum(np.linalg.norm(CN, axis=1, keepdims=True), 1e-9)])
    U2 = np.vstack([U, CUVt]); I2 = np.vstack([I, CI.reshape(-1, 3) + nv])
    J2 = np.vstack([J, np.tile([HEAD, 0, 0, 0], (len(CP), 1))]); W2 = np.vstack([W, np.tile([255, 0, 0, 0], (len(CP), 1))])
    assert len(V2) < 65536
    b64 = lambda a: base64.b64encode(a.tobytes()).decode()
    bio = io.BytesIO(); Image.fromarray(out.astype(np.uint8)).save(bio, 'JPEG', quality=88, subsampling=0)
    o = dict(d)
    o.update(vb=b64(np.round(V2 * 1000).astype(np.int16)), nb=b64(np.round(N2 * 127).astype(np.int8)),
             ub=b64(np.round(np.clip(U2, 0, 1) * 65535).astype(np.uint16)), ib=b64(I2.astype(np.uint16)),
             jb=b64(J2.astype(np.uint8)), wb=b64(np.clip(W2, 0, 255).astype(np.uint8)),
             tex='data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode())
    o.pop('cm', None)
    dst = f'models/{base}_memecape.json'
    json.dump(o, open(dst, 'w'), separators=(',', ':'))
    if preview: Image.fromarray(out.astype(np.uint8)).save(f'/tmp/memecape_tex_{base}.jpg', quality=88)
    print(dst, len(V2), 'verts', len(CP), 'crown verts', round(len(json.dumps(o)) / 1e6, 2), 'MB')


if __name__ == '__main__':
    for b, p in BODIES.items(): make(b, p, '--preview' in sys.argv)
