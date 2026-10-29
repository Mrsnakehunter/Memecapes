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
import base64, io, json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'tools')
os.environ.setdefault('CAPE_S', '2048')     # v2: a 2048 texture, so the medallions on the back are sharp
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
    """128 px round medallion faces on jewel-coloured enamel (float images, sampled smoothly)"""
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
    logo = emblem()
    return out, logo


def emblem():
    """the cape's crest: a gold crown and a bold M on red enamel (reads from across a town; the $CAPES logo full
    of tiny memes turned to mush at this size)"""
    from PIL import ImageDraw, ImageFont
    Z = 512; im = Image.new('RGB', (Z, Z), (120, 14, 26)); d = ImageDraw.Draw(im)
    yy, xx = np.mgrid[0:Z, 0:Z]; rr = np.hypot(xx - Z / 2, yy - Z / 2) / (Z / 2)
    a = np.asarray(im).astype(float) * (1.2 - .5 * rr[..., None]); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    G1, G2 = (255, 224, 120), (176, 116, 20)
    crown = [(120, 210), (150, 110), (200, 175), (256, 80), (312, 175), (362, 110), (392, 210)]
    d.polygon(crown + [(392, 236), (120, 236)], fill=G2); d.polygon([(p[0], p[1] + 6) for p in crown] + [(386, 228), (126, 228)], fill=G1)
    for x, y in ((150, 110), (256, 80), (362, 110)): d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=G1, outline=G2, width=4)
    d.ellipse((240, 196, 272, 228), fill=(40, 150, 90))
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 230)
    except Exception: f = ImageFont.load_default()
    d.text((259, 375), 'M', font=f, fill=G2, anchor='mm'); d.text((256, 370), 'M', font=f, fill=G1, anchor='mm')
    return np.asarray(im.resize((128, 128), Image.LANCZOS)).astype(float)


def sample(img, px, py):
    """bilinear look-up in a 128 px image"""
    from scipy.ndimage import map_coordinates
    return np.stack([map_coordinates(img[..., c], [py, px], order=1, mode='nearest') for c in range(3)], 1)


R, RING, LOGO_R = .074, .014, .1
BODY_R = {'player': .074, 'playerf': .06}
KX = 1.12     # the cape hangs narrower in play than in the model's rest pose: paint discs wider so they read round


