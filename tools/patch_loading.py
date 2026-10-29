#!/usr/bin/env python3
"""A proper loading screen after you log in (Albert, Oct 29: "a loading screen while the game's loading after you log
in, so it doesn't look crappy").

Before: the start screen vanished and the world popped in piece by piece (bare ground, then buildings, characters and
trees appearing as their files arrived).

Now begin() opens a full-screen loading view: the MemeCape art (media/loading_cape.webp, the real in-game cape), the
MemeCapes title, a short flavour line that changes every few seconds, and a gold bar that follows REAL loading:
the models the game has asked for and their textures (regMdl marks models that wait for a texture, m.wt), the tree
pack (TRP.on) and the first frames drawn. It fades out when everything asked for has arrived, or after 16 s at most
(the rest keeps streaming in behind). No fake timer: the bar only moves when something has loaded.

Run near the end of the build (before patch_ticker):  python3 tools/patch_loading.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# models remember whether they wait for a texture
rep("m={k,nv,ni:d.i.length,ok:0,tex:null,clips:{}", "m={k,nv,ni:d.i.length,ok:0,tex:null,wt:!!d.tex,clips:{}")

LDS = r"""const LDS=(()=>{let el=null,t0=0,fr=0,shown=0,gone=0;const pre=new Image();pre.src='media/loading_cape.webp';
const LINES=['Polishing the Meme Coins','Waking up the shopkeepers','Sharpening the bronze swords','Planting the forests',"Filling Froggo's Pond",'Raising Castle Gigachad','Stitching the patches on the MemeCape','Teaching Popcat to pop','Lighting the lamps in Wow Landing','Counting the coins in the bank'];
function css(){const s=document.createElement('style');s.textContent='#ldx{position:fixed;inset:0;z-index:90;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:16px;box-sizing:border-box;background:radial-gradient(ellipse at 50% 38%,#33101a 0%,#160a0e 45%,#0b090a 75%);transition:opacity .65s;font-family:Cinzel,Georgia,serif;user-select:none}'
+'#ldx.ldx-out{opacity:0;pointer-events:none}'
+'.ldx-art{height:min(54vh,520px);max-width:86vw;object-fit:contain;-webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 62%,transparent 100%);mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 62%,transparent 100%);animation:ldxf 4.5s ease-in-out infinite}'
+'@keyframes ldxf{50%{transform:translateY(-7px)}}'
+'.ldx-title{font-weight:900;font-size:clamp(30px,6.5vw,54px);letter-spacing:3px;color:#ffd86a;text-shadow:0 2px 0 #7a4a00,0 0 26px rgba(255,170,40,.35);margin-top:4px}'
+'.ldx-line{color:#ecdcc2;font:italic 15px Georgia,serif;min-height:20px;margin:2px 0 12px;transition:opacity .25s;text-align:center}'
+'.ldx-bar{width:min(80vw,420px);height:12px;border-radius:7px;background:#2a1712;border:1px solid #8a6420;box-shadow:inset 0 1px 3px #000,0 0 14px rgba(255,180,60,.12);overflow:hidden}'
+'.ldx-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#a86e14,#ffe08a 55%,#d49a2a);transition:width .35s ease-out}'
+'.ldx-st{color:#b9a58a;font:12px system-ui,sans-serif;margin-top:8px;letter-spacing:.4px;min-height:16px}';document.head.appendChild(s)}
function show(){if(el)return;try{css();el=document.createElement('div');el.id='ldx';el.innerHTML='<img class="ldx-art" src="media/loading_cape.webp" alt=""><div class="ldx-title">MemeCapes</div><div class="ldx-line"></div><div class="ldx-bar"><i></i></div><div class="ldx-st">Entering the world</div>';document.body.appendChild(el)}catch(e){return}
t0=performance.now();const bar=el.querySelector('.ldx-bar i'),st=el.querySelector('.ldx-st'),ln=el.querySelector('.ldx-line');let li=Math.floor(Math.random()*LINES.length);
const nextLine=()=>{if(gone)return;ln.style.opacity=0;setTimeout(()=>{ln.textContent=LINES[li++%LINES.length]+'...';ln.style.opacity=1},250);setTimeout(nextLine,2600)};ln.textContent=LINES[li++%LINES.length]+'...';setTimeout(nextLine,2600);
const tick=()=>{if(gone)return;fr++;const t=(performance.now()-t0)/1000;let n=0,ok=0;for(const k in MLOAD){n++;const m=MDL[k];if(m&&m.ok&&(!m.wt||m.tex))ok++}
let tr=1;try{tr=(window.MC_CONFIG&&MC_CONFIG.trees===0)||TRP.on?1:0}catch(e){}
const p=.1*Math.min(1,t/1.2)+.62*(n?ok/n:1)+.18*tr+.1*Math.min(1,fr/30);shown=Math.max(shown,Math.min(p,.99));bar.style.width=(shown*100).toFixed(1)+'%';
st.textContent=n&&ok<n?'Loading characters and buildings  '+ok+' / '+n:!tr?'Planting the trees':'Entering the world';
if((t>1.6&&fr>=24&&ok>=n&&tr)||t>16)hide();else requestAnimationFrame(tick)};requestAnimationFrame(tick);setTimeout(hide,22000)}
function hide(){if(gone||!el)return;gone=1;try{el.querySelector('.ldx-bar i').style.width='100%';el.querySelector('.ldx-st').textContent='Entering the world'}catch(e){}setTimeout(()=>{el.classList.add('ldx-out');setTimeout(()=>el.remove(),750)},250)}
return{show,hide}})();
"""
rep("function needMdl(k){", LDS + "function needMdl(k){")
rep("function begin(){started=true;", "function begin(){started=true;LDS.show();")
open(PATH, 'w', encoding='utf-8').write(h)
print('loading screen patch applied')
