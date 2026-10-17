/* MemeCapes settings. This is the ONLY file Albert edits to switch things on.
   Put PUBLIC addresses only (the kind you share to get paid). Never a seed phrase or private key.
   Leave a value empty ("") and that feature stays switched off and shows "coming soon". */
window.MC_CONFIG = {
  // ---- online play: the game server address. Empty = everyone plays offline in their own browser.
  // Live on Render since Oct 12, 2026. Later it can move to "wss://api.memecapes.com/ws" (custom domain).
  server: "wss://memecapes-server.onrender.com/ws",

  // ---- bots: how many walk the world (they look like players; the website FAQ says so). One hides for every
  // real player nearby. Lower it as real players arrive; 0 switches them off.
  wanderers: 36,

  // ---- who to contact
  contactEmail: "",              // e.g. "memecapes@gmail.com" once you make it
  xHandle: "Mrsnakebaby",        // shown as the contact until the email is set
  governingLaw: "the State of Ohio, United States",
  termsVersion: "2026-10-10",    // change this date when the Terms change: everyone is asked to agree again

  // ---- Solana
  rpc: "https://api.mainnet-beta.solana.com",          // a paid RPC URL is more reliable at launch
  shopWallet: "",                // your PUBLIC Solana address that receives shop payments (SOL and USDC both arrive here)
  usdcMint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  // USDC on Solana (official, do not change)
  capesMint: "",                 // the $CAPES token mint address, once the token exists
  capesWallet: "",               // PUBLIC address that receives $CAPES deposits from players
  pit: "https://snakepit-mu.vercel.app",   // SnakePit, the trading app next to the game (switch to "https://pit.memecapes.com" once its DNS is set). Empty = the game shows nothing about it
  solUsdFallback: 150,           // used only if the live SOL price can't be fetched

  // ---- shop (prices in US dollars; SOL is worked out at the live price, $CAPES at capesUsd)
  burnPct: 1,                    // burn this % of all $CAPES for the website ad spot (must match BURN_PCT on the server)
  capesUsd: 0,                   // price of 1 $CAPES in dollars, once it trades (0 = $CAPES not accepted yet)
  shop: [
    { id: "billboard", name: "Town billboard", days: 7,  usd: 50,
      text: "Your project's banner on a billboard in one meme town for 7 days. Art supplied by you, approved by us." },
    { id: "sponsor",   name: "Sponsored monster", days: 30, usd: 250,
      text: "Your community's mascot as a monster in the world for 30 days, with its own drops. Must be your own character." },
    { id: "cape",      name: "Custom cape", usd: 75,
      text: "A one-of-a-kind cape with your design, worn in 3D. Delivered as a redeem code for your account." },
    { id: "item",      name: "Custom item", usd: 40,
      text: "A cosmetic hat, pet skin or held item with your design. Cosmetic only: no combat stats. Delivered as a redeem code." },
    { id: "skin",      name: "Skin", usd: 2.99,
      text: "One weapon or cape skin. Weapons: Laser Eyes Blade, Up Only Axe, Diamond Hands Pick, Moon Rocket Bat, The Rug Pull, Crescent Staff. Capes: Green Candles, Red Candles, Laser Eyes, Diamond Hands, Moon Night, Meme Coin Gold. Write which one in the notes. Looks only, no stats. Delivered as a redeem code." },
    { id: "skin4",     name: "Skin bundle (any 4)", usd: 9.99,
      text: "Any four skins from the list above, in one redeem code. Write which four in the notes." }
  ],

  // ---- $CAPES and Meme Coins
  capesToMemeCoins: 100,         // 1 $CAPES deposited = this many Meme Coins
  depositsOpen: false,           // true = players can deposit $CAPES for Meme Coins (needs capesMint and capesWallet)
  withdrawalsOpen: false,        // keep false until the game server exists (see the note in the game's bank)

  // ---- Launchpad (launch.html): coins launched on memecapes.com, built on Meteora's bonding curve on Solana.
  // partner = the PUBLIC address of the MemeCapes launchpad fee wallet. Empty = launching is switched off (the page
  // still shows coins). Albert signs everything from that wallet himself; nobody else ever needs its keys.
  launchpad: {
    partner: "3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg",   // MemeCapes launchpad fee wallet on mainnet (public address, set by Albert Oct 14)
    partnerDevnet: "3rDgFxM6Yz6fCCvrpkhAL32Bq67qGDu22HpQWVBHuCjg",   // the same wallet on Solana's test network (?net=devnet), for testing
    streamPassUsd: 20,           // the streamer pass: a flat monthly fee to stream, paid in SOL at the live price. 0 = streaming is free
    streamPassDays: 30,          // how long one payment lasts
    streamPassWallet: "",        // PUBLIC address the pass is paid to; empty = the launchpad fee wallet above
    rpcDevnet: "https://api.devnet.solana.com",
    burnShare: 50,               // % of MemeCapes' launchpad income that buys $CAPES and burns it (every burn posted)
    // what launchers can choose (the server refuses coins outside these limits)
    feeBps: { min: 25, max: 200, def: 100 },              // trading fee on the bonding curve, in basis points (100 = 1%)
    creatorShare: { min: 50, max: 80, def: 60 },          // % of the fee left after Meteora's 20% that goes to the launcher
    sniperFee: { maxBps: 5000, defBps: 2500, defSeconds: 60, maxSeconds: 600 },  // starting fee that falls to the normal fee
    graduation: [                                         // market cap in SOL when the coin moves to a real pool
      { id: "quick", name: "Quick", mcapSol: 200 },
      { id: "standard", name: "Standard", mcapSol: 400 },
      { id: "big", name: "Big", mcapSol: 1000 }
    ],
    startMcapSol: 28,            // market cap in SOL at the first trade
    postFeeBps: { min: 25, max: 200, def: 100 },          // trading fee on the graduated pool
    teamMaxPct: 10,              // most of the supply a launcher can set aside for a team, always locked and vested
    creationFeeSol: 0,           // fee to launch a coin, in SOL (0 = free)
    jupReferral: "",             // Jupiter referral account (make one at referral.jup.ag) = MemeCapes earns a fee on swaps of graduated coins
    jupFeeBps: 50                // that fee, in basis points (50 = 0.5%; Jupiter keeps 20% of it)
  },

  // ---- redeem codes for things sold in the shop: SHA-256 of the code -> what it gives
  // make one with:  python3 tools/mkcode.py cape "Shiny cape"
  codes: {}
};
