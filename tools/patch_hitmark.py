#!/usr/bin/env python3
"""Hit markers: Meme Coins instead of a red/blue star.

Every hit now pops up as a small minted coin with a ridged gold rim, in our colours:
  - damage: a crimson coin (the MemeCapes red), white number
  - zero / blocked: a gold coin with a dark number
  - poison stays green, special attacks stay purple (same coin)
The coin flips in edge-on, overshoots and settles, a shine sweeps across its face, then it drifts up and fades.
Big hits (10+) are a size larger and throw off a ring of gold sparks. Numbers use the game's Cinzel lettering.
Plain HTML/CSS, no images. Run from the repo root after the other patches:  python3 tools/patch_hitmark.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


CSS = (".hm{position:fixed;width:30px;height:30px;margin:-15px 0 0 -15px;pointer-events:none;z-index:5;perspective:240px;"
       "animation:hmUp 1.25s cubic-bezier(.3,.6,.3,1) forwards}"
       ".hmBig{width:38px;height:38px;margin:-19px 0 0 -19px}"
       # the coin: a ridged gold rim ...
       ".hmc{position:absolute;inset:0;border-radius:50%;animation:hmFlip .45s cubic-bezier(.25,1.7,.45,1) both;"
       "background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.55),transparent 55%),"
       "repeating-conic-gradient(#ffe27a 0 7deg,#b8860b 7deg 14deg);"
       "box-shadow:0 0 0 1px #5a3a00,0 4px 9px rgba(0,0,0,.55)}"
       # ... around an enamel face with a thin raised gold line
       ".hmc:before{content:'';position:absolute;inset:3px;border-radius:50%;"
       "background:radial-gradient(circle at 36% 30%,var(--a) 0,var(--b) 50%,var(--d) 100%);"
       "box-shadow:0 0 0 1px #5a3a00,inset 0 0 0 1.5px rgba(255,226,122,.75),inset 0 -3px 5px rgba(0,0,0,.4),inset 0 2px 3px rgba(255,255,255,.35)}"
       # a shine sweeps across once it lands
       ".hmc:after{content:'';position:absolute;inset:0;border-radius:50%;"
       "background:linear-gradient(115deg,transparent 38%,rgba(255,255,255,.85) 50%,transparent 62%) no-repeat;"
       "background-size:260% 100%;background-position:130% 0;animation:hmShine .75s .15s ease-out forwards}"
       # a gold ring pulses out from every hit
       ".hm:before{content:'';position:absolute;inset:0;border-radius:50%;border:2px solid var(--w);opacity:0;animation:hmRing .5s .05s ease-out}"
       ".hm .hmN{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;"
       "font:900 15px/1 'Cinzel',Georgia,serif;letter-spacing:-.5px;color:#fff;"
       "text-shadow:0 1px 0 #2b0810,0 0 3px #2b0810,0 0 1px #000;animation:hmFlip .45s cubic-bezier(.25,1.7,.45,1) both}"
       ".hmBig .hmN{font-size:18px}.hmN3 .hmN{font-size:12px}.hmBig.hmN3 .hmN{font-size:14px}"
       ".hmG .hmN{color:#4a2a00;text-shadow:0 1px 0 #fff3b0,0 0 2px #ffe9b0}"
       # big hits throw off gold sparks from the rim
       ".hm .hmK{position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;"
       "background:#fff3b0;box-shadow:0 0 6px 2px #ffd23f;opacity:0;animation:hmSpark .6s .1s ease-out forwards}"
       "@keyframes hmFlip{0%{transform:scale(.25) rotateY(95deg)}70%{transform:scale(1.18) rotateY(-8deg)}100%{transform:scale(1) rotateY(0)}}"
       "@keyframes hmUp{0%,58%{transform:translateY(0);opacity:1}100%{transform:translateY(-20px);opacity:0}}"
       "@keyframes hmShine{to{background-position:-40% 0}}"
       "@keyframes hmRing{0%{opacity:.9;transform:scale(.9)}100%{opacity:0;transform:scale(2.1)}}"
       "@keyframes hmSpark{0%{opacity:1;transform:rotate(var(--r)) translateX(17px)}100%{opacity:0;transform:rotate(var(--r)) translateX(36px) scale(.4)}}")
rep(".hit{position:fixed;width:26px;", CSS + ".hit{position:fixed;width:26px;")

# the coin's enamel: [highlight, body, edge]
FL = r"""function fl(x,y,t,c){const p=[x+.5-E[0],1.8+hgt(x+.5,y+.5)-E[1],y+.5-E[2]],z=d3(p,Fw);if(z<=0)return;const sx=d3(p,Rt)/(z*TH*asp),sy=d3(p,Up)/(z*TH);
 const n=+t||0,zero=!n,k=zero||c=='#39f'?'g':c=='#3a3'?'p':c=='#a0f'?'s':'r',E3={r:['#ff6b6b','#c8102e','#4a0a12'],g:['#fff6c2','#ffd23f','#9a6a06'],p:['#a8ffa0','#2e9e3a','#0f4a18'],s:['#e6b3ff','#8a2be2','#35095e']}[k],big=n>=10,d=document.createElement('div');
 d.className='hm hm'+k.toUpperCase()+(big?' hmBig':'')+(String(t).length>2?' hmN3':'');d.style.setProperty('--a',E3[0]);d.style.setProperty('--b',E3[1]);d.style.setProperty('--d',E3[2]);d.style.setProperty('--w',k=='g'?'#fff3b0':'#ffd23f');
 let sp='';if(big)for(let i=0;i<8;i++)sp+='<span class="hmK" style="--r:'+(i*45+22)+'deg"></span>';d.innerHTML=sp+'<div class="hmc"></div><span class="hmN">'+t+'</span>';
 d.style.left=((sx+1)/2*CW+(Math.random()*10-5))+'px';d.style.top=((1-sy)/2*CH)+'px';document.body.appendChild(d);setTimeout(()=>d.remove(),1300)}"""
i = h.index("function fl(x,y,t,c){")
j = h.index("setTimeout(()=>d.remove(),1200)}", i) + len("setTimeout(()=>d.remove(),1200)}")
assert h.count("function fl(x,y,t,c){") == 1 and 'className=\'hit\'' in h[i:j]
h = h[:i] + FL + h[j:]

open(PATH, 'w', encoding='utf-8').write(h)
print('hit marker patch applied')
