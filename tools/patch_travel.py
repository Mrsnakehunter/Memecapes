#!/usr/bin/env python3
"""Travel, shops and the market.

- The Meme Ring network is the Meme Telly. You can only Telly to a town you have walked into once;
  Castle Gigachad (home) is always open. Teleport tablets follow the same rule.
- New quest: The Grand Tour. Visit the eight meme towns in order, easiest first.
- Shops, the forge and the cape merchant show a picture of every item they sell.
- The Meme Exchange is now the Stock Market.
Run from the repo root after the other patches:  python3 tools/patch_travel.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


ICO = "'<svg viewBox=\"0 0 24 24\" style=\"width:22px;height:22px;vertical-align:middle;margin-right:4px\">'+IC[k]+'</svg>'"

# ---- pictures in the shop, the forge and the cape merchant
rep("""forEach(([k,p])=>h+='<div class="row"><span>'+IN[k]+'</span>'+(""",
    """forEach(([k,p])=>h+='<div class="row"><span>'+""" + ICO + """+IN[k]+'</span>'+(""")
rep("""forEach(([k,n,c,lv])=>h+='<div class="row"><span>'+n+' ('+c+' bars, lvl '+lv+')</span>'""",
    """forEach(([k,n,c,lv])=>h+='<div class="row"><span>'+""" + ICO + """+n+' ('+c+' bars, lvl '+lv+')</span>'""")
rep("""Object.keys(NM).map(k=>{const l=lvl(st.xp[k]);return '<div class="row"><span>'+NM[k]+' <small>('+l+'/100)</small></span>'""",
    """Object.keys(NM).map(k=>{const l=lvl(st.xp[k]);return '<div class="row"><span><svg viewBox="0 0 24 24" style="width:22px;height:22px;vertical-align:middle;margin-right:4px">'+IC['cape_'+k]+'</svg>'+NM[k]+' <small>('+l+'/100)</small></span>'""")
rep("""<span>Quest cape <small>(every quest done)</small></span>""",
    """<span><svg viewBox="0 0 24 24" style="width:22px;height:22px;vertical-align:middle;margin-right:4px">'+IC.qcape+'</svg>Quest cape <small>(every quest done)</small></span>""")
rep("""<span style="color:#ffd23f"><b>The MemeCape</b> <small>(hood and crown)</small></span>""",
    """<span style="color:#ffd23f"><svg viewBox="0 0 24 24" style="width:22px;height:22px;vertical-align:middle;margin-right:4px">'+IC.memecape+'</svg><b>The MemeCape</b> <small>(hood and crown)</small></span>""")

# ---- the Meme Telly
rep("ring:['Use','Meme Ring']", "ring:['Use','Meme Telly']")
rep("ring:'A ring of meme medallions humming with Clout.'", "ring:'A Meme Telly: a ring of meme medallions humming with Clout. It only knows towns you have been to.'")
rep("['ring','Travel by Meme Ring']", "['ring','Travel by Meme Telly']")
rep("""function ringUI(o){M.style.display='flex';MB.innerHTML='<h2>Meme Ring</h2><p style="font-size:12px">The mushrooms hum with fairy magic. Choose a destination:</p>'+XO.filter(x=>x.k=='ring'&&x!==o).map(r=>'<div class="row"><span>'+r.nm+' <b style="color:#ffd23f">'+r.code+'</b></span><button data-rg="'+r.x+','+r.y+'">Travel</button></div>').join('')""",
    """function ringUI(o){M.style.display='flex';MB.innerHTML='<h2>Meme Telly</h2><p style="font-size:12px">The medallions hum with Clout. The Telly only knows places you have walked into; Castle Gigachad is always home.</p>'+XO.filter(x=>x.k=='ring'&&x!==o).map(r=>'<div class="row"><span>'+r.nm+' <b style="color:#ffd23f">'+r.code+'</b></span>'+(townKnown(r.nm)?'<button data-rg="'+r.x+','+r.y+'">Telly</button>':'<span style="color:#888;font-size:11px">Not discovered</span>')+'</div>').join('')""")
rep("say('The ring whisks you away.','#1a4fb0')", "say('The Meme Telly whisks you away.','#1a4fb0')")
# tablets: same rule
rep("""const t=TW[{tab_w:0,tab_s:2,tab_p:1}[k]];st.inv.splice(i,1);""",
    """const t=TW[{tab_w:0,tab_s:2,tab_p:1}[k]];if(!townKnown(t.n))return say('The tablet fizzles. You have never been to '+t.n+', so the magic has nowhere to go.','#c00');st.inv.splice(i,1);""")

# ---- discovery: walking into a town once unlocks it
rep("if(it!==curT){curT=it;if(it)say('You enter '+it.n+'.','#a60')}",
    "if(it!==curT){curT=it;if(it)say('You enter '+it.n+'.','#a60');if(it&&it!==GTT){const ti=TW.indexOf(it);if(ti>=0&&!(st.vt=st.vt||[]).includes(ti)){st.vt.push(ti);say('New place discovered: '+it.n+'. The Meme Telly can take you here now.','#0a0');questVisit();save()}}}")

# ---- the Grand Tour quest (t:-2 = a visiting quest; progress counts towns visited in order)
rep("""{n:'The Ratio Lord',t:IDX.lord,need:1,desc:"Defeat the Ratio Lord (level 75) in his lair. Check the world map.",xp:['at',2000],c:1000,item:'rsword',qp:5,req:[1,2]}];""",
    """{n:'The Ratio Lord',t:IDX.lord,need:1,desc:"Defeat the Ratio Lord (level 75) in his lair. Check the world map.",xp:['at',2000],c:1000,item:'rsword',qp:5,req:[1,2]},
{n:'The Grand Tour',t:-2,need:8,desc:'Walk to all eight meme towns in order, easiest first: Wow Landing, Pepe\\'s Pond, Stonks City, Diamond Hands, Rugpull Ridge, HODL Heights, Moon Landing, Chad Falls. Each one you reach joins the Meme Telly.',xp:['ag',600],c:500,item:'lamp15',qp:2,req:[0]}];
function townKnown(n){const i=TW.findIndex(t=>t.n==n);return i<0||(st.vt||[]).includes(i)}
function questVisit(){QD.forEach((q,i)=>{if(q.t!=-2||st.qs[i]!=1)return;const b=st.qc[i];while(st.qc[i]<q.need&&(st.vt||[]).includes(st.qc[i]))st.qc[i]++;if(st.qc[i]>=q.need){st.qs[i]=2;say('Quest objective complete: '+q.n+'. Return to Pepe.','#a60')}else if(st.qc[i]!=b)say(q.n+': '+st.qc[i]+'/'+q.need+'. Next: '+TW[st.qc[i]].n+'.','#1a4fb0')})}""")
rep("st.qs[q]=1;st.qc[q]=0;say('Quest started: '+QD[q].n+'. '+QD[q].desc,'#a60')",
    "st.qs[q]=1;st.qc[q]=0;say('Quest started: '+QD[q].n+'. '+QD[q].desc,'#a60');if(QD[q].t==-2)questVisit()")
# old saves: 4 quest slots -> 5
rep("if(st.cs==null)st.cs=0;if(st.scape==null)st.scape=0;",
    "if(st.cs==null)st.cs=0;if(st.scape==null)st.scape=0;while(st.qs.length<5){st.qs.push(0);st.qc.push(0)}if(!st.vt)st.vt=[];")

# ---- the Stock Market
rep("ge:['Exchange','Meme Exchange clerk']", "ge:['Trade','Stock Market broker']")
rep("ge:'She runs the Meme Exchange.'", "ge:'She runs the Stock Market. Wall St. is coming.'")
rep("['ge','Buy something at the Meme Exchange']", "['ge','Buy something at the Stock Market']")
rep("if(st.iron)return say('As an Ironman, you cannot use the Meme Exchange.');", "if(st.iron)return say('As an Ironman, you cannot use the Stock Market.');")
rep("<h2>Meme Exchange</h2>", "<h2>Stock Market</h2>")
rep("Player-to-player offers arrive with the game servers.", "Player-to-player offers arrive with the game servers, when the Stock Market moves to Wall St.")

open(PATH, 'w', encoding='utf-8').write(h)
print('travel patch applied')
