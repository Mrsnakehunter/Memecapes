#!/usr/bin/env python3
"""Find the cape on a caped character model and store a mask of it, so the game can repaint the
cape in each cape's own colour (the cape was made plain light grey on purpose).

usage: python3 tools/capemask.py models/player_cape.json
Adds "cm" (a PNG data URI, white = cape) to the model. A triangle counts as cape when its texture is
light grey and it is not on the arms (the light grey sleeves). Prints how much of the model is cape.
"""
import base64, io, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

p = sys.argv[1]; d = json.load(open(p))
V = np.frombuffer(base64.b64decode(d['vb']), np.int16).reshape(-1, 3) / 1000.
U = np.frombuffer(base64.b64decode(d['ub']), np.uint16).reshape(-1, 2) / 65535.
I = np.frombuffer(base64.b64decode(d['ib']), np.uint16).reshape(-1, 3).astype(int)
tex = Image.open(io.BytesIO(base64.b64decode(d['tex'].split(',')[1]))).convert('RGB'); T = np.asarray(tex).astype(float); S = T.shape[0]
hsv = np.asarray(tex.convert('HSV')).astype(float)

def sample(uv):
    x = np.clip((uv[:, 0] * S).astype(int), 0, S - 1); y = np.clip((uv[:, 1] * S).astype(int), 0, S - 1)
    return hsv[y, x]

# look at each triangle's middle and its corners
mid = U[I].mean(1); c = sample(mid)
sat, val = c[:, 1], c[:, 2]
cen = V[I].mean(1)
grey = (sat < 40) & (val > 120)
arms = (np.abs(cen[:, 0]) > 0.27) & (cen[:, 1] > 1.05)
head = cen[:, 1] > 1.45
cape = grey & ~arms & ~head
print(f'{cape.sum()} of {len(I)} triangles are cape ({100*cape.mean():.0f}%)')
# everything else that is not arms, head or the belt buckle may still hold grey cape texels (folds, seams)
buckle = ((np.abs(cen[:, 0]) < 0.13) & (cen[:, 1] > 0.8) & (cen[:, 1] < 1.16) & (cen[:, 2] > 0)) | ((np.abs(cen[:, 0]) < 0.1) & (cen[:, 1] > 1.2) & (cen[:, 2] > 0.02))  # buckle, and the tunic's neckline
maybe = ~arms & ~head & ~buckle & ~cape
m = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(m)
for t in np.where(cape)[0]:
    dr.polygon([tuple(q) for q in (U[I[t]] * S)], fill=255)
m2 = Image.new('L', (S, S), 0); dr2 = ImageDraw.Draw(m2)
for t in np.where(maybe)[0]:
    dr2.polygon([tuple(q) for q in (U[I[t]] * S)], fill=255)
core = m.filter(ImageFilter.MinFilter(3)); grow = m.filter(ImageFilter.MaxFilter(5))
# 255 = inside the cape (always repainted), 128 = its edge (repainted only where the texel is grey)
m3 = Image.new('L', (S, S), 0); dr3 = ImageDraw.Draw(m3)
for t in np.where(arms | head | buckle)[0]:
    dr3.polygon([tuple(q) for q in (U[I[t]] * S)], fill=255)
keep_out = np.asarray(m3) > 128   # texels of the face, arms and buckle never change
edge = ((np.asarray(grow) > 128) | (np.asarray(m2) > 128)) & ~keep_out
m = Image.fromarray(np.where((np.asarray(core) > 128) & ~keep_out, 255, np.where(edge, 128, 0)).astype(np.uint8))
bio = io.BytesIO(); m.resize((512, 512), Image.NEAREST).save(bio, 'PNG', optimize=True)
d['cm'] = 'data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode()
json.dump(d, open(p, 'w'), separators=(',', ':'))
# preview: cape painted red
pv = T.copy(); mx, mn = T.max(2), T.min(2); mm = np.asarray(m.resize((S, S), Image.NEAREST)); mk = (mm > 200) | ((mm > 60) & (mx - mn < 45) & (mx > 70))  # same rule as the game
g = T[mk].mean(1, keepdims=True) / 200.; pv[mk] = np.clip(np.array([150, 18, 30]) * g, 0, 255)
Image.fromarray(pv.astype(np.uint8)).resize((512, 512)).save('/tmp/capemask_preview.png')
print('mask added to', p, len(d['cm']) // 1024, 'KB; preview /tmp/capemask_preview.png')
