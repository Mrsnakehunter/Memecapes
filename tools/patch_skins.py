#!/usr/bin/env python3
"""Skins: new looks for weapons and capes, sold for $2.99 each (see the Shop and Membership Plan).

  weapon skins  models/w_sk_<id>.json (made in Meshy, converted with tools/glb2mdl.py), held in place
                of every weapon of that type; same grip and size settings as the weapon they replace
  cape skins    models/skins/<id>_m.jpg / _f.jpg (tools/capeskins.py), painted onto the caped bodies;
                not on the hooded MemeCape and Quest cape

Owned skins live in st.skins, the ones switched on in st.wear (one per weapon type, one for capes).
The Wardrobe (a button in the Gear tab) switches them on and off and shows the skin store. Until card
payments exist, a skin is unlocked with a redeem code ({"skin": "<id>"}, tools/mkcode.py skin <id>).
Run from the repo root after patch_story.py:  python3 tools/patch_skins.py
"""
import glob, json, os

PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# group = which weapons a skin covers
SKINS = [
    ('sk_laser', 'Laser Eyes Blade', 'sword', 'A silver crystal blade with a glowing red gem eye set in its gold guard.'),
    ('sk_upaxe', 'Up Only Axe', 'axe', 'A steel axe with a green crystal head and a gold tip that points up. Only up.'),
    ('sk_dpick', 'Diamond Hands Pick', 'pick', 'Two blue diamond points held in a golden fist. Never lets go.'),
    ('sk_rocket', 'Moon Rocket Bat', 'club', 'A little rocket on a stick, flames and all. To the moon.'),
    ('sk_rug', 'The Rug Pull', 'club', 'A mallet made of a rolled-up rug. Tassels included.'),
    ('sk_moon', 'Crescent Staff', 'staff', 'A golden crescent moon cradling a Meme Coin.'),
    ('cs_green_candles', 'Green Candles', 'cape', 'Rising green candles on dark velvet.'),
    ('cs_red_candles', 'Red Candles', 'cape', 'Falling red candles, for the bear market.'),
    ('cs_laser_eyes', 'Laser Eyes', 'cape', 'Two red beams crossing your back.'),
    ('cs_diamond_hands', 'Diamond Hands', 'cape', 'A quilted diamond pattern with crystal glints.'),
    ('cs_moon_night', 'Moon Night', 'cape', 'Night sky, stars and a crescent moon.'),
    ('cs_coin_gold', 'Meme Coin Gold', 'cape', 'Gold coins with happy little faces.'),
]
# how a weapon skin sits in the hand when it differs from the weapon it replaces (see WCFG in patch_held.py):
# [length, grip height as a fraction of the length, carry, tilt, swing]
HOLD = {'sk_laser': [1.25, .3, 'f', 25, 20], 'sk_upaxe': [1.0, .12, 'a', -40, 12], 'sk_rocket': [.95, .22, 'f', 35, 20],
        'sk_moon': [1.7, .4, 'v', 22, 8], 'sk_rug': [.95, .1, 'f', 35, 20], 'sk_dpick': [.95, .12, 'a', -40, 12]}
have = lambda sid: os.path.exists(f'models/w_{sid}.json') if sid.startswith('sk_') else os.path.exists(f'models/skins/{sid[3:]}_m.jpg')
cat = [{'id': s, 'n': n, 'g': g, 'd': d, 'ok': 1 if have(s) else 0} for s, n, g, d in SKINS]

