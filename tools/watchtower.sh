#!/usr/bin/env bash
# Watchtower: checks from the outside, every 15 minutes (GitHub runs it, see .github/workflows/watchtower.yml), that
#  1. memecapes.com still points at GitHub Pages (a hijacked domain would point somewhere else),
#  2. every important file the site serves is byte-for-byte the file in this repo (catches a tampered or swapped page,
#     the way the Bybit and Ledger thefts worked),
#  3. the wallet addresses the live config.js shows are the official ones listed below,
#  4. the game server is up, and what mode Sentinel is in.
# Problems open (or add to) a GitHub issue labelled "watchtower", which emails the repo owner. Needs: curl, gh, sha256sum, dig.
set -u
SITE=https://memecapes.com
SERVER=https://memecapes-server.onrender.com
FILES="index.html launch.html play.html config.js gate.js solpay.js shop.js burnad.js lp/app.js lp/social.js lp/chain.js lp/lpcore.js memesnake/index.html"
# the official public wallets. Changing one here is a deliberate act and shows in the repo history.
OFFICIAL_WALLETS="3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # fee wallet; USDC mint
PAGES_IPS="185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153"
problems=()

# 1. DNS
ips=$(dig +short A memecapes.com | sort | tr '\n' ' ')
for ip in $ips; do
  case " $PAGES_IPS " in *" $ip "*) ;; *) problems+=("memecapes.com points to $ip, which is not GitHub Pages (all: $ips). The domain may be hijacked: check the registrar account now.");; esac
done
[ -z "$ips" ] && problems+=("memecapes.com did not resolve at all.")

# 2. files: live vs repo. A push takes a few minutes to go live, so a difference is checked again before it counts.
check_files() {
  local bad=()
  for f in $FILES; do
    live=$(curl -sfL --compressed --max-time 30 "$SITE/$f" | sha256sum | cut -c1-64) || live=missing
    repo=$(sha256sum "$f" | cut -c1-64)
    [ "$live" != "$repo" ] && bad+=("$f")
  done
  echo "${bad[*]:-}"
}
diff1=$(check_files)
if [ -n "$diff1" ]; then
  sleep 300; git pull -q --ff-only 2>/dev/null || true
  diff2=$(check_files)
  [ -n "$diff2" ] && problems+=("The live site serves different files than the repo: $diff2. If nobody pushed in the last 15 minutes, a page may have been tampered with: switch the server to lockdown (/guard lockdown) and check GitHub and the domain.")
fi

# 3. wallets on the live config.js
live_cfg=$(curl -sfL --max-time 30 "$SITE/config.js" || true)
for w in $(printf '%s' "$live_cfg" | grep -oE '"[1-9A-HJ-NP-Za-km-z]{32,44}"' | tr -d '"' | sort -u); do
  case " $OFFICIAL_WALLETS " in *" $w "*) ;; *) problems+=("The live config.js contains a wallet address that is not on the official list: $w");; esac
done

# 4. the game server
health=$(curl -sf --max-time 60 "$SERVER/health" || true)
if [ -z "$health" ]; then problems+=("The game server did not answer $SERVER/health.")
else
  mode=$(printf '%s' "$health" | grep -oE '"mode": *"[a-z]+"' | grep -oE '[a-z]+"$' | tr -d '"')
  [ -n "$mode" ] && [ "$mode" != "normal" ] && problems+=("Sentinel has the server in ${mode^^} mode right now.")
fi

echo "dns: $ips | files differing: ${diff1:-none} | server: ${health:-down}"
if [ ${#problems[@]} -eq 0 ]; then echo "all good"; exit 0; fi
body="Watchtower found a problem at $(date -u '+%Y-%m-%d %H:%M UTC'):"$'\n'
for p in "${problems[@]}"; do body+=$'\n'"- $p"; done
printf '%s\n' "$body"
if [ -n "${GH_TOKEN:-}" ]; then
  gh label create watchtower --color B60205 --description "Watchtower security alerts" 2>/dev/null || true
  open=$(gh issue list --label watchtower --state open --json number --jq '.[0].number' 2>/dev/null)
  if [ -n "$open" ]; then gh issue comment "$open" --body "$body"; else gh issue create --title "Watchtower alert: check memecapes.com" --label watchtower --body "$body"; fi
fi
exit 1
