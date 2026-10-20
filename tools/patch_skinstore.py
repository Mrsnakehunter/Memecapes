#!/usr/bin/env python3
"""The skin store you can see: a picture of every skin, a big Skin of the Month card, and "Try it on".

Albert: "people are visual people, they need images of what they are buying, not just names".
  - Every skin has a picture (models/skins/thumbs/<id>.jpg): capes on the character seen from behind, weapons on
    their own. Made with tools/dev/charview (tools/skinthumbs.py).
  - The Wardrobe is a picture grid: your skins, the Skin of the Month, then the store split into Capes and Weapons.
    Tap a skin for a big picture, its description and what you can do with it (wear it, take it free as a holder,
    or its price).
  - "Try it on" shows the skin on your own character for 30 seconds while the camera circles round you, with a bar
    at the top (back to the Wardrobe / stop). Capes work on the 3D Adventurer look, with or without a cape on;
    weapon skins show in your hand whatever you are holding. Nothing is bought or saved by trying.
New UI uses its own skx* class names (the game has many short global ones).
Run from the repo root after patch_sotm.py:  python3 tools/patch_skinstore.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


CSS = ("#mb.skx{max-width:600px}"
       ".skxh{font-size:12px;color:#e9dcc0;margin:0 0 8px}"
       ".skxs{font:bold 13px Georgia,serif;color:#ffd23f;margin:14px 0 6px;letter-spacing:.5px;text-transform:uppercase}"
       ".skxg{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:8px}"
       ".skxc{position:relative;background:#1a070c;border:1px solid #6b4a06;border-radius:8px;overflow:hidden;cursor:pointer;transition:transform .12s,border-color .12s}"
       ".skxc:hover{transform:translateY(-2px);border-color:#ffd23f}"
       ".skxc img{display:block;width:100%;aspect-ratio:1/1;object-fit:cover;background:#2a0b12}"
       ".skxc .skxn{font:bold 12px Georgia,serif;color:#fff3d6;padding:5px 7px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".skxc .skxl{font-size:11px;color:#c9b89a;padding:0 7px 6px;display:flex;justify-content:space-between}"
       ".skxc .skxl b{color:#ffd23f;font-weight:bold}"
       ".skxtag{position:absolute;top:6px;left:6px;font:bold 10px Georgia,serif;padding:2px 6px;border-radius:9px;background:#ffd23f;color:#2b0810}"
       ".skxtag.on{background:#39d26a;color:#04220e}"
       ".skxm1{display:flex;gap:12px;align-items:center;background:linear-gradient(90deg,#3d0f19,#24060c);border:1px solid #ffd23f;border-radius:10px;padding:8px;cursor:pointer;box-shadow:0 0 18px #ffd23f33}"
       ".skxm1 img{width:132px;height:132px;border-radius:8px;flex:none;object-fit:cover}"
       ".skxm1 .k{font:bold 11px Georgia,serif;color:#ffd23f;text-transform:uppercase;letter-spacing:.6px}"
       ".skxm1 .n{font:bold 17px Georgia,serif;color:#fff3d6;margin:2px 0}"
       ".skxm1 .d{font-size:12px;color:#e9dcc0}"
       ".skxd{text-align:center}.skxd img{width:min(100%,380px);aspect-ratio:1/1;border-radius:10px;border:2px solid #6b4a06;box-shadow:0 8px 30px #000a}"
       ".skxd h2{margin:10px 0 0}.skxd .t{color:#c9b89a;font-size:12px}.skxd p{margin:6px 0}"
       ".skxa{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:10px 0}"
       ".skxa button{font-size:13px;padding:7px 14px}.skxa .p{font:bold 16px Georgia,serif;color:#ffd23f;align-self:center}"
       ".skxq{font-size:11px;color:#c9b89a}"
       "#skxtry{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:60;display:none;gap:10px;align-items:center;"
       "background:#24060cee;border:2px solid #d9a520;border-radius:10px;padding:8px 12px;color:#f6eedc;font:13px Georgia,serif;box-shadow:0 8px 30px #000a;max-width:94vw;flex-wrap:wrap;justify-content:center}"
       "#skxtry b{color:#ffd23f}"
       "@media (max-width:600px){#skxtry{top:auto;bottom:170px;font-size:12px;padding:6px 8px}#skxtry button{padding:4px 8px}}")
rep(".hit{position:fixed;width:26px;", CSS + ".hit{position:fixed;width:26px;")

JS = r"""
// ---- the skin store you can see (tools/patch_skinstore.py)
const skImg=id=>'models/skins/thumbs/'+id+'.jpg';
let SKTRY=null,SKTRYI=0;
function skTry(id){const s=skById(id);if(!s)return;if(s.g=='cape'&&st.body===0)return say('Try-on shows capes on the 3D Adventurer look. Switch it on in the Gear tab.','#c00');
 const d0=SKTRY?SKTRY.d:distT,p0=SKTRY?SKTRY.p:pit;skTryEnd(1);SKTRY={id,g:s.g,t:performance.now()+30000,d:d0,p:p0};M.style.display='none';distT=Math.min(distT,4.4);pit=.5;
 SKTRYI=setInterval(()=>{if(!SKTRY||performance.now()>SKTRY.t)return skTryEnd();yaw+=.016},30);
 let b=$('skxtry');if(!b){b=document.createElement('div');b.id='skxtry';document.body.appendChild(b)}
 b.innerHTML='<span>Trying on <b>'+s.n+'</b></span><button id="skxtb">Back to the Wardrobe</button><button class="ghost" id="skxts">Stop</button>';b.style.display='flex';
 $('skxtb').onclick=()=>{skTryEnd();skDetail(id)};$('skxts').onclick=()=>skTryEnd()}
