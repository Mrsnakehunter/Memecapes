#!/usr/bin/env python3
"""SnakePit in the game (section 7 of the SnakePit brief): the player's snake from the Pit slithers behind them in
the world, the $CAPES tab shows that snake and a "Trade $CAPES in the Pit" button.

* MC_CONFIG.pit = "https://pit.memecapes.com" switches it on ("" = nothing shows). The game asks its own server
  (GET /pit/snake?wallet=...), never the Pit directly; the server caches a minute per wallet (server/snakepit.js).
* The snake needs a linked wallet (the same wallet is the key on both sides). It follows the player's trail: a mint
  head plus one body segment per Pit segment (drawn up to 30, thicker beyond that), rank and segments in the tab.
* "Trade $CAPES" opens pit/?q=<capesMint> when the mint is set, otherwise the Pit's $CAPES hub. New tab, noopener.
Run late in the build (after patch_pace):  python3 tools/patch_snakepit.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- state, fetch, draw
JS = r"""
// ---- SnakePit: the player's snake from pit.memecapes.com, mirrored in the world (MC_CONFIG.pit switches it on)
const PITC=()=>String((window.MC_CONFIG||{}).pit||'').replace(/\/+$/,'');
const PITS={w:'',d:null,t:0,busy:0,tr:[],last:null,wig:0};
function pitWallet(){const w=st.acct&&st.acct.wallet?String(st.acct.wallet).replace(/[^1-9A-HJ-NP-Za-km-z]/g,''):'';return w.length>=32&&w.length<=44?w:''}
function pitTradeUrl(){const C=window.MC_CONFIG||{};return PITC()?(C.capesMint?PITC()+'/?q='+encodeURIComponent(C.capesMint):PITC()+'/capes'):''}
function pitRefresh(force){const w=pitWallet();if(!PITC()||!w){PITS.d=null;PITS.w='';return}
 if(PITS.busy||(!force&&PITS.w==w&&performance.now()-PITS.t<300000))return;PITS.busy=1;
 fetch(SRVH()+'/pit/snake?wallet='+encodeURIComponent(w)).then(r=>r.json()).then(j=>{PITS.busy=0;PITS.t=performance.now();PITS.w=w;if(j&&j.on&&j.snake){const had=PITS.d&&PITS.d.snake.segments;PITS.d=j;if(had!=null&&j.snake.segments>had)say('Your snake grew to '+j.snake.segments+' segments.','#58f0a6');if(tab=='pot')renderPanel()}else if(j&&!j.on){PITS.d=null}})
 .catch(()=>{PITS.busy=0;PITS.t=performance.now()-240000})}
function pitSnakeHTML(){const C=window.MC_CONFIG||{};if(!PITC())return'';const w=pitWallet(),d=PITS.d,u=pitTradeUrl();
 let s='<div style="background:#0b0c0e;border:1px solid #1e2a24;border-radius:6px;padding:7px 8px;margin:8px 0;color:#f4f6f5"><div style="display:flex;align-items:center;gap:6px"><svg width="18" height="18" viewBox="0 0 100 100"><path d="M20 22 C 22 30, 30 30, 40 30 L 72 30 L 26 76 L 68 76" fill="none" stroke="#58f0a6" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/><ellipse cx="76" cy="76" rx="12" ry="8" fill="#58f0a6"/></svg><b style="color:#58f0a6">Your snake</b><span style="margin-left:auto;font-size:9px;color:#7c8590;letter-spacing:.08em">SNAKEPIT</span></div>';
 if(!w)s+='<div style="color:#7c8590;margin-top:4px">Link your wallet at any bank and your snake from the Pit follows you here. Same wallet, same snake.</div>';
 else if(!d)s+='<div style="color:#7c8590;margin-top:4px">'+(PITS.busy?'Looking for your snake…':'No snake yet. Strike something in the Pit and it hatches.')+'</div>';
 else{const k=d.snake;s+='<div style="margin-top:4px;font-family:ui-monospace,monospace"><b style="font-size:15px">'+k.segments+'</b> segment'+(k.segments==1?'':'s')+(d.rank?' · Pit rank <b>#'+d.rank+'</b>':'')+'<br><span style="color:'+(k.realized_pnl_sol>=0?'#58f0a6':'#ff6b7a')+'">'+(k.realized_pnl_sol>=0?'+':'')+k.realized_pnl_sol+' SOL</span> realized · '+k.wins+'W '+k.losses+'L'+(k.streak?' · '+(k.streak>0?'+':'')+k.streak+' streak':'')+(k.segments<=1?'<br><span style="color:#ff6b7a">Ate its own tail.</span>':'')+'</div>'
  +'<a href="'+esc(d.url)+'" target="_blank" rel="noopener" style="color:#58f0a6;font-size:10px">See your snake in the Pit →</a>'}
 s+='</div>';
 if(u)s+='<a href="'+esc(u)+'" target="_blank" rel="noopener" style="display:block;text-align:center;margin:6px 0;padding:8px;border-radius:6px;background:#58f0a6;color:#0b0c0e;font-weight:800;text-decoration:none">Trade $CAPES in the Pit</a><div style="color:#7c8590;font-size:10px;margin:0 0 4px">SnakePit is the trading app next to the game: self-custodial, your wallet, your keys. Crypto can go to zero; nothing here is financial advice.</div>';
 return s}
