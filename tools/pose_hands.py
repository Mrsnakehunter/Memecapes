#!/usr/bin/env python3
"""Turn the character's hanging hands so the thumbs point forward (palms toward the legs),
and rebuild the hand tracks used to hold weapons and shields.

The rig's hands hang with the backs of the hands facing forward, which makes a gripped
weapon point across the body. Rotating the hand bones a quarter turn about the forearm
gives a natural carry: a sword gripped across the palm points forward.

usage: python3 tools/pose_hands.py models/player.json [degrees]
Run it on the ORIGINAL model (git show 7939487:models/player.json); it does not undo itself.
"""
import json, sys, numpy as np

path = sys.argv[1]
deg = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
d = json.load(open(path))
nj = d['nj']
RH, RF, LH, LF = 16, 17, 11, 12  # right hand, right fingers, left hand, left fingers


def m44(a):
    return np.vstack([np.array(a, dtype=float).reshape(3, 4), [0, 0, 0, 1]])


def ry(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])


# hand frames in the bind pose, recovered from the existing right-hand track
clip = [c for c in d['an'] if c['n'] == 'Walking'][0]
Bs = []
for fi, h in enumerate(clip['hand']):
    S = m44(np.array(clip['f'][fi], dtype=float).reshape(nj, 12)[RH])
    Bs.append(np.linalg.inv(S) @ m44(h))
BR = np.mean(Bs, axis=0)
U, _, Vt = np.linalg.svd(BR[:3, :3]); BR[:3, :3] = U @ Vt
MIR = np.diag([-1, 1, 1, 1.0])
BL = MIR @ BR @ MIR
t = np.radians(deg)
for c in d['an']:
    F = [np.array(f, dtype=float).reshape(nj, 12) for f in c['f']]
    nf, hand, handL = [], [], []
    for fr in F:
        S = [m44(fr[j]) for j in range(nj)]
        for H, Fg, B, sgn in ((RH, RF, BR, 1), (LH, LF, BL, 1)):
            Rw = S[H] @ B @ ry(sgn * t) @ np.linalg.inv(B) @ np.linalg.inv(S[H])
            S[H] = Rw @ S[H]; S[Fg] = Rw @ S[Fg]
        nf.append([round(float(x), 4) for j in range(nj) for x in S[j][:3].reshape(-1)])
        hand.append([round(float(x), 4) for x in (S[RH] @ BR)[:3].reshape(-1)])
        handL.append([round(float(x), 4) for x in (S[LH] @ BL)[:3].reshape(-1)])
    c['f'], c['hand'], c['handL'] = nf, hand, handL
json.dump(d, open(path, 'w'), separators=(',', ':'))
print(path, 'hands turned', deg, 'degrees; clips:', [c['n'] for c in d['an']])
