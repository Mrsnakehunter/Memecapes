#!/usr/bin/env python3
"""Build the worn cape models from the MemeCapes cape artwork (tools/art/cape.webp).

  models/c_memecape.json  the MemeCape: the medallion cape, a hood over the head and a gold crown on the hood
  models/c_qcape.json     the Quest cape: the same cape without the hood and crown

Units are world units (the player is 1.7 tall, faces +z, back is -z), drawn at scale 1 at the player's feet.
Run from the repo root:  python3 tools/mkcape.py        (python3 tools/mkcape.py plain  makes only models/c_plain.json)
"""
import json, base64, io, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = Image.open('tools/art/cape.webp').convert('RGBA')
AW, AH = ART.size
alpha = np.array(ART)[..., 3] > 40

# ---------------- texture atlas (1024x1024): cape art on the left 768px, plain patches on the right
S = 1024
atlas = Image.new('RGB', (S, S), (74, 9, 16))
# cape art over a dark velvet red so the edges blend
bg = Image.new('RGBA', (768, 768), (74, 9, 16, 255))
art = ART.resize((768, int(768 * AH / AW)), Image.LANCZOS)
bg.alpha_composite(art, (0, 0))
atlas.paste(bg.convert('RGB'), (0, 0))
d = ImageDraw.Draw(atlas)
# patches: lining (dark red), gold, hood (red with gold trim)
d.rectangle((768, 0, 1023, 255), fill=(96, 12, 20))          # lining
d.rectangle((768, 256, 1023, 383), fill=(214, 168, 52))      # gold
d.rectangle((768, 384, 1023, 639), fill=(128, 16, 28))       # hood red
d.rectangle((768, 384, 783, 639), fill=(214, 168, 52))       # gold trim at the hood's front edge (u=0)
d.rectangle((1008, 384, 1023, 639), fill=(214, 168, 52))     # ... and the other side (u=1)
d.rectangle((768, 624, 1023, 639), fill=(214, 168, 52))      # ... and along the bottom edge (v=1)
d.rectangle((768, 640, 1023, 1023), fill=(60, 8, 14))        # dark (crown inside)
# a little velvet noise on the plain reds
noise = Image.effect_noise((256, 1024), 18).convert('L').filter(ImageFilter.GaussianBlur(1))
patch = atlas.crop((768, 0, 1024, 1024))
patch = Image.composite(patch, Image.eval(patch, lambda v: max(0, v - 14)), noise.point(lambda v: 255 if v > 128 else 0))
atlas.paste(patch, (768, 0))
bio = io.BytesIO(); atlas.save(bio, 'JPEG', quality=86)
TEX = 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()

# per-row extents of the cape art (in atlas pixels) so the cape's texture fills the painted silhouette
rows = {}
for y in range(AH):
    xs = np.where(alpha[y])[0]
    if len(xs): rows[y] = (xs.min(), xs.max())


def art_uv(u, t):
    """u 0..1 across the cape, t 0..1 from the shoulders down to the hem -> atlas uv."""
    Y = 78 + t * (690 - 78)
    y0 = int(Y); x0, x1 = rows.get(y0, (0, AW - 1))
    X = x0 + u * (x1 - x0)
    return (X / AW) * (768 / S), (Y / AH) * (768 / S)


P, N, U, I = [], [], [], []


def quad(a, b, c, dd):  # indices
    I.extend([a, b, c, a, c, dd])


def grid(fn, nu, nv, uvfn, flip=False):
    """fn(u,v)->(pos, normal); builds a (nu+1)x(nv+1) lattice."""
    base = len(P)
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv
            p, n = fn(u, v)
            if flip: n = [-x for x in n]
            P.append(p); N.append(n); U.append(uvfn(u, v))
    for j in range(nv):
        for i in range(nu):
            a = base + j * (nu + 1) + i; b = a + 1; c = a + nu + 2; dd = a + nu + 1
            if flip: quad(a, dd, c, b)
            else: quad(a, b, c, dd)


# ---------------- the cape: an arc around the body's axis, flaring out towards the hem
Y_TOP, Y_BOT = 1.42, 0.22


def cape_pt(u, v, inset=0.0):
    # v: 0 at the shoulders, 1 at the hem
    ease = v * v * (3 - 2 * v)
    # slim at the shoulders, hanging behind the body rather than wrapping round the legs
    r = 0.19 + (0.30 - 0.19) * ease - inset
    cz = -0.045 - 0.11 * ease
    phi_max = math.radians(82 + 10 * ease)
    phi = (u * 2 - 1) * phi_max
    y = Y_TOP + (Y_BOT - Y_TOP) * v + 0.04 * math.sin(math.pi * v) * math.cos(phi * 2)  # a gentle ripple
    x = r * math.sin(phi); z = cz - r * math.cos(phi)
    # outward normal (ignore the small ripple), tilted a little down because the cape flares
    n = [math.sin(phi), 0.22, -math.cos(phi)]
    ln = math.sqrt(sum(c * c for c in n)); n = [c / ln for c in n]
    return [x, y, z], n


def cape(flip_inner=True, plain=False):
    # plain: the outside maps straight onto the left 3/4 of the atlas (u across, v shoulders to hem), so the game can paint any design
    grid(lambda u, v: cape_pt(u, v), 28, 16, (lambda u, v: (0.74 * u + 0.005, 0.74 * v + 0.005)) if plain else (lambda u, v: art_uv(u, v)))
    # inner lining, a touch inside, normals flipped
    grid(lambda u, v: cape_pt(u, v, .012), 28, 16, lambda u, v: (0.76 + 0.24 * u, 0.02 + 0.2 * v), flip=True)


