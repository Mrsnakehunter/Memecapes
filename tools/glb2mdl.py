#!/usr/bin/env python3
"""Convert a Meshy GLB (static, textured) into the game's packed model JSON.

usage: python3 tools/glb2mdl.py in.glb models/KEY.json [--tex 512] [--tris 6000]

Output format (same as the castle kit): vb Int16 positions /1000, nb Int8 normals /127,
ub Uint16 UVs /65535, ib Uint16 indices, tex = JPEG data URI.
Normalised so the widest horizontal side spans 1.9 units, centred on x/z, base at y=0.
In game, scale = footprint width in tiles / 1.9.
"""
import sys, json, struct, base64, io, argparse
import numpy as np
from PIL import Image

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'glTF', 'not a GLB'
    off, J, B = 12, None, None
    while off < len(d):
        ln, ty = struct.unpack('<II', d[off:off + 8])
        ch = d[off + 8:off + 8 + ln]
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
    if a.get('normalized') and dt.kind in 'iu':
        out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def mat4(node):
    if 'matrix' in node: return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    t = np.array(node.get('translation', [0, 0, 0])); s = np.array(node.get('scale', [1, 1, 1]))
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t
    return M


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--tex', type=int, default=512); ap.add_argument('--q', type=int, default=82)
    a = ap.parse_args()
    J, B = load(a.src)
    P, N, U, I, img = [], [], [], [], None
    def walk(ni, M):
        nd = J['nodes'][ni]; M = M @ mat4(nd)
        if 'mesh' in nd:
            for pr in J['meshes'][nd['mesh']]['primitives']:
                at = pr['attributes']; p = acc(J, B, at['POSITION']).astype(np.float64)
                p = (M @ np.c_[p, np.ones(len(p))].T).T[:, :3]
                n = acc(J, B, at['NORMAL']).astype(np.float64) if 'NORMAL' in at else np.zeros_like(p)
                n = (np.linalg.inv(M[:3, :3]).T @ n.T).T
                uv = acc(J, B, at['TEXCOORD_0']) if 'TEXCOORD_0' in at else np.zeros((len(p), 2))
                ix = acc(J, B, pr['indices']).ravel() if 'indices' in pr else np.arange(len(p))
                I.append(ix + sum(len(x) for x in P)); P.append(p); N.append(n); U.append(uv)
                nonlocal img
                if img is None and 'material' in pr:
                    t = J['materials'][pr['material']].get('pbrMetallicRoughness', {}).get('baseColorTexture')
                    if t:
                        im = J['images'][J['textures'][t['index']]['source']]; bv = J['bufferViews'][im['bufferView']]
                        img = Image.open(io.BytesIO(B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')
        for c in nd.get('children', []): walk(c, M)
    sc = J['scenes'][J.get('scene', 0)]
    for r in sc['nodes']: walk(r, np.eye(4))
    P = np.vstack(P); N = np.vstack(N); U = np.vstack(U); I = np.concatenate(I)
    assert len(P) < 65536, f'too many vertices ({len(P)}); remesh lower in Meshy'
    lo, hi = P.min(0), P.max(0)
    P[:, 0] -= (lo[0] + hi[0]) / 2; P[:, 2] -= (lo[2] + hi[2]) / 2; P[:, 1] -= lo[1]
    s = 1.9 / max(hi[0] - lo[0], hi[2] - lo[2]); P *= s
    assert np.abs(P).max() < 32, 'model too tall for Int16/1000 packing'
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    U = np.clip(U, 0, 1)
    b64 = lambda arr: base64.b64encode(arr.tobytes()).decode()
    out = {'vb': b64(np.round(P * 1000).astype(np.int16)), 'nb': b64(np.round(N * 127).astype(np.int8)),
           'ub': b64(np.round(U * 65535).astype(np.uint16)), 'ib': b64(I.astype(np.uint16))}
    if img is not None:
        bio = io.BytesIO(); img.resize((a.tex, a.tex), Image.LANCZOS).save(bio, 'JPEG', quality=a.q)
        out['tex'] = 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode()
    json.dump(out, open(a.dst, 'w'), separators=(',', ':'))
    ext = P.max(0) - P.min(0)
    print(f'{a.dst}: {len(P)} verts, {len(I)//3} tris, size w{ext[0]:.2f} h{ext[1]:.2f} d{ext[2]:.2f}, '
          f'tex {"yes" if img is not None else "NO"}, {len(json.dumps(out))//1024} KB')


if __name__ == '__main__':
    main()
