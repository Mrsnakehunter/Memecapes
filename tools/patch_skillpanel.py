#!/usr/bin/env python3
"""The Skills tab as a wall of struck skill coins (Albert, Oct 31: "recreate our own unique version that's amazing and
very interactive for the levels and leveling").

Our own design, nothing borrowed: every skill is a Meme Coin struck in that skill's enamel colour, with its own line
icon, the level on a gold tag and a thin gold ring around the rim that fills as you work towards the next level.
Tap a coin and it flips to its back: exact XP, XP to the next level, what the next levels unlock (read from the
game's own tables, so it is always true), and the Mastery cape at 100. The coin you trained last glows; a level-up
spins the coin and throws sparks. Total level + combat level sit on a big medallion at the top.
Classes are all sc* (the game's short global class names leak otherwise).
Run after patch_friends.py:  python3 tools/patch_skillpanel.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


CSS = r"""
.sch{display:flex;align-items:center;gap:8px;margin:2px 0 8px;padding:6px;border:1px solid #d9a52044;border-radius:8px;background:linear-gradient(180deg,#2a0a10,#1a0408)}
.schm{position:relative;flex:0 0 54px;width:54px;height:54px;border-radius:50%;background:conic-gradient(from 0deg,#ffe28a,#b8860b 25%,#ffe9a6 50%,#a8720a 75%,#ffe28a);box-shadow:0 2px 6px #000a,inset 0 0 0 2px #5a3a08}
.schm:after{content:attr(data-n);position:absolute;inset:5px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#8a1a2a,#4a0a14 70%);display:flex;align-items:center;justify-content:center;font:700 17px Cinzel,Georgia,serif;color:#ffe28a;text-shadow:0 1px 0 #000}
.scht{flex:1;min-width:0;font-size:11px;line-height:1.45;color:#f6eedc}
.scht b{display:block;font:700 13px Cinzel,Georgia,serif;color:#ffd23f;letter-spacing:.5px}
.scht small{color:#c9b58f}
.scg{display:grid;grid-template-columns:repeat(3,1fr);gap:7px 6px;padding:0 1px}
@media(max-width:640px){.scg{grid-template-columns:repeat(5,1fr);gap:5px}}
.scc{--p:0%;--c:#555;position:relative;aspect-ratio:1;border-radius:50%;padding:4px;cursor:pointer;background:conic-gradient(#ffe066 0,#ffd23f var(--p),#1a0408 0);box-shadow:0 2px 5px #000a,inset 0 0 0 1px #000;transition:transform .15s;user-select:none;-webkit-tap-highlight-color:transparent}
.scc:active{transform:scale(.94)}
.scc.on{box-shadow:0 0 0 2px #ffd23f,0 0 14px #ffd23f88,0 2px 5px #000a}
.scc.last .scf{animation:scGlow 1.6s ease-in-out infinite}
.scc.up{animation:scSpin .9s cubic-bezier(.3,1.4,.4,1) 1}
.scc.up:before{content:'';position:absolute;inset:-10px;border-radius:50%;background:radial-gradient(circle,#fff6c8 0%,#ffd23f55 35%,transparent 70%);animation:scBurst .9s ease-out 1;pointer-events:none}
.sci{position:absolute;inset:4.5px;border-radius:50%;background:repeating-conic-gradient(#e9c25a 0 5deg,#8a5e0c 5deg 10deg);box-shadow:0 0 0 1px #000c,inset 0 0 0 1px #5a3a08}
.scf{position:absolute;inset:8.5px;border-radius:50%;background:radial-gradient(circle at 35% 30%,color-mix(in srgb,var(--c) 70%,#fff) 0%,var(--c) 45%,color-mix(in srgb,var(--c) 60%,#000) 100%);box-shadow:inset 0 0 0 1px #0006,inset 0 2px 4px #fff3;display:flex;align-items:center;justify-content:center}
.scf svg{width:58%;height:58%;fill:none;stroke:#fff;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 1px 0 #0008)}
.scl{position:absolute;right:-2px;bottom:-2px;min-width:20px;height:20px;padding:0 4px;border-radius:10px;background:linear-gradient(#ffe28a,#c9951a);color:#2a1604;font:700 11px Cinzel,Georgia,serif;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px #000c,inset 0 0 0 1px #fff6}
.scl.max{background:linear-gradient(#fff6c8,#ffd23f);box-shadow:0 0 8px #ffd23f,0 1px 3px #000c}
.scd{margin-top:0;padding:8px;border:1px solid #d9a52066;border-radius:8px;background:linear-gradient(180deg,#2a0a10,#1a0408);font-size:11px;color:#f6eedc}
.scd h4{margin:0 0 4px;font:700 14px Cinzel,Georgia,serif;color:#ffd23f;display:flex;justify-content:space-between;align-items:baseline}
.scd h4 span{font:700 18px Cinzel,Georgia,serif;color:#fff}
.scb{height:8px;border-radius:4px;background:#000a;border:1px solid #000;overflow:hidden;margin:4px 0 2px}
.scb i{display:block;height:100%;background:linear-gradient(90deg,#c9951a,#ffe28a);box-shadow:0 0 6px #ffd23f88}
.scx{display:flex;justify-content:space-between;color:#c9b58f;font-size:10px}
.scu{margin-top:6px;border-top:1px solid #d9a52033;padding-top:5px}
.scu div{display:flex;gap:6px;align-items:baseline;padding:2px 0}
.scu b{flex:0 0 26px;font:700 11px Cinzel,Georgia,serif;color:#ffd23f}
.scu .done{opacity:.45}.scu .done b{color:#9bff9b}
.scu .next b{color:#fff}
.scn{color:#9bff9b;font-size:10px;margin-top:4px}
@keyframes scGlow{0%,100%{box-shadow:inset 0 0 0 1px #0006,inset 0 2px 4px #fff3}50%{box-shadow:inset 0 0 0 1px #0006,inset 0 2px 4px #fff3,0 0 12px 3px #ffd23f}}
@keyframes scSpin{0%{transform:rotateY(0)}100%{transform:rotateY(720deg)}}
@keyframes scBurst{0%{opacity:1;transform:scale(.3)}100%{opacity:0;transform:scale(1.6)}}
@keyframes scIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
"""

JS = r"""
// --- Skill coins (the Skills tab)
const SCC={at:'#a8242a',str:'#2a8a3a',def:'#2b57b8',hp:'#c23a5a',pr:'#8a7ad8',wc:'#7a4a1e',mi:'#4e6a7a',fi:'#2f86c8',ck:'#b05a1e',sm:'#6a6a72',fm:'#e0661a',ag:'#3a3a9a',sl:'#4a4a4a',fa:'#4a9a3a',cn:'#b89050'};
const SCI={
at:'<path d="M5 19 15 9m0 0 2-2m-2 2 2 2M15 9l4-4M4 20l1-3 2 2z"/>',
str:'<path d="M5 15c0-5 3-8 7-8s7 3 7 8M5 15v3h14v-3M9 7V5a3 3 0 0 1 6 0v2"/>',
def:'<path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z"/><path d="M12 7v10"/>',
hp:'<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
pr:'<path d="M12 3v3M12 18v3M3 12h3M18 12h3M6 6l2 2M16 16l2 2M6 18l2-2M16 8l2-2"/><circle cx="12" cy="12" r="3"/>',
wc:'<path d="M5 19 13 11M13 11l-2-2 4-4 4 4-4 4zM6 20l-2-2 2-2 2 2z"/>',
mi:'<path d="M5 19 14 10M9 5c3-1 7 0 10 4M9 5l1.5 1.5M19 9l-1.5-1.5"/>',
fi:'<path d="M3 12c3-4 7-6 11-6l2 3 4-3-1 6 1 6-4-3-2 3c-4 0-8-2-11-6z"/><circle cx="8" cy="11" r=".8"/>',
ck:'<path d="M5 10h14l-1 9H6zM3 10h18M9 7c0-2 2-2 2-4M13 7c0-2 2-2 2-4"/>',
sm:'<path d="M4 9h11l4-2v4h-4l-2 2v4h3v2H7v-2h3v-4l-3-2H4z"/>',
fm:'<path d="M12 21c-4 0-6-2.5-6-6 0-3 2-5 3-7 0 2 1 3 2 3 0-3 1-6 4-8-1 4 4 6 4 11 0 4-3 7-7 7z"/>',
ag:'<circle cx="15" cy="4.5" r="1.6"/><path d="M14 8l-4 3 2 3-3 6M14 8l3 3 3-1M14 8l-1 5 3 3 1 4"/>',
sl:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/>',
fa:'<path d="M12 21v-9M12 12c0-4 3-6 7-6 0 4-3 6-7 6zM12 15c0-3-2.5-5-6-5 0 3 2.5 5 6 5z"/>',
cn:'<path d="M4 11 12 4l8 7M6 10v10h12V10M10 20v-5h4v5"/>'};
const SCW={hp:'Every level is one more max health.',str:'Every level hits harder.',at:'Higher levels wield better blades and land more hits.',def:'Higher levels wear better armour and take fewer hits.',pr:'Prayer points equal your level. Bury bones to train it.',wc:'Chop faster. Your axe is only as good as your level lets it be.',mi:'Mine faster and reach new ores.',fi:'Catch more, miss less.',ck:'Burn less. Cook more.',sm:'Hammer bars into armour and blades at the forge.',fm:'Light fires. Keep the braziers fed.',ag:'Run further. Clear obstacles. Counts toward combat level.',sl:'Bounty XP per kill equals the monster\'s health.',fa:'Plant seeds, come back, harvest.',cn:'Build furniture in your own house.'};
function scUnl(k){const u=[];try{
if(k=='at')Object.keys(WREQ).forEach(w=>u.push([WREQ[w],IN[w]]));
if(k=='def')Object.keys(ARMS).forEach(a=>u.push([ARMS[a][1],IN[a]]));
if(k=='sm')ARMREC.forEach(r=>u.push([r[2],IN[r[0]]]));
if(k=='mi'){u.push([15,'Iron ore from copper rocks']);u.push([30,'Coal from tin rocks'])}
if(k=='fm')u.push([10,'Feed the braziers']);
if(k=='fi')u.push([5,'Nemo\'s fishing job']);
if(k=='pr')PRY.forEach(p=>u.push([p[1],p[0]]));
if(k=='ag')u.push([5,'Stepping stones']);
if(k=='fa')Object.values(CROPS).forEach(c=>u.push([c[2],c[0]+' seeds']));
if(k=='cn')Object.values(FURN).forEach(l=>l.forEach(f=>u.push([f[1],f[0]])));
}catch(e){}
u.push([100,'Mastery: the '+NM[k]+' cape']);return u.filter(x=>x[0]>1).sort((a,b)=>a[0]-b[0])}
let scSel=null;const SCUP={};let scLastRender=0;
function SCH(){const ks=Object.keys(NM),tl=ks.reduce((a,k)=>a+lvl(st.xp[k]||0),0),tx=ks.reduce((a,k)=>a+(st.xp[k]||0),0),n100=ks.filter(k=>lvl(st.xp[k]||0)>=100).length;
let hd='<div class="sch"><div class="schm" data-n="'+tl+'"></div><div class="scht"><b>Total level '+tl+'</b>Combat level '+combatLvl()+'<br><small>'+Math.floor(tx).toLocaleString()+' XP'+(n100?' · '+n100+' mastered':'')+' · tap a coin</small></div></div>';let o='<div class="scg">';
for(const k of ks){const x=st.xp[k]||0,l=lvl(x),lo=XT[l-1],hi=l<100?XT[l]:lo+1,pc=l>=100?100:Math.max(0,Math.min(100,100*(x-lo)/(hi-lo)));
o+='<div class="scc'+(scSel==k?' on':'')+(st.last==k?' last':'')+(Date.now()-(SCUP[k]||0)<1200?' up':'')+'" data-sc="'+k+'" style="--p:'+pc.toFixed(1)+'%;--c:'+SCC[k]+'" title="'+NM[k]+' '+l+'"><div class="sci"></div><div class="scf"><svg viewBox="0 0 24 24">'+SCI[k]+'</svg></div><div class="scl'+(l>=100?' max':'')+'">'+l+'</div></div>'}
o+='</div>';let d='';
if(scSel&&NM[scSel]){const k=scSel,x=st.xp[k]||0,l=lvl(x),lo=XT[l-1],hi=l<100?XT[l]:lo+1,pc=l>=100?100:Math.max(0,Math.min(100,100*(x-lo)/(hi-lo))),un=scUnl(k),nx=un.find(u=>u[0]>l);
d+='<div class="scd"><h4><span style="font:inherit;color:inherit">'+NM[k]+' <i data-sc="'+k+'" style="font-style:normal;color:#c9b58f;cursor:pointer;padding:0 6px" title="Back to all skills">&times;</i></span><span>'+(k=='hp'?st.hp+' / ':'')+l+(l>=100?' <small style="font-size:10px;color:#ffd23f">MAX</small>':'')+'</span></h4><div style="color:#c9b58f">'+SCW[k]+'</div><div class="scb"><i style="width:'+pc.toFixed(1)+'%"></i></div><div class="scx"><span>'+Math.floor(x).toLocaleString()+' XP</span><span>'+(l>=100?'mastered':Math.ceil(hi-x).toLocaleString()+' to level '+(l+1))+'</span></div>';
if(nx)d+='<div class="scn">Next: '+nx[1]+' at level '+nx[0]+'</div>';
d+='<div class="scu">'+un.slice(0,12).map(u=>'<div class="'+(u[0]<=l?'done':(nx&&u===nx?'next':''))+'"><b>'+u[0]+'</b><span>'+u[1]+'</span></div>').join('')+'</div></div>'}
return (d||hd)+(d?o.replace('<div class="scg">','<div class="scg" style="margin-top:9px">'):o)}
$('pc').addEventListener('click',e=>{const c=e.target.closest('[data-sc]');if(!c||tab!='sk')return;scSel=scSel==c.dataset.sc?null:c.dataset.sc;renderPanel();$('pc').scrollTop=0});
"""

# 1. CSS
i = h.find('</style>')
assert i > 0
h = h[:i] + CSS + h[i:]

# 2. the Skills tab body
start = h.find("else if(tab=='sk')h=Object.keys(NM).map(k=>{")
end_marker = "reduce((q,k)=>q+lvl(st.xp[k]),0)+'</b></div>';\n"
end = h.find(end_marker, start)
assert start > 0 and end > start, 'skills tab anchor'
h = h[:start] + "else if(tab=='sk')h=SCH();\n" + h[end + len(end_marker):]

# 3. the helpers, right before renderPanel
rep("function renderPanel(){if(!pOpen)return;", JS + "\nfunction renderPanel(){if(!pOpen)return;")

# 4. level-ups spin the coin; XP gains refresh the tab (throttled)
rep("function addXp(k,n){const b=lvl(st.xp[k]);st.xp[k]+=n;st.last=k;xpDrop(k,n);const a=lvl(st.xp[k]);if(a>b){",
    "function addXp(k,n){const b=lvl(st.xp[k]);st.xp[k]+=n;st.last=k;xpDrop(k,n);const a=lvl(st.xp[k]);"
    "if(a>b)SCUP[k]=Date.now();if(pOpen&&tab=='sk'&&(a>b||Date.now()-scLastRender>400)){scLastRender=Date.now();setTimeout(renderPanel,0)}if(a>b){")

open(PATH, 'w', encoding='utf-8').write(h)
print('skill coins applied')
