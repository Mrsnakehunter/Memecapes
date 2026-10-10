#!/usr/bin/env python3
"""Online play: log in, cloud saves, see other players, chat with them, trade with them.

Everything here only switches on when config.js has a server address (MC_CONFIG.server).
With no address the game plays exactly as before, saved in the browser.
The server is in server/ (see server/README.md).
Run from the repo root after patch_anim.py:  python3 tools/patch_net.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


NET = r"""
// ---- online play: only when config.js names a server
const NETS={ws:null,on:false,rev:0,name:'',me:0,dirty:0,lastSave:0,others:new Map(),info:new Map(),inTrade:0,lastPos:'',want:null,retry:0,kicked:0,n:0};
const SRV=()=>(window.MC_CONFIG&&MC_CONFIG.server)||'';
const LS={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}},del:k=>{try{localStorage.removeItem(k)}catch(e){}}};
const SS={get:k=>{try{return sessionStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{sessionStorage.setItem(k,v)}catch(e){}},del:k=>{try{sessionStorage.removeItem(k)}catch(e){}}};
let netIgn=new Set();try{netIgn=new Set(JSON.parse(LS.get('mc_ign')||'[]'))}catch(e){}
function netDirty(){NETS.dirty=1}
function netSend(o){if(NETS.ws&&NETS.ws.readyState==1)NETS.ws.send(JSON.stringify(o))}
function netConnect(first){if(!SRV())return;try{NETS.ws&&NETS.ws.close()}catch(e){}
 const ws=new WebSocket(SRV());NETS.ws=ws;
 ws.onopen=()=>{NETS.retry=0;if(first)netSend(first);else{const tk=LS.get('mc_tok');if(tk)netSend({t:'resume',token:tk})}};
 ws.onmessage=e=>{let m;try{m=JSON.parse(e.data)}catch(x){return}const f=NETH[m.t];if(f)try{f(m)}catch(x){console.error(x)}};
 ws.onclose=()=>{if(NETS.ws!==ws)return;const was=NETS.on;NETS.on=false;NETS.others.clear();netTagsClear();if(NETS.kicked)return;
  if(was){say('Lost the connection to the server. Reconnecting...','#c00')}
  if(was||NETS.retry){const d=Math.min(30,2+NETS.retry*3);NETS.retry++;setTimeout(()=>netConnect(),d*1000)}else if(NETS.want){netErr('Could not reach the game server. Try again in a minute, or play offline.')}}}
function netErr(t){const e=$('ner');if(e)e.textContent=t;else say(t,'#c00')}
function netSaveNow(){if(!NETS.on||NETS.inTrade)return;NETS.dirty=0;NETS.lastSave=Date.now();netSend({t:'save',st,rev:NETS.rev})}
function netReload(save,rev,mode){{const cur=LS.get('ms4');try{const o=JSON.parse(cur);if(o&&o.acct&&!o.upl&&!LS.get('ms4_offline'))LS.set('ms4_offline',cur)}catch(e){}}LS.set('ms4',JSON.stringify(save));LS.set('mc_rev',String(rev));SS.set('mc_auto',mode||'begin');location.reload()}
const NETH={
 hello(){},
 err(m){if(m.relog){LS.del('mc_tok');if(started)say('Please log in again from the start screen.','#c00')}netErr(m.text)},
 welcome(m){NETS.name=m.name;NETS.me=0;NETS.rev=m.rev;NETS.n=m.online;LS.set('mc_tok',m.token);LS.set('mc_name',m.name);
  const w=NETS.want;NETS.want=null;
  if(started){NETS.on=true;if(m.rev!==+(LS.get('mc_rev')||0)&&m.save){say('Your progress changed on another device. Loading it...','#a60');return netReload(m.save,m.rev,'begin')}say('Back online.','#0a0');return}
  if(SS.get('mc_auto')){SS.del('mc_auto');NETS.on=true;LS.set('mc_rev',String(m.rev));const mode=SS.get('mc_mode');SS.del('mc_mode');netStart(m.save?mode:'design');return}
  if(m.save)return netReload(m.save,m.rev,'begin');
  // a brand-new account: bring this browser's progress, or start fresh
  if(w&&w.bring&&!st.upl){st.acct={name:m.name};st.upl=m.name;st.iron=w.iron?1:0;NETS.on=true;netSaveNow();netStart('begin');return}
  const fresh={acct:{name:m.name},ap:st.ap,iron:w&&w.iron?1:0,upl:m.name};LS.set('ms4',JSON.stringify(fresh));LS.set('mc_rev','0');SS.set('mc_auto','design');location.reload()},
 saved(m){NETS.rev=m.rev;LS.set('mc_rev',String(m.rev))},
 stale(m){if(m.rev>NETS.rev)netSend({t:'pull'})},
 resync(m){if(m.save){say('Loading your latest progress from the server...','#a60');netReload(m.save,m.rev,'begin')}},
 chatlog(m){if(m.lines&&m.lines.length)say('<span style="opacity:.7">Recent chat: '+m.lines.slice(-5).map(l=>'<b>'+esc(l.name)+':</b> '+esc(l.text)).join(' | ')+'</span>','#555')},
 info(m){say(esc(m.text),m.color||'#a60')},
 notice(m){say('<b>NOTICE:</b> '+esc(m.text),'#c80')},
 kicked(m){NETS.kicked=1;NETS.on=false;say(esc(m.text),'#c00');netErr(m.text)},
 deleted(){LS.del('mc_tok');LS.del('mc_name');say('Your online account was deleted.','#c00')},
 who(m){say('Online ('+m.names.length+'): '+m.names.map(netName).join(', '),'#a60')},
 pi(m){NETS.info.set(m.id,m);if(m.name===NETS.name)NETS.me=m.id},
 leave(m){NETS.others.delete(m.id);netTagDel(m.id)},
 pl(m){NETS.n=m.n;const seen=new Set();for(const q of m.p){const[id,x,y,r,mv]=q;if(netIgn.has((NETS.info.get(id)||{}).name))continue;seen.add(id);let o=NETS.others.get(id);if(!o){o={id,px:x,py:y,tx:x,ty:y,r,mv:0};NETS.others.set(id,o)}o.tx=x;o.ty=y;o.tr=r;o.mv=mv;o.seen=performance.now()}
  for(const[id,o] of NETS.others)if(!seen.has(id)&&performance.now()-o.seen>1500){NETS.others.delete(id);netTagDel(id)}},
 chat(m){if(m.name===NETS.name||netIgn.has(m.name))return;say('<b>'+(m.role?'<span style="color:#c80">['+esc(m.role)+']</span> ':'')+netName(m.name)+':</b> '+esc(m.text),'#1a1aa0');const o=NETS.others.get(m.id);if(o)netBubble(o,m.text)},
 tradeReq(m){say(netName(m.from)+' wants to trade with you. <a href="#" class="pn" data-ty="'+esc(m.from)+'" style="color:#0a0;font-weight:700">Accept trade</a>','#a60');netSaveNow()},
 tradeStart(m){NETS.inTrade=1;netSaveNow();NETS.inTrade=1;p2pOpen({name:m.with,net:1})},
 tradeTheirs(m){p2pTheirs(m.items,m.coins)},
 tradeAcc(){if(T2){T2.acc[1]=1;p2pUI()}},
 tradeStage2(){if(T2)p2pStage2()},
 tradeDone(m){NETS.inTrade=0;if(T2){T2.mine=m.gave;T2.theirs=m.got;try{p2pDone()}catch(e){}}T2=null;M.style.display='none';st.inv=m.inv;st.coins=m.coins;NETS.rev=m.rev;LS.set('mc_rev',String(m.rev));ui();save()},
 tradeCancel(m){NETS.inTrade=0;if(T2){say(esc(m.why||'Trade cancelled.'),'#c00');T2=null;M.style.display='none'}}
};
function netName(n){n=String(n).replace(/[^A-Za-z0-9_]/g,'');return '<a href="#" class="pn" data-pn="'+n+'" style="color:inherit">'+n+'</a>'}
window.NET={chat:t=>{if(NETS.on)netSend({t:'chat',text:t})},tradeOpen:p=>{},tradeAccept:s=>{if(NETS.on&&NETS.inTrade)netSend({t:'tradeAccept',stage:s})},tradeDone:()=>{},tradeCancel:()=>{if(NETS.inTrade){NETS.inTrade=0;netSend({t:'tradeCancel'})}},mkPlace:()=>{}};
let netOfferLast='';function netTradeSync(T){if(!T.p.net||T.stage!=1||!NETS.inTrade)return;const s=JSON.stringify(T.mine);if(s===netOfferLast)return;netOfferLast=s;netSend({t:'tradeOffer',items:T.mine.items,coins:T.mine.coins})}
// chat commands; anything else that starts with / goes to the server (moderator commands)
function netCmd(t){const[c,a,...r]=t.slice(1).split(' '),nm=(a||'').replace(/[^A-Za-z0-9_]/g,'');
 if(c=='help'){say('Commands: /who, /trade name, /ignore name, /unignore name, /report name reason, /logout'+(SRV()?'':' (online play is not switched on yet)'),'#a60');return true}
 if(!NETS.on){say('You are playing offline.','#c00');return true}
 if(c=='who'){netSend({t:'who'});return true}
 if(c=='trade'&&nm){netSaveNow();netSend({t:'tradeReq',name:nm});return true}
 if(c=='ignore'&&nm){netIgn.add(nm);LS.set('mc_ign',JSON.stringify([...netIgn]));netSend({t:'ignore',name:nm});say('You will not see '+nm+' any more.','#a60');return true}
 if(c=='unignore'&&nm){netIgn.delete(nm);LS.set('mc_ign',JSON.stringify([...netIgn]));netSend({t:'ignore',name:nm,off:1});say(nm+' is no longer ignored.','#a60');return true}
 if(c=='report'&&nm){netSend({t:'report',name:nm,why:r.join(' ')});return true}
 if(c=='logout'){netSaveNow();setTimeout(()=>{netSend({t:'logout',token:LS.get('mc_tok')});LS.del('mc_tok');NETS.kicked=1;location.reload()},400);return true}
 if(c=='deleteaccount'){if(!a){say('Type /deleteaccount followed by your password. This deletes your online account and its progress for good.','#c00');return true}netSend({t:'deleteAccount',pass:a});return true}
 netSend({t:'chat',text:t});return true}
// clicking a name in chat: trade, ignore, report
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('.pn');if(!a)return;e.preventDefault();
 if(a.dataset.ty){netSaveNow();netSend({t:'tradeYes',name:a.dataset.ty});return}
 const n=a.dataset.pn;if(!n||n===NETS.name||!NETS.on)return;let d=$('pnm');if(!d){d=document.createElement('div');d.id='pnm';document.body.appendChild(d)}
 d.innerHTML='<b>'+n+'</b><button data-pa="t">Trade</button><button data-pa="i">'+(netIgn.has(n)?'Unignore':'Ignore')+'</button><button data-pa="r">Report</button><button data-pa="x">Close</button>';
 d.style.left=Math.min(innerWidth-170,e.clientX)+'px';d.style.top=Math.max(8,e.clientY-120)+'px';d.style.display='block';
 d.onclick=ev=>{const b=ev.target.dataset.pa;if(!b)return;d.style.display='none';if(b=='t')netCmd('/trade '+n);if(b=='i')netCmd((netIgn.has(n)?'/unignore ':'/ignore ')+n);if(b=='r'){netCmd('/report '+n+' reported from chat');}}});