function skTryEnd(quiet){if(SKTRYI)clearInterval(SKTRYI);SKTRYI=0;if(SKTRY&&!quiet){distT=SKTRY.d;pit=SKTRY.p}SKTRY=null;const b=$('skxtry');if(b)b.style.display='none'}
function skCard(s,tag){const own=skOwn(s.id),on=(st.wear||{})[s.g]==s.id;
 return '<div class="skxc" data-sd="'+s.id+'"><img alt="'+s.n+'" src="'+skImg(s.id)+'" onerror="this.style.visibility=\'hidden\'">'+(on?'<span class="skxtag on">On</span>':own?'<span class="skxtag">Yours</span>':tag?'<span class="skxtag">'+tag+'</span>':'')+
  '<div class="skxn">'+s.n+'</div><div class="skxl"><span>'+SKGN[s.g]+'</span>'+(own?'':'<b>$2.99</b>')+'</div></div>'}
function skWire(){MB.querySelectorAll('[data-sd]').forEach(b=>b.onclick=()=>skDetail(b.dataset.sd))}
function wardrobeUI(){M.style.display='flex';MB.onclick=null;MB.className='skx';const W=st.wear||{},HC=HPK()&&HPK().canClaim,S=sotmNow();
 let h='<div id="skxroot"><h2 id="wrd">Wardrobe</h2><p class="skxh">Skins change how your cape or a weapon type looks. They never change stats. Tap any skin to see it big and try it on.</p>';
 if(HC)h+='<div class="skxh" style="padding:8px;border:1px solid #ffd23f;border-radius:6px;color:#ffd23f">Holder gift: pick any one skin below and take it free.</div>';
 if(S.skin){const s=skById(S.skin);h+='<div class="skxs">'+(S.soon?'Coming soon':'Skin of the Month')+'</div><div class="skxm1" data-sd="'+s.id+'"><img alt="'+s.n+'" src="'+skImg(s.id)+'"><div><div class="k">'+(S.soon?'The first Skin of the Month':'This month')+'</div><div class="n">'+s.n+'</div><div class="d">'+s.d+'</div><div class="d" style="margin-top:6px;color:#ffd23f">'+(skOwn(s.id)?'You own it.':'Free for holders of 0.1% of $CAPEZ after 30 days of holding. Everyone else: $2.99.')+'</div></div></div>'}
 const own=SKN.filter(s=>skOwn(s.id));
 if(own.length)h+='<div class="skxs">Your skins</div><div class="skxg">'+own.map(s=>skCard(s)).join('')+'</div>';
 {const me=NETS.partner;if(me&&me.live){const on=W.cape==='ptc';h+='<div class="row" style="margin-top:8px"><span><b style="color:#ffd23f">Partner cape</b> <small>(while you hold 3%)</small></span><button data-pw="1">'+(on?'Take off':'Wear')+'</button></div>'}}
 const store=SKN.filter(s=>!skOwn(s.id)&&s.ok);
 const caps=store.filter(s=>s.g=='cape'),wep=store.filter(s=>s.g!='cape');
 if(caps.length)h+='<div class="skxs">Capes</div><div class="skxg">'+caps.map(s=>skCard(s,s.id==S.skin&&!S.soon?'Of the month':'')).join('')+'</div>';
 if(wep.length)h+='<div class="skxs">Weapons</div><div class="skxg">'+wep.map(s=>skCard(s,s.id==S.skin&&!S.soon?'Of the month':'')).join('')+'</div>';
 h+='<p class="skxq" style="margin-top:12px">$2.99 each. Card payments open with the game servers; until then skins come as redeem codes from the shop on memecapes.com. Skins are tied to your account: they cannot be traded.</p><button id="x">Close</button></div>';
 MB.innerHTML=h;MB.scrollTop=0;$('x').onclick=()=>M.style.display='none';skWire();
 MB.querySelectorAll('[data-pw]').forEach(b=>b.onclick=()=>{st.wear=st.wear||{};st.wear.cape=st.wear.cape==='ptc'?null:'ptc';save();ui();wardrobeUI()})}
