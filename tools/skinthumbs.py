#!/usr/bin/env python3
"""Store pictures for every skin: models/skins/thumbs/<id>.jpg (320 x 320).

Capes: the caped body wearing the skin, seen from behind with the idle pose, turned so the cape faces the light.
Weapon skins: the weapon on its own, tilted across the picture. All on a glowing maroon background.
Needs the cape preview models first:  python3 tools/capeskins.py --preview   (writes /tmp/cs_<skin>_m.json)
usage: python3 tools/skinthumbs.py            (run from the repo root; renders with tools/dev/charview)
"""
import base64, json, os, re, subprocess, sys
import numpy as np
from PIL import Image

S, BG = 320, [.10, .04, .06]
src = open('tools/patch_skins.py', encoding='utf-8').read()
ids = re.findall(r"\('((?:cs|sk)_[a-z_]+)', '", src)
an = json.load(open('models/player_cape.json'))['an']
panels, names, tmp = [], [], []
for sid in ids:
    if sid.startswith('cs_'):
        p = f'/tmp/cs_{sid[3:]}_m.json'
        if not os.path.exists(p): print('no preview model for', sid, '(run capeskins.py --preview)'); continue
        d = json.load(open(p)); d['an'] = an; k = 'zz_t_' + sid[3:]; json.dump(d, open(f'models/{k}.json', 'w')); tmp.append(k)
        panels.append({'m': k, 'clip': 'Idle', 'f': 2, 'yaw': 3.14159, 'cam': [0.0, 0.08, 1.9, 1.02], 'bg': BG})
    else:
        f = f'models/w_{sid}.json'
        if not os.path.exists(f): print('no model yet for', sid); continue
        V = np.frombuffer(base64.b64decode(json.load(open(f))['vb']), np.int16).reshape(-1, 3) / 1000
        hgt = V[:, 1].max() - V[:, 1].min()
        panels.append({'m': 'w_' + sid, 'sc': 1 / hgt, 'off': [0, (V[:, 1].max() + V[:, 1].min()) / 2, 0], 'rz': -0.75, 'cam': [0.55, 0.18, 1.6 * hgt, 0], 'bg': BG})
    names.append(sid)
cols = 8; rows = (len(panels) + cols - 1) // cols
json.dump({'cols': cols, 'w': cols * S, 'h': rows * S, 'panels': panels}, open('/tmp/skinthumbs_job.json', 'w'))
try:
    subprocess.run([sys.executable, 'tools/dev/charview/shoot.py', '/tmp/skinthumbs_job.json', '/tmp/skinthumbs.png'], check=True)
finally:
    for k in tmp: os.remove(f'models/{k}.json')
im = np.asarray(Image.open('/tmp/skinthumbs.png').convert('RGB')).astype(float)
bg = np.array(BG) * 255
yy, xx = np.mgrid[0:S, 0:S]; r = np.hypot(xx - S / 2, yy - S * .45) / (S * .72)
grad = (np.array([86, 26, 38]) * (1 - r[..., None]) + np.array([20, 7, 11]) * r[..., None]).clip(0, 255)
os.makedirs('models/skins/thumbs', exist_ok=True)
for i, n in enumerate(names):
    x, y = (i % cols) * S, (i // cols) * S; p = im[y:y + S, x:x + S]
    a = np.clip((np.abs(p - bg).max(2) - 3) / 14, 0, 1)[..., None]     # near-background pixels take the glow
    Image.fromarray((p * a + grad * (1 - a)).astype(np.uint8)).save(f'models/skins/thumbs/{n}.jpg', quality=86)
print(len(names), 'store pictures in models/skins/thumbs')
