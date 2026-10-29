#!/usr/bin/env python3
"""The MemeCape v3: a real wide cape on the plain player bodies (models/player_memecape.json, playerf_memecape.json).

v1/v2 painted the MemeCape onto the caped bodies' own cape: a narrow strip cut into dozens of little texture
islands, so the meme pictures had to bunch up in the middle, came out small, and seams ran through them.

v3 builds its own cape and adds it to the plain body (same outfit, same 28-bone rig and motions):
  - a wide cloth that sits on the shoulders, falls over the shoulder blades and hangs to mid-calf, flaring
    out towards the hem, curved round the back, with soft pleats that deepen towards the hem;
  - designed in the standing pose (Idle, first frame) and turned back into the rest pose by inverting each
    vertex's own skin matrix, so it looks exactly as designed when the character stands;
  - the top follows the upper back and shoulders, the middle the spine and hips, and the lower part also
    follows the thighs a little, so it sways with every step instead of hanging stiff;
  - it has its own clean area of a 2048 texture (the body keeps its texture in one quarter), so the pattern is
    painted on one flat sheet: the game's own meme characters packed edge to edge in gold-corded patches on red
    velvet, a gold border and hem, a dark red lining inside;
  - the gold crown stays on the head bone.
usage: python3 tools/mkmemecape.py [--preview]       (run from the repo root)
"""
import base64, io, json, math, sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.spatial import cKDTree
sys.path.insert(0, 'tools')
import rigkit

BODIES = {'player': 'models/player.json', 'playerf': 'models/playerf.json'}
HEAD = 5                      # Head bone of the 28-bone rig
TS = 2048                     # texture size
ART = 'tools/art/memecape'
# the game's own meme characters, one per patch (portraits cut from their 3D renders)
FACES = ['bonk', 'shibe', 'popcat', 'froggo', 'mog_coin', 'floki', 'bouncy_hippo', 'gigachad', 'fartcoin', 'slerf',
         'nutty_the_squirrel', 'book_of_meme', 'golden_hound', 'lamp_genie', 'brainrot_jester', 'shiba_inu',
         'the_frozen_shibe', 'rich_wojak', 'snack_shibe']
BACKS = [(28, 92, 120), (92, 40, 128), (196, 98, 22), (26, 110, 64), (30, 64, 140), (150, 30, 40), (20, 120, 120),
         (120, 90, 20), (70, 30, 90)]

# cape shape (metres, standing pose; +y up, the back of the body is -z)
NU, NV = 25, 41               # grid across and down
TOP_Y, HEM_Y = 1.43, 0.30     # sits on the shoulders, hangs to mid-calf
HW_TOP, HW_HEM = .17, .34     # half width at the shoulders and at the hem
CLEAR = .035                  # gap kept between the cloth and the body
TORSO = {0, 1, 2, 3, 4, 8, 13}  # bones the upper cape may follow (no head, no arms)
LEG = {'L': 18, 'R': 23}      # LeftUpLeg (+x side), RightUpLeg (-x side)


def medallions():
    """128 px faces on jewel-coloured enamel (black studio backgrounds count as background)"""
    out = []
    yy, xx = np.mgrid[0:128, 0:128]; rr = np.hypot(xx - 63.5, yy - 63.5) / 64
    for i, n in enumerate(FACES):
        im = np.asarray(Image.open(f'{ART}/{n}.png').convert('RGBA')).astype(float)
        bc = np.array(BACKS[i % len(BACKS)], float)
        bg = bc[None, None] * (1.15 - .45 * rr[..., None])
        a = im[..., 3:4] / 255; rgb = im[..., :3]
        a = np.where((rgb.max(2, keepdims=True) < 26) & (a > .5), 0, a)
        out.append(rgb * a + bg * (1 - a))
    return out


def sample(img, px, py):
    return np.stack([map_coordinates(img[..., c], [py, px], order=1, mode='nearest') for c in range(3)], -1)


# ---------------------------------------------------------------- geometry
def back_z(B, y, hw):
    """the back of the body at height y across |x| < hw (the furthest-back point), or None"""
    s = (np.abs(B[:, 1] - y) < .035) & (np.abs(B[:, 0]) < hw)
    return B[s, 2].min() if s.any() else None


