# MemeCapes progress

_Last updated: October 10, 2026 (morning)_

## Where to look

- **Website:** [memecapes.com](https://memecapes.com/), the game's own address (the old github.io link now sends you here).
- **Live game:** [memecapes.com/play.html](https://memecapes.com/play.html), the current public version with the full 3D world.
- **Preview:** [memecapes.com/preview.html](https://memecapes.com/preview.html), where new things land first. Right now it's the same as the live game.

## Live now

- **119 3D building and prop models** made for the world, each sized to match the characters.
- **All 8 meme towns** have their own themed houses and landmarks: Wow Landing, Froggo's Pond, Stonks City, Diamond Hands, Rugpull Ridge, HODL Heights, Moon Landing and Chad Falls. Gigachad Town has its own building set.
- **Town details:** themed lamps, signposts in every town, a herald's sign where players start, market stalls, wells, fountains, crates, docks at the fishing spots and lily pads on the pond.
- **Countryside:** boulders, logs, stumps and mushrooms, haystacks and scarecrows at the farms, ruins, graves, a camp with tents and campfires, mine carts, a dwarven gate at the Copium Mountains, a lunar lander and craters at Moon Landing.
- **Copper and tin rocks** use real 3D models, and the Meme Caves have a rocky mine entrance.
- **The Meme Ring** and the **Meme Coin icons** for stacks of 1 up to 10M+.

## Live now (shipped tonight)

- **Every town re-spaced:** each building sits on a lot the size of its 3D model with two tiles of clear ground around it, roads lead to the doors, no overlaps anywhere. Gigachad Town got a fresh layout with the bank and store either side of the castle gate.
- **Skills go to level 100**, and level 100 is 20,000,000 XP (our own curve). Health starts at level 12. Mastery capes are for level 100.
- **Our own pet names:** Lumber Chonk, Pet Rock and Gull of Wall Street for the skilling pets, plus the five dog pups.
- **Lamp posts** turn to face each other across the roads, and at night every lantern is a real light: it lights the ground, walls, props and players around it with a warm glow that fades with distance (no more flat circle on the ground).
- **Themed banks and general stores in every town** (15 new buildings).
- **A 3D blacksmith forge and cooking range** in every town.
- **New painted inventory pictures for all 99 items:** weapons, tools, food, gems, potions, masks, helmets, armour and capes.
- **Chat box:** the message log scrolls back through the last 150 lines, and there's a chat line at the bottom (press Enter, type, Enter to send). What you say shows in the log and floats over your head next to a little MemeCapes cape medallion, so other players will see who's talking. Ready to hook up to the multiplayer server.
- **Bigger bag:** 35 slots (5 across, 7 down), up from 28.
- **All 13 weapons and tools in the character's hands:** bronze, iron and blue-steel swords, bronze and iron axes and pickaxes, bonk club, nail bat, swamp staff, cyber staff, the endless scroll, and the kite shield on the left arm. They follow the hands through the walk and run animations.

## Launch pieces (live October 10, 2026)

- **18+ and policy gate** before the website or the game opens (asked again whenever the Terms change).
- **Terms of Service and Privacy Policy** on the site (Ohio law), linked from the gate and the footer.
- **Shop** on the site: town billboards, sponsored monsters, custom capes, custom items, paid in SOL, USDC or (later) $CAPES from the buyer's own wallet. The page checks the payment on the blockchain and writes the order. It stays switched off until the official shop wallet address is in `config.js`.
- **At any bank in the game:** deposit $CAPES for Meme Coins (switched off until the token exists), redeem codes from the shop. Withdrawing $CAPES opens with the game servers.
- **config.js** holds every address, price and switch. `tools/mkcode.py` makes redeem codes.

## Shipped to the live game on October 10, 2026

Everything below is now on play.html (it used to be preview only).

- **The world is bigger:** 512 by 448 tiles instead of 384 by 384. The original map is untouched; new land was added east and south: Ember Coast (north-east, with a volcano), Wall St. (east, hugging the shore), the Trenches (south, below Rugpull Ridge) and Normie Island (south-east, sea only). Thick wandering land bridges and new roads join them to the nearest towns. The land is empty for now; buildings come next.

- **The MemeCape:** the real cape from the site, worn in 3D with the hood and crown over your head. 100,000,000 Meme Coins at the cape merchant.
- **Quest cape:** the same cape without hood and crown, for finishing every quest. 100,000 Meme Coins.
- **Capes of Accomplishment** now cost 1,000,000 Meme Coins.
- "Welcome to MemeCapes" appears ten seconds after you enter.
- The mouse wheel over the side panel scrolls the panel instead of zooming the camera.
- New, unique skill cape pictures are coming.
- **The Meme Telly:** the ring network only takes you to towns you have walked into once (Castle Gigachad is always home). Teleport tablets follow the same rule.
- **New quest, The Grand Tour:** walk to all eight meme towns in order, easiest first. 2 quest points.
- **Shops show pictures** of everything they sell (shop, forge, cape merchant).
- **The Stock Market works like an exchange now:** six offer tickets, buy and sell offers at your own price, offers that fill over time, a collect box, a price guide and a history tab. Until the game servers exist, the market itself takes the other side of every offer near the guide price; the same screens switch to player offers when the server arrives.
- **Player-to-player trade screen:** both players add items and coins, both accept, both seal it, then the swap happens. If either side changes anything, both accepts reset and the changed side flashes. A practice partner at the Stock Market broker lets you try it today.
- **Every name is ours now.** The frog is Froggo (Froggo's Pond, Telly code FRG), the chill dog is the Vibe Dog, the Shiba is the Shibe, plus Bouncy Hippo, Nutty the Squirrel and the Ghost of Rugmoon. The prayer book has 15 new prayers (Touch Grass to Unbonkable), the emotes are meme emotes (Stonks, GG, Ratio, Griddy...), bounties replace tasks (Bounty Boss Bonkwell, skip for 25 points), and the More tab has Town tasks, Loot log, Combat feats and Leaderboards. Meme hunts and strongboxes, wish lamps, Mastery capes, the Home Telly and Telly tablets, Diamond Hands mode (no trading), the right-click menu in plain words, a new XP curve (level 100 is still 20,000,000) and a new combat level formula. Froggo borrows the bog frog's model until he gets his own.
- **The MemeCapes look for every screen:** crimson velvet and gold leaf, the website's Cinzel titles, the medallion in the header. The Stock Market has a live ticker tape of guide prices, tickets with inked BUY / SELL / FILLED stamps, and a price line for every item (its last 24 moves). The trade screen has two vaults, a fairness bar (what you give against what you get), a warning when you are giving far more than you get, and a red wax seal you press to finish. Shops, the bank, quests and the cape merchant all wear the same look, and so do the side panel, the chat scroll, the start screen, the world map, the minimap ring, the status pills and the right-click menu.
- A Wall St. town around the Stock Market is on the new land.
- **No more flat pictures:** Froggo, Bonk Hounds, NPC Guards and Dogwifhat now use 3D models, and the dog pups are small 3D models too.

## Built October 10, 2026 (early morning): online play and caped characters

- **Game server** (`server/`): accounts with passwords, progress saved on the server, other players walking around with their name and level over their heads, global chat with a word filter, ignore and report, and real player-to-player trades that the server checks and swaps itself. Moderator commands (mute, kick, ban, roll back a save, announce), a list of suspicious saves, daily backups. `node server/test.js` runs 30 checks with fake players. No packages to install.
- **In the game:** "Play Online: Log in / Create Account" on the start screen, "Continue online as …", bring your browser progress into a new account once, chat commands `/who /trade /ignore /report /logout /deleteaccount`, click a name in chat to trade, ignore or report. The game also says when a new update is out.
- **It stays offline until the server is switched on**: `config.js` → `server: ""`. Setup steps are in `server/README.md` (Render, about $7 a month, updates itself on every push).
- **Caped characters:** wearing any cape switches the character to a caped body made in Meshy (male and female), and the cape is painted in that cape's colour. The MemeCape and Quest cape keep their hooded models. Tools: `tools/glb2rig.py` (rigged Meshy character → game model, any bone count) and `tools/capemask.py`.

## Built October 10, 2026 (morning): real animations (preview)

- **Every character now moves with real motion-captured style animations** from Meshy: the male and female players and both caped bodies, 38 to 39 animations each.
- **Combat:** sword slash, sword stab, punch and kick (each cut to the one strike that matters, timed to your weapon speed), a flinch when you get hit, and a proper fall backwards when you die.
- **Skills:** a real two-handed chop at trees with the axe in hand, an overhead pickaxe swing at rocks, a bend-and-scoop at fishing spots with a new **shrimp net** in your hand, and stirring at the range.
- **Also:** idle breathing, the Home Telly spell cast, a jump for agility shortcuts, and all 22 meme emotes (Stonks, GG, Ratio, Griddy, Sigma...) play their own dance or gesture.
- Animations are only prepared the first time they play, so loading stays fast. Tools: `tools/glb2rig.py` + `tools/clipmap.json` (which Meshy motion is which game animation), `tools/mknet.py` (the net).

## Built and waiting for a spot in the world

- **Lava zone set:** obsidian hut, furnace cave and lava bridge.
- **Stone and wooden bridges, walls and fences.**
- **Tutorial island buildings:** bakery, camp, quest hut, shrine, vault, training yard and a portal dock.