JS = r"""
// ---- skins: new looks for weapons and capes (tools/patch_skins.py)
const SKN=""" + json.dumps(cat) + r""",SKG={sword:'sword',isword:'sword',rsword:'sword',axe:'axe',iaxe:'axe',pick:'pick',ipick:'pick',club:'club',bbat:'club',bstaff:'staff',astaff:'staff',iscroll:'staff'},SKB={sword:'w_sword',axe:'w_axe',pick:'w_pick',club:'w_club',staff:'w_bstaff'},SKGN={sword:'Swords',axe:'Axes',pick:'Pickaxes',club:'Clubs and bats',staff:'Staffs and scrolls',cape:'Capes'};
const skOwn=id=>(st.skins||[]).includes(id),skById=id=>SKN.find(s=>s.id==id);
function skinW(k){const g=SKG[k],id=g&&st.wear&&st.wear[g];return id&&skOwn(id)?'w_'+id:null}
function capeSkin(){const id=st.wear&&st.wear.cape;return id&&skOwn(id)?id:null}
const SKHOLD=""" + json.dumps(HOLD) + r""";SKN.forEach(s=>{if(s.g!='cape'&&WCFG[SKB[s.g]])WCFG['w_'+s.id]=SKHOLD[s.id]||WCFG[SKB[s.g]]});
function skinGive(id){if(!skById(id))return false;(st.skins=st.skins||[]);if(!st.skins.includes(id))st.skins.push(id);(st.wear=st.wear||{})[skById(id).g]=id;save();return true}
function wardrobeUI(){M.style.display='flex';MB.onclick=null;const W=st.wear||{};let h='<h2>Wardrobe</h2><p style="font-size:12px">Skins change how a weapon type or your cape looks. They never change stats. Cape skins work on every cape except the MemeCape and the Quest cape.</p>';
 const own=SKN.filter(s=>skOwn(s.id));h+=own.length?'':'<p style="font-size:12px;color:#ccc">You do not own any skins yet.</p>';
 own.forEach(s=>{const on=W[s.g]==s.id;h+='<div class="row"><span><b style="color:#ffd23f">'+s.n+'</b> <small>('+SKGN[s.g]+')</small></span><button data-wr="'+s.id+'">'+(on?'Take off':'Wear')+'</button></div>'});
 h+='<h2 style="margin-top:14px">Skin store</h2><p style="font-size:12px">$2.99 each. Card payments open with the game servers; until then skins come as redeem codes from the shop on memecapes.com.</p>';
 SKN.filter(s=>!skOwn(s.id)).forEach(s=>{h+='<div class="row"><span><b>'+s.n+'</b> <small>('+SKGN[s.g]+')</small><br><small style="color:#ccc">'+s.d+'</small></span><span style="color:#ffd23f;white-space:nowrap">$2.99</span></div>'});
 h+='<br><button id="x">Close</button>';MB.innerHTML=h;$('x').onclick=()=>M.style.display='none';
 MB.querySelectorAll('[data-wr]').forEach(b=>b.onclick=()=>{const s=skById(b.dataset.wr);st.wear=st.wear||{};st.wear[s.g]=st.wear[s.g]==s.id?null:s.id;save();ui();wardrobeUI()})}
window.mcWardrobe=()=>wardrobeUI();
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", JS + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", 1)
# the held weapon: the skin's model in place of the weapon's own
rep("if(!k)return null;if(HTEST)return HTEST;const w='w_'+k;return WAV.has(w)?w:null}",
    "if(!k)return null;if(HTEST)return HTEST;const w='w_'+k,sw=skinW(k);return sw&&WAV.has(sw)?sw:WAV.has(w)?w:null}")
# the caped body: a cape skin replaces the cape's colour with its own painted texture
rep("function capeBody(base,k){if(CAPEM[k])return null;", "function capeBody(base,k,sk){if(CAPEM[k])return null;")
rep(" const src=base+'_cape',key='cb_'+src+'_'+k,m=MDL[key];", " const src=base+'_cape',key='cb_'+src+'_'+(sk||k),m=MDL[key];")
rep("CBP[key]=1;const d=JSON.parse(CBD[src]);if(!d.cm)return null;capePaint(d,capeCol(k)).then(",
    "CBP[key]=1;const d=JSON.parse(CBD[src]);if(!d.cm)return null;(sk?Promise.resolve('models/skins/'+sk.slice(3)+'_'+(base=='playerf'?'f':'m')+'.jpg'):capePaint(d,capeCol(k))).then(")
rep("capeBody(PK,st.eq.cape):null", "capeBody(PK,st.eq.cape,capeSkin()):null")
# redeem codes can give a skin
rep("if(g.item&&IN[g.item])put(g.item);", "if(g.item&&IN[g.item])put(g.item);{const L=(g.skins||[]).concat(g.skin?[g.skin]:[]).filter(skinGive);if(L.length)say((L.length>1?'New skins: ':'New skin: ')+L.map(i=>skById(i).n).join(', ')+'. '+(L.length>1?'They are':'It is')+' on; change it in the Wardrobe (Gear tab).','#0a0')}")
rep("Bought a custom cape or item in the shop? Enter its code.", "Bought a skin, a custom cape or an item in the shop? Enter its code.")
# the Wardrobe button in the Gear tab
rep("function EQH(){", "function EQH(){return EQH0()+'<div style=\"margin-top:8px\"><button onclick=\"mcWardrobe()\" style=\"width:100%\">Wardrobe and skins</button></div>'}function EQH0(){")

open(PATH, 'w', encoding='utf-8').write(h)
print('skins patch applied:', sum(c['ok'] for c in cat), 'of', len(cat), 'skins have their art')
