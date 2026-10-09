#!/usr/bin/env python3
"""The Stock Market (offers, like a grand exchange) and player-to-player trading.

Stock Market: six offer slots. A buy offer locks the coins, a sell offer takes the items; offers fill over time
and what you are owed waits in the slot until you collect it. Until the game servers exist, the other side of
every offer is the market itself (bots trading at the drifting guide price), and the same screens switch to
player offers when the server arrives (the NET hooks).

Trade screen: two players put items and coins in, both accept, both confirm, then the swap happens. Until the
servers exist there is a practice partner (a bot) at the Stock Market broker, so the screen can be played today.
Run from the repo root after the other patches:  python3 tools/patch_market.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()

i = h.find("let geQ='';function geOpen(){")
j = h.find("\n// --- Wandering Trader", i)
assert i > 0 and j > i, 'market anchors not found'

MARKET = r"""let geQ='';
// ---- what can be traded between players
const NOTRADE=k=>k=='coin'||k.startsWith('cape_')||k=='qcape'||k.startsWith('pet')||k=='clue'||k.startsWith('lamp');
const TRADEABLE=k=>!!IN[k]&&!NOTRADE(k);
const ICO=k=>'<svg viewBox="0 0 24 24" style="width:26px;height:26px;vertical-align:middle;margin-right:4px">'+IC[k]+'</svg>';
const fmt=n=>(+n).toLocaleString();
// ---- the market: offers live in st.mk
function MKS(){if(!st.mk)st.mk={offers:[],hist:[],n:0};return st.mk}
const MKSLOTS=6;let mkTab='offers',mkNew=null;
function mkLimit(k,n){const lim=(st.gl=st.gl||{}),L=lim[k]&&Date.now()-lim[k].t<144e5?lim[k]:{n:0,t:Date.now()},mx=(ITM[k]&&ITM[k][4]>=1)?10:100;return{ok:L.n+n<=mx,left:mx-L.n,L,lim}}
function mkPlace(side,k,qty,price){const m=MKS();if(m.offers.length>=MKSLOTS)return say('All six offer slots are in use. Collect or abort one first.','#c00');qty=Math.floor(qty);price=Math.floor(price);if(!(qty>0&&price>0))return;
 if(side=='buy'){const cost=qty*price;if(st.coins<cost)return say('You need '+fmt(cost)+' Meme Coins for that offer.','#c00');const L=mkLimit(k,qty);if(!L.ok)return say('Buy limit: you can buy '+L.left+' more '+IN[k]+' in the next 4 hours.','#c00');burn(cost,'market offer');L.L.n+=qty;L.lim[k]=L.L}
 else{const have=st.inv.filter(x=>x==k).length;if(have<qty)return say("You don't have that many.",'#c00');let left=qty;st.inv=st.inv.filter(x=>{if(x==k&&left>0){left--;return false}return true})}
 m.offers.push({id:++m.n,side,k,qty,price,filled:0,coins:0,items:0,t:Date.now()});if(window.NET&&NET.mkPlace)NET.mkPlace(m.offers[m.offers.length-1]);mkNew=null;ui();save();geOpen()}
function mkAbort(o){const m=MKS();if(o.side=='buy'){const back=(o.qty-o.filled)*o.price;if(back>0)pay(back,'offer cancelled')}else{o.items+=o.qty-o.filled}o.qty=o.filled;o.done=1;if(!o.items&&!o.coins)m.offers=m.offers.filter(x=>x!==o);ui();save();geOpen()}
function mkCollect(o){const m=MKS();if(o.coins>0){pay(o.coins,'market sale');o.coins=0}while(o.items>0){if(cap()>0)st.inv.push(o.k);else bankAdd(o.k,1);o.items--}if(o.done||o.filled>=o.qty)m.offers=m.offers.filter(x=>x!==o);ui();save();geOpen()}
// the other side of the book until the servers exist: the market fills offers near the guide price, a chunk at a time
function mkTick(){const m=MKS();if(!m.offers.length)return;let changed=0;for(const o of m.offers){if(o.done||o.filled>=o.qty)continue;const gp=gePrice(o.k),e=st.gp[o.k];
 if(o.side=='buy'&&o.price>=gp*.95){if(Math.random()<.45){const n=Math.min(o.qty-o.filled,1+Math.floor(Math.random()*Math.max(1,o.qty*.3)));o.filled+=n;o.items+=n;const pd=Math.max(0,o.price-gp)*n;if(pd>0)o.coins+=pd;e.p=Math.min(GV(o.k)*2,Math.round(e.p*(1+.004*n)));changed=1;m.hist.unshift({k:o.k,side:'buy',n,p:gp,t:Date.now()})}}
 else if(o.side=='sell'&&o.price<=gp*1.05){if(Math.random()<.45){const n=Math.min(o.qty-o.filled,1+Math.floor(Math.random()*Math.max(1,o.qty*.3)));o.filled+=n;o.coins+=Math.floor(o.price*n*.98);e.p=Math.max(1,Math.round(e.p*(1-.004*n)));changed=1;m.hist.unshift({k:o.k,side:'sell',n,p:o.price,t:Date.now()})}}
 if(o.filled>=o.qty&&!o.told){o.told=1;say('Stock Market: your '+o.side+' offer for '+o.qty+' '+IN[o.k]+' has filled. Collect it at the broker.','#1a4fb0')}}
 if(m.hist.length>30)m.hist.length=30;if(changed){save();if(M.style.display=='flex'&&MB.querySelector('#mkroot')&&!mkNew)geOpen()}}
