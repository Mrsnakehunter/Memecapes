#!/usr/bin/env python3
"""Copy a clip between two bodies with DIFFERENT rigs but the same shape (e.g. player2 -> player_cape2, the 22-bone
caped body). Every target bone gets the rigid motion (Kabsch fit) that best moves its own vertices to where the
nearest source vertices go in that frame, so no bone tables are needed.
usage: python3 tools/clip_by_mesh.py SRC CLIP target1 target2 ...
"""
import json, os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
import rigkit as K
import add_clips as A

def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); H = (P - cp).T @ (Q - cq); U, _, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ D @ U.T
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = cq - R @ cp; return M

def main(src, clip, targets):
    S = K.load(f'models/{src}.json'); SF = S['clips'][clip]; tree = cKDTree(S['V'])
    sc = [c for c in S['d']['an'] if c['n'] == clip][0]
    for key in targets:
        path = f'models/{key}.json'; m = K.load(path); nj = m['nj']
        dist, nn = tree.query(m['V'])
        dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
        F = np.zeros((len(SF), nj, 4, 4)); F[:] = np.eye(4)
        for f in range(len(SF)):
            Q = K.skin(S, SF[f])[nn]
            for j in range(nj):
                sel = np.where((dom == j) & (dist < .03))[0]
                if len(sel) < 6: sel = np.where(dom == j)[0]
                if len(sel) >= 3: F[f, j] = kabsch(m['V'][sel], Q[sel])
        RH, LH = (16, 11) if nj == 28 else (None, None)
        c = K.pack_clip(clip, F, sc.get('fps', 12), dur=sc.get('dur')); c['hand'] = sc.get('hand'); c['handL'] = sc.get('handL')
        # grip tracks: copy the source's (same shape, same hands)
        m['d']['an'] = [a for a in m['d']['an'] if a['n'] != clip] + [c]
        open(path, 'w').write(json.dumps(m['d'], separators=(',', ':')))
        err = np.mean([np.linalg.norm(K.skin(m, F[f]) - K.skin(S, SF[f])[nn], axis=1)[dist < .03].mean() for f in range(0, len(SF), 4)])
        print(f'{key}: {nj} bones, {clip} copied, mean vertex error {err * 100:.1f} cm')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
