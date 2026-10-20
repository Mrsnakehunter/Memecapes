#!/usr/bin/env python3
"""Player-to-player trade window, version 2.

Built from how the best trade windows work (two confirmation screens, a value scale, a red mark where an item was
taken out, warnings before you accept something that changed) plus our own extras:
  - Every item is shown as its real painted picture, big, with its name, how many, and what it is worth.
  - Your own bag sits inside the trade window: tap to offer one, right-click or long-press to offer 5, 10, all or
    any amount, or to look at it. Items already in your offer are ticked, items that can't be traded are locked.
  - The inspector: point at or tap any item (yours or theirs) to see it up close: big picture, rarity, what it does
    (attack, strength, defence, healing, slot), its description, its guide price and how many you already have.
  - Anti-scam: items they add glow NEW; items they take out stay on screen as a red "!" until the trade ends; a coin
    drop is called out; Accept is locked for 3 seconds after they change anything (the server enforces it too, and
    an accept only counts for the exact version of the offer you saw); their items you have not looked at carry a
    gold dot, and Accept asks once if you skip them; Accept is blocked if their items won't fit in your bag.
  - Final check screen: a receipt of both sides with exact coin amounts in words, what was removed earlier, your free
    bag slots after the trade and the value difference; the seal button waits 1.5 seconds so a double tap can't
    skip it.
  - A "Trade complete" receipt, and a trade history (your last 30 trades).
Run from the repo root after patch_net.py (and the later patches):  python3 tools/patch_trade.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


TRADE = r"""// ---- player-to-player trade, version 2 (tools/patch_trade.py)
let T2=null,TRS=null,TRlp=0;
const TRRN=['Common','Uncommon','Rare','Epic','Legendary'],TRLOCK=3000;
const trRar=k=>ITM[k]?Math.max(0,Math.min(4,ITM[k][4]||0)):({'#5c5':1,'#4a9aff':2,'#c77dff':3,'#ff9a2a':4})[RAR[k]]||0;
const trCnt=a=>{const o={};a.forEach(k=>o[k]=(o[k]||0)+1);return o};
const trGroup=a=>{const m=new Map();a.forEach(k=>m.set(k,(m.get(k)||0)+1));return[...m.entries()]};
const trVal=o=>o.items.reduce((a,k)=>a+gePrice(k),0)+(o.coins|0);
const trShort=n=>n>=1e7?Math.floor(n/1e6)+'M':n>=1e5?Math.floor(n/1e3)+'K':fmt(n);
const trWords=n=>n>=1e9?(Math.round(n/1e7)/100)+' billion':n>=1e6?(Math.round(n/1e4)/100)+' million':n>=1e4?(Math.round(n/10)/100)+' thousand':'';
const trSv=k=>'<svg viewBox="0 0 24 24">'+(k=='coin'?COINI(1e6):IC[k])+'</svg>';
const TRLK='<svg class="trlk" viewBox="0 0 24 24"><path d="M7.5 11V8a4.5 4.5 0 0 1 9 0v3" fill="none" stroke="#ffd23f" stroke-width="2.6"/><rect x="5" y="11" width="14" height="10" rx="2" fill="#ffd23f"/></svg>';
function trInfo(k){const L=[];let ty='Item';
 if(HEAL[k]){ty='Food';L.push('Heals '+HEAL[k])}
 if(SLOT[k])ty=(SLN[SLOT[k]]||'Gear')+' gear';
 if(WST[k]){ty='Weapon';L.push('Attack +'+WST[k][0],'Strength +'+WST[k][1])}else if(WB[k])L.push('Hit +'+WB[k]);
 if(AB[k])L.push('Defence +'+AB[k]);
 if(/^tab_/.test(k))ty='Teleport';else if(/^s(pot|onion|cab|tom)$/.test(k))ty='Seed';
 return{ty,L}}
// how many free bag slots you will have after the trade (negative = their items won't fit)
function trSpace(T){const coins=st.coins-T.mine.coins+T.theirs.coins;return 35-(coins>0?1:0)-(st.inv.length-T.mine.items.length+T.theirs.items.length)}
const trUnseen=T=>trGroup(T.theirs.items).map(e=>e[0]).filter(k=>!T.seen[k]);
function p2pOpen(partner){if(st.iron)return say('In Diamond Hands mode you cannot trade.');if(typeof netOfferLast!='undefined')netOfferLast='';TRS=null;
 T2={p:partner,stage:1,mine:{items:[],coins:0},theirs:{items:[],coins:0},acc:[0,0],ver:0,pend:0,t:Date.now(),chg:0,lock:0,gone:{},fresh:{},coinDrop:0,seen:{},sel:null,warnU:0,menu:null,flash:0};
 if(partner.bot)p2pBot('open');p2pUI()}
// the other side changed their offer (the server calls this with the new version number)
function p2pTheirs(items,coins,ver){const T=T2;if(!T||T.stage!=1)return;const a=trCnt(T.theirs.items),b=trCnt(items),now=Date.now(),had=T.theirs.items.length||T.theirs.coins;coins=coins|0;
 for(const k in a){const d=a[k]-(b[k]||0);if(d>0)T.gone[k]=(T.gone[k]||0)+d}
 for(const k in b){const d=b[k]-(a[k]||0);if(d>0){T.fresh[k]=now;delete T.seen[k];if(T.gone[k]){T.gone[k]-=d;if(T.gone[k]<=0)delete T.gone[k]}}}
 if(coins<T.theirs.coins)T.coinDrop+=T.theirs.coins-coins;else if(coins>T.theirs.coins){T.coinDrop=Math.max(0,T.coinDrop-(coins-T.theirs.coins));T.fresh.coin=now}
 const wasAcc=T.acc[0]||T.acc[1];T.theirs={items:items.slice(),coins};if(ver!=null)T.ver=ver|0;T.acc=[0,0];T.chg=now;T.lock=now+TRLOCK;T.warnU=0;T.flash=now;
 if(had||wasAcc)say(T.p.name+' changed their offer'+(wasAcc?'. Both accepts were reset':'')+'. Check it again.','#c00');p2pUI()}
function p2pBot(ev){const T=T2;if(!T||!T.p.bot)return;
 if(ev=='open'){const pool=Object.keys(IN).filter(k=>TRADEABLE(k)&&GV(k)<=400&&IC[k]);const n=2+Math.floor(Math.random()*3),it=[];for(let i=0;i<n;i++)it.push(pool[Math.floor(Math.random()*pool.length)]);if(Math.random()<.5)it.push(it[0]);
  const T0=T;setTimeout(()=>{if(T2===T0)p2pTheirs(it,Math.floor(Math.random()*150)*10)},900);
  if(Math.random()<.6)setTimeout(()=>{if(T2!==T0||T0.stage!=1)return;p2pTheirs(T0.theirs.items.slice(0,Math.max(0,T0.theirs.items.length-1)),Math.max(0,T0.theirs.coins-200))},7000+Math.random()*6000)}
 if(ev=='accept'){const T0=T,s=T.stage;setTimeout(()=>{if(T2!==T0||T0.stage!=s)return;T0.acc[1]=1;if(T0.acc[0]){if(s==1)p2pStage2();else p2pFinish(T0.mine,T0.theirs,1)}else p2pUI()},1500+Math.random()*2000)}}