setInterval(mkTick,2500);
function mkSlot(o){const pc=Math.round(100*o.filled/o.qty),col=o.side=='buy'?'#3a9ad9':'#d9a400';return '<div style="border:1px solid #7a6640;border-radius:4px;padding:6px;margin:4px 0;background:#0002"><div style="display:flex;justify-content:space-between;align-items:center"><span>'+ICO(o.k)+'<b>'+IN[o.k]+'</b></span><span style="color:'+col+';font-weight:bold">'+(o.side=='buy'?'BUY':'SELL')+'</span></div><div style="font-size:11px;color:#ccc">'+fmt(o.qty)+' at '+fmt(o.price)+' MC each'+(o.done?' - cancelled':'')+'</div><div style="height:8px;background:#222;border:1px solid #000;margin:4px 0"><div style="height:8px;width:'+pc+'%;background:'+(o.filled>=o.qty?'#2a9a2a':col)+'"></div></div><div style="display:flex;justify-content:space-between;align-items:center;font-size:11px"><span>'+fmt(o.filled)+' / '+fmt(o.qty)+(o.items?' | '+fmt(o.items)+' to collect':'')+(o.coins?' | '+fmt(o.coins)+' MC':'')+'</span><span>'+((o.items||o.coins)?'<button data-mkc="'+o.id+'">Collect</button> ':'')+(o.filled<o.qty&&!o.done?'<button data-mka="'+o.id+'">Abort</button>':'')+'</span></div></div>'}
function mkNewHTML(){const N=mkNew;if(!N.k){if(N.side=='sell'){const have={};st.inv.forEach(k=>{if(TRADEABLE(k))have[k]=(have[k]||0)+1});const ks=Object.keys(have);return '<h3 style="margin:6px 0">Sell: pick an item from your bag</h3>'+(ks.length?'<div style="max-height:220px;overflow:auto">'+ks.map(k=>'<div class="row"><span>'+ICO(k)+IN[k]+' <small>x'+have[k]+'</small></span><span><small>guide '+fmt(gePrice(k))+'</small> <button data-mkk="'+k+'">Pick</button></span></div>').join('')+'</div>':'<div style="color:#ccc;font-size:12px">Nothing tradeable in your bag.</div>')+'<br><button data-mkx="1">Back</button>'}
  const list=Object.keys(IN).filter(k=>TRADEABLE(k)&&(!geQ||IN[k].toLowerCase().includes(geQ))).slice(0,60);return '<h3 style="margin:6px 0">Buy: what are you after?</h3><input id="geq" placeholder="Search items" value="'+geQ.replace(/[^a-z ]/g,'')+'" style="width:100%;box-sizing:border-box;padding:6px;font:13px Georgia"><div style="max-height:220px;overflow:auto">'+list.map(k=>'<div class="row"><span>'+ICO(k)+IN[k]+'</span><span><small>guide '+fmt(gePrice(k))+'</small> <button data-mkk="'+k+'">Pick</button></span></div>').join('')+'</div><br><button data-mkx="1">Back</button>'}
 const gp=gePrice(N.k),have=st.inv.filter(x=>x==N.k).length,total=N.qty*N.price;return '<h3 style="margin:6px 0">'+(N.side=='buy'?'Buy':'Sell')+' '+IN[N.k]+'</h3><div class="row"><span>'+ICO(N.k)+IN[N.k]+'</span><span><small>guide price '+fmt(gp)+' MC</small></span></div><div class="row"><span>Quantity: <b>'+fmt(N.qty)+'</b></span><span><button data-mkq="-1">-</button> <button data-mkq="1">+1</button> <button data-mkq="10">+10</button> <button data-mkq="100">+100</button>'+(N.side=='sell'?' <button data-mkq="all">All ('+have+')</button>':'')+'</span></div><div class="row"><span>Price each: <b>'+fmt(N.price)+'</b></span><span><button data-mkp="-5">-5%</button> <button data-mkp="0">Guide</button> <button data-mkp="5">+5%</button></span></div><div class="row"><span>Custom price</span><input id="mkpi" type="number" min="1" value="'+N.price+'" style="width:90px;padding:4px;font:13px Georgia"></div><div style="margin:8px 0;font-size:12px">Total: <b>'+fmt(total)+' Meme Coins</b>'+(N.side=='sell'?' <small>(2% tax on each sale)</small>':' <small>(locked until the offer fills or you abort)</small>')+'</div><button data-mkgo="1" style="background:#d9a520;color:#000">Confirm '+(N.side=='buy'?'buy':'sell')+' offer</button> <button data-mkx="1">Back</button>'}
