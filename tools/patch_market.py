#!/usr/bin/env python3
"""The Stock Market (offers, like a grand exchange) and player-to-player trading.

Stock Market: six offer tickets. A buy offer locks the coins, a sell offer takes the items; offers fill over time
and what you are owed waits in the ticket until you collect it. Until the game servers exist, the other side of
every offer is the market itself (bots trading at the drifting guide price), and the same screens switch to
player offers when the server arrives (the NET hooks). The ticker tape and the sparklines show real guide-price
history (the last 24 moves of each item).

Trade screen: two players put items and coins in, both accept, both seal, then the swap happens. If either side
changes anything, both accepts reset and the changed side flashes. Until the servers exist there is a practice
partner (a bot) at the Stock Market broker, so the screen can be played today.
The look (CSS) lives in patch_theme.py. Run from the repo root after the other patches:  python3 tools/patch_market.py
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
const ICS=k=>'<svg viewBox="0 0 24 24" class="ic">'+IC[k]+'</svg>';
const fmt=n=>(+n).toLocaleString();
const ago=t=>{const s=(Date.now()-t)/1e3;return s<60?'just now':s<3600?Math.floor(s/60)+' min ago':s<86400?Math.floor(s/3600)+' h ago':Math.floor(s/86400)+' d ago'};
// guide-price history: the last 24 moves of each item feed the ticker tape and the sparklines
function gpH(e){(e.h=e.h||[]).push(+(e.f||e.p).toFixed(2));if(e.h.length>24)e.h.shift()}
// ---- the market: offers live in st.mk
function MKS(){if(!st.mk)st.mk={offers:[],hist:[],n:0};return st.mk}
const MKSLOTS=6;let mkTab='offers',mkNew=null;
function mkLimit(k,n){const lim=(st.gl=st.gl||{}),L=lim[k]&&Date.now()-lim[k].t<144e5?lim[k]:{n:0,t:Date.now()},mx=(ITM[k]&&ITM[k][4]>=1)?10:100;return{ok:L.n+n<=mx,left:mx-L.n,L,lim}}
function mkPlace(side,k,qty,price){const m=MKS();if(m.offers.length>=MKSLOTS)return say('All six tickets are in use. Collect or abort one first.','#c00');qty=Math.floor(qty);price=Math.floor(price);if(!(qty>0&&price>0))return;
 if(side=='buy'){const cost=qty*price;if(st.coins<cost)return say('You need '+fmt(cost)+' Meme Coins for that offer.','#c00');const L=mkLimit(k,qty);if(!L.ok)return say('Buy limit: you can buy '+L.left+' more '+IN[k]+' in the next 4 hours.','#c00');burn(cost,'market offer');L.L.n+=qty;L.lim[k]=L.L}
 else{const have=st.inv.filter(x=>x==k).length;if(have<qty)return say("You don't have that many.",'#c00');let left=qty;st.inv=st.inv.filter(x=>{if(x==k&&left>0){left--;return false}return true})}
 m.offers.push({id:++m.n,side,k,qty,price,filled:0,coins:0,items:0,t:Date.now()});if(window.NET&&NET.mkPlace)NET.mkPlace(m.offers[m.offers.length-1]);mkNew=null;ui();save();geOpen()}
function mkAbort(o){const m=MKS();if(o.side=='buy'){const back=(o.qty-o.filled)*o.price;if(back>0)pay(back,'offer cancelled')}else{o.items+=o.qty-o.filled}o.qty=o.filled;o.done=1;if(!o.items&&!o.coins)m.offers=m.offers.filter(x=>x!==o);ui();save();geOpen()}
function mkCollect(o){const m=MKS();if(o.coins>0){pay(o.coins,'market sale');o.coins=0}while(o.items>0){if(cap()>0)st.inv.push(o.k);else bankAdd(o.k,1);o.items--}if(o.done||o.filled>=o.qty)m.offers=m.offers.filter(x=>x!==o);ui();save();geOpen()}
// the other side of the book until the servers exist: the market fills offers near the guide price, a chunk at a time
function mkTick(){const m=MKS();if(!m.offers.length)return;let changed=0;for(const o of m.offers){if(o.done||o.filled>=o.qty)continue;const gp=gePrice(o.k),e=st.gp[o.k];
 if(o.side=='buy'&&o.price>=gp*.95){if(Math.random()<.45){const n=Math.min(o.qty-o.filled,1+Math.floor(Math.random()*Math.max(1,o.qty*.3)));o.filled+=n;o.items+=n;const pd=Math.max(0,o.price-gp)*n;if(pd>0)o.coins+=pd;gpH(e);e.f=Math.min(GV(o.k)*2,(e.f||e.p)*(1+.004*n));e.p=Math.max(1,Math.round(e.f));changed=1;m.hist.unshift({k:o.k,side:'buy',n,p:gp,t:Date.now()})}}
 else if(o.side=='sell'&&o.price<=gp*1.05){if(Math.random()<.45){const n=Math.min(o.qty-o.filled,1+Math.floor(Math.random()*Math.max(1,o.qty*.3)));o.filled+=n;o.coins+=Math.floor(o.price*n*.98);gpH(e);e.f=Math.max(.5,(e.f||e.p)*(1-.004*n));e.p=Math.max(1,Math.round(e.f));changed=1;m.hist.unshift({k:o.k,side:'sell',n,p:o.price,t:Date.now()})}}
 if(o.filled>=o.qty&&!o.told){o.told=1;say('Stock Market: your '+o.side+' offer for '+o.qty+' '+IN[o.k]+' has filled. Collect it at the broker.','#1a4fb0')}}
 if(m.hist.length>30)m.hist.length=30;if(changed){save();if(M.style.display=='flex'&&$('mkt')&&!mkNew){$('mkt').innerHTML=mkTickets();mkBind()}}}
setInterval(mkTick,2500);
// ---- the ticker tape: items that have moved, then the everyday goods
const TAPE=['logs','ore','fish','bar','bread','cake','bones','herbs','potion','plank','gold','rgem','runes','protein','jewel','potato','onion','cabbage'];
function mkTape(){const ks=[...new Set([...Object.keys(st.gp||{}),...TAPE])].filter(TRADEABLE).slice(0,24);if(!ks.length)return '';const sp=ks.map(k=>{const p=gePrice(k),e=st.gp[k],q=e.h&&e.h.length?e.h[0]:p,d=p>q?'up':p<q?'dn':'';return '<span>'+ICS(k)+IN[k]+' <b>'+fmt(p)+'</b><i class="'+d+'">'+(d=='up'?'&#9650;':d=='dn'?'&#9660;':'&#8226;')+'</i></span>'}).join('');return '<div class="mk-tape" aria-hidden="true"><div class="mk-track" style="--dur:'+Math.round(ks.length*3.2)+'s">'+sp+sp+'</div></div>'}
function spark(k){const e=st.gp[k]||{},pts=[...(e.h||[]),gePrice(k)];if(pts.length<2)return '<svg class="sp" viewBox="0 0 64 18"><line x1="1" y1="9" x2="63" y2="9" stroke="#8a6a3a" stroke-dasharray="2 3"/></svg>';const lo=Math.min(...pts),hi=Math.max(...pts),r=hi-lo||1,P=pts.map((v,i)=>[(i/(pts.length-1)*62+1).toFixed(1),(16-(v-lo)/r*14).toFixed(1)]),c=pts[pts.length-1]>pts[0]?'#39ff88':pts[pts.length-1]<pts[0]?'#ff7a59':'#ffd23f';return '<svg class="sp" viewBox="0 0 64 18"><polyline fill="none" stroke="'+c+'" stroke-width="1.5" stroke-linejoin="round" points="'+P.map(p=>p.join(',')).join(' ')+'"/><circle cx="'+P[P.length-1][0]+'" cy="'+P[P.length-1][1]+'" r="1.8" fill="'+c+'"/></svg>'}
// ---- offer tickets
function mkSlot(o){const pc=Math.round(100*o.filled/o.qty),full=o.filled>=o.qty,owed=o.items||o.coins;return '<div class="tk'+(owed?' ready':'')+'"><div class="tk-top"><div class="tk-ico">'+ICS(o.k)+'</div><div class="tk-name"><b>'+IN[o.k]+'</b><small>'+fmt(o.qty)+' at '+fmt(o.price)+' MC each'+(o.done?', aborted':'')+'</small></div><span class="stamp '+(o.done?'done':full?'done':o.side)+'">'+(o.done?'VOID':full?'FILLED':o.side.toUpperCase())+'</span></div><div class="tk-bar '+o.side+'"><i style="width:'+pc+'%"></i></div><div class="tk-foot"><span><b>'+fmt(o.filled)+'</b> of '+fmt(o.qty)+(o.side=='sell'?' sold':' bought')+(o.items?', <b>'+fmt(o.items)+'</b> waiting':'')+(o.coins?', <b>'+fmt(o.coins)+' MC</b> waiting':'')+'</span><span>'+(owed?'<button data-mkc="'+o.id+'">Collect</button>':'')+(!full&&!o.done?' <button class="ghost" data-mka="'+o.id+'">Abort</button>':'')+'</span></div></div>'}
function mkTickets(){const m=MKS();let h='';for(let i=0;i<MKSLOTS;i++){const o=m.offers[i];h+=o?mkSlot(o):'<div class="tk empty"><span>Empty ticket</span><span><button data-mkn="buy">Buy</button> <button data-mkn="sell">Sell</button></span></div>'}return h}
function mkNewHTML(){const N=mkNew;if(!N.k){if(N.side=='sell'){const have={};st.inv.forEach(k=>{if(TRADEABLE(k))have[k]=(have[k]||0)+1});const ks=Object.keys(have);return '<div class="mk-form"><h3>Sell: pick an item from your bag</h3>'+(ks.length?'<div class="mk-list">'+ks.map(k=>'<div class="row"><span>'+ICO(k)+IN[k]+' <small>you have '+have[k]+'</small></span><span><small>guide '+fmt(gePrice(k))+' MC</small> <button data-mkk="'+k+'">Pick</button></span></div>').join('')+'</div>':'<div class="mk-empty">Nothing tradeable in your bag. Capes, pets, lamps and clues stay with you.</div>')+'<div class="mk-foot"><button class="ghost" data-mkx="1">Back</button></div></div>'}
  const list=Object.keys(IN).filter(k=>TRADEABLE(k)&&(!geQ||IN[k].toLowerCase().includes(geQ))).slice(0,60);return '<div class="mk-form"><h3>Buy: what are you after?</h3><input id="geq" placeholder="Search items" value="'+geQ.replace(/[^a-z ]/g,'')+'"><div class="mk-list">'+(list.length?list.map(k=>'<div class="row"><span>'+ICO(k)+IN[k]+'</span><span><small>guide '+fmt(gePrice(k))+' MC</small> <button data-mkk="'+k+'">Pick</button></span></div>').join(''):'<div class="mk-empty">No item called that.</div>')+'</div><div class="mk-foot"><button class="ghost" data-mkx="1">Back</button></div></div>'}
 const buy=N.side=='buy',gp=gePrice(N.k),have=st.inv.filter(x=>x==N.k).length,total=N.qty*N.price,quick=buy?N.price>=gp*.95:N.price<=gp*1.05;
 return '<div class="mk-form"><h3>'+(buy?'Buy ':'Sell ')+IN[N.k]+'</h3><div class="row"><span>'+ICO(N.k)+IN[N.k]+'</span><small>guide price '+fmt(gp)+' MC'+(buy?'':', you have '+have)+'</small></div>'
 +'<div class="row"><span>Quantity <b>'+fmt(N.qty)+'</b></span><span class="qbtn"><button data-mkq="-1">&minus;1</button><button data-mkq="1">+1</button><button data-mkq="10">+10</button><button data-mkq="100">+100</button>'+(buy?'':'<button data-mkq="all">All '+have+'</button>')+'</span></div>'
 +'<div class="row"><span>Price each <b>'+fmt(N.price)+'</b></span><span class="qbtn"><button data-mkp="-5">&minus;5%</button><button data-mkp="0">Guide</button><button data-mkp="5">+5%</button><input id="mkpi" type="number" min="1" value="'+N.price+'" style="width:72px" aria-label="Custom price"></span></div>'
 +'<div class="mk-note" style="margin-top:6px">'+(quick?'Close to the going rate, so it should fill soon.':buy?'Below the going rate. It may sit until prices come down.':'Above the going rate. It may sit until prices climb.')+'</div>'
 +'<div class="mk-total"><span>'+(buy?'Locked in the ticket until it fills or you abort':'2% tax comes off each sale')+'</span><b>'+fmt(total)+' MC</b></div>'
 +'<div class="mk-foot"><button class="ghost" data-mkx="1">Back</button><button data-mkgo="1">Place '+(buy?'buy':'sell')+' offer</button></div></div>'}
function geOpen(){if(st.iron)return say('As an Ironman, you cannot use the Stock Market.');M.style.display='flex';MB.className='mk';const m=MKS();
 let h='<div id="mkroot"><div class="mk-head"><img class="mk-logo" src="'+BRAND.logo+'" alt=""><h2>Stock Market<br><small>Six tickets. What you are owed waits in its ticket until you collect it.</small></h2></div>'+mkTape()
 +'<div class="mk-tabs">'+[['offers','Offers'],['prices','Prices'],['hist','History']].map(([t,n])=>'<button data-mkt="'+t+'"'+(mkTab==t?' class="on"':'')+'>'+n+'</button>').join('')+'<span class="sp"></span><button class="pt" data-mkpt="1" title="Try the trade screen with a practice partner">Practice a trade</button></div>';
 if(mkTab=='offers'){h+=mkNew?mkNewHTML():'<div class="mk-tickets" id="mkt">'+mkTickets()+'</div>'}
 else if(mkTab=='prices'){const list=Object.keys(IN).filter(k=>TRADEABLE(k)&&(!geQ||IN[k].toLowerCase().includes(geQ))).slice(0,80);h+='<input id="geq" placeholder="Search items" value="'+geQ.replace(/[^a-z ]/g,'')+'"><div class="mk-note" style="margin:6px 0">Guide prices move with what gets bought and sold. The line is the last 24 moves.</div><div class="mk-list" style="max-height:300px">'+(list.length?list.map(k=>{const have=st.inv.filter(x=>x==k).length;return '<div class="pr">'+ICS(k)+'<span class="nm">'+IN[k]+(have?'<small>you have '+have+'</small>':'')+'</span>'+spark(k)+'<span class="p">'+fmt(gePrice(k))+' MC</span></div>'}).join(''):'<div class="mk-empty">No item called that.</div>')+'</div>'}
 else{h+='<div class="mk-list" style="max-height:320px">'+(m.hist.length?m.hist.map(x=>'<div class="hs">'+ICS(x.k)+'<span>'+(x.side=='buy'?'Bought ':'Sold ')+x.n+' '+IN[x.k]+' at '+fmt(x.p)+' MC each<small>'+ago(x.t)+'</small></span><span class="stamp '+x.side+'">'+x.side.toUpperCase()+'</span></div>').join(''):'<div class="mk-empty">No trades yet. Place a ticket and the floor will find you a match.</div>')+'</div>'}
 MB.innerHTML=h+'<div class="mk-foot"><button id="x">Close</button></div></div>';mkBind()}
function mkBind(){const m=MKS();const X=$('x');if(X)X.onclick=()=>M.style.display='none';
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
// ---- player-to-player trade: offer, accept, seal, swap
let T2=null;
function p2pOpen(partner){if(st.iron)return say('As an Ironman, you cannot trade.');T2={p:partner,stage:1,mine:{items:[],coins:0},theirs:{items:[],coins:0},acc:[0,0],t:Date.now(),chg:0};if(partner.bot)p2pBot('open');if(window.NET&&NET.tradeOpen&&!partner.bot)NET.tradeOpen(partner);p2pUI()}
function p2pVal(o){return o.items.reduce((a,k)=>a+gePrice(k),0)+o.coins}
// the other side changed their offer (the server calls this): both accepts reset and their vault flashes
function p2pTheirs(items,coins){const T=T2;if(!T||T.stage!=1)return;T.theirs={items:items.slice(),coins:coins|0};T.acc=[0,0];T.chg=Date.now();say(T.p.name+' changed the offer. Accepts reset: check it again.','#c00');p2pUI();setTimeout(()=>{if(T2===T)p2pUI()},4200)}
function p2pBot(ev){const T=T2;if(!T||!T.p.bot)return;if(ev=='open'){const pool=Object.keys(IN).filter(k=>TRADEABLE(k)&&GV(k)<=400);const n=1+Math.floor(Math.random()*3);T.theirs.items=[];for(let i=0;i<n;i++)T.theirs.items.push(pool[Math.floor(Math.random()*pool.length)]);T.theirs.coins=Math.floor(Math.random()*150);
  if(Math.random()<.35){const T0=T;setTimeout(()=>{if(T2!==T0||T0.stage!=1)return;p2pTheirs(T0.theirs.items.slice(0,Math.max(0,T0.theirs.items.length-1)),T0.theirs.coins+40)},6000+Math.random()*6000)}}
 if(ev=='accept'){const T0=T;setTimeout(()=>{if(T2!==T0)return;T0.acc[1]=1;if(T0.stage==1&&T0.acc[0]){p2pStage2()}else if(T0.stage==2&&T0.acc[0])p2pDone();else p2pUI()},1500+Math.random()*2000)}}
function p2pStage2(){const T=T2;T.stage=2;T.acc=[0,0];if(T.p.bot)p2pBot('accept');p2pUI()}
function p2pDone(){const T=T2;let free=cap()+T.mine.items.length;if(T.theirs.items.length>free)return p2pCancel('You do not have enough bag space for their items.');
 let rm=T.mine.items.slice();st.inv=st.inv.filter(k=>{const i=rm.indexOf(k);if(i>=0){rm.splice(i,1);return false}return true});if(T.mine.coins)burn(T.mine.coins,'trade with '+T.p.name);T.theirs.items.forEach(k=>st.inv.push(k));if(T.theirs.coins)pay(T.theirs.coins,'trade with '+T.p.name);
 say('Trade sealed with '+T.p.name+': you gave '+(T.mine.items.map(k=>IN[k]).join(', ')||'nothing')+(T.mine.coins?' + '+fmt(T.mine.coins)+' MC':'')+', you got '+(T.theirs.items.map(k=>IN[k]).join(', ')||'nothing')+(T.theirs.coins?' + '+fmt(T.theirs.coins)+' MC':'')+'.','#0a0');if(window.NET&&NET.tradeDone&&!T.p.bot)NET.tradeDone(T);T2=null;M.style.display='none';ui();save()}
function p2pCancel(why){say(why||'Trade declined.','#c00');if(window.NET&&NET.tradeCancel&&T2&&!T2.p.bot)NET.tradeCancel();T2=null;M.style.display='none'}
function p2pUI(){const T=T2;if(!T)return;M.style.display='flex';MB.className='tr';const nm=esc(T.p.name),fresh=T.chg&&Date.now()-T.chg<4000;
 const vault=(o,who,mine,cls)=>'<div class="vault'+(cls||'')+'"><h4><span>'+who+'</span>'+(fresh&&!mine?'<em>Offer changed</em>':'')+'</h4>'+(o.items.length?o.items.map((k,i)=>'<div class="it">'+ICS(k)+IN[k]+(mine&&T.stage==1?'<button class="ghost" data-tr="'+i+'" title="Take it back">remove</button>':'')+'</div>').join(''):'<div class="none">'+(mine&&T.stage==1?'Tap items in your bag to add them.':'Nothing yet.')+'</div>')+(o.coins?'<span class="coins">'+ICS('coin')+fmt(o.coins)+' MC</span>':'')+'<div class="val">Worth about '+fmt(p2pVal(o))+' MC at guide prices</div></div>';
 const vm=p2pVal(T.mine),vt=p2pVal(T.theirs),tot=vm+vt||1;
 const fair='<div class="tr-fair"><span>You give</span><div class="bar"><i class="a" style="width:'+Math.round(100*vm/tot)+'%"></i><i class="b" style="width:'+Math.round(100*vt/tot)+'%"></i></div><span>You get</span></div>'+(vm>vt*2+50?'<div class="tr-warn">You are giving about '+(vt?(Math.round(vm/vt*10)/10)+'x':'')+' more than you get. Make sure that is what you want.</div>':'');
 const seal='<div class="tr-mid"><div class="tr-seal '+(T.acc[0]&&T.acc[1]?'both':(T.acc[0]||T.acc[1])?'half':'')+'"><img src="'+BRAND.logo+'" alt=""></div></div>';
 const status='<div class="tr-status"><span class="dot'+(T.acc[1]?' on':'')+'"></span><span>'+(T.acc[1]?'<b>'+nm+' has accepted.</b>':nm+(T.stage==1?' is looking at the offer.':' is checking the final trade.'))+'</span><span class="dot'+(T.acc[0]?' on':'')+'"></span><span>'+(T.acc[0]?'<b>You have accepted.</b>':'Waiting for you.')+'</span></div>';
 let h='<div id="trroot"><div class="mk-head"><img class="mk-logo" src="'+BRAND.logo+'" alt=""><h2>'+(T.stage==1?'Trading with '+nm:'Seal the trade')+'<br><small>'+(T.stage==1?'Both of you accept, then both of you seal it. Nothing moves before that.':'Check both sides one more time. Nothing moves until you both press the seal.')+'</small></h2></div>';
 if(T.stage==1){const used={},seen={};T.mine.items.forEach(k=>used[k]=(used[k]||0)+1);
  h+='<div class="tr-vaults" style="margin-top:12px">'+vault(T.mine,'Your offer',1)+seal+vault(T.theirs,nm+"'s offer",0,fresh?' changed':'')+'</div>'+fair
  +'<div class="tr-coins"><button data-tc="100">+100 MC</button><button data-tc="1000">+1K MC</button><button data-tc="10000">+10K MC</button><button data-tc="all">All coins</button><button class="ghost" data-tc="0">Clear coins</button></div>'
  +'<div class="tr-bag"><div class="g">'+st.inv.map((k,i)=>{const no=!TRADEABLE(k)||(seen[k]=(seen[k]||0)+1)<=(used[k]||0);return '<div class="s'+(no?' no':'')+'" data-ta="'+i+'" title="'+IN[k]+'"><svg viewBox="0 0 24 24">'+IC[k]+'</svg></div>'}).join('')+'</div></div>'
  +status+'<div class="tr-acts"><button data-tacc="1"'+(T.acc[0]?' disabled':'')+'>'+(T.acc[0]?'Accepted':'Accept offer')+'</button><button class="ghost" data-tdec="1">Decline</button></div>'}
 else{h+='<div class="tr-conf"><div class="wax'+(T.acc[0]?' sealed':'')+'"><img src="'+BRAND.logo+'" alt=""></div><p>'+(T.acc[0]?'Your seal is on it.':'Your seal goes here.')+'</p></div><div class="tr-vaults">'+vault(T.mine,'You give',0)+seal+vault(T.theirs,'You get',0)+'</div>'+fair+status
  +'<div class="tr-acts"><button data-tacc="1"'+(T.acc[0]?' disabled':'')+'>'+(T.acc[0]?'Sealed':'Press your seal')+'</button><button class="ghost" data-tdec="1">Decline</button></div>'}
 MB.innerHTML=h+'</div>';
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


# the guide price keeps its history when it drifts on its own
rep("e.t+=6e5;e.p=Math.max(1,Math.round(Math.min(GV(k)*2,Math.max(GV(k)*.5,e.p*(1+(Math.random()-.5)*.06)))))}", "e.t+=6e5;gpH(e);e.f=Math.min(GV(k)*2,Math.max(GV(k)*.5,(e.f||e.p)*(1+(Math.random()-.5)*.06)));e.p=Math.max(1,Math.round(e.f))}")

open(PATH, 'w', encoding='utf-8').write(h)
print('market + trade patch applied')
