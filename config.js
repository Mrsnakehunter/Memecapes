/* MemeCapes settings. This is the ONLY file Albert edits to switch things on.
   Put PUBLIC addresses only (the kind you share to get paid). Never a seed phrase or private key.
   Leave a value empty ("") and that feature stays switched off and shows "coming soon". */
window.MC_CONFIG = {
  // ---- online play: the game server address. Empty = everyone plays offline in their own browser.
  // After the server is running on Render it will be "wss://api.memecapes.com/ws"
  server: "",

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
  solUsdFallback: 150,           // used only if the live SOL price can't be fetched

  // ---- shop (prices in US dollars; SOL is worked out at the live price, $CAPES at capesUsd)
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

  // ---- redeem codes for things sold in the shop: SHA-256 of the code -> what it gives
  // make one with:  python3 tools/mkcode.py cape "Shiny cape"
  codes: {}
};
