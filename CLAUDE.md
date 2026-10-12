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

## Open items

- Render: live since Oct 12 (Blueprint "memecapes", service memecapes-server, Starter + 1 GB disk, Ohio).
  https://memecapes-server.onrender.com/health ; config.js server = wss://memecapes-server.onrender.com/ws.
  Albert added the card himself in the Claude browser pane; ADMIN_KEY was generated by Render (his only).
  Still to do: custom domain api.memecapes.com (needs a DNS CNAME), ADMIN_NAMES env var.
- Shipped Oct 12 (build 20261012061129, "make it live"): trade v2, see-through, water edges, bridges, NPC
  weapons/attacks (npc-models branch merged), coin hit markers. Preview = live again.
- Bouncy Hippo needs a new Meshy model (old one broken); uses the blocky hand-built one for now.
- Waiting on Albert: shop wallet go-live decision, DNS (api.memecapes.com), Stripe.
