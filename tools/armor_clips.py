#!/usr/bin/env python3
"""Give armour bodies the full motion set of one armour body that Meshy animated natively.

All armour sets are rigged by Meshy's newer auto-rig (64 bones, brought to the game's 28 with glb2rig --rig28), so
their motions differ from the player's older rig by up to 34 degrees per bone: retargeting the player's clips onto
them (tools/npc_clips.py) bends arms and flings shoulder plates. Retargeting between two bodies of the SAME rig is
near-exact, so one set (the source) gets every motion from Meshy itself, and the others copy them from it:
same method as npc_clips.py (skeleton rebuilt from Walking + Running, R = R_src @ C per bone), with the source's own
skeleton as the reference and every clip the source has.

usage: python3 tools/armor_clips.py arm_lv40 arm_lv01 arm_lv80 ...   (source first; targets updated in place)
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rigkit as K
import npc_clips as N

def main(src, targets):
    S = K.load(os.path.join(N.ROOT, 'models', src + '.json'))
    shands = {c['n']: (c.get('hand'), c.get('handL')) for c in S['d']['an']}
    Xs, res = N.recon(S, N.PB * ((S['V'].max(0) - S['V'].min(0)) / (N.load_player()[0]['V'].max(0) - N.load_player()[0]['V'].min(0))))
    print(f'{src}: source skeleton fit {res * 1000:.2f} mm, clips {list(S["clips"])}')
    N.PB = Xs                                   # the source's own joints are the reference from here on
    G = N.grip_frames(S, shands)
    for key in targets:
        path = os.path.join(N.ROOT, 'models', key + '.json'); m = K.load(path)
        assert m['nj'] == 28 and 'Walking' in m['clips'], key
        ext = m['V'].max(0) - m['V'].min(0); sext = S['V'].max(0) - S['V'].min(0)
        X, r2 = N.recon(m, Xs * (ext / sext))
        C, err = N.fit_offsets(m, S)
        hl = np.linalg.norm(X[N.RH] - X[N.RH - 1]) / np.linalg.norm(Xs[N.RH] - Xs[N.RH - 1]); palm = float(np.clip(hl, .6, 1.6))
        T = m['clips']['Running']; R = N.retarget(X, C, S['clips']['Running']); n = min(len(T), len(R))
        chk = float(np.mean([np.sqrt(np.mean(np.sum((K.skin(m, T[f]) - K.skin(m, R[f])) ** 2, 1))) for f in range(0, n, 2)]))
        print(f'{key}: skeleton fit {r2 * 1000:.2f} mm, rotation fit max {err.max():.1f} deg (mean {err.mean():.1f}), running check {chk * 100:.1f} cm')
        new = []
        for c in S['d']['an']:
            name = c['n']
            F = m['clips'][name] if name in ('Walking', 'Running') else N.retarget(X, C, S['clips'][name])
            h, hL = N.tracks(F, X, C, G, palm)
            new.append(K.pack_clip(name, F, c.get('fps', 12), h, hL, c.get('dur')))
        m['d']['an'] = new
        json.dump(m['d'], open(path, 'w'), separators=(',', ':'))
        print(f'  {path}: {len(new)} clips, {os.path.getsize(path) // 1024} KB')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
