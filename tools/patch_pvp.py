#!/usr/bin/env python3
"""Two worlds and PvP (Albert, Nov 1: "multiple worlds... when you log in you click PvP world or the regular world").

World 1 = the normal world, World 2 = PvP: same account, same save; you only see, chat with and trade with players in
your own world. In World 2 players can fight each other anywhere outside the towns (towns and Gigachad Town are safe
zones). The server checks every hit (server/pvp.js): reach for the style, attack speed, combat levels within 15,
damage capped by saved levels, and it keeps the fighters' hitpoints, so a modified game can't cheat.
  - start screen: World 1 / World 2 picker (remembered), with the number of players online in each
  - online chip shows the world; in World 2 a badge says Safe zone / PvP zone (red) as you walk
  - name menu (tap a player's name tag or chat name): Fight (World 2 only)
  - fighting: walks into reach, attacks at the weapon's speed with your style (melee / bow / staff + the spell's effect),
    hit splats on both sides, food sends the heal to the server, a PvP death sends you to the start with nothing lost
Run after patch_vfx.py:  python3 tools/patch_pvp.py
"""
import json, os
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


TOWNS = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'server', 'towns.json')))
SAFE = json.dumps([[t['x'], t['y'], t['r']] for t in TOWNS])

JS = r"""
// ---- worlds + PvP (tools/patch_pvp.py; the server checks every hit, server/pvp.js)
const PVPW={safe:__SAFE__,t:0,last:0,seen:0,badge:null,dead:0};
const pvpWorld=()=>+(LS.get('mc_world')||1)==2?2:1;
const pvpSafe=(x,y)=>PVPW.safe.some(t=>(x-t[0])*(x-t[0])+(y-t[1])*(y-t[1])<=t[2]*t[2]);
{const ns=netSend;netSend=function(o){if(o&&(o.t=='login'||o.t=='register'||o.t=='resume'))o.world=pvpWorld();return ns(o)}}
// start screen: the world picker above the buttons
{const ms=menuScr;menuScr=function(){ms.apply(this,arguments);if(!SRV()||!SBX)return;const b=SBX.querySelector('button.big');if(!b||$('pvw'))return;
 const d=document.createElement('div');d.id='pvw';d.className='pvw';
 const draw=n=>{const w=pvpWorld();d.innerHTML=[[1,'World 1','Classic'],[2,'World 2','PvP']].map(([i,a,c])=>'<button data-w="'+i+'" class="pvwB'+(w==i?' on':'')+(i==2?' pv':'')+'"><b>'+a+'</b><span>'+c+(n&&n[i]!=null?' · '+n[i]+' online':'')+'</span></button>').join('')+'<div class="pvwT">'+(w==2?'Fight other players outside the towns. Towns are safe. Nothing drops when you lose.':'The normal world: no player fights.')+'</div>'};
 draw(null);b.before(d);d.onclick=e=>{const t=e.target.closest('[data-w]');if(!t)return;LS.set('mc_world',t.dataset.w);draw(PVPW.n)};
 try{fetch(SRV().replace(/^ws/,'http').replace(/\/ws$/,'')+'/worlds').then(r=>r.json()).then(j=>{PVPW.n={};for(const w of j.worlds)PVPW.n[w.id]=w.online;if(d.isConnected)draw(PVPW.n)}).catch(()=>{})}catch(e){}}}
{const css=document.createElement('style');css.textContent='.pvw{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px}.pvwB{flex:1 1 140px;padding:9px 8px;border:2px solid #5a4630;border-radius:8px;background:#1c140c;color:#e8d8b0;cursor:pointer;font:13px Georgia;text-align:center}.pvwB b{display:block;font:700 15px Cinzel,Georgia,serif;color:#ffd23f}.pvwB span{font-size:12px;opacity:.85}#pvw .pvwB{background:#1c140c!important;opacity:.7}#pvw .pvwB.on{opacity:1;border:3px solid #ffd23f!important;box-shadow:0 0 14px #ffd23f88!important;background:#3a2410!important}#pvw .pvwB.pv.on{border-color:#ff4a4a!important;box-shadow:0 0 14px #ff4a4a99!important;background:#4a1010!important}.pvwB.pv b{color:#ff7a6a}.pvwT{flex-basis:100%;font:12px Georgia;color:#cdbb92;text-align:center}#pvz{position:fixed;top:54px;left:50%;transform:translateX(-50%);z-index:30;padding:3px 12px;border-radius:12px;font:700 12px Cinzel,Georgia,serif;letter-spacing:1px;pointer-events:none;border:2px solid #000}#pvz.safe{background:#1f4a22;color:#c8ffb8}#pvz.pvp{background:#7a0f12;color:#ffd2c8;animation:pvzP 1.6s infinite}@keyframes pvzP{50%{box-shadow:0 0 12px #ff3a3a}}';document.head.appendChild(css)}
NETH.pvpHit=m=>{st.hp=Math.max(0,m.hp);fl(P.x,P.y,m.d,m.d?'#d22':'#39f');if(m.d)pAnim=pAnim||{k:'block',t0:performance.now(),d:400};
 if(performance.now()-PVPW.seen>15000)say(m.name+' is attacking you!','#c00');PVPW.seen=performance.now();
 if(!PVPW.t&&!act&&!path.length){PVPW.t=m.id;PVPW.t0=performance.now()}ui()};
NETH.pvpAck=m=>{const o=NETS.others.get(m.id);const ms=wSty()=='mg'?600:wSty()=='rg'?390:120;if(o)setTimeout(()=>fl(Math.round(o.px),Math.round(o.py),m.d,m.d?'#d22':'#39f'),ms)};
NETH.pvpNo=m=>{};
NETH.pvpHp=m=>{st.hp=Math.min(hpMax(),m.hp);ui()};
NETH.pvpDead=m=>{PVPW.t=0;PVPW.dead=1;st.hp=0;say('You were defeated by '+m.by+'. Nothing was taken.','#c00')};
NETH.pvpWin=m=>{PVPW.t=0;say('You defeated '+m.name+'!','#0a0')};
NETH.pvpFx=m=>{if(m.a===NETS.me||m.b===NETS.me)return;const a=NETS.others.get(m.a),b=NETS.others.get(m.b);if(!b)return;
 if(a&&m.s=='rg')FX.arrow(a.px+.5,a.py+.5,b.px+.5,b.py+.5);else if(a&&m.s=='mg')FX.spell(0,a.px+.5,a.py+.5,b.px+.5,b.py+.5);
 setTimeout(()=>fl(Math.round(b.px),Math.round(b.py),m.d,m.d?'#d22':'#39f'),m.s=='at'?120:500)};
NETH.pvpTop=m=>{say('PvP: you have '+(m.me?m.me.kills:0)+' wins, '+(m.me?m.me.deaths:0)+' losses. Top: '+(m.list.map(r=>r.name+' '+r.kills).join(', ')||'nobody yet'),'#a60')};
{const od=onDeath;onDeath=function(z){if(PVPW.dead){PVPW.dead=0;return 'You lost a PvP fight: you keep everything.'}return od.apply(this,arguments)}}
function pvpFight(name){if(pvpWorld()!=2||!NETS.on)return say('Player fights are only in World 2 (PvP). Pick it on the start screen.','#c00');
 let id=0;for(const[i,inf] of NETS.info)if(inf.name==name)id=i;if(!id||!NETS.others.get(id))return say(name+' is not nearby.','#c00');
 if(pvpSafe(P.x,P.y))return say('You are in a safe zone. Leave town to fight players.','#c00');
 act=null;PVPW.t=id;PVPW.t0=performance.now();say('Fighting '+name+'.','#a60')}
// a click or tap on the world (walking somewhere else) ends the fight
addEventListener('pointerdown',e=>{if(PVPW.t&&e.target&&e.target.tagName=='CANVAS'&&performance.now()-(PVPW.t0||0)>600)PVPW.t=0},true);
setInterval(()=>{
 if(!started)return;const w2=NETS.on&&pvpWorld()==2;
 if(!PVPW.badge){PVPW.badge=document.createElement('div');PVPW.badge.id='pvz';document.body.appendChild(PVPW.badge)}
 const sf=pvpSafe(P.x,P.y);PVPW.badge.style.display=w2?'block':'none';PVPW.badge.className=sf?'safe':'pvp';PVPW.badge.textContent=sf?'SAFE ZONE':'PvP ZONE';
 if(!PVPW.t)return;if(act||!w2||st.hp<=0){PVPW.t=0;return}
 const o=NETS.others.get(PVPW.t);if(!o){PVPW.t=0;return say('They got away.','#a60')}
 const tx=Math.round(o.px),ty=Math.round(o.py),d=Math.max(Math.abs(tx-P.x),Math.abs(ty-P.y));
 if(sf||pvpSafe(tx,ty)){PVPW.t=0;return say('That is a safe zone.','#a60')}
 if(d>rch()||d==0){if(!path.length)path=walkTo(tx,ty)||[];return}
 path=[];const s=wSty(),spd=s=='mg'?2800:2200,now=performance.now();if(now-PVPW.last<spd)return;PVPW.last=now;
 let mx=styMax();if(s=='rg'&&!bestArrow())return PVPW.t=0,say('Your quiver is empty.','#c00');if(s=='mg'&&!curSpell())return PVPW.t=0,say('Pick a spell you have the scrolls for.','#c00');
 const dmg=Math.random()<.7?Math.floor(Math.random()*(mx+1)):0;
 if(s=='mg'){castAnim();const sp=curSpell();FX.spell(SPL.indexOf(sp),P.px+.5,P.py+.5,o.px+.5,o.py+.5)}
 else if(s=='rg'){pAnim={k:'stab',t0:now,d:600};FX.arrow(P.px+.5,P.py+.5,o.px+.5,o.py+.5)}
 else pAnim={k:'slash',t0:now,d:600};
 netSend({t:'pvpHit',id:PVPW.t,s:s=='me'?'at':s,d:dmg})},200);
"""

# the code goes in before the other-players block (net code is in scope there)
rep("// other players in the world\nfunction netSelf(", JS.replace('__SAFE__', SAFE) + "// other players in the world\nfunction netSelf(")
# name menu: Fight in World 2
rep("+'<button data-pa=\"t\">Trade</button>", "+(pvpWorld()==2&&NETS.on?'<button data-pa=\"pv\" style=\"color:#ff7a6a\">Fight</button>':'')+'<button data-pa=\"t\">Trade</button>")
rep("if(b=='t')netCmd('/trade '+n);", "if(b=='pv')pvpFight(n);if(b=='t')netCmd('/trade '+n);")
# food mid-fight: the server keeps PvP hitpoints, tell it about the heal
rep("st.hp=Math.min(hpMax(),st.hp+HEAL[k]);", "st.hp=Math.min(hpMax(),st.hp+HEAL[k]);if(typeof pvpWorld=='function'&&pvpWorld()==2&&NETS.on)netSend({t:'pvpEat',h:HEAL[k]});")
open(PATH, 'w', encoding='utf-8').write(h)
print('patch_pvp: worlds + PvP added')