function p2pStage2(){const T=T2;if(!T)return;T.stage=2;T.acc=[0,0];T.lock=Date.now()+1500;T.menu=null;T.warnU=0;if(T.p.bot)p2pBot('accept');p2pUI()}
// your own offer changed
function trMine(){const T=T2;T.acc=[0,0];T.warnU=0;T.menu=null;p2pUI()}
function trAdd(k,n){const T=T2;if(!T||T.stage!=1)return;if(!TRADEABLE(k))return say('That cannot be traded.','#c00');const have=st.inv.filter(x=>x==k).length,used=T.mine.items.filter(x=>x==k).length;n=Math.min(n,have-used);if(n<=0)return;for(let i=0;i<n;i++)T.mine.items.push(k);trMine()}
function trTake(k,n){const T=T2;if(!T||T.stage!=1)return;for(let i=T.mine.items.length-1;i>=0&&n>0;i--)if(T.mine.items[i]==k){T.mine.items.splice(i,1);n--}trMine()}
function trCoins(v){const T=T2;if(!T||T.stage!=1)return;T.mine.coins=Math.max(0,Math.min(st.coins,Math.floor(v)||0));trMine()}
const trParse=s=>{const m=String(s).trim().toLowerCase().replace(/,/g,'').match(/^(\d+(?:\.\d+)?)\s*([kmb]?)$/);if(!m)return null;return Math.floor(+m[1]*({'':1,k:1e3,m:1e6,b:1e9})[m[2]])};
function trAccept(){const T=T2;if(!T||T.acc[0]||T.pend||Date.now()<T.lock)return;if(trSpace(T)<0)return p2pUI();
 if(T.stage==1&&trUnseen(T).length&&!T.warnU){T.warnU=1;return p2pUI()}
 T.acc[0]=1;T.warnU=0;if(T.p.net&&window.NET&&NET.tradeAccept)NET.tradeAccept(T.stage);if(T.p.bot)p2pBot('accept');
 if(!T.p.net&&T.acc[1]){if(T.stage==1)p2pStage2();else p2pFinish(T.mine,T.theirs,1);return}p2pUI()}
// the trade went through: local = do the swap here (practice partner); online the server already did it
function p2pFinish(gave,got,local){const T=T2;if(!T)return;
 if(local){if(trSpace(T)<0)return p2pCancel('You do not have enough bag space for their items.');let rm=gave.items.slice();st.inv=st.inv.filter(k=>{const i=rm.indexOf(k);if(i>=0){rm.splice(i,1);return false}return true});if(gave.coins)burn(gave.coins,'trade with '+T.p.name);got.items.forEach(k=>st.inv.push(k));if(got.coins)pay(got.coins,'trade with '+T.p.name)}
 const rec={t:Date.now(),p:T.p.name,gave:{items:gave.items.slice(),coins:gave.coins|0},got:{items:got.items.slice(),coins:got.coins|0}};if(!Array.isArray(st.tlog))st.tlog=[];st.tlog.unshift(rec);st.tlog.length=Math.min(st.tlog.length,30);
 say('Trade complete with '+T.p.name+': you gave '+(trList(gave)||'nothing')+', you got '+(trList(got)||'nothing')+'.','#0a0');
 T2=null;TRS={m:'done',r:rec};p2pUI();ui();save()}
const trList=o=>trGroup(o.items).map(([k,n])=>IN[k]+(n>1?' x'+n:'')).concat(o.coins?[fmt(o.coins)+' MC']:[]).join(', ');
function p2pCancel(why,them){const T=T2;say(why||'Trade declined.','#c00');if(window.NET&&NET.tradeCancel&&T&&!T.p.bot&&!them)NET.tradeCancel();T2=null;if(them&&T){TRS={m:'cancel',why:why||'The trade was cancelled.',p:T.p.name};p2pUI()}else{TRS=null;M.style.display='none'}}
// ---- drawing
function trTile(T,k,n,side){const now=Date.now(),fr=side=='t'&&T.fresh[k]&&now-T.fresh[k]<9000,un=side=='t'&&T.stage==1&&!T.seen[k],sel=T.sel&&T.sel.k==k&&T.sel.s==side;
 return '<div class="trt'+(fr?' isnew':'')+(un?' isuns':'')+(sel?' issel':'')+'" data-tk="'+k+'" data-ts="'+side+'" data-tn="'+n+'" style="--rc:'+RC[trRar(k)]+'" title="'+IN[k]+'"><div class="trpic">'+trSv(k)+(n>1?'<b class="trn">x'+n+'</b>':'')+(fr?'<i class="trtag">NEW</i>':'')+(un?'<i class="treye"></i>':'')+'</div><span class="trnm">'+IN[k]+'</span><span class="trv">'+trShort(gePrice(k)*n)+' MC</span></div>'}
function trCoinTile(T,o,side){const fr=side=='t'&&T.fresh.coin&&Date.now()-T.fresh.coin<9000;return '<div class="trt iscoin'+(fr?' isnew':'')+'" data-tk="coin" data-ts="'+side+'" data-tn="'+o.coins+'" style="--rc:#ffd23f"><div class="trpic"><svg viewBox="0 0 24 24">'+COINI(o.coins)+'</svg>'+(fr?'<i class="trtag">NEW</i>':'')+'</div><span class="trnm">'+trShort(o.coins)+'</span><span class="trv">Meme Coins</span></div>'}
function trPanel(T,side){const o=side=='m'?T.mine:T.theirs,nm=esc(T.p.name),g=trGroup(o.items);let t='';
 if(o.coins)t+=trCoinTile(T,o,side);t+=g.map(([k,n])=>trTile(T,k,n,side)).join('');
 if(side=='t'){for(const k in T.gone)t+='<div class="trt isgone" data-tk="'+k+'" data-ts="g" data-tn="'+T.gone[k]+'" title="Taken out of the offer"><div class="trpic">'+trSv(k)+'<i class="trbang">!</i></div><span class="trnm">'+IN[k]+'</span><span class="trv">Taken out'+(T.gone[k]>1?' x'+T.gone[k]:'')+'</span></div>';if(T.coinDrop)t+='<div class="trt isgone" data-tk="coin" data-ts="g" data-tn="'+T.coinDrop+'"><div class="trpic"><svg viewBox="0 0 24 24">'+COINI(T.coinDrop)+'</svg><i class="trbang">!</i></div><span class="trnm">'+trShort(T.coinDrop)+' MC</span><span class="trv">Taken out</span></div>'}
 const empty=!o.items.length&&!o.coins,cnt=o.items.length;
 return '<section class="trp is'+side+(side=='t'&&T.flash&&Date.now()-T.flash<2500?' ischg':'')+'"><header><h4>'+(side=='m'?'You give':nm+' gives')+'</h4><span>'+(cnt?cnt+' item'+(cnt>1?'s':''):'')+(cnt&&o.coins?' + coins':o.coins?'coins':'')+'</span></header>'
  +'<div class="trg">'+t+'</div>'+(empty?'<div class="tre">'+(side=='m'?'Nothing yet. Tap items in your bag to offer them.':nm+' has not offered anything yet.')+'</div>':'')
  +(side=='m'&&T.stage==1?'<div class="trc"><label>Coins <input id="trci" inputmode="decimal" autocomplete="off" placeholder="0" value="'+(T.mine.coins||'')+'"></label><button data-tc="1000">+1K</button><button data-tc="10000">+10K</button><button data-tc="100000">+100K</button><button data-tc="1000000">+1M</button><button data-tc="all">All</button>'+(T.mine.coins?'<button class="ghost" data-tc="0">Clear</button>':'')+'<small>You have '+fmt(st.coins)+' MC. Type an amount like 25k or 1.5m.</small></div>':'')
  +'<footer>Worth about <b>'+fmt(trVal(o))+' MC</b></footer></section>'}
