# before/after sheet: rows of (title, before shot or None, after shot)
import sys, json
from PIL import Image, ImageDraw, ImageFont
D = '/home/claude/scratch/shots/site/'
rows = json.load(open(sys.argv[1])); out = sys.argv[2]; head = sys.argv[3]
S = 400; G = 14; L = 30
FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 22)
FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
FT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 28)
cols = 2
W = L * 2 + cols * (S * 2 + G) + (cols - 1) * 40
nr = (len(rows) + cols - 1) // cols
H = 80 + nr * (S + 70)
im = Image.new('RGB', (W, H), (40, 8, 12)); d = ImageDraw.Draw(im)
d.text((L, 22), head, font=FT, fill=(244, 196, 64))
def shot(n):
    return Image.open(D + n + '_full.png').crop((20, 0, 820, 800)).resize((S, S), Image.LANCZOS)
for i, (title, sub, a, b) in enumerate(rows):
    x = L + (i % cols) * (S * 2 + G + 40); y = 80 + (i // cols) * (S + 70)
    if a:
        im.paste(shot(a), (x, y)); d.text((x + 8, y + 6), 'BEFORE (v2)', font=FS, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    im.paste(shot(b), (x + (S + G if a else 0), y)); d.text((x + (S + G if a else 0) + 8, y + 6), 'NOW (v3)', font=FS, fill=(255, 230, 120), stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((x, y + S + 8), title, font=FB, fill=(244, 196, 64)); d.text((x, y + S + 38), sub, font=FS, fill=(230, 220, 210))
im.save(out); print(im.size)
