#!/usr/bin/env python3
"""Bring a rigged Meshy character (GLB with skin + animations) into the game as an animated model.

usage: python3 tools/glb2rig.py rigged.glb models/KEY.json [--hands-from models/player.json] [--tex 1024]

Output: the game's packed model (vb/nb/ub/ib/tex) plus jb/wb (4 joints and weights per vertex),
nj (joint count) and an (one clip per animation in the GLB, sampled at 12 fps).
Characters are scaled to 1.7 tall, feet on the ground, centred (same as tools/addclips.py).
--hands-from: copy the weapon grip from an existing player model so held weapons and shields sit the
same way; the hands get the same quarter turn as tools/pose_hands.py (hand bone and all its fingers).
Works for any number of bones (Meshy's newer rig has 66 with fingers, the older one 28).
"""
import argparse, base64, io, json, sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import addclips as A

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--hands-from'); ap.add_argument('--tex', type=int, default=1024); ap.add_argument('--q', type=int, default=82)
a = ap.parse_args()

r = A.Rig(a.src); J, B = r.J, r.B
names = [r.nodes[j].get('name', '') for j in r.joints]; nj = len(names)
mesh_node = next(nd for nd in r.nodes if 'mesh' in nd and 'skin' in nd)
pr = J['meshes'][mesh_node['mesh']]['primitives'][0]; at = pr['attributes']
P = A.acc(J, B, at['POSITION']); Nn = A.acc(J, B, at['NORMAL']); UV = A.acc(J, B, at['TEXCOORD_0'])
JI = A.acc(J, B, at['JOINTS_0']).astype(int); WT = A.acc(J, B, at['WEIGHTS_0']); IX = A.acc(J, B, pr['indices']).ravel().astype(int)
assert len(P) < 65536, 'too many vertices'
N = r.norm(); Ni = np.linalg.inv(N)
V = (np.c_[P, np.ones(len(P))] @ N.T)[:, :3]
Nn = Nn / np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
# weights: keep 4, normalise, pack to bytes so they still sum to 255
WT = WT / np.maximum(WT.sum(1, keepdims=True), 1e-9); wb = np.floor(WT * 255).astype(int)
for i in range(len(wb)): wb[i, np.argmax(WT[i])] += 255 - wb[i].sum()
# texture
mat = J['materials'][pr['material']]; ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
im = J['images'][J['textures'][ti]['source']]; bv = J['bufferViews'][im['bufferView']]
img = Image.open(io.BytesIO(B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')
bio = io.BytesIO(); img.resize((a.tex, a.tex), Image.LANCZOS).save(bio, 'JPEG', quality=a.q)
b64 = lambda arr: base64.b64encode(arr.tobytes()).decode()
out = {'vb': b64(np.round(V * 1000).astype(np.int16)), 'nb': b64(np.round(Nn * 127).astype(np.int8)),
       'ub': b64(np.round(np.clip(UV, 0, 1) * 65535).astype(np.uint16)), 'ib': b64(IX.astype(np.uint16)),
       'tex': 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode(),
       'jb': b64(JI.astype(np.uint8)), 'wb': b64(wb.astype(np.uint8)), 'nj': nj, 'an': []}

# weapon grip, from an existing model with hand tracks
BR = BL = None
if a.hands_from:
    d0 = json.load(open(a.hands_from)); n0 = d0['nj']; wc = next(c for c in d0['an'] if c['n'] == 'Walking')
    RH0 = 16 if n0 == 28 else None
    Bs = [np.linalg.inv(A.m44(np.array(wc['f'][i]).reshape(n0, 12)[RH0])) @ A.m44(h) for i, h in enumerate(wc['hand'])]
    BR = np.mean(Bs, axis=0); U, _, Vt = np.linalg.svd(BR[:3, :3]); BR[:3, :3] = U @ Vt
    G = [np.linalg.inv(r.ibm[k]) for k in range(nj)]
    RH, LH = names.index('RightHand'), names.index('LeftHand')
    BR[:3, 3] = (N @ G[RH])[:3, 3]             # grip at this model's own hand
    MIR = np.diag([-1, 1, 1, 1.0]); BL = MIR @ BR @ MIR; BL[:3, 3] = (N @ G[LH])[:3, 3]
    kids = {k: [] for k in range(nj)}; jpos = {j: k for k, j in enumerate(r.joints)}
    for k, j in enumerate(r.joints):
        p = r.parent[j]
        while p >= 0 and p not in jpos: p = r.parent[p]
        if p >= 0: kids[jpos[p]].append(k)
    def subtree(k):
        s = [k]
        for c in kids[k]: s += subtree(c)
        return s
    RT, LT = subtree(RH), subtree(LH); th = np.radians(A.HAND_TURN)

for an in r.anims:
    dur = max(A.acc(J, B, s['input']).max() for s in an['samplers']); nf = max(2, int(round(dur * A.FPS)) + 1)
    F, hand, handL = [], [], []
    for i in range(nf):
        S = [N @ M @ Ni for M in r.pose(an, min(dur, i / A.FPS))]
        if BR is not None:
            for H, T, Bm in ((RH, RT, BR), (LH, LT, BL)):
                Rw = S[H] @ Bm @ A.ry(th) @ np.linalg.inv(Bm) @ np.linalg.inv(S[H])
                for k in T: S[k] = Rw @ S[k]
            hand.append([round(float(x), 4) for x in (S[RH] @ BR)[:3].reshape(-1)])
            handL.append([round(float(x), 4) for x in (S[LH] @ BL)[:3].reshape(-1)])
        F.append([round(float(x), 4) for k in range(nj) for x in S[k][:3].reshape(-1)])
    clip = {'n': an.get('name', 'Anim'), 'fps': A.FPS, 'f': F, 'dur': round(float(dur), 3)}
    if BR is not None: clip['hand'], clip['handL'] = hand, handL
    out['an'].append(clip); print(f"clip {clip['n']}: {dur:.2f}s, {nf} frames")
json.dump(out, open(a.dst, 'w'), separators=(',', ':'))
ext = V.max(0) - V.min(0)
print(f'{a.dst}: {len(V)} verts, {len(IX)//3} tris, {nj} bones, size w{ext[0]:.2f} h{ext[1]:.2f} d{ext[2]:.2f}, {os.path.getsize(a.dst)//1024} KB')