function trBag(T){const used=trCnt(T.mine.items),seen={};let s='',n=0;
 if(st.coins>0){n++;const left=st.coins-T.mine.coins;s+='<div class="trs iscoin'+(left<=0?' isin':'')+'" data-bc="1" title="Meme Coins: type an amount under your offer"><svg viewBox="0 0 24 24">'+COINI(Math.max(1,left))+'</svg><small>'+trShort(Math.max(0,left))+'</small></div>'}
 st.inv.forEach((k,i)=>{n++;seen[k]=(seen[k]||0)+1;const inO=seen[k]<=(used[k]||0),no=!TRADEABLE(k);s+='<div class="trs'+(no?' isno':'')+(inO?' isin':'')+'" data-bi="'+i+'" data-tk="'+k+'" data-ts="b" style="--rc:'+RC[trRar(k)]+'" title="'+IN[k]+(no?' (cannot be traded)':'')+'">'+trSv(k)+(no?TRLK:'')+'</div>'});
 for(;n<35;n++)s+='<div class="trs isempty"></div>';
 return '<section class="trp trbag"><header><h4>Your bag</h4><span>'+(35-(st.coins>0?1:0)-st.inv.length)+' free</span></header><div class="trgrid">'+s+'</div><div class="tre issmall">Tap to offer one. Right-click or hold for more.</div></section>'}
function trInsp(T){const s=T&&T.sel;if(!s)return '';
 const k=s.k,n=s.n||1;
 if(k=='coin')return '<div class="tri" style="--rc:#ffd23f"><div class="trbig"><svg viewBox="0 0 24 24">'+COINI(n)+'</svg></div><div class="trtxt"><h5>'+fmt(n)+' Meme Coins</h5><div class="trty">Currency'+(trWords(n)?' · '+trWords(n):'')+'</div><p>'+(s.s=='g'?'Taken out of '+esc(T.p.name)+"'s offer.":'Meme Coins. Trade them, spend them, swap them for $CAPES at any bank.')+'</p></div></div>';
 const r=trRar(k),inf=trInfo(k),have=st.inv.filter(x=>x==k).length;
 return '<div class="tri" style="--rc:'+RC[r]+'"><div class="trbig"><svg viewBox="0 0 24 24">'+IC[k]+'</svg></div><div class="trtxt"><h5>'+IN[k]+(n>1?' <span>x'+n+'</span>':'')+'</h5><div class="trty">'+TRRN[r]+' · '+inf.ty+'</div>'
  +(inf.L.length?'<div class="trst">'+inf.L.map(x=>'<span>'+x+'</span>').join('')+'</div>':'')+'<p>'+(EX[k]||'')+'</p>'
  +'<div class="trpr">Guide price <b>'+fmt(gePrice(k))+' MC</b> each'+(n>1?' · '+n+' = <b>'+fmt(gePrice(k)*n)+' MC</b>':'')+'</div>'
  +'<div class="trown">'+(s.s=='g'?'<b class="trbad">Taken out of '+esc(T.p.name)+"'s offer</b> · ":s.s=='t'?'In '+esc(T.p.name)+"'s offer · ":s.s=='m'?'In your offer · ':'')+(have?'You have '+have+' in your bag':'You have none')+(TRADEABLE(k)?'':' · <b class="trbad">Cannot be traded</b>')+'</div></div></div>'}
function trWarn(T){const W=[],nm=esc(T.p.name),vm=trVal(T.mine),vt=trVal(T.theirs),sp=trSpace(T),gone=Object.keys(T.gone);
 if(gone.length||T.coinDrop)W.push(['trwbad',nm+' took things out of their offer: '+gone.map(k=>IN[k]+(T.gone[k]>1?' x'+T.gone[k]:'')).concat(T.coinDrop?[fmt(T.coinDrop)+' MC']:[]).join(', ')+' (marked with a red !). Check what is left before you accept.']);
 if(sp<0)W.push(['trwbad','Their items will not fit: you need '+(-sp)+' more free bag slot'+(sp<-1?'s':'')+'.']);
 if(vm>0&&!T.theirs.items.length&&!T.theirs.coins)W.push(['trwwarn','You get nothing back. This would be a gift.']);
 else if(vt>0&&vm>vt*2&&vm-vt>200)W.push(['trwwarn','You are giving about '+(Math.round(vm/vt*10)/10)+' times more than you get, at guide prices.']);
 if(T.warnU){const u=trUnseen(T);if(u.length)W.push(['trwinfo','You have not looked at '+u.map(k=>IN[k]).join(', ')+' yet (gold dot). Tap '+(u.length>1?'them':'it')+' to check, or press Accept again.'])}
 return W.length?'<div class="trw">'+W.map(w=>'<div class="'+w[0]+'">'+w[1]+'</div>').join('')+'</div>':''}
function trScale(T){const vm=trVal(T.mine),vt=trVal(T.theirs),tot=vm+vt||1,d=vt-vm;
 return '<div class="trb"><div class="trside"><small>You give</small><b>'+fmt(vm)+' MC</b></div><div class="trbar"><i class="tra" style="width:'+(100*vm/tot)+'%"></i><i class="trbb" style="width:'+(100*vt/tot)+'%"></i></div><div class="trside isr"><small>You get</small><b>'+fmt(vt)+' MC</b></div></div>'
  +(vm||vt?'<div class="trnet '+(d>=0?'trup':'trdn')+'">'+(d>=0?'+':'−')+fmt(Math.abs(d))+' MC for you at guide prices</div>':'')}
function trAccLabel(T){const now=Date.now(),s=Math.ceil((T.lock-now)/1000);if(T.acc[0])return[1,T.stage==1?'Accepted':'Sealed'];if(T.pend)return[1,'Sending...'];if(trSpace(T)<0)return[1,'No bag space'];
 const base=T.stage==1?(T.warnU?'Accept anyway':'Accept offer'):'Press your seal';return now<T.lock?[1,base+' ('+s+')']:[0,base]}
function trStatus(T){const nm=esc(T.p.name);return '<div class="tr-status"><span class="dot'+(T.acc[1]?' on':'')+'"></span><span>'+(T.acc[1]?'<b>'+nm+(T.stage==1?' has accepted.':' has pressed their seal.')+'</b>':nm+(T.stage==1?' is choosing.':' is checking the final trade.'))+'</span><span class="dot'+(T.acc[0]?' on':'')+'"></span><span>'+(T.acc[0]?'<b>You have '+(T.stage==1?'accepted.':'pressed your seal.')+'</b>':'Waiting for you.')+'</span></div>'}
function trHead(title,sub,stage){return '<div class="mk-head"><img class="mk-logo" src="'+BRAND.logo+'" alt=""><h2>'+title+'<br><small>'+sub+'</small></h2>'+(Array.isArray(st.tlog)&&st.tlog.length&&!(TRS&&TRS.m=='hist')?'<button class="ghost" data-trh="1">History</button>':'')+'</div>'
 +(stage?'<ol class="trstep"><li class="'+(stage==1?'on':'ok')+'">1 · Offer</li><li class="'+(stage==2?'on':stage>2?'ok':'')+'">2 · Final check</li><li class="'+(stage>2?'on':'')+'">3 · Done</li></ol>':'')}