def sheet(Vp, body):
    """the cape's points in the standing pose, (NV, NU, 3), plus arc length along it and its half widths"""
    B = Vp[body]
    ys = np.linspace(TOP_Y, HEM_Y, 200)
    hw = lambda y: HW_TOP + (HW_HEM - HW_TOP) * ((TOP_Y - y) / (TOP_Y - HEM_Y)) ** .8
    # centre line: from on top of the shoulders, back over the shoulder blades, then straight down past the
    # bottom and the backs of the legs; never closer to the body than CLEAR, and it never comes forward again
    zc = []; z_run = None
    for i, y in enumerate(ys):
        zb = back_z(B, y, hw(y) * .8)
        if y > TOP_Y - .04:                           # the first few cm lie on top of the shoulders
            z = (zb if zb is not None else -.1) + .01
        else:
            z = (zb if zb is not None else z_run) - CLEAR
        z_run = z if z_run is None else min(z_run, z)
        t = (TOP_Y - y) / (TOP_Y - HEM_Y)
        zc.append(z_run - .07 * max(0, t - .35) ** 1.3)  # a little flare out at the hem
    zc = np.array(zc)
    # smooth it, then put the rows evenly along the cloth (arc length), not evenly in height
    k = np.ones(9) / 9; zc = np.convolve(np.pad(zc, 4, mode='edge'), k, 'valid')
    seg = np.hypot(np.diff(ys), np.diff(zc)); arc = np.r_[0, np.cumsum(seg)]
    L = arc[-1]
    ar = np.linspace(0, L, NV)
    ry, rz = np.interp(ar, arc, ys), np.interp(ar, arc, zc)
    P = np.zeros((NV, NU, 3))
    for r in range(NV):
        t = ar[r] / L; h = hw(ry[r])
        s = np.linspace(-1, 1, NU)
        x = s * h
        wrap = .055 + .03 * (1 - t)                   # the edges come forward round the body
        pleat = .016 * t ** 1.2 * np.cos(s * math.pi * 3.5) * (1 - .4 * np.abs(s))
        P[r, :, 0] = x
        P[r, :, 1] = ry[r] + .015 * t * np.abs(s) ** 2  # the corners hang a touch higher than the middle
        P[r, :, 2] = rz[r] + wrap * s ** 2 + pleat
    halfw = np.array([hw(y) for y in ry])
    return P, ar, halfw


def weights(Pg, Vp, J, W):
    """skin weights per cape point: the upper back/shoulders and spine/hips from the nearest torso vertex,
    the lower part also a little from each thigh (it swings with the stride)"""
    dom = J[np.arange(len(J)), W.argmax(1)]
    tor = np.nonzero(np.isin(dom, list(TORSO)))[0]
    tree = cKDTree(Vp[tor])
    out = []
    ymin = Pg[..., 1].min(); hip_y = .97
    for p in Pg.reshape(-1, 3):
        q = np.array([np.clip(p[0], -.14, .14), max(p[1], hip_y), p[2] + CLEAR])
        _, i = tree.query(q, k=6)
        acc = {}
        for ii in i:
            v = tor[ii]
            for b, w in zip(J[v], W[v]):
                if w > 0: acc[b] = acc.get(b, 0) + w / 6
        f = .38 * np.clip((hip_y - p[1]) / (hip_y - ymin), 0, 1) ** 1.1
        if f > 0:
            sl = 1 / (1 + math.exp(-p[0] / .07))           # +x = left leg
            for b in acc: acc[b] *= (1 - f)
            acc[LEG['L']] = acc.get(LEG['L'], 0) + f * sl
            acc[LEG['R']] = acc.get(LEG['R'], 0) + f * (1 - sl)
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top)
        out.append([(b, w / tot) for b, w in top])
    return out


def unskin(Pg, wts, F0):
    """standing-pose points -> rest-pose points (inverse of each point's own blended skin matrix)"""
    out = []
    for p, wl in zip(Pg.reshape(-1, 3), wts):
        M = sum(w * F0[b] for b, w in wl)
        out.append(np.linalg.solve(M, np.r_[p, 1])[:3])
    return np.array(out)


def grid_tris(nu, nv, base, flip=False):
    I = []
    for r in range(nv - 1):
        for c in range(nu - 1):
            a, b, d, e = base + r * nu + c, base + r * nu + c + 1, base + (r + 1) * nu + c, base + (r + 1) * nu + c + 1
            I += ([a, d, b, b, d, e] if not flip else [a, b, d, b, e, d])
    return I