// other players in the world
function netSelf(x,y,r,mv){if(!NETS.on||!started)return;const lv=(()=>{try{return combatLvl()}catch(e){return 3}})(),k=[x.toFixed(2),y.toFixed(2),r.toFixed(2),mv,st.ap&&st.ap.g?1:0,(st.eq&&st.eq.cape)||'',lv].join(',');
 const t=performance.now();if(k===NETS.lastPos&&t-(NETS.lastPosT||0)<3000||t-(NETS.lastPosT||0)<190)return;NETS.lastPos=k;NETS.lastPosT=t;
 netSend({t:'pos',x,y,r,m:mv,g:st.ap&&st.ap.g?1:0,c:(st.eq&&st.eq.cape)||'',lv})}
function netDraw(now){if(!NETS.on||!NETS.others.size)return;const dt=Math.min(.1,(now-(NETS.lt||now))/1000);NETS.lt=now;
 for(const o of NETS.others.values()){const inf=NETS.info.get(o.id)||{},dx=o.tx-o.px,dy=o.ty-o.py,dd=Math.hypot(dx,dy);
  if(dd>6){o.px=o.tx;o.py=o.ty}else{const k=Math.min(1,dt*8);o.px+=dx*k;o.py+=dy*k}
  let dr=(o.tr||0)-(o.r||0);dr=Math.atan2(Math.sin(dr),Math.cos(dr));o.r=(o.r||0)+dr*Math.min(1,dt*10);
  const K=inf.g?'playerf':'player';needMdl(K);const PMo=(MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player;if(!PMo||!PMo.ok)continue;
  const mv=o.mv||(dd>.05?1:0);qMdl(PMo,o.px+.5,0,o.py+.5,o.r,MDLSC.player,mv?(mv==2?'Running':'Walking'):null,now/1000+o.id,0,null,false,1);
  if(inf.c)qCape(o.px+.5,o.py+.5,o.r,inf.c)}
 netTags()}
const NTAG=new Map();function netTagDel(id){const d=NTAG.get(id);if(d){d.remove();NTAG.delete(id)}}function netTagsClear(){for(const id of [...NTAG.keys()])netTagDel(id)}
function netTags(){for(const o of NETS.others.values()){const inf=NETS.info.get(o.id);if(!inf)continue;let d=NTAG.get(o.id);if(!d){d=document.createElement('div');d.className='ntag';document.body.appendChild(d);NTAG.set(o.id,d)}
  const lbl=inf.name+' (lvl '+inf.lv+')';if(d.textContent!==lbl)d.textContent=lbl;
  const p=[o.px+.5-E[0],2.05+hgt(o.px+.5,o.py+.5)-E[1],o.py+.5-E[2]],zz=d3(p,Fw);if(zz<=0){d.style.display='none';continue}
  const sx=d3(p,Rt)/(zz*TH*asp),sy=d3(p,Up)/(zz*TH);d.style.display=(Math.abs(sx)>1.1||Math.abs(sy)>1.1||zz>40)?'none':'block';d.style.left=((sx+1)/2*CW)+'px';d.style.top=((1-sy)/2*CH)+'px'}}
function netBubble(o,tx){for(let i=bubbles.length-1;i>=0;i--)if(bubbles[i].gb===o){bubbles[i].d.remove();bubbles.splice(i,1)}const d=document.createElement('div');d.className='pbub';d.style.display='none';const sp=document.createElement('span');sp.textContent=tx;d.appendChild(sp);document.body.appendChild(d);bubbles.push({gb:o,d,h:2.5,t:performance.now()+2500+40*tx.length})}
setInterval(()=>{if(NETS.on&&NETS.dirty&&!NETS.inTrade&&Date.now()-NETS.lastSave>10000)netSaveNow()},1000);
addEventListener('pagehide',()=>{if(NETS.on&&NETS.dirty)netSaveNow()});
// start screen: log in / create an online account
function netStart(mode){if(mode=='design')designScr();else begin()}
function netLoginScr(reg){ST.className='full';const has=(st.acct&&!st.upl)&&(Object.values(st.xp||{}).some(v=>v>1200)||st.coins>0);
 SBX.innerHTML='<h2>'+(reg?'Create an online account':'Log in')+'</h2>Username<br><input id="nun" maxlength="12" autocomplete="username" style="width:100%;box-sizing:border-box;padding:8px;font:14px Georgia" value="'+(reg?'':(LS.get('mc_name')||''))+'"><br><br>Password<br><input id="npw" type="password" maxlength="100" autocomplete="'+(reg?'new-password':'current-password')+'" style="width:100%;box-sizing:border-box;padding:8px;font:14px Georgia">'
 +(reg?'<br><br>Password again<br><input id="npw2" type="password" maxlength="100" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:8px;font:14px Georgia"><label style="display:block;margin-top:10px"><input type="checkbox" id="nim"> Diamond Hands mode (no trading, no Stock Market)</label>'+(has?'<label style="display:block;margin-top:6px"><input type="checkbox" id="nbr" checked> Bring my progress from this browser ('+esc(st.acct.name)+')</label>':''):'')
 +'<div id="ner" style="color:#ff8a8a;margin-top:8px;min-height:16px"></div><button class="big" id="ngo">'+(reg?'Create account':'Log in')+'</button><button class="big" id="nbk">Back</button><div style="font-size:11px;color:#ccc;margin-top:8px">Pick a password you do not use anywhere else. MemeCapes never asks for your wallet seed phrase or private key.</div>';
 $('nbk').onclick=menuScr;const go=()=>{const u=$('nun').value.trim(),p=$('npw').value;$('ner').textContent='';
  if(!/^[A-Za-z0-9_]{3,12}$/.test(u))return netErr('Username: 3 to 12 letters, numbers or _.');if(p.length<8)return netErr('Password: at least 8 characters.');
  if(reg&&p!==$('npw2').value)return netErr('The two passwords are different.');
  NETS.want={bring:reg&&$('nbr')&&$('nbr').checked,iron:reg&&$('nim').checked};$('ngo').textContent='Connecting...';
  netConnect(reg?{t:'register',name:u,pass:p,iron:NETS.want.iron?1:0}:{t:'login',name:u,pass:p});setTimeout(()=>{const b=$('ngo');if(b)b.textContent=reg?'Create account':'Log in'},4000)};
 $('ngo').onclick=go;$('npw').onkeydown=e=>{if(e.key=='Enter')go()}}
function netMenu(){if(!SRV())return;const box=document.createElement('div'),tk=LS.get('mc_tok'),nm=LS.get('mc_name');
 box.innerHTML=(tk&&nm?'<button class="big" id="noc">Continue online as '+esc(nm)+'</button>':'')+'<button class="big" id="nol">Play Online: Log in</button><button class="big" id="nor">Play Online: Create Account</button><div style="font-size:11px;color:#ccc;margin:2px 0 8px">Online: your progress is saved on the server and you can play, chat and trade with other players. The buttons below play offline in this browser.</div>';
 const ref=SBX.querySelector('.big');SBX.insertBefore(box,ref);
 if($('noc'))$('noc').onclick=()=>{$('noc').textContent='Connecting...';NETS.want={};SS.set('mc_pending','1');netConnect({t:'resume',token:tk})};
 if(st.upl&&$('bc'))$('bc').style.display='none';$('nol').onclick=()=>netLoginScr(0);$('nor').onclick=()=>netLoginScr(1)}
// after a reload that came from logging in: connect again and go straight in
if(SRV()&&SS.get('mc_auto')&&LS.get('mc_tok')){const mode=SS.get('mc_auto');SS.set('mc_mode',mode);setTimeout(()=>{SBX.innerHTML='<h2>Connecting to MemeCapes...</h2><div id="ner" style="color:#ff8a8a;min-height:16px;margin:8px 0"></div><button class="big" id="nbk">Back</button>';$('nbk').onclick=()=>{SS.del('mc_auto');NETS.want=null;menuScr()};NETS.want={};netConnect({t:'resume',token:LS.get('mc_tok')})},50)}
// a new version of the game is out: say so (checked every 5 minutes)
setInterval(()=>{fetch('version.json?t='+Date.now()).then(r=>r.json()).then(v=>{if(v&&v.build&&v.build!==BUILD&&!NETS.upd){NETS.upd=1;say('<b>A new MemeCapes update is out.</b> Refresh the page to get it.','#c80')}}).catch(()=>{})},300000);
"""

# insert the module next to the other helpers
rep("// ---- which animation to play:", NET + "// ---- which animation to play:")

# the build id (build.sh replaces __BUILD__)
rep("const $=i=>document.getElementById(i);", "const $=i=>document.getElementById(i);const BUILD='__BUILD__';")

# saving also marks the online copy as needing an upload
rep("const save=()=>{try{localStorage.setItem('ms4',JSON.stringify(st))}catch(e){}};",
    "const save=()=>{try{localStorage.setItem('ms4',JSON.stringify(st))}catch(e){}netDirty()};")

# chat commands
rep("function sendChat(t){t=(t||'').replace(/\\s+/g,' ').trim().slice(0,80);if(!t)return;",
    "function sendChat(t){t=(t||'').replace(/\\s+/g,' ').trim().slice(0,80);if(!t)return;if(t[0]=='/'&&netCmd(t))return;")

# start screen gets the online buttons
rep("if(n)$('bc').onclick=begin;$('bn').onclick=acctScr;", "netMenu();if(n)$('bc').onclick=begin;$('bn').onclick=acctScr;")

# trades with real players: offers go to the server, and the server decides when both have accepted
rep("function p2pUI(){const T=T2;if(!T)return;", "function p2pUI(){const T=T2;if(!T)return;netTradeSync(T);")
rep("if(T.acc[1]){if(T.stage==1)p2pStage2();else p2pDone()}else p2pUI()", "if(T.acc[1]&&!T.p.net){if(T.stage==1)p2pStage2();else p2pDone()}else p2pUI()")
rep("function p2pOpen(partner){if(st.iron)return say('In Diamond Hands mode you cannot trade.');T2=", "function p2pOpen(partner){if(st.iron)return say('In Diamond Hands mode you cannot trade.');netOfferLast='';T2=")

# capes on other players
rep("function qCape(x,z,yaw){const k=st.eq&&st.eq.cape;if(!k)return;let cm=CAPEM[k];if(cm)needMdl(cm);else{cm='cp_'+k+(st.trim&&k.startsWith('cape_')?'_t':'');",
    "function qCape(x,z,yaw,kk){const k=kk!==undefined?kk:st.eq&&st.eq.cape;if(!k)return;let cm=CAPEM[k];if(cm)needMdl(cm);else{cm='cp_'+k+(kk===undefined&&st.trim&&k.startsWith('cape_')?'_t':'');")

# draw the other players right after ourselves, and tell the server where we are
rep("PC=PM&&PM.ok?pClip(PM,skA,mvg,now):null;if(PM&&PM.ok&&st.body!==0&&",
    "PC=PM&&PM.ok?pClip(PM,skA,mvg,now):null;netSelf(P.px,P.py,pry,mvg?(pspd>2.4?2:1):0);netDraw(now);if(PM&&PM.ok&&st.body!==0&&")

# styles: name tags and the little name menu
h = h.replace("</style>", "#pnm{position:fixed;z-index:60;display:none;background:linear-gradient(#5a0d14,#2a0508);border:2px solid #c9a03a;border-radius:8px;padding:8px;min-width:140px;box-shadow:0 6px 18px #000a;font:13px Georgia;color:#ffe9a8}#pnm b{display:block;margin-bottom:6px;color:#ffd23f;font-family:Cinzel,Georgia,serif}#pnm button{display:block;width:100%;margin:3px 0;padding:6px;background:#3a070c;color:#ffe9a8;border:1px solid #c9a03a;border-radius:5px;cursor:pointer;font:13px Georgia}#pnm button:hover{background:#6a1018}.ntag{position:fixed;z-index:4;transform:translate(-50%,-100%);pointer-events:none;white-space:nowrap;font:700 11px Cinzel,Georgia,serif;color:#ffd23f;text-shadow:0 1px 2px #000,0 0 3px #000}.pn{text-decoration:none;cursor:pointer}.pn:hover{text-decoration:underline}</style>", 1)  # first style block

open(PATH, 'w', encoding='utf-8').write(h)
print('net patch applied')