function trRows(o,side,gone){const g=trGroup(o.items);let s=(o.coins?'<div class="trr iscoin" data-tk="coin" data-ts="'+side+'" data-tn="'+o.coins+'" style="--rc:#ffd23f"><svg viewBox="0 0 24 24">'+COINI(o.coins)+'</svg><span class="trnm">'+fmt(o.coins)+' Meme Coins'+(trWords(o.coins)?'<small>'+trWords(o.coins)+'</small>':'')+'</span><span class="trn"></span><span class="trv">'+fmt(o.coins)+' MC</span></div>':'')
  +g.map(([k,n])=>'<div class="trr" data-tk="'+k+'" data-ts="'+side+'" data-tn="'+n+'" style="--rc:'+RC[trRar(k)]+'">'+trSv(k)+'<span class="trnm">'+IN[k]+'<small>'+TRRN[trRar(k)]+' · '+trInfo(k).ty+'</small></span><span class="trn">x'+n+'</span><span class="trv">'+fmt(gePrice(k)*n)+' MC</span></div>').join('');
 if(gone)for(const k in gone)s+='<div class="trr isgone" data-tk="'+k+'" data-ts="g" data-tn="'+gone[k]+'">'+trSv(k)+'<span class="trnm">'+IN[k]+'<small>Taken out earlier</small></span><span class="trn">x'+gone[k]+'</span><span class="trv">removed</span></div>';
 return s||'<div class="tre">Nothing</div>'}
function p2pUI(){const T=T2;M.style.display='flex';MB.className='tr';const ae=document.activeElement,foc=ae&&ae.id=='trci',cs=foc?ae.selectionStart:0;
 if(!T)return trScreen();if(typeof netTradeSync=='function')netTradeSync(T);
 const nm=esc(T.p.name),lv=T.p.net&&typeof NETS!='undefined'?[...NETS.info.values()].find(i=>i.name===T.p.name):null,acc=trAccLabel(T);
 let x='<div id="trroot">';
 if(T.stage==1){x+=trHead('Trading with '+nm+(lv&&lv.lv?' <span class="trlv">level '+lv.lv+'</span>':''),T.p.bot?'Practice partner. The swap is real, so only offer things you do not need.':'Pick what you give. Both of you accept, then both of you check the final trade and press your seal. Nothing moves before that.',1);
  x+='<div class="tr-main">'+trBag(T)+trPanel(T,'m')+trPanel(T,'t')+'</div>'+trScale(T)}
 else{const sp=trSpace(T),d=trVal(T.theirs)-trVal(T.mine);x+=trHead('Final check','Read both lists. Nothing moves until both of you press your seal.',2);
  x+='<div class="trx"><section><h4>You give</h4>'+trRows(T.mine,'m')+'<footer>Worth about <b>'+fmt(trVal(T.mine))+' MC</b></footer></section><section class="ist"><h4>You get from '+nm+'</h4>'+trRows(T.theirs,'t',T.gone)+'<footer>Worth about <b>'+fmt(trVal(T.theirs))+' MC</b></footer></section></div>'
  +'<div class="trsum"><span>After the trade you will have <b>'+Math.max(0,sp)+'</b> free bag slot'+(sp==1?'':'s')+'.</span><span class="'+(d>=0?'trup':'trdn')+'">'+(d>=0?'You come out about +':'You come out about −')+fmt(Math.abs(d))+' MC at guide prices.</span></div>'
  +'<div class="tr-conf"><div class="wax'+(T.acc[0]?' sealed':'')+'"><img src="'+BRAND.logo+'" alt=""></div></div>'}
 x+='<div class="tr-foot">'+trWarn(T)+trStatus(T)+'<button id="tracc" data-tacc="1"'+(acc[0]?' disabled':'')+'>'+acc[1]+'</button><button class="ghost" data-tdec="1">Decline</button></div>';
 if(T.menu)x+=trMenuH(T);
 MB.innerHTML=x+'</div>';trWire(T);
 if(foc){const q=$('trci');if(q){q.focus();try{q.setSelectionRange(cs,cs)}catch(e){}}}}
function trScreen(){const S=TRS;if(!S){M.style.display='none';return}let x='<div id="trroot">';
 if(S.m=='done'){const r=S.r;x+=trHead('Trade complete','With '+esc(r.p)+' · '+new Date(r.t).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}),3)+'<div class="tr-conf"><div class="wax sealed"><img src="'+BRAND.logo+'" alt=""></div><p>Sealed. The items are in your bag.</p></div><div class="trx"><section class="ist"><h4>You got</h4>'+trRows(r.got,'x')+'</section><section><h4>You gave</h4>'+trRows(r.gave,'x')+'</section></div>'}
 else if(S.m=='cancel')x+=trHead('Trade cancelled',esc(S.p||''),0)+'<div class="trw"><div class="trwwarn">'+esc(S.why)+'</div></div><p class="tre">'+(/connection dropped/.test(S.why)?'':'Nothing was swapped. Your items are still in your bag.')+'</p>';
 else if(S.m=='hist'){const L=Array.isArray(st.tlog)?st.tlog:[];x+=trHead('Trade history','Your last '+L.length+' trade'+(L.length==1?'':'s')+', newest first.',0)+'<div class="trh">'+(L.map(r=>'<div class="trhr"><div class="trwhen"><b>'+esc(r.p)+'</b><small>'+new Date(r.t).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+'</small></div><div class="trcol"><small>You gave</small>'+trMini(r.gave)+'</div><div class="trcol"><small>You got</small>'+trMini(r.got)+'</div></div>').join('')||'<p class="tre">No trades yet.</p>')+'</div>'}
 x+='<div class="tr-foot"><span style="flex:1"></span>'+(S.m=='hist'&&S.back?'<button data-trb="1">Back</button>':'<button data-trx="1">Close</button>')+'</div></div>';MB.innerHTML=x;
 MB.querySelectorAll('[data-trx]').forEach(b=>b.onclick=()=>{TRS=null;M.style.display='none'});MB.querySelectorAll('[data-trb]').forEach(b=>b.onclick=()=>{TRS=S.back;p2pUI()});MB.querySelectorAll('[data-trh]').forEach(b=>b.onclick=()=>{TRS={m:'hist',back:S};p2pUI()})}
const trMini=o=>'<div class="trmini">'+(o.coins?'<span title="'+fmt(o.coins)+' MC"><svg viewBox="0 0 24 24">'+COINI(o.coins)+'</svg>'+trShort(o.coins)+'</span>':'')+trGroup(o.items).map(([k,n])=>'<span title="'+IN[k]+'">'+trSv(k)+(n>1?'x'+n:'')+'</span>').join('')+(!o.coins&&!o.items.length?'<em>nothing</em>':'')+'</div>';
function trMenuH(T){const m=T.menu,k=m.k,nm=IN[k]||'';let b='';
 if(m.s=='b'){const left=st.inv.filter(x=>x==k).length-T.mine.items.filter(x=>x==k).length;if(TRADEABLE(k)&&left>0){b+='<button data-tm="a1">Offer 1</button>';if(left>1)b+='<button data-tm="a5">Offer 5</button><button data-tm="a10">Offer 10</button><button data-tm="aall">Offer all ('+left+')</button><button data-tm="ax">Offer X...</button>'}}
 if(m.s=='m'){const c=T.mine.items.filter(x=>x==k).length;b+='<button data-tm="t1">Take back 1</button>';if(c>1)b+='<button data-tm="t5">Take back 5</button><button data-tm="tall">Take back all ('+c+')</button>'}
 b+='<button data-tm="look">Look at it</button><button data-tm="close">Cancel</button>';
 return '<div class="trmenu" style="left:'+m.x+'px;top:'+m.y+'px"><div class="trhd">'+nm+'</div>'+(m.ask?'<form data-tmf="1"><input id="trmx" inputmode="numeric" placeholder="How many?" autocomplete="off"><button>OK</button></form>':b)+'</div>'}
