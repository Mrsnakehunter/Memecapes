#!/usr/bin/env python3
"""Put painted item pictures into the icon sprite (icons/items.webp + icons/items.json).

usage: python3 tools/icon_pack.py KEY=picture.png [KEY=picture.png ...]
Each picture (any size, transparent background) is trimmed to its alpha box, centred on a square with a small margin,
saved as a 256 px master in icons/src/KEY.png (so the sprite can be rebuilt), and downscaled in two steps with a light
sharpen into a 96 px cell. A key that already has a cell is overwritten in place; a new key gets the next free cell
(the sprite grows by a row when needed). patch_icons.py then points IC[KEY] at the cell.
"""
import json, os, sys
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
J, W = os.path.join(ROOT, 'icons/items.json'), os.path.join(ROOT, 'icons/items.webp')
MARGIN = .05


def prep(path):
    im = Image.open(path).convert('RGBA')
    a = im.split()[3].point(lambda v: 255 if v > 16 else 0)
    im = im.crop(a.getbbox())
    side = int(max(im.size) * (1 + 2 * MARGIN))
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    return sq


def cell(master, s):
    big = master.resize((s * 4, s * 4), Image.LANCZOS)
    small = big.resize((s, s), Image.LANCZOS)
    # sharpen colour only (keep the soft alpha edge)
    rgb = small.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=1))
    out = rgb.convert('RGBA'); out.putalpha(small.split()[3]); return out


def main(pairs):
    meta = json.load(open(J)); s, c = meta['size'], meta['cols']
    sheet = Image.open(W).convert('RGBA'); idx = meta['idx']
    os.makedirs(os.path.join(ROOT, 'icons/src'), exist_ok=True)
    for key, path in pairs:
        m = prep(path); m.resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, 'icons/src', key + '.png'))
        if key not in idx: idx[key] = max(idx.values()) + 1
        i = idx[key]; rows = i // c + 1
        if sheet.height < rows * s:
            g = Image.new('RGBA', (sheet.width, rows * s), (0, 0, 0, 0)); g.alpha_composite(sheet); sheet = g
        x, y = (i % c) * s, (i // c) * s
        sheet.paste(Image.new('RGBA', (s, s), (0, 0, 0, 0)), (x, y))
        sheet.alpha_composite(cell(m, s), (x, y))
        print(key, '-> cell', i)
    meta['w'], meta['h'] = sheet.width, sheet.height
    sheet.save(W, 'WEBP', quality=92, method=6)
    json.dump(meta, open(J, 'w'))
    print('sprite', sheet.size, len(idx), 'pictures')


if __name__ == '__main__':
    main([a.split('=', 1) for a in sys.argv[1:]])
