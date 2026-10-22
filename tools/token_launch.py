#!/usr/bin/env python3
"""Token launch day: put the live token on everything in one go.

    python3 tools/token_launch.py --ticker TICKER --mint MINT --creator WALLET [--pit ../snakepit] [--check]

What it does (memecapes repo, and the Pit's code when --pit is given):
  * every "$CAPES" a player can read becomes "$TICKER" (site, game, server messages, support answers, Pit screens)
  * the "no token exists yet" lines on the site become the official contract address (Solscan link)
  * config.js gets the mint and the ticker; the creator wallet and the mint join the Official wallets
    section on the site and Watchtower's official list
  * code names (capesMint, CAPES_MINT, NEXT_PUBLIC_CAPES_MINT ...) and the MemeCapes / Meme Cape names stay as they are
--check runs everything on a scratch copy and prints what would change; nothing in the real repos is touched.
The script itself holds no ticker: it is given at launch, so nothing in this public repo gives it away early.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile

B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
TEXT = ('.html', '.js', '.py', '.json', '.md', '.yaml', '.yml', '.sh', '.txt', '.ts', '.tsx', '.mjs')
SKIP = {'CLAUDE.md', 'PROGRESS.md', 'tools/token_launch.py', 'tools/patch_ticker.py'}   # history stays as written

def ca_link(m):
    return ('<a href="https://solscan.io/token/%s" target="_blank" rel="noopener" '
            'style="font-family:monospace;overflow-wrap:anywhere;color:var(--gold)">%s</a>' % (m, m))

def site_lines(t, mint, creator):
    """exact sentences on index.html that change at launch: (old, new, expected count)"""
    CA = ca_link(mint)
    X = '<a href="https://x.com/Mrsnakebaby" style="color:var(--gold)">@Mrsnakebaby</a>'
    return [
        ('<b>No $CAPES token exists yet.</b> When it does, the contract address will be posted only on this site and on ',
         '<b>$%s is live.</b> Official contract address: %s. It is posted only on this site and on ' % (t, CA), 1),
        ('The token does not exist yet. When it launches, the contract address will be posted only on this site and on @Mrsnakebaby.',
         'Official contract address: %s. It is posted only on this site and on @Mrsnakebaby.' % CA, 1),
        ('<b>No $CAPES token exists yet.</b> The contract address will be posted only on this page and on ' + X +
         '. If you see a "$CAPES" anywhere before that, it is fake. Do not buy it.',
         '<b>Official contract address:</b> %s. It is posted only on this page and on %s. Any other "$%s" is fake. Do not buy it.' % (CA, X, t), 1),
        ('<b>No $CAPES token exists yet.</b> Any token using the name before the official announcement is fake.',
         '<b>Official $%s contract: %s.</b> Any other token using the name is fake.' % (t, CA), 1),
        ('<span class="pill red">Not live yet</span><h1>$CAPES</h1>', '<span class="pill green">Live on Solana</span><h1>$%s</h1>' % t, 1),
        (' The token launches only after the multiplayer server is ready, not before.', ' Live on Solana: the official contract address is below.', 1),
        ('The $CAPES side is optional and comes later.', 'The $%s side is optional.' % t, 1),
        ('<summary>Is there a token?</summary>Not yet. When there is, it will be announced here first. Anything before that is fake.',
         '<summary>Is there a token?</summary>Yes: $%s on Solana. The only official contract address is %s, posted here and on @Mrsnakebaby. Anything else is fake.' % (t, CA), 1),
        ('<b>No $CAPES token exists until we announce it on this website and on <a href="https://x.com/Mrsnakebaby">@Mrsnakebaby</a>.</b> Any token using the name before that is not ours. If and when $CAPES launches:',
         '<b>The only official $%s token is %s, announced on this website and on <a href="https://x.com/Mrsnakebaby">@Mrsnakebaby</a>.</b> Any other token using the name is not ours. About $%s:' % (t, CA, t), 1),
        ('Meme Coins are play money, $CAPES does not exist yet, and crypto can go to zero.', 'Meme Coins are play money, and crypto can go to zero.', 1),
        ('<p class="mute" style="margin-top:10px">More wallets (creator, game pot) are added here as they are used.',
         '<p class="mute" style="margin-top:10px">More wallets (game pot) are added here as they are used.', 1),
    ]

def wallet_cards(t, mint, creator):
    card = ('<div class="card"><h3>%s</h3><p class="mute">%s</p><p style="font-family:monospace;font-size:13px;'
            'overflow-wrap:anywhere"><a href="https://solscan.io/%s/%s" target="_blank" rel="noopener">%s</a></p></div>')
    return (card % ('$%s token contract' % t, 'The one and only official $%s. Check this address before you buy anything.' % t, 'token', mint, mint) +
            card % ('Creator wallet', 'Launched $%s and made the first buy in the same transaction. Public from the first second.' % t, 'account', creator, creator))

def files(root, subdirs=None):
    out = []
    tracked = subprocess.run(['git', 'ls-files'], cwd=root, capture_output=True, text=True, check=True).stdout.split('\n')
    for f in tracked:
        if not f or f in SKIP or not f.endswith(TEXT): continue
        if subdirs and not any(f.startswith(s) for s in subdirs): continue
        if f.startswith('scratch/'): continue
        out.append(f)
    return out

def swap(root, flist, t, extra=()):
    changed = {}
    for f in flist:
        p = os.path.join(root, f)
        try: s = open(p, encoding='utf-8').read()
        except (UnicodeDecodeError, FileNotFoundError): continue
        n = s.count('$CAPES') + s.count('$capes')
        s2 = s.replace('$CAPES', '$' + t).replace('$capes', '$' + t.lower())
        for a, b in extra:
            if f.endswith(a[0]): n += s2.count(a[1]); s2 = s2.replace(a[1], b)
        if s2 != s: open(p, 'w', encoding='utf-8').write(s2); changed[f] = n
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticker', required=True); ap.add_argument('--mint', required=True); ap.add_argument('--creator', required=True)
    ap.add_argument('--pit', default=''); ap.add_argument('--logo', default='', help='new coin logo picture (square) for the site'); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    t = a.ticker.lstrip('$').upper()
    if not re.fullmatch(r'[A-Z0-9]{2,10}', t): sys.exit('ticker must be 2-10 letters or digits')
    for k in ('mint', 'creator'):
        if not B58.match(getattr(a, k)): sys.exit('%s is not a Solana address' % k)
    if a.mint == a.creator: sys.exit('mint and creator must differ')
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mc, pit = here, os.path.abspath(a.pit) if a.pit else ''
    if a.check:   # work on throwaway copies
        tmp = tempfile.mkdtemp(prefix='tokenlaunch_')
        def copy(src, dst):   # HEAD plus any uncommitted edits
            subprocess.run(['git', 'worktree', 'add', '--detach', dst], cwd=src, check=True, capture_output=True)
            out = lambda *c: subprocess.run(['git', *c], cwd=src, capture_output=True, text=True).stdout.split()
            for f in out('diff', '--name-only', 'HEAD') + out('ls-files', '--others', '--exclude-standard'):
                if os.path.isfile(os.path.join(src, f)):
                    os.makedirs(os.path.dirname(os.path.join(dst, f)) or dst, exist_ok=True); shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
                    subprocess.run(['git', 'add', '-N', f], cwd=dst, capture_output=True)
            return dst
        mc = copy(mc, tmp + '/mc')
        if pit: pit = copy(pit, tmp + '/pit')
        print('checking on copies in', tmp)
    # 1) the site's "not live yet" lines (before the general swap, so the old text still matches)
    p = os.path.join(mc, 'index.html'); s = open(p).read()
    for old, new, cnt in site_lines(t, a.mint, a.creator):
        got = s.count(old)
        if got != cnt: sys.exit('index.html: expected %d of %r, found %d (the page changed: update site_lines)' % (cnt, old[:70], got))
        s = s.replace(old, new)
    anchor = '</div><p class="mute" style="margin-top:10px">More wallets (game pot)'
    if s.count(anchor) != 1: sys.exit('index.html: Official wallets anchor not found')
    s = s.replace(anchor, wallet_cards(t, a.mint, a.creator) + anchor)
    if a.logo:
        import base64, io
        from PIL import Image
        im = Image.open(a.logo).convert('RGB').resize((520, 520), Image.LANCZOS); buf = io.BytesIO(); im.save(buf, 'WEBP', quality=88)
        s, n = re.subn(r'<img src="data:image/webp;base64,[^"]+" alt="\$CAPES logo"',
                       '<img src="data:image/webp;base64,%s" alt="$CAPES logo"' % base64.b64encode(buf.getvalue()).decode(), s)
        if n != 1: sys.exit('index.html: logo picture not found')
    open(p, 'w').write(s)
    # 2) config.js: mint + ticker + creator (the burn log reads the creator's Snake Bite)
    p = os.path.join(mc, 'config.js'); s = open(p).read()
    s, n1 = re.subn(r'capesMint:\s*""', 'capesMint: "%s"' % a.mint, s)
    s, n2 = re.subn(r'ticker:\s*"[A-Z0-9]*"', 'ticker: "%s"' % t, s)
    s, n3 = re.subn(r'capesCreator:\s*""', 'capesCreator: "%s"' % a.creator, s)
    if n1 != 1 or n2 != 1 or n3 != 1: sys.exit('config.js: capesMint, capesCreator or ticker line not found (or mint already set)')
    open(p, 'w').write(s)
    # 2b) README: the contract address in the token section (repo scanners compare it with the chain)
    p = os.path.join(mc, 'README.md'); s = open(p).read()
    old = "The project's token, its official contract address and every official wallet are listed on the token page of\n[memecapes.com](https://memecapes.com)."
    if s.count(old) != 1: sys.exit('README.md: token paragraph not found')
    s = s.replace(old, "The project's token is $%s on Solana. Official contract address: [`%s`](https://solscan.io/token/%s), launched by the\ncreator wallet [`%s`](https://solscan.io/account/%s). Every official wallet is listed on the token page of\n[memecapes.com](https://memecapes.com), and every burn is in its burn log." % (t, a.mint, a.mint, a.creator, a.creator))
    for row in ("Live from the token's first block (reads the chain once the token address is set)", "Live from the token's first block (reads wallets once the token address is set)", "Live from the token's first block (needs the token address and the pot wallet)"):
        if s.count(row) != 1: sys.exit('README.md: status row not found: ' + row[:40])
        s = s.replace(row, 'Live')
    open(p, 'w').write(s)
    # 3) Watchtower's official list
    p = os.path.join(mc, 'tools/watchtower.sh'); s = open(p).read()
    s, n = re.subn(r'OFFICIAL_WALLETS="([^"]*)"', lambda m: 'OFFICIAL_WALLETS="%s %s %s"' % (m.group(1), a.creator, a.mint), s, count=1)
    if n != 1: sys.exit('watchtower.sh: OFFICIAL_WALLETS not found')
    open(p, 'w').write(s)
    # 4) every readable $CAPES
    ch = swap(mc, files(mc), t)
    print('memecapes: %d mentions in %d files' % (sum(ch.values()), len(ch)))
    for f, n in sorted(ch.items(), key=lambda x: -x[1]): print('   %4d  %s' % (n, f))
    if pit:
        chp = swap(pit, files(pit, ['app/', 'components/', 'lib/', 'public/']), t,
                   extra=[(('battle/config.ts', 'symbol: "CAPES"'), 'symbol: "%s"' % t)])
        print('pit: %d mentions in %d files' % (sum(chp.values()), len(chp)))
        for f, n in sorted(chp.items(), key=lambda x: -x[1]): print('   %4d  %s' % (n, f))
    # 5) what is left
    left = subprocess.run(['grep', '-rIn', '--exclude-dir=.git', '--exclude-dir=scratch', '-F', '$CAPES', '.'], cwd=mc, capture_output=True, text=True).stdout
    left = [l for l in left.split('\n') if l and not any(l.startswith('./' + k) for k in SKIP)]
    print('left over in memecapes:', len(left)); [print('   ', l[:160]) for l in left[:20]]
    print('\nNext: node --check the changed .js, server tests, git diff, commit + push both repos, then set NEXT_PUBLIC_CAPES_MINT on Vercel.')

if __name__ == '__main__':
    main()