function trPop(T,el,pin){const k=el.dataset.tk,s=el.dataset.ts||'b',n=+el.dataset.tn||1,root=$('trroot');if(!k||!root)return;T.sel={k,s,n};if(pin)T.pin=1;
 if(s=='t'&&T.stage==1&&!T.seen[k]){T.seen[k]=1;MB.querySelectorAll('.trt[data-ts="t"][data-tk="'+k+'"]').forEach(e=>{e.classList.remove('isuns');const y=e.querySelector('.treye');if(y)y.remove()})}
 MB.querySelectorAll('.issel').forEach(e=>e.classList.remove('issel'));el.classList.add('issel');
 let p=$('trpop');if(!p){p=document.createElement('div');p.id='trpop';root.appendChild(p)}p.innerHTML=trInsp(T)+(T.pin?'<button class="ghost trpx" data-trpx="1">Close</button>':'');p.style.display='block';
 const R=root.getBoundingClientRect(),E=el.getBoundingClientRect(),w=Math.min(330,R.width-12);p.style.width=w+'px';
 let x=E.right-R.left+8,y=E.top-R.top-6;if(x+w>R.width-4){x=E.left-R.left-w-8;if(x<4){x=Math.max(4,Math.min(R.width-w-4,E.left-R.left+E.width/2-w/2));y=E.bottom-R.top+6}}
 p.style.left=x+'px';p.style.top=Math.max(4,Math.min(y,R.height-p.offsetHeight-4))+'px';const c=p.querySelector('[data-trpx]');if(c)c.onclick=e=>{e.stopPropagation();trUnpop(T,1)}}
function trUnpop(T,force){if(T&&T.pin&&!force)return;if(T){T.pin=0;T.sel=null}const p=$('trpop');if(p)p.style.display='none';MB.querySelectorAll('.issel').forEach(e=>e.classList.remove('issel'))}
function trMenuAt(T,ev,k,s,i){const R=$('trroot').getBoundingClientRect(),x=Math.max(4,Math.min(R.width-170,(ev.clientX||0)-R.left)),y=Math.max(4,(ev.clientY||0)-R.top);T.menu={k,s,i,x,y};p2pUI()}
function trHold(el,fn){let t=0;el.addEventListener('pointerdown',e=>{if(e.pointerType=='mouse')return;t=setTimeout(()=>{TRlp=Date.now();fn(e)},450)});['pointerup','pointerleave','pointercancel','pointermove'].forEach(v=>el.addEventListener(v,e=>{if(v=='pointermove'&&Math.abs(e.movementX||0)+Math.abs(e.movementY||0)<6)return;clearTimeout(t)}))}
function trWire(T){const Q=s=>MB.querySelectorAll(s);
 Q('[data-bi]').forEach(d=>{const k=st.inv[+d.dataset.bi];d.onclick=()=>{if(Date.now()-TRlp<600)return;trAdd(k,1)};d.oncontextmenu=e=>{e.preventDefault();trMenuAt(T,e,k,'b')};trHold(d,e=>trMenuAt(T,e,k,'b'));
  d.onmouseenter=()=>trPop(T,d);d.onmouseleave=()=>trUnpop(T)});
 Q('[data-bc]').forEach(d=>d.onclick=()=>{const q=$('trci');if(q){q.focus();q.select()}});
 Q('.trt,.trr').forEach(d=>{const s=d.dataset.ts,k=d.dataset.tk;d.onmouseenter=()=>trPop(T,d);d.onmouseleave=()=>trUnpop(T);
  d.onclick=e=>{e.stopPropagation();if(Date.now()-TRlp<600)return;if(s=='m'&&T.stage==1&&k!='coin'){T.pin=0;return trTake(k,1)}if(s=='m'&&k=='coin'&&T.stage==1){const q=$('trci');if(q){q.focus();q.select()}return}trPop(T,d,1)};
  if(s=='m'&&T.stage==1&&k!='coin'){d.oncontextmenu=e=>{e.preventDefault();trMenuAt(T,e,k,'m')};trHold(d,e=>trMenuAt(T,e,k,'m'))}});
 const q=$('trci');if(q){q.oninput=()=>{const v=q.value.trim()?trParse(q.value):0;q.classList.toggle('bad',v==null||v>st.coins);if(v!=null&&v!=T.mine.coins&&v<=st.coins)trCoins(v)};q.onkeydown=e=>{e.stopPropagation();if(e.key=='Enter')q.blur()}}
 Q('[data-tc]').forEach(b=>b.onclick=()=>{const v=b.dataset.tc;trCoins(v=='all'?st.coins:v=='0'?0:T.mine.coins+ +v)});
 Q('[data-tacc]').forEach(b=>b.onclick=trAccept);Q('[data-tdec]').forEach(b=>b.onclick=()=>p2pCancel('You declined the trade.'));
 Q('[data-trh]').forEach(b=>b.onclick=trHist);
 Q('[data-tm]').forEach(b=>b.onclick=e=>{e.stopPropagation();const m=T.menu,a=b.dataset.tm,c=a.slice(1);if(!m)return;
  if(a=='close'){T.menu=null;return p2pUI()}if(a=='look'){T.menu=null;T.sel={k:m.k,s:m.s,n:1};T.pin=1;return p2pUI()}if(a=='ax'){m.ask=1;p2pUI();const i=$('trmx');if(i)i.focus();return}
  T.menu=null;const n=c=='all'?99:+c;if(a[0]=='a')trAdd(m.k,n);else trTake(m.k,n)});
 Q('[data-tmf]').forEach(f=>f.onsubmit=e=>{e.preventDefault();const m=T.menu,v=trParse($('trmx').value);T.menu=null;if(m&&v)trAdd(m.k,v);else p2pUI()});
 const mx=$('trmx');if(mx)mx.onkeydown=e=>{e.stopPropagation();if(e.key=='Escape'){T.menu=null;p2pUI()}};
 const root=$('trroot');if(root)root.addEventListener('click',e=>{if(Date.now()-TRlp<600)return;if(T.menu&&!e.target.closest('.trmenu')){T.menu=null;return p2pUI()}if(T.pin&&!e.target.closest('#trpop,.trt,.trr,.trs'))trUnpop(T,1)});
 if(T.pin&&T.sel){const el=MB.querySelector('[data-tk="'+T.sel.k+'"][data-ts="'+T.sel.s+'"]');if(el)trPop(T,el,1);else T.pin=0}}
