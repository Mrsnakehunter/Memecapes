#!/usr/bin/env python3
"""Capes, the welcome, and the mouse wheel.

- Capes of Accomplishment (level 100): 1,000,000 Meme Coins.
- Quest cape (all quests done): 100,000 Meme Coins at the cape merchant.
- MemeCape: 100,000,000 Meme Coins at the cape merchant. Worn, it shows on the character in 3D with the hood
  and crown over the head (models/c_memecape.json). The Quest cape is the same cape without hood and crown.
- "Welcome to MemeCapes" ten seconds after you enter the game.
- The mouse wheel over the side panel, chat box or world map scrolls that, not the camera.
Run from the repo root after the other patches:  python3 tools/patch_capes.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- the two new capes (registered right after the skill capes)
rep("AB[c]=2;SLOT[c]='cape';RAR[c]=RC[4]});\nIN.broot='Frost root';",
    "AB[c]=2;SLOT[c]='cape';RAR[c]=RC[4]});\n"
    "ITM.memecape=['MemeCape','cape','#c8102e','The MemeCape. Every meme, one cape, one crown.',4,0,0,0,5,'cape'];IN.memecape='MemeCape';EX.memecape='The MemeCape. Every meme, one cape, one crown.';AB.memecape=5;SLOT.memecape='cape';RAR.memecape=RC[4];"
    "ITM.qcape=['Quest cape','cape','#1f8a4c','Every quest in MemeCapes, done.',4,0,0,0,3,'cape'];IN.qcape='Quest cape';EX.qcape='Every quest in MemeCapes, done.';AB.qcape=3;SLOT.qcape='cape';RAR.qcape=RC[4];if(!IC.qcape)IC.qcape=ICT.cape('#1f8a4c');\n"
    "IN.broot='Frost root';")

# ---- the cape merchant
rep("""function capeUI(){const n99=Object.keys(NM).filter(k=>lvl(st.xp[k])>=100).length;M.style.display='flex';MB.innerHTML='<h2>Cape merchant</h2><p style="font-size:12px">"Reach level 100 in a skill and I will sell you its Cape of Accomplishment for 100,000 Meme Coins.'+(n99>=2?' With two or more at 100, your capes come trimmed."':'"')+'</p>'+Object.keys(NM).map(k=>{const l=lvl(st.xp[k]);return '<div class="row"><span>'+NM[k]+' <small>('+l+'/100)</small></span>'+(l>=100?'<button data-cp="'+k+'">Buy (100,000)</button>':'<span style="color:#888;font-size:11px">Locked</span>')+'</div>'}).join('')+'<br><button id="x">Close</button>';$('x').onclick=()=>M.style.display='none';MB.querySelectorAll('[data-cp]').forEach(b=>b.onclick=()=>{if(st.coins<100000)return say('You need 100,000 Meme Coins for that.','#c00');if(cap()<=0)return say('Inventory full.','#c00');burn(100000,'skill cape');st.inv.push('cape_'+b.dataset.cp);if(n99>=2)st.trim=1;clog('cape_'+b.dataset.cp);M.style.display='none';say('You buy the '+NM[b.dataset.cp]+' cape'+(n99>=2?' (t)':'')+'!','#0a0');ui();save()})}""",
    """function capeUI(){const n99=Object.keys(NM).filter(k=>lvl(st.xp[k])>=100).length,qdone=QD.every((q,i)=>st.qs[i]==3),L='<span style="color:#888;font-size:11px">Locked</span>';M.style.display='flex';MB.innerHTML='<h2>Cape merchant</h2><p style="font-size:12px">"Reach level 100 in a skill and I will sell you its Cape of Accomplishment for 1,000,000 Meme Coins.'+(n99>=2?' With two or more at 100, your capes come trimmed."':'"')+'</p>'+Object.keys(NM).map(k=>{const l=lvl(st.xp[k]);return '<div class="row"><span>'+NM[k]+' <small>('+l+'/100)</small></span>'+(l>=100?'<button data-cp="'+k+'">Buy (1,000,000)</button>':L)+'</div>'}).join('')+'<div class="row" style="margin-top:8px"><span>Quest cape <small>(every quest done)</small></span>'+(qdone?'<button data-qc="1">Buy (100,000)</button>':L)+'</div><div class="row"><span style="color:#ffd23f"><b>The MemeCape</b> <small>(hood and crown)</small></span><button data-mc="1">Buy (100,000,000)</button></div><br><button id="x">Close</button>';$('x').onclick=()=>M.style.display='none';const buy=(cost,k,what)=>{if(st.coins<cost)return say('You need '+cost.toLocaleString()+' Meme Coins for that.','#c00');if(cap()<=0)return say('Inventory full.','#c00');burn(cost,what);st.inv.push(k);clog(k);M.style.display='none';ui();save();return 1};MB.querySelectorAll('[data-cp]').forEach(b=>b.onclick=()=>{if(buy(1000000,'cape_'+b.dataset.cp,'skill cape')){if(n99>=2)st.trim=1;say('You buy the '+NM[b.dataset.cp]+' cape'+(n99>=2?' (t)':'')+'!','#0a0')}});MB.querySelectorAll('[data-qc]').forEach(b=>b.onclick=()=>{if(buy(100000,'qcape','quest cape'))say('You buy the Quest cape!','#0a0')});MB.querySelectorAll('[data-mc]').forEach(b=>b.onclick=()=>{if(buy(100000000,'memecape','MemeCape'))say('You buy the MemeCape! Every meme, one cape, one crown.','#0a0')})}""")

# ---- wear it: draw the cape model on the character
rep("qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),mvg?(pspd>2.4?'Running':'Walking'):null,now/1000)}",
    "qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),mvg?(pspd>2.4?'Running':'Walking'):null,now/1000);qCape(P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0))}")
rep("function qHeld(PM,x,z,yaw,clip,t){",
    "const CAPEM={memecape:'c_memecape',qcape:'c_qcape'};function qCape(x,z,yaw){const k=st.eq&&st.eq.cape,cm=k&&CAPEM[k];if(!cm)return;needMdl(cm);const M=MDL[cm];if(!M||!M.ok)return;qMdl(M,x,0,z,yaw,MDLSC.player,null,0,0,null,false,0)}"
    "function qHeld(PM,x,z,yaw,clip,t){")

# ---- welcome, ten seconds in
rep("rs();save();say('Welcome to MemeCapes, '+st.acct.name+'!','#a60');say('You wake up at Castle Gigachad.",
    "rs();save();setTimeout(()=>{if(!started)return;say('Welcome to MemeCapes, '+st.acct.name+'!','#a60');const d=document.createElement('div');d.textContent='Welcome to MemeCapes';d.style.cssText='position:fixed;left:50%;top:18%;transform:translate(-50%,-50%) scale(.9);z-index:8;pointer-events:none;font:700 34px Cinzel,Georgia,serif;letter-spacing:2px;color:#ffd23f;text-shadow:0 2px 0 #7a4a00,0 0 18px #000,0 0 6px #000;opacity:0;transition:opacity .8s,transform .8s;white-space:nowrap';document.body.appendChild(d);requestAnimationFrame(()=>{d.style.opacity='1';d.style.transform='translate(-50%,-50%) scale(1)'});setTimeout(()=>{d.style.opacity='0'},3800);setTimeout(()=>d.remove(),4800)},10000);say('You wake up at Castle Gigachad.")

# ---- the wheel: panels scroll themselves
rep("addEventListener('wheel',e=>{distT=Math.max(7,Math.min(30,distT+e.deltaY*.01))});",
    "addEventListener('wheel',e=>{if(e.target&&e.target.closest&&e.target.closest('#panel,#chat,#wm,#modal,#start'))return;distT=Math.max(7,Math.min(30,distT+e.deltaY*.01))});")

open(PATH, 'w', encoding='utf-8').write(h)
print('capes patch applied')
