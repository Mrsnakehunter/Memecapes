# MemeCapes: working notes for Claude

Read this first in every session. Add to it after every task (what was asked, what worked, what the owner disliked),
so each task starts smarter than the last. This repo is PUBLIC: no business plans, wallet details, keys or private
numbers in here or anywhere in the repo.

## Owner and dates

- Owner: Albert (GitHub Mrsnakehunter, X @Mrsnakebaby), Ohio. Writes fast and casually; wants results, not questions.
  When he says "ship" or "keep going", ship and keep going.
- Launch: Mon Nov 2, 2026. Server live about Oct 19, playtest Oct 19-25, freeze Oct 28.

## Standing rules (never break)

- Never touch crypto wallets, seed phrases, private keys or transactions. Albert signs everything himself.
  A 32-44 character base58 string is a public address, not a seed phrase: say so.
- No posting on X until launch.
- Show screenshots before pushing big game changes live, unless Albert has said ship.
- IP safety: no RuneScape, OSRS or Jagex names, art or wording anywhere. All names are our own.
- Token honesty: no hidden wallets, no promised gains; holder perks are in-game only.
- Never push test hooks. `grep -c '__tp=tpTo\|window.__g=' preview.html play.html` must print 0 for both
  (grep exits 1 on a count of 0, so don't chain it with &&).
- Don't read or handle auth tokens, passwords or one-time codes. A Stripe secret key goes only in Render.
- Meshy credits: allowed to spend.
- Money or legal questions: give facts and trade-offs, not a recommendation, and say I'm not an advisor or lawyer.

## Build and ship

- The game is one file. `tools/build.sh` rebuilds play.html from the base by running every `tools/patch_*.py` in
  order, then makes preview.html and the test pages (tools/dev/mktest.sh, copied from scratch: test.html, test2.html, test3.html, test7.html).
- Ship: `tools/ship.sh` (copies preview.html to play.html, writes version.json). Check the live build number at
  https://memecapes.com/version.json.
- PROGRESS.md is the public log: add a dated section for every shipped feature, in plain words.
- Patches use exact-string `rep(old, new, count)` with an assertion; if an anchor moves, fix the anchor, never loosen it.

## Screenshots and testing

- Shots: `python3 tools/dev/shoot_site.py plan.json` with jobs {name, day, setup, tp, wait, act, cam:[yaw,pitch,dist],
  camwait, frames}. Output in scratch/shots/site; the game canvas is x 0-840 of the 1100 px shot.
- The test machine renders with SwiftShader (software). Heavy shaders make it slow: use wait 30000 and camwait 12000,
  or the shot shows sky or the wrong place.
- Make the character tough in `setup` (xp 2e7, hp 999) or monsters kill it and it respawns in Gigachad Town.
- Rain: `(Date.now()/60000)%17 < 4`. Day: `((Date.now()/1000)%1800)/1800`. Shift time with window.__toff / __day(dp).

## Engine facts learned the hard way

- The ground is drawn by shader program pg3 (not pg). Its vertex colours blend road and grass per corner
  (road weight 3, grass 1, water 0); the normal's length carries the paving material and amount.
- Texture units 0-4 are taken; the road map uses unit 5. WebGL1: NPOT textures need CLAMP_TO_EDGE and no mipmaps.
- A JS comment inside a Python string inside a JS string breaks things: keep GLSL comments out (patch_roads.glsl()
  strips them).

## Art direction (Albert's feedback)

- Roads: NO straight lines, NO rows or grids of stones, NO bulky lines. Randomised, natural, realistic.
  Plazas round and symmetrical. Grey dirt around cobbles, blending into normal dirt. Cobblestone in towns,
  concrete only at Wall St., dirt in the countryside and Froggo's Pond.
- He likes: the original dirt ground re-coloured grey as a blend zone; things that look real rather than tiled.
- Techniques that worked for the ground (roads v3): per-pixel road edges from a road-tile texture with noise warp;
  height blending (dirt fills joints first, stones sink, tops show last); pillow-shaped stones lit by the sun;
  subtle colour variety; fade fine detail with distance; wet darkening and sky-reflecting puddles in rain.

## Open items

- Retake the website screenshots (home strip and Towns page) from the current game once Albert approves the roads.
- Waiting on Albert: shop wallet go-live decision, Render server address, DNS, Stripe.