// trade history opened from inside a live trade comes back to the trade
function trHist(){const T=T2;const S={m:'hist',back:null};if(T){const keepT=T;let x;TRS=S;T2=null;trScreen();T2=keepT;TRS=null;MB.querySelectorAll('[data-trx]').forEach(b=>{b.textContent='Back to the trade';b.onclick=()=>p2pUI()})}else{TRS=S;trScreen()}}
// keep the Accept countdown and the NEW glows fresh without redrawing the whole window
setInterval(()=>{const T=T2;if(!T||M.style.display=='none')return;const b=$('tracc');if(!b)return;const a=trAccLabel(T);if(b.textContent!=a[1]){b.textContent=a[1];b.disabled=!!a[0]}
 const now=Date.now();MB.querySelectorAll('.trt.isnew').forEach(e=>{const k=e.dataset.tk;if(!T.fresh[k]||now-T.fresh[k]>9000){e.classList.remove('isnew');const t=e.querySelector('.trtag');if(t)t.remove()}})},250);
"""

a = h.index('// ---- player-to-player trade: offer, accept, seal, swap')
end_anchor = "MB.querySelectorAll('[data-tdec]').forEach(b=>b.onclick=()=>p2pCancel('You decline the trade.'))}"
b = h.index(end_anchor) + len(end_anchor)
assert h.count('// ---- player-to-player trade: offer, accept, seal, swap') == 1 and h.count(end_anchor) == 1
h = h[:a] + TRADE + h[b:]

# online play: version numbers, pending sends, the server's receipt, cancels from the other side
rep("tradeTheirs(m){p2pTheirs(m.items,m.coins)},",
    "tradeTheirs(m){p2pTheirs(m.items,m.coins,m.ver)},\n tradeVer(m){if(!T2)return;T2.pend=0;T2.ver=m.ver|0;if(m.bad&&Array.isArray(m.items)){T2.mine={items:m.items.slice(),coins:m.coins|0};netOfferLast=JSON.stringify(T2.mine)}p2pUI()},\n tradeNoAcc(m){if(!T2)return;T2.acc[0]=0;T2.lock=Math.max(T2.lock,Date.now()+1200);say(esc(m.why||'Check the trade again.'),'#c00');p2pUI()},")
rep("tradeDone(m){NETS.inTrade=0;if(T2){T2.mine=m.gave;T2.theirs=m.got;try{p2pDone()}catch(e){}}T2=null;M.style.display='none';st.inv=m.inv;st.coins=m.coins;NETS.rev=m.rev;LS.set('mc_rev',String(m.rev));ui();save()},",
    "tradeDone(m){NETS.inTrade=0;st.inv=m.inv;st.coins=m.coins;NETS.rev=m.rev;LS.set('mc_rev',String(m.rev));if(T2)p2pFinish(m.gave,m.got,0);else{ui();save()}},")
rep("tradeCancel(m){NETS.inTrade=0;if(T2){say(esc(m.why||'Trade cancelled.'),'#c00');T2=null;M.style.display='none'}}",
    "tradeCancel(m){NETS.inTrade=0;if(T2)p2pCancel(m.why||'Trade cancelled.',1)}")
rep("tradeAccept:s=>{if(NETS.on&&NETS.inTrade)netSend({t:'tradeAccept',stage:s})}",
    "tradeAccept:s=>{if(NETS.on&&NETS.inTrade)netSend({t:'tradeAccept',stage:s,ver:T2?T2.ver:0})}")
rep("netOfferLast=s;netSend({t:'tradeOffer',items:T.mine.items,coins:T.mine.coins})",
    "netOfferLast=s;T.pend=1;netSend({t:'tradeOffer',items:T.mine.items,coins:T.mine.coins})")

# a trade request pops up as a card (Trade / No thanks, 60 seconds), not just a chat line
rep("""Accept trade</a>','#a60');netSaveNow()},""", """Accept trade</a>','#a60');netSaveNow();trReq(m.from)},""")
rep("function p2pOpen(partner){", """function trReq(from){if(T2)return;let d=$('trq');if(!d){d=document.createElement('div');d.id='trq';document.body.appendChild(d)}const inf=typeof NETS!='undefined'?[...NETS.info.values()].find(i=>i.name===from):null;
 d.innerHTML='<img src="'+BRAND.logo+'" alt=""><div class="trqt"><b>'+esc(from)+'</b>'+(inf&&inf.lv?' <small>level '+inf.lv+'</small>':'')+'<span>wants to trade with you</span></div><button data-q="y">Trade</button><button class="trqn" data-q="n">No thanks</button><i></i>';
 d.style.display='flex';d.classList.remove('go');void d.offsetWidth;d.classList.add('go');clearTimeout(trReq.t);trReq.t=setTimeout(()=>{d.style.display='none'},60000);
 d.onclick=e=>{const q=e.target.dataset.q;if(!q)return;d.style.display='none';if(q=='y'&&typeof netSend=='function'){netSaveNow();netSend({t:'tradeYes',name:from})}}}
function p2pOpen(partner){{const q=$('trq');if(q)q.style.display='none'}""")
# other players' name tags open the player menu (Trade, Ignore, Report) when tapped
rep("d=document.createElement('div');d.className='ntag';document.body.appendChild(d);NTAG.set(o.id,d)}", "d=document.createElement('div');d.className='ntag pn';document.body.appendChild(d);NTAG.set(o.id,d)}if(d.dataset.pn!==inf.name)d.dataset.pn=inf.name;")

# losing the connection ends an online trade on screen too (the server has already called it off)
rep("onclose=()=>{if(NETS.ws!==ws)return;const was=NETS.on;NETS.on=false;", "onclose=()=>{if(NETS.ws!==ws)return;const was=NETS.on;NETS.on=false;if(T2&&T2.p.net){NETS.inTrade=0;p2pCancel('The connection dropped, so the trade window closed. If both seals were already pressed, your bag updates when you reconnect; otherwise nothing was swapped.',1)}")

