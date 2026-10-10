#!/usr/bin/env python3
"""Chapter 1, The Great Rug: the five launch story quests.

  1 Much Wow, Such Cake  Chef Bagholder (Gigachad Town kitchen): an egg, a bucket of milk, a pot of flour.
  2 Wallet Not Found     Froggo: three forgetful Wojaks each remember one word of your seed phrase.
  3 Touch Grass          Farmer Ted (allotments by the castle): plant a potato, send 4 Doomscrollers outside.
  4 The Fish Are Rugged  Fisherwoman Nemo (Froggo's Pond, Fishing 5): search the shallows for the drain plug.
  5 Feels Bad, Man       Froggo (after 1 to 4): the Bot Captain and his Spam Bots attack the castle gate.

New NPCs reuse models already in the game. The quest card and gold arrow of the starter guide
(tools/patch_guide.py) carry on with the current quest step after the guide is done, so the
player always knows where to go next. The old first quest "The Great Rug" is renamed "Proof of Work"
so the chapter can carry the name. The Quest cape now needs the chapter too.
Run from the repo root after patch_guide.py:  python3 tools/patch_story.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- items
rep("moonamu:['Moon amulet','chain','#e8e8d0','It almost went to the moon.',3,0,0,0,2,'neck']};",
    "moonamu:['Moon amulet','chain','#e8e8d0','It almost went to the moon.',3,0,0,0,2,'neck'],"
    "egg:['Egg','veg','#f3ecd8','A fresh egg. Probably.',0],milk:['Bucket of milk','potion','#f6f6f2','Udderly fresh.',0],"
    "flour:['Pot of flour','sack','#efe6d0','Finely ground. Bought at the top.',0],"
    "seedp:['Seed phrase scroll','scroll','#e8d9a8','Hodl. Wen. Lambo. Never show this to anyone. Especially not a Ratio Knight.',1],"
    "plug:['Drain plug','gem','#5a5a66','A plug with a tiny Rugpuller sigil on it. This is where the Liquidity went.',1],"
    "cfrag1:['Cape fragment (Feels)','cape','#2e8b3a','One third of the Feels Cape. It hums, softly and sadly.',3]};")
# ---- the bots that attack the gate (only ever spawned by the quest)
rep("ratio'd the kingdom.\",{boss:1,spd:4,h:3.9,lt:[['rshard',1],['rarmor',.05],['rshield',.1]]}]];",
    "ratio'd the kingdom.\",{boss:1,spd:4,h:3.9,lt:[['rshard',1],['rarmor',.05],['rshield',.1]]}],"
    "['botcap','Bot Captain',14,96,16,10,'reboot',4,[20,40],'Captain of the spam army. Beep boop, you have been rugged.',{q:1,h:2.6,bl:['BEEP BOOP','You have been selected!','Click here for free coins','Your wallet has been rugged']}],"
    "['spambot','Spam Bot',4,28,7,3,'crisis',3,[1,3],'It wants to tell you about a great opportunity.',{q:1,h:2.1,bl:['FREE AIRDROP','DM me','100x guaranteed','gm gm gm']}]];")
rep("const ORDT=[...MT.keys()].filter(i=>!MT[i].boss)", "const ORDT=[...MT.keys()].filter(i=>!MT[i].boss&&!MT[i].q)")
rep("'k:chill':'doge'},MSK={bonk:.62,wif:.9,chill:.95}", "'k:chill':'doge','k:botcap':'cult','k:spambot':'doom'},MSK={bonk:.62,wif:.9,chill:.95,botcap:1.2,spambot:.85}")
# the old first quest gives its name to the chapter
rep("MDLSC={player:1,frogw:1,", "MDLSC={player:1,playerf:1,frogw:1,")
rep("QD=[{n:'The Great Rug',t:-1,", "QD=[{n:'Proof of Work',t:-1,")

# ---- people and things in the world (made with the other extra world objects, before the world is indexed)
WORLD = r"""
{const SQO=window.SQO={sc:[],sh:[]},S0={x:CA.gx+1,y:CA.y+CA.h+2};const near=(x,y,r)=>fN(Math.round(x),Math.round(y),r||8);
 const kit=HS.find(o=>o.mk=='b_kitchen');{const p=kit?near(kit.nt[0]+1,kit.nt[1]+1):near(S0.x-14,S0.y+4);SQO.chef=xo(p[0],p[1],'sq_chef',{nm:'Chef Bagholder',ry:0})}
 [[S0.x+7,S0.y+5],[TW[0].cx+4,TW[0].cy-6],[CA.x+CA.w+3,CA.y+CA.h+9]].forEach((a,i)=>{const p=near(a[0],a[1]);SQO['w'+(i+1)]=xo(p[0],p[1],'sq_w'+(i+1),{nm:'Forgetful Wojak',ry:i*2.1})});
 {const bx=CA.x-9,by=CA.y+CA.h+4,p=near(bx-3,by+1);SQO.farmer=xo(p[0],p[1],'sq_farmer',{nm:'Farmer Ted',ry:1.57});[[bx+5,by-1],[bx+5,by+4],[bx-2,by+5],[bx+1,by+6]].forEach((a,i)=>{const q=near(a[0],a[1]);const o=xo(q[0],q[1],'sq_scroll',{nm:'Doomscroller',si:i,ry:i*1.6});if(o){o.hide=()=>!!(st.sqf&&st.sqf['sc'+i]);SQO.sc.push(o)}})}
 {const W=TW[0];let p=near(W.cx+7,W.cy-4);SQO.nest=xo(p[0],p[1],'sq_nest',{nm:'Hay nest'});p=near(W.cx-7,W.cy+5);SQO.churn=xo(p[0],p[1],'sq_churn',{nm:'Butter churn'});
  const mill=HS.concat(SB).filter(o=>o.mk=='b_windmill').sort((a,b)=>Math.hypot(a.cx-W.cx,a.cz-W.cy)-Math.hypot(b.cx-W.cx,b.cz-W.cy))[0];p=mill?near(mill.nt?mill.nt[0]+1:mill.cx+3,mill.nt?mill.nt[1]:mill.cz+3):near(W.cx+2,W.cy+8);SQO.flour=xo(p[0],p[1],'sq_flour',{nm:'Flour sacks'})}
 {const F=TW[1],sp=fish.filter(f=>!f.gone).sort((a,b)=>Math.hypot(a.x-F.cx,a.y-F.cy)-Math.hypot(b.x-F.cx,b.y-F.cy));const f0=sp[0]||{x:F.cx,y:F.cy};let p=near(f0.x,f0.y+1,6);SQO.nemo=xo(p[0],p[1],'sq_nemo',{nm:'Fisherwoman Nemo',ry:3.14});
  const used=[];for(const f of sp){if(SQO.sh.length>=3)break;if(f===f0||used.some(u=>Math.hypot(u.x-f.x,u.y-f.y)<6))continue;used.push(f);const q=near(f.x,f.y,4);const o=xo(q[0],q[1],'sq_shallow',{nm:'Muddy shallows',hi:SQO.sh.length});if(o)SQO.sh.push(o)}
  while(SQO.sh.length<3){const q=near(F.cx+SQO.sh.length*5-5,F.cy+9);const o=xo(q[0],q[1],'sq_shallow',{nm:'Muddy shallows',hi:SQO.sh.length});if(!o)break;SQO.sh.push(o)}}}