// the snake: a trail of the player's recent positions, the head about a tile behind, a body segment every third of a tile
function pitSnakeDraw(dt,now){if(!PITS.d||!PITS.d.snake)return;const seg=PITS.d.snake.segments,T=PITS.tr,px=P.px+.5,pz=P.py+.5,L=PITS.last;
 if(L&&Math.hypot(px-L[0],pz-L[1])>6){T.length=0;PITS.last=null}
 if(!PITS.last||Math.hypot(px-PITS.last[0],pz-PITS.last[1])>=.2){T.unshift([px,pz]);PITS.last=[px,pz];if(T.length>200)T.length=200}
 if(T.length<2)return;
 const n=Math.min(30,seg),th=.14+.05*Math.min(1,Math.log10(Math.max(1,seg))/2.1),step=.23;   // past 30 segments the snake gets thicker instead of longer
 const mv=Math.hypot(px-(PITS.pp||[px,pz])[0],pz-(PITS.pp||[px,pz])[1])>.01;PITS.pp=[px,pz];PITS.wig+=dt*(mv?9:2.2);
 PITS.lead=PITS.lead==null?.9:PITS.lead+((mv?.9:.45)-PITS.lead)*Math.min(1,dt*1.5);   // the head closes in when the player stops
 const at=(d)=>{let acc=0;for(let i=0;i+1<T.length;i++){const a=T[i],b=T[i+1],l=Math.hypot(b[0]-a[0],b[1]-a[1]);if(acc+l>=d){const k=l?(d-acc)/l:0;return[a[0]+(b[0]-a[0])*k,a[1]+(b[1]-a[1])*k,Math.atan2(a[0]-b[0],a[1]-b[1])]}acc+=l}
  const a=T[T.length-2],b=T[T.length-1],l=Math.hypot(b[0]-a[0],b[1]-a[1])||1,e=d-acc;return[b[0]+(b[0]-a[0])/l*e,b[1]+(b[1]-a[1])/l*e,Math.atan2(a[0]-b[0],a[1]-b[1])]};   // beyond the trail: straight on, so a fresh snake lies behind the player
 const y0=YO,m0=MAT;YO=0;MAT=0;
 for(let i=n;i>=0;i--){const p=at(PITS.lead+i*step),w=Math.sin(PITS.wig-i*.7)*.07*(mv?1:.4),cs=Math.cos(p[2]),sn=Math.sin(p[2]),x=p[0]+cs*w,z=p[1]-sn*w,y=hgt(x,z);
  if(i===0){ball(x,y+th*1.1,z,th*1.35,th*1.0,th*1.7,p[2],'#58f0a6',10);const ex=x+sn*th*1.2,ez=z+cs*th*1.2;ball(ex+cs*th*.6,y+th*1.75,ez-sn*th*.6,.04,.04,.04,0,'#0b0c0e',4);ball(ex-cs*th*.6,y+th*1.75,ez+sn*th*.6,.04,.04,.04,0,'#0b0c0e',4);if(mv&&Math.sin(now/180)>.6)ball(x+sn*th*2.3,y+th*.8,z+cs*th*2.3,.025,.012,.11,p[2],'#ff3b4e',4)}
  else{const k=1-i/(n+1)*.5,c=i%2?'#46d892':'#58f0a6';ball(x,y+th*k,z,th*k,th*k*.9,th*k*1.1,p[2],c,8)}}
 YO=y0;MAT=m0}
"""
rep("const angD=(a,b)=>{const d=b-a;return isFinite(d)?((d+Math.PI)%6.283185307+6.283185307)%6.283185307-Math.PI:0};",
    "const angD=(a,b)=>{const d=b-a;return isFinite(d)?((d+Math.PI)%6.283185307+6.283185307)%6.283185307-Math.PI:0};" + JS)

# draw it where the pets are drawn
rep("if(st.pet){const fp=follow(PT,dt,1.667);", "pitSnakeDraw(dt,now);if(st.pet){const fp=follow(PT,dt,1.667);")

# the $CAPES tab: the snake card + the trade button, under the exchange lines
rep("""<br><span style="color:#ccc">Exchange at any bank.</span><br><button disabled style="opacity:.55;margin:6px 0">Withdraw to wallet (soon)</button>""",
    """<br><span style="color:#ccc">Exchange at any bank.</span><br><button disabled style="opacity:.55;margin:6px 0">Withdraw to wallet (soon)</button>'+pitSnakeHTML()+'""")

# ask for the snake: at start (after the saved game loads), when the $CAPES tab opens, and every 5 minutes
rep("function renderPanel(){if(!pOpen)return;let h='';", "function renderPanel(){if(!pOpen)return;let h='';if(tab=='pot')pitRefresh();")
rep("setInterval(tick,600);", "setInterval(tick,600);setInterval(()=>pitRefresh(),60000);setTimeout(()=>pitRefresh(),4000);")

open(PATH, 'w', encoding='utf-8').write(h)
print('SnakePit patch applied.')
