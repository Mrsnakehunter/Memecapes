#!/usr/bin/env python3
"""Starter guide: the first few minutes of the game, one step at a time.

A small card under the zoom buttons says what to do next (walk, meet Froggo, chop, light a fire,
fish, cook, mine, fight, bank), a gold arrow bobs over the nearest tree / fishing spot / rock /
meme / bank, and the card says how far away it is when it is off screen. Each step ticks off by
itself when the player does it. Finishing the guide pays 200 Meme Coins and a small XP lamp.
Players who already have progress never see it. The x hides it; the small "?" brings it back.
Run from the repo root after patch_lazyskin.py:  python3 tools/patch_guide.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


G = r"""
// ---- starter guide: the first few minutes, one step at a time
const gNear=(L,f,xy)=>{let b=null,bd=1e9;for(const o of L){if(f&&!f(o))continue;const p=xy?xy(o):[o.x,o.y];if(!p)continue;const d=Math.hypot(p[0]-P.x,p[1]-P.y);if(d<bd){bd=d;b=p}}return b};
const GST=[
 {t:'Walk around',h:'Tap the ground to walk there. Drag to turn the camera, pinch or use + and - to zoom.',ok:()=>Math.hypot(P.x-SP.x,P.y-SP.y)>4},
 {t:'Meet Froggo',h:'Froggo has a job for you. Tap him and choose HELP HIM.',ok:()=>st.qs[0]>=1,at:()=>PR.quest&&[Math.floor(PR.quest[0]),Math.floor(PR.quest[1])],up:2.9},
 {t:'Chop a tree',h:'Tap a tree to chop it with your axe. You get logs.',ok:()=>st.ev&&st.ev.chop,at:()=>gNear(trees,o=>!(o.d>tickN)&&!inCastle(o.x,o.y,0)),up:3.4},
 {t:'Light a fire',h:'Walk out of the castle, tap the logs in your bag, then Light.',ok:()=>st.ev&&st.ev.fire},
 {t:'Catch shrimps',h:'Tap a fishing spot (the bubbles in the water) to use your net.',ok:()=>st.xp.fi>0,at:()=>gNear(fish,o=>!o.gone),up:1.2},
 {t:'Cook your catch',h:'Tap your fire, or a cooking range in town, while you carry raw shrimps.',ok:()=>st.ev&&st.ev.cook,at:()=>gNear(fires.concat(PR.ranges.map(r=>({x:Math.floor(r[0]),y:Math.floor(r[1])})))),up:1.6},
 {t:'Mine some ore',h:'Tap a copper or tin rock with your pickaxe.',ok:()=>st.ev&&st.ev.mine,at:()=>gNear(rocks,o=>!(o.d>tickN)),up:1.8},
 {t:'Defeat a meme',h:'Tap a weak meme (level 5 or lower) to fight it. Eat bread from your bag if your health gets low.',ok:()=>(st.xp.at||0)+(st.xp.str||0)+(st.xp.def||0)>0,at:()=>gNear(gobs,g=>!g.dead&&MT[g.t].lv<=5&&!MT[g.t].boss),up:2.4},
 {t:'Visit a bank',h:'Banks keep your items and Meme Coins safe. Tap a bank and deposit your loot.',ok:()=>st.ev&&st.ev.bank,at:()=>gNear(SB,s=>s.k=='bank',s=>s.nt),up:2.6}];