function geOpen(){if(st.iron)return say('As an Ironman, you cannot use the Stock Market.');M.style.display='flex';const m=MKS();let h='<div id="mkroot"><h2>Stock Market</h2><div style="display:flex;gap:4px;margin-bottom:6px">'+[['offers','Offers'],['prices','Prices'],['hist','History']].map(([t,n])=>'<button data-mkt="'+t+'"'+(mkTab==t?' style="background:#d9a520;color:#000"':'')+'>'+n+'</button>').join('')+'<span style="flex:1"></span><button data-mkpt="1" title="Try the trade screen">Practice trade</button></div>';
 if(mkTab=='offers'){if(mkNew)h+=mkNewHTML();else{h+='<div style="font-size:11px;color:#ccc;margin:4px 0">Six slots. Offers fill over time; collect what you are owed from the slot. Until the servers arrive the market itself takes the other side near the guide price.</div>';for(let i=0;i<MKSLOTS;i++){const o=m.offers[i];h+=o?mkSlot(o):'<div style="border:1px dashed #7a6640;border-radius:4px;padding:8px;margin:4px 0;display:flex;justify-content:space-between;align-items:center"><span style="color:#ccc;font-size:12px">Empty slot</span><span><button data-mkn="buy">Buy</button> <button data-mkn="sell">Sell</button></span></div>'}}}
 else if(mkTab=='prices'){const list=Object.keys(IN).filter(k=>TRADEABLE(k)&&(!geQ||IN[k].toLowerCase().includes(geQ))).slice(0,80);h+='<input id="geq" placeholder="Search items" value="'+geQ.replace(/[^a-z ]/g,'')+'" style="width:100%;box-sizing:border-box;padding:6px;font:13px Georgia"><div style="font-size:10px;color:#ccc;margin:4px 0">Guide prices drift with what gets bought and sold.</div><div style="max-height:260px;overflow:auto">'+list.map(k=>{const have=st.inv.filter(x=>x==k).length;return '<div class="row"><span>'+ICO(k)+IN[k]+(have?' <small>you have '+have+'</small>':'')+'</span><b>'+fmt(gePrice(k))+' MC</b></div>'}).join('')+'</div>'}
 else{h+='<div style="max-height:300px;overflow:auto">'+(m.hist.length?m.hist.map(x=>'<div class="row"><span>'+ICO(x.k)+(x.side=='buy'?'Bought ':'Sold ')+x.n+' '+IN[x.k]+'</span><small>'+fmt(x.p)+' MC each</small></div>').join(''):'<div style="color:#ccc;font-size:12px">No trades yet.</div>')+'</div>'}
 MB.innerHTML=h+'</div><br><button id="x">Close</button>';$('x').onclick=()=>M.style.display='none';
 MB.querySelectorAll('[data-mkt]').forEach(b=>b.onclick=()=>{mkTab=b.dataset.mkt;mkNew=null;geOpen()});
 MB.querySelectorAll('[data-mkn]').forEach(b=>b.onclick=()=>{mkNew={side:b.dataset.mkn,k:null,qty:1,price:1};geQ='';geOpen()});
 MB.querySelectorAll('[data-mkk]').forEach(b=>b.onclick=()=>{mkNew.k=b.dataset.mkk;mkNew.qty=1;mkNew.price=gePrice(mkNew.k);geOpen()});
 MB.querySelectorAll('[data-mkq]').forEach(b=>b.onclick=()=>{const v=b.dataset.mkq,have=st.inv.filter(x=>x==mkNew.k).length;if(v=='all')mkNew.qty=Math.max(1,have);else mkNew.qty=Math.max(1,mkNew.qty+ +v);if(mkNew.side=='sell')mkNew.qty=Math.min(mkNew.qty,Math.max(1,have));geOpen()});
 MB.querySelectorAll('[data-mkp]').forEach(b=>b.onclick=()=>{const g=gePrice(mkNew.k),v=+b.dataset.mkp;mkNew.price=v==0?g:Math.max(1,Math.round(mkNew.price*(1+v/100)));geOpen()});
 const pi=$('mkpi');if(pi)pi.onchange=()=>{mkNew.price=Math.max(1,Math.floor(+pi.value||1));geOpen()};
 MB.querySelectorAll('[data-mkgo]').forEach(b=>b.onclick=()=>mkPlace(mkNew.side,mkNew.k,mkNew.qty,mkNew.price));
 MB.querySelectorAll('[data-mkx]').forEach(b=>b.onclick=()=>{mkNew=null;geOpen()});
 MB.querySelectorAll('[data-mkc]').forEach(b=>b.onclick=()=>{const o=m.offers.find(x=>x.id==+b.dataset.mkc);if(o)mkCollect(o)});
 MB.querySelectorAll('[data-mka]').forEach(b=>b.onclick=()=>{const o=m.offers.find(x=>x.id==+b.dataset.mka);if(o)mkAbort(o)});
 MB.querySelectorAll('[data-mkpt]').forEach(b=>b.onclick=()=>p2pOpen({name:'Practice bot',bot:1}));
 const q=$('geq');if(q)q.oninput=()=>{geQ=q.value.toLowerCase();const sv=q.selectionStart;geOpen();const q2=$('geq');q2.focus();q2.setSelectionRange(sv,sv)}}
