#!/usr/bin/env python3
"""Turn the armour sets' splayed feet back to the front.

Albert (Nov 1): "when you put on the armour their feet point straight out to the sides" (worst on Paper Hands). The
armour sets play the same motions as the plain body, whose feet look right, but Meshy built their boots turned out,
so standing they splay 40-115 degrees (the plain body: 10-30). For every frame of every motion, each boot's heading
(from the foot bone's vertices to the toe bones' vertices, seen from above) is measured on the armour and on the plain
body (models/player2.json, same motion, same moment), and the foot + toe bones are turned about the vertical through
the ankle so the armour's boot points where the plain body's does.
usage: python3 tools/feet_fix.py [--dry] [models...]   (default: models/arm_lv??.json; run on unfixed models)
"""
import glob, json, sys
import numpy as np
sys.path.insert(0, 'tools')
import rigkit as K

REF = 'models/player2.json'
SKIP = ('Death', 'Kick')
FEET = (('L', 19, 20, (21, 22)), ('R', 24, 25, (26, 27)))


def parts(m):
    dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
    out = {}
    for s, leg, ft, toe in FEET:
        fi = np.where(dom == ft)[0]; ti = np.where(np.isin(dom, toe))[0]
        if len(ti) < 20:   # boot skinned to the foot bone only: its front third stands in for the toes
            z = m['V'][fi, 2]; cut = np.quantile(z, .7); ti = fi[z >= cut]; fi = fi[z < cut]
        ank = np.where(np.isin(dom, (leg, ft)) & (m['V'][:, 1] < .2))[0]
        out[s] = (fi, ti, ank)
    return out


def skin_sub(m, S, idx):
    V = np.c_[m['V'][idx], np.ones(len(idx))]; J = m['J'][idx]; W = m['W'][idx]
    out = np.zeros((len(idx), 3))
    for k in range(4): out += W[:, k:k + 1] * np.einsum('nij,nj->ni', S[J[:, k]][:, :3, :], V)
    return out


def heading(m, S, fi, ti):
    """(heading about the vertical, how flat the boot is: 1 = flat, 0 = pointing straight down/up)"""
    v = skin_sub(m, S, ti).mean(0) - skin_sub(m, S, fi).mean(0)
    return np.arctan2(v[0], v[2]), np.hypot(v[0], v[2]) / max(np.linalg.norm(v), 1e-9)


def fix(path, ref, rp, dry=False):
    m = K.load(path); d = m['d']; pp = parts(m); rep = {}
    for c in d['an']:
        if c['n'] not in ref['clips'] or c['n'] in SKIP: continue
        F = K.clip_frames(c); RF = ref['clips'][c['n']]; worst = [0, 0]
        for i in range(len(F)):
            j = min(len(RF) - 1, round(i * (len(RF) - 1) / max(1, len(F) - 1)))
            for k, (s, leg, ft, toe) in enumerate(FEET):
                fi, ti, ank = pp[s]
                (want, fw), (have, fh) = heading(ref, RF[j], *rp[s][:2]), heading(m, F[i], fi, ti)
                if min(fw, fh) < .5: continue          # boot pointing down or up: its heading means nothing
                t = (want - have + np.pi) % (2 * np.pi) - np.pi
                worst[k] = max(worst[k], round(abs(np.degrees(t))))
                if dry or abs(t) < np.radians(2): continue
                R = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
                p = skin_sub(m, F[i], ank).mean(0); p[1] = 0
                T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p - R @ p
                for b in (ft,) + toe: F[i, b] = T @ F[i, b]
        rep[c['n']] = worst
        if not dry: c.update(K.pack_clip(c['n'], F, fps=c['fps'], dur=c.get('dur')))
    if not dry: open(path, 'w').write(json.dumps(d, separators=(',', ':')))
    print(path, 'largest turn per foot (deg):', rep)


if __name__ == '__main__':
    a = sys.argv[1:]; dry = '--dry' in a; a = [x for x in a if x != '--dry']
    ref = K.load(REF); rp = parts(ref)
    for p in a or sorted(glob.glob('models/arm_lv??.json')): fix(p, ref, rp, dry)
