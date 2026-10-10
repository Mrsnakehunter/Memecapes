#!/usr/bin/env python3
"""Add Meshy animations to a character that is already in the game.

Meshy rigs every humanoid with the same 28-bone skeleton, so an animation downloaded from Meshy's
animation library for a character lines up with that character's model here. This script reads the
animations out of one or more GLB files and appends them as clips; the mesh is left alone.

usage:
  python3 tools/addclips.py models/player.json Attack=attack.glb Death=death.glb Wave=wave.glb ...
  python3 tools/addclips.py models/player.json --list some.glb          (show the animations inside a GLB)
  NAME=file.glb       take the first animation in the file and call it NAME in the game
  NAME=file.glb:Anim  take the animation called Anim inside the file

Clip names the game knows (see tools/patch_anim.py): Idle, Attack, Punch, Kick, Hit, Death, Chop, Mine,
Fish, Cook, Cast, Jump, Pickup, and one per emote (Stonks, GG, Ratio, Moon, Panic Sell, Cope, LOL, Wave,
Yes, No, Hmm, Shrug, Dance, Griddy, Spin, Headbang, Rage, Come Here, Bored, Mwah, Clap, Sigma).
A clip that already exists is replaced. Characters with weapon hand tracks (the player models) get the
same hand turn as tools/pose_hands.py, so held weapons sit the same in every animation.
"""
import json, struct, sys
import numpy as np

FPS = 12
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
RH, RF, LH, LF = 16, 17, 11, 12          # right hand, right fingers, left hand, left fingers (Meshy rig)
HAND_TURN = 90.0                         # degrees, as in pose_hands.py


def load(path):
    d = open(path, 'rb').read(); assert d[:4] == b'glTF', path + ' is not a GLB'
    off, J, B = 12, None, None
    while off < len(d):
        ln, ty = struct.unpack('<II', d[off:off + 8]); ch = d[off + 8:off + 8 + ln]
        if ty == 0x4E4F534A: J = json.loads(ch)
        elif ty == 0x004E4942: B = ch
        off += 8 + ln
    return J, B


def acc(J, B, i):
    a = J['accessors'][i]; bv = J['bufferViews'][a['bufferView']]
    n, c, dt = a['count'], NC[a['type']], np.dtype(CT[a['componentType']])
    st = bv.get('byteStride') or c * dt.itemsize
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    raw = np.frombuffer(B, np.uint8, count=st * (n - 1) + c * dt.itemsize, offset=base)
    out = np.lib.stride_tricks.as_strided(raw, (n, c * dt.itemsize), (st, 1)).copy().view(dt).reshape(n, c)
    if a.get('normalized') and dt.kind in 'iu': out = out.astype(np.float64) / np.iinfo(dt).max
    return out.astype(np.float64)


def quat(q):
    x, y, z, w = q / (np.linalg.norm(q) or 1)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s):
    M = np.eye(4); M[:3, :3] = quat(np.asarray(r, float)) * np.asarray(s, float); M[:3, 3] = t; return M


def slerp(a, b, f):
    d = float(np.dot(a, b))
    if d < 0: b, d = -b, -d
    if d > .9995: q = a + f * (b - a); return q / np.linalg.norm(q)
    th = np.arccos(d); return (np.sin((1 - f) * th) * a + np.sin(f * th) * b) / np.sin(th)


