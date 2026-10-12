#!/usr/bin/env python3
"""Give NPC and monster models the player's combat animations (idle, attacks, hit, death, cast), retargeted.

Every character here was rigged by Meshy with the same 28-bone skeleton, but each has its own proportions and its
own bind pose (some T-pose, some A-pose). The NPC models only came with Walking and Running, so before this they
stood frozen, never swung anything and simply vanished when killed.

How the retarget works (checked against data, not guessed):
  1. Rebuild the NPC's skeleton from its own Walking and Running frames: a child joint sits at the one point that
     both its own skin matrix and its parent's map to the same place in every frame (least squares; error 0.1 mm).
  2. Meshy retargets a library motion to a character by keeping each bone's world rotation change, up to a fixed
     per-bone offset (the bind pose difference). So for every bone: R_npc(t) = R_player(t) @ C, with C fitted
     from the Walking motion both characters share. The fit error is under 1 degree for every bone.
  3. New motions: rotations R_player(t) @ C, joint positions chained down the NPC's own bone lengths, hips moved
     by the player's hip motion scaled to the NPC's hip height.
  4. Weapon grip tracks ('hand', 'handL') in the same form the player uses, so the game's held-weapon code can put
     a sword, staff or shield in an NPC's hand and it follows every swing.
Checked by retargeting the player's Running onto each NPC and comparing with the NPC's own Running from Meshy.

usage: python3 tools/npc_clips.py knight chad doge ...      (models/KEY.json is updated in place)
       python3 tools/npc_clips.py --check knight            (report only)
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rigkit as K

ROOT = os.path.join(os.path.dirname(__file__), '..')
PB = np.array(json.load(open(os.path.join(os.path.dirname(__file__), 'player_bind.json')))['bind'])
RH, LH, RHE, LHE = 16, 11, 17, 12
PALM = np.array([-.03, .14, 0])          # the game's palm offset in hand space (window.PALM)
CLIPS = ['Idle', 'Attack', 'Stab', 'Punch', 'Kick', 'Mine', 'Hit', 'Death', 'Cast']
TOWN = {'banker', 'cobbler', 'trader', 'richw', 'chefdoge', 'bonkwell', 'frostdoge'}   # never fight: idle only
SLOW = {'Idle': 2}       # breathing is slow: every 2nd frame is plenty (smaller download, less graphics memory)


def load_player():
    m = K.load(os.path.join(ROOT, 'models/player.json'))
    hands = {c['n']: (c.get('hand'), c.get('handL')) for c in m['d']['an']}
    return m, hands


def m44(a): return np.vstack([np.array(a, float).reshape(3, 4), [0, 0, 0, 1]])


def recon(m, prior, lam=1e-3):
    """bind position of every joint from the model's own animation frames"""
    Fs = np.concatenate([m['clips'][c] for c in ('Walking', 'Running') if c in m['clips']])
    nj = Fs.shape[1]; X = np.zeros((nj, 3)); res = 0
    for c in range(1, nj):
        p = K.PAR[c]
        A_ = np.concatenate([Fs[f, p, :3, :3] - Fs[f, c, :3, :3] for f in range(len(Fs))])
        b = np.concatenate([Fs[f, c, :3, 3] - Fs[f, p, :3, 3] for f in range(len(Fs))])
        X[c] = np.linalg.solve(A_.T @ A_ + lam * np.eye(3), A_.T @ b + lam * prior[c])
        res = max(res, float(np.sqrt(np.mean((A_ @ X[c] - b) ** 2))))
    X[0] = (X[18] + X[23]) / 2 + (prior[0] - (prior[18] + prior[23]) / 2)
    return X, res


def fit_offsets(m, P):
    """per-bone rotation offset C so that R_npc = R_player @ C (fitted on Walking + Running)"""
    C, err = [], []
    for j in range(28):
        M = np.zeros((3, 3)); pairs = []
        for cl in ('Walking', 'Running'):
            if cl not in m['clips']: continue
            T, S = m['clips'][cl], P['clips'][cl]
            for f in range(min(len(T), len(S))):
                M += S[f, j, :3, :3].T @ T[f, j, :3, :3]; pairs.append((S[f, j, :3, :3], T[f, j, :3, :3]))
        Cj = K.so3(M); C.append(Cj)
        err.append(max(np.degrees(np.arccos(np.clip((np.trace((a @ Cj).T @ b) - 1) / 2, -1, 1))) for a, b in pairs))
    return np.array(C), np.array(err)


