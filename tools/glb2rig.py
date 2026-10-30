#!/usr/bin/env python3
"""Bring a rigged Meshy character (GLB with skin + animations) into the game as an animated model.

usage: python3 tools/glb2rig.py rigged.glb models/KEY.json [--hands-from tools/hands_ref.json] [--tex 1024]
                               [--map tools/clipmap.json] [--pack] [--drop-fingers]

Output: the game's packed model (vb/nb/ub/ib/tex) plus jb/wb (4 joints and weights per vertex),
nj (joint count) and an (one clip per animation in the GLB, sampled at 12 fps).
Characters are scaled to 1.7 tall, feet on the ground, centred (same as tools/addclips.py).
--hands-from: copy the weapon grip from an existing player model so held weapons and shields sit the
same way; the hands get the same quarter turn as tools/pose_hands.py (hand bone and all its fingers).
Works for any number of bones (Meshy's newer rig has 66 with fingers, the older one 28).
--map: rename Meshy's motions to the game's clip names (see tools/clipmap.json); motions not in the map are left out.
--pack: store frames as 16-bit numbers (about 3x smaller files).
--rig28: keep only the game's 28 bones in rigkit.NAMES order (for tools/npc_clips.py), everything else follows its parent.
--drop-fingers: fingers move with the hand (fewer bones, smaller files; fingers are too small to see in game).
Clips other than Death have their sideways drift removed, so the character stays on its tile.
"_trim" in the map keeps only part of a motion: {"Stab": [start, end]} in seconds.
"""
import argparse, base64, io, json, sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import addclips as A

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--hands-from'); ap.add_argument('--map'); ap.add_argument('--extra', nargs='*', default=[]); ap.add_argument('--pack', action='store_true'); ap.add_argument('--drop-fingers', action='store_true'); ap.add_argument('--rig28', action='store_true'); ap.add_argument('--tex', type=int, default=1024); ap.add_argument('--q', type=int, default=82)
a = ap.parse_args()

r = A.Rig(a.src); J, B = r.J, r.B
names = [r.nodes[j].get('name', '') for j in r.joints]; nj = len(names)
mesh_node = next(nd for nd in r.nodes if 'mesh' in nd and 'skin' in nd)
pr = J['meshes'][mesh_node['mesh']]['primitives'][0]; at = pr['attributes']
P = A.acc(J, B, at['POSITION']); Nn = A.acc(J, B, at['NORMAL']); UV = A.acc(J, B, at['TEXCOORD_0'])
JI = A.acc(J, B, at['JOINTS_0']).astype(int); WT = A.acc(J, B, at['WEIGHTS_0']); IX = A.acc(J, B, pr['indices']).ravel().astype(int)
assert len(P) < 65536, 'too many vertices'
N = r.norm(); Ni = np.linalg.inv(N)
keep = list(range(nj))
if a.drop_fingers:
    FING = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Hand_End', 'head_end', 'headfront', 'Toe_end')
    jpos = {j: k for k, j in enumerate(r.joints)}
    def up(k):  # nearest kept ancestor
        while any(f in names[k] for f in FING):
            p = r.parent[r.joints[k]]
            while p >= 0 and p not in jpos: p = r.parent[p]
            k = jpos[p]
        return k
    target = [up(k) for k in range(nj)]
    keep = sorted(set(target)); newi = {k: i for i, k in enumerate(keep)}
    JI = np.vectorize(lambda k: newi[target[k]])(JI)
    print(f'fingers dropped: {nj} -> {len(keep)} bones')
if a.rig28:  # the game's exact 28-bone layout (rigkit.NAMES order); fingers and extra bones follow their nearest kept ancestor
    import rigkit
    clean = [n.split(':')[-1] for n in names]
    keep = [clean.index(n) for n in rigkit.NAMES]
    jpos = {j: k for k, j in enumerate(r.joints)}
    def up28(k):
        while k not in keep:
            p = r.parent[r.joints[k]]
            while p >= 0 and p not in jpos: p = r.parent[p]
            k = jpos[p]
        return k
    newi = {k: i for i, k in enumerate(keep)}
    # the dropped bones (fingers, toes) keep the pose they have in the reference motion (Idle, else Walking, else the
    # first), relative to the kept ancestor: baked into the rest mesh so a hand stays relaxed instead of the stiff
    # open bind pose
    ref = next((an for an in r.anims if 'idle' in an.get('name', '').lower()), None) or \
          next((an for an in r.anims if 'walk' in an.get('name', '').lower()), None) or (r.anims[0] if r.anims else None)
    if ref is not None:
        S0 = r.pose(ref, 0.0)
        def rel(k):
            try: return np.eye(4) if k in keep else np.linalg.inv(S0[up28(k)]) @ S0[k]
            except KeyError: return np.eye(4)       # a bone above the hips with no kept ancestor: no vertices use it
        REL = [rel(k) for k in range(nj)]
        Wn = WT / np.maximum(WT.sum(1, keepdims=True), 1e-9)
        Mv = np.einsum('vb,vbij->vij', Wn, np.array([[REL[k] for k in row] for row in JI]))
        P = (np.einsum('vij,vj->vi', Mv, np.c_[P, np.ones(len(P))]))[:, :3]
        Nn = np.einsum('vij,vj->vi', Mv[:, :3, :3], Nn)
        nb = sum(1 for k in range(nj) if k not in keep)
        print(f'rig28: baked the {ref.get("name")} pose of {nb} dropped bones (fingers, toes) into the mesh')
    JI = np.vectorize(lambda k: newi[up28(k)])(JI)
    print(f'rig28: {nj} -> 28 bones')
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
       'jb': b64(JI.astype(np.uint8)), 'wb': b64(wb.astype(np.uint8)), 'nj': len(keep), 'an': []}

