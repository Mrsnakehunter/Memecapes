#!/usr/bin/env python3
"""Put the weapon in the armour's fist: grip tracks copied from the plain player body, moved to each armour's own hand.

The armour sets play the same motions as the plain body, frame for frame, so the plain body's grip ('hand' / 'handL'
tracks, the frame the weapon is drawn in) is right for them too, except for where the fist is: a gauntlet is bigger
and its hand bone sits differently, so the grip built from the hand bone landed beside the fist. Now, per frame, the
grip keeps the player's orientation and is moved by the difference between the armour's fist centre and the player's
(fist = the vertices the hand bone moves most, skinned at that frame).
Run BEFORE tools/carry_bake.py, on unbaked clips:  python3 tools/armor_hands.py [models/arm_lv40.json ...]
"""
import glob, json, sys
import numpy as np
sys.path.insert(0, 'tools')
import rigkit as K

RH, LH = 16, 11


def fist_centres(m, F, bone):
    dom = m['J'][np.arange(len(m['J'])), m['W'].argmax(1)]
    sel = dom == bone
    return np.array([K.skin(m, F[i])[sel].mean(0) for i in range(len(F))])


def main(paths):
    pl = K.load('models/player.json')
    pclips = {c['n']: c for c in pl['d']['an']}
    for path in paths:
        m = K.load(path); d = m['d']; done = []
        for c in d['an']:
            pc = pclips.get(c['n'])
            if not pc or not pc.get('hand'): continue
            Fa, Fp = K.clip_frames(c), K.clip_frames(pc)
            if len(Fa) != len(Fp): print(path, c['n'], 'frame count differs, kept'); continue
            for tr, bone in (('hand', RH), ('handL', LH)):
                if not pc.get(tr): continue
                ca, cp = fist_centres(m, Fa, bone), fist_centres(pl, Fp, bone)
                out = []
                for i in range(len(Fa)):
                    H = np.array(pc[tr][i], float).reshape(3, 4)
                    H[:, 3] += ca[i] - cp[i]
                    out.append([round(float(x), 4) for x in H.reshape(-1)])
                c[tr] = out
            done.append(c['n'])
        d.pop('carry', None)
        open(path, 'w').write(json.dumps(d, separators=(',', ':')))
        print(path, 'grips from the player for', len(done), 'clips')


if __name__ == '__main__':
    main(sys.argv[1:] or sorted(glob.glob('models/arm_lv??.json')))