class Rig:
    def __init__(self, path):
        self.J, self.B = J, B = load(path)
        self.nodes = J['nodes']; n = len(self.nodes)
        self.parent = [-1] * n
        for i, nd in enumerate(self.nodes):
            for c in nd.get('children', []): self.parent[c] = i
        sk = J['skins'][0]; self.joints = sk['joints']
        self.ibm = acc(J, B, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1) if 'inverseBindMatrices' in sk else np.tile(np.eye(4), (len(self.joints), 1, 1))
        self.rest = [(np.array(nd.get('translation', [0, 0, 0]), float), np.array(nd.get('rotation', [0, 0, 0, 1]), float), np.array(nd.get('scale', [1, 1, 1]), float)) for nd in self.nodes]
        self.anims = J.get('animations', [])
        # the skinned mesh, for the size normalisation (height 1.7, base on the ground, centred)
        self.mesh = None
        for nd in self.nodes:
            if 'mesh' in nd and 'skin' in nd:
                pr = J['meshes'][nd['mesh']]['primitives'][0]; at = pr['attributes']
                self.mesh = (acc(J, B, at['POSITION']), acc(J, B, at['JOINTS_0']).astype(int), acc(J, B, at['WEIGHTS_0'])); break

    def globals(self, local):
        G = [None] * len(self.nodes)
        def g(i):
            if G[i] is None: G[i] = local[i] if self.parent[i] < 0 else g(self.parent[i]) @ local[i]
            return G[i]
        for i in range(len(self.nodes)): g(i)
        return G

    def pose(self, anim, t):
        tr = {i: list(v) for i, v in enumerate(self.rest)}
        for ch in (anim['channels'] if anim else []):
            nd, path = ch['target'].get('node'), ch['target']['path']
            if nd is None or path not in ('translation', 'rotation', 'scale'): continue
            sm = anim['samplers'][ch['sampler']]; T = acc(self.J, self.B, sm['input']).ravel(); V = acc(self.J, self.B, sm['output'])
            interp = sm.get('interpolation', 'LINEAR')
            if interp == 'CUBICSPLINE': V = V[1::3]
            if t <= T[0]: v = V[0]
            elif t >= T[-1]: v = V[-1]
            else:
                k = int(np.searchsorted(T, t) - 1); f = (t - T[k]) / ((T[k + 1] - T[k]) or 1)
                v = V[k] if interp == 'STEP' else (slerp(V[k], V[k + 1], f) if path == 'rotation' else V[k] + f * (V[k + 1] - V[k]))
            tr[nd][{'translation': 0, 'rotation': 1, 'scale': 2}[path]] = np.asarray(v, float)
        G = self.globals([trs(*tr[i]) for i in range(len(self.nodes))])
        return np.array([G[j] @ self.ibm[k] for k, j in enumerate(self.joints)])

    def norm(self):
        """The same normalisation the characters were brought in with: bind pose 1.7 tall, feet at 0, centred."""
        P, Jn, Wt = self.mesh; S = self.pose(None, 0)
        Ph = np.c_[P, np.ones(len(P))]
        Q = np.zeros((len(P), 3))
        for k in range(4): Q += Wt[:, k:k + 1] * np.einsum('nij,nj->ni', S[Jn[:, k]], Ph)[:, :3]
        lo, hi = Q.min(0), Q.max(0); s = 1.7 / (hi[1] - lo[1])
        N = np.eye(4) * s; N[3, 3] = 1; N[:3, 3] = -s * np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])
        return N


def m44(a): return np.vstack([np.array(a, float).reshape(3, 4), [0, 0, 0, 1]])


def ry(t):
    c, s = np.cos(t), np.sin(t); return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])


def main():
    if len(sys.argv) >= 4 and sys.argv[2] == '--list':
        for p in sys.argv[3:]:
            r = Rig(p); print(p, 'joints', len(r.joints), 'animations:', [(a.get('name'), round(max(acc(r.J, r.B, s['input']).max() for s in a['samplers']), 2)) for a in r.anims])
        return
    dst = sys.argv[1]; d = json.load(open(dst)); nj = d['nj']
    has_hands = any('hand' in c for c in d.get('an', []))
    if has_hands:
        wc = next(c for c in d['an'] if c['n'] == 'Walking')
        Bs = [np.linalg.inv(m44(np.array(wc['f'][i]).reshape(nj, 12)[RH])) @ m44(h) for i, h in enumerate(wc['hand'])]
        BR = np.mean(Bs, axis=0); U, _, Vt = np.linalg.svd(BR[:3, :3]); BR[:3, :3] = U @ Vt
        MIR = np.diag([-1, 1, 1, 1.0]); BL = MIR @ BR @ MIR; th = np.radians(HAND_TURN)
    for arg in sys.argv[2:]:
        name, src = arg.split('=', 1); src, _, want = src.partition(':')
        r = Rig(src); assert len(r.joints) == nj, f'{src} has {len(r.joints)} bones, the model has {nj}: not the same rig'
        an = [a for a in r.anims if not want or a.get('name') == want]; assert an, f'no animation {want!r} in {src}'
        an = an[0]; dur = max(acc(r.J, r.B, s['input']).max() for s in an['samplers'])
        N = r.norm(); Ni = np.linalg.inv(N); nf = max(2, int(round(dur * FPS)) + 1)
        F, hand, handL = [], [], []
        for i in range(nf):
            S = [N @ M @ Ni for M in r.pose(an, min(dur, i / FPS))]
            if has_hands:
                for H, Fg, Bm in ((RH, RF, BR), (LH, LF, BL)):
                    Rw = S[H] @ Bm @ ry(th) @ np.linalg.inv(Bm) @ np.linalg.inv(S[H]); S[H] = Rw @ S[H]; S[Fg] = Rw @ S[Fg]
                hand.append([round(float(x), 4) for x in (S[RH] @ BR)[:3].reshape(-1)])
                handL.append([round(float(x), 4) for x in (S[LH] @ BL)[:3].reshape(-1)])
            F.append([round(float(x), 4) for j in range(nj) for x in S[j][:3].reshape(-1)])
        clip = {'n': name, 'fps': FPS, 'f': F, 'dur': round(float(dur), 3)}
        if has_hands: clip['hand'], clip['handL'] = hand, handL
        d['an'] = [c for c in d.get('an', []) if c['n'] != name] + [clip]
        print(f'{dst}: {name} <- {src} ({an.get("name")}, {dur:.2f}s, {nf} frames)')
    json.dump(d, open(dst, 'w'), separators=(',', ':'))
    print(dst, 'clips:', [c['n'] for c in d['an']])


if __name__ == '__main__':
    main()
