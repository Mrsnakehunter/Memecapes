#!/usr/bin/env python3
"""Withdrawals in the game (the rules live on the server: server/withdraw.js).

At any bank, "Withdraw to your wallet" replaces the old demo exchange: turn banked Meme Coins into real $CAPES, paid to
the wallet linked under Holder perks from the public pot wallet 30 days after asking. The coins leave the bank at once
(the server takes them from the saved bank), the request can be cancelled until the wait is over (coins back), and
the list shows each request with its date, Ready, Paid (with the transaction) or Refused. Needs online play.
Run from the repo root after patch_pitlink.py:  python3 tools/patch_withdraw.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""
// ---- withdrawals (tools/patch_withdraw.py; the rules live on the server)
const wdDay=t=>new Date(t).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'});
const wdE=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function wdHTML(){const W=NETS.wd;let h='<div id="wdx" style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Withdraw to your wallet</b>'+(W&&W.open?' <span style="background:#2bd96b;color:#062;font-size:10px;font-weight:800;padding:1px 7px;border-radius:9px;vertical-align:2px">LIVE</span>':'')+'<br>';
 if(!SRV()||!NETS.on)return h+'<span style="font-size:12px;color:#ccc">Needs online play: log in from the start screen.</span></div>';
 if(!W)return h+'<span style="font-size:12px;color:#ccc">Loading...</span></div>';
 h+='<span style="font-size:12px">Turn banked Meme Coins into real $CAPES: <b>'+W.rate+' Meme Coins = 1 $CAPES</b>. Paid to your linked wallet from the public pot wallet <b>'+W.days+' days</b> after you ask; you can cancel until then and get your coins back. Up to '+W.dayMax+' $CAPES a day.</span><br>';
 if(!W.open)h+='<span style="font-size:12px;color:#ffb35c">'+wdE(W.why)+'</span><br>';
 else if(!W.wallet)h+='<span style="font-size:12px;color:#ffb35c">Link your wallet under Holder perks below first: withdrawals are paid to that wallet.</span><br>';
 else{h+='<span style="font-size:12px">To wallet <b>'+W.wallet.slice(0,4)+'...'+W.wallet.slice(-4)+'</b> · today you can still take <b>'+W.dayLeft+'</b>'+(W.room!=null?' · the pot can cover <b>'+W.room+'</b> more':'')+'</span><br>';
  h+='<input id="wdn" type="number" min="1" step="1" max="'+Math.max(1,Math.min(W.dayLeft,W.room==null?W.dayLeft:W.room))+'" placeholder="$CAPES" style="width:90px;margin:6px 4px 0 0"> <button data-wd="go">Withdraw</button><div id="wdc" style="font-size:12px;color:#ccc;margin-top:3px"></div>'}
 if(W.list&&W.list.length){h+='<div style="margin-top:8px;font-size:12px">';W.list.forEach(r=>{let s;
   if(r.status=='waiting')s='arrives after '+wdDay(r.due)+' <button class="ghost" data-wc="'+r.id+'" style="font-size:11px;padding:1px 8px">Cancel</button>';
   else if(r.status=='ready')s='<span style="color:#7dff9a">ready: in the payout queue</span>';
   else if(r.status=='paid')s='<span style="color:#7dff9a">paid</span>'+(r.sig?' <a href="https://solscan.io/tx/'+wdE(r.sig)+'" target="_blank" rel="noopener" style="color:#ffd23f">transaction</a>':'');
   else if(r.status=='held')s='<span style="color:#ffb35c">under review</span>'+(r.note?': '+wdE(r.note):'')+' <button class="ghost" data-wc="'+r.id+'" style="font-size:11px;padding:1px 8px">Cancel</button>';
   else if(r.status=='refused')s='<span style="color:#ff7a59">refused, coins returned</span>'+(r.note?': '+wdE(r.note):'');
   else s='<span style="color:#ccc">cancelled, coins returned</span>';
   h+='<div style="padding:3px 0;border-top:1px solid #fff2">#'+r.id+' · <b>'+r.capes+' $CAPES</b> ('+r.coins.toLocaleString()+' Meme Coins) · '+s+'</div>'});h+='</div>'}
 return h+'</div>'}
function wdWire(){if(NETS.on&&SRV()&&(!NETS.wdT||Date.now()-NETS.wdT>20000)){NETS.wdT=Date.now();netSend({t:'wdInfo'})}
 const n=$('wdn'),c=$('wdc'),W=NETS.wd;if(n&&c&&W)n.oninput=()=>{const v=Math.floor(+n.value||0);c.textContent=v>0?'Costs '+(v*W.rate).toLocaleString()+' Meme Coins from your bank (you have '+Math.floor(st.bank).toLocaleString()+').':''};
 MB.querySelectorAll('[data-wd]').forEach(b=>b.onclick=()=>{const v=Math.floor(+($('wdn')||{}).value||0);if(!(v>0))return say('Type how many $CAPES to withdraw.','#c00');
  if(W&&v*W.rate>st.bank)return say('You need '+(v*W.rate).toLocaleString()+' Meme Coins in your bank for '+v+' $CAPES.','#c00');
  netSaveNow();b.disabled=true;b.textContent='...';setTimeout(()=>netSend({t:'withdraw',capes:v}),400)});
 MB.querySelectorAll('[data-wc]').forEach(b=>b.onclick=()=>{netSaveNow();b.disabled=true;setTimeout(()=>netSend({t:'withdrawCancel',id:+b.dataset.wc}),400)})}
function wdRefresh(){if(M.style.display!='none'&&$('wdx'))modal('bank')}
"""
rep("function depWire(){", JS + "function depWire(){wdWire();")
# the old demo exchange goes; the live withdraw box takes its place
rep("""'<div style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Exchange for $CAPES</b><br>Rate: '+exRate()+' Meme Coins = 1 $CAPES<br>Your $CAPES: '+st.scape.toLocaleString()+'<br>Today: '+(EXCAP-exLeft())+' / '+EXCAP+' $CAPES<br><br><button data-x="1">Get 1</button> <button data-x="10">Get 10</button> <button data-x="max">Get max</button><div style="font-size:10px;color:#ccc;margin-top:6px">Uses banked Meme Coins first. The rate gets steeper as the $CAPES pot empties, so it lasts longer. Demo values for now: real $CAPES payouts open once the public pot wallet is funded.</div></div>'+depHTML();""",
    "wdHTML()+depHTML();")
rep(""" h+='</div><div style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Withdraw Meme Coins as $CAPES</b><br><span style="color:#ccc;font-size:12px">'+(C.withdrawalsOpen?'Withdrawals open with the game servers.':'Opens with the game servers, when your Meme Coins are kept safe on our server instead of in this browser.')+'</span></div>';""",
    " h+='</div>';")
# the server's messages: the request list, and the bank change it made
rep(" saved(m){NETS.rev=m.rev;LS.set('mc_rev',String(m.rev))},",
    " saved(m){NETS.rev=m.rev;LS.set('mc_rev',String(m.rev))},"
    "wd(m){NETS.wd=m;NETS.wdT=Date.now();const k=JSON.stringify(m);if(k!==NETS.wdk){NETS.wdk=k;wdRefresh()}},"
    "wdBank(m){st.bank=Math.max(0,Math.floor(st.bank)+(+m.delta||0));NETS.rev=m.rev;LS.set('mc_rev',String(m.rev));flow((m.delta>0?'+':'')+m.delta+' Meme Coins: withdrawal'+(m.delta>0?' returned':''));save();ui()},")

open(PATH, 'w', encoding='utf-8').write(h)
print('withdraw patch applied')