// ---- player-to-player trade: offer, accept, confirm, swap
let T2=null;
function p2pOpen(partner){if(st.iron)return say('As an Ironman, you cannot trade.');T2={p:partner,stage:1,mine:{items:[],coins:0},theirs:{items:[],coins:0},acc:[0,0],t:Date.now()};if(partner.bot)p2pBot('open');if(window.NET&&NET.tradeOpen&&!partner.bot)NET.tradeOpen(partner);p2pUI()}
function p2pVal(o){return o.items.reduce((a,k)=>a+gePrice(k),0)+o.coins}
function p2pBot(ev){const T=T2;if(!T||!T.p.bot)return;if(ev=='open'){const pool=Object.keys(IN).filter(k=>TRADEABLE(k)&&GV(k)<=400);const n=1+Math.floor(Math.random()*3);T.theirs.items=[];for(let i=0;i<n;i++)T.theirs.items.push(pool[Math.floor(Math.random()*pool.length)]);T.theirs.coins=Math.floor(Math.random()*150)}
 if(ev=='accept'){const T0=T;setTimeout(()=>{if(T2!==T0)return;T0.acc[1]=1;if(T0.stage==1&&T0.acc[0]){p2pStage2()}else if(T0.stage==2&&T0.acc[0])p2pDone();else p2pUI()},1500+Math.random()*2000)}}
function p2pStage2(){const T=T2;T.stage=2;T.acc=[0,0];if(T.p.bot)p2pBot('accept');p2pUI()}
function p2pDone(){const T=T2;const need=T.theirs.items.length+(T.theirs.coins&&!st.coins?0:0);let free=cap()+T.mine.items.length;if(T.theirs.items.length>free)return p2pCancel('You do not have enough bag space for their items.');
 let rm=T.mine.items.slice();st.inv=st.inv.filter(k=>{const i=rm.indexOf(k);if(i>=0){rm.splice(i,1);return false}return true});if(T.mine.coins)burn(T.mine.coins,'trade with '+T.p.name);T.theirs.items.forEach(k=>st.inv.push(k));if(T.theirs.coins)pay(T.theirs.coins,'trade with '+T.p.name);
 say('Trade complete with '+T.p.name+': you gave '+(T.mine.items.map(k=>IN[k]).join(', ')||'nothing')+(T.mine.coins?' + '+fmt(T.mine.coins)+' MC':'')+', you got '+(T.theirs.items.map(k=>IN[k]).join(', ')||'nothing')+(T.theirs.coins?' + '+fmt(T.theirs.coins)+' MC':'')+'.','#0a0');if(window.NET&&NET.tradeDone&&!T.p.bot)NET.tradeDone(T);T2=null;M.style.display='none';ui();save()}
