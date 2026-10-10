#!/usr/bin/env python3
"""Launch pieces in the game:
- config.js, solpay.js and gate.js load first (the 18+ and policy gate; settings Albert fills in).
- At any bank: deposit $CAPES for Meme Coins (the player pays from their own wallet to the posted address,
  pastes the transaction, the game checks it on the blockchain read-only and credits Meme Coins), and
  redeem codes bought in the shop (custom capes, items, coins).
- Withdrawing Meme Coins to $CAPES stays switched off until the game server exists, because a save that
  lives in the browser can be edited, so paying real tokens out of it would let anyone drain the pot.
Run from the repo root after patch_layout.py:  python3 tools/patch_launch.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


rep('<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Alegreya:wght@400;700&display=swap" rel="stylesheet">',
    '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Alegreya:wght@400;700&display=swap" rel="stylesheet">'
    '<script src="config.js"></script><script src="solpay.js"></script><script src="gate.js"></script>')

# custom items from redeem codes come back on every load
rep("for(const k in ITM)RAR[k]=RC[ITM[k][4]];",
    "for(const k in ITM)RAR[k]=RC[ITM[k][4]];\n"
    "function regCust(k,c){const kind=ICT[c.kind]?c.kind:'cape',sl=c.slot||(kind=='cape'?'cape':kind=='helm'||kind=='mask'?'head':'');ITM[k]=[String(c.name).slice(0,40),kind,c.color||'#d9a520',String(c.ex||'One of a kind.').slice(0,120),4,0,0,0,0,sl];IC[k]=ICT[kind](c.color||'#d9a520');IN[k]=ITM[k][0];EX[k]=ITM[k][3];if(sl)SLOT[k]=sl;RAR[k]=RC[4]}\n"
    "if(st.cust)Object.keys(st.cust).forEach(k=>regCust(k,st.cust[k]));")

DEP = r"""
// ---- $CAPES in (deposits) and redeem codes, at any bank
const CFG=()=>window.MC_CONFIG||{},PAYOK=()=>!!(window.MCPAY);
function depHTML(){const C=CFG(),A=window.MCPAY,on=C.depositsOpen&&A&&A.isAddr(C.capesMint)&&A.isAddr(C.capesWallet),w=st.acct&&st.acct.wallet&&A&&A.isAddr(st.acct.wallet)?st.acct.wallet:'';let h='<div style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Deposit $CAPES for Meme Coins</b><br>';
 if(!on)h+='<span style="color:#ccc;font-size:12px">Opens when the $CAPES token launches. The address will be posted here and on the official site only.</span>';
 else{h+='<span style="font-size:12px">1 $CAPES = '+(C.capesToMemeCoins||100).toLocaleString()+' Meme Coins, paid into your bank.</span><br>';
  if(!w)h+='<span style="font-size:12px">First save the PUBLIC address of the wallet you will pay from (never your seed phrase):</span><br><input id="dpw" placeholder="Your Solana wallet address" style="width:100%;box-sizing:border-box;margin:4px 0"><button data-dp="w">Save wallet</button>';
  else h+='<span style="font-size:12px">From your wallet <b>'+w.slice(0,4)+'...'+w.slice(-4)+'</b>, send $CAPES to:</span><br><code style="font-size:11px;word-break:break-all;display:block;margin:4px 0;color:#ffe9b0">'+C.capesWallet+'</code><button data-dp="copy">Copy address</button> <a href="'+window.MCPAY.payLink(C.capesWallet,10,C.capesMint,'MemeCapes deposit')+'" style="color:#ffd23f;font-size:12px">Open in my wallet (10 $CAPES)</a><br><span style="font-size:12px">Then paste the transaction signature:</span><br><input id="dps" placeholder="Transaction signature" style="width:100%;box-sizing:border-box;margin:4px 0"><button data-dp="check">Check and credit</button> <button class="ghost" data-dp="forget">Use a different wallet</button><div id="dpr" style="font-size:12px;margin-top:4px"></div>'}
 h+='</div><div style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Withdraw Meme Coins as $CAPES</b><br><span style="color:#ccc;font-size:12px">'+(C.withdrawalsOpen?'Withdrawals open with the game servers.':'Opens with the game servers, when your Meme Coins are kept safe on our server instead of in this browser.')+'</span></div>';
 h+='<div style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Redeem a code</b><br><span style="font-size:12px">Bought a custom cape or item in the shop? Enter its code.</span><br><input id="rcc" placeholder="MC-XXXX-XXXX" style="width:60%;margin:4px 0;text-transform:uppercase"> <button data-dp="redeem">Redeem</button><div id="rcr" style="font-size:12px;margin-top:4px"></div></div>';return h}
