#!/usr/bin/env python3
"""Bots: a few dozen characters who live in the world so it never feels empty, and look like players.

Albert (Oct 13): no label on them in the game; the website says plainly that the game has bots that look like
players (FAQ "Are there bots in the game?" and the $CAPES page), and bots are never counted as players anywhere
(posts, player numbers, screenshots sold as "players online").
  - 12 social bots hang around the towns: stroll, wave, dance, cheer, chat, and greet you by name.
  - 24 working bots chop trees, fish and mine near their home town, and a few walk the roads between towns.
  - Each has a name, a level shown on the name tag, a body, a cape (many wear Skin of the Month capes), a weapon
    and their own lines (tools/wanderer_lines.py: 1,000+ lines, all different; each bot says all of its lines in a
    shuffled order before any comes round again, at random moderate gaps).
  - They thin out as real players arrive: one bot hides for every real player nearby, and MC_CONFIG.wanderers in
    config.js sets how many there are in all (0 switches them off).
They run on each player's own screen (not on the server): they never trade, never use the Stock Market, never
block a path, and never take a monster's kill or a resource.
Run from the repo root after patch_skinstore.py:  python3 tools/patch_wanderers.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wanderer_lines import LINES, GREET
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# name, body (0 male, 1 female), role, home (0 = Gigachad Town, 1.. = meme towns in TW order), cape, weapon (lines: tools/wanderer_lines.py)
NPCS = [
    # ---- social: in town, chatty
    ('Bramblefoot', 0, 'social', 0, 'cs_laser_grid', 'sword'),
    ('Kettle Kate', 1, 'social', 0, 'cs_pond_lily', 'bstaff'),
    ('Sir Hodlington', 0, 'social', 5, 'cape_at', 'isword'),
    ('Pixel Pete', 0, 'social', 3, 'cs_shades_on', 'club'),
    ('Mossy Meg', 1, 'social', 6, 'cs_jungle_leaves', 'axe'),
    ('Wen Wally', 0, 'social', 1, 'cs_wen_lambo', 'sword'),
    ('Froggy Fran', 1, 'social', 2, 'cs_pond_lily', 'net'),
    ('Chartwell', 0, 'social', 3, 'cs_stonks_arrow', 'isword'),
    ('Diamond Di', 1, 'social', 4, 'cs_diamond_hands', 'pick'),
    ('Ghosty Gus', 0, 'social', 5, 'cs_the_burn', 'bstaff'),
    ('Frosty Flo', 1, 'social', 6, 'cs_hodl_frost', 'axe'),
    ('Luna Lex', 1, 'social', 7, 'cs_moon_phases', 'bstaff'),
    # ---- workers: chop, fish, mine near home; a few travel
    ('Timber Tom', 0, 'chop', 0, 'cape_wc', 'axe'),
    ('Oakley', 1, 'chop', 1, '', 'axe'),
    ('Barky Bo', 0, 'chop', 2, 'cs_comfy_knit', 'axe'),
    ('Willow Wyn', 1, 'chop', 3, '', 'axe'),
    ('Splinters', 0, 'chop', 7, 'cs_rug_fringe', 'axe'),
    ('Pinecone Pam', 1, 'chop', 6, 'cs_hodl_frost', 'axe'),
    ('Captain Cast', 0, 'fish', 2, 'cape_fi', 'net'),
    ('Reel Rita', 1, 'fish', 0, 'cs_whale_waves', 'net'),
    ('Gill Bill', 0, 'fish', 1, '', 'net'),
    ('Nets Nora', 1, 'fish', 2, 'cs_pond_lily', 'net'),
    ('Bait Boris', 0, 'fish', 7, 'cs_rocket_trail', 'net'),
    ('Rocky Rae', 1, 'mine', 4, 'cs_copium_crystal', 'pick'),
    ('Dusty Dan', 0, 'mine', 2, 'cape_mi', 'pick'),
    ('Pebble Pip', 1, 'mine', 3, '', 'pick'),
    ('Gravel Greg', 0, 'mine', 5, 'cs_bonk_stripes', 'pick'),
    ('Ore-ville', 0, 'mine', 1, 'cs_chad_marble', 'pick'),
    ('Wander Will', 0, 'travel', 0, 'cs_up_only_rainbow', 'sword'),
    ('Roadie Roz', 1, 'travel', 1, 'cs_royal_ermine', 'isword'),
    ('Hiker Hal', 0, 'travel', 3, '', 'bstaff'),
    ('Scout Sky', 1, 'travel', 4, 'cs_laser_grid', 'sword'),
    ('Bonk Buddy', 0, 'chop', 5, 'cs_bonk_stripes', 'axe'),
    ('Tidal Tess', 1, 'fish', 6, 'cs_whale_waves', 'net'),
    ('Crag Carl', 0, 'mine', 7, 'cs_moon_phases', 'pick'),
    ('Leafy Lou', 1, 'chop', 4, 'cs_jungle_leaves', 'axe'),
]
EMOTES = ['Wave', 'Dance', 'GG', 'Clap', 'Yes', 'LOL', 'Shrug', 'Stonks', 'Griddy', 'Sigma']
assert sorted(LINES) == sorted(n[0] for n in NPCS), 'every bot needs its lines in tools/wanderer_lines.py'
_all = [l.strip().lower() for v in LINES.values() for l in v] + [g.lower() for g in GREET]
assert len(_all) == len(set(_all)), 'two lines are the same: ' + str([l for l in set(_all) if _all.count(l) > 1])
assert sum(len(v) for v in LINES.values()) >= 1000 and min(len(v) for v in LINES.values()) >= 25, 'need 1000+ lines, 25+ per bot'
NPCS = [n + (LINES[n[0]],) for n in NPCS]

JS = r"""
// ---- bots (tools/patch_wanderers.py): characters who live in the world (the website FAQ says the game has bots); one hides per real player nearby
const WNDD=""" + json.dumps(NPCS) + ",WNDE=" + json.dumps(EMOTES) + ",WNDG=" + json.dumps(GREET) + r""";
const WND=[];let WNDok=0,WNDtalk=0,WNDlast=0;const WNDtag=new Map();
// every bot works through all of its own lines in a shuffled order before it repeats any (kept between visits), then reshuffles
let WNDsv={};try{WNDsv=JSON.parse(localStorage.getItem('mcWndSaid')||'{}')||{}}catch(e){}
function wndOrder(n,seed){const a=[];for(let i=0;i<n;i++)a.push(i);let s=seed|0;for(let i=n-1;i>0;i--){s=(Math.imul(s,1664525)+1013904223)|0;const j=((s>>>8)%(i+1));const t=a[i];a[i]=a[j];a[j]=t}return a}
function wndNext(key,list){let s=WNDsv[key];if(!Array.isArray(s)||s[2]!==list.length||s[1]>=list.length)s=[1+((Math.random()*2e9)|0),0,list.length];
 const t=list[wndOrder(list.length,s[0])[s[1]]];s[1]++;WNDsv[key]=s;try{localStorage.setItem('mcWndSaid',JSON.stringify(WNDsv))}catch(e){}return t}
