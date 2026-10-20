#!/usr/bin/env python3
"""Link with snakepit: one account for the game and the Pit.

The $CAPEZ tab's snake card gets a "Link with snakepit" button for players with no wallet linked. It makes a one-time
code, tells the game server (pitLinkStart) and opens the Pit's /link page with that code in a new tab. There the
player signs in with email (the Pit creates a Solana wallet for anyone without one) or with Phantom, and the Pit
signs a short message with that wallet and posts it to the game server (/plink). The server links the wallet to the
game account and tells the game at once. The window opens on the click itself, so phones don't block it.
The snake pet and the card now use the linked wallet first. Run after patch_snakepit.py.
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# the linked wallet (verified by signature) comes first; the typed payout wallet is the fallback
rep("function pitWallet(){const w=st.acct&&st.acct.wallet?String(st.acct.wallet).replace(/[^1-9A-HJ-NP-Za-km-z]/g,''):'';return w.length>=32&&w.length<=44?w:''}",
    "function pitWallet(){const L=NETS.holder&&NETS.holder.wallet,w=String(L||(st.acct&&st.acct.wallet)||'').replace(/[^1-9A-HJ-NP-Za-km-z]/g,'');return w.length>=32&&w.length<=44?w:''}\n"
    "function pitLink(){const r=$('plr');if(!SRV()||!NETS.on){if(r)r.textContent='Log in online first (start screen), then link.';return}"
    "const a=new Uint8Array(12);crypto.getRandomValues(a);const code=[...a].map(x=>x.toString(16).padStart(2,'0')).join('');"
    "netSend({t:'pitLinkStart',code});const u=PITC()+'/link?code='+code+'&srv='+encodeURIComponent(SRVH());"
    "const wn=window.open(u,'_blank','noopener');if(r)r.innerHTML=wn===null?'Your browser blocked the new tab. <a href=\"'+u+'\" target=\"_blank\" rel=\"noopener\" style=\"color:#58f0a6\">Open snakepit</a> to finish.':'Finish in the snakepit tab: sign in with your email (a wallet is made for you) and tap Link. This tab updates by itself.'}window.pitLink=pitLink;")
rep("""if(!w)s+='<div style="color:#7c8590;margin-top:4px">Link your wallet at any bank and your snake from the Pit follows you here. Same wallet, same snake.</div>';""",
    """if(!w)s+='<div style="color:#7c8590;margin-top:4px">One account for the game and the Pit: sign in to snakepit with your email (it makes you a wallet) and your snake follows you here.</div><button onclick="pitLink()" style="margin:6px 0 2px;background:#58f0a6;color:#0b0c0e;border:0;border-radius:6px;padding:6px 10px;font-weight:800;cursor:pointer">Link with snakepit</button><div id="plr" style="font-size:11px;color:#c8d0d6;margin-top:3px"></div>';""")
# when the server says the wallet is linked, the snake and the tab refresh at once
rep("if(k!==NETS.hk){NETS.hk=k;hpkRefresh()}}",
    "if(k!==NETS.hk){NETS.hk=k;hpkRefresh();try{pitRefresh(true);if(pOpen)renderPanel()}catch(e){}}}")
open(PATH, 'w', encoding='utf-8').write(h)
print('patch_pitlink: link with snakepit')