"""
rep("xo(...fN(CX-7,CY+6),'saw');", "xo(...fN(CX-7,CY+6),'saw');" + WORLD)

# ---- how they look
rep("const DYNXO={trader:'trader',fdoge:'frostdoge',slayer:'bonkwell'}",
    "const DYNXO={trader:'trader',fdoge:'frostdoge',slayer:'bonkwell',sq_chef:'chefdoge',sq_w1:'wojak',sq_w2:'wojak',sq_w3:'wojak',sq_farmer:'cobbler',sq_nemo:'playerf',sq_scroll:'doom'}")
rep("for(const o of window.__dxo){if(!vis(o.x+.5,o.y+.5,45))continue;", "for(const o of window.__dxo){if(!vis(o.x+.5,o.y+.5,45)||(o.hide&&o.hide()))continue;")
rep("const XDRAW={altar:o=>{",
    "const XDRAW={sq_nest:o=>{const x=o.x+.5,z=o.y+.5;ball(x,.14,z,.42,.18,.42,0,'#d8b45a',7);ball(x-.08,.3,z,.1,.13,.1,0,'#f3ecd8',6);ball(x+.1,.28,z+.06,.09,.12,.09,0,'#efe6d0',6)},"
    "sq_churn:o=>{const x=o.x+.5,z=o.y+.5;tube([x,0,z],[x,.75,z],.26,.2,'#8a5a2b',8,1);tube([x,.75,z],[x,1.15,z],.03,.03,'#5a3a1a',4,0);boxR(x+.45,.15,z,.3,.3,.3,0,'#9aa0a8')},"
    "sq_flour:o=>{const x=o.x+.5,z=o.y+.5;ball(x-.18,.3,z,.3,.32,.26,0,'#efe6d0',7);ball(x+.22,.26,z+.1,.26,.28,.24,0,'#e6dcc2',7);ball(x,.3,z-.25,.24,.27,.22,0,'#f2ead6',7)},"
    "sq_shallow:o=>{const x=o.x+.5,z=o.y+.5;ball(x,.02,z,.46,.02,.46,0,'#5a4a32',8);ball(x+.1,.05,z-.08,.16,.04,.12,0,'#7a6a4a',6)},"
    "altar:o=>{")
rep("const LBL={tree:['Chop down','Tree'],",
    "const LBL={sq_chef:['Talk to','Chef Bagholder'],sq_w1:['Talk to','Forgetful Wojak'],sq_w2:['Talk to','Forgetful Wojak'],sq_w3:['Talk to','Forgetful Wojak'],sq_farmer:['Talk to','Farmer Ted'],sq_nemo:['Talk to','Fisherwoman Nemo'],sq_scroll:['Talk to','Doomscroller'],sq_nest:['Search','Hay nest'],sq_churn:['Use','Butter churn'],sq_flour:['Take from','Flour sacks'],sq_shallow:['Search','Muddy shallows'],tree:['Chop down','Tree'],")
rep("const EXM={altar:", "const EXM={sq_chef:'The castle chef. He bought all the ingredients at the top.',sq_farmer:'Farmer Ted. His field is full of people looking at phones.',sq_nemo:'Fisherwoman Nemo. The fish are gone and so is her patience.',sq_scroll:'Has not looked up since 2021.',sq_nest:'A nest in the hay.',sq_churn:'A butter churn with a bucket beside it.',sq_flour:'Sacks of flour from the windmill.',sq_shallow:'Muddy shallows. Something might be down there.',sq_w1:'He has forgotten something important.',sq_w2:'He has forgotten something important.',sq_w3:'He has forgotten something important.',altar:")
rep("const XA={altar:", "const XA={sq_chef:o=>sqTalk('chef',o),sq_w1:o=>sqTalk('w1',o),sq_w2:o=>sqTalk('w2',o),sq_w3:o=>sqTalk('w3',o),sq_farmer:o=>sqTalk('farmer',o),sq_nemo:o=>sqTalk('nemo',o),sq_scroll:o=>sqTalk('scroll',o),sq_nest:o=>sqTalk('nest',o),sq_churn:o=>sqTalk('churn',o),sq_flour:o=>sqTalk('flour',o),sq_shallow:o=>sqTalk('shallow',o),altar:")

# ---- Froggo also gives the chapter's quests 2 and 5
rep("MB.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{const a=b.dataset.q.split(':'),i=+a[1];M.style.display='none';",
    "MB.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{const a=b.dataset.q.split(':'),i=+a[1];M.style.display='none';if(a[0]=='sq'){sqTalk('froggo:'+a[1]);return}")
rep("function QUESTH(){let h='<h2>Froggo</h2>';", "function QUESTH(){return QUESTH0()+sqFroggoBtns()}function QUESTH0(){let h='<h2>Froggo</h2>';")
rep("function QSH(){", "function QSH(){return QSH0()+SQH()}function QSH0(){")
rep("qdone=QD.every((q,i)=>st.qs[i]==3)", "qdone=QD.every((q,i)=>st.qs[i]==3)&&SQD.every(q=>sqDone(q.id))")
# ---- quest kills
rep("caCheck();questKill(gb);ui()}", "caCheck();questKill(gb);sqKill(gb);ui()}")

LOGIC = r"""
// ---- Chapter 1: The Great Rug (story quests)
const SQD=[{id:'cake',n:'Much Wow, Such Cake',g:'Chef Bagholder',gk:'chef',at:'the kitchen in Gigachad Town',qp:1,rw:'300 Cooking XP, 50 Meme Coins, a party cake'},
 {id:'wallet',n:'Wallet Not Found',g:'Froggo',gk:'froggo',at:'the castle courtyard',req:['cake'],qp:1,rw:'a small XP lamp, 75 Meme Coins, the Seed phrase scroll'},
 {id:'grass',n:'Touch Grass',g:'Farmer Ted',gk:'farmer',at:'the allotments by the castle',qp:1,rw:'400 Farming XP, 60 Meme Coins'},
 {id:'fish',n:'The Fish Are Rugged',g:'Fisherwoman Nemo',gk:'nemo',at:"Froggo's Pond",lv:['fi',5],qp:1,rw:'600 Fishing XP, 80 Meme Coins, a meme hunt scroll'},
 {id:'feels',n:'Feels Bad, Man',g:'Froggo',gk:'froggo',at:'the castle courtyard',req:['cake','wallet','grass','fish'],qp:2,rw:'350 Attack, Strength and Defence XP, 250 Meme Coins, Cape fragment (Feels)'}];