const gCard=document.createElement('div'),gArw=document.createElement('div'),gPill=document.createElement('div');
gCard.id='guide';gCard.style.cssText='position:fixed;left:8px;top:74px;width:min(230px,calc(100vw - 160px));z-index:5;display:none;background:linear-gradient(#3a0a12f0,#22060bf0);border:1px solid #c9a24a;border-radius:9px;box-shadow:0 3px 12px #0008;padding:8px 10px 9px;color:#f3e6c8;font:12px/1.4 Georgia,serif';
gArw.style.cssText='position:fixed;z-index:4;pointer-events:none;display:none;transform:translate(-50%,-100%);font:bold 30px Georgia;color:#ffd23f;text-shadow:0 2px 0 #7a4a00,0 0 10px #000';gArw.textContent='▼';
gPill.style.cssText='position:fixed;left:8px;top:74px;z-index:5;display:none;width:28px;height:28px;border-radius:50%;background:#3a0a12;border:1px solid #c9a24a;color:#ffd23f;font:bold 16px Georgia;text-align:center;line-height:27px;cursor:pointer';gPill.textContent='?';gPill.title='Starter guide';
document.body.append(gCard,gArw,gPill);
gCard.addEventListener('pointerdown',e=>e.stopPropagation());gPill.addEventListener('pointerdown',e=>e.stopPropagation());
gPill.onclick=()=>{st.gOff=0;gKey='';save()};
let gKey='',gTgt=null,gT=0,gFlash=0,gLast=-1;
const gDir=(dx,dy)=>{const a=Math.atan2(dx,-dy)*180/Math.PI,N=['north','north-east','east','south-east','south','south-west','west','north-west'];return N[Math.round(((a+360)%360)/45)%8]};
function guideDraw(){
 if(!started||!st||!st.xp){gCard.style.display=gArw.style.display=gPill.style.display='none';return}
 if(st.gDone==null)st.gDone=(st.qp>0||(st.xp.wc||0)+(st.xp.mi||0)+(st.xp.fi||0)+(st.xp.at||0)+(st.xp.str||0)>0)?1:0; // players who already started never see it
 if(st.gDone){gCard.style.display=gArw.style.display=gPill.style.display='none';return}
 let i=0;while(i<GST.length&&GST[i].ok())i++;
 if(i>=GST.length){st.gDone=1;pay(200,'starter guide');if(cap()>0)st.inv.push('lamp5');save();ui();
  say('Starter guide complete! You got 200 Meme Coins and a small XP lamp. Froggo\'s quest, The Great Rug, is your next goal.','#a60');return}
 if(st.gI!=null&&i>st.gI){say('Guide: '+GST[st.gI].t+' done! Next: '+GST[i].t+'.','#0a7a2a');gFlash=performance.now()}st.gI=i;
 if(st.gOff){gCard.style.display=gArw.style.display='none';gPill.style.display='block';return}gPill.style.display='none';
 const g=GST[i],tn=performance.now();if(i!=gLast||tn-gT>800){gLast=i;gT=tn;gTgt=g.at?g.at():null}
 let far='';if(gTgt){const d=Math.round(Math.hypot(gTgt[0]-P.x,gTgt[1]-P.y));if(d>3)far='<div style="margin-top:4px;color:#ffd23f">➤ '+d+' tiles '+gDir(gTgt[0]-P.x,gTgt[1]-P.y)+'</div>'}
 const k=i+'|'+far;if(k!=gKey){gKey=k;let dots='';for(let j=0;j<GST.length;j++)dots+='<span style="display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:3px;background:'+(j<i?'#ffd23f':j==i?'#fff':'#ffffff33')+'"></span>';
  gCard.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center"><b style="font:700 11px Cinzel,Georgia,serif;letter-spacing:1px;color:#c9a24a">STARTER GUIDE '+(i+1)+'/'+GST.length+'</b><span id="gx" style="cursor:pointer;color:#c9a24a;font-size:15px;padding:0 2px" title="Hide the guide">✕</span></div>'
   +'<div style="font:700 14px Cinzel,Georgia,serif;color:#ffd23f;margin:3px 0 2px">'+g.t+'</div><div>'+g.h+'</div>'+far+'<div style="margin-top:6px">'+dots+'</div>';
  gCard.querySelector('#gx').onclick=()=>{st.gOff=1;save()}}
 gCard.style.display='block';gCard.style.boxShadow=performance.now()-gFlash<900?'0 0 18px #ffd23f':'0 3px 12px #0008';
 if(gTgt){const x=gTgt[0]+.5,z=gTgt[1]+.5,p=[x-E[0],(g.up||2)+hgt(x,z)+Math.sin(performance.now()/260)*.15-E[1],z-E[2]],zz=d3(p,Fw);
  if(zz>0){const sx=d3(p,Rt)/(zz*TH*asp),sy=d3(p,Up)/(zz*TH);if(Math.abs(sx)<1.05&&Math.abs(sy)<1.05){gArw.style.display='block';gArw.style.left=((sx+1)/2*CW)+'px';gArw.style.top=((1-sy)/2*CH)+'px';return}}}
 gArw.style.display='none'}
"""
rep("function nameplate(){", G + "function nameplate(){guideDraw();")
# opening a bank counts for the guide (and anything else that listens for it)
rep("if(k=='shop'||k=='bank'||k=='forge'||k=='chest'||k=='quest'){act=null;modal(k);return}",
    "if(k=='shop'||k=='bank'||k=='forge'||k=='chest'||k=='quest'){act=null;if(k=='bank')evn('bank');modal(k);return}")

open(PATH, 'w', encoding='utf-8').write(h)
print('starter guide patch applied')