function p2pCancel(why){say(why||'Trade declined.','#c00');if(window.NET&&NET.tradeCancel&&T2&&!T2.p.bot)NET.tradeCancel();T2=null;M.style.display='none'}
function p2pUI(){const T=T2;if(!T)return;M.style.display='flex';const side=(o,who,mineSide)=>'<div style="flex:1;min-width:0;border:1px solid #7a6640;border-radius:4px;padding:6px;background:#0002"><div style="font-weight:bold;margin-bottom:4px">'+who+'</div>'+(o.items.length?o.items.map((k,i)=>'<div class="row"><span>'+ICO(k)+IN[k]+'</span>'+(mineSide&&T.stage==1?'<button data-tr="'+i+'">x</button>':'')+'</div>').join(''):'<div style="color:#ccc;font-size:12px">No items</div>')+(o.coins?'<div class="row"><span>'+fmt(o.coins)+' Meme Coins</span></div>':'')+'<div style="font-size:11px;color:#ccc;margin-top:4px">Value about '+fmt(p2pVal(o))+' MC</div></div>';
 let h='<h2>Trading with: '+T.p.name+'</h2>';
 if(T.stage==1){h+='<div style="display:flex;gap:6px">'+side(T.mine,'Your offer',1)+side(T.theirs,T.p.name+"'s offer",0)+'</div><div style="margin:6px 0"><button data-tc="100">+100 MC</button> <button data-tc="1000">+1K MC</button> <button data-tc="10000">+10K MC</button> <button data-tc="all">All coins</button> <button data-tc="0">Clear coins</button></div><div style="font-size:11px;color:#ccc">Tap items in your bag to add them:</div><div class="g">'+st.inv.map((k,i)=>'<div class="s" data-ta="'+i+'"'+(TRADEABLE(k)?'':' style="opacity:.3"')+'><svg viewBox="0 0 24 24">'+IC[k]+'</svg></div>').join('')+'</div><div style="margin:8px 0;font-size:12px">'+(T.acc[1]?'<b style="color:#0a0">'+T.p.name+' has accepted.</b>':T.p.name+' is looking at the offer...')+(T.acc[0]?' <b>You have accepted.</b>':'')+'</div><button data-tacc="1" style="background:#d9a520;color:#000"'+(T.acc[0]?' disabled':'')+'>Accept</button> <button data-tdec="1">Decline</button>'}
 else{h+='<div style="font-size:12px;margin:4px 0;color:#ffd23f"><b>Confirm the trade.</b> Check both sides. Nothing moves until both of you accept this screen.</div><div style="display:flex;gap:6px">'+side(T.mine,'You give',0)+side(T.theirs,'You get',0)+'</div><div style="margin:8px 0;font-size:12px">'+(T.acc[1]?'<b style="color:#0a0">'+T.p.name+' has accepted.</b>':T.p.name+' is checking...')+(T.acc[0]?' <b>You have accepted.</b>':'')+'</div><button data-tacc="1" style="background:#d9a520;color:#000"'+(T.acc[0]?' disabled':'')+'>Accept</button> <button data-tdec="1">Decline</button>'}
 MB.innerHTML=h;
 MB.querySelectorAll('[data-ta]').forEach(d=>d.onclick=()=>{const i=+d.dataset.ta,k=st.inv[i];if(!TRADEABLE(k))return say('That cannot be traded.','#c00');const used=T.mine.items.filter(x=>x==k).length,have=st.inv.filter(x=>x==k).length;if(used>=have)return;T.mine.items.push(k);T.acc=[0,0];p2pUI()});
 MB.querySelectorAll('[data-tr]').forEach(b=>b.onclick=()=>{T.mine.items.splice(+b.dataset.tr,1);T.acc=[0,0];p2pUI()});
 MB.querySelectorAll('[data-tc]').forEach(b=>b.onclick=()=>{const v=b.dataset.tc;if(v=='all')T.mine.coins=st.coins;else if(v=='0')T.mine.coins=0;else T.mine.coins=Math.min(st.coins,T.mine.coins+ +v);T.acc=[0,0];p2pUI()});
 MB.querySelectorAll('[data-tacc]').forEach(b=>b.onclick=()=>{T.acc[0]=1;if(window.NET&&NET.tradeAccept&&!T.p.bot)NET.tradeAccept(T.stage);if(T.p.bot)p2pBot('accept');if(T.acc[1]){if(T.stage==1)p2pStage2();else p2pDone()}else p2pUI()});
 MB.querySelectorAll('[data-tdec]').forEach(b=>b.onclick=()=>p2pCancel('You decline the trade.'))}"""

h = h[:i] + MARKET + h[j:]


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# the broker's examine and the diary line stay; the bank card mention is fine
open(PATH, 'w', encoding='utf-8').write(h)
print('market + trade patch applied')
