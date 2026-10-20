#!/usr/bin/env python3
"""Skin of the Month: one new skin each month, free for $CAPES holders of 0.1% (1,000,000 $CAPES) after 30 days.

Rules (agreed with Albert, Oct 13): a skin changes how a cape or a weapon type looks, never stats. Holders whose linked
wallet keeps 0.1% of all $CAPES for 30 days take that month's skin free at any bank or in the Wardrobe; everyone else
buys it in the skin store for $2.99 and it stays in the store after its month. Once taken it is yours for good. Skins
are tied to the account: not tradable. One free monthly skin per account per month (the server decides and keeps
the claims; server/server.js "Skin of the Month"). 1% holders keep Cape Club and a free pick every 14 days.

The line-up (30 months, from SOTM_START) is the same list as SOTM in server/server.js. A month whose skin is not made
yet (a weapon skin still to model) shows no Skin of the Month. Before month 1 the Wardrobe shows the first one as
coming. No dates are shown anywhere.
Run from the repo root after patch_tokenplan.py:  python3 tools/patch_sotm.py
"""
import json
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


SOTM_START = '2026-11'
SOTM = ['cs_laser_grid', 'sk_candle', 'cs_pond_lily', 'cs_stonks_arrow', 'sk_banhammer', 'cs_moon_phases', 'cs_wow_plaid', 'sk_copium',
        'cs_whale_waves', 'cs_shades_on', 'sk_chonkaxe', 'cs_royal_ermine', 'cs_the_burn', 'sk_oracle', 'cs_rug_fringe', 'cs_hodl_frost',
        'sk_frostfang', 'cs_jungle_leaves', 'cs_rocket_trail', 'sk_sweeper', 'cs_wen_lambo', 'cs_chad_marble', 'sk_gascleaver',
        'cs_up_only_rainbow', 'cs_bonk_stripes', 'sk_goldrush', 'cs_copium_crystal', 'cs_comfy_knit', 'sk_bubble', 'sk_wrench']
srv = open('server/server.js', encoding='utf-8').read()
assert all("'" + s + "'" in srv for s in SOTM) and "SOTM_START = process.env.SOTM_START || '" + SOTM_START + "'" in srv, 'line-up differs from the server'

JS = r"""
// ---- Skin of the Month (tools/patch_sotm.py; who gets it free is decided by the server)
const SOTM_START='""" + SOTM_START + "',SOTM=" + json.dumps(SOTM) + r""";
function sotmNow(){const d=new Date(),y=+SOTM_START.slice(0,4),m=+SOTM_START.slice(5),i=(d.getUTCFullYear()-y)*12+d.getUTCMonth()-(m-1);
 const id=i<0?SOTM[0]:i<SOTM.length?SOTM[i]:'',s=id&&skById(id);return {soon:i<0,skin:s&&s.ok?id:''}}
function sotmHTML(){const S=sotmNow();if(!S.skin)return '';const s=skById(S.skin),H=HPK(),own=skOwn(S.skin);
 let h='<div style="margin-top:10px;padding:8px;border:1px solid #ffd23f;border-radius:6px;font-size:12px"><b style="color:#ffd23f">'+(S.soon?'Coming soon: the first Skin of the Month':'Skin of the Month')+'</b><br><b>'+s.n+'</b> <small>('+SKGN[s.g]+')</small><br><span style="color:#ccc">'+s.d+'</span><br>';
 if(own)h+='<span style="color:#7dff9a">You own it.</span>';
 else if(!S.soon&&H&&H.canSotm)h+='<button data-sm="1">Take it free (holder gift)</button>';
 else if(!S.soon&&H&&H.sotmGot)h+='<span style="color:#7dff9a">You took this month\'s skin.</span>';
 else h+='Free for holders of 0.1% of $CAPES (1,000,000) after 30 days of holding. Everyone else: $2.99 in the store.';
 return h+'</div>'}
function sotmWire(){MB.querySelectorAll('[data-sm]').forEach(b=>b.onclick=()=>{netSaveNow();netSend({t:'holderSotm'});b.disabled=true;b.textContent='...'})}
"""
rep("function wardrobeUI(){", JS + "function wardrobeUI(){")
# the Wardrobe: the Skin of the Month above the store
rep("h+='<h2 style=\"margin-top:14px\">Skin store</h2>", "h+=sotmHTML();h+='<h2 style=\"margin-top:14px\">Skin store</h2>")
rep("MB.querySelectorAll('[data-hc]').forEach(b=>b.onclick=", "sotmWire();MB.querySelectorAll('[data-hc]').forEach(b=>b.onclick=")
# the bank's holder box: the 0.1% tier and its claim
rep("one free skin from the skin store every '+days+' days.</span><br>';",
    "one free skin from the skin store every '+days+' days.<br>Hold at least '+(H?H.sotmNeed:0.1)+'% (1,000,000 $CAPES) for '+(H?H.sotmDays:30)+' days: the Skin of the Month free.</span><br>';")
rep("Below '+need+'%: no perks right now. Perks start", "Below '+need+'%: no Cape Club right now. Cape Club starts")
rep(" return h+'<button class=\"ghost\" data-hp=\"unlink\">Unlink wallet</button>",
    " if(H.sotm){const sn=skById(H.sotm);h+=H.sotmGot?'<span style=\"font-size:12px;color:#7dff9a\">Skin of the Month ('+sn.n+'): taken.</span><br>':H.canSotm?'<span style=\"font-size:12px;color:#ffd23f\">Skin of the Month ('+sn.n+') is ready for you.</span> <button data-hp=\"sotm\">Take it free</button><br>':H.sotmOk?'<span style=\"font-size:12px\">Skin of the Month ('+sn.n+'): free on '+hpkDate(H.sotmAt)+' if you keep '+H.sotmNeed+'%.</span><br>':'<span style=\"font-size:12px;color:#ccc\">Below '+H.sotmNeed+'%: the Skin of the Month is $2.99 in the store.</span><br>'}\n"
    " return h+'<button class=\"ghost\" data-hp=\"unlink\">Unlink wallet</button>")
rep("function holderWire(){MB.querySelectorAll('[data-hp]').forEach(b=>b.onclick=()=>{if(b.dataset.hp=='link')hpkLink();else netSend({t:'walletUnlink'})})}",
    "function holderWire(){MB.querySelectorAll('[data-hp]').forEach(b=>b.onclick=()=>{if(b.dataset.hp=='link')hpkLink();else if(b.dataset.hp=='sotm'){netSaveNow();netSend({t:'holderSotm'});b.disabled=true}else netSend({t:'walletUnlink'})})}")

open(PATH, 'w', encoding='utf-8').write(h)
print('skin of the month patch applied')
