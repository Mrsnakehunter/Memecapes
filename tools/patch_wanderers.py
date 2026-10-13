#!/usr/bin/env python3
"""Bots: a few dozen characters who live in the world so it never feels empty, and look like players.

Albert (Oct 13): no label on them in the game; the website says plainly that the game has bots that look like
players (FAQ "Are there bots in the game?" and the $CAPES page), and bots are never counted as players anywhere
(posts, player numbers, screenshots sold as "players online").
  - 12 social bots hang around the towns: stroll, wave, dance, cheer, chat, and greet you by name.
  - 24 working bots chop trees, fish and mine near their home town, and a few walk the roads between towns.
  - Each has a name, a level shown on the name tag, a body, a cape (many wear Skin of the Month capes), a weapon
    and their own lines.
  - They thin out as real players arrive: one bot hides for every real player nearby, and MC_CONFIG.wanderers in
    config.js sets how many there are in all (0 switches them off).
They run on each player's own screen (not on the server): they never trade, never use the Stock Market, never
block a path, and never take a monster's kill or a resource.
Run from the repo root after patch_skinstore.py:  python3 tools/patch_wanderers.py
"""
import json
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# name, body (0 male, 1 female), role, home (0 = Gigachad Town, 1.. = meme towns in TW order), cape, weapon, lines
NPCS = [
    # ---- social: in town, chatty
    ('Bramblefoot', 0, 'social', 0, 'cs_laser_grid', 'sword', ["yoo what's up", 'what am I even playing, this is awesome', 'anyone seen the castle at night? lanterns go crazy', 'gm gm gm']),
    ('Kettle Kate', 1, 'social', 0, 'cs_pond_lily', 'bstaff', ['the fountain in Gigachad Town is my favourite spot', 'tip: bank before you go fight stuff', 'I came here for the capes ngl', 'hiii']),
    ('Sir Hodlington', 0, 'social', 0, 'cape_at', 'isword', ['never selling this cape', 'a true knight trains attack to 100', 'hold the line, adventurer', 'good morrow']),
    ('Pixel Pete', 0, 'social', 0, 'cs_shades_on', 'club', ['shades on, problems gone', 'bonk.', 'has anyone tried the Meme Caves yet?', 'lol']),
    ('Mossy Meg', 1, 'social', 0, 'cs_jungle_leaves', 'axe', ['the trees by the river are the comfiest', 'I talk to the guards. they never talk back', 'nice cape!', 'what a day']),
    ('Wen Wally', 0, 'social', 1, 'cs_wen_lambo', 'sword', ['wen lambo? wen level 10 first', 'Wow Landing has the best windmill, fight me', 'yo!', 'gg']),
    ('Froggy Fran', 1, 'social', 2, 'cs_pond_lily', 'net', ['the pond is calling', 'stilt houses > normal houses', 'catch anything good?', 'ribbit (sorry)']),
    ('Chartwell', 0, 'social', 3, 'cs_stonks_arrow', 'isword', ['stonks only go up in this town', 'the Stock Market is next door, check it out', 'buy low, craft high', 'hello trader']),
    ('Diamond Di', 1, 'social', 4, 'cs_diamond_hands', 'pick', ['solo life in Diamond Hands, no trades no worries', 'these halls are so shiny', 'hey there', 'never letting go']),
    ('Ghosty Gus', 0, 'social', 5, 'cs_the_burn', 'bstaff', ['Rugpull Ridge is spooky at night', 'did you hear that?', 'the ghost waved at me. I think', 'boo']),
    ('Frosty Flo', 1, 'social', 6, 'cs_hodl_frost', 'axe', ['so cold up here, so worth it', 'HODL Heights has the best snow', 'brr', 'warm up by the fire with me']),
    ('Luna Lex', 1, 'social', 7, 'cs_moon_phases', 'bstaff', ['a town on the moon. what a time', 'the lander still works. probably', 'stars look closer from here', 'hi from the moon']),
    # ---- workers: chop, fish, mine near home; a few travel
    ('Timber Tom', 0, 'chop', 0, 'cape_wc', 'axe', ['logs logs logs', 'almost 30 woodcutting', 'timberrr']),
    ('Oakley', 1, 'chop', 1, '', 'axe', ['this oak is stubborn', 'chop chop', 'need a better axe']),
    ('Barky Bo', 0, 'chop', 2, 'cs_comfy_knit', 'axe', ['sweater weather for chopping', 'one more tree', 'my arms hurt lol']),
    ('Willow Wyn', 1, 'chop', 3, '', 'axe', ['love the sound of this', 'logs for the bank', 'woo level up']),
    ('Splinters', 0, 'chop', 0, 'cs_rug_fringe', 'axe', ['ouch', 'chop then cook, that is the way', 'ok just ten more']),
    ('Pinecone Pam', 1, 'chop', 6, 'cs_hodl_frost', 'axe', ['frosty logs hit different', 'cold hands, warm heart', 'tree #47']),
    ('Captain Cast', 0, 'fish', 2, 'cape_fi', 'net', ['the shrimp are biting', 'shh, fishing', 'caught one!']),
    ('Reel Rita', 1, 'fish', 0, 'cs_whale_waves', 'net', ['waves are perfect today', 'net full of shrimp', 'fishing is my therapy']),
    ('Gill Bill', 0, 'fish', 1, '', 'net', ['nothing yet...', 'oh wait, got one', 'patience pays']),
    ('Nets Nora', 1, 'fish', 2, 'cs_pond_lily', 'net', ['Froggo would be proud', 'this spot is mine (jk share)', 'fishy fishy']),
    ('Bait Boris', 0, 'fish', 7, 'cs_rocket_trail', 'net', ['fishing on the moon? sure', 'space shrimp, wild', 'brb cooking these']),
    ('Rocky Rae', 1, 'mine', 4, 'cs_copium_crystal', 'pick', ['copper and tin, the dream team', 'clink clink', 'ore for bars']),
    ('Dusty Dan', 0, 'mine', 0, 'cape_mi', 'pick', ['mining is honest work', 'need tin', 'pickaxe go brrr']),
    ('Pebble Pip', 1, 'mine', 3, '', 'pick', ['this rock is empty', 'found some', 'smithing next']),
    ('Gravel Greg', 0, 'mine', 5, 'cs_bonk_stripes', 'pick', ['rocks rock', 'deep breath, swing', 'ok that one was heavy']),
    ('Ore-ville', 0, 'mine', 1, 'cs_chad_marble', 'pick', ['marble cape, rocky hands', 'one more load', 'nice']),
    ('Wander Will', 0, 'travel', 0, 'cs_up_only_rainbow', 'sword', ['on my way to the next town', 'the roads are so pretty', 'grand tour time']),
    ('Roadie Roz', 1, 'travel', 1, 'cs_royal_ermine', 'isword', ['walking to Stonks City', 'the stone bridges are so nice', 'hey traveller']),
    ('Hiker Hal', 0, 'travel', 3, '', 'bstaff', ['legs tired, spirit strong', 'Meme Telly is faster but walking is vibes', 'hello!']),
    ('Scout Sky', 1, 'travel', 4, 'cs_laser_grid', 'sword', ['scouting the roads', 'saw a goblin back there', 'stay safe out there']),
    ('Bonk Buddy', 0, 'chop', 5, 'cs_bonk_stripes', 'axe', ['bonk the tree', 'logs for days', 'heh']),
    ('Tidal Tess', 1, 'fish', 6, 'cs_whale_waves', 'net', ['ice fishing!', 'brr but worth it', 'got one']),
    ('Crag Carl', 0, 'mine', 7, 'cs_moon_phases', 'pick', ['moon rocks!', 'low gravity mining', 'clank']),
    ('Leafy Lou', 1, 'chop', 4, 'cs_jungle_leaves', 'axe', ['nature is healing', 'chop chop', 'one more']),
]
EMOTES = ['Wave', 'Dance', 'GG', 'Clap', 'Yes', 'LOL', 'Shrug', 'Stonks', 'Griddy', 'Sigma']
GREET = ["yoo what's up, {n}!", 'hey {n}!', 'welcome {n}, enjoy the game', "{n}! nice to see a new face", 'gm {n}']