function depWire(){const C=CFG(),r=$('dpr');MB.querySelectorAll('[data-dp]').forEach(b=>b.onclick=async()=>{const a=b.dataset.dp;
 if(a=='w'){const v=($('dpw').value||'').trim();if(!window.MCPAY.isAddr(v))return say('That is not a Solana wallet address.','#c00');st.acct=st.acct||{name:'Guest'};st.acct.wallet=v;save();modal('bank')}
 else if(a=='forget'){st.acct.wallet='';save();modal('bank')}
 else if(a=='copy'){try{navigator.clipboard.writeText(C.capesWallet);b.textContent='Copied'}catch(e){}}
 else if(a=='check'){const sig=($('dps').value||'').trim();if((st.dsig||[]).includes(sig)){r.textContent='That deposit was already credited.';return}r.textContent='Checking the blockchain...';
  const v=await window.MCPAY.verify({sig,to:C.capesWallet,mint:C.capesMint,min:1,from:st.acct.wallet,maxAgeDays:30,label:'$CAPES'});
  if(!v.ok){r.innerHTML='<span style="color:#ff7a59">'+v.err+'</span>';return}
  const mc=Math.floor(v.amount*(C.capesToMemeCoins||100));(st.dsig=st.dsig||[]).push(sig);st.bank+=mc;flow('+'+mc+' Meme Coins: $CAPES deposit');save();ui();say('Deposit found: '+v.amount+' $CAPES. '+mc.toLocaleString()+' Meme Coins are in your bank.','#0a0');modal('bank')}
 else if(a=='redeem'){const raw=($('rcc').value||'').trim().toUpperCase(),rr=$('rcr');if(!raw)return;let hx='';try{const d=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw));hx=[...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,'0')).join('')}catch(e){rr.textContent='This browser cannot check codes.';return}
  const g=(C.codes||{})[hx];if(!g){rr.innerHTML='<span style="color:#ff7a59">That code is not valid.</span>';return}if((st.rc||[]).includes(hx)){rr.textContent='You already redeemed that code.';return}
  const put=k=>{if(cap()>0)st.inv.push(k);else bankAdd(k,1)};
  if(g.coins){st.bank+=+g.coins;flow('+'+g.coins+' Meme Coins: code')}
  if(g.item&&IN[g.item])put(g.item);
  if(g.custom){const k='cx_'+hx.slice(0,10);(st.cust=st.cust||{})[k]=g.custom;regCust(k,g.custom);put(k)}
  (st.rc=st.rc||[]).push(hx);save();ui();say('Code redeemed'+(g.custom?': '+g.custom.name+' is yours.':'.'),'#0a0');modal('bank')}})}
"""
rep("function bankAdd(k,n){", DEP + "function bankAdd(k,n){")
rep("""<div style="font-size:10px;color:#ccc;margin-top:6px">Uses banked Meme Coins first. The rate gets steeper as the $CAPES pot empties, so it lasts longer.</div></div>';""",
    """<div style="font-size:10px;color:#ccc;margin-top:6px">Uses banked Meme Coins first. The rate gets steeper as the $CAPES pot empties, so it lasts longer. Demo values until $CAPES launches.</div></div>'+depHTML();""")
rep("if(t=='bank')bankWire();", "if(t=='bank'){bankWire();depWire()}")
# custom items are personal: never traded or sold on the market
rep("const NOTRADE=k=>k=='coin'||", "const NOTRADE=k=>k=='coin'||k.startsWith('cx_')||")

open(PATH, 'w', encoding='utf-8').write(h)
print('launch patch applied')