const SQS=()=>st.sq||(st.sq={}),SF=()=>st.sqf||(st.sqf={}),sqDone=id=>SQS()[id]==9,sqQ=id=>SQD.find(q=>q.id==id);
const sqAvail=q=>!SQS()[q.id]&&(q.req||[]).every(sqDone)&&(!q.lv||lvl(st.xp[q.lv[0]])>=q.lv[1]);
const sqXY=o=>o?[o.x,o.y]:null,sqFrog=()=>PR.quest?[PR.quest[3],PR.quest[4]]:null;
const sqPlanted=()=>{if(SF().planted)return true;if(st.farm&&st.farm.some(f=>f&&f.s=='spot')){SF().planted=1;return true}return false};
function sqDlg(title,body,btns){M.style.display='flex';MB.onclick=null;MB.oncontextmenu=null;MB.innerHTML='<h2>'+title+'</h2><div style="font-size:13px;line-height:1.55">'+body+'</div><br>'+(btns||[]).map((b,i)=>'<button data-sb="'+i+'">'+b[0]+'</button> ').join('')+'<button id="x">Close</button>';$('x').onclick=()=>M.style.display='none';MB.querySelectorAll('[data-sb]').forEach(e=>e.onclick=()=>{M.style.display='none';btns[+e.dataset.sb][1]()})}
function sqBanner(t){const d=document.createElement('div');d.textContent=t;d.style.cssText='position:fixed;left:50%;top:22%;transform:translate(-50%,-50%) scale(.9);z-index:8;pointer-events:none;font:700 26px Cinzel,Georgia,serif;letter-spacing:1px;color:#ffd23f;text-shadow:0 2px 0 #7a4a00,0 0 18px #000;opacity:0;transition:opacity .6s,transform .6s;white-space:nowrap';document.body.appendChild(d);requestAnimationFrame(()=>{d.style.opacity='1';d.style.transform='translate(-50%,-50%) scale(1)'});setTimeout(()=>{d.style.opacity='0'},3200);setTimeout(()=>d.remove(),4000)}
function sqStart(id){SQS()[id]=1;const q=sqQ(id);say('Quest started: '+q.n+'.','#a60');sqBanner('Quest started: '+q.n);save();ui()}
function sqFinish(id,fn){const q=sqQ(id);fn();SQS()[id]=9;st.qp=(st.qp||0)+q.qp;say('Quest complete: '+q.n+'! You get '+q.rw+' and '+q.qp+' quest point'+(q.qp>1?'s':'')+'.','#a60');sqBanner('Quest complete!');save();ui()}
const sqGive=k=>{if(cap()>0){st.inv.push(k);return true}say('Your bag is too full.','#c00');return false},sqTake=k=>{const i=st.inv.indexOf(k);if(i>=0)st.inv.splice(i,1)};
function sqSpawnBots(){const g=fN(CA.gx+1,CA.y+CA.h+4,6);mob(g[0],g[1],IDX.botcap);const c=gobs[gobs.length-1];c.minion=1;c.sq=1;[[2,1],[-2,1],[0,3]].forEach(([dx,dy])=>{const p=fN(g[0]+dx,g[1]+dy,4);mob(p[0],p[1],IDX.spambot);const b=gobs[gobs.length-1];b.minion=1;b.sq=1});say('BEEP BOOP. The Bot Captain and his Spam Bots attack the castle gate!','#c00')}
function sqKill(gb){if(!gb.sq)return;if(gb.t==IDX.botcap&&SQS().feels==1){SF().capdead=1;SQS().feels=2;say('The Bot Captain falls apart into spam. Tell Froggo the gate is safe.','#a60');save()}setTimeout(()=>{const i=gobs.indexOf(gb);if(i>=0)gobs.splice(i,1)},4000)}
function sqFroggoBtns(){let h='';const w=SQS().wallet,f=SQS().feels;
 if(sqAvail(sqQ('wallet')))h+='<button data-q="sq:wallet">START: Wallet Not Found</button><br><br>';else if(w==1)h+='<button data-q="sq:wallet">'+(SF().w1&&SF().w2&&SF().w3?'CLAIM':'ASK')+': Wallet Not Found</button><br><br>';
 if(sqAvail(sqQ('feels')))h+='<button data-q="sq:feels">START: Feels Bad, Man</button><br><br>';else if(f==1||f==2)h+='<button data-q="sq:feels">'+(f==2?'CLAIM':'ASK')+': Feels Bad, Man</button><br><br>';
 return h?'<div style="margin-top:6px;border-top:1px solid #c9a24a55;padding-top:8px"><b style="color:#ffd23f">Chapter 1: The Great Rug</b><br><br>'+h+'</div>':''}
