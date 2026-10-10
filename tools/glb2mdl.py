#!/usr/bin/env python3
"""Convert a Meshy GLB (static, textured) into the game's packed model JSON.

usage: python3 tools/glb2mdl.py in.glb models/KEY.json [--tex 512] [--tris 6000] [--orient [--flip] [--mirror]]
--tris N lowers a full-detail Meshy model to about N triangles (tools/decimate.cpp, keeps the texture).

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


def decimate(P, U, I, target):
    """weld the vertices Meshy splits at texture seams, collapse edges down to `target` faces, then
    split again where the UV or a hard edge (over 60 degrees) needs it"""
    import os, subprocess
    exe = '/tmp/decimate'
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decimate.cpp')
    if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
        subprocess.check_call(['g++', '-O2', '-o', exe, src])
    key = np.round(P / 1e-5).astype(np.int64)
    _, pid, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    W = P[pid]; inv = inv.ravel(); T = inv[I.reshape(-1, 3)]; CU = U[I.reshape(-1, 3)].astype(np.float32)
    buf = (struct.pack('<i', len(W)) + W.astype(np.float32).tobytes() + struct.pack('<i', len(T)) +
           T.astype(np.int32).tobytes() + CU.tobytes() + struct.pack('<i', target))
    out = subprocess.run([exe], input=buf, capture_output=True, check=True)
    sys.stderr.write(out.stderr.decode())
    d = out.stdout; nf = struct.unpack('<i', d[:4])[0]
    T = np.frombuffer(d[4:4 + nf * 12], np.int32).reshape(-1, 3)
    CU = np.frombuffer(d[4 + nf * 12:4 + nf * 36], np.float32).reshape(-1, 3, 2)
    fn = np.cross(W[T[:, 1]] - W[T[:, 0]], W[T[:, 2]] - W[T[:, 0]])
    fa = np.linalg.norm(fn, axis=1, keepdims=True); fu = fn / np.maximum(fa, 1e-12)
    # corner normals: the area-weighted faces around that point that bend less than 60 degrees
    from collections import defaultdict
    around = defaultdict(list)
    for f, t in enumerate(T):
        for k in range(3): around[t[k]].append(f)
    CN = np.zeros((nf, 3, 3))
    for f, t in enumerate(T):
        for k in range(3):
            fs = np.array(around[t[k]]); ok = fs[(fu[fs] @ fu[f]) > .5]
            n = fn[ok].sum(0); CN[f, k] = n / max(np.linalg.norm(n), 1e-12)
    vk = {}; P2, N2, U2, I2 = [], [], [], []
    for f in range(nf):
        for k in range(3):
            kk = (int(T[f, k]), round(float(CU[f, k, 0]), 5), round(float(CU[f, k, 1]), 5), *np.round(CN[f, k] * 20).astype(int).tolist())
            if kk not in vk:
                vk[kk] = len(P2); P2.append(W[T[f, k]]); N2.append(CN[f, k]); U2.append(CU[f, k])
            I2.append(vk[kk])
    return np.array(P2), np.array(N2), np.array(U2, np.float64), np.array(I2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--tex', type=int, default=512); ap.add_argument('--q', type=int, default=82)
    ap.add_argument('--tris', type=int, default=0)
    ap.add_argument('--orient', action='store_true', help='stand a held item up: its long axis becomes y, its flat side faces z')
    ap.add_argument('--flip', action='store_true', help='with --orient: turn it upside down (grip at the other end)')
    ap.add_argument('--rotx', type=float, default=0, help='turn it this many degrees about x (before sizing)')
    ap.add_argument('--rotz', type=float, default=0, help='turn it this many degrees about z (before sizing)')
    ap.add_argument('--mirror', action='store_true', help='with --orient: spin it half a turn so its head points the other way')
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
    if a.tris and len(I) // 3 > a.tris: P, N, U, I = decimate(P, U, I, a.tris)
    if a.rotx or a.rotz:
        cx, sx = np.cos(np.radians(a.rotx)), np.sin(np.radians(a.rotx)); cz, sz = np.cos(np.radians(a.rotz)), np.sin(np.radians(a.rotz))
        R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        P = P @ R.T; N = N @ R.T
    if a.orient:
        c = P.mean(0); _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
        R = np.array([Vt[1], Vt[0], Vt[2]])
        if np.linalg.det(R) < 0: R[2] *= -1
        if a.flip: R[1] *= -1; R[2] *= -1
        if a.mirror: R[0] *= -1; R[2] *= -1
        P = (P - c) @ R.T; N = N @ R.T
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