JS = r"""
// ---- bots (tools/patch_wanderers.py): characters who live in the world (the website FAQ says the game has bots); one hides per real player nearby
const WNDD=""" + json.dumps(NPCS) + ",WNDE=" + json.dumps(EMOTES) + ",WNDG=" + json.dumps(GREET) + r""";
const WND=[];let WNDok=0,WNDtalk=0;const WNDtag=new Map();
const wndN=()=>{const c=window.MC_CONFIG&&MC_CONFIG.wanderers;return c==null?WNDD.length:Math.max(0,Math.min(WNDD.length,c|0))};
function wndRng(s){return()=>{s=(s*1103515245+12345)&0x7fffffff;return s/0x7fffffff}}
function wndHome(i){if(!i)return[(GT.x0+GT.x1)/2|0,(GT.y0+GT.y1)/2|0];const t=TW[(i-1)%TW.length];return[t.cx|0,t.cy|0]}
function wndFree(x,y,r,R){for(let k=0;k<80;k++){const a=R()*6.283,d=R()*r,tx=Math.round(x+Math.cos(a)*d),ty=Math.round(y+Math.sin(a)*d);if(!solid(tx,ty))return[tx,ty]}return[x,y]}
function wndInit(){WNDok=1;WNDD.forEach((d,i)=>{const R=wndRng(7919*(i+3)),hm=wndHome(d[3]),p=wndFree(hm[0],hm[1],d[2]=='social'?7:12,R);
 WND.push({i,id:'wnd'+i,lv:3+((R()*55)|0),n:d[0],g:d[1],role:d[2],home:d[3],hm,cape:d[4],w:d[5],lines:d[6],R,x:p[0],y:p[1],px:p[0],py:p[1],r:R()*6.283,path:[],st:'idle',until:0,emo:null,next:performance.now()+8000+R()*40000,greet:0,act:null})})}
// a short walk: breadth-first search inside a box around the start (never far, never through walls or water)
const WNDP=new Int32Array(W*H).fill(-1);
function wndPath(sx,sy,goal,box){const s=sy*W+sx,q=[s],seen=[s];WNDP[s]=s;let f=-1;
 for(let h=0;h<q.length&&h<6000;h++){const c=q[h],x=c%W,y=(c/W)|0;if(goal(x,y)){f=c;break}for(const[dx,dy]of DIRS){const nx=x+dx,ny=y+dy;if(Math.abs(nx-sx)>box||Math.abs(ny-sy)>box||solid(nx,ny))continue;if(dx&&dy&&(solid(x+dx,y)||solid(x,y+dy)))continue;const k=ny*W+nx;if(WNDP[k]>=0)continue;WNDP[k]=c;seen.push(k);q.push(k)}}
 const p=[];if(f>=0){while(f!=s){p.unshift([f%W,(f/W)|0]);f=WNDP[f]}}for(const k of seen)WNDP[k]=-1;return p}
function wndNear(list,x,y,r){let b=null,bd=r*r;for(const o of list){if(o.gone||o.dead)continue;const d=(o.x-x)**2+(o.y-y)**2;if(d<bd){bd=d;b=o}}return b}
const WNDA={chop:['Chop','axe',()=>trees],fish:['Fish','net',()=>fish],mine:['Mine','pick',()=>rocks]};
function wndPlan(o,now){const R=o.R;o.act=null;o.emo=null;
 if(o.role=='social'){if(R()<.35){o.st='emote';o.emo={n:WNDE[(R()*WNDE.length)|0],t0:now};o.until=now+3500+R()*2500;return}
  const t=wndFree(o.hm[0],o.hm[1],9,R);o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>x==t[0]&&y==t[1],16);o.st=o.path.length?'walk':'idle';o.until=now+4000+R()*9000;return}
 if(o.role=='travel'){const k=1+((R()*TW.length)|0),t=wndHome(R()<.25?0:k);const dx=t[0]-o.x,dy=t[1]-o.y,L=Math.hypot(dx,dy)||1,s=Math.min(40,L),gx=Math.round(o.x+dx/L*s),gy=Math.round(o.y+dy/L*s);
  o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>Math.abs(x-gx)<=3&&Math.abs(y-gy)<=3,44);o.st=o.path.length?'walk':'idle';o.until=now+2000+R()*6000;if(!o.path.length)o.hm=wndHome(k);return}
 const A=WNDA[o.role],res=wndNear(A[2](),o.hm[0]+(R()-.5)*16,o.hm[1]+(R()-.5)*16,30);
 if(res){o.act=res;o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>Math.max(Math.abs(x-res.x),Math.abs(y-res.y))==1,34);if(o.path.length||Math.max(Math.abs(o.x-res.x),Math.abs(o.y-res.y))<=1.5){o.st=o.path.length?'walk':'work';o.until=now+25000+R()*50000;return}}
 const t=wndFree(o.hm[0],o.hm[1],10,R);o.path=wndPath(Math.round(o.x),Math.round(o.y),(x,y)=>x==t[0]&&y==t[1],16);o.st=o.path.length?'walk':'idle';o.until=now+5000+R()*8000}
function wndSay(o,txt){const t=String(txt).replace('{n}',(st.acct&&st.acct.name)||'adventurer');netBubble(o,t);say('<b>'+esc(o.n)+':</b> '+esc(t),'#1a1aa0')}
function wndTick(now){if(!started)return;if(!WNDok){if(!trees||!trees.length||!TW||!TW.length)return;wndInit()}
 const dt=Math.min(.1,(now-(wndTick.lt||now))/1000);wndTick.lt=now;
 const real=(NETS.on&&NETS.others)?NETS.others.size:0,N=Math.max(0,wndN()-real);
 WND.forEach((o,k)=>{const on=k<N,near=Math.abs(o.x-P.px)<90&&Math.abs(o.y-P.py)<90;
  if(!on||!near){wndTagDel(o);return}
  // move along the path
  if(o.st=='walk'&&o.path.length){const n=o.path[0],dx=n[0]-o.x,dy=n[1]-o.y,L=Math.hypot(dx,dy),sp=2.3*dt;
   if(L<=sp){o.x=n[0];o.y=n[1];o.path.shift()}else{o.x+=dx/L*sp;o.y+=dy/L*sp}
   o.tr=Math.atan2(dx,dy);if(!o.path.length){if(o.act){o.st='work'}else o.st='idle'}}
  if(o.st=='work'&&o.act){o.tr=Math.atan2(o.act.x-o.x,o.act.y-o.y);if(o.act.gone||o.act.dead)o.until=0}
  if(o.tr!=null){let dr=o.tr-o.r;dr=Math.atan2(Math.sin(dr),Math.cos(dr));o.r+=dr*Math.min(1,dt*8)}
  o.px=o.x;o.py=o.y;
  if(now>o.until&&o.st!='walk')wndPlan(o,now);
  // talk: greet a player who comes close, and now and then say one of their own lines (never more than one bot every few seconds)
  const dp=Math.hypot(o.x-P.px,o.y-P.py);
  if(dp<6&&now-o.greet>600000&&now-WNDtalk>6000&&o.role=='social'){o.greet=now;WNDtalk=now;wndSay(o,WNDG[(o.R()*WNDG.length)|0]);if(o.st!='walk'){o.st='emote';o.emo={n:'Wave',t0:now};o.until=now+3000;o.tr=Math.atan2(P.px-o.x,P.py-o.y)}}
  else if(dp<14&&now>o.next&&now-WNDtalk>22000){WNDtalk=now;o.next=now+(o.role=='social'?60000:120000)+o.R()*120000;wndSay(o,o.lines[(o.R()*o.lines.length)|0])}
  if(Math.abs(o.x-P.px)>40||Math.abs(o.y-P.py)>40){wndTagDel(o);return}
  wndDraw(o,now);wndTagSet(o)})}
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
print("bots patch applied:", len(NPCS))