def layout(top, ymin, half):
    """the coin under the collar, then rows of big medallions: as many per row as fit inside the border at that
    height (2 high up, 3 lower down where the cape is wider), staggered, never touching the border or the hem"""
    yl = top - .25
    discs = [(0., yl, LOGO_R, -1)]
    pitch_y = 2 * R + RING * 2 + .022
    cy = yl - LOGO_R - RING - .02 - R - RING
    k = 0; row = 0
    while cy - R - RING > ymin + .07:
        hw = np.interp(cy, *half) * .8
        avail = hw - (R + RING) / KX - .01
        n = 1 + int(2 * avail // (2 * (R + RING) / KX + .02)) if avail > 0 else 0
        if n > 1 and row % 2 and n % 2 == 0 and n > 2: n -= 1            # alternate counts so rows interlock
        step = min(2 * (R + RING) / KX + .04, 2 * avail / (n - 1)) if n > 1 else 0
        for i in range(n):
            discs.append(((i - (n - 1) / 2) * step, cy, R, k)); k += 1
        cy -= pitch_y; row += 1
    return discs


def pattern(X, Y, u, v, discs, faces, logo):
    """the MemeCape v2: deep red velvet with a soft sheen and small gold stars, big gold-roped medallions with the
    game's own meme characters, the MemeCapes coin under the collar, a wide gold baroque border and hem.
    X, Y in metres (X from the cape's middle, seen from behind +X is on the left)."""
    n = len(X)
    sheen = .5 + .5 * np.sin(X * 7.1 + np.sin(Y * 3.3) * 1.7) * np.sin(Y * 5.3 + X * 2.1)
    out = np.array([138., 14, 30])[None] * ((1 - .3 * v) * (.88 + .24 * sheen))[:, None]
    # small gold four-point stars on a staggered lattice
    gy = Y / .075; ry = np.round(gy); gx = X / .075 + (ry % 2) * .5; rx = np.round(gx)
    ddx, ddy = np.abs(gx - rx), np.abs(gy - ry)
    star = (ddx * ddy < .0016) & (ddx + ddy < .16)
    out[star] = out[star] * .35 + np.array([232., 180, 70]) * .65
    for cx, cy, r, k in discs:
        img = logo if k < 0 else faces[k % len(faces)]
        dx, dy = -(X - cx) * KX, (cy - Y)                           # image x runs left to right seen from behind
        d = np.hypot(dx, dy)
        sh = (d < r + RING + .016) & (d >= r + RING)                 # soft shadow round the patch
        out[sh] *= (.55 + .45 * ((d[sh] - r - RING) / .016))[:, None]
        ring = (d < r + RING) & (d >= r)
        t = (d[ring] - r) / RING
        ang = np.arctan2(dy[ring], dx[ring])
        rope = .5 + .5 * np.sin(ang * (34 if k >= 0 else 40) + t * 5.5)          # twisted gold cord
        prof = np.sin(t * np.pi) ** .6
        gold = np.array([120., 76, 10])[None] + (np.array([255., 226, 120]) - np.array([120., 76, 10]))[None] * (prof * (.45 + .55 * rope))[:, None]
        out[ring] = gold
        ins = d < r
        px = np.clip((dx[ins] / r + 1) / 2 * 127, 0, 127)
        py = np.clip((dy[ins] / r + 1) / 2 * 127, 0, 127)
        col = sample(img, px, py)
        edge = d[ins] / r
        col *= (1 - .35 * np.clip((edge - .88) / .12, 0, 1))[:, None]   # thin dark line inside the cord
        out[ins] = col
    # wide gold baroque border down both edges and along the hem, with a dark inner line
    edge = np.abs(u)
    side = edge > .87; hem = v > .94
    bd = side | hem
    t = np.where(side, (edge - .87) / .13, (v - .94) / .06)
    along = np.where(side, Y * 46, X * 46)
    scroll = .5 + .5 * np.sin(along + 1.2 * np.sin(along * .5))
    lines = 1 - .3 * (np.abs(t - .3) < .06) - .3 * (np.abs(t - .7) < .06)
    g = (.8 + .2 * scroll) * (.78 + .22 * np.sin(t * np.pi)) * lines
    out[bd] = np.array([238., 184, 62])[None] * g[bd][:, None]
    inner = ((edge > .85) & (edge <= .87) & ~hem) | ((v > .93) & (v <= .94) & ~side)
    out[inner] = np.array([84., 46, 6])
    return out


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


def tri_ids(U, I):
    """for every texel, the triangle that paints it (-1 = none)"""
    tid = np.full((S, S), -1, np.int32)
    for k, t in enumerate(I):
        uv = U[t] * S
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
        if x1 < x0 or y1 < y0: continue
        (ax, ay), (bx, by), (cx, cy) = uv
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        ins = (w0 >= -.02) & (w1 >= -.02) & (1 - w0 - w1 >= -.02)
        tid[ys[ins].astype(int), xs[ins].astype(int)] = k
    return tid


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
    # paint in the standing pose, not the rest pose: in the rest pose the cape is spread
    # wider in some places than others, so circles painted there turned into ovals when the character stands
    import rigkit
    rm = rigkit.load(path)
    fr = [f for c in ('Idle', 'Walking') for f in rm['clips'][c]]       # the cape's average shape while standing and walking
    Vp = np.mean([rigkit.skin(rm, f) for f in fr], 0)
    pm = posmap(Vp, U, I); nm = posmap(Nn, U, I)
    hi, lo = tex.max(2), tex.min(2)
    raw = ((cm > 200) | ((cm > 60) & (hi - lo < 45) & (hi > 70))) & ~np.isnan(pm[..., 0])
    # whole triangles: a triangle is cape when most of its texels are; then all its texels are painted, plus a
    # few texels of padding round each island (texels at island edges kept the old texture = red streaks)
    tid = tri_ids(U, I)
    ok = tid >= 0
    cnt = np.bincount(tid[ok], minlength=len(I)); hit = np.bincount(tid[ok & raw], minlength=len(I))
    capet = hit > .25 * np.maximum(cnt, 1)
    sel = np.zeros_like(raw); sel[ok] = capet[tid[ok]]
    from scipy.ndimage import binary_dilation
    sel = (sel | (binary_dilation(sel, iterations=3) & ~ok)) & ~np.isnan(pm[..., 0])
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
    vb = (np.arange(nb) + .5) / nb                                       # smooth edges between the height steps
    xl, xr = np.interp(v, vb, XL), np.interp(v, vb, XR)
    xc = (xl + xr) / 2
    u = np.clip(-(P[:, 0] - xc) / ((xr - xl) / 2), -1, 1)   # seen from behind, left to right
    ys = y1 - (np.arange(nb) + .5) / nb * (y1 - y0)                    # cape half-width at each height (for layout)
    half = (ys[::-1], ((XR - XL) / 2)[::-1])
    global R
    R = BODY_R[base]                      # the female cape is narrower: smaller medallions, more of them
    discs = layout(y1, y0, half)
    faces, logo = medallions()
    print(base, "medallions", len(discs) - 1)
    # 2x2 supersampling: each texel averages four points spread over its footprint (pm's change per texel)
    gx = np.nan_to_num(np.gradient(pm, axis=1))[sel]; gy = np.nan_to_num(np.gradient(pm, axis=0))[sel]
    lim = .012
    gx = np.clip(gx, -lim, lim); gy = np.clip(gy, -lim, lim)
    col = 0
    for ox, oy in ((-.25, -.25), (.25, -.25), (-.25, .25), (.25, .25)):
        Q = P + gx * ox + gy * oy
        col = col + pattern(Q[:, 0] - xc, Q[:, 1], u, v, discs, faces, logo) / 4
    lum = tex[sel].mean(1); g = np.clip(lum / np.percentile(lum, 70), .5, 1.15)[:, None]
    # the lining: texels facing the body AND behind the cape's outer surface at that spot (normals alone
    # flip in folds and painted red streaks through the medallions)
    bx_ = np.floor(P[:, 0] / .02).astype(int); by_ = np.floor(P[:, 1] / .02).astype(int)
    key = (bx_ - bx_.min()) * 10000 + (by_ - by_.min())
    uk, inv = np.unique(key, return_inverse=True)
    zmin = np.full(len(uk), np.inf); np.minimum.at(zmin, inv, P[:, 2])
    inner = (Nt[:, 2] > .35) & (P[:, 2] > zmin[inv] + .045)
    lining = np.array([92., 12., 24.]) * (.75 + .25 * (1 - v))[:, None]
    out = tex.copy()
    px = np.where(inner[:, None], lining, col * (.55 + .45 * g))
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
    bio = io.BytesIO(); Image.fromarray(out.astype(np.uint8)).save(bio, 'JPEG', quality=86, subsampling=0)
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
