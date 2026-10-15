#!/usr/bin/env python3
"""Build models/trees.json, the tree pack the game draws with instancing (tools/patch_trees.py).

usage: python3 tools/treepack.py <folder with t_<species>.glb> [--out models/trees.json] [--tex 512]

Each GLB (a textured Meshy remesh, ~6k triangles) becomes three detail levels, decimated with
tools/decimate.cpp (keeps the texture): near ~1600, mid ~500, far ~160 triangles. All three share one
normalisation (widest horizontal side = 1.9 units, centred on x/z, base at y=0) so the levels swap
without a size jump. One 512 px JPEG per species.

pack = {"<species>": {"h": height, "w": widest side (always 1.9), "lod": [{vb,nb,ub,ib}, ...], "tex": dataURI}}
"""
import argparse, base64, glob, io, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb2mdl as G

LODS = [1600, 500, 160]


def mesh(path):
    J, B = G.load(path)
    P, N, U, I, img = [], [], [], [], None

    def walk(ni, M):
        nonlocal img
        nd = J['nodes'][ni]; M = M @ G.mat4(nd)
        if 'mesh' in nd:
            for pr in J['meshes'][nd['mesh']]['primitives']:
                at = pr['attributes']; p = G.acc(J, B, at['POSITION']).astype(np.float64)
                p = (M @ np.c_[p, np.ones(len(p))].T).T[:, :3]
                n = G.acc(J, B, at['NORMAL']).astype(np.float64) if 'NORMAL' in at else np.zeros_like(p)
                n = (np.linalg.inv(M[:3, :3]).T @ n.T).T
                uv = G.acc(J, B, at['TEXCOORD_0']) if 'TEXCOORD_0' in at else np.zeros((len(p), 2))
                ix = G.acc(J, B, pr['indices']).ravel() if 'indices' in pr else np.arange(len(p))
                I.append(ix + sum(len(x) for x in P)); P.append(p); N.append(n); U.append(uv)
                if img is None and 'material' in pr:
                    t = J['materials'][pr['material']].get('pbrMetallicRoughness', {}).get('baseColorTexture')
                    if t:
                        im = J['images'][J['textures'][t['index']]['source']]; bv = J['bufferViews'][im['bufferView']]
                        img = Image.open(io.BytesIO(B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')
        for c in nd.get('children', []): walk(c, M)
    for r in J['scenes'][J.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    return np.vstack(P), np.vstack(N), np.vstack(U), np.concatenate(I), img


def pack(P, N, U, I, off, s):
    P = (P - off) * s
    assert len(P) < 65536, f'too many vertices ({len(P)})'
    assert np.abs(P).max() < 32, 'too tall for Int16/1000'
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    b64 = lambda arr: base64.b64encode(arr.tobytes()).decode()
    return {'vb': b64(np.round(P * 1000).astype(np.int16)), 'nb': b64(np.round(N * 127).astype(np.int8)),
            'ub': b64(np.round(np.clip(U, 0, 1) * 65535).astype(np.uint16)), 'ib': b64(I.astype(np.uint16))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--out', default='models/trees.json')
    ap.add_argument('--tex', type=int, default=512); ap.add_argument('--q', type=int, default=80)
    ap.add_argument('--lods', default=','.join(map(str, LODS)))
    a = ap.parse_args(); lods = [int(x) for x in a.lods.split(',')]
    out = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for f in sorted(glob.glob(os.path.join(a.src, 't_*.glb'))):
        key = os.path.basename(f)[2:-4]
        P, N, U, I, img = mesh(f)
        assert img is not None, f'{f}: no texture'
        levels = []
        cur = (P, N, U, I)
        for t in lods:  # each level is cut from the previous one: the re-weld frees the seams the last pass got stuck on
            if len(cur[3]) // 3 > t:
                cur = G.decimate(cur[0], cur[2], cur[3], t, 1)
                if len(cur[3]) // 3 > t * 1.15: cur = G.decimate(cur[0], cur[2], cur[3], t, 1)
            levels.append(cur)
        P0 = levels[0][0]; lo, hi = P0.min(0), P0.max(0)
        off = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]); s = 1.9 / max(hi[0] - lo[0], hi[2] - lo[2])
        e = {'h': round(float((hi[1] - lo[1]) * s), 3), 'w': 1.9, 'lod': [pack(*lv, off, s) for lv in levels]}
        bio = io.BytesIO(); img.resize((a.tex, a.tex), Image.LANCZOS).save(bio, 'JPEG', quality=a.q)
        e['tex'] = 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()
        out[key] = e
        print(f'{key}: h {e["h"]}, tris {[len(lv[3]) // 3 for lv in levels]}, verts {[len(lv[0]) for lv in levels]}, {len(json.dumps(e)) // 1024} KB')
    json.dump(out, open(a.out, 'w'), separators=(',', ':'))
    print(f'{a.out}: {len(out)} species, {os.path.getsize(a.out) // 1024} KB')


if __name__ == '__main__':
    main()