# ---------------- the hood: part of a sphere over the head, open at the front
HC = (0.0, 1.57, -0.045); HR = 0.215


def hood_pt(u, v):
    az = (u * 2 - 1) * math.radians(100)         # 0 = straight back
    th = v * math.radians(118)                    # 0 = top of the head
    # lower edge dips at the back (th 118deg) and rises towards the front
    th = th * (1 - 0.18 * (1 - math.cos(az)) / 2)
    x = HR * math.sin(th) * math.sin(az); y = HC[1] + HR * math.cos(th); z = HC[2] - HR * math.sin(th) * math.cos(az)
    # a peaked top, like the artwork: the crown sits around the peak
    pk = max(0.0, 1 - th / math.radians(34))
    y += 0.075 * pk * pk; z -= 0.02 * pk
    n = [math.sin(th) * math.sin(az), math.cos(th), -math.sin(th) * math.cos(az)]
    return [x, y, z], n


def hood():
    grid(hood_pt, 24, 10, lambda u, v: (0.76 + 0.24 * u, 0.376 + 0.248 * v))
    grid(lambda u, v: ((lambda p, n: ([p[0] - n[0] * .01, p[1] - n[1] * .01, p[2] - n[2] * .01], n))(*hood_pt(u, v))),
         24, 10, lambda u, v: (0.76 + 0.24 * u, 0.02 + 0.2 * v), flip=True)


# ---------------- the crown: a gold band with points, sitting on top of the hood
def crown():
    cy = HC[1] + HR - 0.01; R = 0.09; H = 0.055
    def band(u, v):
        a = u * 2 * math.pi; r = R + 0.004 * v
        return [r * math.sin(a), cy + H * v, -r * math.cos(a)], [math.sin(a), 0, -math.cos(a)]
    gold = lambda u, v: (0.76 + 0.24 * u, 0.26 + 0.1 * v)
    grid(band, 24, 1, gold)
    grid(lambda u, v: ((lambda p, n: (p, [-n[0], 0, -n[2]]))(*band(u, v))), 24, 1, lambda u, v: (0.76 + 0.24 * u, 0.64 + 0.3 * v), flip=True)
    # a plate for the top rim and 6 points
    for k in range(6):
        a0 = k / 6 * 2 * math.pi; a1 = (k + 1) / 6 * 2 * math.pi; am = (a0 + a1) / 2
        b = len(P)
        for a in (a0, a1):
            P.append([R * math.sin(a), cy + H, -R * math.cos(a)]); N.append([math.sin(a), .3, -math.cos(a)]); U.append(gold(0.5, 0.5))
        P.append([(R + .01) * math.sin(am), cy + H + 0.07, -(R + .01) * math.cos(am)]); N.append([math.sin(am), .5, -math.cos(am)]); U.append(gold(0.5, 0.9))
        I.extend([b, b + 1, b + 2, b, b + 2, b + 1])
        # a little ball on each point
        c = [(R + .01) * math.sin(am), cy + H + 0.08, -(R + .01) * math.cos(am)]
        bb = len(P)
        for j in range(3):
            for i in range(6):
                th = (j + 0.5) / 3 * math.pi; ph = i / 6 * 2 * math.pi
                n = [math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)]
                P.append([c[0] + n[0] * .012, c[1] + n[1] * .012, c[2] + n[2] * .012]); N.append(n); U.append(gold(0.5, 0.3))
        for j in range(2):
            for i in range(6):
                a = bb + j * 6 + i; b2 = bb + j * 6 + (i + 1) % 6; c2 = a + 6; d2 = b2 + 6
                I.extend([a, b2, d2, a, d2, c2])


def write(path):
    global P, N, U, I
    Pa = np.array(P, np.float64); Na = np.array(N, np.float64); Ua = np.clip(np.array(U, np.float64), 0, 1); Ia = np.array(I, np.uint32)
    Na /= np.maximum(np.linalg.norm(Na, axis=1, keepdims=True), 1e-9)
    assert len(Pa) < 65536
    b64 = lambda arr: base64.b64encode(arr.tobytes()).decode()
    out = {'vb': b64(np.round(Pa * 1000).astype(np.int16)), 'nb': b64(np.round(Na * 127).astype(np.int8)),
           'ub': b64(np.round(Ua * 65535).astype(np.uint16)), 'ib': b64(Ia.astype(np.uint16)), 'tex': TEX}
    json.dump(out, open(path, 'w'), separators=(',', ':'))
    print(path, len(Pa), 'verts', len(Ia) // 3, 'tris', 'y', round(Pa[:, 1].min(), 2), round(Pa[:, 1].max(), 2), len(json.dumps(out)) // 1024, 'KB')
    P, N, U, I = [], [], [], []


import sys
if 'plain' in sys.argv:
    # every other cape: the same shape, painted by the game (skill capes, Chad cape, custom capes from the shop)
    small = Image.new('RGB', (64, 64), (120, 20, 30)); bio2 = io.BytesIO(); small.save(bio2, 'JPEG', quality=70)
    TEX = 'data:image/jpeg;base64,' + base64.b64encode(bio2.getvalue()).decode()
    cape(plain=True); write('models/c_plain.json')
else:
    cape(); hood(); crown(); write('models/c_memecape.json')
    cape(); write('models/c_qcape.json')
    atlas.save('/home/claude/scratch/shots/cape_atlas.jpg', quality=80)