def vnormals(V, I):
    N = np.zeros_like(V)
    T = np.array(I).reshape(-1, 3)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3): np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)


# ---------------------------------------------------------------- the painting (1024 x 2048 sheet)
GOLD_HI, GOLD_LO = np.array([255., 226, 120]), np.array([120., 76, 10])


def paint(L, halfw, ar, faces, ss=2):
    """the cape's sheet texture: x across (0..1 = left..right edge seen from behind), y down the cloth"""
    Wt, Ht = 1024 * ss, 2048 * ss
    t = (np.arange(Ht) + .5) / Ht
    hwt = np.interp(t * L, ar, halfw)                         # half width at each texel row
    s = (np.arange(Wt) + .5) / Wt
    X = (s[None, :] - .5) * 2 * hwt[:, None]                  # metres across, seen from behind
    Y = np.broadcast_to((t * L)[:, None], X.shape)            # metres down the cloth
    edge = np.abs(s[None, :] - .5) * 2                        # 0 middle .. 1 edge
    # red velvet: soft sheen and a tone-on-tone damask diamond, darker towards the hem
    sheen = .5 + .5 * np.sin(X * 9 + np.sin(Y * 4) * 1.5) * np.sin(Y * 6.5 + X * 3)
    q1, q2 = (X * 14 + Y * 14) % 1, (X * 14 - Y * 14) % 1
    dam = (np.minimum(np.minimum(q1, 1 - q1), np.minimum(q2, 1 - q2)) < .06)
    out = np.empty(X.shape + (3,))
    out[:] = np.array([140., 14, 30])
    out *= ((.9 + .2 * sheen) * (1 - .22 * t[:, None]) * np.where(dam, .86, 1))[..., None]
    BD, HEM, COL = .045, .065, .035                            # border, hem and collar band widths (m)
    in_hw = hwt - BD - .012
    # patches packed edge to edge like the website cape: hex rows, symmetric, every patch whole
    R, CORD, GAP = .052, .009, .008
    D = 2 * (R + CORD)
    hw_at = lambda y: min(np.interp(max(y - R, 0), t * L, in_hw), np.interp(min(y + R, L), t * L, in_hw))
    def count(y):
        w = 2 * hw_at(y)
        return max(0, int((w + GAP) // (D + GAP)))
    def place(y, n):
        if n == 1: return [0.]
        w = 2 * hw_at(y) - D
        step = min(w / (n - 1), (D + GAP) * 1.35)
        return [(k - (n - 1) / 2) * step for k in range(n)]
    # rows: as many patches as fit, alternating with one fewer so neighbouring rows interlock (hex packing);
    # rows that interlock sit closer together than rows that stack
    rows = []; y = max(COL + .012, .075) + R + CORD; prev = None      # the first cm fold over the shoulders
    while y + R + CORD < L - HEM - .01:
        n = count(y)
        if prev is not None and n == prev and n >= 2: n -= 1
        if n == 0: y += .01; continue
        rows.append((y, place(y, n)))
        nxt = y + (D + GAP) * .88
        n2 = count(nxt); n2 = n2 - 1 if (n2 == n and n2 >= 2) else n2
        y = nxt if n2 != n else y + D + GAP
        prev = n
    discs = [(x, y) for y, xs in rows for x in xs]
    # faces: never the same picture close together
    order = []; used = {}
    for i, (x, y) in enumerate(discs):
        best = None
        for f in sorted(range(len(faces)), key=lambda f: (len(used.get(f, [])), (f * 7 + i * 3) % len(faces))):
            if all(math.hypot(x - a, y - b) > 3.2 * (D + GAP) for a, b in used.get(f, [])):
                best = f; break
        if best is None: best = min(range(len(faces)), key=lambda f: len(used.get(f, [])))
        used.setdefault(best, []).append((x, y)); order.append(best)
    sh = (Ht / L)                                             # texels per metre down
    for (cx, cy), f in zip(discs, order):
        img = faces[f]
        r0 = int(max(0, (cy - R - CORD - .02) * sh)); r1 = int(min(Ht, (cy + R + CORD + .02) * sh))
        Xs, Ys = X[r0:r1], Y[r0:r1]
        dx, dy = -(Xs - cx), Ys - cy                           # (image x runs left to right seen from behind)
        d = np.hypot(dx, dy)
        o = out[r0:r1]
        shd = (d >= R + CORD) & (d < R + CORD + .014)
        o[shd] *= (.5 + .5 * ((d[shd] - R - CORD) / .014))[:, None]
        ring = (d >= R) & (d < R + CORD)
        tt = (d[ring] - R) / CORD; ang = np.arctan2(dy[ring], dx[ring])
        rope = .5 + .5 * np.sin(ang * 46 + tt * 6)
        prof = np.sin(tt * np.pi) ** .6
        o[ring] = GOLD_LO + (GOLD_HI - GOLD_LO) * (prof * (.4 + .6 * rope))[:, None]
        ins = d < R
        px = np.clip((dx[ins] / R + 1) / 2 * 127, 0, 127); py = np.clip((dy[ins] / R + 1) / 2 * 127, 0, 127)
        col = sample(img, px, py)
        e = d[ins] / R
        col *= (1 - .4 * np.clip((e - .9) / .1, 0, 1))[:, None]      # stitched dark line inside the cord
        col = col * .93 + 255 * .07 * (((px + py) % 3) < 1)[:, None] * 0  # (no fake stitches)
        o[ins] = col
    # gold border down both edges, hem and collar band, with engraved scroll and a dark inner line
    def goldband(mask, tt, along):
        scroll = .5 + .5 * np.sin(along + 1.4 * np.sin(along * .5 + tt * 3))
        lines = 1 - .32 * (np.abs(tt - .22) < .07) - .32 * (np.abs(tt - .78) < .07)
        g = (.74 + .26 * scroll) * (.75 + .25 * np.sin(tt * np.pi)) * lines
        out[mask] = np.array([236., 182, 62]) * g[mask][:, None]
    dside = hwt[:, None] - np.abs(X)                           # metres in from the side edge
    side = dside < BD; hem = Y > L - HEM; col_ = Y < COL
    goldband(side & ~hem & ~col_, np.clip(1 - dside / BD, 0, 1), Y * 70)
    goldband(hem, np.clip((Y - (L - HEM)) / HEM, 0, 1), X * 70)
    goldband(col_ & ~side, np.clip(Y / COL, 0, 1), X * 70)
    inner = ((dside >= BD) & (dside < BD + .006) & (Y >= COL) & (Y <= L - HEM)) | \
            ((Y <= L - HEM) & (Y > L - HEM - .006) & (dside >= BD)) | ((Y >= COL) & (Y < COL + .006) & (dside >= BD))
    out[inner] = np.array([70., 36, 4])
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1024, 2048), Image.LANCZOS)
    return np.asarray(img).astype(float), len(discs)