CSS = r"""
/* ---- trade window v2 (tools/patch_trade.py) */
#modal #mb.tr{max-width:1080px;max-height:92vh}
#trroot{position:relative}
#trroot .mk-head .ghost{margin-left:auto}
#trroot .trlv{font:700 11px Alegreya,Georgia,serif;color:#d9b98a;-webkit-text-fill-color:#d9b98a;margin-left:6px}
.trstep{display:flex;gap:6px;list-style:none;margin:10px 0 0;padding:0;font:700 10px Cinzel,Georgia,serif;flex-wrap:wrap}
.trstep li{padding:3px 9px;border:1px solid #d9a52055;border-radius:10px;color:#8a6a3a}
.trstep li.on{color:#2a1400;background:linear-gradient(#ffe88a,#f2b400);border-color:#6b4a06}
.trstep li.ok{color:#39ff88;border-color:#39ff8866}
.tr-main{display:grid;grid-template-columns:236px 1fr 1fr;gap:10px;margin-top:10px;align-items:start}
@media (max-width:860px){.tr-main{grid-template-columns:1fr 1fr}.trbag{grid-column:1/-1;order:3}}
@media (max-width:440px){.tr-main{grid-template-columns:1fr}#modal #mb.tr{max-height:96vh;padding:10px}}
.trp{border:1px solid #d9a52066;border-radius:6px;background:linear-gradient(#2b0810,#1f0509);display:flex;flex-direction:column;min-width:0;min-height:240px}
.trp header{display:flex;justify-content:space-between;align-items:baseline;gap:6px;padding:7px 10px;border-bottom:1px solid #d9a52033}
.trp h4{margin:0;font:700 13px Cinzel,Georgia,serif;color:#ffd23f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.trp header span{font-size:11px;color:#d9b98a;white-space:nowrap}
.trp.ist{box-shadow:inset 0 0 0 1px #39ff8818}
.trp.ischg{animation:tr-flash 1s ease-out 2}
.trp footer{margin-top:auto;padding:7px 10px;border-top:1px solid #d9a52033;font-size:12px;color:#d9b98a}.trp footer b{color:#f6eedc}
.trg{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:6px;padding:8px}
.trt{position:relative;background:#16030a;border:1px solid #d9a52033;border-bottom:2px solid var(--rc,#bbb);border-radius:6px;padding:6px 3px 4px;text-align:center;cursor:pointer;transition:transform .12s,border-color .12s,box-shadow .12s;min-width:0;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
.trt:hover{border-color:#ffd23f;transform:translateY(-1px)}
.trt.issel{border-color:#ffd23f;box-shadow:0 0 0 1px #ffd23f,0 0 14px #ffd23f55}
.trt .trpic{position:relative;width:54px;height:54px;margin:0 auto 3px;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle,#ffffff12 0%,transparent 68%)}
.trt .trpic>svg{width:50px;height:50px;filter:drop-shadow(0 2px 2px #000)}
.trt .trn{position:absolute;right:-8px;bottom:-3px;background:#000d;color:#ffd23f;font:700 11px Cinzel,Georgia,serif;padding:1px 5px;border-radius:8px;border:1px solid #d9a52099}
.trt .trnm{display:block;font-size:11px;line-height:1.15;color:#f6eedc;height:2.3em;overflow:hidden}
.trt .trv{display:block;font-size:10px;color:#d9b98a;white-space:nowrap}
.trt.iscoin .trnm{color:#ffd23f;font:700 12px Cinzel,Georgia,serif;height:auto}
.trt.isnew{border-color:#39ff88;box-shadow:0 0 0 1px #39ff88,0 0 16px #39ff8866;animation:tr-glow 1.2s ease-in-out 3}
.trt .trtag{position:absolute;left:-10px;top:-6px;background:#39ff88;color:#04210f;font:900 9px Cinzel,Georgia,serif;padding:1px 4px;border-radius:3px;font-style:normal;box-shadow:0 1px 3px #000}
.trt .treye{position:absolute;right:-6px;top:-5px;width:12px;height:12px;border-radius:50%;background:#ffd23f;box-shadow:0 0 0 2px #2b0810,0 0 8px #ffd23f;animation:tr-pulse 1.4s infinite}
.trt.isgone{border:1px dashed #ff7a59;border-bottom:2px solid #ff4a3a;background:#2a0606;cursor:help}
.trt.isgone .trpic>svg{opacity:.3;filter:grayscale(1)}
.trt.isgone .trbang{position:absolute;inset:0;display:grid;place-items:center;font:900 32px/1 Cinzel,Georgia,serif;color:#ff4a3a;text-shadow:0 0 10px #f00,0 2px 0 #000;font-style:normal;animation:tr-pulse 1s infinite}
.trt.isgone .trv{color:#ff7a59;font-weight:700}
.tre{color:#8a6a3a;font-size:12px;padding:2px 10px 10px;text-align:center;margin:0}.tre.issmall{font-size:11px;padding-top:0}
.trc{display:flex;flex-wrap:wrap;gap:4px;align-items:center;padding:0 8px 8px}
.trc label{display:flex;align-items:center;gap:6px;font:700 12px Cinzel,Georgia,serif;color:#d9b98a;flex:1 1 100%}
#mb .trc input{flex:1;min-width:0;width:100%;box-sizing:border-box;font:700 15px Cinzel,Georgia,serif;color:#ffd23f;padding:6px 8px}
#mb .trc input.bad{border-color:#ff7a59;box-shadow:0 0 0 2px #ff7a5944}
#mb .trc button{padding:5px 7px;font-size:11px}
.trc small{flex:1 1 100%;font-size:11px}
.trbag .trgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;padding:8px}
.trs{position:relative;aspect-ratio:1;background:#1a0408;border:1px solid #d9a52033;border-bottom:2px solid var(--rc,#d9a52033);border-radius:4px;display:grid;place-items:center;cursor:pointer;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
.trs>svg:not(.trlk){width:82%;height:82%;filter:drop-shadow(0 1px 1px #000)}
.trs:hover{border-color:#ffd23f}
.trs.isin{opacity:.32}
.trs.isin::after{content:"";position:absolute;right:2px;top:2px;width:9px;height:9px;border-radius:50%;background:#39ff88;box-shadow:0 0 6px #39ff88}
.trs.isno{opacity:.35;cursor:not-allowed}
.trs .trlk{position:absolute;right:1px;bottom:1px;width:13px;height:13px}
.trs.isempty{cursor:default;border-bottom-color:#d9a52018}.trs.isempty:hover{border-color:#d9a52033}
.trs small{position:absolute;left:3px;top:1px;font:700 10px Cinzel,Georgia,serif;color:#ffd23f;text-shadow:0 1px 0 #000}
.trs.iscoin>svg{width:96%;height:96%}
.tri{display:flex;gap:12px;align-items:flex-start;padding:10px;border:1px solid #d9a52044;border-radius:6px;background:#16030a;min-height:112px}
.tri.isempty{align-items:center;justify-content:center;color:#8a6a3a;font-size:12px;text-align:center}
.tri .trbig{width:84px;height:84px;flex:none;border-radius:10px;display:grid;place-items:center;background:radial-gradient(circle,#ffffff16,transparent 70%),#1f0509;box-shadow:inset 0 0 0 1px var(--rc),0 0 22px -6px var(--rc)}
.tri .trbig>svg{width:76px;height:76px;filter:drop-shadow(0 3px 3px #000)}
.tri .trtxt{min-width:0;flex:1}
.tri h5{margin:0;font:900 17px Cinzel,Georgia,serif;color:var(--rc)}.tri h5 span{color:#ffd23f;font-size:13px}
.tri .trty{font-size:11px;color:#d9b98a;text-transform:uppercase;letter-spacing:.6px}
.tri .trst{display:flex;gap:5px;flex-wrap:wrap;margin:5px 0 2px}.tri .trst span{background:#2b0810;border:1px solid #d9a52055;border-radius:10px;padding:1px 8px;font-size:11px;color:#f6eedc}
.tri p{margin:4px 0;font-style:italic;color:#e8dcc0}
.tri .trpr{font-size:12px;color:#d9b98a}.tri .trpr b{color:#ffd23f}
.tri .trown{font-size:11px;color:#a8875a;margin-top:2px}.tri .trbad{color:#ff7a59}
.trb{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;margin-top:10px}
.trb .trside small{display:block;font-size:10px;color:#d9b98a;text-transform:uppercase;letter-spacing:.6px}.trb .trside b{font:700 14px Cinzel,Georgia,serif;color:#f6eedc}.trb .trside.isr{text-align:right}
.trb .trbar{height:10px;background:#120306;border-radius:5px;overflow:hidden;display:flex;border:1px solid #000;box-shadow:inset 0 1px 2px #000}
.trb .trbar i{display:block;height:100%;transition:width .4s}.trb .trbar .tra{background:linear-gradient(90deg,#c98a10,#ffd23f)}.trb .trbar .trbb{background:linear-gradient(90deg,#39ff88,#1e9a52)}
.trnet{text-align:center;font-size:12px;margin-top:3px}.trnet.trup,.trsum .trup{color:#39ff88}.trnet.trdn,.trsum .trdn{color:#ff7a59}
.trw{margin-top:8px;display:flex;flex-direction:column;gap:5px}.tr-foot .trw{flex:1 1 100%;margin:0}
.trw div{padding:7px 10px;border-radius:4px;font-size:12px;font-weight:700;border-left:3px solid;line-height:1.35}
.trw .trwbad{background:#3a0808;border-color:#ff4a3a;color:#ffc2b6}
.trw .trwwarn{background:#3a2208;border-color:#ffb02a;color:#ffdca6}
.trw .trwinfo{background:#2a2208;border-color:#ffd23f;color:#ffeab0}
.tr-foot{position:sticky;bottom:-14px;margin:12px -14px -14px;padding:10px 14px;background:linear-gradient(#2b0810f2,#15030a);border-top:1px solid #d9a52066;display:flex;gap:10px;align-items:center;flex-wrap:wrap;z-index:3}
@media (max-width:440px){.tr-foot{bottom:-10px;margin:12px -10px -10px;padding:8px 10px}}
#mb .tr-foot [data-tacc]{font-size:15px;padding:10px 20px;min-width:180px}
.tr-foot .tr-status{margin:0;flex:1 1 260px}
.trmenu{position:absolute;z-index:6;background:#15030a;border:1px solid #d9a520;border-radius:4px;box-shadow:0 10px 28px #000d;min-width:160px;padding:4px}
#mb .trmenu button{display:block;width:100%;text-align:left;background:none;border:0;box-shadow:none;padding:8px 10px;font:700 12px Cinzel,Georgia,serif;color:#ffe9b0;border-radius:2px}
#mb .trmenu button:hover{background:#7a1420}
.trmenu .trhd{padding:4px 10px 6px;font:700 12px Alegreya,Georgia,serif;color:#ffd23f;border-bottom:1px solid #d9a52033;margin-bottom:2px}
.trmenu form{display:flex;gap:4px;padding:4px}#mb .trmenu form input{width:110px}#mb .trmenu form button{width:auto;text-align:center;background:linear-gradient(#ffe88a,#f2b400);color:#2a1400}
.trx{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}@media (max-width:600px){.trx{grid-template-columns:1fr}}
.trx section{border:1px solid #d9a52066;border-radius:6px;background:linear-gradient(#2b0810,#1f0509);padding:8px 10px;display:flex;flex-direction:column}
.trx section.ist{box-shadow:inset 0 0 0 1px #39ff8822}
.trx h4{margin:0 0 6px;font:700 13px Cinzel,Georgia,serif;color:#ffd23f}
.trx footer{margin-top:auto;padding-top:6px;font-size:12px;color:#d9b98a}.trx footer b{color:#f6eedc}
.trr{display:grid;grid-template-columns:42px 1fr auto auto;gap:8px;align-items:center;padding:5px 4px 5px 8px;border-bottom:1px solid #ffd23f14;border-left:3px solid var(--rc,#bbb);cursor:pointer;margin-bottom:3px;border-radius:2px;background:#16030a}
.trr:hover,.trr.issel{background:#2b0810}
#trpop{position:absolute;z-index:7;display:none;filter:drop-shadow(0 10px 24px #000e)}
#trpop .tri{background:linear-gradient(#2b0810,#15030a);border:1px solid #d9a520;min-height:0}
#trpop .trpx{position:absolute;right:6px;top:4px;padding:2px 6px}
.trs.issel{border-color:#ffd23f;box-shadow:0 0 0 1px #ffd23f}
.trr>svg{width:40px;height:40px;filter:drop-shadow(0 2px 2px #000)}
.trr .trnm{font-weight:700;min-width:0}.trr .trnm small{display:block;font-weight:400;font-size:11px;color:#a8875a}
.trr .trn{color:#ffd23f;font:700 13px Cinzel,Georgia,serif}.trr .trv{color:#d9b98a;font-size:12px;text-align:right;white-space:nowrap}
.trr.iscoin .trnm{color:#ffd23f}
.trr.isgone{border-left-color:#ff4a3a;background:#2a0606}.trr.isgone .trnm{color:#ff7a59;text-decoration:line-through}.trr.isgone>svg{opacity:.4;filter:grayscale(1)}
.trsum{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:10px;padding:8px 10px;border:1px solid #d9a52044;border-radius:6px;background:#16030a;font-size:12px;color:#d9b98a}.trsum b{color:#f6eedc}
.trh{display:flex;flex-direction:column;gap:6px;margin-top:10px;max-height:60vh;overflow:auto}
.trhr{display:grid;grid-template-columns:130px 1fr 1fr;gap:8px;padding:8px;border:1px solid #d9a52033;border-radius:6px;background:#16030a;align-items:center}
@media (max-width:520px){.trhr{grid-template-columns:1fr}}
.trhr .trwhen b{display:block;color:#ffd23f}.trhr small{color:#a8875a;font-size:11px}
.trhr .trmini{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}.trhr .trmini span{display:inline-flex;align-items:center;gap:2px;font-size:11px;color:#f6eedc}.trhr .trmini span>svg{width:26px;height:26px}.trhr em{color:#8a6a3a;font-size:11px}
#trq{position:fixed;top:64px;left:50%;transform:translateX(-50%);z-index:30;display:none;align-items:center;gap:10px;background:radial-gradient(120% 120% at 50% 0%,#5a1220,#24060c);border:2px solid #d9a520;outline:1px solid #15030a;border-radius:6px;padding:10px 12px 12px;box-shadow:0 10px 30px #000c;color:#f6eedc;font:13px Alegreya,Georgia,serif;max-width:calc(100vw - 24px);overflow:hidden}
#trq img{width:38px;height:38px;border-radius:50%;box-shadow:0 0 0 2px #d9a520;flex:none}
#trq .trqt b{font:900 15px Cinzel,Georgia,serif;color:#ffd23f}#trq .trqt small{color:#d9b98a}#trq .trqt span{display:block;color:#f6eedc}
#trq button{font:700 13px Cinzel,Georgia,serif;color:#2a1400;background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);border:1px solid #6b4a06;border-radius:3px;padding:8px 14px;cursor:pointer}
#trq button.trqn{background:none;border-color:transparent;color:#d9b98a;text-decoration:underline;padding:8px 6px}
#trq i{position:absolute;left:0;bottom:0;height:3px;width:100%;background:#ffd23f}#trq.go i{animation:trq-t 60s linear forwards}
@keyframes trq-t{to{width:0}}
.ntag.pn{pointer-events:auto;cursor:pointer;padding:2px 4px}.ntag.pn:hover{color:#fff2a8}
@keyframes tr-glow{50%{box-shadow:0 0 0 2px #39ff88,0 0 26px #39ff88aa}}
@keyframes tr-pulse{50%{opacity:.4}}
@media (prefers-reduced-motion:reduce){.trt,.trt.new,.trt .eye,.trt.gone .bang,.trp.ischg{animation:none!important;transition:none!important}}
"""
i = h.index("</style>")
h = h[:i] + CSS + h[i:]

open(PATH, 'w', encoding='utf-8').write(h)
print('trade window v2 patch applied')
