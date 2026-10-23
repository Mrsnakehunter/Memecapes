#!/usr/bin/env python3
# The project's X account is @memecapes (the base game links the old personal handle). Runs late in build.sh.
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'play.html'
s = open(p).read()
n = s.count('Mrsnakebaby')
s = s.replace('Mrsnakebaby', 'memecapes')
open(p, 'w').write(s)
print('patch_xhandle: %d replaced' % n)