const wndN=()=>{const c=window.MC_CONFIG&&MC_CONFIG.wanderers;return c==null?WNDD.length:Math.max(0,Math.min(WNDD.length,c|0))};
function wndRng(s){return()=>{s=(s*1103515245+12345)&0x7fffffff;return s/0x7fffffff}}
function wndHome(i){if(!i)return[(GT.x0+GT.x1)/2|0,(GT.y0+GT.y1)/2|0];const t=TW[(i-1)%TW.length];return[t.cx|0,t.cy|0]}
function wndFree(x,y,r,R){for(let k=0;k<80;k++){const a=R()*6.283,d=R()*r,tx=Math.round(x+Math.cos(a)*d),ty=Math.round(y+Math.sin(a)*d);if(!solid(tx,ty))return[tx,ty]}return[x,y]}
function wndInit(){WNDok=1;WNDD.forEach((d,i)=>{const R=wndRng(7919*(i+3)),hm=wndHome(d[3]),p=wndFree(hm[0],hm[1],d[2]=='social'?13:14,R);
 WND.push({i,id:'wnd'+i,lv:3+((R()*55)|0),n:d[0],g:d[1],role:d[2],home:d[3],hm,cape:d[4],w:d[5],lines:d[6],R,x:p[0],y:p[1],px:p[0],py:p[1],r:R()*6.283,path:[],st:'idle',until:0,emo:null,next:performance.now()+15000+Math.random()*75000,greet:-1e9,act:null})})}
