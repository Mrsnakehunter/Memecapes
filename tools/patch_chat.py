#!/usr/bin/env python3
"""Chat box + bigger bag.

- The message log keeps the last 150 lines and scrolls (sticks to the newest line unless you scroll up).
- A chat line at the bottom of the box: press Enter (or tap it), type, Enter to send. Your words show in the
  log and as a speech bubble over your character. sendChat() is the hook the multiplayer server will use later.
- The bag holds 35 items (5 across, 7 down) instead of 28.
Run from the repo root:  python3 tools/patch_chat.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# ---- CSS: the box is a column (log on top, chat line at the bottom); the log scrolls
rep("#chat{position:fixed;left:0;bottom:env(safe-area-inset-bottom,0px);width:min(520px,calc(100vw - 210px));height:118px;background:#e8dcc0e6;border:3px solid #4a3d2b;color:#000;padding:4px 6px;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end}",
    "#chat{position:fixed;left:0;bottom:env(safe-area-inset-bottom,0px);width:min(520px,calc(100vw - 210px));height:138px;background:#e8dcc0e6;border:3px solid #4a3d2b;color:#000;padding:4px 6px 3px;overflow:hidden;display:flex;flex-direction:column;box-sizing:border-box}"
    "#clog{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#4a3d2b #0000;padding-right:4px;display:flex;flex-direction:column}#cl{margin-top:auto;flex:none}"
    "#cin{display:flex;align-items:center;gap:4px;border-top:1px solid #4a3d2b66;padding-top:3px;margin-top:3px;flex:none}#cin b{color:#1a4fb0;white-space:nowrap}"
    "#cin input{flex:1;min-width:0;background:#fff6;border:1px solid #4a3d2b44;border-radius:3px;outline:0;font:13px Georgia,serif;color:#000;padding:2px 5px;user-select:text;-webkit-user-select:text}#cin input:focus{background:#fffa;border-color:#4a3d2b}")
rep("@media (max-width:640px){#chat{width:calc(100vw - 6px);bottom:calc(env(safe-area-inset-bottom,0px) + 276px);height:86px}",
    "@media (max-width:640px){#chat{width:calc(100vw - 6px);bottom:calc(env(safe-area-inset-bottom,0px) + 276px);height:104px}")
# ---- HTML
rep('<div id="chat"></div>',
    '<div id="chat"><div id="clog"><div id="cl"></div></div><div id="cin"><b id="cnm">Guest:</b><input id="cti" maxlength="80" placeholder="Press Enter to chat" autocomplete="off" spellcheck="false" enterkeyhint="send"></div></div>')
# ---- the log: keep 150 lines, scroll, stick to the newest line unless the player scrolled up
rep("const chat=[];function say(t,c){chat.push('<div style=\"color:'+(c||'#000')+'\">'+t+'</div>');if(chat.length>7)chat.shift();$('chat').innerHTML=chat.join('')}",
    "const chat=[];function say(t,c){chat.push('<div style=\"color:'+(c||'#000')+'\">'+t+'</div>');if(chat.length>150)chat.shift();const L=$('clog'),atB=L.scrollHeight-L.scrollTop-L.clientHeight<28;$('cl').innerHTML=chat.join('');if(atB)L.scrollTop=L.scrollHeight}\n"
    # chat line
    "const CTI=$('cti'),esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');function chatName(){return st.acct&&st.acct.name?st.acct.name:'Guest'}"
    "function sendChat(t){t=(t||'').replace(/\\s+/g,' ').trim().slice(0,80);if(!t)return;say('<b>'+esc(chatName())+':</b> '+esc(t),'#1a1aa0');pBubble(t);if(window.NET&&NET.chat)NET.chat(t)}"
    "function pBubble(tx){for(let i=bubbles.length-1;i>=0;i--)if(bubbles[i].gb===P){bubbles[i].d.remove();bubbles.splice(i,1)}const d=document.createElement('div');d.textContent=tx;d.style.cssText='position:fixed;font:bold 15px \"Comic Sans MS\",\"Comic Neue\",cursive;pointer-events:none;transform:translate(-50%,-100%);z-index:4;text-shadow:1px 1px 2px #000,-1px -1px 2px #000;color:#ffe14d;max-width:260px;text-align:center';document.body.appendChild(d);bubbles.push({gb:P,d,h:2.75,t:performance.now()+2500+40*tx.length})}"
    "CTI.addEventListener('keydown',e=>{e.stopPropagation();if(e.key=='Enter'){sendChat(CTI.value);CTI.value='';CTI.blur()}else if(e.key=='Escape'){CTI.value='';CTI.blur()}});"
    "CTI.addEventListener('focus',()=>{$('cnm').textContent=chatName()+':'});"
    "addEventListener('keydown',e=>{if(e.key=='Enter'&&started&&document.activeElement!==CTI&&!(e.target&&e.target.closest&&e.target.closest('input,textarea,select'))){e.preventDefault();CTI.focus()}});")
# the bubble over the player sits above the name tag
rep("const p=[g.px+.5-E[0],1.75+hgt(g.px+.5,g.py+.5)-E[1],g.py+.5-E[2]],zz=d3(p,Fw);if(zz<=0){b.d.style.display='none';continue}",
    "const p=[g.px+.5-E[0],(b.h||1.75)+hgt(g.px+.5,g.py+.5)-E[1],g.py+.5-E[2]],zz=d3(p,Fw);if(zz<=0){b.d.style.display='none';continue}")
# ---- the bag: 35 slots, 5 across
rep("cap=()=>28-(st.coins>0?1:0)-st.inv.length;", "cap=()=>35-(st.coins>0?1:0)-st.inv.length;")
rep("const it=(st.coins>0?['coin']:[]).concat(st.inv);for(let i=0;i<28;i++){", "const it=(st.coins>0?['coin']:[]).concat(st.inv);for(let i=0;i<35;i++){")
rep(".g{display:grid;grid-template-columns:repeat(4,1fr);gap:2px}", ".g{display:grid;grid-template-columns:repeat(5,1fr);gap:2px}")
# the side panel grows 20px on desktop so all 7 rows show without scrolling (phones keep 270px: 7 across, 5 down)
rep("padding:6px 6px 34px;height:270px}", "padding:6px 6px 34px;height:290px}")
rep("#pc{max-height:226px;overflow-y:auto}", "#pc{max-height:246px;overflow-y:auto}")

open(PATH, 'w', encoding='utf-8').write(h)
print('chat + bag patch applied')