function sqTalk(k,o){const S=SQS(),F=SF();
 if(k=='chef'){const s=S.cake;if(!s)return sqDlg('Chef Bagholder','<i>"It is King Chad\'s birthday and there is no cake. I bought every ingredient at the top. Now they are worth nothing, and so am I."</i><br><br><i>"Bring me an <b>egg</b>, a <b>bucket of milk</b> and a <b>pot of flour</b>. Try Wow Landing: the hay, the dairy, the windmill. Much wow. Such cake."</i>',[['I will get them',()=>sqStart('cake')]]);
  if(s==1){if(has('egg')&&has('milk')&&has('flour'))return sqDlg('Chef Bagholder','<i>"An egg! Milk! Flour! We are so back."</i>',[['Hand them over',()=>sqFinish('cake',()=>{['egg','milk','flour'].forEach(sqTake);addXp('ck',300);pay(50,'quest reward');sqGive('cake')})]]);
   const need=['egg','milk','flour'].filter(x=>!has(x)).map(x=>IN[x].toLowerCase());return sqDlg('Chef Bagholder','<i>"Still missing: '+need.join(', ')+'. The hay nest, the butter churn and the flour sacks are all in Wow Landing."</i>')}
  return sqDlg('Chef Bagholder','<i>"Best cake I ever made. King Chad cried. Do not tell him I said that."</i>')}
 if(k=='nest'){if(S.cake==1&&!has('egg')){if(sqGive('egg'))say('You find an egg in the hay. Nobody needs to know where it came from.','#0a0');ui();return}return say('Just hay. Very scratchy.')}
 if(k=='churn'){if(S.cake==1&&!has('milk')){if(sqGive('milk'))say('You fill a bucket from the churn.','#0a0');ui();return}return say('The churn is empty. Someone has been drinking the milk.')}
 if(k=='flour'){if(S.cake==1&&!has('flour')){if(sqGive('flour'))say('You scoop a pot of flour from the windmill sacks.','#0a0');ui();return}return say('Sacks of flour. You already have all you need.')}
 if(k=='w1'||k=='w2'||k=='w3'){const W={w1:'Hodl',w2:'Wen',w3:'Lambo'},L={w1:'"I had a seed phrase once. I wrote it on a napkin. I ate the napkin. I remember one word though."',w2:'"Your wallet? I lost mine in the Great Rug too. It is over. But one word stuck with me."',w3:'"I know that feel. I only remember the last word. It was the best word."'};
  if(S.wallet==1){if(!F[k]){F[k]=1;save();say('Seed phrase word: '+W[k]+'.','#a60')}return sqDlg('Forgetful Wojak','<i>'+L[k]+'</i><br><br>Your word is <b style="color:#ffd23f">'+W[k]+'</b>.'+(F.w1&&F.w2&&F.w3?'<br><br>That is all three words. Go back to Froggo.':''))}
  return sqDlg('Forgetful Wojak','<i>"It is over. I forgot what I was going to say."</i>')}
 if(k=='froggo:wallet'){const s=S.wallet;if(!s)return sqDlg('Froggo','<i>"Sit down, Normie. Long ago the Seven Originals each wove an OG Cape, and the capes kept the Liquidity flowing. Then the Dev rugged everyone. He drained the Liquidity, took the name the Rugpuller, and now he hunts the capes."</i><br><br><i>"He wiped your wallet too. Your seed phrase is gone, but three Wojaks around Gigachad Town and Wow Landing each remember one word of it. Find them."</i>',[['Find the Wojaks',()=>sqStart('wallet')]]);
  if(s==1&&F.w1&&F.w2&&F.w3)return sqDlg('Froggo','<i>"Hodl. Wen. Lambo. That is a terrible seed phrase. It is perfect. Here, I wrote it down for you."</i>',[['Take the scroll',()=>sqFinish('wallet',()=>{pay(75,'quest reward');sqGive('seedp');sqGive('lamp5')})]]);
  return sqDlg('Froggo','<i>"Three Wojaks, three words. One near the town square, one in Wow Landing, one east of the castle. Words so far: '+(['w1','w2','w3'].filter(x=>F[x]).length)+' of 3."</i>')}
 if(k=='froggo:feels'){const s=S.feels;if(!s)return sqDlg('Froggo','<i>"You have done well, Normie. Too well. The Rugpuller has noticed."</i><br><br>A horn sounds from the castle gate. <i>"BEEP BOOP."</i><br><br><i>"The Bot Captain! Defend the gate!"</i>',[['To the gate!',()=>{sqStart('feels');F.capdead=0;sqSpawnBots()}]]);
  if(s==2)return sqDlg('Froggo','<i>"The gate holds. Feels good, man. For once."</i><br><br><i>"The Rugpuller wants the OG Capes. Mine, the Feels Cape, is hidden in the pond, torn in three. Take the first piece. Keep it away from him."</i>',[['Take the fragment',()=>sqFinish('feels',()=>{['at','str','def'].forEach(x=>addXp(x,350));pay(250,'quest reward');sqGive('cfrag1')})]]);
  return sqDlg('Froggo','<i>"The Bot Captain is at the castle gate! Beat him before he spams the whole kingdom."</i>')}
 if(k=='farmer'){const s=S.grass;if(!s)return sqDlg('Farmer Ted','<i>"Four Doomscrollers have moved into my allotments. They will not leave. They will not look up. One of them has been refreshing the same chart for three days."</i><br><br><i>"Plant a potato so they remember what the outside looks like, then tell each one to touch grass."</i>',[['I will sort them out',()=>{sqStart('grass');if(!has('spot')&&!sqPlanted()&&sqGive('spot'))say('Farmer Ted gives you a potato seed.','#0a0')}]]);
  if(s==1){const n=[0,1,2,3].filter(i=>F['sc'+i]).length;if(sqPlanted()&&n>=4)return sqDlg('Farmer Ted','<i>"They are outside! One of them saw a bird and screamed. Beautiful."</i>',[['You are welcome',()=>sqFinish('grass',()=>{addXp('fa',400);pay(60,'quest reward')})]]);
   if(!has('spot')&&!sqPlanted()&&sqGive('spot'))say('Farmer Ted gives you another potato seed.','#0a0');return sqDlg('Farmer Ted','<i>"'+(sqPlanted()?'The potato is in.':'Plant that potato in one of the four patches.')+' Doomscrollers told to touch grass: '+n+' of 4."</i>')}
  return sqDlg('Farmer Ted','<i>"My field is free. My potatoes are growing. Life is good."</i>')}
 if(k=='scroll'){const i=o&&o.si;if(S.grass==1&&!F['sc'+i]){F['sc'+i]=1;save();const L=['"Grass? Is that a new coin? What is the ticker?"','"Outside? I saw that in a video once."','"Fine. FINE. But if I miss a pump, it is your fault."','"The sun... it is so bright... it is beautiful..."'];return sqDlg('Doomscroller','You tell the Doomscroller to go touch grass.<br><br><i>'+L[i%4]+'</i><br><br>He wanders off outside.')}
  return sqDlg('Doomscroller','<i>"Not now. The chart is doing something."</i>')}
 if(k=='nemo'){const s=S.fish;if(!s){if(lvl(st.xp.fi)<5)return sqDlg('Fisherwoman Nemo','<i>"The fish are gone and I do not have time for beginners. Come back with a Fishing level of 5."</i>');return sqDlg('Fisherwoman Nemo','<i>"Ever since the Great Rug, the pond keeps draining. The fish are going somewhere. Search the muddy shallows around the pond and find out where."</i>',[['I will look',()=>sqStart('fish')]])}
  if(s==1){if(has('plug'))return sqDlg('Fisherwoman Nemo','<i>"A drain plug... with a Rugpuller sigil on it. He has been draining the Liquidity from my pond. I knew it. Put it back where it belongs: in my evidence box."</i>',[['Hand it over',()=>sqFinish('fish',()=>{sqTake('plug');addXp('fi',600);pay(80,'quest reward');sqGive('clue')})]]);
   return sqDlg('Fisherwoman Nemo','<i>"Search all the muddy shallows around the pond. Searched: '+[0,1,2].filter(i=>F['sh'+i]).length+' of 3."</i>')}
  return sqDlg('Fisherwoman Nemo','<i>"The fish are back. Some of them, anyway. Thanks, Normie."</i>')}
 if(k=='shallow'){const i=o&&o.hi;if(S.fish!=1)return say('Muddy shallows.');if(F['sh'+i]&&!(has('plug')))return say('You already searched here.');if(!F['sh'+i]){F['sh'+i]=1;save()}const n=[0,1,2].filter(j=>F['sh'+j]).length;if(n>=3&&!has('plug')&&!F.plug){if(sqGive('plug')){F.plug=1;say('Something is blocking the drain... a plug with a tiny Rugpuller sigil!','#0a0')}ui();return}return say(n<3?'Just mud and a very confused frog. ('+n+' of 3 searched)':'Nothing else here.')}
}
// what the quest card shows: the step in progress, or the next quest to start
function sqCur(){const S=SQS(),F=SF(),O=window.SQO||{};
 for(const q of SQD){const s=S[q.id];if(!s||s==9)continue;let t='',at=null,up=2.6;
  if(q.id=='cake'){const m=['egg','milk','flour'].filter(x=>!has(x));if(m.length){const o={egg:O.nest,milk:O.churn,flour:O.flour}[m[0]];t='Get '+IN[m[0]].toLowerCase()+' in Wow Landing ('+(3-m.length)+' of 3).';at=sqXY(o);up=1.4}else{t='Bring the egg, milk and flour to Chef Bagholder.';at=sqXY(O.chef)}}
  if(q.id=='wallet'){const w=['w1','w2','w3'].find(x=>!F[x]);if(w){t='Find the forgetful Wojaks ('+['w1','w2','w3'].filter(x=>F[x]).length+' of 3 words).';at=sqXY(O[w])}else{t='Tell Froggo your seed phrase.';at=sqFrog();up=2.9}}
  if(q.id=='grass'){const i=[0,1,2,3].find(j=>!F['sc'+j]);if(!sqPlanted()){t='Plant a potato seed in an allotment patch.';const p=XO.find(o=>o.k=='patch');at=sqXY(p);up=1.2}else if(i!=null){t='Tell the Doomscrollers to touch grass ('+[0,1,2,3].filter(j=>F['sc'+j]).length+' of 4).';at=sqXY(O.sc&&O.sc[i])}else{t='Tell Farmer Ted his field is clear.';at=sqXY(O.farmer)}}
  if(q.id=='fish'){if(has('plug')){t='Bring the drain plug to Fisherwoman Nemo.';at=sqXY(O.nemo)}else{const i=[0,1,2].find(j=>!F['sh'+j]);t='Search the muddy shallows around the pond ('+[0,1,2].filter(j=>F['sh'+j]).length+' of 3).';at=sqXY(O.sh&&O.sh[i!=null?i:2]);up=1}}
  if(q.id=='feels'){if(s==1){if(!F.capdead&&!gobs.some(g=>g.sq&&g.t==IDX.botcap&&!g.dead))sqSpawnBots();const c=gobs.find(g=>g.sq&&g.t==IDX.botcap&&!g.dead);t='Defeat the Bot Captain at the castle gate.';at=c?[c.x,c.y]:null;up=3.2}else{t='Tell Froggo the gate is safe.';at=sqFrog();up=2.9}}
  return {key:'q'+q.id+t,hdr:'QUEST',t:q.n,h:t,at:()=>at,up}}
 const q=SQD.find(sqAvail);if(!q)return null;const at=q.gk=='froggo'?sqFrog():sqXY(O[q.gk]);return {key:'n'+q.id,hdr:'NEW QUEST',t:q.n,h:'Talk to '+q.g+' at '+q.at+'.',at:()=>at,up:q.gk=='froggo'?2.9:2.6}}