// a short walk: breadth-first search inside a box around the start (never far, never through walls or water)
const WNDP=new Int32Array(W*H).fill(-1);
function wndPath(sx,sy,goal,box){const s=sy*W+sx,q=[s],seen=[s];WNDP[s]=s;let f=-1;
 for(let h=0;h<q.length&&h<6000;h++){const c=q[h],x=c%W,y=(c/W)|0;if(goal(x,y)){f=c;break}for(const[dx,dy]of DIRS){const nx=x+dx,ny=y+dy;if(Math.abs(nx-sx)>box||Math.abs(ny-sy)>box||solid(nx,ny))continue;if(dx&&dy&&(solid(x+dx,y)||solid(x,y+dy)))continue;const k=ny*W+nx;if(WNDP[k]>=0)continue;WNDP[k]=c;seen.push(k);q.push(k)}}
 const p=[];if(f>=0){while(f!=s){p.unshift([f%W,(f/W)|0]);f=WNDP[f]}}for(const k of seen)WNDP[k]=-1;return p}
function wndNear(list,x,y,r){let b=null,bd=r*r;for(const o of list){if(o.gone||o.dead)continue;const d=(o.x-x)**2+(o.y-y)**2;if(d<bd){bd=d;b=o}}return b}
const WNDA={chop:['Chop','axe',()=>trees],fish:['Fish','net',()=>fish],mine:['Mine','pick',()=>rocks]};
function wndPlan(o,now){const R=o.R;o.act=null;o.emo=null;
 if(o.role=='social'){if(R()<.3){o.st='emote';o.emo={n:WNDE[(R()*WNDE.length)|0],t0:now};o.until=now+3500+R()*2500;return}
  if(R()<.35){o.st='idle';o.tr=R()*6.283;o.until=now+8000+R()*14000;return}
  const t=wndFree(o.hm[0],o.hm[1],16,R);o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>x==t[0]&&y==t[1],30);o.st=o.path.length?'walk':'idle';o.until=now+9000+R()*16000;return}
 if(o.role=='travel'){const k=1+((R()*TW.length)|0),t=wndHome(R()<.25?0:k);const dx=t[0]-o.x,dy=t[1]-o.y,L=Math.hypot(dx,dy)||1,s=Math.min(40,L),gx=Math.round(o.x+dx/L*s),gy=Math.round(o.y+dy/L*s);
  o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>Math.abs(x-gx)<=3&&Math.abs(y-gy)<=3,44);o.st=o.path.length?'walk':'idle';o.until=now+2000+R()*6000;if(!o.path.length)o.hm=wndHome(k);return}
 const A=WNDA[o.role],res=wndNear(A[2](),o.hm[0]+(R()-.5)*16,o.hm[1]+(R()-.5)*16,30);
 if(res){o.act=res;o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>Math.max(Math.abs(x-res.x),Math.abs(y-res.y))==1,34);if(o.path.length||Math.max(Math.abs(o.x-res.x),Math.abs(o.y-res.y))<=1.5){o.st=o.path.length?'walk':'work';o.until=now+25000+R()*50000;return}}
 const t=wndFree(o.hm[0],o.hm[1],10,R);o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>x==t[0]&&y==t[1],16);o.st=o.path.length?'walk':'idle';o.until=now+5000+R()*8000}
