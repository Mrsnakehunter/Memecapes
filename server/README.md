# MemeCapes game server

Accounts, cloud saves, other players in the world, chat, and player-to-player trades.
Plain Node.js 22 with no packages to install (built-in SQLite, crypto and a small WebSocket layer).

## What it does
- **Accounts**: username + password (stored scrambled with scrypt). One login at a time per account.
- **Cloud saves**: the game uploads progress every ~10 seconds. Each save has a number, so an old save can never overwrite a newer one (for example, a trade).
- **Live players**: everyone within 48 tiles sees everyone else move, 5 times a second, with their name, level and cape.
- **Chat**: everyone online, a word filter (`badwords.txt`), 1 message per 1.2 s, ignore, report.
- **Trades**: the server checks both offers against each player's saved bag and does the swap itself. Untradeable items (capes, pets, custom shop items, clue, lamps) are refused.
- **Cheat watch**: big jumps in coins or XP between saves are written to a flags list for a moderator to look at.
- **Moderators**: `/announce text`, `/mute name minutes`, `/unmute name`, `/kick name`, `/ban name`, `/unban name`, `/rollback name` (undo that player's last save), `/mod name` (make a mod).
- **Holder perks**: a player links their wallet by signing a short free message in their wallet app (not a transaction). The server reads that wallet's $CAPES balance from the blockchain at link time, at every login and once a day at a random hour. Holding at least `HOLDER_PCT` % of all $CAPES = free Cape Club membership while it lasts, and one free skin from the skin store after `HOLDER_DAYS` days of holding without dropping below, then every `HOLDER_DAYS` days. One wallet per account. Passing tokens to another wallet restarts the count, so the same tokens can't collect extra skins. `node test_holder.js` checks all of it against a fake blockchain.
- **Partners**: a wallet that has held at least `PARTNER_PCT` % of all $CAPES for `PARTNER_DAYS` days can run a free partner ad: a billboard with their picture and an NPC (their name, line, link and cape colour) in each of the 8 meme towns, plus that cape colour for themselves. They make the ad at any bank; an admin reviews it with `/partner view Name` and `/partner approve Name` or `/partner reject Name reason` (`/partner list`, `/partner remove Name`). Partner wallets are checked every 15 minutes, and the ad comes down at the first check below `PARTNER_PCT` %. Going back above restarts the `PARTNER_DAYS` count. `GET /partners` is the live list and `GET /partners/<id>.jpg` their billboard pictures.
- **Backups**: a copy of the database every day, the last 14 kept, in `DATA_DIR/backups`.

## Settings (environment variables)
| name | what |
|---|---|
| `PORT` | set by the host |
| `DATA_DIR` | where the database lives. On Render: `/var/data` (the disk) |
| `ADMIN_KEY` | password for the admin pages below. Render makes one for you |
| `ADMIN_NAMES` | your in-game name(s), comma separated. Those accounts get moderator commands. **Create that account right after the server starts, before anyone else can take the name.** |
| `CAPES_MINT` | the $CAPES token mint address. Empty = holder perks stay "coming soon" |
| `SOLANA_RPC` | Solana RPC address for the balance checks. Default: the free public one; a paid one (Helius, QuickNode) is more reliable |
| `HOLDER_PCT` | how much of all $CAPES a wallet must hold for the perks, in %. Default 1 |
| `HOLDER_DAYS` | days between free skins (and the first wait). Default 14 |
| `PARTNER_PCT` | share of all $CAPES for a partner ad, in %. Default 3 |
| `PARTNER_DAYS` | days at that share before the ad goes live. Default 14 |
| `ALLOWED_ORIGINS` | websites allowed to connect. Default: memecapes.com and localhost |

## Admin pages
Send the header `Authorization: Bearer <ADMIN_KEY>`:
- `/admin/stats`: who is online, how many accounts
- `/admin/flags`: suspicious saves
- `/admin/holders`: linked wallets, their share of $CAPES, whether they pass, free skins claimed
- `/admin/partners`: every partner ad, its status and whether it is live
- `/admin/reports`: player reports with the chat around them
- `/admin/backup`: download the whole database

## Test it
`node test.js`: starts a throwaway server and runs fake players through sign-up, saves, chat, positions and a full trade.

## Turning it on (Render)
1. render.com, sign in with GitHub, New, Blueprint, pick the `Memecapes` repo. It reads `render.yaml`: a $7/month Starter web service plus a 1 GB disk.
2. When asked, type your in-game name for `ADMIN_NAMES`.
3. Settings, Custom Domains: add `api.memecapes.com`. Render shows a CNAME record; add it where you manage the memecapes.com domain.
4. In `config.js` set `server: "wss://api.memecapes.com/ws"` and push. Every push to GitHub also updates the server by itself.