# ---------------------------------------------------------------- crown (gold ring with points on the head)
def crown(V, J, W, top):
    dom = J[np.arange(len(J)), W.argmax(1)]
    hd = V[dom == HEAD]
    yb = top - 0.115
    band = hd[np.abs(hd[:, 1] - (yb + .03)) < .02]
    cx, cz = (band[:, 0].min() + band[:, 0].max()) / 2, (band[:, 2].min() + band[:, 2].max()) / 2
    rx = (np.percentile(band[:, 0], 99) - np.percentile(band[:, 0], 1)) / 2 + .016
    rz = (np.percentile(band[:, 2], 97) - np.percentile(band[:, 2], 3)) / 2 + .012
    H = .05; P, N, UVc, I = [], [], [], []
    def add(p, n, uv): P.append(p); N.append(n); UVc.append(uv); return len(P) - 1
    n = 36
    for side in (1, -1):
        base = len(P)
        for i in range(n + 1):
            a = i / n * 2 * math.pi; s, c = math.sin(a), math.cos(a)
            for j, y in enumerate((yb, yb + H)):
                k = 1 + (.04 if side > 0 else 0)
                add([cx + rx * k * s, y, cz + rz * k * c], [side * s, 0, side * c], (i / n, j))
        for i in range(n):
            a0, a1, b0, b1 = base + i * 2, base + i * 2 + 1, base + i * 2 + 2, base + i * 2 + 3
            I += ([a0, b0, b1, a0, b1, a1] if side > 0 else [a0, b1, b0, a0, a1, b1])
    base = len(P)
    for i in range(n + 1):
        a = i / n * 2 * math.pi; s, c = math.sin(a), math.cos(a)
        add([cx + rx * 1.04 * s, yb + H, cz + rz * 1.04 * c], [0, 1, 0], (i / n, .9))
        add([cx + rx * s, yb + H, cz + rz * c], [0, 1, 0], (i / n, .9))
    for i in range(n):
        a0, a1, b0, b1 = base + i * 2, base + i * 2 + 1, base + i * 2 + 2, base + i * 2 + 3
        I += [a0, b1, b0, a0, a1, b1]
    for k in range(6):
        am = k / 6 * 2 * math.pi; a0, a1 = am - .3, am + .3
        p0 = [cx + rx * 1.02 * math.sin(a0), yb + H, cz + rz * 1.02 * math.cos(a0)]
        p1 = [cx + rx * 1.02 * math.sin(a1), yb + H, cz + rz * 1.02 * math.cos(a1)]
        tip = [cx + rx * 1.06 * math.sin(am), yb + H + .055, cz + rz * 1.06 * math.cos(am)]
        nn = [math.sin(am), .35, math.cos(am)]
        i0, i1, i2 = add(p0, nn, (.3, .9)), add(p1, nn, (.7, .9)), add(tip, nn, (.5, 1.))
        I += [i0, i1, i2, i0, i2, i1]
        add(tip, [0, 1, 0], (.5, 3.))
    return np.array(P), np.array(N), UVc, np.array(I)