function wndSay(o,txt){const t=String(txt).replace('{n}',(st.acct&&st.acct.name)||'adventurer');netBubble(o,t);say('<b>'+esc(o.n)+':</b> '+esc(t),'#1a1aa0')}
function wndTick(now){if(!started)return;if(!WNDok){if(!trees||!trees.length||!TW||!TW.length)return;wndInit()}
 const dt=Math.min(.1,(now-(wndTick.lt||now))/1000);wndTick.lt=now;
 const real=(NETS.on&&NETS.others)?NETS.others.size:0,N=Math.max(0,wndN()-real);
 const cand=[];WND.forEach((o,k)=>{const on=k<N,near=Math.abs(o.x-P.px)<90&&Math.abs(o.y-P.py)<90;
  if(!on||!near){wndTagDel(o);return}
  // move along the path
  if(o.st=='walk'&&o.path.length){const n=o.path[0],dx=n[0]-o.x,dy=n[1]-o.y,L=Math.hypot(dx,dy),sp=2.3*dt;
   if(L<=sp){o.x=n[0];o.y=n[1];o.path.shift()}else{o.x+=dx/L*sp;o.y+=dy/L*sp}
   o.tr=Math.atan2(dx,dy);if(!o.path.length){if(o.act){o.st='work'}else o.st='idle'}}
  if(o.st=='work'&&o.act){o.tr=Math.atan2(o.act.x-o.x,o.act.y-o.y);if(o.act.gone||o.act.dead)o.until=0}
  if(o.tr!=null){let dr=o.tr-o.r;dr=Math.atan2(Math.sin(dr),Math.cos(dr));o.r+=dr*Math.min(1,dt*8)}
  o.px=o.x;o.py=o.y;
  if(now>o.until&&o.st!='walk')wndPlan(o,now);
  // talk: greet a player who comes close; now and then one bot nearby, picked at random, says its next line. Random gaps: 25-55 s between any two
  // lines, 1.5-5 min before the same bot speaks again (social bots a little more often)
  const dp=Math.hypot(o.x-P.px,o.y-P.py);
  if(dp<6&&now-o.greet>600000&&now-WNDlast>8000&&o.role=='social'){o.greet=now;WNDlast=now;WNDtalk=Math.max(WNDtalk,now+12000+Math.random()*10000);wndSay(o,wndNext('~greet',WNDG));if(o.st!='walk'){o.st='emote';o.emo={n:'Wave',t0:now};o.until=now+3000;o.tr=Math.atan2(P.px-o.x,P.py-o.y)}}
  else if(dp<14&&now>o.next&&now>WNDtalk)cand.push(o);
  if(Math.abs(o.x-P.px)>40||Math.abs(o.y-P.py)>40){wndTagDel(o);return}
  wndDraw(o,now);wndTagSet(o)});
 if(cand.length&&now>WNDtalk){const o=cand[(Math.random()*cand.length)|0];WNDlast=now;WNDtalk=now+25000+Math.random()*30000;o.next=now+(o.role=='social'?90000:120000)+Math.random()*180000;wndSay(o,wndNext(o.n,o.lines))}}
function wndDraw(o,now){const K=o.g?'playerf':'player';needMdl(K);const sk=o.cape&&o.cape.startsWith('cs_')?o.cape:null,ck=sk?'cape_npc':o.cape;
 const CB=ck&&st.body!==0?capeBody(K,ck,sk):null,PM=CB||((MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player);if(!PM||!PM.ok)return;
 let cl=null,t=now/1000+o.i*.37,wk='w_'+o.w;
 if(o.st=='walk')cl='Walking';
 else if(o.st=='work'&&o.act){cl=WNDA[o.role][0];wk='w_'+WNDA[o.role][1]}
 else if(o.st=='emote'&&o.emo&&PM.clips[o.emo.n]){cl=o.emo.n;t=(now-o.emo.t0)/1000;const c=PM.clips[cl];if(c&&c.nf&&t>(c.nf-1)/c.fps){o.emo=null;o.st='idle'}}
 if(!cl||!PM.clips[cl])cl=PM.clips.Idle?'Idle':null;
 const x=o.x+.5,z=o.y+.5;YO=hgt(x,z);qMdl(PM,x,0,z,o.r,MDLSC.player,cl,t);
 if(WAV.has(wk))qHold(PM,x,z,o.r,cl,t,wk,false,null,heldTilt(cl,t,wk));YO=0}
function wndTagSet(o){let d=WNDtag.get(o.id);if(!d){d=document.createElement('div');d.className='ntag';d.textContent=o.n+' (lvl '+o.lv+')';document.body.appendChild(d);WNDtag.set(o.id,d)}
 const p=[o.x+.5-E[0],2.05+hgt(o.x+.5,o.y+.5)-E[1],o.y+.5-E[2]],zz=d3(p,Fw);if(zz<=0){d.style.display='none';return}
 const sx=d3(p,Rt)/(zz*TH*asp),sy=d3(p,Up)/(zz*TH);d.style.display=(Math.abs(sx)>1.1||Math.abs(sy)>1.1||zz>34)?'none':'block';d.style.left=((sx+1)/2*CW)+'px';d.style.top=((1-sy)/2*CH)+'px'}
function wndTagDel(o){const d=WNDtag.get(o.id);if(d){d.remove();WNDtag.delete(o.id)}}
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", JS + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){")
# drawn every frame with the town guards
rep("else person('k',a[0],a[1],a[2]||0,1,0,0,1);YO=0});",
    "else person('k',a[0],a[1],a[2]||0,1,0,0,1);YO=0});wndTick(performance.now());")

open(PATH, 'w', encoding='utf-8').write(h)
print("bots patch applied:", len(NPCS), "bots,", sum(len(n[6]) for n in NPCS), "lines,", len(GREET), "greetings")
