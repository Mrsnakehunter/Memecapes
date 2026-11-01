#!/usr/bin/env python3
"""Scale a rigged body so its shoulders sit at the same height as a reference body's.

glb2rig scales every character to 1.7 m tall, so a body with a tall hat (mage sets) or a big hood comes out
shorter than the others. Run this straight after glb2rig (before armor_clips / armor_hands / carry_bake):
vertices are scaled about the feet (glb2rig puts them at y=0, centred), and every clip's skin matrices get
M' = S M S^-1 (same rotation, translation x s), which for packed clips is just the translation scale qs[1].

usage: python3 tools/fit_height.py arm_lv40 ma_lv10 ma_lv20 ...   (reference first; targets updated in place)
"""
import base64, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rigkit as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def shoulder_y(m):
    dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
    sel = np.isin(dom, [9, 14])          # LeftArm, RightArm
    return float(np.median(m['V'][sel, 1]))


def main(ref, keys):
    r = K.load(os.path.join(ROOT, 'models', ref + '.json')); ry = shoulder_y(r)
    for k in keys:
        path = os.path.join(ROOT, 'models', k + '.json'); m = K.load(path); d = m['d']
        s = ry / shoulder_y(m)
        if abs(s - 1) < .01: print(f'{k}: already fits ({s:.3f})'); continue
        V = np.round(m['V'] * s * 1000)
        assert np.abs(V).max() < 32767
        d['vb'] = base64.b64encode(V.astype(np.int16).tobytes()).decode()
        for c in d.get('an', []):
            if 'fb' in c: c['qs'][1] = round(c['qs'][1] * s, 6)
            else:
                F = np.array(c['f'], float).reshape(len(c['f']), -1, 3, 4); F[..., 3] *= s
                c['f'] = [[round(float(x), 5) for x in f.ravel()] for f in F]
            for h in ('hand', 'handL'):
                if h in c:
                    for i, row in enumerate(c[h]):
                        row = np.array(row).reshape(3, 4); row[:, 3] *= s; c[h][i] = [round(float(x), 4) for x in row.ravel()]
        open(path, 'w').write(json.dumps(d, separators=(',', ':')))
        print(f'{k}: x{s:.3f} (shoulders {shoulder_y(m):.3f} -> {ry:.3f} m, height {m["V"][:, 1].max() * s:.2f} m)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
