#!/usr/bin/env python3
"""Friends and private messages in the game (Albert, Oct 31: "a spot where people can add people in game so they can
private message them").

  - Friends button in the chat bar (with an unread badge) opens the Friends window: requests waiting for you (Accept /
    Decline), your friends with a green dot when online (Message / Remove), and a box to add someone by name.
  - A friend's name in the list opens the conversation: the last messages (kept on the server for 30 days), and a
    box to write. Messages also show in the chat log in purple ("From Bob: ...", click = reply) and a "PMs" filter.
  - Clicking a player's name (chat or name tag) now also offers Add friend / Remove friend and Message.
  - Chat commands: /add name, /accept name, /decline name, /remove name, /friends, /pm name text (also /w, /msg, /tell).
  Only friends can message each other; ignoring someone drops their messages and requests. Server side: server/friends.js.
Run after patch_weapons.py:  python3 tools/patch_friends.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


CSS = r"""#frdb{position:relative;flex:none;padding:2px 7px;font:700 13px/1 Georgia,serif;border-radius:10px;background:linear-gradient(#7a1420,#4a0a12);color:#ffe9b0;border:1px solid #d9a520;cursor:pointer;margin-right:2px}#frdn{display:none;position:absolute;top:-6px;right:-6px;min-width:16px;height:16px;border-radius:8px;background:#e0342c;color:#fff;font:700 10px/16px Georgia,serif;text-align:center;padding:0 3px;font-style:normal}#frdn.on{display:block}
#cl.f-pm>div:not(.pm){display:none}#cl .pm{color:#7a2cb8!important}#cl .pm a.frr{color:#7a2cb8;font-weight:700}
#mb.frd{max-width:460px;padding:0;overflow:hidden;display:flex;flex-direction:column;max-height:84vh}
.frdh{display:flex;align-items:center;gap:8px;padding:10px 12px;background:linear-gradient(#7a1420,#4a0a12);color:#ffe9b0;font:700 15px Cinzel,Georgia,serif;border-bottom:2px solid #d9a520}.frdh b{flex:1}.frdh button{padding:3px 9px;font-size:11px}
.frdbody{overflow:auto;padding:10px 12px;flex:1;min-height:200px}
.frdsec{font:700 11px Cinzel,Georgia,serif;color:#d9b98a;letter-spacing:.06em;margin:10px 0 4px}.frdsec:first-child{margin-top:0}
.frdrow{display:flex;align-items:center;gap:8px;padding:6px 4px;border-bottom:1px dashed #fff3}.frdrow .nm{flex:1;font-weight:700;cursor:pointer;color:var(--ink)}.frdrow .nm small{font-weight:400;opacity:.7;margin-left:6px}
.frdot{width:9px;height:9px;border-radius:50%;background:#777;flex:none;box-shadow:0 0 0 1px #0006 inset}.frdot.on{background:#3ddc6a;box-shadow:0 0 6px #3ddc6a}
.frdrow button{padding:3px 8px;font-size:11px}.frdadd{display:flex;gap:6px;margin-top:6px}.frdadd input{flex:1;min-width:0;font:700 13px Georgia,serif;padding:5px 8px}
.frdempty{opacity:.75;font-size:12px;padding:4px}
.frdlog{overflow:auto;flex:1;padding:10px 12px;display:flex;flex-direction:column;gap:6px;min-height:220px;max-height:50vh;background:#0002}
.frdm{max-width:82%;padding:6px 10px;border-radius:12px;background:#fff8;color:#2a1400;font-size:13px;line-height:1.35;align-self:flex-start;word-break:break-word}.frdm.me{align-self:flex-end;background:#f2d27a}.frdm small{display:block;opacity:.6;font-size:10px;margin-top:2px}
.frdin{display:flex;gap:6px;padding:8px 12px;border-top:1px solid #fff3}.frdin input{flex:1;min-width:0;font:13px Georgia,serif;padding:6px 8px}
.frdnote{font-size:11px;opacity:.75;padding:0 12px 8px}
"""
rep("#modal{position:fixed;inset:0;", CSS + "#modal{position:fixed;inset:0;")

# chat bar: PMs filter + Friends button
rep('<button data-cf="chat">Chat</button></div>', '<button data-cf="chat">Chat</button><button data-cf="pm">PMs</button></div>')
# the Friends button sits on the input row, so phones (no filter bar) have it too
rep('<div id="cin"><b id="cnm">Guest:</b>', '<div id="cin"><button id="frdb" type="button" title="Friends and messages">&#9825;<i id="frdn"></i></button><b id="cnm">Guest:</b>')
rep("if(MB.className&&!MB.querySelector('#mkroot,#trroot,#skxroot'))", "if(MB.className&&!MB.querySelector('#mkroot,#trroot,#skxroot,#frdroot'))")

JS = r"""
// ---- friends and private messages (server/friends.js)
const FRD={list:[],reqs:[],unread:{},open:null,hist:{},view:'list'};
function frdBadge(){let n=0;for(const k in FRD.unread)n+=FRD.unread[k];n+=FRD.reqs.length;const b=$('frdn');if(!b)return;b.textContent=n>99?'99+':String(n);b.classList.toggle('on',n>0)}
function frdWhen(t){const d=new Date(t||Date.now()),n=new Date();return (d.toDateString()==n.toDateString()?'':d.toLocaleDateString(undefined,{month:'short',day:'numeric'})+' ')+d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'})}
function frdSay(html){chat.push('<div class="pm pl">'+html+'</div>');if(chat.length>150)chat.shift();const L=$('clog'),atB=L.scrollHeight-L.scrollTop-L.clientHeight<28;$('cl').innerHTML=chat.join('');if(atB)L.scrollTop=L.scrollHeight}
function frdOpen(name){if(!NETS.on){say('Friends and messages need online play.','#c00');return}FRD.view=name?'thread':'list';FRD.open=name||null;M.style.display='flex';MB.onclick=null;MB.oncontextmenu=null;MB.className='frd';frdRender();if(name){FRD.unread[name]=0;frdBadge();netSend({t:'pmHist',name})}}
function frdClose(){M.style.display='none';MB.className='';MB.innerHTML='';FRD.open=null;FRD.view='list'}
function frdRender(){if(MB.className!='frd')return;let x='';
 if(FRD.view=='thread'&&FRD.open){const n=FRD.open,f=FRD.list.find(q=>q.name==n),on=f&&f.on;
  x='<div id="frdroot"><div class="frdh"><button data-fa="back">&larr;</button><span class="frdot'+(on?' on':'')+'"></span><b>'+esc(n)+'</b>'+(on?'<button data-fa="trade" data-n="'+esc(n)+'">Trade</button>':'')+'<button data-fa="close">&times;</button></div><div class="frdlog" id="frdlog">';
  const L=FRD.hist[n]||[];if(!L.length)x+='<div class="frdempty">No messages yet. Say hi.</div>';
  for(const m of L)x+='<div class="frdm'+(m.mine?' me':'')+'">'+esc(m.text)+'<small>'+frdWhen(m.t0)+'</small></div>';
  x+='</div><div class="frdin"><input id="frdi" maxlength="160" placeholder="Message '+esc(n)+'" autocomplete="off" spellcheck="false" enterkeyhint="send"><button data-fa="send">Send</button></div>'+(on?'':'<div class="frdnote">'+esc(n)+' is offline: they get your message when they sign in.</div>')+'</div>';
 }else{
  x='<div id="frdroot"><div class="frdh"><b>Friends</b><button data-fa="close">&times;</button></div><div class="frdbody">';
  if(FRD.reqs.length){x+='<div class="frdsec">WANT TO BE YOUR FRIEND</div>';for(const n of FRD.reqs)x+='<div class="frdrow"><span class="nm">'+esc(n)+'</span><button data-fa="yes" data-n="'+esc(n)+'">Accept</button><button data-fa="no" data-n="'+esc(n)+'">Decline</button></div>'}
  const L=FRD.list.slice().sort((a,b)=>(b.ok-a.ok)||(b.on-a.on)||a.name.localeCompare(b.name));
  x+='<div class="frdsec">FRIENDS ('+L.filter(q=>q.ok).length+')</div>';
  if(!L.length)x+='<div class="frdempty">No friends yet. Add someone by name below, or click a player\'s name in chat.</div>';
  for(const f of L){const u=FRD.unread[f.name]||0;x+='<div class="frdrow"><span class="frdot'+(f.on?' on':'')+'"></span><span class="nm" data-fa="open" data-n="'+esc(f.name)+'">'+esc(f.name)+(f.ok?(f.on?'':'<small>offline</small>'):'<small>waiting for them</small>')+(u?' <i id="frdn" class="on" style="position:static;display:inline-block">'+u+'</i>':'')+'</span>'+(f.ok?'<button data-fa="open" data-n="'+esc(f.name)+'">Message</button>':'')+'<button data-fa="no" data-n="'+esc(f.name)+'" title="Remove">&times;</button></div>'}
  x+='<div class="frdsec">ADD A FRIEND</div><div class="frdadd"><input id="frda" maxlength="12" placeholder="Player name" autocomplete="off" spellcheck="false"><button data-fa="add">Add</button></div><div class="frdempty">Friends see when you are online and can message you. Only friends can.</div></div></div>';
 }
 MB.innerHTML=x;const lg=$('frdlog');if(lg)lg.scrollTop=lg.scrollHeight;const inp=$('frdi')||$('frda');if(inp&&innerWidth>640)inp.focus();
 MB.onclick=e=>{const b=e.target.closest&&e.target.closest('[data-fa]');if(!b)return;const a=b.dataset.fa,n=b.dataset.n;
  if(a=='close')frdClose();else if(a=='trade'){frdClose();netCmd('/trade '+n)}else if(a=='back')frdOpen(null);else if(a=='open')frdOpen(n);else if(a=='yes')netSend({t:'friendYes',name:n});else if(a=='no')netSend({t:'friendNo',name:n});
  else if(a=='add'){const v=($('frda').value||'').replace(/[^A-Za-z0-9_]/g,'');if(v){netSend({t:'friendAdd',name:v});$('frda').value=''}}
  else if(a=='send')frdSend()};
 MB.onkeydown=e=>{if(e.key!='Enter')return;if(e.target.id=='frdi'){e.preventDefault();frdSend()}else if(e.target.id=='frda'){e.preventDefault();const v=(e.target.value||'').replace(/[^A-Za-z0-9_]/g,'');if(v){netSend({t:'friendAdd',name:v});e.target.value=''}}}}
function frdSend(){const i=$('frdi');if(!i||!FRD.open)return;const t=i.value.trim();if(!t)return;netSend({t:'pm',name:FRD.open,text:t});i.value=''}
function frdPush(name,m){(FRD.hist[name]=FRD.hist[name]||[]).push(m);if(FRD.hist[name].length>120)FRD.hist[name].shift()}
const FRDH={
 friends(m){FRD.list=m.list||[];FRD.reqs=m.reqs||[];frdBadge();frdRender()},
 fon(m){const f=FRD.list.find(q=>q.name==m.name);if(f){f.on=m.on?1:0;if(m.gone)FRD.list=FRD.list.filter(q=>q!==f)}if(f&&f.ok&&!m.gone)say('<b>'+netName(m.name)+'</b> is '+(m.on?'online.':'offline.'),'#7a2cb8');frdRender()},
 pm(m){const other=m.mine?m.to:m.from;frdPush(other,{t0:m.t0,mine:m.mine?1:0,text:m.text});
  if(m.mine)frdSay('<b>To '+netName(other)+':</b> '+esc(m.text));else{frdSay('<b>From <a href="#" class="frr" data-frr="'+esc(other)+'">'+esc(other)+'</a>'+(m.late?' (while you were away)':'')+':</b> '+esc(m.text));
   if(!(FRD.view=='thread'&&FRD.open==other&&M.style.display=='flex')){FRD.unread[other]=(FRD.unread[other]||0)+1;frdBadge()}
   const o=[...NETS.others.values()].find(q=>(NETS.info.get(q.id)||{}).name==other);if(o&&!m.late)netBubble(o,'(whispers)')}
  if(FRD.view=='thread'&&FRD.open==other)frdRender()},
 pmHist(m){const L=(m.lines||[]).map(q=>({t0:q.t0,mine:q.mine,text:q.text}));FRD.hist[m.name]=L;if(FRD.view=='thread'&&FRD.open==m.name)frdRender()}
};
$('frdb').onclick=()=>{if(MB.className=='frd'&&M.style.display=='flex')frdClose();else frdOpen(null)};
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('.frr');if(!a)return;e.preventDefault();frdOpen(a.dataset.frr)});
"""
# the handlers live next to the other net handlers, and the table dispatches them
rep("tradeCancel(m){NETS.inTrade=0;if(T2)p2pCancel(m.why||'Trade cancelled.',1)}\n};",
    "tradeCancel(m){NETS.inTrade=0;if(T2)p2pCancel(m.why||'Trade cancelled.',1)},\n"
    " friends(m){FRDH.friends(m)},fon(m){FRDH.fon(m)},pm(m){FRDH.pm(m)},pmHist(m){FRDH.pmHist(m)}\n};" + JS)

# chat commands
rep("say('Commands: /who, /trade name, /ignore name, /unignore name, /report name reason, /logout'",
    "say('Commands: /who, /friends, /add name, /accept name, /remove name, /pm name message, /trade name, /ignore name, /unignore name, /report name reason, /logout'")
rep("if(c=='who'){netSend({t:'who'});return",
    "if(c=='friends'||c=='fl'){frdOpen(null);return true}"
    "if(c=='add'&&nm){netSend({t:'friendAdd',name:nm});return true}if(c=='accept'&&nm){netSend({t:'friendYes',name:nm});return true}"
    "if((c=='decline'||c=='remove'||c=='unfriend')&&nm){netSend({t:'friendNo',name:nm});return true}"
    "if((c=='pm'||c=='w'||c=='msg'||c=='tell'||c=='whisper')&&nm){const tx=r.join(' ').trim();if(tx)netSend({t:'pm',name:nm,text:tx});else frdOpen(nm);return true}"
    "if(c=='who'){netSend({t:'who'});return")

# the name menu: Add friend / Remove friend + Message
rep("""d.innerHTML='<b>'+n+'</b><button data-pa="t">Trade</button><button data-pa="i">'+(netIgn.has(n)?'Unignore':'Ignore')+'</button><button data-pa="r">Report</button><button data-pa="x">Close</button>';""",
    """const fr_=FRD.list.find(q=>q.name==n&&q.ok);d.innerHTML='<b>'+n+'</b>'+(n==NETS.name?'':'<button data-pa="f">'+(fr_?'Remove friend':'Add friend')+'</button>'+(fr_?'<button data-pa="m">Message</button>':''))+'<button data-pa="t">Trade</button><button data-pa="i">'+(netIgn.has(n)?'Unignore':'Ignore')+'</button><button data-pa="r">Report</button><button data-pa="x">Close</button>';""")
rep("if(b=='t')netCmd('/trade '+n);if(b=='i')netCmd((netIgn.has(n)?'/unignore ':'/ignore ')+n);",
    "if(b=='t')netCmd('/trade '+n);if(b=='f')netSend({t:FRD.list.find(q=>q.name==n&&q.ok)?'friendNo':'friendAdd',name:n});if(b=='m')frdOpen(n);if(b=='i')netCmd((netIgn.has(n)?'/unignore ':'/ignore ')+n);")

open(PATH, 'w', encoding='utf-8').write(h)
print('friends patch applied')
