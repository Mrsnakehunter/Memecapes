#!/usr/bin/env python3
"""Real players and bots look and behave the same to everyone (the website says the game has bots).
- Real players now show other players what they are doing and holding: the animation (idle, chopping, fishing,
  mining, fighting, emotes), the weapon or tool in hand, a shield, and their cape skin. Before, other players saw
  a bare-handed figure in its bind pose whenever it stood still.
- Bots answer the name menu like a player who doesn't reply: "Trade request sent" and then nothing.
Run from the repo root after patch_online.py:  python3 tools/patch_lookalike.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# 1. send what I'm doing: a = clip|weapon|shield (keys without the w_), c = cape:skin
rep("netSelf(P.px,P.py,pry,mvg?(pspd>2.4?2:1):0);",
    "netSelf(P.px,P.py,pry,mvg?(pspd>2.4?2:1):0,PC&&!mvg?PC.n:'',heldKey()||'',shieldKey()||'');")
rep("function netSelf(x,y,r,mv){if(!NETS.on||!started)return;const lv=(()=>{try{return combatLvl()}catch(e){return 3}})(),k=[x.toFixed(2),y.toFixed(2),r.toFixed(2),mv,st.ap&&st.ap.g?1:0,(st.eq&&st.eq.cape)||'',lv].join(',');",
    "function netSelf(x,y,r,mv,cl,wk,sk){if(!NETS.on||!started)return;const lv=(()=>{try{return combatLvl()}catch(e){return 3}})(),cs=(()=>{try{return capeSkin()||''}catch(e){return ''}})(),cc=((st.eq&&st.eq.cape)||'')+(cs&&st.eq&&st.eq.cape?':'+cs:''),a=[cl||'',String(wk||'').replace(/^w_/,''),String(sk||'').replace(/^w_/,'')].join('|'),k=[x.toFixed(2),y.toFixed(2),r.toFixed(2),mv,st.ap&&st.ap.g?1:0,cc,lv,a].join(',');")
rep("netSend({t:'pos',x,y,r,m:mv,g:st.ap&&st.ap.g?1:0,c:(st.eq&&st.eq.cape)||'',lv})}",
    "netSend({t:'pos',x,y,r,m:mv,g:st.ap&&st.ap.g?1:0,c:cc,lv,a})}")
# 2. read it
rep("for(const q of m.p){const[id,x,y,r,mv]=q;", "for(const q of m.p){const[id,x,y,r,mv,a]=q;")
rep("o.tx=x;o.ty=y;o.tr=r;o.mv=mv;o.seen=performance.now()}", "o.tx=x;o.ty=y;o.tr=r;o.mv=mv;o.a=a||'';o.seen=performance.now()}")
# 3. draw it, the same way bots and the local player are drawn
rep("""  const K=inf.g?'playerf':'player';needMdl(K);const CBo=inf.c?capeBody(K,inf.c):null,PMo=CBo||((MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player);if(!PMo||!PMo.ok)continue;
  const mv=o.mv||(dd>.05?1:0);qMdl(PMo,o.px+.5,0,o.py+.5,o.r,MDLSC.player,mv?(mv==2?'Running':'Walking'):null,now/1000+o.id,0,null,false,1);
  if(inf.c&&!CBo)qCape(o.px+.5,o.py+.5,o.r,inf.c)}""",
"""  const K=inf.g?'playerf':'player';needMdl(K);const cp=String(inf.c||'').split(':'),ck=cp[0],csk=cp[1]&&/^cs_[a-z0-9_]+$/.test(cp[1])?cp[1]:null,CBo=ck?capeBody(K,ck,csk):null,PMo=CBo||((MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player);if(!PMo||!PMo.ok)continue;
  const mv=o.mv||(dd>.05?1:0),A=String(o.a||'').split('|'),t0=now/1000+o.id;let cl=mv?(mv==2?'Running':'Walking'):(A[0]&&PMo.clips[A[0]]?A[0]:PMo.clips.Idle?'Idle':null);
  const x=o.px+.5,z=o.py+.5;qMdl(PMo,x,0,z,o.r,MDLSC.player,cl,t0,0,null,false,1);
  if(ck&&!CBo)qCape(x,z,o.r,ck);
  {const wk=A[1]&&/^[a-z0-9_]+$/.test(A[1])?'w_'+A[1]:null,sk=A[2]&&/^[a-z0-9_]+$/.test(A[2])?'w_'+A[2]:null;if(wk&&WAV.has(wk))qHold(PMo,x,z,o.r,cl,t0,wk,false,null,heldTilt(cl,t0,wk));if(sk&&WAV.has(sk))qHold(PMo,x,z,o.r,cl,t0,sk,true)}}""")
# 4. a trade request to a bot: sent, and (like a busy player) never answered
rep("if(c=='trade'&&nm){netSaveNow();netSend({t:'tradeReq',name:nm});return true}",
    "if(c=='trade'&&nm){if(typeof WND!=='undefined'&&WND.some(o=>o.dn&&o.dn.toLowerCase()===nm.toLowerCase())){say('Trade request sent to '+esc(WND.find(o=>o.dn.toLowerCase()===nm.toLowerCase()).dn)+'.','#0a0');return true}netSaveNow();netSend({t:'tradeReq',name:nm});return true}")

open(PATH, 'w', encoding='utf-8').write(h)
print("lookalike patch applied")
