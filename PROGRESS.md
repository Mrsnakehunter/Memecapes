# MemeCapes progress

_Last updated: October 17, 2026_

## Oct 17, 2026: a new front door

The home page now says who makes it: MemeCapes, powered by snakepit, run by MemeSnake, in gold above the floating Meme Cape (snakepit opens the trading side, MemeSnake opens the AI agent's page). The "Straight from the game" pictures are replaced by the 37-second tour video (it plays silently as you scroll to it; tap "Play with sound" for the music) and two shots of your snakepit snake following you through Wow Landing. The Launch side of the site (Coins, Watch, Stream, Hatch) now wears snakepit's own logo and colours, and anyone without a wallet can make one free by signing in to snakepit with their email.

## Oct 17, 2026: SnakePit is on

SnakePit, the trading app that pairs with MemeCapes, is live, and the game and website are now connected to it. Link a wallet at any bank and a mint-green snake follows you around the world, as long as your snake in the Pit. The $CAPES tab shows your snake's segments, rank and record, with a button to trade $CAPES in the Pit. Launching a coin now happens in the Pit (the Launchpad clerk and the Launch page send you there), so there is one launchpad with one set of rules. Trading in the Pit costs 0.4% per trade, flat.

## Oct 17, 2026: ready for the Pit

The game now knows about SnakePit, the trading app that pairs with MemeCapes. Nothing shows until the Pit is switched on, and then: a small mint-green snake follows you around the world, one segment for every segment your snake has in the Pit, and the $CAPES tab at any bank gets a "Your snake" card (segments, rank, realized SOL, wins and losses, streak) with a "Trade $CAPES in the Pit" button. The Launch page gets a Pit panel and the Launchpad clerk sends you to the Pit to hatch a coin. The game server fetches your snake from the Pit once a minute and keeps the last good answer if the Pit is ever down.

## Oct 16, 2026: calmer monsters and adventurers

Monsters and the other adventurers were moving too fast. Monsters out for a stroll would stand still, then dash to catch up with where they were going, faster than a player walks, with their legs pumping almost twice as fast as a player's. Now a strolling monster ambles along at an easy, steady pace and its legs move at the same rate as yours for the ground it covers. A monster chasing you still keeps up. The adventurers walking around the world now walk like everyone else. On a really long trip one might break into a jog, but nobody sprints around town anymore.

## Oct 16, 2026: Support page

The website has a Support page (the Support link at the top, next to AI Agent). Type a few words and it answers at once: 260 plain answers covering getting started, accounts and login, online play, every skill, combat, items and the bank, towns, quests, capes, Meme Coins and $CAPES, skins, trading, the shop, the launchpad, Watch and Stream, the AI Agent, safety and scams, technical trouble and the rules. Each answer knows the many ways people ask the same thing, 11,471 phrasings in all, so "forgot password", "can't log in" and "how do I recover my account" all land on the same answer. There are topic buttons for browsing, a Most asked list, and a Still stuck box that points to the official X account. The answers are honest about what the game can and cannot do (there is no password reset yet, bots are disclosed, $CAPES does not exist yet) and say nothing about how the servers are guarded.

## Oct 15, 2026: real trees

The scribbly code-drawn trees are gone. Every one of the 4,300 trees in the world is now a proper 3D model with a painted texture, and there are 16 kinds: oak, beech, maple, birch, weeping willow, cherry blossom, dead tree, pine, spruce, fir, snow-covered spruce, Italian cypress, palm, a crystal alien tree, and two kinds of bush. Which kind grows where follows the land: conifers and oaks in the forests, dead trees around Rugpull Ridge, snow trees around HODL Heights, cypresses and palms on the Chad Falls hills, willows by Froggo's Pond, blossoms near Diamond Hands and Wow Landing, alien trees at Moon Landing. Each tree has its own size, turn and shade (some oaks and beeches turn orange, some birches yellow), leafy trees sway in the wind, and all of them cast shadows and darken in the rain like everything else. Chopping works as before: a chopped tree leaves its stump.

It is built not to slow the game down: trees come in three detail levels (full detail up close, lighter further out, a simple shape in the distance) and are drawn in a handful of batches instead of one by one. The densest forest in view costs about 200,000 triangles, about what one town's buildings cost.

## Oct 15, 2026: sharper buildings

Every building and prop in the world (109 of them: houses, banks, shops, chapels, towers, bridges, wells, rocks, stalls and more) now has a more detailed shape, with at least 7,500 triangles each, up from about 3,000 to 6,000. Round things like well rims, arches, barrels and fountains are smoother, and nothing moved: every model keeps the same size, place and textures.

## Oct 15, 2026: the Security page

A new Security page (in the menu after AI Agent) explains how MemeCapes is guarded. It covers Sentinel inside the servers, Watchtower outside them, the daily AI security patrol, why there is nothing at MemeCapes worth stealing, and four habits that keep players safe from scams.

## Oct 15, 2026: the stronghold (security)

- **Sentinel, an always-on guard inside the game server.** It knows every visitor's real address and blocks floods, hacker probes and password or admin-key guessing on its own. An account name locks for 15 minutes after 8 wrong passwords. One address can hold at most 8 game connections. Every answer from the server carries security headers.
- **Shield and lockdown modes.** In shield, new accounts, uploads, launches, posts and ads pause while play and payments go on. Lockdown also pauses new sign-ins. Sentinel switches to shield by itself during an attack, and admins can switch modes in game with `/guard`. Payments already made on the blockchain are always counted, in every mode.
- **Alarms.** Sentinel raises an alarm if the wallet addresses in config.js ever change, and it pauses uploads before the server disk fills.
- **Watchtower checks the site from outside every 15 minutes.** It confirms the domain still points at our host, that every page is byte-for-byte the one in this repo, that the live wallet addresses are the official ones, and that the server is up. Any problem opens an alert.
- **Fixes:**
  - Coin pages only use links that start with https://, and only read a coin's details from our own server.
  - Fee splits show every full address before you approve.
  - The streamer pass is only ever paid to the official wallet in config.js.
  - Devnet test money can no longer buy a pass.
  - Graduated coins now trade on jup.ag in a new tab, so no outside code runs inside memecapes.com.
  - Other sites can't show our pages inside a frame.
  - The launch page gets a strict content policy.
  - Wallet sign-in messages name the site.
  - Wallet sessions are stored as hashes.
- **New FAQ entry:** "How does MemeCapes keep me safe?"

## Oct 15, 2026: tidier NPCs page

On the NPCs page, characters with finished pictures come first and the ones whose pictures are still coming sit at the bottom of each section. Characters that share a look never sit side by side.

## Oct 15, 2026: a simpler menu

The website menu now has five things: Play, Watch, Stream, Launch and AI Agent. All the game pages (story, NPCs, items, towns, quests, capes, roadmap, $CAPES, shop and FAQ) live inside Play.

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

## Shipped October 14, 2026 (late): see what other players are doing (live)

- **Other players now show what they're doing.** When another player stands still you see them idle, chopping, fishing, mining, fighting or dancing, holding the weapon or tool they really have and wearing their cape skin. Before, other players stood in a stiff pose with empty hands.
- **The world's characters move at real speeds**, walking a tile a step and running on longer trips, and they keep a little space from each other instead of bunching up.

## Shipped October 14, 2026 (evening): online first, a calmer town square (live)

- **Online is now the way in.** The start screen leads with "Play Online: Create Account" and "Log in". The browser-only ways to play are folded under "Play offline instead (nobody else can see you)", so nobody ends up alone by accident. Already played offline? Create an account and tick "bring my progress".
- **You always know if you're online.** A small sign at the top of the screen says "Online" with how many players are on, or "Offline: other players can't see you" with a button to go online.
- **A calmer Gigachad Town.** Fewer bots hang around the starting town (5 instead of 10; the others moved to the meme towns), and the ones that stay wander the whole town and stop to chat and look around instead of pacing one spot.

## Shipped October 14, 2026: Play, Watch, Stream, Launch (live)

- **The home page now opens on four words:** PLAY, WATCH, STREAM and LAUNCH, beside the floating Meme Cape. Each one is a door into a side of memecapes.com.
- **Launch: the MemeCapes Launchpad.** Anyone can launch a Solana coin from memecapes.com. You pick the trading fee and how much of it you keep, bots that buy in the first seconds pay a sniper fee that fades to the normal fee, you can split your share with up to 10 wallets, and the coin's liquidity is locked for good when it graduates. Every coin page shows a launch check (who bought in the launch block, who sniped, what they still hold), where every fee goes, recent trades and the coin's own posts. Half of what MemeCapes earns from the launchpad buys $CAPES and burns it, and every burn is posted. It runs on Meteora's audited bonding-curve program; your wallet signs everything and MemeCapes never holds your keys or your money.
- **Coins look like coins.** Every coin on the launchpad is a struck gold coin: a reeded rim, a molten ring that fills as it nears graduation, a glow that cools over its first day, a laurel once it graduates, and it tilts toward your pointer. New coins land on the forge floor the moment they are made: the latest strike is spotlit, the hottest run along a rail, then the walls: Fresh from the forge, Heating up, In the vault.
- **Watch: the trading floor.** Live trades slide in as they happen (whale buys marked), the wallet of the hour is spotlit, the featured stream plays with its chat beside it, and a feed takes posts (tag a coin with its $TICKER) and shows launches, whale buys, graduations, streams and tips. Trending coins and the day's top wallets sit on the right. Sign-in is your wallet signing a short message, never a transaction.
- **Stream: go live and keep everything.** Name a channel, go live from your browser (camera or screen) or from OBS with a stream key, attach your coin so viewers get a buy box under your video. A streamer pass is a flat $20 a month, paid in SOL from your wallet, and it is the only charge: viewers tip and subscribe in SOL, straight from their wallet to yours, and MemeCapes takes nothing from that. Watching is free. Live video switches on once the streaming service is connected; channels, chat, tips and subscriptions work now.
- **In the game:** a Launchpad clerk in Gigachad Town and Stonks City shows the newest coins and opens the launchpad.
- **Website:** the Watch and Stream pages, a "Launch a coin while you play" section on the home page, and a Launchpad link in the menu.

## Shipped October 13, 2026: Skin of the Month, a skin store with pictures, the MemeCape, a livelier world (live)

- **Skin store with pictures.** The Wardrobe shows a picture of every skin, capes and weapons in their own sections.
  Tap one for a big picture, then Wear it, take it free if you can, or buy it for $2.99.
- **Try it on.** Any skin can be tried on for 30 seconds before you buy: your character wears it and the camera
  circles round so you can see it from every side.
- **Skin of the Month.** One new skin each month, a cape pattern or a weapon look (looks only, never stats). Accounts
  whose linked wallet has held at least 0.1% of all $CAPES for 30 days take it free at any bank or in the Wardrobe,
  once per account; everyone else can buy it in the store, and it stays there after its month. Skins belong to your
  account and can't be traded. 19 new cape patterns are in the store.
- **The MemeCape and the Quest cape** are now real capes that hang from the shoulders and move with your character,
  like every other cape. The MemeCape has medallions of the game's own characters, a gold border and a crown.
- **The exchange** says plainly that payouts open once the player pot wallet is funded.
- **A livelier world.** The game has bots that look like players (the FAQ says so): a dozen hang around the towns,
  wave, dance and chat, and two dozen chop trees, fish, mine and walk the roads. They have over a thousand different
  things to say, each one works through all its lines before it repeats one, and they talk at random, unhurried
  times. They never trade, never take your kills or resources, and there are fewer of them as more people play.
  Bots are never counted as players.
- **Website:** the FAQ explains the Skin of the Month and the bots, and the Terms cover skins.

## Shipped October 12, 2026 (later): every building faces its street, town signs at the roads in (live)

- **Buildings face the street.** Each house, shop and bank turns its front door to the side of its lot with the
  most road. In Gigachad Town the general store and the house beside it used to face the castle wall; they now open
  onto the square, and the shopkeeper's counter, the shopkeeper and the crates moved round with the door.
- **Doorsteps are paved** straight onto the nearest street.
- **The chapel and one cottage** had their doors on the side of the model; they're turned so the door is at the
  front.
- **Town signs where they make sense:** every town has a sign on each real road into town (up to 4), standing beside
  the road at the edge of town and facing you as you walk in. The old signs in dead corners are gone. Gigachad Town's
  herald signs stand at its gate roads.
- **New website pictures,** taken from the game as it is today.

## Shipped October 12, 2026: monsters that fight back, coin hit markers, water, bridges, trading (live)

- **Monsters hold real weapons and really fight.** Guards and Ratio Knights carry a sword and shield, Bonk and the
  Bonk Hounds a bat (with an overhead BONK), Floki an axe, the Rage Goblin a spiked club, shamans and cultists
  staffs, and the brawlers use their fists and feet. Each attack is a real motion: a wind-up, then the blow lands
  the moment the hit number appears. Spell casters raise their staff and throw the bolt.
- **They react.** Monsters flinch when you hit them and fall over when they die, dropping their weapon, instead of
  vanishing. Standing monsters breathe and look around, stroll a few steps near home, and turn to watch you.
- **Town guards, bankers, shopkeepers, quest characters and pets** stand naturally instead of frozen mid-step.
  Guards hold sword and shield at ease. Swords and clubs (yours too) hang at your side when you're not swinging.
- **The Bouncy Hippo is visible again** (its 3D model was broken; it uses its hand-built model for now).
- **New hit markers: Meme Coins.** Every hit pops up as a minted coin with a ridged gold rim: crimson for damage,
  gold for a zero, green for poison. It flips in, lands with a gold ring pulse and a shine, then floats away.
  Big hits (10+) are bigger and throw off gold sparks.
- **Water with real shores:** sloping sandy banks, wet sand, shallow turquoise water that deepens to blue, foam and
  lapping waves, instead of square edges.
- **Proper bridges:** one stone arch bridge (or a timber one near Froggo's Pond) where a road crosses water,
  instead of several small ones. Every bridge is walkable and you walk up and over the arch.
- **See-through only for big buildings:** only the castle and the tallest buildings turn see-through when they
  block your view. Trees, bushes, booths and small houses always stay.
- **Trading, rebuilt:** big item pictures with names and values, a close-up card for any item, warnings right next
  to Accept when the other player changes the offer, a second check screen, and a trade history. Works online once
  the game server is up.

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

## Website, October 11, 2026

- **Fresh screenshots from the current game:** all six home page pictures (Stonks City market square, fishing at Froggo's Pond, Castle Gigachad at night, the MemeCape worn, a fight outside Wow Landing, Chad Falls town square) and all nine town pictures on the Towns page, with the new cobbled roads.

## Built October 11, 2026 (morning): roads v3 (live)

- **Natural road edges everywhere:** dirt roads now meet the grass with wavy, uneven edges and little grass tufts, instead of blurry tile-shaped smudges. The grass along a road is a bit worn and yellower.
- **Real-looking cobbles:** each stone is rounded and lit by the sun, with dirt and moss in the joints and its own shade of grey, blue-grey or warm tan.
- **Paving that blends into dirt:** where a plaza ends, dirt fills the joints first, then the stones sink into the dirt with only their tops showing, then a few loose stones, then grey dirt, then dirt. Plazas stay round.
- **Fountain squares:** a collar of big pale flagstones and a ring of edge stones around the fountain in every paved town.
- **Rugpull Ridge** is properly run down: stones missing, dirt washed over them, moss in the gaps.
- **Wall St.** has kerb stones and straight, clean street edges, with staggered concrete slabs and stains.
- **Rain** darkens and wets the stones and dirt, and puddles collect on the dirt and reflect the sky. Loose pebbles on country roads. Far-off plazas no longer shimmer.

## Built October 11, 2026: road surfaces (live)

- **Roads are no longer all dirt.** Town centres are cobblestone, by how important the place is: Castle Gigachad and Gigachad Town (the capital) with the King's Road down to Wow Landing, Stonks City, Diamond Hands, Moon Landing, HODL Heights and Chad Falls get big round cobbled plazas; Wow Landing gets a small cobbled market square; Rugpull Ridge has worn cobbles with stones missing; Froggo's Pond stays swamp mud. **Wall St. is the only concrete.**
- **Real-looking cobbles:** irregular, randomly sized and shaded stones, no rows or grid. Plazas are smooth and round (Gigachad Town a rounded rectangle), not tile-shaped.
- **Grey dirt edges:** every paved area is ringed with grey dirt that blends into the normal dirt roads (cobble, then grey dirt, then dirt), and the stones thin out one by one at the edge. Country roads stay dirt. The minimap and world map show paved streets in grey.
- Drawn by the terrain shader: nothing extra to download. Tool: `tools/patch_roads.py`.

## Built October 10, 2026 (late night): website ads for burning 1% (switched off until the token exists)

- **Burn 1% of all $CAPES = your ad on the memecapes.com home page.** One ad card in the page flow, styled like the site's own cards and labelled Sponsored. No pop-ups, nothing sticky, no motion, hidden when there are no ads.
- **The spot is shared:** each visit shows one ad, with odds by how much each project burned (1% = 1 share, 2% = 2 shares).
- **Approval before burning:** the project sends its ad in the Shop (wallet signature, no transaction), Albert approves it in game (`/burnad view 7`), then they burn from the same wallet and paste the transaction; the server checks the burn on the blockchain and the ad goes up. Terms say burns are not refundable.

## Built October 10, 2026 (night): partners (switched off until the token exists)

- **Hold at least 3% of all $CAPES for 14 days = a free partner ad for as long as you keep 3%:** a billboard with your picture and an NPC (your line, link and cape colour) in every meme town, plus that cape colour for your own character. With more than 8 partners the billboards take turns.
- Partners make their ad in the "Partners" box at any bank; Albert approves each one (`/partner view Name`). Partner wallets are checked every 15 minutes; under 3% everything comes down. Going back over 3% starts a new 14 days.

## Built October 10, 2026 (evening): holder perks (switched off until the token exists)

- **Hold at least 1% of all $CAPES = free Cape Club membership, plus one free skin from the skin store every 14 days** (the first after 14 days of holding). Linked at any bank by signing a free message in the wallet app; the server checks the balance on the blockchain at link time, every login and daily.
- Switch on with `CAPES_MINT` on the Render server (`HOLDER_PCT`, `HOLDER_DAYS`, `PARTNER_PCT`, `PARTNER_DAYS`, `BURN_PCT`, `BURN_AD_DAYS` change the numbers). Server tests: `node server/test_holder.js` (51 checks) and `node server/test.js` (30).

## Built October 10, 2026 (afternoon): skins

- **12 skins, $2.99 each.** Six weapon skins made in Meshy: Laser Eyes Blade (swords), Up Only Axe (axes), Diamond Hands Pick (pickaxes), Moon Rocket Bat and The Rug Pull (clubs and bats), Crescent Staff (staffs and scrolls). Six cape skins painted onto the caped bodies: Green Candles, Red Candles, Laser Eyes, Diamond Hands, Moon Night and Meme Coin Gold. Looks only, no stats.
- **Wardrobe** (a button in the Gear tab): wear or take off each skin you own, and see the skin store. A weapon skin replaces every weapon of its type in your hand; a cape skin works on every cape except the MemeCape and the Quest cape.
- **Selling them:** until card payments exist, a skin comes as a redeem code (`tools/mkcode.py skin sk_laser`, or `skin bundle` with four ids for the $9.99 bundle). The website shop lists "Skin" and "Skin bundle (any 4)"; it stays switched off until the shop wallet is set.
- Tools: `tools/decimate.cpp` (lowers a full-detail Meshy model to a game-sized one and keeps its texture; used by `tools/glb2mdl.py --tris`), `--orient/--flip/--mirror/--rotx` to stand held items up, `tools/capeskins.py` (the cape patterns).

## Built October 10, 2026 (day): launch content

- **Chapter 1, The Great Rug: five new story quests** with three new quest givers. Chef Bagholder needs cake ingredients from Wow Landing, three forgetful Wojaks hold your seed phrase, Farmer Ted's allotments are full of Doomscrollers, Fisherwoman Nemo's pond is being drained, and the Bot Captain attacks the castle gate. Rewards include the first Cape fragment. Froggo's first quest is now called Proof of Work. The Quest cape needs the chapter too.
- **Starter Guide** for new players: nine steps (walk, Froggo, chop, fire, fish, cook, mine, fight, bank) with a gold arrow over the next target. After the guide, the same card shows your current quest step and where to go.
- **Faster loading:** the game file went from 7 MB to 1.4 MB (the castle models now load on their own and stay cached between updates), and phones keep less animation data in memory.
- **Website:** Quests page lists the new chapter, FAQ and roadmap updated for online play, and later-chapter names changed to our own (Burn Gauntlet, Burnzilla, the Rug Pit, the Liquidator).

## Built October 10, 2026 (morning): real animations (live)

- **Every character now moves with real motion-captured style animations** from Meshy: the male and female players and both caped bodies, 38 to 39 animations each.
- **Combat:** sword slash, sword stab, punch and kick (each cut to the one strike that matters, timed to your weapon speed), a flinch when you get hit, and a proper fall backwards when you die.
- **Skills:** a real two-handed chop at trees with the axe in hand, an overhead pickaxe swing at rocks, a bend-and-scoop at fishing spots with a new **shrimp net** in your hand, and stirring at the range.
- **Also:** idle breathing, the Home Telly spell cast, a jump for agility shortcuts, and all 22 meme emotes (Stonks, GG, Ratio, Griddy, Sigma...) play their own dance or gesture.
- Animations are only prepared the first time they play, so loading stays fast. Tools: `tools/glb2rig.py` + `tools/clipmap.json` (which Meshy motion is which game animation), `tools/mknet.py` (the net).

## Built and waiting for a spot in the world

- **Lava zone set:** obsidian hut, furnace cave and lava bridge.
- **Stone and wooden bridges, walls and fences.**
- **Tutorial island buildings:** bakery, camp, quest hut, shrine, vault, training yard and a portal dock.