function skDetail(id){const s=skById(id);if(!s)return wardrobeUI();M.style.display='flex';MB.className='skx';
 const own=skOwn(id),on=(st.wear||{})[s.g]==id,H=HPK(),HC=H&&H.canClaim,S=sotmNow(),isM=S.skin==id&&!S.soon;
 let act='<button data-try="'+id+'">Try it on</button>';
 if(own)act+='<button data-wr="'+id+'">'+(on?'Take off':'Wear it')+'</button>';
 else if(isM&&H&&H.canSotm)act+='<button data-sm="1">Take it free (holder gift)</button>';
 else if(HC)act+='<button data-hc="'+id+'">Take it free (holder gift)</button>';
 else act+='<span class="p">$2.99</span>';
 let h='<div id="skxroot" class="skxd"><img alt="'+s.n+'" src="'+skImg(id)+'"><h2>'+s.n+'</h2><div class="t">'+SKGN[s.g]+(isM?' · Skin of the Month':'')+'</div><p>'+s.d+'</p><div class="skxa">'+act+'</div>'+
  '<p class="skxq">Looks only: it never changes stats.'+(s.g=='cape'?' Works on every cape except the MemeCape.':' Shows on every '+SKGN[s.g].toLowerCase()+' you hold.')+' Tied to your account, not tradable.'+(own?'':isM?' Free for holders of 0.1% of $CAPEZ after 30 days of holding.':'')+'</p>'+
  (own||HC?'':'<p class="skxq">Card payments open with the game servers; until then skins come as redeem codes from the shop on memecapes.com.</p>')+'<button class="ghost" id="skxbk">Back to the Wardrobe</button></div>';
 MB.innerHTML=h;MB.scrollTop=0;$('skxbk').onclick=()=>wardrobeUI();sotmWire();
 MB.querySelectorAll('[data-try]').forEach(b=>b.onclick=()=>skTry(b.dataset.try));
 MB.querySelectorAll('[data-hc]').forEach(b=>b.onclick=()=>{netSaveNow();netSend({t:'holderClaim',skin:b.dataset.hc});b.disabled=true;b.textContent='...'});
 MB.querySelectorAll('[data-wr]').forEach(b=>b.onclick=()=>{st.wear=st.wear||{};st.wear[s.g]=st.wear[s.g]==s.id?null:s.id;save();ui();skDetail(id)})}
"""
# swap the old Wardrobe for the picture one (it was built up by patch_skins, patch_holder, patch_partner and patch_sotm)
i = h.index('function wardrobeUI(){'); j = h.index('\nwindow.mcWardrobe=', i)
old = h[i:j]
assert h.count('function wardrobeUI(){') == 1 and 'sotmHTML()' in old and "data-hc" in old and "data-pw" in old, 'the old Wardrobe changed'
h = h[:i] + JS.strip('\n') + h[j:]
# the modal keeps its wide class while the Wardrobe is open
rep("!MB.querySelector('#mkroot,#trroot')", "!MB.querySelector('#mkroot,#trroot,#skxroot')")
# trying on: the cape on your back (even with no cape on) and the weapon skin in your hand
rep("function capeSkin(){", "function capeSkin(){if(SKTRY&&SKTRY.g=='cape')return SKTRY.id;")
rep("const CBM=st.eq&&st.eq.cape&&st.body!==0?capeBody(PK,st.eq.cape,capeSkin()):null;",
    "const SKTC=SKTRY&&SKTRY.g=='cape',CBM=(SKTC||st.eq&&st.eq.cape)&&st.body!==0?capeBody(PK,SKTC?'cape_try':st.eq.cape,capeSkin()):null;")
rep("else if(act&&act.k=='fish'&&has('net'))k='net';if(!k)return null;if(HTEST)return HTEST;",
    "else if(act&&act.k=='fish'&&has('net'))k='net';if(SKTRY&&SKTRY.g!='cape'&&WAV.has('w_'+SKTRY.id))return 'w_'+SKTRY.id;if(!k)return null;if(HTEST)return HTEST;")
# a holder gift or a monthly skin lands on the detail page's skin: show the Wardrobe again
rep("function hpkRefresh(){if(M.style.display=='none')return;if($('wrd'))wardrobeUI();",
    "function hpkRefresh(){if(M.style.display=='none')return;if($('wrd')||$('skxroot'))wardrobeUI();")

open(PATH, 'w', encoding='utf-8').write(h)
print('skin store patch applied')
