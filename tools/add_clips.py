#!/usr/bin/env python3
"""Add new motions from one rigged body to others (same method as armor_clips.py, but it only ADDS clips).

The bow shot (Nov 1): Meshy's "Archery Shot 1" (reach to the quiver, nock, draw) + "Archery Shot 3" (hold and
release) played back to back = the game's 'Shoot' clip. Grip tracks for the new clip are the fist centres (the
vertices each hand bone moves most), which is all the bow code needs (it builds the bow's own frame from the hands).
usage: python3 tools/add_clips.py SRC 'Shoot=Shoot1+Shoot3' target1 target2 ...   (SRC/targets = model keys)
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rigkit as K
import npc_clips as N

RH, LH = 16, 11


def fists(m, F, bone):
    dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
    sel = np.where(dom == bone)[0]
    V = np.c_[m['V'][sel], np.ones(len(sel))]; J = m['J'][sel]; W = m['W'][sel]
    out = []
    for f in range(len(F)):
        p = np.zeros((len(sel), 3))
        for k in range(4): p += W[:, k:k + 1] * np.einsum('nij,nj->ni', F[f][J[:, k]][:, :3, :], V)
        out.append(p.mean(0))
    return out


def track(F, P, bone):
    rows = []
    for f in range(len(F)):
        M = np.eye(4); M[:3, :3] = K.so3(F[f, bone, :3, :3]); M[:3, 3] = P[f]; rows.append(M)
    return rows


def main(src, spec, targets):
    S = K.load(os.path.join(N.ROOT, 'models', src + '.json'))
    name, parts = spec.split('='); parts = parts.split('+')
    SF = np.concatenate([S['clips'][p] for p in parts])
    Xs, res = N.recon(S, N.PB * ((S['V'].max(0) - S['V'].min(0)) / (N.load_player()[0]['V'].max(0) - N.load_player()[0]['V'].min(0))))
    print(f'{src}: skeleton fit {res * 1000:.2f} mm, {name} = {"+".join(parts)} ({len(SF)} frames)')
    for key in targets:
        path = os.path.join(N.ROOT, 'models', key + '.json'); m = K.load(path)
        ext = m['V'].max(0) - m['V'].min(0); sext = S['V'].max(0) - S['V'].min(0)
        X, r2 = N.recon(m, Xs * (ext / sext))
        C, err = N.fit_offsets(m, S)
        T = m['clips']['Running']; R = N.retarget(X, C, S['clips']['Running']); n = min(len(T), len(R))
        chk = float(np.mean([np.sqrt(np.mean(np.sum((K.skin(m, T[f]) - K.skin(m, R[f])) ** 2, 1))) for f in range(0, n, 2)]))
        F = N.retarget(X, C, SF)
        c = K.pack_clip(name, F, 12, track(F, fists(m, F, RH), RH), track(F, fists(m, F, LH), LH))
        m['d']['an'] = [a for a in m['d']['an'] if a['n'] != name] + [c]
        open(path, 'w').write(json.dumps(m['d'], separators=(',', ':')))
        print(f'  {key}: rotation fit mean {err.mean():.1f} deg, running check {chk * 100:.1f} cm, {os.path.getsize(path) // 1024} KB')



def relax_hands(key, name='Shoot', ref='Idle'):
    """plain player bodies: the retarget twists their wrists (different rig), so each hand keeps its Idle pose
    relative to the forearm: S_hand' = S_forearm' . S_forearm_idle^-1 . S_hand_idle (bones 11/12 and 16/17)."""
    path = os.path.join(N.ROOT, 'models', key + '.json'); m = K.load(path); I = m['clips'][ref][0]
    for c in m['d']['an']:
        if c['n'] != name: continue
        F = K.clip_frames(c)
        for f in range(len(F)):
            for par, kids in ((10, (11, 12)), (15, (16, 17))):
                A = F[f, par] @ np.linalg.inv(I[par])
                for k in kids: F[f, k] = A @ I[k]
        c.update(K.pack_clip(name, F, 12, track(F, fists(m, F, RH), RH), track(F, fists(m, F, LH), LH)))
    open(path, 'w').write(json.dumps(m['d'], separators=(',', ':')))
    print('  relaxed hands:', key)


if __name__ == '__main__':
    if sys.argv[1] == '--relax': [relax_hands(k) for k in sys.argv[2:]]
    else: main(sys.argv[1], sys.argv[2], sys.argv[3:])
