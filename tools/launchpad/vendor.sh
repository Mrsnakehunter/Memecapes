#!/bin/sh
# Clones the exact library sources the launchpad bundle is built from (lp/lpcore.js), into $LP_VENDOR.
# Only git access to github.com is needed (no npm). Then: node tools/launchpad/build.mjs
set -e
V=${LP_VENDOR:-/home/claude/scratch/lp/vendor}
mkdir -p "$V"; cd "$V"
c() { [ -d "$2" ] || git clone -q --depth 1 ${3:+-b $3} "https://github.com/$1.git" "$2"; echo "$2 $(git -C "$2" rev-parse --short HEAD)"; }
c MeteoraAg/dynamic-bonding-curve-sdk dbc-sdk
c MeteoraAg/dynamic-bonding-curve dbc-program
c solana-foundation/solana-web3.js web3 maintenance/v1.x
c solana-foundation/anchor anchor v0.31.1
c anza-xyz/kit kit
c paulmillr/noble-curves noble-curves 1.9.7
c paulmillr/noble-hashes noble-hashes 1.8.0
c indutny/bn.js bn.js v5.2.1
c MikeMcl/decimal.js decimal.js v10.5.0
c feross/buffer buffer v6.0.3
c beatgammit/base64-js base64-js v1.5.1
c feross/ieee754 ieee754 v1.2.1
c ianstormtaylor/superstruct superstruct2 v2.0.2
c ianstormtaylor/superstruct superstruct015 v0.15.5
c tedeh/jayson jayson v4.1.3
c nickyout/fast-stable-stringify fast-stable-stringify
c solana-labs/buffer-layout solana-buffer-layout
c near/borsh-js borsh v0.7.0
c cryptocoinjs/bs58 bs58 v4.0.1
c cryptocoinjs/base-x base-x v3.0.9
c feross/safe-buffer safe-buffer v5.2.1
c pabigot/buffer-layout buffer-layout v1.2.2
c sindresorhus/camelcase camelcase v6.3.0
c primus/eventemitter3 eventemitter3 4.0.7
