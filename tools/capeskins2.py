"""Cape skins for the Skin of the Month line-up (used by tools/capeskins.py).

Each pattern is f(u, v) -> rgb array: u = across the back (-1 left .. 1 right, seen from behind), v = down the cape
(0 at the collar .. 1 at the hem). The cape is about 0.7 m wide and 1.2 m long, so shapes that should look round use
metres: X = u * 0.35, Y = v * 1.2. Every pattern is our own design: no logos, no real brands.
"""
import math
import numpy as np


def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def M(u, v): return u * 0.35, v * 1.2


def noise(x, y, scale, seed=0, octaves=4):
    """smooth value noise 0..1 (fractal)"""
    out = np.zeros_like(x, float); amp = 1; tot = 0
    rng = np.random.default_rng(seed)
    for o in range(octaves):
        g = rng.random((512, 512)); s = scale * 2 ** o
        gx, gy = np.clip(x * s + 128, 0, 510), np.clip(y * s + 128, 0, 510)
        x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int); fx, fy = gx - x0, gy - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = g[y0, x0]; b = g[y0, x0 + 1]; c = g[y0 + 1, x0]; d = g[y0 + 1, x0 + 1]
        out += amp * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy); tot += amp; amp *= .5
    return out / tot


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]; return a * (1 - t) + b * t


def fill(u, c): return np.tile(hexc(c), u.shape + (1,))


def vgrad(u, v, top, bot): return mix(hexc(top), hexc(bot), v)


