"""Reorder the website NPCs page (index.html #pg-bestiary), section by section:
   1. cards with a natural-pose picture, 2. cards whose picture is a T-pose, 3. cards with no picture yet (coming soon),
   keeping the original order inside each group, and never putting two cards that show the same character back to back.
T-pose is judged by eye (TPOSE_FREE below lists the cards that are NOT a T-pose); "same character" = same or
near-identical picture (difference hash) plus SAME pairs listed by hand. Run: python3 tools/site/bestiary_order.py"""
import re, io, base64, sys
from PIL import Image
P = 'index.html'
TPOSE_FREE = {'Book of Meme', 'Bouncy Hippo', 'NPC Guard', 'Fartcoin', 'Ratio Lord'}
SAME = [{'Shibe', 'Golden Hound'}, {'Bounty Boss Bonkwell', 'Shiba Inu'}]

def dhash(b64):
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert('L')
    w, h = im.size; c = min(w, h); im = im.crop(((w - c) // 2, (h - c) // 2, (w + c) // 2, (h + c) // 2)).resize((17, 16))
    px = list(im.getdata()); return [px[r * 17 + k] > px[r * 17 + k + 1] for r in range(16) for k in range(16)]

def main():
    s = open(P).read()
    i = s.find('id="pg-bestiary"'); j = s.find('</main>', i); page = s[i:j]
    out = page
    for gm in re.finditer(r'<div class="bgrid">(.*?)</div></div></div>(?=<div class="sec-title">|$)', page, re.S):
        grid = gm.group(1) + '</div></div>'
        cards = re.findall(r'<div class="bcard[^"]*">.*?</div></div>(?=<div class="bcard|$)', grid, re.S)
        assert ''.join(cards) == grid, 'card split failed'
        info = []
        for n, c in enumerate(cards):
            name = re.search(r'<h2[^>]*>(.*?)</h2>', c).group(1)
            m = re.search(r'<img src="data:image/\w+;base64,([^"]+)"', c)
            tier = 2 if not m else (0 if name in TPOSE_FREE else 1)
            info.append(dict(n=n, c=c, name=name, tier=tier, h=dhash(m.group(1)) if m else None))
        def same(a, b):
            if any({a['name'], b['name']} <= g for g in SAME): return True
            return a['h'] and b['h'] and sum(x != y for x, y in zip(a['h'], b['h'])) <= 40
        rest = sorted(info, key=lambda x: (x['tier'], x['n'])); order = []
        while rest:  # earliest card (in group order) that doesn't repeat the previous character
            k = next((k for k, x in enumerate(rest) if not order or not same(order[-1], x)), 0)
            order.append(rest.pop(k))
        for a, b in zip(order, order[1:]):
            if same(a, b): print('WARNING back to back:', a['name'], b['name'])
        print(' | '.join(f"{x['name']}{'' if x['tier'] == 0 else ' (T)' if x['tier'] == 1 else ' (soon)'}" for x in order))
        out = out.replace(grid, ''.join(x['c'] for x in order), 1)
    open(P, 'w').write(s[:i] + out + s[j:])

if __name__ == '__main__': main()