# weapon grip, from an existing model with hand tracks
BR = BL = None
if a.hands_from:
    d0 = json.load(open(a.hands_from)); n0 = d0['nj']; wc = next(c for c in d0['an'] if c['n'] == 'Walking')
    RH0 = 16 if n0 == 28 else None
    import rigkit; WF = rigkit.clip_frames(wc)   # packed ('fb') or plain ('f') frames
    Bs = [np.linalg.inv(WF[i, RH0]) @ A.m44(h) for i, h in enumerate(wc['hand'])]
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

norm = lambda s: ''.join(ch for ch in s.split('|')[-1].lower() if ch.isalnum())
MAXD, TRIM = {}, {}
pool = [(an, r) for an in r.anims]
for ex in a.extra:  # more motions for the same character, from other downloads (Meshy gives 20 per file)
    rx = A.Rig(ex); assert len(rx.joints) == nj, ex + ': different rig'
    pool += [(an, rx) for an in rx.anims]
todo = [(an.get('name', 'Anim'), an, rr) for an, rr in pool]
if a.map:
    MJ = json.load(open(a.map)); MAXD = MJ.get('_maxdur', {}); TRIM = MJ.get('_trim', {}); M = {k: v for k, v in MJ.items() if not k.startswith('_')}
    have = {}
    for an, rr in pool: have.setdefault(norm(an.get('name', '')), (an, rr))
    todo = []
    for game, wants in M.items():
        hit = next((have[norm(w)] for w in wants if norm(w) in have), None)
        if hit is not None: todo.append((game,) + hit)
        else: print('  no motion for', game)
    print('motions found:', sorted(set(an.get('name') for an, rr in pool)))
HIPS = names.index('Hips') if 'Hips' in names else 0
hip0 = (N @ np.linalg.inv(r.ibm[HIPS]))[:3, 3]
for gname, an, rr in todo:
    dur = max(A.acc(rr.J, rr.B, s['input']).max() for s in an['samplers'])
    t0 = 0.0
    if gname in TRIM: t0, t1 = TRIM[gname]; dur = min(dur, t1) - t0   # keep only the part that matters (one stab, one kick)
    elif gname not in ('Walking', 'Running'): dur = min(dur, MAXD.get(gname, MAXD.get('default', 99)))  # long motions are cut short
    nf = max(2, int(round(dur * A.FPS)) + 1)
    F, hand, handL = [], [], []
    for i in range(nf):
        S = [N @ M @ Ni for M in rr.pose(an, t0 + min(dur, i / A.FPS))]
        if gname != 'Death':  # stay on the tile: take out sideways drift of the hips
            hp = (S[HIPS] @ np.r_[hip0, 1])[:3]
            d = np.array([hp[0] - hip0[0], 0, hp[2] - hip0[2]])
            for k in range(nj): S[k] = S[k].copy(); S[k][:3, 3] -= d
        if BR is not None:
            for H, T, Bm in ((RH, RT, BR), (LH, LT, BL)):
                Rw = S[H] @ Bm @ A.ry(th) @ np.linalg.inv(Bm) @ np.linalg.inv(S[H])
                for k in T: S[k] = Rw @ S[k]
            hand.append([round(float(x), 4) for x in (S[RH] @ BR)[:3].reshape(-1)])
            handL.append([round(float(x), 4) for x in (S[LH] @ BL)[:3].reshape(-1)])
        F.append([float(x) for k in keep for x in S[k][:3].reshape(-1)])
    clip = {'n': gname, 'fps': A.FPS, 'dur': round(float(dur), 3)}
    if a.pack:
        Fa = np.array(F); tm = np.zeros(Fa.shape[1], bool); tm[3::4] = True
        sr = float(np.abs(Fa[:, ~tm]).max()) or 1.0; st = float(np.abs(Fa[:, tm]).max()) or 1.0
        Q = np.where(tm, Fa / st, Fa / sr) * 32767
        clip.update({'fb': b64(np.round(Q).astype(np.int16)), 'qs': [round(sr, 6), round(st, 6)], 'nj': len(keep)})
    else:
        clip['f'] = [[round(x, 4) for x in fr] for fr in F]
    if BR is not None: clip['hand'], clip['handL'] = hand, handL
    out['an'].append(clip); print(f"clip {clip['n']} <- {an.get('name')}: {dur:.2f}s, {nf} frames")
json.dump(out, open(a.dst, 'w'), separators=(',', ':'))
ext = V.max(0) - V.min(0)
print(f'{a.dst}: {len(V)} verts, {len(IX)//3} tris, {len(keep)} bones, size w{ext[0]:.2f} h{ext[1]:.2f} d{ext[2]:.2f}, {os.path.getsize(a.dst)//1024} KB')
