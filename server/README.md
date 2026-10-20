# MemeCapes game server

Accounts, cloud saves, other players in the world, chat, and player-to-player trades.
Plain Node.js 22 with no packages to install (built-in SQLite, crypto and a small WebSocket layer).

## What it does
- **Accounts**: username + password (stored scrambled with scrypt). One login at a time per account.
- **Cloud saves**: the game uploads progress every ~10 seconds. Each save has a number, so an old save can never overwrite a newer one (for example, a trade).
- **Live players**: everyone within 48 tiles sees everyone else move, 5 times a second, with their name, level and cape.
- **Chat**: everyone online, a word filter (`badwords.txt`), 1 message per 1.2 s, ignore, report.
- **Trades**: the server checks both offers against each player's saved bag and does the swap itself. Untradeable items (capes, pets, custom shop items, clue, lamps) are refused. Every offer change gets a version number and an accept only counts for the exact version that player saw; for `TRADE_LOCK_MS` (2.5 s) after the other player changes their offer, accepts are refused. Both players accept, then both seal on a final screen. Every finished trade is stored in the `trades` table.
- **Cheat watch**: big jumps in coins or XP between saves are written to a flags list for a moderator to look at.
- **Moderators**: `/announce text`, `/mute name minutes`, `/unmute name`, `/kick name`, `/ban name`, `/unban name`, `/rollback name` (undo that player's last save), `/mod name` (make a mod).
- **Holder perks**: a player links their wallet by signing a short free message in their wallet app (not a transaction). The server reads that wallet's $CAPEZ balance from the blockchain at link time, at every login and once a day at a random hour. Holding at least `HOLDER_PCT` % of all $CAPEZ = free Cape Club membership while it lasts, and one free skin from the skin store after `HOLDER_DAYS` days of holding without dropping below, then every `HOLDER_DAYS` days. One wallet per account. Passing tokens to another wallet restarts the count, so the same tokens can't collect extra skins. **Skin of the Month**: holding `SOTM_PCT` % for `SOTM_DAYS` days = that month's skin free, one per account per month (claims are kept per account, so unlinking and linking again does not give it twice). `node test_holder.js` checks all of it against a fake blockchain.
- **Partners**: a wallet that has held at least `PARTNER_PCT` % of all $CAPEZ for `PARTNER_DAYS` days can run a free partner ad: a billboard with their picture and an NPC (their name, line, link and cape colour) in each of the 8 meme towns, plus that cape colour for themselves. They make the ad at any bank; an admin reviews it with `/partner view Name` and `/partner approve Name` or `/partner reject Name reason` (`/partner list`, `/partner remove Name`). Partner wallets are checked every 15 minutes, and the ad comes down at the first check below `PARTNER_PCT` %. Going back above restarts the `PARTNER_DAYS` count. `GET /partners` is the live list and `GET /partners/<id>.jpg` their billboard pictures.
- **Website ads for burning**: a project sends its ad on memecapes.com (wallet signature, no transaction). An admin approves it in game (`/burnad list`, `/burnad view 7`, `/burnad approve 7`, `/burnad reject 7 reason`, `/burnad remove 7`). Only then does the project burn `BURN_PCT` % of all $CAPEZ from that wallet and paste the transaction; the server reads it from the blockchain (a real burn of the $CAPEZ mint, signed by that wallet, big enough, never used before) and the ad goes up. One ad spot on the home page, shared: each visit shows one ad, with odds = how many whole `BURN_PCT` %s each project burned. `GET /burnads` lists them. `BURN_AD_DAYS` limits how long an ad runs (0 = for good).
- **Backups**: a copy of the database every day, the last 14 kept, in `DATA_DIR/backups`.

## Settings (environment variables)
| name | what |
|---|---|
| `PORT` | set by the host |
| `DATA_DIR` | where the database lives. On Render: `/var/data` (the disk) |
| `ADMIN_KEY` | password for the admin pages below. Render makes one for you |
| `ADMIN_NAMES` | your in-game name(s), comma separated. Those accounts get moderator commands. **Create that account right after the server starts, before anyone else can take the name.** |
| `CAPES_MINT` | the $CAPEZ token mint address. Empty = holder perks stay "coming soon" |
| `SOLANA_RPC` | Solana RPC address for the balance checks. Default: the free public one; a paid one (Helius, QuickNode) is more reliable |
| `HOLDER_PCT` | how much of all $CAPEZ a wallet must hold for the perks, in %. Default 1 |
| `HOLDER_DAYS` | days between free skins (and the first wait). Default 14 |
| `SOTM_PCT` | Skin of the Month: how much of all $CAPEZ a wallet must hold to take that month's skin free, in %. Default 0.1 |
| `SOTM_DAYS` | Skin of the Month: days of holding before the free monthly skin. Default 30 |
| `SOTM_START` | Skin of the Month: month 1 of the line-up, `YYYY-MM` (UTC). Default 2026-11 |
| `PARTNER_PCT` | share of all $CAPEZ for a partner ad, in %. Default 3 |
| `PARTNER_DAYS` | days at that share before the ad goes live. Default 14 |
| `BURN_PCT` | share of all $CAPEZ to burn for a website ad, in %. Default 1. Keep `burnPct` in config.js the same |
| `BURN_AD_DAYS` | days a website ad runs; 0 = for good. Default 0 |
| `TRADE_LOCK_MS` | no accepting for this long after the other player changes their offer. Default 2500 |
| `ALLOWED_ORIGINS` | websites allowed to connect. Default: memecapes.com and localhost |
| `GUARD_WEBHOOK` | Sentinel alerts: a Discord (or Slack) webhook URL. Empty = alerts only in game and in the server log |
| `GUARD_TG_TOKEN`, `GUARD_TG_CHAT` | Sentinel alerts to Telegram: a bot token (from @BotFather) and the chat id to post in |
| `GUARD_ALLOW` | addresses Sentinel never blocks, comma separated (e.g. your own) |
| `GUARD_WS_PER_IP` | most game connections from one address at once. Default 8 |
| `PROXY_HOPS` | how many proxies add themselves to X-Forwarded-For after the visitor. Empty = the right-most public address is the visitor |
| `ALLOW_DEVNET_PAY` | `1` = devnet payments count for passes, tips and subs (testing only; never on the live server) |

## Admin pages
Send the header `Authorization: Bearer <ADMIN_KEY>`:
- `/admin/stats`: who is online, how many accounts
- `/admin/flags`: suspicious saves
- `/admin/holders`: linked wallets, their share of $CAPEZ, whether they pass, free skins claimed
- `/admin/partners`: every partner ad, its status and whether it is live
- `/admin/burnads`: every website ad, its status and how much was burned
- `/admin/reports`: player reports with the chat around them
- `/admin/backup`: download the whole database
- `/admin/guard`: Sentinel: mode, blocked addresses, locked names, disk, the latest guard log
- `POST /admin/guard/mode?to=normal|shield|lockdown`: switch Sentinel's mode

## Sentinel (sentinel.js): the always-on guard
Blocks floods, hacker probes (/.env, /wp-admin ...), password and admin-key guessing; locks a name for 15 minutes after 8 wrong
passwords; at most 8 game connections per address; security headers on every answer; pauses uploads before the disk fills;
an alarm if the wallet addresses in config.js change. Modes: `normal`; `shield` (new accounts, uploads, launches, posts and ads
paused, play and payments go on); `lockdown` (shield + no new sign-ins). It switches to shield by itself for 30 minutes when
25+ addresses get blocked in 10 minutes. In game (admins): `/guard`, `/guard shield`, `/guard lockdown`, `/guard normal`,
`/guard log`, `/guard block <ip>`, `/guard unblock <ip>`. Payments already made on-chain are always checked and counted.

## Test it
`node test.js`: starts a throwaway server and runs fake players through sign-up, saves, chat, positions and a full trade.
`node test_guard.js`: attacks a throwaway server (floods, probes, password guessing, admin-key guessing, spoofed addresses, too many connections, devnet payments) and checks Sentinel stops each one.

## Turning it on (Render)
1. render.com, sign in with GitHub, New, Blueprint, pick the `Memecapes` repo. It reads `render.yaml`: a $7/month Starter web service plus a 1 GB disk.
2. When asked, type your in-game name for `ADMIN_NAMES`.
3. Settings, Custom Domains: add `api.memecapes.com`. Render shows a CNAME record; add it where you manage the memecapes.com domain.
4. In `config.js` set `server: "wss://api.memecapes.com/ws"` and push. Every push to GitHub also updates the server by itself.
