#!/usr/bin/env python3
"""Capes over armour: a cape-only model for each armour set (models/arm_lvNN_cape.json).

Capes are normally part of the caped bodies, so a player in armour (a separate 3D body) lost their cape. This builds
the MemeCape v3 cloth (tools/mkmemecape.py: shoulders to mid-calf, pleats, lining) around EACH armour body's own
standing pose and skin weights, as a model of its own with no body and no clips: in the game the cape borrows the
armour's animation matrices (same 28-bone rig, same bind), so it moves with the armour exactly.
Each file holds the cloth plus two paintings on the mkmemecape layout (sheet in the right half, lining bottom-left):
  texm  the MemeCape (meme patches, gold border), 2048 px
  texp  plain grey velvet with the gold border, 1024 px, tinted in the game to any cape colour (cm = tint mask)
usage: python3 tools/mkarmorcape.py [arm_lv40 ...]     (run from the repo root; default: every arm_lv*.json)
"""
import base64, glob, io, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'tools')
import rigkit
import mkmemecape as M

HEADARM = [9, 10, 11, 12, 14, 15, 16, 17, M.HEAD, 6, 7]


def build(base):
    path = f'models/{base}.json'
    d = json.load(open(path))
    m = rigkit.load(path)
    V, J, W = m['V'], m['J'], m['W']
    F0 = m['clips']['Idle'][0] if 'Idle' in m['clips'] else m['clips'][sorted(m['clips'])[0]][0]
    Vp = rigkit.skin(m, F0)
    dom = J[np.arange(len(J)), W.argmax(1)]
    body = ~np.isin(dom, HEADARM)
    Pg, ar, halfw = M.sheet(Vp, body)
    L = ar[-1]
    wts = M.weights(Pg, Vp, J, W)
    Pb = M.unskin(Pg, wts, F0)
    Ig = M.grid_tris(M.NU, M.NV, 0)
    Ng = M.vnormals(Pg.reshape(-1, 3), Ig)
    if Ng[:, 2].mean() > 0: Ng = -Ng
    Pin = M.unskin(Pg.reshape(-1, 3) - Ng * .006, wts, F0)
    # paintings
    faces = M.medallions()
    capeimg, npatch = M.paint(L, halfw, ar, faces)
    plainimg, mask = M.paint(L, halfw, ar, [], plain=True)
    TS = M.TS
    Tm = np.zeros((TS, TS, 3)); Tm[:, 1024:] = capeimg
    yy = np.arange(1024)[:, None]
    lining = np.array([88., 12, 24]) * (.85 + .15 * np.sin(yy / 1024 * 20))[..., None]
    Tm[1024:, :1024] = lining
    Tp = np.zeros((TS, TS, 3)); Tp[:, 1024:] = plainimg
    Tp[1024:, :1024] = np.array([120., 120, 120]) * (.85 + .15 * np.sin(yy / 1024 * 20))[..., None]
    CM = np.zeros((TS, TS)); CM[:, 1024:] = mask; CM[1024:, :1024] = 255
    # UVs (same mapping as mkmemecape)
    rr, cc = np.meshgrid(np.arange(M.NV), np.arange(M.NU), indexing='ij')
    s = (cc / (M.NU - 1)).ravel(); tcl = (ar[rr] / L).ravel()
    uo = np.c_[.5 + .5 * ((1 - s) * (1 - 2 / 1024) + 1 / 1024), tcl * (1 - 2 / 2048) + 1 / 2048]
    ui = np.c_[np.full(len(s), .25), .5 + .5 * np.clip(tcl, .02, .98)]
    nC = M.NU * M.NV
    Io = M.grid_tris(M.NU, M.NV, 0); Ii = M.grid_tris(M.NU, M.NV, nC, flip=True)
    tri0 = np.array(Io[:3])
    P3 = Pg.reshape(-1, 3)
    fn = np.cross(P3[tri0[1]] - P3[tri0[0]], P3[tri0[2]] - P3[tri0[0]])
    if fn[2] > 0:
        Io = M.grid_tris(M.NU, M.NV, 0, flip=True); Ii = M.grid_tris(M.NU, M.NV, nC)
    V2 = np.vstack([Pb, Pin])
    I2 = np.array(Io + Ii)
    N2 = M.vnormals(V2, I2)
    U3 = np.vstack([uo, ui])
    def jw(wl):
        b = [x[0] for x in wl] + [0] * (4 - len(wl)); w = [x[1] for x in wl] + [0] * (4 - len(wl))
        q = np.round(np.array(w) * 255).astype(int); q[0] += 255 - q.sum(); return b, q
    JWc = [jw(wl) for wl in wts]
    J2 = np.array([a for a, _ in JWc] * 2); W2 = np.array([b for _, b in JWc] * 2)
    b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    def jpg(T, size, q):
        im = Image.fromarray(np.clip(T, 0, 255).astype(np.uint8))
        if size != TS: im = im.resize((size, size), Image.LANCZOS)
        bio = io.BytesIO(); im.save(bio, 'JPEG', quality=q, subsampling=0)
        return 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()
    mk = Image.fromarray(np.clip(CM, 0, 255).astype(np.uint8)).resize((512, 512), Image.BILINEAR)
    bio = io.BytesIO(); mk.save(bio, 'PNG', optimize=True)
    o = dict(vb=b64(np.round(V2 * 1000).astype(np.int16)), nb=b64(np.round(N2 * 127).astype(np.int8)),
             ub=b64(np.round(np.clip(U3, 0, 1) * 65535).astype(np.uint16)), ib=b64(I2.astype(np.uint16)),
             jb=b64(J2.astype(np.uint8)), wb=b64(np.clip(W2, 0, 255).astype(np.uint8)), nj=d.get('nj', 28),
             texm=jpg(Tm, 2048, 86), texp=jpg(Tp, 1024, 84),
             cm='data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode())
    dst = f'models/{base}_cape.json'
    s_ = json.dumps(o, separators=(',', ':'))
    open(dst, 'w').write(s_)
    print(dst, 'patches', npatch, 'cape length %.2f m' % L, len(V2), 'verts', round(len(s_) / 1e6, 2), 'MB')


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob('models/arm_lv??.json'))
    for n in names: build(n)
