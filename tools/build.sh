#!/bin/sh
# rebuild preview.html + test.html from the live base; leaves play.html = live
set -e
# BASE = the game before the art and name patches (= play.html at commit e1df6ab)
BASE=${BASE:-/home/claude/scratch/play_gt.html}
cd /home/claude/memecapes
[ -f "$BASE" ] || git show e1df6ab:play.html > "$BASE"
cp "$BASE" play.html
python3 tools/patch_xp.py >/dev/null
python3 tools/patch_names.py >/dev/null
python3 tools/patch_bld_models.py >/dev/null
python3 tools/patch_ring_coins.py >/dev/null
python3 tools/patch_bld_models.py >/dev/null
python3 tools/patch_lights.py >/dev/null
python3 tools/patch_held.py >/dev/null
python3 tools/patch_icons.py >/dev/null
python3 tools/patch_logo.py >/dev/null
python3 tools/patch_chat.py >/dev/null
python3 tools/patch_capes.py >/dev/null
python3 tools/patch_3d.py >/dev/null
python3 tools/patch_travel.py >/dev/null
python3 - <<'P'
import re;h=open('play.html').read();s=re.findall(r'<script>([\s\S]*?)</script>',h);open('/tmp/x.js','w').write(max(s,key=len))
P
node --check /tmp/x.js
cp play.html preview.html
/home/claude/scratch/mktest.sh
git checkout -- play.html
echo built
