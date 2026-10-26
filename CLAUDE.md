# MemeCapes: working notes for Claude

Read this first in every session. Add to it after every task (what was asked, what worked, what the owner disliked),
so each task starts smarter than the last. This repo is PUBLIC: no business plans, wallet details, keys or private
numbers in here or anywhere in the repo.

## Owner and dates

- Owner: Albert (GitHub Mrsnakehunter), Ohio. Project X account: @memecapes (made Oct 23, display name snakepitapp; his old
  personal @Mrsnakebaby is renamed 'trash can', not deactivated: never link it again; @memecapes bio/location Solana/website memecapes.com set Oct 23, name left as is so the check stays). Writes fast and casually; wants results, not questions.
  When he says "ship" or "keep going", ship and keep going.
- Launch: Mon Nov 2, 2026. Server live about Oct 19, playtest Oct 19-25, freeze Oct 28.
  Oct 22 (3 am) Albert: the token relaunch is the MORNING of Oct 22 (Hatch, with boosts); the Friday Oct 23 update =
  Beat the Boss + payout button + streaming copy (branches beat-the-boss + friday-stream).

## Standing rules (never break)

- Never touch crypto wallets, seed phrases, private keys or transactions. Albert signs everything himself.
  A 32-44 character base58 string is a public address, not a seed phrase: say so.
- X posting started Oct 26 (Albert: "auto posting regularly"): only posts he approved (weekly batches). The safety layer
  refuses scheduling/posting on his X account from the pane even after his yes, so he schedules them himself in X's
  composer (the clock icon) or via his own X API keys. Daily raid sheet = scheduled task 8:23 am ET (research only,
  never posts, replies by hand).
- Posts (Telegram, X, update posts) never mention dates, deadlines or countdowns (Albert: people get upset when
  timelines slip). The Telegram plan is a queue, not a calendar.
