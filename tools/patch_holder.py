#!/usr/bin/env python3
"""Holder perks: hold at least 1% of all $CAPEZ in your own wallet = free Cape Club membership and one free
shop skin every 14 days (the server decides: server/server.js, "holder perks").

In the game: a "Holder perks" box at every bank. Link wallet asks the player's wallet app (Phantom, Solflare)
to sign a short free message that proves the wallet is theirs; no transaction, nothing moves. The server reads
the balance from the blockchain itself. When a free skin is ready, the Wardrobe shows "Take free" next to each
skin in the store. window.mcMember() says whether this player has Cape Club (for the members-only content
that comes in Update 1.5). Needs online play; it stays "coming soon" until the server has CAPES_MINT set.
Run from the repo root after patch_skins.py:  python3 tools/patch_holder.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""
// ---- holder perks (tools/patch_holder.py; the rules live on the server)
const HPK=()=>NETS.holder||null;
window.mcMember=()=>!!(HPK()&&HPK().member);
function hpkWalletApp(){const w=window;return (w.phantom&&w.phantom.solana)||(w.solana&&w.solana.isPhantom&&w.solana)||w.solflare||w.solana||null}
const hpkDate=t=>new Date(t).toLocaleDateString(undefined,{month:'short',day:'numeric'});
function holderHTML(){const H=HPK(),need=H?H.need:1,days=H?H.days:14;
 let h='<div id="hpk" style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Holder perks</b><br><span style="font-size:12px">Hold at least '+need+'% of all $CAPEZ in your own wallet: free Cape Club membership, and one free skin from the skin store every '+days+' days.</span><br>';
 if(!SRV()||!NETS.on)return h+'<span style="color:#ccc;font-size:12px">Needs online play: log in from the start screen.</span></div>';
 if(!H||!H.on)return h+'<span style="color:#ccc;font-size:12px">Not open yet: it opens once the public player pot wallet is funded.</span></div>';
 if(!H.wallet)return h+'<span style="font-size:12px">Link the wallet that holds your $CAPEZ. Your wallet app asks you to sign a short message: it is free, it is not a transaction and nothing moves. We never ask for your seed phrase.</span><br><button data-hp="link">Link my wallet</button><div id="hpr" style="font-size:12px;margin-top:4px"></div></div>';
 h+='<span style="font-size:12px">Wallet <b>'+H.wallet.slice(0,4)+'...'+H.wallet.slice(-4)+'</b> holds <b>'+(+H.pct||0)+'%</b> of all $CAPEZ'+(H.checked?' (checked '+hpkDate(H.checked)+')':'')+'.</span><br>';
 if(H.err)h+='<span style="color:#ff7a59;font-size:12px">The last check could not reach the blockchain. It tries again within the hour.</span><br>';
 if(H.member){h+='<span style="color:#7dff9a;font-size:12px">Cape Club: active while you keep '+need+'% or more.</span><br>';
  h+=H.canClaim?'<span style="font-size:12px;color:#ffd23f">Your free skin is ready.</span> <button onclick="mcWardrobe()">Pick it in the Wardrobe</button><br>':'<span style="font-size:12px">Next free skin: '+hpkDate(H.claimAt)+(H.claims?'':' (after '+days+' days of holding)')+'.</span><br>'}
 else h+='<span style="color:#ccc;font-size:12px">Below '+need+'%: no perks right now. Perks start at the next check after you reach '+need+'%; the free skin needs '+days+' days of holding without dropping below.</span><br>';
 return h+'<button class="ghost" data-hp="unlink">Unlink wallet</button><div id="hpr" style="font-size:12px;margin-top:4px"></div></div>'}
async function hpkLink(){const r=$('hpr'),p=hpkWalletApp();
 if(!p){if(r)r.innerHTML='No wallet app found in this browser. Open memecapes.com/play.html inside your wallet app (Phantom or Solflare), or on a computer with the wallet extension, then link here.';return}
 try{if(r)r.textContent='Asking your wallet app...';const c=await p.connect();const pk=((c&&c.publicKey)||p.publicKey);const w=pk&&pk.toString();if(!w)throw new Error('no address');netSend({t:'walletNonce',wallet:w})}
 catch(e){if(r)r.textContent='Your wallet app did not connect. Nothing was linked.'}}
async function hpkSign(m){const p=hpkWalletApp(),r=$('hpr');if(!p)return;
 try{const pk=p.publicKey&&p.publicKey.toString();if(pk!==m.wallet){if(r)r.textContent='Your wallet app switched address. Try again.';return}
  const s=await p.signMessage(new TextEncoder().encode(m.msg),'utf8'),sig=(s&&s.signature)||s;let b='';for(const x of new Uint8Array(sig))b+=String.fromCharCode(x);
  netSend({t:'walletLink',wallet:m.wallet,sig:btoa(b)});if(r)r.textContent='Signed. Checking your $CAPEZ...'}
 catch(e){if(r)r.textContent='You did not sign, so nothing was linked.'}}
function holderWire(){MB.querySelectorAll('[data-hp]').forEach(b=>b.onclick=()=>{if(b.dataset.hp=='link')hpkLink();else netSend({t:'walletUnlink'})})}
function hpkRefresh(){if(M.style.display=='none')return;if($('wrd'))wardrobeUI();else if($('hpk'))modal('bank')}
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", JS + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", 1)
# the server's messages
rep(" saved(m){NETS.rev=m.rev;LS.set('mc_rev',String(m.rev))},",
    " saved(m){NETS.rev=m.rev;LS.set('mc_rev',String(m.rev))},"
    "holder(m){NETS.holder=m;hpkRefresh()},walletSign(m){hpkSign(m)},"
    "skinGift(m){st.skins=m.skins;(st.wear=st.wear||{})[skById(m.skin).g]=m.skin;NETS.rev=m.rev;LS.set('mc_rev',String(m.rev));save();ui();say('Holder gift: '+skById(m.skin).n+' is yours and it is on. Thanks for holding $CAPEZ.','#0a0');hpkRefresh()},")
# the bank box
rep("function depHTML(){", "function depHTML(){return depHTML1()+holderHTML()}function depHTML1(){")
rep("function depWire(){", "function depWire(){holderWire();")
# the Wardrobe: take a free skin when one is ready
rep("let h='<h2>Wardrobe</h2>", "const HC=HPK()&&HPK().canClaim;let h='<h2 id=\"wrd\">Wardrobe</h2>")
rep("h+='<h2 style=\"margin-top:14px\">Skin store</h2>",
    "if(HC)h+='<div style=\"margin-top:10px;padding:8px;border:1px solid #ffd23f;border-radius:6px;font-size:12px;color:#ffd23f\">Holder gift: take any one skin below for free.</div>';h+='<h2 style=\"margin-top:14px\">Skin store</h2>")
rep("<span style=\"color:#ffd23f;white-space:nowrap\">$2.99</span></div>'})",
    "'+(HC?'<button data-hc=\"'+s.id+'\">Take free</button>':'<span style=\"color:#ffd23f;white-space:nowrap\">$2.99</span>')+'</div>'})")
rep(" MB.querySelectorAll('[data-wr]').forEach(b=>b.onclick=",
    " MB.querySelectorAll('[data-hc]').forEach(b=>b.onclick=()=>{netSaveNow();netSend({t:'holderClaim',skin:b.dataset.hc});b.disabled=true;b.textContent='...'});MB.querySelectorAll('[data-wr]').forEach(b=>b.onclick=")

open(PATH, 'w', encoding='utf-8').write(h)
print('holder perks patch applied')
