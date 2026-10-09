#!/bin/sh
# rebuild preview.html + test.html from the live base; leaves play.html = live
set -e
cd /home/claude/memecapes
[ -f /home/claude/scratch/play_gt.html ] || git show e1df6ab:play.html > /home/claude/scratch/play_gt.html
cp /home/claude/scratch/play_gt.html play.html
python3 tools/patch_xp.py >/dev/null
python3 tools/patch_names.py >/dev/null
python3 tools/patch_bld_models.py >/dev/null
python3 tools/patch_ring_coins.py >/dev/null
python3 tools/patch_bld_models.py >/dev/null
python3 tools/patch_held.py >/dev/null
python3 tools/patch_icons.py >/dev/null
python3 - <<'P'
import re;h=open('play.html').read();s=re.findall(r'<script>([\s\S]*?)</script>',h);open('/tmp/x.js','w').write(max(s,key=len))
P
node --check /tmp/x.js
cp play.html preview.html
/home/claude/scratch/mktest.sh
git checkout -- play.html
echo built