function SQH(){const N=['Not started','In progress','Ready to hand in'],S=SQS();let h='<div style="margin:10px 0 4px;color:#ffd23f;font:700 13px Cinzel,Georgia,serif">Chapter 1: The Great Rug</div>';
 SQD.forEach(q=>{const s=S[q.id],c=s==9?'#7f7':s?'#ff8':sqAvail(q)?'#f88':'#f88',lab=s==9?'Complete':s?'In progress':sqAvail(q)?'Not started':'Locked';const cur=s&&s!=9?sqCur():null;
  h+='<div style="margin:6px 0;font-size:11px;line-height:1.45"><b style="color:#ffb000">'+q.n+'</b> <span style="color:'+c+'">('+lab+')</span><br>'+(s==9?'Done.':cur&&cur.t==q.n?cur.h:'Talk to '+q.g+' at '+q.at+'.')+(q.lv&&!s?' Needs Fishing '+q.lv[1]+'.':'')+'<br><span style="color:#ccc">Reward: '+q.rw+', '+q.qp+' QP</span></div>'});return h}
"""
rep("function QSH(){return QSH0()+SQH()}", LOGIC + "function QSH(){return QSH0()+SQH()}")

open(PATH, 'w', encoding='utf-8').write(h)
print('story quests patch applied')
