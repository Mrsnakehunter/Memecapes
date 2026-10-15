#!/usr/bin/env python3
"""Make online play the obvious way in, and never let anyone be offline without knowing it.
- Start screen: "Play Online" (create account / log in) comes first; the browser-only buttons (Continue, Create
  Account, Guest, Random Character) fold away under "Play offline instead (nobody else can see you)".
- In the game: a small chip says "Online · N players" or, when offline, "Offline: other players can't see you"
  with a button back to the online log-in. While reconnecting it says so.
Run from the repo root after patch_launchpad.py:  python3 tools/patch_online.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# 1. start screen: online first, offline folded away
rep("""box.innerHTML=(tk&&nm?'<button class="big" id="noc">Continue online as '+esc(nm)+'</button>':'')+'<button class="big" id="nol">Play Online: Log in</button><button class="big" id="nor">Play Online: Create Account</button><div style="font-size:11px;color:#ccc;margin:2px 0 8px">Online: your progress is saved on the server and you can play, chat and trade with other players. The buttons below play offline in this browser.</div>';
 const ref=SBX.querySelector('.big');SBX.insertBefore(box,ref);""",
"""box.innerHTML=(tk&&nm?'<button class="big" id="noc">Continue online as '+esc(nm)+'</button>':'')+'<button class="big" id="nor" style="background:linear-gradient(180deg,#ffd877,#e3ac35);color:#2b1d05">Play Online: Create Account</button><button class="big" id="nol">Play Online: Log in</button><div style="font-size:11px;color:#ccc;margin:2px 0 8px">Online, you see and chat with everyone else playing, trade, and your progress is saved on the server.'+(LS.get('ms4')&&!tk?' Already played here? Create an account and tick "bring my progress".':'')+'</div>';
 const ref=SBX.querySelector('.big');SBX.insertBefore(box,ref);
 {const off=document.createElement('details');off.className='onoff';off.style.cssText='margin:6px 0;text-align:left';off.innerHTML='<summary style="cursor:pointer;font-size:12px;color:#ccc;padding:6px 0">Play offline instead (nobody else can see you)</summary>';
  ['bc','bn','bg','br'].forEach(id=>{const b=$(id);if(b)off.appendChild(b)});
  [...SBX.querySelectorAll('button[disabled]')].forEach(b=>b.remove());[...SBX.querySelectorAll('div')].forEach(d=>{if(/your account lives only in this browser/.test(d.textContent)&&!d.querySelector('button'))d.remove()});
  box.after(off)}""")

# 2. in the game: online / offline chip
JS = r"""
// ---- online status chip (tools/patch_online.py)
setInterval(()=>{if(!SRV()||!started)return;let d=document.getElementById('onchip');
 if(!d){d=document.createElement('div');d.id='onchip';d.style.cssText='position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:30;font:700 12px system-ui,sans-serif;border-radius:999px;padding:5px 12px;pointer-events:auto;box-shadow:0 2px 10px #0006';document.body.appendChild(d)}
 const st2=NETS.on?'on':LS.get('mc_tok')&&NETS.ws&&NETS.ws.readyState<2?'re':'off';if(d.dataset.s===st2+(NETS.n||0))return;d.dataset.s=st2+(NETS.n||0);
 if(st2=='on'){d.style.background='#0f2219';d.style.color='#7dffb2';d.style.border='1px solid #1f5a40';d.innerHTML='&#9679; Online'+(NETS.n?' &middot; '+NETS.n+' player'+(NETS.n==1?'':'s'):'');setTimeout(()=>{if(NETS.on&&d)d.style.opacity='.55'},6000)}
 else if(st2=='re'){d.style.opacity='1';d.style.background='#2a2209';d.style.color='#ffd23f';d.style.border='1px solid #6b5a14';d.textContent='Reconnecting to the server...'}
 else{d.style.opacity='1';d.style.background='#2a1209';d.style.color='#ffb59a';d.style.border='1px solid #6b2a14';d.innerHTML='Offline: other players can\'t see you. <a href="#" id="ongo" style="color:#ffd23f;margin-left:6px">Play online</a>';
  document.getElementById('ongo').onclick=e=>{e.preventDefault();try{netSaveNow()}catch(x){}location.reload()}}},2000);
"""
rep("// a new version of the game is out: say so (checked every 5 minutes)", JS + "// a new version of the game is out: say so (checked every 5 minutes)")

open(PATH, 'w', encoding='utf-8').write(h)
print("online patch applied")
