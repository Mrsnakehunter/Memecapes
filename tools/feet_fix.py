#!/usr/bin/env python3
"""Turn the armour sets' splayed feet back to the front.

Albert (Nov 1): "when you put on the armour their feet point straight out to the sides". The motions are the same
ones the plain body uses (its feet look right); the difference is the meshes: Meshy built every armour set standing
with its toes turned ~22 degrees out in the bind pose (the plain body: ~0). So for each foot the splay is measured on
the bind mesh (principal axis of the boot vertices, seen from above) and taken out of EVERY frame of every motion by
turning the foot + toe bones in their bind space about the bind ankle. Run once per model (it reads the bind mesh, so
a second run measures ~0 and does nothing).
usage: python3 tools/feet_fix.py [--dry] [models...]   (default: models/arm_lv??.json)
"""
import glob, json, sys
import numpy as np
sys.path.insert(0, 'tools')
import rigkit as K

LEGS = {'L': (19, (20, 21, 22)), 'R': (24, (25, 26, 27))}


def splay(m, dom, fb):
    sel = np.isin(dom, fb) & (m['V'][:, 1] < .15)
    X = m['V'][sel][:, [0, 2]]; X = X - X.mean(0)
    a = np.linalg.svd(X, full_matrices=False)[2][0]
    if a[1] < 0: a = -a
    return float(np.degrees(np.arctan2(a[0], a[1])))     # + = toes turned toward +x (the character's left)


def fix(path, dry=False):
    m = K.load(path); d = m['d']
    dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
    T = {}
    for s, (leg, fb) in LEGS.items():
        ang = splay(m, dom, fb)
        if abs(ang) < 3: continue
        w = np.zeros(len(m['V']))
        for k in range(4): w += np.where(np.isin(m['J'][:, k], (leg, fb[0])), m['W'][:, k], 0) * (m['V'][:, 1] < .2)
        p = (m['V'] * w[:, None]).sum(0) / w.sum()
        t = np.radians(-ang); R = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = p - R @ p
        T[s] = (fb, M, round(ang, 1))
    print(path, 'bind splay (deg):', {s: v[2] for s, v in T.items()})
    if dry or not T: return
    for c in d['an']:
        F = K.clip_frames(c)
        for fb, M, _ in T.values():
            for b in fb: F[:, b] = F[:, b] @ M
        c.update(K.pack_clip(c['n'], F, fps=c['fps'], dur=c.get('dur')))
    open(path, 'w').write(json.dumps(d, separators=(',', ':')))


if __name__ == '__main__':
    a = sys.argv[1:]; dry = '--dry' in a; a = [x for x in a if x != '--dry']
    for p in a or sorted(glob.glob('models/arm_lv??.json')): fix(p, dry)