# ---------------------------------------------------------------- the patterns
def pond_lily(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#1d6b66', '#0c3a3d')
    out = out * (.9 + .2 * noise(X, Y, 6, 1)[..., None])
    rng = np.random.default_rng(11)
    for _ in range(26):
        cx, cy, r = rng.uniform(-.3, .3), rng.uniform(.05, 1.15), rng.uniform(.035, .07)
        a = np.arctan2(Y - cy, X - cx); d = np.hypot(X - cx, Y - cy)
        notch = (np.abs(((a - rng.uniform(0, 6.28)) + np.pi) % (2 * np.pi) - np.pi) < .35)
        pad = (d < r) & ~notch
        out[pad] = mix(hexc('#3f9b3a'), hexc('#7bc96a'), (1 - d[pad] / r))
        out[(d < r) & (d > r * .9) & ~notch] = hexc('#2a6b2a')
        if rng.random() < .35:   # a pink flower on some pads
            fd = np.hypot(X - cx - r * .2, Y - cy + r * .1); fa = np.arctan2(Y - cy + r * .1, X - cx - r * .2)
            pet = fd < r * .45 * (.6 + .4 * np.abs(np.cos(fa * 3)))
            out[pet] = hexc('#f6a6c8'); out[fd < r * .12] = hexc('#ffe27a')
    return out


def wow_plaid(u, v):
    X, Y = M(u, v)
    out = fill(u, '#eadbb0')
    def band(c, w, col, a):
        nonlocal out
        m = (np.abs(((c / w) % 1) - .5) < .22)
        out = np.where(m[..., None], out * (1 - a) + hexc(col) * a, out)
    band(X + .02, .16, '#d9a441', .55); band(Y, .16, '#d9a441', .55)
    band(X + .1, .16, '#7a5420', .35); band(Y + .08, .16, '#7a5420', .35)
    thin = (np.abs(((X / .16) % 1) - .5) < .03) | (np.abs(((Y / .16) % 1) - .5) < .03)
    out[thin] = hexc('#b8322b')
    return out


def stonks_arrow(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#06210f', '#020a05')
    grid = (np.abs(((X / .06) % 1) - .5) > .46) | (np.abs(((Y / .06) % 1) - .5) > .46)
    out[grid] = out[grid] * .5 + hexc('#1f7a3a') * .5
    # a rising zig-zag line from bottom left to top right
    pts = [(x * .72, .25 + (y - .25) * .85) for x, y in [(-.3, 1.1), (-.2, .9), (-.12, .98), (-.02, .7), (.06, .78), (.16, .45), (.22, .52), (.28, .22)]]
    best = np.full(X.shape, 9.)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0; t = np.clip(((X - x0) * dx + (Y - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        best = np.minimum(best, np.hypot(X - x0 - t * dx, Y - y0 - t * dy))
    glow = np.exp(-(best / .03) ** 2)[..., None]
    out = out * (1 - glow * .7) + hexc('#39ff88') * glow * .7
    out[best < .011] = hexc('#a8ffc8')
    # the arrowhead
    hx, hy = pts[-1]; rx, ry = X - hx, Y - hy
    al = math.atan2(-.3, .06)
    d = np.hypot(rx, ry); ang = np.arctan2(ry, rx)
    head = (d < .09) & (np.abs(((ang - (al + np.pi)) + np.pi) % (2 * np.pi) - np.pi) < .45)
    out[head] = hexc('#39ff88')
    return out


def bonk_stripes(u, v):
    X, Y = M(u, v)
    s = ((X * .9 + Y) / .09) % 1
    out = np.where((s < .5)[..., None], hexc('#d8262e'), hexc('#f6efe2'))
    shade = (.85 + .15 * np.cos(s * 2 * np.pi))[..., None]
    return out * shade


def rug_fringe(u, v):
    X, Y = M(u, v)
    out = fill(u, '#8e1622')
    # a navy diamond medallion with a gold outline, and a smaller one above and below
    for cy, s in ((.6, .2), (.22, .1), (.98, .1)):
        d = np.abs(X) / .75 + np.abs(Y - cy)
        out[d < s] = hexc('#1d2a5a'); out[(d < s) & (d > s * .88)] = hexc('#e2b44a'); out[d < s * .35] = hexc('#e2b44a')
    # little motifs
    m = (np.abs(((X / .07) % 1) - .5) < .1) & (np.abs(((Y / .07) % 1) - .5) < .1)
    out[m] = out[m] * .6 + hexc('#e9c27a') * .4
    # border bands
    edge = (np.abs(u) > .82)
    out[edge] = hexc('#1d2a5a'); out[(np.abs(u) > .82) & (np.abs(u) < .86)] = hexc('#e2b44a')
    out[edge & (np.abs(((Y / .05) % 1) - .5) < .15)] = hexc('#c23a3a')
    # cream tassels at the hem
    tas = (v > .93) & (np.abs(((X / .018) % 1) - .5) < .3)
    out[v > .93] = hexc('#4a0d14'); out[tas] = hexc('#efe4c8')
    return out


def hodl_frost(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#d9f1ff', '#5aa7d6')
    out = out * (.92 + .1 * noise(X, Y, 8, 3)[..., None])
    rng = np.random.default_rng(5)
    for _ in range(34):
        cx, cy, r = rng.uniform(-.32, .32), rng.uniform(0, 1.2), rng.uniform(.02, .05)
        dx, dy = X - cx, Y - cy; d = np.hypot(dx, dy); a = np.arctan2(dy, dx)
        arm = (d < r) & (np.abs(np.sin(3 * a)) * d < .004 + .002 * (r / .05))
        tip = (d < r) & (np.abs(d - r * .6) < .003) & (np.abs(np.sin(3 * a)) < .5)
        out[arm | tip] = hexc('#ffffff')
    return out


def moon_phases(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#0a1030', '#1b0d33')
    rng = np.random.default_rng(9)
    for _ in range(160):
        cx, cy = rng.uniform(-.35, .35), rng.uniform(0, 1.2); out[np.hypot(X - cx, Y - cy) < rng.uniform(.002, .005)] = hexc('#fff6d0')
    for i in range(7):   # new moon to full moon, down the back
        cy = .14 + i * .15; r = .055
        disc = np.hypot(X, Y - cy) < r
        k = i / 6
        off = 2 * r * (1 - k) + .001
        lit = disc & ~(np.hypot(X + off, Y - cy) < r)
        out[disc] = hexc('#2a2a4a'); out[lit] = hexc('#ffeaa0')
    return out


def chad_marble(u, v):
    X, Y = M(u, v)
    n = noise(X, Y, 3, 7, 5)
    vein = np.abs(np.sin((X * 9 + Y * 4 + n * 7) * math.pi))
    out = mix(hexc('#f4f1ea'), hexc('#d8d2c4'), noise(X, Y, 5, 2))
    out = mix(out, hexc('#c9a03a'), (vein < .05) * 1.0)
    out = mix(out, hexc('#8a8478'), ((vein > .05) & (vein < .09)) * .4)
    return out


def laser_grid(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#2a0845', '#05010d')
    # a striped sun in the upper half
    sd = np.hypot(X, Y - .38); sun = (sd < .2) & ~((Y > .38) & (np.abs(((Y - .38) / .035) % 1 - .5) < .18))
    out[sun] = mix(hexc('#ffd23f'), hexc('#ff3fa4'), np.clip((Y[sun] - .2) / .35, 0, 1))
    # a perspective grid on the lower half
    low = Y > .62; t = (Y - .6) / .6
    hz = np.abs(((np.log(np.maximum(t, 1e-3)) * 3.2) % 1) - .5) > .45
    vt = np.abs(((X / np.maximum(t, .05) / .12) % 1) - .5) > .45
    out[low & (hz | vt)] = hexc('#ff3fa4')
    return out


def shades_on(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#ff8fc4', '#c2437f')
    tw, th = .21, .19
    col = np.floor((X + 1) / tw)
    fx = ((X + 1) / tw % 1 - .5) * tw
    fy = (((Y + (col % 2) * th / 2) / th) % 1 - .5) * th        # metres from each tile's centre
    def lens(cx):   # a flat-topped lens, rounded at the bottom
        dx, dy = fx - cx, fy
        return ((np.abs(dx) < .036) & (dy > -.022) & (dy < 0)) | ((np.hypot(dx / .036, dy / .026) < 1) & (dy >= 0))
    sh = lens(-.042) | lens(.042) | ((np.abs(fx) < .012) & (np.abs(fy + .016) < .005)) | ((np.abs(fy + .019) < .005) & (np.abs(fx) < .082))
    out[sh] = hexc('#111111')
    for cx in (-.042, .042):    # a white glint on each lens
        out[sh & (np.abs((fx - cx + .012) + (fy + .004) * .9) < .004) & (fy > -.018) & (fy < .012)] = hexc('#ffffff')
    return out


def whale_waves(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#3b7fb8', '#0a2147')
    for k in range(9):
        y0 = .1 + k * .13; w = Y - (y0 + .03 * np.sin(X * 22 + k * 1.7))
        band = (w > 0) & (w < .09)
        out[band] = mix(hexc('#1d5a94'), hexc('#0e3466'), w[band] / .09)
        crest = (w > 0) & (w < .012); out[crest] = hexc('#e8f6ff')
    return out


def rocket_trail(u, v):
    X, Y = M(u, v)
    out = fill(u, '#05060f')
    rng = np.random.default_rng(3)
    for _ in range(120):
        out[np.hypot(X - rng.uniform(-.35, .35), Y - rng.uniform(0, 1.2)) < rng.uniform(.002, .004)] = hexc('#ffffff')
    w = .04 + .2 * np.clip((Y - .25) / .95, 0, 1)
    f = np.clip(1 - np.abs(X) / w, 0, 1) * (Y > .2) * (.75 + .25 * noise(X, Y * .5 - 0, 9, 8))
    flame = mix(mix(hexc('#ff4b1f'), hexc('#ffb23f'), f * 1.3), hexc('#fff3c0'), f ** 3 * 1.6)
    out = mix(out, flame, np.clip(f * 2.2, 0, 1))
    body = (np.abs(X) < .03) & (Y > .05) & (Y < .2); out[body] = hexc('#e6e6ee')
    out[(np.abs(X) < .03) & (Y < .07) & (np.abs(X) < (Y - .02) * .7)] = hexc('#c8102e')
    return out


def the_burn(u, v):
    X, Y = M(u, v)
    n = noise(X * 1.5, Y * .7, 6, 12, 5)
    h = (Y / 1.2) + (n - .5) * .7
    out = mix(hexc('#1a0402'), hexc('#c42a0a'), np.clip(h * 1.6 - .3, 0, 1))
    out = mix(out, hexc('#ffb22e'), np.clip(h * 2.2 - 1.2, 0, 1))
    out = mix(out, hexc('#fff0b0'), np.clip(h * 3 - 2.4, 0, 1))
    return out


def copium_crystal(u, v):
    X, Y = M(u, v)
    rng = np.random.default_rng(21); P = np.c_[rng.uniform(-.4, .4, 60), rng.uniform(-.1, 1.3, 60)]
    d = np.stack([np.hypot(X - px, Y - py) for px, py in P], -1); i = d.argmin(-1); ds = np.sort(d, -1)
    edge = (ds[..., 1] - ds[..., 0]) < .006
    shade = (.7 + .3 * rng.random(60))[i][..., None]
    out = fill(u, '#5d5a63') * shade
    crys = (i % 5 == 0)
    out[crys] = mix(hexc('#7b3fd6'), hexc('#d9b8ff'), (1 - ds[..., 0][crys] / .08))
    out[edge] = hexc('#2b2930')
    return out


def wen_lambo(u, v):
    X, Y = M(u, v)
    w = Y + .02 * np.sin(X * 18)
    c = ((np.floor(X / .07) + np.floor(w / .07)) % 2 == 0)
    out = np.where(c[..., None], hexc('#111111'), hexc('#f4f4f4'))
    return out * (.88 + .12 * np.sin(X * 18 + 1)[..., None])


def jungle_leaves(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#123d22', '#08210f')
    rng = np.random.default_rng(31)
    for _ in range(30):
        cx, cy, L, a = rng.uniform(-.35, .35), rng.uniform(0, 1.2), rng.uniform(.08, .16), rng.uniform(0, math.pi)
        dx, dy = X - cx, Y - cy; p = dx * math.cos(a) + dy * math.sin(a); q = -dx * math.sin(a) + dy * math.cos(a)
        leaf = (np.abs(p) < L) & (np.abs(q) < (L * .38) * np.sqrt(np.clip(1 - (p / L) ** 2, 0, 1)))
        col = mix(hexc('#2f8a3e'), hexc('#6cc24a'), rng.random() * np.ones_like(p))
        out[leaf] = col[leaf] * (.85 + .15 * (q[leaf] > 0))[..., None]
        out[leaf & (np.abs(q) < .003)] = hexc('#bfe8a0')
    return out


def up_only_rainbow(u, v):
    X, Y = M(u, v)
    cols = ['#e53935', '#fb8c00', '#fdd835', '#43a047', '#1e88e5', '#5e35b1']
    k = np.floor(((Y - X * 1.4) / .07) % 6).astype(int)
    pal = np.array([hexc(c) for c in cols])
    return pal[k] * (.9 + .1 * noise(X, Y, 10, 5))[..., None]


def comfy_knit(u, v):
    X, Y = M(u, v)
    row = np.floor(Y / .045); cols = [hexc('#c9b79c'), hexc('#8f3b2e'), hexc('#c9b79c'), hexc('#2e4a6b')]
    pal = np.array(cols); out = pal[(row % 4).astype(int)]
    vx = ((X / .03) % 1); vy = (Y / .045) % 1
    chev = np.abs(vx - .5) * 2
    stitch = (.75 + .25 * np.cos((vy - chev * .5) * 2 * np.pi))[..., None]
    return out * stitch


def royal_ermine(u, v):
    X, Y = M(u, v)
    out = vgrad(u, v, '#5a1a8a', '#2a0845')
    out = out * (.9 + .15 * noise(X, Y, 9, 14)[..., None])
    trim = (np.abs(u) > .8) | (v > .9)
    out[trim] = hexc('#f6f3ec')
    gx, gy = (X + 1) / .07, (Y + (np.floor((X + 1) / .07) % 2) * .045) / .09
    fx, fy = gx % 1 - .5, gy % 1 - .5
    tail = trim & (np.abs(fx) < .09 * (1 - fy)) & (fy > -.35) & (fy < .3)      # little black ermine tails
    out[tail] = hexc('#151515')
    return out


MONTHLY = {
    'pond_lily': pond_lily, 'wow_plaid': wow_plaid, 'stonks_arrow': stonks_arrow, 'bonk_stripes': bonk_stripes,
    'rug_fringe': rug_fringe, 'hodl_frost': hodl_frost, 'moon_phases': moon_phases, 'chad_marble': chad_marble,
    'laser_grid': laser_grid, 'shades_on': shades_on, 'whale_waves': whale_waves, 'rocket_trail': rocket_trail,
    'the_burn': the_burn, 'copium_crystal': copium_crystal, 'wen_lambo': wen_lambo, 'jungle_leaves': jungle_leaves,
    'up_only_rainbow': up_only_rainbow, 'comfy_knit': comfy_knit, 'royal_ermine': royal_ermine,
}
