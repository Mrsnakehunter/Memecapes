# replace embedded screenshots in index.html: json list of [old_alt, new_alt, shot_png, size, crop_box_or_null]
import sys, json, re, base64, io
from PIL import Image
P = '/home/claude/memecapes/index.html'
h = open(P, encoding='utf-8').read()
for old, new, png, size, box in json.load(open(sys.argv[1])):
    k = None
    if '@@' in old: old, k = old.split('@@'); k = int(k)
    im = Image.open(png).convert('RGB')
    if box: im = im.crop(tuple(box))
    im = im.resize((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'WEBP', quality=82, method=6)
    data = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
    pat = re.compile(r'(<img[^>]*?src=")data:image/[a-z]+;base64,[A-Za-z0-9+/=]+("[^>]*?alt=")' + re.escape(old) + '"')
    hits = [m for m in pat.finditer(h) if m.start() > 1000000]   # skip the hero and feature images near the top
    if k is not None: hits = [hits[k]]
    assert len(hits) == 1, (old, len(hits))
    m = hits[0]
    h = h[:m.start()] + m.group(1) + data + m.group(2) + new + '"' + h[m.end():]
    print(old, '->', new, len(b.getvalue()) // 1024, 'KB')
open(P, 'w', encoding='utf-8').write(h)
