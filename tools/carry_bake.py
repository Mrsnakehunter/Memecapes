#!/usr/bin/env python3
"""Bake the weapon carry into the standing, walking and running motions: the right HAND turns with the blade.

Before (tools/carry.js), only the weapon was turned at the grip while the hand kept the animation's pose, so the
wrist looked bent backwards (Albert: "his hand is broken and bent backwards"). Now the hand bone (and whatever hangs
off it) is rotated in the clip itself, about the grip, so the blade's length axis points along CARRY (body frame: x
right-to-left, y up, z forward; the hand's y axis is the blade) and the wrist follows. The 'hand' grip track turns
the same way, so the weapon still sits in the hand, and nothing is done at run time (carry.js keeps only the staff).
usage: python3 tools/carry_bake.py [--carry x,y,z] [models...]   (default: every player body and armour set)
"""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, 'tools')
import rigkit as K

CARRY = np.array([-.05, -.55, .83])          # blade tip forward, angled down (standing / walking / running)
RH, RHE = 16, 17                               # RightHand, RightHand_End
CLIPS = ('Idle', 'Walking', 'Running')


def blade_axis_local():
    """the sword's length axis in the hand's frame, as the game sets it at rest (qHold: M = R @ FOFF('f', REST, 20))"""
    a = -100 * np.pi / 180; b = 20 * np.pi / 180
    A = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    return (Ry @ Rx @ A)[:, 1]


BLADE = blade_axis_local()


def rot_to(c, g):
    c = c / np.linalg.norm(c); g = g / np.linalg.norm(g)
    v = np.cross(c, g); s2 = v @ v; co = c @ g
    if s2 < 1e-12: return np.eye(3)
    Kx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + Kx + Kx @ Kx * ((1 - co) / s2)


def bake(path, carry):
    d = json.load(open(path))
    done = []
    for c in d['an']:
        if c['n'] not in CLIPS or not c.get('hand'): continue
        F = K.clip_frames(c)
        H = np.array([np.vstack([np.array(h, float).reshape(3, 4), [0, 0, 0, 1]]) for h in c['hand']])
        for i in range(len(F)):
            R = H[i, :3, :3]; p = H[i, :3, 3]
            Q = rot_to(R @ BLADE, carry)
            Rw = np.eye(4); Rw[:3, :3] = Q; Rw[:3, 3] = p - Q @ p
            for b in (RH, RHE): F[i, b] = Rw @ F[i, b]
            H[i, :3, :3] = Q @ R
        hl = [np.vstack([np.array(h, float).reshape(3, 4), [0, 0, 0, 1]]) for h in c['handL']] if c.get('handL') else None
        c2 = K.pack_clip(c['n'], F, fps=c['fps'], hand=H, handL=hl, dur=c.get('dur'))
        c.update(c2); done.append(c['n'])
    d['carry'] = [round(float(x), 3) for x in carry]
    open(path, 'w').write(json.dumps(d, separators=(',', ':')))
    print(path, 'baked', done)


if __name__ == '__main__':
    args = sys.argv[1:]; carry = CARRY
    if args[:1] == ['--carry']: carry = np.array([float(x) for x in args[1].split(',')]); args = args[2:]
    paths = args or sorted(glob.glob('models/player*.json') + glob.glob('models/arm_lv??.json'))
    for p in paths: bake(p, carry)