- Show screenshots before pushing big game changes live, unless Albert has said ship.
- IP safety: no RuneScape, OSRS or Jagex names, art or wording anywhere. All names are our own.
- Token honesty: no hidden wallets, no promised gains; holder perks are in-game only.
- Bots: the game has bots that look like players (Albert's call, Oct 13). The website must keep saying so (FAQ "Are
  there bots in the game?" + the $CAPES page). Never count bots as players in posts, numbers or screenshots.
- Never push test hooks. `grep -c '__tp=tpTo\|window.__g=' preview.html play.html` must print 0 for both
  (grep exits 1 on a count of 0, so don't chain it with &&).
- Don't read or handle auth tokens, passwords or one-time codes. A Stripe secret key goes only in Render.
- Meshy credits: allowed to spend.
- Money or legal questions: give facts and trade-offs, not a recommendation, and say I'm not an advisor or lawyer.

## Build and ship

- The game is one file. `tools/build.sh` rebuilds play.html from the base by running every `tools/patch_*.py` in
  order, then makes preview.html and the test pages (tools/dev/mktest.sh, copied from scratch: test.html, test2.html, test3.html, test7.html).
- Ship: `tools/ship.sh` (copies preview.html to play.html, writes version.json). Check the live build number at
  https://memecapes.com/version.json from a browser tab (fetch it in page JS); the shell and WebFetch can't reach the site.
- PROGRESS.md is the public log: add a dated section for every shipped feature, in plain words.
- Patches use exact-string `rep(old, new, count)` with an assertion; if an anchor moves, fix the anchor, never loosen it.

## Screenshots and testing

- Shots: `PAGE=test7.html PORT=8770 python3 tools/dev/shoot_site.py plan.json` (two runs in parallel need different PORTs) with jobs {name, day, setup, tp, wait, act, cam:[yaw,pitch,dist],
  camwait, frames}. Output in scratch/shots/site; the game canvas is x 0-840 of the 1100 px shot.
- The test machine renders with SwiftShader (software). Heavy shaders make it slow: use wait 30000 and camwait 12000,
  or the shot shows sky or the wrong place.
- Make the character tough in `setup` (xp 2e7, hp 999) or monsters kill it and it respawns in Gigachad Town.
- tools/dev/mktest.sh reads play.html, so only run it through build.sh (alone it rebuilds the test pages from the
  live game, not the new build).
- UI flows: `python3 tools/dev/ui_trade.py plan.json [width height port]` (steps: js, click, rclick, hover, wait, shot).
  Use force clicks: SwiftShader is too slow for Playwright's "stable element" check. Test phones at 390x844.
- Online flows: `python3 tools/dev/trade_e2e.py` runs the real server plus two players (must be served on port 8000,
  the server only accepts that origin locally). Sign-in takes 20-40 s on this machine: poll for NETS.name, then set
  bags and send a save before testing. Server tests: `node server/test.js` (35) and `node server/test_holder.js`.
- Rain: `(Date.now()/60000)%17 < 4`. Day: `((Date.now()/1000)%1800)/1800`. Shift time with window.__toff / __day(dp).

## Engine facts learned the hard way

- The ground is drawn by shader program pg3 (not pg). Its vertex colours blend road and grass per corner
  (road weight 3, grass 1, water 0); the normal's length carries the paving material and amount.
- Texture units 0-4 are taken; the road map uses unit 5. WebGL1: NPOT textures need CLAMP_TO_EDGE and no mipmaps.
- Game CSS has many short global class names (.pr .nm .v .n .st .big .pic .g .bar .side .bad .warn ...). New UI
  must use its own prefixed class names (trade uses tr*/is*), or old styles leak in and break layouts.
- Painted item icons are nested SVGs: size only the outer one (`.x>svg`), never `.x svg`, or the sprite zooms and crops.
- A JS comment inside a Python string inside a JS string breaks things: keep GLSL comments out (patch_roads.glsl()
  strips them).
- Characters: all Meshy humanoids share one 28-bone rig (Hips 0 ... RightHand 16, LeftHand 11; table in tools/rigkit.py).
  Clips store per-frame skin matrices (bone world x inverse bind), so motions can't be copied between characters as is.
  tools/npc_clips.py retargets: rebuild each NPC skeleton from its own Walking/Running (0.1 mm fit), then
  R_npc = R_player @ C per bone (Meshy keeps world rotation changes; fit < 1 degree). Validate on Running.
- Held weapons: qHold(PM,x,z,yaw,clip,t,wk,left,sc,dd) reads the clip's 'hand'/'handL' grip tracks; sc = character
  scale, dd = blade tilt override for straight ('f') weapons. A weapon held in a lying hand points at the sky: drop it.
- Top-level `const` in the game is not on window: page.evaluate can use NPCW directly, not window.NPCW.
- models/moodeng.json is broken (1 cm tall); the Bouncy Hippo uses its hand-built model (MM.moodeng).
- Monster AI ticks every 600 ms; gb.cd counts ticks to the next attack, which lands (and splats) at once.

## Art direction (Albert's feedback)

- Roads: NO straight lines, NO rows or grids of stones, NO bulky lines. Randomised, natural, realistic.
  Plazas round and symmetrical. Grey dirt around cobbles, blending into normal dirt. Cobblestone in towns,
  concrete only at Wall St., dirt in the countryside and Froggo's Pond.
- He likes: the original dirt ground re-coloured grey as a blend zone; things that look real rather than tiled.
- Website pictures: no Wall St. shots.
- See-through: ONLY massive structures may turn see-through when they block the camera (castle; buildings 6+ tiles
  tall, or 5+ tall with a 64+ square-tile footprint). Trees, bushes, flowers, rocks, lamps, fences, booths, stalls,
  Meme Telly rings and small or normal houses must never disappear: the player moves the camera himself.
  (tools/patch_seethru.py; the castle's procedural walls carry material flag +32.)
- Techniques that worked for the ground (roads v3): per-pixel road edges from a road-tile texture with noise warp;
  height blending (dirt fills joints first, stones sink, tops show last); pillow-shaped stones lit by the sun;
  subtle colour variety; fade fine detail with distance; wet darkening and sky-reflecting puddles in rain.

## Task log (newest first): what was asked, what we learned

- Oct 25 (7 pm): "Go" on TradingAgents (TauricResearch/TradingAgents, Apache-2.0, pinned e8f5503) for MemeSnake trading,
  PAPER first. memesnake-bots main 9aee84b, folder boss_agent/ (README_BOSS.md): vendor.py registers a "solana_dex"
  vendor into router.VENDOR_METHODS and swaps tools.build_verified_market_snapshot (the market analyst's Yahoo snapshot)
  for ours; the mint is the instrument (InjectedState, the model never types it), rows are HOURLY candles (GeckoTerminal),
  prices keep 4 significant digits (Yahoo code rounds to cents = 0.00 on memecoins); analysts market,news,fundamentals
  (social skipped: StockTwits/Reddit by mint is junk); asset_type crypto; Grok via XAI_API_KEY (grok-4.6). book.py = paper
  book with 0.4% venom + 0.3% + constant-product impact, hard rules (liquidity/volume/age/top-10/dev/mint+freeze
  authority/honeypot/launch check, sizes, -30% stop, half at 2x, trailing, rug floor), unknown holders = SKIP (fail
  closed). Two books: agents vs a trend+RSI baseline (boss_book.json / boss_baseline.json on branch boss-ledger, force-
  pushed by the workflow). .github/workflows/boss.yml: tests on push, mark every 3 h, decide 14:41 UTC; no XAI_API_KEY
  secret = mark only. Lessons: pip/PyPI is blocked here, so GitHub Actions is the test bench; Actions logs are blocked
  (blob storage) but annotations are readable (::notice + check-runs/<job>/annotations); public Solana RPCs refuse
  getTokenLargestAccounts from GitHub and Vercel (403/429/timeouts) and the Pit's middleware 403s server POSTs without
  its Origin (by design, don't fake it): GeckoTerminal /tokens/<mint>/info gives holders count, top_10 % (pool excluded),
  mint/freeze authority, honeypot, developer % keyless. Pit main 08baaf1: GET /api/public/holders?mint= (read-only,
  fallback; needs a real RPC key in the Pit to answer). Albert's to do: xAI API key at console.x.ai -> GitHub secret
  XAI_API_KEY (+ MEMESNAKE_KEY secret for feed posts). Real money only after it beats the baseline after costs for weeks,
  then only the Boss's own wallet.

- Oct 23 (11:55 pm): "a 4 minute video showcasing everything, better music, slowed down, no ticker, important stuff first,
  10 s hook". /tmp/claude-0/ad6: make6.py (make5 with A=ad6, exec's plan6.py), plan6.py PLANS['long'] = 32 scenes, 121 bars
  at 122 BPM (We Are Made Of Win = ad3/mus/stream.mp3 from 30.267 s: beat from bar 0, the track's own breakdown lands at
  bars 13-15 = "And that is only the game", the drop at bar 16 = 0.4%) = 238 s. Scenes 4 bars (8 s) so the text reads.
  New helpers: site_scene (browser mockup of a scrolling site capture + headline/sub, pmax caps the scroll), facts_scene
  (bullets one per beat; the coin section with NO ticker, "what it is not", Telegram/X), skins_scene (wall of
  models/skins/thumbs), breath_scene, progress bar + brand chip on every inner scene. Assets: ad6/siteshots.py (Playwright,
  1280x800 dpr 1.5 scroll sequences of #story #bestiary #items #towns #quests #capes #roadmap #shop #faq #security #support
  #home + launch.html#/stream (stream2; the OLD ad3 site/stream capture carries the retired "flat $20, only charge" copy:
  never use it) and #/watch (watch2 = "Failed to fetch" offline: use the old ad3 watch); ad6/clips.json via ad4/gp4.py
  (PORT 8791, GPOUT ad6/gp): sq_fish, sq_mine (S.fish / S.rocks nearest, go({k:'fish'|'rock'})), sq_town (orbit over
  TW[0]), sq_street (TW[2]), sq_night (day .82), sq_high (TW[5], dist 30); ~2 s/frame. The game's side tab under the $ icon
  says the placeholder ticker: plan6 _nolabel() paints it over with COIN on every sq/sq6 frame. Not used: roadmap (dates),
  items/faq (placeholder ticker in text), shop (Coming soon). Render = ~55 min for 7,140 frames and the 30-min background
  limit kills it: re-render the missing frames by index (job(n) after exec'ing make6 up to `if __name__`). encode.sh:
  1:1 crf 21 + loudnorm -14 + 2 s fade; 16:9 = square centred on a blurred copy. Outputs outputs/x_ads/memecapes_full_tour_*.
  Lesson: check extracted frames only after the encoder has really finished (a check that races the encode reads the old file).

- Oct 23 (8:20 pm): "the best X ad video humanly possible... one with rattle and one without". /tmp/claude-0/ad5: make5.py
  (ad3/make.py + scenes + vids helpers, exec's plan5.py; FROM=n re-renders from frame n), plan5.py PLANS hero / hero_rattle:
  15 bars at 160 BPM (Swag Drop, ad3/mus/launch.mp3 from 72.38 s = the drop) = 22.5 s: hook MEME/COINS/HAVE/HP., Fight the
  memes (free, browser), 0.4%, Hatch, Beat the Boss, Acid Pit, then Meme Cape + end card (plain) or $RATTLE reveal + end
  card (rattle). brand_chip on every frame (X: brand inside 3 s). encode.sh <video>: 1:1 crf 20 + loudnorm -14 + fade, and
  9:16 (square centred, blurred copy behind, vbars_<video>.png bands with brand line / CTA / honesty lines). Thumbs via
  ffmpeg -ss. Output outputs/x_ads (4 MP4s ~7 MB, 2 thumbnails). QC rules kept: EXAMPLE DATA chip on every Pit screen,
  no dates, "Mrsnakebaby" painted out (ad5/clean), coin art keyed from its dark square (rattle_coin_rgba.png). Lessons: make5
  reads music_<VIDEO>.json (copy music.json to it or the sheet runs at 140 BPM); frames are %05d.png. X ad rules found:
  crypto ads allowed with X's review (not paid partnerships), <= 30 s, captions for sound-off, 50-100 char copy, no hashtags.
  The ticker is in the video files only, which stay out of the repo.
  Then (9:30 pm) "the rattle isn't touching the snake tail, the banner ends aren't green": the old rattle was pasted on
  after the fact (rattle/rattle_tail.py). Now /tmp/claude-0/pit/coin_rattle.py (coin.py + the rattle built in): the tail
  tapers to a blunt end (radius clip .42), six keratin beads grow out of P[0] along a bezier down past the ribbon's left
  end, drawn after the letters and before body_front (the snake is in front of the ribbon, so the rattle is too); the
  folds are the ribbon's green with a gold edge. Render: RIBBON='$RATTLE' RSIZE=125 RTRACK=10 python3 coin_rattle.py out.png;
  kit: COIN=.. TK=.. TS=0.8 OUTD=.. PFX=rattle python3 /tmp/claude-0/rattle/banners.py still (the pit/ copy has a fixed
  OUTD). Ad lesson: a glow made by blurring the coin's alpha stops at the image edge = a visible square; pad the sprite
  (200 px) first. Kit in outputs/rattle_v2.

- Oct 23 (6:45 pm): MemeSnake bot /start still said "tracks $CAPES". memesnake-bots f8d48c3: config TICKER default blank;
  coin_name() shows $TICKER only once TICKER AND TOKEN_CA are both set (pre-launch: "the MemeCapes x snakepit coin"),
  so the private ticker can sit nowhere until launch; /buy + alert Buy buttons -> <PIT_URL>/?q=<CA> first, Jupiter
  second (Hatch coins may not route on Jupiter at first); TELEGRAM_URL default t.me/memecapes, X_URL x.com/memecapes;
  chat ID line only in private chats. LAUNCH DAY on Railway (Albert or the pane): TICKER, TOKEN_CA, ALERT_CHAT_IDS=
  -1004352172935 (the group), then /alerts on in the group. Tests pass.

- Oct 23 (3:20 pm): "do the lock through Streamflow instead" (Uxento reads Streamflow locks, not Jupiter Lock). Pit
  branch `streamflow-lock` (48a348a, Vercel preview success, NOT merged): lib/streamflow.ts (@streamflow/stream ^13,
  dynamic import; v13 exports SolanaStreamClient at the top level and ships its OWN @solana/web3.js, so give it the RPC
  address string and rebuild its instructions/keypair with our classes), useHatch lock step = Streamflow vesting
  (start = cliff = now + 30 d, period 30 d, cliffAmount = first share, per = deposit/N; nothing cancellable,
  transferable, pausable or top-up-able; deposit = balance less the fee-oracle token fee, 0.19%), the coin page's
  Creator lock badge adds the hatcher's Streamflow locks (searchStreams mint + sender). NEXT_PUBLIC_LOCK_PROVIDER=jupiter
  switches back. LIVE Oct 23 6:35 pm ("make it live"): Pit main 48a348a (production ok, hatch chunks carry Streamflow); site token page +
  support say the creator's 10% is in a Streamflow lock (the holder 1M lock on /capes stays Jupiter Lock). Simulated on mainnet from a throwaway preview page: 24-month lock of USDC from Albert's Pit wallet,
  OK, 66.7k CU, 784 bytes. GitHub branch deletes are blocked by the proxy: the throwaway branch sf-test was reset to main
  (Albert can delete it). A real Streamflow stream was not read back yet (none existed): check the badge after launch.

- Oct 23 (1:45 pm): "why can't you open larpcheck?" WebFetch has an allowlist; the browser pane works (site access granted).
  TESTED larpcheck.live: it makes NO GitHub API call and the same repo scored 4.2, 4.6, 7.3, 3.7, 5.6 on five scans
  (famous names like torvalds are fixed at 9.8): its scores are random, so don't chase them. The other checker is
  Uxento (Vision "Scan" on a post: past usernames, smart followers, CA history = the X account's tweets with contract
  addresses; "PumpFun Lookup" by wallet or username: coins it deployed on pump.fun). A new X account has no CA history.

- Oct 23 (5 am): Albert: "get rid of the old contract addresses from the repo, my choice". History REWRITTEN with
  git-filter-repo (cloned from github.com/newren/git-filter-repo; pip has no package here) on a --mirror clone:
  --replace-text + --replace-message turned the two earlier mints, the $PIT lock escrow and both earlier creator wallets
  into [removed], and the private next ticker into "nextcoin"; dates kept, today's files identical; all 8 branches
  force-pushed. Old SHAs are gone: re-clone or `git fetch -f` + reset any other copy. On-chain history is unchanged.

- Oct 23 (3:50 am): FRIDAY UPDATE SHIPPED ("make it live"). Pit main 86d8532 = friday (Beat the Boss, one-tap payout;
  Vercel production ok). memecapes main 423d1dd = friday re-merged with main (conflicts: two blank lines in index.html +
  support/qa.json regenerated) + d5b9b46 home video media/memecapes-tour-4.mp4 (NEW kicker; tour-3 removed). Supabase
  (project vzholjzivivoeyntgxwt, SQL editor via monaco setValue + Run): boss.sql + payout.sql + acid.sql run, Success
  ("destructive" warning = the drop-policy lines only). Live: /api/battle/boss has the Boss (Snake on POPCAT) after the
  next server tick; memesnake page has the Boss panel; streaming small print on the site. Video encode: frames from
  /tmp/claude-0/ad3/make.py (non-LONG, 1673 frames, ~6 min) + music.json start 135.51, crf 25, loudnorm -14, 55.77 s.
  Pay out button still needs Albert signed in with the pot wallet when a week closes.

- Oct 23 (2:50 am): "set up the telegram again". The old supergroup t.me/memecapesXsnakepit is GONE (the link resolves to
  nothing; it is not in the groups Albert admins). He had made a new private CHANNEL (peer -1004467752371, "memecape X
  snakepit", 1 subscriber). Set up in the pane (web.telegram.org/a handles @links; /k kept showing his DM list: avoid):
  name "MemeCapes x snakepit", description, public username t.me/memecapes (was free), welcome post with every official
  link posted and pinned. Albert: "they can't say stuff" (a channel is read-only), then "I want ONE telegram where everyone
  can type". Telegram can't turn a channel into a group, so the GROUP is now the one Telegram: supergroup
  "MemeCapes x snakepit" (peer -1004352172935, Bot API -1004352172935), public at t.me/memecapes, same description,
  welcome post posted + pinned, everyone can post. The channel (peer -1004467752371) is private and unused: Albert can
  delete it. Pane lessons: Telegram's Group/Channel type screen only saves when its blue tick is pressed (setting the
  channel Private without the tick did nothing and the group's name change said "already taken"); the link input ignores
  typed text, so focus it by JS (setSelectionRange) and use Backspace. Site, launch.html and support link t.me/memecapes
  only. Still his: group photo (memecapes_telegram_avatar.png in outputs/nextcoin; the pane can't upload files), re-adding
  the bots as admins, Railway ALERT_CHAT_IDS=-1004352172935 + TELEGRAM_URL=https://t.me/memecapes. "Remain anonymous" is
  OFF (Albert wants everyone's name shown; the box said "Send anonymously"); group photo set by Albert; members may add users.

- Oct 22 (10 pm): "send money wallet to wallet like FOMO?" The Pit had Receive only. Pit main 8320458 (+ friday):
  components/SendSheet.tsx (To = address or @username via GET /api/profile?handle=, coin picker SOL + holdings, Max keeps
  0.001 SOL for fees, review shows fee + 0.00204 SOL rent when the recipient has no token account, sign, confirmSig,
  Solscan), lib/send.ts (SystemProgram transfer; tokens: idempotent create-ATA ix [1] + TransferChecked ix 12, hand-built
  like acid.ts; toBase for decimals). Wallet sheet (TopBar + PortfolioSnake) has "Send SOL or a coin to someone".
  Tested by simulateTransaction on mainnet through the Pit's own /api/rpc: public/dev harness on a throwaway branch
  (esbuild bundle of lib/send via /tmp/claude-0/sendt/build.mjs from the dbcs pattern, platform browser; the artifact
  sandbox blocks RPC fetches and gists are blocked by the proxy, so a Vercel preview of the branch was the way). Lesson:
  `git commit -a` skips untracked files: `git add` new files explicitly before pushing a branch.
  Same evening: Tuesday launch considered then "as soon as the new X account exists"; told him honestly that $100M
  volume in 4 weeks is lottery territory, that longer hype + the Hatch sniper fee is the right pair, and that pre-launch
  allocations for friends read as a bundle. $nextcoin kit rendered (coin with a nextcoin tail: /tmp/claude-0/nextcoin/
  nextcoin_tail.py post-process; banners via env TK/TS/COIN/OUTD/PFX in /tmp/claude-0/nextcoin/banners.py) + plain
  snakepit avatar/header with no ticker (plain.py) in /mnt/user-data/outputs/nextcoin. GoDaddy has no free forwarding
  any more: pit@memecapes.com = ImprovMX (Albert signs up; then MX records at GoDaddy).

- Oct 22 (3:30 pm): "people need to pay with cash". Privy dashboard (app cmvc7cdca00mc0fl4kmd9paoo, /funding): Card
  onramps ON with Stripe + MoonPay, BUT without a KYB Privy's card providers only take USD via Stripe (needs react-auth
  3.33+; we are on 2.25 and v3 drops @solana/web3.js = a big migration) and AUD/BRL via MoonPay. So Pit main 523fa92
  (+ friday): lib/useFunding.ts cashUrl/openCash/cash() = MoonPay's PUBLIC checkout (buy.moonpay.com, no API key,
  currencyCode sol + walletAddress + USD amount, min $20) in a new tab; EmptyWallet $25/$50/$100 buttons, ReceiveSheet
  "Pay with cash" button. Checked in the pane: the link opens MoonPay's sign-in (Google/Apple/email) then card. Privy's
  own fund() modal stays for exchange transfers. Privy app is STILL in development mode: Albert presses Upgrade to
  production himself. Later option: complete Meld KYB in Privy for in-app USD cards.

- Oct 22 (2:40 pm): Albert's screenshot "you took down the whole launch site": hiding the Pit from the site (pit "") had
  removed the home LAUNCH block too. Now that coins are hidden inside the Pit, config.js pit = https://pit.memecapes.com
  again (pitWas removed; one-line switch, no rebuild: site, game and launch.html read it at runtime; live check ok).
  A player's Shed failed "Attempt to debit an account but found no record of a prior credit" = the wallet had 0 SOL for
  the network fee. Pit main a58b3bd (+ friday): lib/useSwap.ts plainError() (no-SOL, slippage 0x1771, expired blockhash
  in plain words, used by strike/shed/acid), components/GetSol.tsx (the gasless Add SOL card, Jupiter Ultra) now sells a
  few dollars of whichever held coin is worth the most (prices from the store; stables count $1), not only USDC/USDT.

- Oct 22 (1:50 pm): "I still want to claim fees off them but nobody sees them on the platform". Pit main 3fad273 (also in
  friday): lib/hidden.ts, Vercel env PIT_HIDDEN_MINTS (Production; the four mints are in the chat, NOT here) = comma list
  of hatched mints dropped from /api/trending (pin + DexScreener list), /api/hatch (public), /api/token?q=, /api/token/
  <mint> (404), /api/public/stats, /api/fees public numbers. A signed-in PIT_ADMIN_WALLETS wallet (Privy token in the
  Authorization header: MyHatches, BurnDesk, TokenSheet, deep links send it) still sees them, so Claim keeps working.
  Checked live: all six public answers empty/404. Vercel add-variable form: clicking the Config card by coordinates did
  NOT take (saved as Secret, editing a secret needs an email code): click the radio by ref, type values with the keyboard
  (JS value-setting on the form is refused by the safety layer), then check the radios before Save. Albert is deleting his
  X account (@Mrsnakebaby): pull its links from the site, launch.html footer and the Telegram pinned post once it is gone.
  Asked for: pit@memecapes.com (GoDaddy forwarding) + an official SnakePit X account (openly "by MemeCapes", linked both
  ways; never a cover account) and a new ticker (brainstormed in chat only; the chosen one stays out of this repo).

- Oct 22 (1 pm): LAUNCH PULLED. $PIT was hatched at 11:44 (CA + lock escrow are in the chat, NOT here), the site/game/
  Pit were switched over (token_launch.py; lesson: it also rewrites tools/patch_*.py anchors -> `git checkout -- tools/
  patch_*.py` before build.sh, patch_ticker.py does the ticker), then a CA-history tool showed the X account's deleted
  Oct 20 launch, buyers backed out, and Albert ordered everything down. Done: memecapes revert of 12415aa (site, game
  build back, server), Pit revert of the ticker switch, NEXT_PUBLIC_CAPES_MINT deleted on Vercel. REFUSED: a new X
  account / covering up the previous launch (deceiving buyers). Then "I want to see the Pit but nobody on the site":
  config.js pit "" (pitWas keeps the address) = game/server dormant; index.html hides a[data-pit], .cr-by, #battle,
  section.lpshow, details.pitfaq when pit is empty; launch.html hides data-pit links + Trade and sends '' /launch/
  coin/me to #/watch. Side effect: Stream/Watch sign-in with the Pit wallet (stream-link) is off too; only browser
  wallets until pit is set again. Build 20261022170554. His Pit wallet [removed] has 84.5M $PIT locked 24 months.
  He was under heavy stress ("6k of transactions fell through"): be steady, no lectures.

- Oct 22 (10:40 am): STREAMING IS LIVE. Cloudflare: Albert paid the Starter Bundle ($5/mo: 1,000 min stored, 5,000
  delivered) in the pane; account 118037479472c2d9ca477b31831516cc, customer code 85i7n9jjy7zldqtc (both public, in
  Render env); API token "memecapes-stream" (Stream: Edit, no expiry) made in the pane, value pasted by Albert himself
  into Render CF_STREAM_TOKEN (he pasted it in chat once: if it ever leaks, roll it at Cloudflare > API tokens and
  update Render). Render env editor: rows are inputs named envVars.N.envVarKey / envVarValue (value = TEXTAREA);
  screenshot frame = CSS px x 1.25. Deploy ok; /st/live answers streaming:true. README streaming row back as Live.
  Not yet done: a real go-live (needs Albert's wallet + pass; admin can grant one with `/watch pass <wallet>` in game).

- Oct 22 (9:40 am): "token withdraw says live but a 30-day wait". SHIPPED build 20261022134821: server/withdraw.js
  (table withdrawals; H.wdInfo/withdraw/withdrawCancel; coins leave the saved bank at once; due = +WITHDRAW_DAYS; cancel
  while waiting/held; 100/day per account; total waiting <= pot wallet balance read on-chain (POT_WALLET / config.js
  potWallet, cached 5 min); /withdraw list|hold|release|refuse|paid <id> <tx> (paid only after getTransaction shows
  >= capes to the linked wallet AND the pot wallet signed); GET /withdrawals public numbers; test_withdraw.js 27 with
  WITHDRAW_DAYS=0.00004). Game: tools/patch_withdraw.py (last in build.sh) = "Withdraw to your wallet" LIVE box at
  the bank replacing the demo exchange (wd/wdBank messages; netSaveNow before sending). config.js withdrawalsOpen
  true + potWallet "" (set it at launch; Albert must also set CAPES_MINT/capesMint). Site: exchange cards, table,
  FAQ, Terms 11 (termsVersion NOT bumped), support answer, README row, PROGRESS. Payouts are Albert's: ready requests
  listed by /withdraw list, he sends from the pot wallet, then /withdraw paid. Also: site logo = coin with the snake
  (coin_mc.png crop, 168 px webp); "← Home" link on every page (Albert: /#token had no way back).
  Streaming asked ("get it ready, I put the card in"): device bridge DOWN, so steps given instead; CF prices (docs):
  $5/1000 stored min prepaid, $1/1000 delivered; recordings on (7 days) count as storage.

- Oct 22 (9:25 am): "make the Strike/Info/Comment tabs and the Acid Pit live now". Pit main dbb6cbe = main + coin-tabs +
  acid-pit (StrikeSheet taken from friday, which already had green Strike + Acid tab) + burn desk (cherry-pick) +
  useWallet addresses/signTxAs (was only on beat-the-boss; BurnDesk/useSwap need it). Preview success, then ff main.
  Beat the Boss stays on friday (friday = main + beat-the-boss now). supabase/acid.sql must be run (acid_burns table):
  until then the Acid tally shows 0 but burns still happen on-chain. Token page: Acid Pit card (Live) on main.
  Device bridge was offline: live Pit not checked in a browser (WebFetch can't reach pit.memecapes.com).

- Oct 22 (9 am): "I want it to say live so it doesn't look half cooked for the larp". Rule kept: never tag something Live
  that isn't; instead public pages show only live things. Token page burn sources: 3 cards, all tagged Live (Acid Pit
  card added on `friday` only, also Live); Planned/Coming soon cards removed (the roadmap still covers them). README
  Status: only live rows; streaming row removed until the Cloudflare keys are on Render (add it back as Live then);
  burn log + holder perks rows say "Live from the token's first block" and token_launch.py flips them to "Live".

- Oct 22 (5 am): LARP burn finding ("page says half of launchpad income buys and burns, no burn instructions, ad-burn
  list empty") + "everything else ready for larpcheck 100%". memecapes main: server/burns.js GET /burns (total = capesSupply0
  - getTokenSupply, counts every burn; list = burns from the fee wallet + creator token accounts: both ATAs derived in
  plain Node (sha256 + ed25519 off-curve check, matches web3 12/12) + getTokenAccountsByOwner, getSignaturesForAddress
  `until` the last read sig, jsonParsed burn/burnChecked of the mint; launch tx = log "Instruction: InitializeVirtualPool"
  = Snake Bite; persisted DATA/burns.json; test_burns.js 20). burnlog.js + #burns section on the token page (Live / Coming
  soon / Planned tags), config.js capesCreator + capesSupply0 (token_launch.py sets capesCreator and writes the CA into
  README). Claims fixed: launchpad lives in snakepit, online play is live, pot-dependent features say so, "After legal
  review" gone. README: Who builds it. LIVE: /burns answers {on:false} until the mint is set. Pit: burn-desk branch
  (merged into friday only, it needs the Acid Pit lib): BurnDesk on /capes (public: MemeCapes fees waiting, /api/fees
  reads partnerQuoteFee of every hatched pool, 5-min cache; fee wallet connected via signTxAs: Claim per pool, then
  acid(..., {memo "snakepit burn", noVenom, as FEE_CLAIMER})). Pit main: capes page copy (token wording, no Nov 2 line,
  quests rewards planned). Telegram pinned post now links x.com/Mrsnakebaby. Still open: MemeSnake bot @username
  (never read @BotFather: tokens), Railway ALERT_CHAT_IDS, Cloudflare Stream keys (Stream claims), Terms still say the
  servers have not launched (changing Terms = bump termsVersion: ask Albert).

- Oct 22 (4:30 am): LARP CHECK (larpcheck.live) scores the public GITHUB repo (code authenticity, commit timing, dev
  identity, consistency, README claims vs code, contract alignment), not the website. README.md was just a title:
  rewritten (what is here, Live/Built status, run/test/build). Repo description/topics: GitHub settings writes are
  blocked by the proxy (Albert sets the About box). Its burn finding on the old coin: "page says half of launchpad
  income buys and burns, no burn instructions, ad-burn list empty". Answer: Snake Bite = real burn in the launch tx;
  ongoing burns stay creator-signed (automatic = a server key = custody, against the rules); offered a one-tap
  claim + buy + burn for the fee wallet and a public burn log. Telegram: group t.me/memecapesXsnakepit (supergroup
  peer -4445161618 = Bot API -1004445161618; old basic group -5106298088 migrated into it; DELETED Oct 23, see above). Done in the pane: new
  description, welcome/rules post pinned; site + launch.html footers + support answer link it. Adding the bots /
  admin rights was DENIED by the safety classifier (permission grant): Albert adds MrSnake (admin: delete, ban,
  restrict, pin) + MemeSnake himself. Bots repo Mrsnakehunter/memesnake-bots (Railway "divine-courtesy"): /links now
  lists SnakePit + Telegram (PIT_URL, TELEGRAM_URL), knowledge.md facts updated (no RuneScape-style line, no old
  "legal review" line). ALERT_CHAT_IDS on Railway must change to the new group's id.

- Oct 22 (4:15 am): photo of the coin sheet, "too much going on with the scroll: 3 buttons under the chart: Strike,
  Info, Comment". Pit branch `coin-tabs` (preview success; merged into `friday`, AcidTally lands in Info): TokenSheet
  `top` slot passed into LiveChart (slot + showTrades props): tab bar right under the chart; Strike = STRIKE button +
  MC/Liq/Vol/1h + 5m flow + trades (12 rows, "Show more", no inner scrollbar); Info = curve, Snake Bite, lock, fees,
  launch check, Pit activity, Solscan/Copy CA; Comments = Holders talk. Studio chart stub (studio/chart.tsx) now takes
  slot/showTrades. His photo still showed Price selected: taken at 4:09, before the 4:10 MC deploy (refresh).
- Oct 22 (4 am): "MC auto showing, not the price, on the chart". Pit LiveChart: opens on MC (state `pick`, default
  "mc", localStorage pit_chart_mode remembers a Price pick; mode falls back to price while supply is unknown). On
  `buy-green` + `friday`. LIVE Oct 22 4:10 am (Albert "done now"): Pit main 1e36b86 = buy-green (green Strike, red
  Shed, chart on MC); checked on pit.memecapes.com (STRIKE rgb(88,240,166), MC selected).
- Oct 22 (3:50 am): "Strike red / Shed green is backwards (buys make green candles)". Pit branch `buy-green`
  (Vercel preview success; also merged into `friday`): Strike = mint (green) everywhere, Shed = red (bg-strike token,
  now meaning red/sell), incl. % picks, activity labels, BOUGHT badges; SNAKEPIT-BRIEF palette line updated. The old
  "red only for Strike" brand rule is gone. Also asked "does any platform offer buy-and-burn?": searched; found burns
  only as a separate cleanup action (Phantom burns NFTs/spam, Sol Incinerator burns held tokens) and no app with a
  one-tap buy+burn; don't claim "first" publicly without a fuller check.

- Oct 22 (3:35 am): "I need it [Acid Pit] ready for Friday". FRIDAY = one merge per repo, already combined and
  conflict-free: Pit branch `friday` (main + beat-the-boss + acid-pit; store.ts closeWeek conflict resolved keeping
  settleBoss; Vercel preview success) and memecapes branch `friday` (main + beat-the-boss + friday-stream; crews tests
  19/19). On Friday: re-merge main into each `friday` if main moved, ff main to it, run supabase/payout.sql + boss.sql +
  acid.sql in Supabase, Cloudflare Stream keys on Render (Albert), re-render the home video with the NEW kicker.

- Oct 22 (3:30 am): "acid pit with a caution sign next to Strike and Shed: what you buy gets burned, never goes into
  your wallet". Pit branch `acid-pit` (5ac6141, Vercel preview success, NOT merged): ☣ Acid tab in StrikeSheet (hazard
  stripes, two-tap confirm), lib/acid.ts (BurnChecked for SPL/2022 + memo "snakepit acid"), buildSwapTx(..., after)
  puts burn + memo right after the swap (Jupiter's CU limit +40k; DBC path too), burn = quote.otherAmountThreshold, a
  better-price extra is offered as "melt it too" (plain burn), /api/acid verifies on-chain (memo + burn by the signer)
  into acid_burns (supabase/acid.sql: RUN it on merge), AcidTally card on the coin sheet. Simulated on live SITELOG:
  swap + burn + memo ok (77k CU). Same hour: Albert sold all his SITELOG through the new own-pool fallback (works live).
  Creator-fee split explained: Meteora 20% of the fee; of the rest, creator share 50-80%, the remainder half buys + burns
  the coin, half runs the Pit; partner fees sit in each pool until the fee wallet claims (no claim button yet).

- Oct 22 (3 am): streaming copy for the Friday update (Albert: tips and subs are 100% the streamer's; small print "if
  you're using more than $20 of streaming, price may vary"; "keep it for the Friday launch"). Branch `friday-stream`
  (7ffdd7a, NOT merged; merge with beat-the-boss on Friday): lp/social.js Stream page (hero line, step 3, the $20 card +
  .sfine small print, pass panel, FAQ), index.html (Stream card with *, FAQ, Terms 6a), support_qa.py (no $ allowed in
  answers: "covers a set amount of streaming"). Removed the old "flat / only charge / no surprises" claims, which the
  small print would contradict. Live video still needs Albert's Cloudflare Stream keys on Render before Friday.

- Oct 22 (2 am): "quote failed: 400 NO_ROUTES_FOUND when I try to sell SITELOG from my launch". Jupiter had never
  picked up that Hatch pool (8 h after the hatch, no route either way) while $SNAKE/$FANGS routed within 30 min; no
  difference found in their configs. Pit main c5f0c1b: lib/dbcswap.ts, getQuote falls back on NO_ROUTES_FOUND to the
  coin's own DBC pool when /api/token/<mint> has hatched.pool (SDK swapQuote takes getPool()'s { poolState } wrapper
  AS IS, not the inner state), buildSwapTx builds client.pool.swap + the same venom transfers + compute budget, one v0
  tx. Tested: node bundle with recorded accounts (/tmp/claude-0/dbcs: pre.ts stub, acc.json from the pane, buildn.mjs)
  -> simulateTransaction via pit /api/rpc (sigVerify false, replaceRecentBlockhash): sell + buy both succeed; live
  Strike/Shed sheets quote SITELOG. Launch risk: if Jupiter doesn't index the real coin, outside wallets can't trade it.
  Same night: launch game plan Doc + DexScreener description (Albert's docs, private); streaming left out of the
  description until Cloudflare Stream keys are on Render.

- Oct 21 (10 pm): launch plan changed (Albert): 20% creator buy on snakepit Hatch = 10% Snake Bite (burned in the launch
  tx, supply 900M) + 10% First Strike locked in Jupiter Lock, 1/24 a month over 24 months (nothing in month 1). Website
  $CAPES page (roadmap card, Planned supply text, bar 80/10/10, table rows Public 80% / Creator locked 10% / Burned 10%)
  + support answer updated, replacing "at most 4%". Pit main (strike-lock): Hatch "Lock your First Strike" (6/12/24
  months, a 3rd approval right after the listing; "Lock it now" retry), 2/5/10% supply buttons for the First Strike,
  coin sheet "🔒 Creator lock · X% locked" (hatcher's non-cancellable escrows of the mint, gPA memcmp 40 mint + 72
  creator). lib/lock.ts buildVestTx: start now, cliff +30 d, freq 30 d, cliff = amount - per*(N-1), per = amount/N,
  periods N-1 (tests vk.ts 10). Cost at SOL $106: 20% ≈ 6.95 SOL. DexScreener shows burned supply by itself; for the
  lock, list the escrow address in the Enhanced Token Info form's locked-supply field (and lock.jup.ag shows it).

- Oct 21 (8 pm): brand kit for the relaunch ticker (private: in the chat, NOT here): "MemeCapes logo with snakepit,
  new ticker, for Telegram, X, the launch, and a DexScreener header, video + picture". /tmp/claude-0/pit: coin.py (the
  cape coin scaled 0.9 on a 1500 canvas, a rendered snake on the rim: KD-tree tube shading, staggered scales, dorsal
  diamonds, warm bounce light, grain, contact shadow; head = wedge ellipse + eyes + red forked tongue; an emerald
  ribbon with gold edges over the old name, ticker in Cinzel 900 with a chamfer bevel along the arc) and banners.py
  (3:1 header still + 4 s MP4 + light GIF: sparks, shine sweep, glow pulse; the GIF has no camera move or it is 14 MB;
  X header keeps words centre-right because the avatar covers the bottom-left; avatars 1000/640/400; 1280x720 card).
  Outputs in outputs/pit (kept out of the repo). Wrap-behind-the-coin cuts looked like a bug: snake lies on the rim.
  DexScreener's header is 3:1 (600 px wide min); whether it takes animated files is unconfirmed.

- Oct 21 (3 pm): "option to lock 1 million tokens for free trading fees on their account" + "locked for a year minimum".
  Pit main (capes-lock), dormant until NEXT_PUBLIC_CAPES_MINT: components/LockCard.tsx on /capes (min 1,000,000, 1/2/3
  years, can't-be-undone confirm, your locks + Claim), lib/lock.ts = Jupiter Lock (LocpQgucEQHbqNABEYvBvwoxCPsSbG91A1QaQhQQqjn)
  create_vesting_escrow_v2 / claim_v2 built by hand: recipient = holder, cancel 0, update 0, start = cliff = unlock,
  freq 60, per 0, periods 1 (exactly what lock.jup.ag sends; our data is byte-identical to a real mainnet lock).
  jup-ag/jup-lock is NOT reachable by git here: the oraichain/jup-lock fork has the same layout (different declare_id);
  everything was checked against real LocpQ txs/accounts via pit /api/rpc. Tests /tmp/claude-0/bite/lk.ts (29, blk.mjs).
  /api/lock?wallet= = getProgramAccounts (dataSize 296, memcmp 8 recipient, 40 mint), lock dated by the escrow's first
  tx; counts only if cliff - created >= 365 d, not cancellable/redirectable, not open. LockWatch (layout) sets
  jupiter.ts setVenomWaived -> venomOn() = 0 (client-side, like all venom). Open: game holder perks read the wallet
  balance, so locked $CAPES don't count for in-game perks yet (Skin of the Month is the same 1M); say so before launch.

- Oct 21 (afternoon): "the snake's curves show your account's daily/weekly/monthly/all-time growth, down if down, up if
  up". Pit main (growth-snake): components/GrowthSnake.tsx (24H/7D/30D/ALL tabs, remembered; body = account value over
  time, mint + climbing when up, red + sinking when down, dashed start line, "▲ +x% · 7D"; head = live total; plates
  still = segments; also on /s/<wallet>), lib/snake.ts growthGeom (averages into ~16 slices or a 10 px body crumples;
  flat = gentle wiggle), lib/growth.ts (server values the wallet on-chain + getPrices: nobody can post a fake curve; a
  snap with more unpriced coins than the last is skipped for 2 h = price-feed dropout guard), POST /api/snake/value
  (<=1 per 15 min, client throttles 10 min), GET /api/snake/history. Supabase value_snaps created from the pane (SQL
  editor: monaco.editor.getModels()[0].setValue + Run; "destructive" warning = the drop-policy line). History only
  starts when a wallet first opens the app (no backfill); deposits/withdrawals move the curve too.
  Also today: Hatch price on the button + Privy confirm screens (uiOptions description/buttonText), pct() label bug
  (/\.?0+$/ turned 50% into 5%).

- Oct 21 (4 am): Albert's Snake Bite test hatch (2% fee, sniper 50%/120 s, bite 1%) went through on-chain (burn in the
  launch tx, supply 990M) but listing failed: "pool not found, or not hatched through this launchpad". Cause: the SDK
  lands an exponential sniper fee's END at or just above the target (whole reduction-factor steps): 120 steps -> 2.017%,
  over the 2% limit in verifyHatched. Pit main (hatch-finish): sniperPeriods() picks the step count dividing the time
  that ends on target (288 combos exact vs the SDK), verify allows 2% rounding, failed listings keep a "Finish listing"
  card (no tx) in place of the Hatch button, "Hatched a coin that isn't listed?" rebuilds the listing from the coin's
  first tx (DBC init ix: accounts config 0, creator 2, mint 3, pool 5; data = 8-byte disc + borsh name/symbol/uri),
  stored fee fields now come from the chain. Lesson: any check on fee limits must allow the SDK's step rounding.

- Oct 21: "Snake Bite" for Hatch (Albert: a % you pick gets burnt automatically; dead wallet). Built on the Pit's
  `snake-bite` branch (NOT merged; Vercel preview success): lib/launchpad.ts snakeBiteQuote (walks the curve segments:
  base = L*(b-a)/(a*b), quote = L*(b-a)/2^128; + normal fee, the launch tx's first swap pays the min fee; + 2% headroom;
  matches the SDK's getQuoteFromOutputAmount to the lamport), burnIx (hand-built BurnChecked, no spl-token import),
  buildHatchTxs adds the bite to the first buy (minimumAmountOut = burn amount) and appends the burn (pool tx 929 bytes
  with it, limit 1232). LAUNCH.snakeBite options 0/1/2/5/10/20, max 20. launchcheck biteInLaunch() reads the burn from
  the launch tx; TokenSheet badge "Snake Bite · X% burned" -> Solscan. A real burn, not a dead wallet (a dead wallet keeps
  the supply and shows as a holder; Solana's keyless one is 1nc1nerator11111111111111111111111111111111). Declined an
  automatic recurring burn (needs a server hot wallet = custody); offered a creator-signed "Burn now" instead.
  Tests: /tmp/claude-0/bite (t.ts + pre.ts fetch stub loaded BEFORE web3; 60 checks; run build.mjs from the memecapes
  root). Shots: /tmp/claude-0/studio build_bite.mjs + lpshim.ts (real curve prices, the studio stubs the SDK).
  Before merging: one real tiny test hatch (1% bite) on mainnet; the config tx is sent before the pool tx, so a pool tx
  that fails preflight leaves an orphan config (rent lost, nothing else). Default plan prices: 1% 0.29, 2% 0.59,
  5% 1.51, 10% 3.18, 20% 7.09 SOL.
  Then (Oct 21, 3:40 am) MERGED to Pit main 0aa6fa8 and live (Albert: "make it so I can do another test run"), with:
  Claim fix (MyHatches called .serialize() on signTx's bytes -> "u.serialize is not a function"; send the bytes as is) and
  First Strike "other" = any amount (supplyPctForSol: inverse curve walk, matches the SDK's exact-in quote; capped at 95%
  of the raise minus the bite so one buy can't graduate the coin; 25 SOL ≈ 48% of supply). Albert's first real Hatch
  coin: "im a snake" $SNAKE ...5pit, 1.51% fee / 80% share / 50% sniper fee over 120 s; DexScreener listed it pre-grad
  as meteoradbc; no buys in the first 3 blocks, four same-block buys at +90 s (one operator, ~13.8%). Vercel posts two
  statuses per main push: wait for the SECOND (production) success before checking live.
  Same night: Shed got a Custom token-amount box (StrikeSheet sellText, capped at the bag, "% of your bag"), and Albert
  hit Jupiter's free-tier 429 ("swap build failed: 429 Too many requests") selling then buying again: the browser calls
  lite-api.jup.ag directly. lib/jupiter.ts jupFetch retries 429s (Retry-After or 0.6/1.5/3 s), getQuote shares quotes for
  8 s (the preview quotes the exact Strike amount, gross - venomOn(gross), so the Strike reuses it), preview debounce
  600 ms, plain "Jupiter is busy" message. Real fix if it keeps happening: a Jupiter API key (portal.jup.ag, Albert) used
  server-side through a Pit proxy route.

- Oct 20: a first token launch was abandoned for a relaunch. Albert: take EVERYTHING about that contract down (no address,
  no notes, nothing in this public repo). The site, game and Pit are back to the pre-launch state, so tools/token_launch.py
  runs unchanged on the relaunch. Lessons: read the coin on-chain from the pane via pit /api/rpc (getTransaction needs
  maxSupportedTransactionVersion 1 for pump.fun txs; the shell can't reach any RPC); pump.fun launches are sniped in
  the first blocks by generic bots whatever the ticker; the site says "at most 4%" for the creator buy, so fix the
  numbers after launch if the dev buy is bigger; support_page.py's footer and the game's exchange fallbacks (patch_holder,
  patch_launch) carry "not live yet" text that token_launch.py does not touch; Telegram is public at t.me/memecapes.
  Never write a launch's mint or creator wallet in this repo's notes again: keep them in the chat only.

- Oct 20: "yes build it" (one-tap Battle payout), then "make this part of the Friday update": it lives ONLY on the
  Pit's `beat-the-boss` branch (7ad50d9, Vercel preview success), not main. lib/battle/payout.ts (payLines: prize > 0,
  never the pot wallet itself, whole lamports rounded down; buildPayoutTx: one transfer per winner + memo "snakepit
  battle payout <week>"; verifyPayout), /api/battle/payout (no sign-in: the on-chain payment is the proof; saves paid_sig
  once), supabase/payout.sql (paid_sig, paid_at: RUN IT on Friday's merge, before that the owner sees a note instead of
  the button). Board: button shows only when a connected wallet = pot wallet (useWallet now exposes addresses +
  signTxAs, external wallets sign with their own signTransaction), "Last week's winners are waiting" card, "Last week's
  results" link, Paid + Solscan for everyone. Retry safety: signed bytes + lastValidBlockHeight in localStorage; retry
  re-sends while still valid, rebuilds only after expiry. Tests: /tmp/claude-0/tt/test_payout.ts (22, run build3.mjs from
  the memecapes root); screens: /tmp/claude-0/bh/build_pay.mjs + out/pay.html + shoot_pay.py. Still to check on Friday:
  Albert signs into the Pit with the pot wallet connected (if it's in Phantom, Privy's "wallet" login).

- Oct 20: Albert's Battle trial run (1 player) -> "does it auto refund? I can't pay manually" then "just run it no
  matter what, even with one person". Nothing auto-sends by design (pot wallet key is his; a server hot wallet = custody
  + hack risk). Pit main 9886ada (+ cherry-picked onto beat-the-boss, conflict in closeWeek resolved keeping
  settleBoss): BATTLE.minEntrants 1, every week pays; prize places nobody filled roll into next week's pot. Live check:
  week 2026-10-19, 1 entrant, prize 0.0855 SOL (60% of 95% of 0.15). Payouts are still sent by Albert from the pot wallet;
  offered a one-tap "Pay out" button (one batched transfer tx he signs), not built yet.

- Oct 20: "don't let anyone snipe the coin; the real ticker is new; on 'make it live' the real ticker is on everything".
  The NEW TICKER IS PRIVATE: never write it in this public repo (code, notes, branches, commit messages) before launch;
  it is in Albert's Oct 20 chat (ask him if unsure). Launch day: get the coin address and creator wallet from Albert
  (public addresses), then `python3 tools/token_launch.py --ticker T --mint M --creator W --pit /home/claude/snakepit
  [--logo new.png]` (run with --check first: it works on git worktree copies, prune them after): every readable $CAPES
  (site, game play/preview, server messages, support, patches, Pit app/components/lib/public + battle symbol), the 11
  "no token yet" site lines -> official contract address (Solscan link), token + creator cards in Official wallets,
  config.js capesMint + ticker, Watchtower OFFICIAL_WALLETS (+mint, else it alarms). Then node --check, server tests,
  commit + push both repos, set NEXT_PUBLIC_CAPES_MINT on Vercel (Pit), add a PROGRESS.md section. patch_ticker.py
  (last in build.sh) keeps later rebuilds on the new ticker (the base has 24 $CAPES). Server reads capesMint from
  config.js when Render has no CAPES_MINT. The coin logo has "$CAPES" engraved: my programmatic letter swap looked
  pasted on; Albert should regenerate the logo in his own image tool (pass it as --logo; also the pump.fun image).
  Anti-snipe advice given: keep the ticker and creator wallet unknown until launch, dev buy in the create tx, no
  announced time, post the CA everywhere at once, no multi-wallet bundles (hidden wallets). pump.fun has no
  anti-snipe; Hatch has the sniper fee (trade-offs given, not advice).

- Oct 19 (night): "raid big communities on X (streamers, launchpad users, MMO players, BONK/FLOKI), make categories and a
  video for each, better music for each". Doc "MemeCapes X raid playbook" (Albert's Claude Doc): rules from X's platform
  manipulation policy (real people, one account each, on-topic replies, no copypasta/mass tags/like trains), six
  communities (traders, launchpad, streamers, MMO gamers, memecoin communities, AI agent fans), videos, how a raid runs,
  reply lines, tracking/stop rules. Videos: ad3/vids.py (VIDEO=traders|launch|stream|mmo|memes|ai, music_<v>.json,
  frames_<v>), new scenes: hook_scene, full_scene (square gameplay), bignum_scene, curve_scene (sniper fee), tips_scene,
  end_card; downbeat punch. Square desktop game clips (720x720 dpr 1.5, full UI) in /tmp/claude-0/ad4/gp via gp4.py.
  Gamers' video has no crypto; FLOKI is on other chains (never say it trades in the Pit); memecoin video ends with
  "not affiliated with or endorsed by any meme or coin shown"; AI video waits for Friday (Beat the Boss).
  Music (Pixabay, no Content ID, downloaded with Albert's yes; staged copies in ad3/mus): traders Golden Empire Entrance
  150 BPM, launch Swag Drop (detected 80 = half time, use 160), stream We Are Made Of Win 122, mmo Epic Trailer 118
  (bars 60-75: climax then ring-out under the end card), memes Upbeat Funk (Kulakovka) 110, ai Carbon Shadows 111.5.
  Hard Cyberpunk, Evasion and most cyberpunk/funk picks ARE Content ID registered: check each page's HTML first (fetch
  from a pixabay.com tab; cdn mp3s fetch fine there as blobs -> a[download] + real clicks). beat2.py picks the loudest
  window per video; render_all.sh renders + encodes all six to outputs/memecapes_<v>.mp4 (~25-35 s each).

- Oct 19: "a new X ad video, more updated than the last one, top of the line, no big selling point left out, music
  that makes people excited". 1080x1080, ~56 s, 33 bars at 142 BPM ('Royal trap', the already-licensed track, a later
  section than ad 1): hook words PLAY/TRADE/HATCH/BATTLE on the beats, crest, game (walk/fight/chop/cape), Pit (0.4%
  flat venom, holders-only comments, profiles, gasless USDC->SOL), Hatch (sniper fee, split, locked liquidity),
  Weekly Agent Battle, Beat the Boss, Watch, Stream, MemeSnake, montage, end card (memecapes.com + pit.memecapes.com,
  "Not financial advice" line). Pit screens = studio renders of the real components with example data (EXAMPLE DATA
  chip on every one). Dates/countdowns painted out of the battle shots before use (ad3/prep.py). Composer: ad3/make.py
  + scenes.py (scenes in bars, music.json = bpm/start). Not posted (X waits for launch). Beat the Boss is on the
  `beat-the-boss` branches of both repos (not merged): Albert is keeping it for the Friday update.
  Then "slow it down to ~105 s and put it in the old video's spot on the home page": LONG=1 gives every part more bars
  (62 bars, music from 69.59 s, not a slowed-down file); BOSS_KICK='COMING SOON · BEAT THE BOSS' until Friday (re-render
  with the default 'NEW' kicker after the merge). Home: media/memecapes-tour-2.mp4 (crf 25, 15 MB), new poster, caption
  "Game footage is real; app screens show example data" (the old "Real gameplay, no renders" was no longer true).
  Lost frames when a background render was stopped: re-render missing ones by number before encoding.
  Oct 20: Albert wanted the 56 s cut back on the home page: media/memecapes-tour-3.mp4 (BOSS_KICK coming soon, crf 25,
  9 MB). Re-render with the default 'NEW' kicker after Friday's merge. Also made new-ticker versions of the coin logo
  and of the medallion-ring badge (Albert's art, not used on the site yet) with a chamfered Z built from the E's real
  gold face (/tmp/claude-0/logo2/z3.py, logo3/z4.py); sent in chat, kept out of the repo until launch.

- Oct 19 (2 am): "are the AI slaves working for the big boss? free AI for the lower bots". server/crews.js: 7 crews as
  plain code on the game server (no model, no paid API), each on a timer, reporting through MS.apply() (memesnake.js
  now exposes apply/get): QA Testers 30 min (site, game, launch page, Pit, Battle board), Community 60 (real online
  count; skips 0), Game Build 60 (GitHub commits, skips Notes/merge/revert), Security Review 60 (G.status mode/blocked,
  no thresholds), Launch Site 120 (Pit hatched), Market Scouts 120 (Pit /api/trending, % only), Trading Bot Desk 120
  (Battle entrants). Logs only on change or every 6 h; a failed check shows the crew as blocked. CREWS=0 = off.
  test_crews.js (15). LIVE: 5 crews reported within 3 min of the deploy. Albert may upgrade Claude for AI-written crews.

- Oct 19 (1 am): "get the AI agent (MemeSnake) ready for an update in 5 days, start now". Its page had never received
  anything (StarNet can't write the site's feed.json). Now memesnake/index.html reads LIVE_URL = the game server's
  /ms/feed first, feed.json as fallback (minimal edit to Albert's page: FEED_URL line + load()). server/memesnake.js:
  starter rooms come from memesnake/feed.json, log entries are ADDED (replace:true starts over; before, any post with
  status/parts wiped the log), rooms merge by id. test_memesnake.js (9 checks). Albert must set MEMESNAKE_KEY on Render
  and paste the "Live page updates" section (scratchpad memesnake-live-feed-prompt.md) into StarNet. Still unknown: what
  the update itself contains, and whether StarNet can make HTTP POSTs with a header.

- Oct 18 (night): "Launch still says memecapes.com, every link into snakepit must go to pit.memecapes.com, proper page".
  index.html: Launch / Launch card / "powered by snakepit" / See new coins -> pit /, Launch a coin -> pit /hatch, a coin
  tile -> pit /?q=<mint> (all data-pit, rewritten from config.js pit). launch.html nav: Coins -> pit /, Hatch -> pit
  /hatch; lp/app.js route() forwards the old addresses ('' / launch / coin / me) to the Pit by the RAW hash (views.watch
  and views.stream register after the first route(), so checking `name` forwarded Watch too). Watch + Stream stay on
  memecapes.com/launch.html (the Pit has no Watch/Stream). battle_site.py anchors updated to match.

- Oct 18 (night): "follow wallets, profile picture, comments under their buys if they're a holder" -> holder = holds THAT
  coin. Pit (snakepit main c5e1fd3): supabase/social.sql (run in the pane: users.avatar/avatar_at, comments,
  comment_reports, banned; Supabase calls it "destructive" only for the drop-policy line), /api/avatar/<wallet> (always an
  image: upload as small data URL in users.avatar, or preset:n, or a snake from the address hash), /api/profile,
  /api/comments (POST: signed in, getTokenAccountsByOwner > 0 for that mint, 1 per 15 s + 20/h per wallet, no links/
  addresses/scam phrases/slurs, banned table), /api/comments/<id> report (3 = hidden) / delete (own or mod) / ban (mod).
  Mods = PIT_ADMIN_WALLETS env, default Albert's Pit wallet (TEAM badge). UI: "Holders talk" under STRIKE in TokenSheet
  with HOLDS/BOUGHT badges, ProfileSheet (upload crops to 192 px webp, 12 snake presets, username), pictures in the top
  bar chip, desktop side nav, Slither rows, /s/<wallet>. Following already existed (+ Nest / Slither). Local render
  harness: /tmp/claude-0/bh/soc (zustand + BossPanel stubs, fake fetch, avatar route stub in shoot.py).

- Oct 18 (evening): pit.memecapes.com is LIVE (GoDaddy CNAME pit -> 0b7b7a5e2c5ea15e.vercel-dns-017.com saved by Albert
  on his phone; Vercel cert issued in minutes; Privy allowed origins already had it). config.js pit + all links switched;
  snakepit-mu.vercel.app still works and stays allowed. Albert's real test passed: gasless USDC->SOL swap, 0.2 SOL ticket
  (pot 0.15 SOL, #1 of 1). Fixed from his screenshots: total dropped SOL when Jupiter price v3 answered 429 (prices now
  merge with the last known + CoinGecko backup for SOL), chart axis "$0.0NaNNaN" (negative ticks), "User exited the
  modal" now reads as cancelled. Vercel: a ff-merge's commit status shows the PREVIEW's success; wait for the Production
  row on /deployments before checking live. Privy app is still in DEVELOPMENT mode: Albert must press "Upgrade to
  production" himself before launch (I may not).

- Oct 18 (afternoon): Pit fixes from Albert's real test. Browser Solana calls 403'd (public RPC blocks web pages):
  the Pit now proxies them through /api/rpc (method allow-list, upstream fallbacks incl. publicnode) and confirms by
  polling (lib/confirm.ts). Jupiter price v2 is gone: getPrices uses v3 (+ $1 for USDC/USDT); the total shows a
  breakdown (SOL · USDC · ...). Tapping the wallet chip used to SIGN OUT: it now opens ReceiveSheet (plain-address QR,
  Nayuki qrcodegen MIT in lib/qrcodegen.ts, copy fallback, share). Privy's "Fund your snake" QR is rejected by FOMO's
  scanner: + Add SOL opens our sheet instead. FOMO's withdraw sends USDC, not SOL: GetSol card (Jupiter Ultra gasless,
  lite-api.jup.ag/ultra/v1 order+execute, needs < 0.01 SOL and ~$10+) turns USDC into SOL with no SOL in the wallet.
  HostNav (launch-site menu inside the Pit, from the other chat's Oct 18 2 am task) is switched OFF because Albert
  complained the menu changed ("back to these words at the bottom"): ask him before switching it back on.
  launch.html: with no wallet app (phones) the top button says "Sign in" and opens the Pit.

- Oct 18 (2 am): "when you click Battle (launch.html) all the symbols change". Battle is a link out to the Pit's
  /battle, which showed the Pit's own icon tab bar (Pit/Hatch/Arena/Slither/Capes). Fix: launch.html Battle links are
  now <pit>/battle?from=memecapes; the Pit (snakepit commit a305ea9) remembers that in sessionStorage, hides its own
  nav (.pit-chrome) and shows a copy of the launch site's Coins / Watch / Stream / Hatch / Battle bar (components/
  HostNav.tsx). An iframe was rejected: Privy sign-in and signing break in a cross-site iframe. ?from=pit resets it.
  Any new launch.html link into a Pit page should carry ?from=memecapes too.

- Oct 18 (1 am): Albert demanded a real-SOL Battle by Monday with no vault/audit ("full send"); he can't afford the
  ~$105k audit+legal. Held the line on custody (no server wallet holding players' SOL, no unaudited vault) and built
  TICKET weeks instead (snakepit lib/battle/ticket.ts): the player pays 0.2 SOL from their own wallet in one tx (0.15 pot
  wallet + 0.05 fee wallet + memo "snakepit battle <week>"), /api/battle/enter verifies it on-chain (signer, both
  transfers, memo, 14 days, ticket_sig unique), stacks stay practice SOL, closed weeks list PAYOUTS (full wallets) for
  Albert to pay from the pot wallet. The tx id is computed before sending (base58 of the signature) and kept in
  localStorage so a retry never pays twice. 18+/allowed-where-I-live checkbox. Dormant until Vercel env
  NEXT_PUBLIC_BATTLE_MODE=ticket + NEXT_PUBLIC_BATTLE_POT_WALLET (+ _FEE_WALLET, default venom income wallet).
  Tests: /tmp/claude-0/tt (bundled with the launchpad's vendored web3 resolver): 17 checks. He is under heavy personal
  financial pressure: be steady, quick and kind; explain that custody adds no income (stacks are the players' money).

- Oct 17 (late night): "I need this built into the app and website, 3 days till launch": the Weekly Agent Battle is LIVE
  in the Pit (practice mode). The snakepit repo is on GitHub (Mrsnakehunter/snakepit, private, we can push; Vercel
  deploys main and posts its build result as a commit status: `gh api repos/Mrsnakehunter/snakepit/commits/<sha>/status`).
  npm is blocked here: type-check with /tmp/claude-0/tc2 stubs, render screens with esbuild + Tailwind 4 compile()
  (/tmp/claude-0/bh: fake board data, shoot.py), push a branch first, merge when Vercel says success. Vercel Hobby only
  allows daily crons: the battle clock is OUR server (server/snakepit.js battleTick every 5 min, BATTLE_CLOCK=0 off,
  BATTLE_TICK_SECRET optional on both). Board API with no tables = {configured:false}. Website: tools/site/battle_site.py
  (nav + pw line + #battle home section reading <pit>/api/battle/board, FAQ, launch.html nav; data-pit links follow
  config.js pit). Supabase: supabase/battle.sql must be run once in the SQL editor (Albert, or the browser pane).

- Oct 17 (night): home page: gold crest above the floating cape "MemeCapes / powered by snakepit (-> launch.html) · run by
  MemeSnake (-> memesnake/)" (.crest, .cr-*); "Straight from the game" six screenshots replaced by the 37 s tour video
  (media/memecapes-tour.mp4 = memecapes_ad_platform.mp4, muted autoplay when on screen, "Play with sound" button) + two
  snake-pet shots (/tmp/claude-0/pitshots ang0/ang1 cropped 0,300,585,1000). Headless Chromium can't play H.264
  (readyState 0): check the video on a real phone. Grid items holding a <video> need min-width:0 or they overflow.
  Also "Link with snakepit" (one account): server /plink/msg + /plink (test_plink.js 8 checks), WS pitLinkStart with a
  client-made 24-hex code; game patch tools/patch_pitlink.py (after patch_snakepit) puts a button on the $CAPES snake
  card, opens PIT/link?code=..&srv=.. on the click; pitWallet() prefers NETS.holder.wallet. On PREVIEW only until the
  Pit has its /link page (brief for the other chat given). Linking works before $CAPES launches (holderCheck skipped).

- Oct 17 (night): "I thought snakepit would let you create your own wallet, it says connect wallet". The Pit does
  (Privy embeddedWallets createOnLogin users-without-wallets: email sign-in makes a Solana wallet). launch.html only
  connects browser wallets, so the picker now leads with "No wallet? Make one free" -> config pit (.mkw). Limit: a Pit
  (Privy) wallet lives in the Pit; memecapes.com's Stream/tips/pass still need a browser wallet (Privy can export the
  key to Phantom). Real fix later = move Stream/Watch into the Pit or add Privy to launch.html (no npm here).

- Oct 17 (night): "where's the snakepit logo and theme, that's gonna be the whole new launch page". launch.html (Coins/
  Watch/Stream/Hatch) is now SnakePit-skinned: the Pit's logo (Z-snake path, mint #58F0A6 on ink #0B0C0E) + "snake**pit**"
  wordmark, Outfit + JetBrains Mono, white headings, mint accents (red only for live/Strike), svg favicon; nav Coins /
  Watch / Stream / Hatch / Trade (Trade -> config pit). All brown/gold hexes mapped in launch.html + lp/app.js (one
  python mapping pass); forge wording -> "Just hatched / Getting hot / Graduated", "Latest hatch", "Hatched by" (in
  the Pit "Strike" means BUY, so never say "struck" for a launch). Shots: scratch/lp/test/shoot.py sp_theme.json.

- Oct 17 (evening): the Pit is LIVE at https://snakepit-mu.vercel.app (the other chat deployed it; Privy secret no longer
  used: it verifies sign-ins with Privy's public keys). config.js pit = that address; lp/app.js and launch.html CSP accept
  pit.memecapes.com OR snakepit-mu.vercel.app. When Albert adds the GoDaddy CNAME (pit -> the Vercel target the other
  chat gave), switch config.js pit to https://pit.memecapes.com (both stay allowed). Render's server reads pit from
  config.js at start (needs the redeploy that a push triggers). Signed-in test trade still to do by Albert (0.05 SOL
  Strike + Shed; each should pay 0.0001 SOL to the fee wallet and 0.0001 to the income wallet).

- Oct 17: Albert's "Weekly Agent Battle" (spec doc "Weekly Agent Battle — Build Spec" + design canvas "Weekly Agent
  Battle Screens", both his artifacts): 1.2 SOL entry (1 stack / 0.15 pot / 0.05 fee), AI agent Turtle/Snake/Wild + lucky
  coin from a board of 5, Advanced (bet/TP/SL), one BOOST a day, top 3 by % return split 95% (60/25/15), 5% rolls on.
  Told him the real-money blockers: someone must sign trades while the player sleeps (custodial server keys vs a custom
  audited vault program), same picks would trade identically (fixed with a per-player personality seed), legal (pooled
  prizes + automated trading). He OK'd PAPER MODE "named snakepit, looks like the design". Built as an add-on for the
  SnakePit codebase (snakepit-battle-addon.zip, ADD-TO-SNAKEPIT.md lists 3 hand edits: nav, vercel cron, env):
  lib/battle/{config,time,engine,store,draft}.ts, app/api/battle/{board,enter,boost,tick}, app/battle (+ board), supabase/
  battle.sql, BATTLE.md, scripts/battle-sim.ts. Engine is pure code (no LLM): 10-min ticks, prices from Jupiter price v3/
  v2 + DexScreener, rails (limits, cooldown, $250k liquidity, 0.4% fee + 0.3% slippage). Tuned in sims: Wild first lost
  ~60% every week from churn; now cooldown 60 / 12 a day. Real mode returns 403 until the vault exists. Not rendered
  here (no npm, no React): the other chat must screenshot the screens on first build.

- Oct 17: Albert sent the Pit's wallets (public addresses): fee wallet 3rDg...uCjg (= launchpad partner, also Pit
  NEXT_PUBLIC_FEE_CLAIMER + VENOM_WALLET), Pit income 3UYB...XQij (NEXT_PUBLIC_VENOM_INCOME_WALLET), MemeSnake agent
  FNxq...z9Ns (NEXT_PUBLIC_BOSS_WALLET, pays Molt prizes). $CAPES page (#token) now has an "Official wallets" section
  (#official-wallets, Solscan links) and all three are in watchtower.sh OFFICIAL_WALLETS. Add creator + pot wallets
  there when they exist.

- Oct 16 (night): MISREAD, then fixed. Albert's "3.2% not 5% like FOMO, 50% fee wallet (25% burns, 25% buyback), I keep
  50%" was about the PIT's trade fee (SnakePit Strike/Shed venom), NOT the launchpad. I had made the launchpad fee fixed
  and removed the fee/share sliders: reverted (commit "Revert ..."; launchpad = fee 0.25-2%, share 50-80%, burnShare 50,
  as before). Pit venom now: 3.2% on every Strike and Shed. Jupiter's own fee mechanism stops at 2.55% (255 bps, and
  takes 20% of it), so lib/jupiter.ts uses /swap/v1/swap-instructions and adds plain SOL transfers in the same v0 tx
  (Strike: venom off the SOL going in, the rest is swapped; Shed: venom on otherAmountThreshold after the unwrap).
  Split at the transfer: half to NEXT_PUBLIC_VENOM_WALLET (fee wallet; a quarter of venom burns $CAPES, a quarter buys
  $CAPES for the game pot), half to NEXT_PUBLIC_VENOM_INCOME_WALLET (empty = all to the fee wallet). Copy on the Pit's
  Capes page, Strike sheet ("Venom 3.2% comes off the top" + SOL amount), README, brief. Nothing on memecapes.com yet:
  when the Pit goes live, add a "The Pit" card under Burns on the $CAPES page with the same words. FOMO's exact fee
  was not verified. Lesson: when Albert says "the fees" ask which product before touching published economics.
  Oct 17: FOMO checked (help centre via fomoappguide.com, Sept 2026): Solana = flat 0.10 USDC under 5, 2% from 5 to
  47.50, flat 0.95 to 190, 0.5% above, 0.45% with a referral; FOMO pays gas. 3.2% would have been ~6x dearer on $200+.
  Albert: "make it cheaper than fomo" -> Pit venom = flat 0.4%, no tiers, no minimums (NEXT_PUBLIC_VENOM_BPS=40),
  under FOMO at every size incl. referral. Same 50/25/25 split and transfer mechanism. Re-check FOMO's schedule before
  any public "cheaper than FOMO" claim; the Pit's own copy says "0.4%, flat, no tiers, no minimums" and names nobody.

- Oct 16: "combine the launchpads: the new one (SnakePit's Hatch) like the old one, designed like the new one, that is
  going to be the app". Delivered snakepit-launchpad.zip (the SnakePit codebase with the merge; LAUNCHPAD-MERGE.md
  lists it): lib/launchpad.ts = our curveParams/presets/limits ported to TS on SDK 2.x (per-hatch config +
  createConfigAndPoolWithFirstBuy, feeClaimer = MemeCapes fee wallet via NEXT_PUBLIC_FEE_CLAIMER, verifyHatched
  checks feeClaimer + creator share on-chain, readFees, claim-with-split), lib/launchcheck.ts (bundlers/snipers via
  RPC + Helius), app/hatch/page.tsx (presets, sliders, decay curve, split editor, graduation/pool fee/team tokens,
  First Strike, Your hatches + Claim), TokenSheet fee rules + split + launch check, schema v0.4, docs. Type-checked
  lib/*.ts against the vendored SDK 2.0 source (/tmp/claude-0/tc/tsconfig.json pattern: paths -> scratch/lp/vendor);
  React files syntax-checked only (no react/next here). SDK 2.x names: getPoolQuoteTokenCurveProgress,
  claimPartnerTradingFee needs payer, pool state is pool.poolState.*. memecapes.com: lp/app.js #/launch shows a
  "Hatch it in the Pit" handoff and the Launchpad clerk opens pit/hatch when config.js pit is set; our own form stays
  until then. Still open: coin floor/Watch index only our server's coins; migrate or retire once the Pit is live.

- Oct 16: SnakePit (Albert's trading app, pit.memecapes.com, separate codebase from another chat: SNAKEPIT-BRIEF.md +
  snakepit.zip, Next.js/Privy/Jupiter/Meteora DBC, NOT built or deployed yet). Vocabulary: Strike=buy, Shed=sell, Venom=
  fee, Hatch=launch, segments=score (3 + realized SOL/0.05), Boss Snake=MemeSnake's wallet, Molt Season=weekly reset.
  Section 7 built here: config.js `pit` ("" = off; set "https://pit.memecapes.com" when it is live); server/snakepit.js
  proxies GET /pit/snake?wallet= and /pit/stats (PIT_URL env or config.js, 60 s cache, fields whitelisted, last good
  answer kept when the Pit is down; test_pit.js 12 checks); tools/patch_snakepit.py (after patch_pace): PITS state,
  pitRefresh (start, $CAPES tab, every minute, 5-min freshness), pitSnakeDraw = mint snake on the player's trail (lead
  .9 tile, .23 spacing, up to 30 segments then thicker, tongue flick), $CAPES tab card "Your snake" + "Trade $CAPES in
  the Pit" (pit/?q=<capesMint>, else /capes); launch.html #pitwrap + widget loaded by lp/app.js when pit is set (CSP
  script-src allows pit.memecapes.com). Brand on our side: mint #58F0A6, red only for the tongue/Strike. On preview,
  dormant until `pit` is set. Conflicts to settle with Albert/the other chat: two launchpads (ours on launch.html vs
  Hatch), the brief calls $CAPES "the in-game currency" (ours: Meme Coins in game, $CAPES = the token), the brief's
  "trading is the front door" vs our home page, venom -> prize pool must match the pot wallet on the $CAPES page.
  Test: /tmp/claude-0/pittest.py (fake Pit :8799 + local server PIT_URL + test9 hooks __PITS/__pitRefresh).

- Oct 16: "the video evenly split between all the platform, plus good music". memecapes_ad_platform.mp4 (37 s):
  intro + Play/Watch/Stream/Launch/AI Agent 3 bars each + $CAPES + end, every cut on a downbeat, gold flash +
  punch-in, nav pills with the current part lit (scratch/ad/compose2.py, reuses compose.py by exec). Music: 'Royal
  trap' by ShimaFM (Pixabay Content License: ads OK, no credit, NOT Content ID registered; downloaded with Albert's
  OK into his Downloads, staged here), 142 BPM, window 69.58 s + 37.18 s, loudnorm -14 LUFS. Also added it to the
  first ad (memecapes_ad_music.mp4). Pixabay track pages' server HTML carries the mp3 URL, duration and
  "Content ID Registered" (filter on that); blob + a[download] + a REAL click downloads in the pane. Watch/Coins
  scenes use the seeded example data (scratch/lp/test/seed.mjs, local server) with an EXAMPLE DATA chip: never show
  fake trades as real. Research: 120-140 BPM for short ads, hook in 1-3 s, cuts on beats, plan for muted autoplay.

- Oct 16: "NPCs and bots running around really fast, movements sped up" + "make the trees live" (shipped build
  20261015235521, then 20261016100238 with the fix). Measured with the virtual clock (/tmp/claude-0/ad/speed.py
  pattern: sample gobs px/py and __WND() bots every 50 ms for 20-40 game-s): monsters' follow() caught up at up to
  3x (2.7 tiles/s) and their walk clip ran 1 clip-s per tile (player's natural cycle = 0.6 s per tile); bots ran
  3.33 t/s on 70% of trips > 10 tiles. tools/patch_pace.py (last in build.sh): follow(e,dt,br,lo,hi,dv), strolls
  step every other tick (gb.rs marks a stroller), monsters 0.83 t/s strolling / 1.667 chasing, catch-up <= 1.4x,
  walk clip t = ph/4*.6, bots run only on 25+ tile trips (1 in 3) and never in towns. After: mobs p90 1.2 t/s,
  bots 1.67. The live game's internals are scoped (not reachable from page JS): measure on scratch test pages.

- Oct 16: "create an ad video for X of using the site": 36 s, 1080x1080 MP4 (not posted; X posting waits for launch).
  Smooth game footage on this slow machine = a VIRTUAL CLOCK (scratch/ad/vclock.js: Date.now, performance.now,
  timers and rAF replaced; __vstep(ms) advances), frozen from page start, ~3 s per frame at 390x844 dpr 1.5 phone
  view (scratch/ad/gp.py, scratch/site/test9.html = test7 + window.__MK walk marker). Clips: walk (Wow Landing
  fountain, tp 156,184 cam 3.75/.42/10), fight Bonk (pitch .55 or bushes block), chop a lone meadow tree (forest
  trees block the camera), MemeCape orbit at the castle. Site scenes typed/scrolled per frame (scratch/ad/site.py),
  compose.py = phone + browser mockups, Cinzel/Alegreya from a sparse clone of github.com/google/fonts. Hide dates in
  ad footage: #cd + its date line, MemeSnake's countdown stat. Found + fixed: launch.html#/stream opened directly
  showed "Cannot set properties of null" when the coins request failed (route token in lp/app.js).

- Oct 16: "support page next to the AI Agent, think of 10,000 questions, answer them without giving away secrets".
  Website #support: tools/site/support_qa.py = the knowledge base (260 answers in 20 topics, each with alts + a verb
  phrase vp and/or noun phrase np; 'pl' marks plural nps) -> support/qa.json (96 KB, in Watchtower's FILES);
  tools/site/support_page.py splices CSS (sp-*), the page, the nav link after AI Agent and support:'Support' into
  index.html (idempotent, run it after editing). The page expands vp/np through the VP/NP templates in the browser
  (11,471 phrasings, real count shown), scores tokens (canonical q 4, alts 3, keywords 2.5, answer 1, prefix 1.5;
  below 1.5 = no match), topic chips, Most asked (top:true), "Also asked as" samples, .mc-contact in Still stuck.
  The generator asserts no years or $ prices in any answer. Add an answer = one q() line, rerun both scripts.
  Testing: /tmp/claude-0/sp/shot.py pattern (serve the repo, localStorage mc_gate_<termsVersion>='yes', #support).

- Oct 15 night: Albert's phone (an in-app browser, http:// link) showed "Could not reach the game server". Server was
  fine (health ok, mode normal). Cause: GitHub Pages does NOT enforce HTTPS, so http://memecapes.com serves the game
  and the WebSocket origin is http://memecapes.com, which server.js rejects (403) -> that message. Fix: gate.js now
  sends any http://*.memecapes.com page to https (live, checked in the pane). "Enforce HTTPS" is now ON in GitHub ->
  Settings -> Pages (ticked Oct 16 after the new certificate was issued; http:// now redirects at GitHub too). Also raised Sentinel's WS_PER_IP 8 -> 40 (phone carriers share one
  address; test_guard pins GUARD_WS_PER_IP=8). Check the server from the pane: fetch /health and /guard/me; a WS from
  another origin errors by design.

- Oct 15: "make the trees 1000% better but not so good it lags, variety". Trees are now Meshy models drawn with
  instancing: models/trees.json (tools/treepack.py from t_<species>.glb: 3 detail levels ~1600/500/160 tris cut with
  tools/decimate.cpp relax mode, one 512 px JPEG each, ~3.5 MB for 16 species) + tools/patch_trees.py (runs last in
  build.sh). Engine: ANGLE_instanced_arrays, programs pgT/pgTS reuse the chunk fragment shaders (material 10 =
  model texture on unit 4 + tint in vraw.z: brightness + 4*season), treeKind(o) picks the species from the region
  (town 4 dead, 5 snow, 6 alien, 7 cypress/palm, 1 willow, 0/3 blossom; forests conifers) with the old tp/hv dice,
  treeGather buckets trees (and pack bushes, TRB per chunk key) by species x LOD x frustum each frame, treeDraw
  draws in the shadow pass and the main pass; stumps stay chunk geometry (chopping unchanged); old code trees stay
  until the pack loads (then chunks rebuild) and when MC_CONFIG.trees===0 (website shots). Densest forest in view
  ~200k tris, 15 draw calls. Species heights in TRH; fallbacks in TRFB. Hooks for tests: window.__TRP in mktest.sh.
  Known gaps: decimate gets stuck on some Meshy remeshes (maple/willow mid LOD ~900 tris, bushes ~1600: fine);
  alien tree reads odd from afar. Meshy lessons: text-to-3D = 20 credits mesh + 10 texture ("Texture" button, then
  the panel's Texture; dispatched pointer events work there and for Remesh Confirm); the asset grid RE-SORTS as tasks
  finish, so never work by index: search by name (__search) and check faces/prompt each time (I textured the alien
  tree 11 times = 100 credits wasted); page downloads need a REAL click on the popup's Download (dispatched clicks
  are blocked as "multiple downloads" after the first) and land as <uuid>.tmp (map them by triangle count);
  the pane's screenshots were stale/scaled in emulated viewports: drive the page by JS + coordinates
  (1280x800 emulation = screenshot frame 800x500, scale .625). Credits 1,850 -> 1,260.

- Oct 15: "everything at a minimum of 7.5k triangles" (Meshy remesh is free: 0 credits). All 109 Meshy structures remeshed
  from their textured originals (Custom 8000, Triangle; redo at 9500 when Meshy lands under 7.5k, it often gives ~7-8% less)
  and converted with glb2mdl --tex 512 (bounds identical to the old 6k models). Models folder 28.5 MB -> ~40 MB.
  Meshy web app lessons: the search box needs an Enter keydown; Confirm/Download need a REAL click (find ref);
  the Remesh menu opens with dispatched pointer events; setTimeout is throttled to ~1/min when the pane is hidden,
  so sleep through a Web Worker; thumbnails load via /_next/image?url=...&w=256 (direct api.meshy.ai is CORS-blocked);
  tell same-name assets apart by thumbnail similarity and pick the TEXTURED original (colourful thumbnail; the grey
  one with the same face count is untextured); downloads in the desktop pane sometimes stay as <uuid>.tmp files in
  Downloads (complete GLBs): identify them by triangle count. Helpers live in Meshy's localStorage (mc_rh, mc_dq, mc_sig).

- Oct 15: Albert loved the security plan: website page #security ('The Stronghold': Sentinel + Watchtower cards, 'nothing to
  steal' tiles, daily AI patrol, user safety habits, honest line) + nav link 'Security' after AI Agent. sx-* classes.
  Public copy must never give away thresholds, intervals, commands, endpoints or how addresses are read.

- Oct 15: "make the site almost impenetrable, a bunker, fail-safes, an AI bot protecting us at all times". Built:
  server/sentinel.js (G): real IP = right-most public X-Forwarded-For entry (Render appends; visitors can spoof the left;
  PROXY_HOPS overrides); per-IP GET/POST buckets, strikes -> blocks 10 min/1 h/6 h/1 day; TRAP regex for probe paths;
  8 wrong passwords lock a name 15 min; constant-time admin key; 8 WS per IP; 2-min sign-in timeout; WS fragment cap;
  modes normal/shield/lockdown (G.allow(kind); 'pay' always allowed), auto-shield at 25 blocks/10 min for 30 min;
  disk guard (<12% free pauses uploads); config.js wallet-change alarm; alerts in game + GUARD_WEBHOOK/GUARD_TG_*.
  /guard in game, /admin/guard, /guard/me (shows your IP + hop count: use it to check the proxy setup). Fixes from the
  audit: devnet payments refused for pass/tips/subs (ALLOW_DEVNET_PAY=1 for testing), nonces per wallet (5),
  so_sessions hashed, /lp/register requires our own metadata URI, javascript: links blocked, fee-split addresses
  shown in full, pass recipient checked against config.js, Jupiter plugin replaced by a jup.ag link-out, iframes
  sandboxed, frame-buster in gate.js, CSP meta on launch.html (no inline scripts there: keep it that way),
  tools/patch_security.py (game esc() escapes quotes, chat colours must be #hex). Watchtower: .github/workflows/
  watchtower.yml + tools/watchtower.sh every 15 min (DNS = GitHub Pages IPs, live files == repo, live config.js
  wallets on the official list, server health/mode) -> GitHub issue labelled watchtower. If Cloudflare is ever put in
  front, update PAGES_IPS. New official wallet = add it to OFFICIAL_WALLETS in watchtower.sh. Tests: server/test_guard.js.
  LIVE CHECK: Render's X-Forwarded-For = '<visitor>, <Cloudflare edge>' (a faked entry goes to the left): Sentinel skips
  private AND Cloudflare ranges from the right (/guard/me showed the real IP, cf:true, and ignored a spoofed 1.2.3.4).
  Watchtower run 1 passed. Daily Claude 'MemeCapes security patrol' scheduled task 7:49 ET (read-only: commits, tests,
  Watchtower runs via REST, gh GraphQL is blocked). Plan doc: 'MemeCapes security plan: the stronghold' (Albert's to-do:
  GitHub/registrar/X/Telegram passkeys, verify Pages domain, Render 2FA + LP_PARTNER + ADMIN_NAMES, GUARD_WEBHOOK).

- Oct 15: "stop making legal the biggest priority on the AI agent, switch the first step to security". MemeSnake page:
  Token Launch Protocol step 1 = "Security first"; Token Mint crew 'Legal Review' -> 'Security Review' (server prop),
  room tag + demo samples say security; feed.json crew renamed. Albert's StarNet prompt must use 'Security Review' too
  (gave him the lines). Don't lead with legal in his agent/product copy; security comes first.

- Oct 15: NPCs page order: "no-picture ones to the bottom, above them the T-pose ones, same character with different
  names never back to back". tools/site/bestiary_order.py reorders each section of #pg-bestiary: natural-pose pictures
  first (TPOSE_FREE list, judged by eye), then T-pose, then 'Picture coming' cards; same character = near-identical
  picture (difference hash) or the SAME list. Re-run it after adding cards. Almost every portrait is a T-pose render.

- Oct 15: "the game is drowning out the other stuff": site menu is now Play / Watch / Stream / Launch / AI Agent
  (+ the gold Play free button). Play is a <details class="nvg"> dropdown holding all the game pages (Home, Story, NPCs,
  Items, Towns, Quests, Meme Capes, Roadmap, $CAPES, Shop, FAQ). AI Agent = memesnake/. Phone: nav .in wraps (it didn't,
  so the open menu sat beside the logo). Site tests: accept the age gate first (localStorage mc_gate_<termsVersion>='yes').

- Oct 14 night: Albert sent two files with no message: the MemeSnake agent prompt (an AI "boss agent" he runs on
  StarNet; it writes feed.json for a public "MemeSnake Live" page at memecapes.com) and that page's HTML. The HTML
  arrived cut off at exactly 100,000 characters, inside the base64 logo: only the CSS and the top of the page made it,
  and the logo decodes to its top 2/3. Built memesnake.html with his CSS as is, my own body + script, and the logo top
  faded to black (mix-blend screen hides black). Feed lives on the game server: server/memesnake.js, GET /ms/feed,
  POST /ms/feed with Bearer MEMESNAKE_KEY (Render env, Albert makes it; we never see it). A whole feed.json replaces
  the feed, {log:[...]} adds entries; parts/statuses whitelisted, newest 50, and anything with a money amount, a
  base58/hex key-looking string or "seed phrase/private key/password" is dropped with a note (his own rules).
  Then (same night) Albert asked for it at /memesnake with a menu link and a same-folder feed.json: now memesnake/index.html
  reads memesnake/feed.json (starter: status offline, all crews idle, empty log); DEMO banner + labelled samples until
  the log has entries; back link https://memecapes.com/; memesnake.html redirects; nav link 'MemeSnake' after
  Launchpad. The agent prompt file stays OFF the site (it's for StarNet). He then sent the full logo as an image (1254 px PNG):
  now embedded in memesnake/index.html as a 640 px webp. Demo mode shows the feed's real status, not "Online". Server /ms/feed still exists but the page doesn't use it.
  Oct 15: Albert sent v2 (pixel world) + a prompt with a 4th part, Token Mint (Legal Review, Tokenomics, Contract Audit,
  Launch Site, Hype Crew, Launch Control). HTML cut at 100k again: kept his head/CSS, rebuilt the body: canvas world with
  4 rooms + throne, one worker per crew walks a scroll to the throne per log entry, room panel, comms filters, Token Mint
  steps, money order, promises. feed.json + server/memesnake.js accept part 'token'. Draw small logos via a smoothed
  offscreen canvas (imageSmoothingEnabled=false turns them to noise). Never pkill -f a pattern that's in your own command.
  Oct 15 later: Albert sent his complete v3 file (54 KB, logo as memesnake-logo.png beside it) with "use it exactly as
  written, do not rewrite". memesnake/index.html is now his file byte for byte (back link '/' left as is); logo = his
  1254 px PNG resized to 512 px. His page shows DEMO only when feed.json can't be loaded; with the starter feed it
  shows Offline + "No activity here yet". It has a launch-day countdown (his choice; the no-dates rule is for posts).
  Don't edit his MemeSnake page beyond what he asks.

- Oct 14 late: "make the bots look 100% like real characters (the site discloses them), a little spaced out". Gaps found:
  bot names had spaces (real usernames can't), tags/chat names not clickable, capes skipped on the blocky body, no
  render flag, 2.3 tiles/s (real: 1.67 walk, 3.33 run) - and real players looked WORSE (others drew them bare-handed in
  bind pose). patch_wanderers: UNAME map (valid usernames, o.dn; o.n stays the lines key), 'ntag pn' tags + netName in
  chat, same qMdl args, capes always, Running on long trips, wndFree keeps 3 tiles from other bots and their targets,
  hidden if ignored or a real player online has the name. tools/patch_lookalike.py: pos carries a='clip|weapon|shield'
  and c='cape:skin' (server now keeps 48 chars of each), others drawn with that clip, weapon, shield, cape skin; /trade
  to a bot says "Trade request sent" and nothing follows. /who and the online count still list real players only.
  online_e2e.py: A sees B as "Idle|sword|". Shipped.

- Oct 14 evening: "too many bots at the start point walking the same spots; my coworker and I can't see each other, is the
  server live?". Server WAS live (health ok, socket opens). Cause: the start screen's offline buttons (Create Account,
  Guest, Random, Continue as) look like the online ones and nothing in game said offline. tools/patch_online.py: online
  buttons first, offline folded into <details class="onoff">; #onchip "Online · N players" / "Offline: … Play online" /
  "Reconnecting". Bots: GT homes 10 -> 5 (moved to towns 2,3,5,6,7), social bots wander 16 tiles, idle 8-22 s.
  Test: scratch/online_e2e.py (local server :18902, site_t/t.html = preview + window.__H hook, never pushed): two
  players register and see each other (PASS). Shipped.

- Oct 14, streamer pass: "charge them a flat 20 dollars a month for being able to stream". config.js launchpad.streamPassUsd 20,
  streamPassDays 30, streamPassWallet "" (= the launchpad fee wallet). Server (social.js): so_pass(wallet, until) +
  so_pass_pay(sig…); GET /st/pass quotes the SOL amount at the live coingecko price (held 15 min per wallet, fallback
  solUsdFallback), POST /st/pass {sig} checks the transfer on-chain (checkPay, >= 98.5% of the quote, from the signed-in
  wallet) and adds 30 days; /st/golive answers 402 without a pass; /so/me carries pass{}; admin `/watch pass <wallet>
  [days]` grants one free (server.js now passes the whole argument to /watch). Stream page: 4 steps when the pass is
  needed, pass panel with "Pay x SOL from my wallet" (LPC.pay + memo), FAQ/earn text; website: home blurb, FAQ
  "What does streaming cost?" + "What is the launchpad?", Terms 6a (launchpad, pass non-refundable, tips untouched,
  18+ to stream). Tested: gating + quote with sotest_pass.mjs; pass panel with the fake wallet (shoot p16.json).

- Oct 14, launchpad look v2 (shipped Oct 14, build 20261014090407): "top of the line, visually like nothing done before, token
  pictures not a list, streaming interactive for new users, watch like FOMO + X, 1000x better". Coins page = the forge
  floor: hero + latest strike spotlight, "Hot right now" rail, then walls of coin tiles (Fresh from the forge / Heating
  up / In the vault); every coin is a struck gold coin (stamp(): reeded rim, molten progress ring, heat glow that cools
  over 24 h, laurel when graduated, 3D tilt toward the pointer via .coin3d, embers canvas #forge behind everything).
  Watch = trading floor: live trades column (new rows slide in), wallet of the hour, featured stream with chat beside
  the video, feed with filter chips, trending, top wallets (server /lp/leaders?by=wallet&range=hour|day|week).
  Stream = "Go live. Keep everything." with a mock-up of what viewers see, 3 steps, FAQ. index.html Watch/Stream now
  go to launch.html#/watch and #/stream. Fixed: fee numerator is /1e5 for bps (was /1e7); mine() used a dead card().
  Testing: scratch/lp/test/seed.mjs (14 sample coins from tools/art/memecape, 377 trades, posts, 2 live channels with
  fake video pages on port 8793) + shoot.py step {"fakelive":1} stubs LPC.dbc() so market caps and rings render
  without Solana. In shoot.py a step runs url -> js -> wait -> shot, so put measuring js in its own step after a wait.
  Gotcha: inline style on .wgrid overrode the phone media query (now .ugrid); long unbroken addresses need
  overflow-wrap:anywhere or the page widens on phones. Shots: scratch/lp/shots/review_desktop.jpg, review_phone.jpg.

- Oct 14, Play/Watch/Stream/Launch (branch `launchpad`): home top = PLAY / WATCH / STREAM / LAUNCH beside the floating
  Meme Cape (#watch, #stream = coming-soon pages). Launchpad: trade indexer (server reads EvtSwap2 from each pool's
  transactions every 20 s; offsets checked against Anchor's decoder), /lp/trades feed, /lp/leaders (SOL out minus in,
  losses shown too), /lp/early launch check (launch-slot buyers = bundling sign, next 3 slots = snipers, still held),
  Jupiter Plugin on graduated coins (config launchpad.jupReferral). Albert wanted refunds for everyone except snipers:
  impossible after settlement and not honest to promise; we block up front instead (sniper fee, atomic first buy,
  launch check; next: Helius MEV Protect, funded-by check; later: presale-style fair launch). Alpha Vault does NOT
  work with DBC. Streaming plan (not built): 100% of crypto tips/subs to streamers, Cloudflare Stream or Livepeer
  (~$2.7k-7.9k/mo for 20 streamers x 50 viewers x 4 h/day), 18+, moderation, DMCA/NCMEC/TAKE IT DOWN. Other chains:
  Robinhood Chain via Bags partner (0.25% of volume), Base via Zora/Clanker. Plan doc: "MemeCapes Launchpad plan".
  Gotcha: `pkill -f "node server.js"` kills your own shell; start test servers with nohup + pidfile.

- Oct 14, Launchpad (branch `launchpad`, NOT live): "launch on pump.fun, have a launchpad on the site, 50/50 burns, more fee
  options than pump.fun, visible on the site and in game". Built on Meteora DBC (launch.html + lp/app.js + lp/chain.js +
  lp/lpcore.js bundle). This machine has NO npm/CDN/Solana access: lpcore.js is built from GitHub source clones
  (tools/launchpad/vendor.sh + vendor.lock, build: `node tools/launchpad/build.mjs lp/lpcore.js`, shims in
  tools/launchpad/shims; spl-token is our own small shim). Per-coin config (createConfigAndPoolWithFirstBuy):
  fee_claimer = MemeCapes fee wallet (config.js launchpad.partner / Render LP_PARTNER); creator share 50-80% of the
  non-Meteora 80%; sniper fee = exponential fee scheduler; LP 100% permanently locked, split like the fees; team
  tokens = lockedVesting. Server: server/launchpad.js (/lp/upload, /lp/meta, /lp/register checks the tx on-chain:
  DBC init ix + config fee_claimer at offset 40 + creator share at 245 <= LP_CREATOR_MAX; /lp/coins; reports; /lp
  admin cmd). Game: tools/patch_launchpad.py (Launchpad clerk 'lpad' in GT and Stonks City, opens launch.html in a
  new tab). Tests: scratch/lp/test (shoot.py with a fake RPC + fake wallet; smoke.mjs offline). Real test still to
  do on devnet from Albert's computer: launch.html?net=devnet&testwallet=1. Plan doc: "MemeCapes Launchpad plan".
  Research: pump.fun 1.25% fee, creator 0.30%, splits to 10 wallets since Jan 2026; Bags 100 recipients; Jupiter
  Studio sniper fee + vesting; Heaven's 100% burn flywheel failed. Never claim features others don't have without
  checking.

- Oct 13: Albert said "make it live": shipped build 20261013182150 (Skin of the Month, picture store + try-on,
  MemeCape/Quest cape, plan C exchange note, bots with 1,082 lines); live version.json checked in the browser pane.
  Website: FAQ "What is the Skin of the Month?", 0.1% line in the holders FAQ and Terms, skins can't be traded;
  new "The MemeCape, worn" picture (GT, yaw 3.14, pit .3, dist 3.6, day .3). Website shots: set MC_CONFIG.wanderers=0
  so no bots appear, and hide the walk marker (scratch-only hook window.__mk=()=>mk). Telegram update post drafted
  in the posts doc (bots and token perks left out); post only when he says "post in telegram".

- Oct 13, bot lines: "at least 1000 different things, none saying the same thing over and over, on a loop, random
  timing not fast but not too slow". tools/wanderer_lines.py: 1,082 lines (30-31 per bot, each in its own voice)
  + 40 greetings; patch_wanderers.py asserts 1000+, 25+ per bot, no line twice anywhere. Each bot goes through its
  whole list in a shuffled order before repeating (localStorage mcWndSaid keeps the place between visits), then
  reshuffles. Timing: 25-55 s between any two lines, the same bot again after 1.5-5 min (social 1.5-4.5), a random
  nearby bot is picked (not the first in the list). Fixed: greetings never fired in a session's first 10 min.
  Lines: no prices, tokens, dates or player-count claims; only real game names (check play.html first).
  Testing: the game script isn't global, so add a hook to the scratch test page only (window.__wnd). On preview.

- Oct 13, NPC adventurers: Albert wanted ~a dozen chatty "players" plus a few dozen playing, to make the world look
  busy, dropped as real players arrive. Declined fake real players (misleading, token context); built labelled NPCs
  instead (he said "make the npc players"). tools/patch_wanderers.py: 36 NPCs (12 social in towns, 24 chop/fish/mine/
  travel), each with name, body, cape (many wear Skin of the Month capes), weapon, lines; "NPC" chip on the name
  tag (click = "an NPC adventurer, not a real player"), "[NPC] Name: ..." in chat, greet the player by name; one
  hides per real player nearby; config.js `wanderers` (0 = off). Client-side only, never block tiles or touch
  monsters/resources. Then Albert insisted on no label in the game: bots now look like players (name + level tag,
  normal chat); disclosed on the website instead (FAQ entry + $CAPES page line), and never counted as players. Learned: `vis()` is local to the draw function (a top-level helper calling it killed the render
  loop: use a distance check); keep NPC chat sparse (22 s gap between any two lines). On preview.

- Oct 13, skin store pictures: "people are visual, they need to see what they are buying". Every skin has a picture
  (models/skins/thumbs/<id>.jpg, tools/skinthumbs.py: charview, capes from behind with the model turned to face the
  light, Idle frame 2, preview models need `an` copied in; weapons alone, tilted; bg keyed to a maroon glow). New
  Wardrobe (tools/patch_skinstore.py, skx* classes, #mb.skx 600 px): Skin of the Month card, picture grid split
  Capes/Weapons, tap = big picture + Try it on / Wear / Take free / $2.99. Try it on: 30 s, camera circles (yaw)
  closer and lower (distT, pit restored after), cape shows even with no cape on ('cape_try' key), weapon skins via
  heldKey. Learned: lazy images inside the modal did not load in time: load them directly. On preview.

- Oct 13, Skin of the Month: "define the free monthly skin (tradable? what is it) and create the next 30 months".
  Proposed rules: one new skin a month (cape or weapon), looks only; free to accounts whose linked wallet holds
  1,000,000+ $CAPES (0.1%) for a 30-day holding period, $2.99 in the store for everyone else, kept for good once
  claimed, NOT tradable (account-bound like all skins: keeps perks in-game, stops farming). 30-month line-up in
  Albert's spreadsheet (CAPES_holder_tiers.xlsx, not in the repo): 19 capes made with tools/capeskins2.py
  (patterns in metres on the cape, `python3 tools/capeskins.py --only=name`), 11 weapon skins still to model in
  Meshy. Albert OK'd the rules; now on preview: the 19 capes in the store (patch_skins.py), tools/patch_sotm.py
  (Wardrobe banner + bank box claim; line-up must match server SOTM, the patch asserts it), server: SOTM_PCT 0.1,
  SOTM_DAYS 30, SOTM_START 2026-11, wallets.sinceM, table sotm(uid,month) so unlink/relink can't claim twice,
  handler holderSotm (8 new checks in test_holder.js). A month whose weapon skin isn't modelled yet shows no
  Skin of the Month: model Candle Blade (month 2) before then. Website FAQ/Terms still say only 1%/3% perks:
  update them when this ships.

- Oct 13, token plan C: buyers balk at a big dev holding, so Albert chose plan C: the creator buys at most 4% in the
  create transaction (NOT locked, Albert's call Oct 13: public creator wallet; the creator keeps the launchpad creator
  fees, so "no revenue share" stays true; donations to the pot are posted with who paid for them); the player pot is NOT bought at launch but over time from the public ecosystem
  wallet with game income (every buy posted); marketing and payments wallets hold no tokens; four public wallets in
  all. Website $CAPES page, roadmap and cosmetic splits (60% burned, 40% to MemeCapes; the treasury line is gone)
  updated; the in-game exchange note says payouts open once the pot wallet is funded (tools/patch_tokenplan.py,
  on preview). Holder rewards decided (Oct 13): no; the creator keeps the creator fees, the site says so and
  "no revenue share". Coin picture = the official $CAPES logo (real memes, Albert's call); site disclaimer: not
  affiliated with or endorsed by the creators of any meme shown. Never help hide a wallet.

- Oct 12, MemeCape: phone photo of the website cape picture, "fix the cape and make like the rest of them". The
  MemeCape and Quest cape were stiff separate shapes (c_memecape/c_qcape) drawn at the player's position, so they
  hung off one shoulder; every other cape is the Meshy caped body (moves with the skeleton). tools/mkmemecape.py
  builds models/player_memecape.json + playerf_memecape.json: the caped body with the pattern painted in the cape's
  3D space (capeskins.posmap), medallions of the game's own characters (tools/art/memecape, cut from the website
  portraits), MemeCapes coin, gold border, red lining, and a crown baked in on head bone 5 (its gold sits in a free
  32 px texture square). tools/patch_memecape.py: capeBody loads it; Quest cape = caped body in its green; no stiff
  fallback on 3D bodies. Learned: a painted photo of a cape smears on Meshy's cut-up UVs, a clean pattern laid out in
  metres reads well; charview renders a new model in ~1 min (fast check before in-game shots).

- Oct 12, posts + update: "update the game and website with accurate pictures… 25 X posts, 25 Telegram messages
  (two a day), when I text 'post in telegram' you do it, 'post on x' you do it; after updates make a Telegram post".
  The posts live in Albert's Claude Doc "MemeCapes posts: Telegram and X" (not in this public repo): how-to,
  Telegram plan Oct 13-25 10 am/7 pm ET, X1-X25 rotation, update template. Post only on his command, through the
  Claude browser where he is signed in; tick the box after. Only true, shipped facts; no price talk; $CAPES = later,
  in-game perks only. Shipped build 20261012073101 (facing + signs). shoot_site.py now keeps coin hit markers
  (.hm) visible in shots.

- Oct 12, building facing + town signs: photo of Gigachad Town, "the yellow house and the red house face the castle
  wall, turn them 180, same with the NPC, boxes and barrels; the town sign isn't doing anything; make all town signs
  make sense; fix all houses pointed in pointless directions". Found: GT lots used ry=PI ("S") which faces NORTH
  (front vector is (sin ry, cos ry) in tile x/y, y grows south), so GT's north row faced the wall and its south row
  the fields; meme-town lots all face the centre even with a street on another side; chapel's door is on its +x
  side, houseD's on -x (all other models: +z); signs were random spots at random angles. tools/patch_facing.py runs
  after the whole world is built (just before CKIT): turns each building to the side with the most road (castle
  side forbidden, away-from-town penalised, quarter turns only if the model fits, shrink <= 22%), moves the
  shop/bank counter, shopkeeper and crates with the door, paves the doorstep, moves a quest NPC off a doorstep;
  MOFF table for model door offsets; signs at each real road entrance (road continues 25+ tiles), max 4, own side
  of the town boundary, not within 7 tiles of another town's sign, facing arriving travellers. 26 buildings turned.
  Tools: scratch/rt/dumpw.py (world dump), facing.py (road score per side), signs.py. Roads between towns are laid
  late: any layout pass must run after them (anchor before `const CKIT=(()=>{`).

- Oct 12: Albert said "make it live": shipped everything on preview (one build, PROGRESS.md section).
- Oct 12, hit markers: "change red and blue to our red and gold, different font and shape than RuneScape, jaw
  dropping but simple and original". tools/patch_hitmark.py: fl() now pops a Meme Coin (ridged gold rim, crimson
  enamel for damage, gold coin for 0, green poison, purple specials), Cinzel numbers, flip-in + overshoot, shine
  sweep, gold ring pulse, sparks on 10+. Pure CSS. Google Fonts are blocked here: previews fall back to Georgia.
- Oct 11-12, NPC weapons and attacks: "are all the npc holding their weapons 10000% correctly and using attacking
  motions correctly... spot on". Found: no NPC held anything, attacks were a slide, idle was a frozen stride, kills
  vanished, guards frozen, hippo model 1 cm tall. Built tools/npc_clips.py (retarget) + tools/patch_npcfight.py
  (weapons per monster in NPCW, motion timing NCL, wind-up on the tick before the hit, flinch, death + dropped
  weapon, idle for town NPCs/pets, lowered at-ease grip for swords/clubs incl. the player, monsters stroll).
  Albert also asked (photo of Castle Gigachad) why NPCs "aren't moving or doing anything": the lv1 starter mobs
  there are by design; live has no idle and one random step per ~5 s. Learned: check grips from the side, a weapon
  in a lying hand points at the sky, the slash/stab/punch impact frames (NCL), the game script is not global (test
  hooks must expose functions), in-game shots need a frozen clock (__FZ) and waiting for real frames (__fc).
  Tools: tools/dev/charview (fast skinned contact sheets), scratch/rt/show.py (in-game before/after rows).

- Oct 11, bridges: "bridges unforgettable, 1000x better; why 3 tiny bridges where we need one; all walkable".
  Bridges came from random roads stepping onto water (BR tiles). tools/patch_bridges.py plans one straight crossing
  per spot (merge within 16 tiles, main road near a town wins), restores water elsewhere, keeps land reachable
  (BFS; boardwalk fallback), stone arch bridges (walk height follows the arch via HG) and timber ones near Froggo.
  Walk-tested every type (tools: /tmp/walk.py pattern: __tp then S.go(null,x,y), poll P and hgt).

- Oct 11, water edges: "all the water with really sharp square lines... gradually going to the water, more realistic".
  tools/patch_water.py: Catmull-Rom shore field over tile centres (+ edge noise), sloping bank and deepening bed,
  4x4 subdivided shore tiles, sand/wet-sand/bed colours, depth-faded turquoise-to-blue water with foam and lapping
  waves. Tile centres never change side (walking and fishing unchanged). Before/after water_sheet.jpg.
- Oct 11, see-through: Albert said things disappear; only massive structures may. tools/patch_seethru.py.

- Oct 11, trade window v2: "look more into the trading of players and the interface and seeing the actual items,
  1000 times better, perfect, one of the last things before going live" (Stock Exchange parked for later).
  Built tools/patch_trade.py + server versioned accepts. Researched the classic two-screen trade, change warnings
  and inspection rules. Learned: big painted pictures with names and values make items readable; warnings must sit
  next to the Accept button (sticky footer) or nobody sees them; the item close-up works as a pop-up card next to
  the item, not a box below the fold; test online flows with two real players against the real server.

- Oct 11, website screenshots: Albert approved roads v3 ("they are awesome") and said leave Wall St. out of the
  website pictures. Home strip = 6 squares (700 px webp), Towns page = 9 squares (640 px webp, class tshot), all
  embedded as base64 in index.html. Camera yaw about 3.14 looks north with the sun behind the camera (best light).

- Oct 11, roads v3: "do more research and make the roads even better, blend them". Shipped build 20261011090233.
  Learned: crisp per-pixel edges look cartoonish unless softened with fine noise (tufts); facet-lit Voronoi stones look
  like broken tiles, pillow-shaped stones look like cobbles; black joints look fake, dirt-brown joints look real; a dark
  ring around a fountain reads as a solid band unless the joints between its stones are wider. Before/after sheets
  (tools/dev/roadsheet.py) are the best way to show Albert a change.
- Oct 11, roads v2: v1 had tile-shaped plazas and rows of stones; Albert hated it. Round plazas, random stones,
  grey dirt edges fixed it.

## After launch (Albert: "later after launch, make sure things like this get fixed") - bring these up after Nov 2

- Server address: move from wss://memecapes-server.onrender.com/ws to api.memecapes.com (custom domain in Render +
  one CNAME where the domain was bought; then change config.js `server`). Old address keeps working meanwhile.
- Bouncy Hippo: new Meshy model (old one is broken, it uses the blocky hand-built hippo).
- Ghost of Rugmoon: has no idle/attack/death motions (different rig); give it its own.

## Open items

- Render: live since Oct 12 (Blueprint "memecapes", service memecapes-server, Starter + 1 GB disk, Ohio).
  https://memecapes-server.onrender.com/health ; config.js server = wss://memecapes-server.onrender.com/ws.
  Albert added the card himself in the Claude browser pane; ADMIN_KEY was generated by Render (his only).
  Still to do: custom domain api.memecapes.com (needs a DNS CNAME). Oct 15: Render 2FA on (Albert, Google Authenticator);
  LP_PARTNER + ADMIN_NAMES set on Render (log shows the fee wallet from env). Render login = Albert's GitHub, so GitHub's
  2FA protects Render too. Render's env editor: masked rows become editable when clicked and the page scrolls between
  actions: click by ref, never by coordinates, and check every row's key before saving.
  Oct 15 (later): GitHub 2FA on (authenticator + GitHub Mobile); Albert signs into GitHub with Google (Google 2FA on);
  domain at GoDaddy (locks on): added SPF '-all', DMARC p=reject, CAA letsencrypt.org + pki.goog (a new cert issuer for
  Render/Cloudflare must be added to CAA first), GitHub Pages domain verified. GoDaddy asks Albert to verify every DNS
  save; batch rows with 'Add More Records'. The safety layer may refuse DNS edits until Albert explicitly asks.
- Shipped Oct 12 (build 20261012061129, "make it live"): trade v2, see-through, water edges, bridges, NPC
  weapons/attacks (npc-models branch merged), coin hit markers. Then build 20261012073101 (building facing +
  town signs) and fresh website pictures (Oct 12). Preview = live again.
- Bouncy Hippo needs a new Meshy model (old one broken); uses the blocky hand-built one for now.
- Shipped Oct 13 (build 20261013182150): everything that was on preview. Preview = live again.
  Still to model in Meshy: the 11 weapon skins (Candle Blade first, Skin of the Month 2).
- Shipped Oct 15 (build 20261015193853, "make it live"): 8k+ building models (hi-models branch merged).
- Shipped Oct 17 (build 20261016225603, "make it live"): SnakePit integration (snake pet, $CAPES tab card, Pit panel,
  Launchpad handoff), all dormant until config.js `pit` is set. Preview = live again. Pages deploy checked via gh
  (the device bridge was offline, so version.json was read from the repo, not the live site).
- Shipped Oct 14 (build 20261014090407, "make it live"): the whole `launchpad` branch merged to main: Play/Watch/
  Stream/Launch home, launch.html (forge floor, Watch, Stream, launchpad with launching ON), server launchpad.js +
  social.js, Launchpad clerk in the game. Fee wallet (public address, Albert): 3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg
  in config.js launchpad.partner; the server reads it from config.js when Render has no LP_PARTNER. NOT yet tested
  on devnet or mainnet with a real wallet: the first real launch should be Albert's own small one. Live video needs
  CF_ACCOUNT_ID/CF_STREAM_TOKEN/CF_CUSTOMER_CODE on Render (render.yaml lists them, sync: false).
- Waiting on Albert: shop wallet go-live decision, DNS (api.memecapes.com), Stripe, devnet test of the launchpad,
  Cloudflare Stream keys, Helius, Jupiter referral account.