def retarget(X, C, S):
    nf = len(S); out = np.zeros((nf, 28, 4, 4)); out[:, :, 3, 3] = 1
    k = X[0, 1] / PB[0, 1]
    for f in range(nf):
        D = [S[f, j, :3, :3] @ C[j] for j in range(28)]
        p = np.zeros((28, 3))
        p[0] = X[0] + k * ((S[f, 0] @ np.r_[PB[0], 1])[:3] - PB[0])
        for j in range(1, 28):
            q = K.PAR[j]; p[j] = p[q] + D[q] @ (X[j] - X[q])
        for j in range(28):
            out[f, j, :3, :3] = D[j]; out[f, j, :3, 3] = p[j] - D[j] @ X[j]
    return out


def grip_frames(P, phands):
    """the player's hand-bone -> grip offset (rotation only), right and left"""
    W = P['clips']['Walking']; hand, handL = phands['Walking']
    out = []
    for H, tr in ((RH, hand), (LH, handL)):
        Bs = [np.linalg.inv(W[i, H]) @ m44(h) for i, h in enumerate(tr)]
        out.append(K.so3(np.mean([b[:3, :3] for b in Bs], axis=0)))
    return out


def tracks(F, X, C, G, palm):
    """grip tracks for frames F of this NPC: same world orientation as the player's grip, at the NPC's own hand"""
    hand, handL = [], []
    for f in range(len(F)):
        for H, Gr, lst in ((RH, G[0], hand), (LH, G[1], handL)):
            R = F[f, H, :3, :3] @ C[H].T @ Gr
            T = (F[f, H] @ np.r_[X[H], 1])[:3]
            if H == RH: T = T + (palm - 1) * (R @ PALM)    # the game adds PALM once; bigger hands hold further in
            M = np.eye(4); M[:3, :3] = R; M[:3, 3] = T; lst.append(M)
    return hand, handL


def process(key, check=False):
    path = os.path.join(ROOT, 'models', key + '.json')
    P, phands = load_player()
    m = K.load(path)
    assert m['nj'] == 28 and 'Walking' in m['clips'], key + ': needs the 28-bone rig and a Walking clip'
    V = m['V']; ext = V.max(0) - V.min(0); pext = P['V'].max(0) - P['V'].min(0)
    X, res = recon(m, PB * (ext / pext))
    C, err = fit_offsets(m, P)
    G = grip_frames(P, phands)
    hl = np.linalg.norm(X[RH] - X[RH - 1]) / np.linalg.norm(PB[RH] - PB[RH - 1])   # forearm length vs the player's
    palm = float(np.clip(hl, .6, 1.6))
    # check: the player's Running retargeted vs the model's own Running
    chk = None
    if 'Running' in m['clips']:
        T = m['clips']['Running']; R = retarget(X, C, P['clips']['Running']); n = min(len(T), len(R))
        chk = float(np.mean([np.sqrt(np.mean(np.sum((K.skin(m, T[f]) - K.skin(m, R[f])) ** 2, 1))) for f in range(0, n, 2)]))
    print(f'{key}: skeleton fit {res * 1000:.2f} mm, rotation fit max {err.max():.1f} deg, running check {chk and chk * 100:.1f} cm (hip drift only), forearm {hl:.2f}')
    if check: return
    d = m['d']; new = []
    for c in d['an']:
        if c['n'] in ('Walking', 'Running'):
            F = m['clips'][c['n']]; h, hL = tracks(F, X, C, G, palm)
            new.append(K.pack_clip(c['n'], F, c.get('fps', 12), h, hL, c.get('dur')))
    for name in (['Idle'] if key in TOWN else CLIPS):
        S = P['clips'][name]; F = retarget(X, C, S); h, hL = tracks(F, X, C, G, palm)
        k = SLOW.get(name, 1); n = (len(F) - 1) // k * k + 1
        new.append(K.pack_clip(name, F[:n:k], 12 // k, h[:n:k], hL[:n:k], (n - 1) / 12))
    d['an'] = new
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    print(f'  {path}: clips {[c["n"] for c in new]}, {os.path.getsize(path) // 1024} KB')


if __name__ == '__main__':
    args = sys.argv[1:]; check = '--check' in args
    for k in [a for a in args if not a.startswith('--')]: process(k, check)