def make(base, path, preview):
    d = json.load(open(path))
    m = rigkit.load(path)
    V, U, I, J, W = m['V'], m['UV'], m['I'], m['J'], m['W']
    Nn = rigkit.dec(d['nb'], np.int8).astype(float).reshape(-1, 3) / 127
    F0 = m['clips']['Idle'][0]
    Vp = rigkit.skin(m, F0)
    dom = J[np.arange(len(J)), W.argmax(1)]
    body = ~np.isin(dom, [9, 10, 11, 12, 14, 15, 16, 17, HEAD, 6, 7])   # torso + legs (arms and head left out)
    Pg, ar, halfw = sheet(Vp, body)
    L = ar[-1]
    wts = weights(Pg, Vp, J, W)
    Pb = unskin(Pg, wts, F0)
    # outer sheet + lining a few mm closer to the body (both faces drawn by their own triangles)
    Vo = Pb
    # lining: offset toward the body along the standing-pose normal, then unskinned with the same weights
    Ig = grid_tris(NU, NV, 0)
    Ng = vnormals(Pg.reshape(-1, 3), Ig)
    if Ng[:, 2].mean() > 0: Ng = -Ng                       # outer face points back (-z)
    Pin = unskin(Pg.reshape(-1, 3) - Ng * .006, wts, F0)
    # texture: body atlas in the top-left quarter, cape sheet in the right half, lining + crown bottom-left
    tex0 = np.asarray(Image.open(io.BytesIO(base64.b64decode(d['tex'].split(',')[1]))).convert('RGB').resize((1024, 1024), Image.LANCZOS)).astype(float)
    T = np.zeros((TS, TS, 3)); T[:1024, :1024] = tex0
    faces = medallions()
    capeimg, npatch = paint(L, halfw, ar, faces)
    T[:, 1024:] = capeimg
    yy = np.arange(1024)[:, None]
    T[1024:, :1024] = np.array([88., 12, 24]) * (.85 + .15 * np.sin(yy / 1024 * 20))[..., None]   # lining velvet
    # crown gold block at (32, 1056): 32 px
    bx, by = 32, 1056
    for k in range(20):
        tt = k / 19; T[by + k, bx:bx + 32] = np.array([250, 214, 96]) * (1 - tt) + np.array([168, 112, 18]) * tt
    T[by + 20:by + 26, bx:bx + 32] = [255, 236, 150]; T[by + 26:by + 32, bx:bx + 32] = [200, 16, 40]
    # UVs
    U2 = U * .5                                             # body into its quarter
    rr, cc = np.meshgrid(np.arange(NV), np.arange(NU), indexing='ij')
    s = (cc / (NU - 1)).ravel(); tcl = (ar[rr] / L).ravel()
    # seen from behind the sheet's +x is on the viewer's left; the painting's x=0 is the viewer's left
    uo = np.c_[.5 + .5 * (1 - (s * (1 - 2 / 1024) + 1 / 1024)), tcl * (1 - 2 / 2048) + 1 / 2048]
    uo[:, 0] = 1 - .5 * (s * (1 - 2 / 1024) + 1 / 1024) - 0  # x: s=0 (+x? no: -x side) handled below
    # Pg's s runs -1..1 = -x..+x; from behind (camera at -z looking +z) +x appears on the LEFT, so viewer-left
    # (painting x=0) is s=1: painting x = 1 - s
    uo[:, 0] = .5 + .5 * ((1 - s) * (1 - 2 / 1024) + 1 / 1024)
    ui = np.c_[np.full(len(s), .25), .5 + .5 * np.clip(tcl, .02, .98)]
    CP, CN, CUV, CI = crown(V, J, W, V[:, 1].max())
    def cuv(tv):
        u_, v_ = tv
        if v_ >= 3: return (bx + 16) / TS, (by + 29.5) / TS
        if v_ >= 2: return (bx + 16) / TS, (by + 23) / TS
        return (bx + 2 + u_ * 28) / TS, (by + 1 + (1 - min(v_, 1)) * 17) / TS
    CUVt = np.array([cuv(t) for t in CUV])
    nv0 = len(V); nC = NU * NV
    Io = grid_tris(NU, NV, nv0)
    Ii = grid_tris(NU, NV, nv0 + nC, flip=True)
    # winding: outer triangles must face back (-z) in the standing pose
    tri0 = np.array(Io[:3]) - nv0
    fn = np.cross(Pg.reshape(-1, 3)[tri0[1]] - Pg.reshape(-1, 3)[tri0[0]], Pg.reshape(-1, 3)[tri0[2]] - Pg.reshape(-1, 3)[tri0[0]])
    if fn[2] > 0:
        Io = grid_tris(NU, NV, nv0, flip=True); Ii = grid_tris(NU, NV, nv0 + nC)
    V2 = np.vstack([V, Vo, Pin, CP])
    Ivert = np.array(Io + Ii)
    Ncape = vnormals(V2, Ivert)
    N2 = np.vstack([Nn, Ncape[nv0:nv0 + 2 * nC], CN / np.maximum(np.linalg.norm(CN, axis=1, keepdims=True), 1e-9)])
    U3 = np.vstack([U2, uo, ui, CUVt])
    I2 = np.r_[I.ravel(), Ivert, CI + nv0 + 2 * nC]
    def jw(wl):
        b = [x[0] for x in wl] + [0] * (4 - len(wl)); w = [x[1] for x in wl] + [0] * (4 - len(wl))
        q = np.round(np.array(w) * 255).astype(int); q[0] += 255 - q.sum(); return b, q
    JWc = [jw(wl) for wl in wts]
    Jc = np.array([a for a, _ in JWc] * 2); Wc = np.array([b for _, b in JWc] * 2)
    Jo = np.asarray(rigkit.dec(d['jb'], np.uint8)).reshape(-1, 4).astype(int)
    Wo = np.asarray(rigkit.dec(d['wb'], np.uint8)).reshape(-1, 4).astype(int)
    J2 = np.vstack([Jo, Jc, np.tile([HEAD, 0, 0, 0], (len(CP), 1))])
    W2 = np.vstack([Wo, Wc, np.tile([255, 0, 0, 0], (len(CP), 1))])
    assert len(V2) < 65536
    b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    bio = io.BytesIO(); Image.fromarray(np.clip(T, 0, 255).astype(np.uint8)).save(bio, 'JPEG', quality=87, subsampling=0)
    o = dict(d)
    o.update(vb=b64(np.round(V2 * 1000).astype(np.int16)), nb=b64(np.round(N2 * 127).astype(np.int8)),
             ub=b64(np.round(np.clip(U3, 0, 1) * 65535).astype(np.uint16)), ib=b64(I2.astype(np.uint16)),
             jb=b64(J2.astype(np.uint8)), wb=b64(np.clip(W2, 0, 255).astype(np.uint8)),
             tex='data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode())
    o.pop('cm', None)
    dst = f'models/{base}_memecape.json'
    s_ = json.dumps(o, separators=(',', ':'))
    open(dst, 'w').write(s_)
    if preview: Image.fromarray(np.clip(T, 0, 255).astype(np.uint8)).save(f'/tmp/memecape_tex_{base}.jpg', quality=88)
    print(dst, 'patches', npatch, 'cape length %.2f m' % L, len(V2), 'verts', round(len(s_) / 1e6, 2), 'MB')


if __name__ == '__main__':
    for b, p in BODIES.items(): make(b, p, '--preview' in sys.argv)
