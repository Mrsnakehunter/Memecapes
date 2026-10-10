#!/bin/sh
# make the tested preview the live game, and tell running games that an update is out
set -e
cd /home/claude/memecapes
[ "$(grep -c '__tp=tpTo\|window.__g=' preview.html)" = 0 ] || { echo 'test hooks in preview.html, not shipping'; exit 1; }
cp preview.html play.html
B=$(grep -o "const BUILD='[0-9]*'" play.html | grep -o '[0-9]\{6,\}')
printf '{"build":"%s"}\n' "$B" > version.json
echo "shipping build $B"
