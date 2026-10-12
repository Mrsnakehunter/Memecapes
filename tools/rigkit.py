"""Shared helpers for the character tools: read a game model (models/KEY.json) into numpy, write clips back."""
import base64, json
import numpy as np

NAMES = ['Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head', 'head_end', 'headfront', 'LeftShoulder', 'LeftArm',
         'LeftForeArm', 'LeftHand', 'LeftHand_End', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
         'RightHand_End', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftToe_end', 'RightUpLeg', 'RightLeg',
         'RightFoot', 'RightToeBase', 'RightToe_end']
PAR = [-1, 0, 1, 2, 3, 4, 5, 5, 3, 8, 9, 10, 11, 3, 13, 14, 15, 16, 0, 18, 19, 20, 21, 0, 23, 24, 25, 26]


def dec(s, t): return np.frombuffer(base64.b64decode(s), t)


def load(path):
    d = json.load(open(path))
    m = {'d': d, 'nj': d.get('nj')}
    m['V'] = dec(d['vb'], np.int16).astype(np.float64).reshape(-1, 3) / 1000
    m['I'] = dec(d['ib'], np.uint16).astype(int).reshape(-1, 3)
    m['UV'] = dec(d['ub'], np.uint16).astype(np.float64).reshape(-1, 2) / 65535
    if 'jb' in d:
        m['J'] = dec(d['jb'], np.uint8).astype(int).reshape(-1, 4)
        m['W'] = dec(d['wb'], np.uint8).astype(np.float64).reshape(-1, 4) / 255
    m['clips'] = {}
    for c in d.get('an', []):
        m['clips'][c['n']] = clip_frames(c)
    return m


def clip_frames(c):
    """frames as (nf, nj, 4, 4) skin matrices"""
    if 'fb' in c:
        q = dec(c['fb'], np.int16).astype(np.float64); nj = c['nj']; n = nj * 12
        q = q.reshape(-1, n); tm = np.zeros(n, bool); tm[3::4] = True
        F = np.where(tm, q * c['qs'][1] / 32767, q * c['qs'][0] / 32767)
    else:
        F = np.array(c['f'], float); nj = F.shape[1] // 12
    F = F.reshape(len(F), nj, 3, 4)
    out = np.zeros((len(F), nj, 4, 4)); out[:, :, :3, :] = F; out[:, :, 3, 3] = 1
    return out


def skin(m, S):
    """skin the bind-pose vertices with one frame of skin matrices (nj,4,4)"""
    V = np.c_[m['V'], np.ones(len(m['V']))]
    out = np.zeros((len(V), 3))
    for k in range(4):
        out += m['W'][:, k:k + 1] * np.einsum('nij,nj->ni', S[m['J'][:, k]][:, :3, :], V)
    return out


def so3(M):
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt
    if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
    return R


def pack_clip(name, F, fps=12, hand=None, handL=None, dur=None):
    """F: (nf,nj,4,4) -> packed clip dict (16-bit, like glb2rig --pack)"""
    nf, nj = F.shape[:2]
    Fa = F[:, :, :3, :].reshape(nf, nj * 12)
    tm = np.zeros(nj * 12, bool); tm[3::4] = True
    sr = float(np.abs(Fa[:, ~tm]).max()) or 1.0; st = float(np.abs(Fa[:, tm]).max()) or 1.0
    Q = np.where(tm, Fa / st, Fa / sr) * 32767
    c = {'n': name, 'fps': fps, 'dur': round(float(dur if dur is not None else (nf - 1) / fps), 3),
         'fb': base64.b64encode(np.round(Q).astype(np.int16).tobytes()).decode(), 'qs': [round(sr, 6), round(st, 6)], 'nj': nj}
    if hand is not None: c['hand'] = [[round(float(x), 4) for x in h[:3].reshape(-1)] for h in hand]
    if handL is not None: c['handL'] = [[round(float(x), 4) for x in h[:3].reshape(-1)] for h in handL]
    return c
