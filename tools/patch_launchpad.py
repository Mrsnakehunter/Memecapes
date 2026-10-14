#!/usr/bin/env python3
"""Launchpad in the game: a Launchpad clerk in Gigachad Town (beside the Stock Market broker) and one in Stonks City.
Talking to her shows the newest coins launched on memecapes.com (from the game server's /lp/coins list), with their
pictures, and buttons to look at a coin or launch your own. Buying, selling and launching happen on launch.html in a
new tab, in the player's own wallet: the game itself never touches a wallet.
Run from the repo root after patch_wanderers.py:  python3 tools/patch_launchpad.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""
// ---- Launchpad clerk (tools/patch_launchpad.py): the newest coins launched on memecapes.com
let LPL=null,LPT=0;
function lpUI(){M.style.display='flex';MB.onclick=null;MB.className='';
 const row=c=>'<div style="display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #fff2"><img src="'+esc(c.image||'')+'" alt="" style="width:46px;height:46px;border-radius:50%;object-fit:cover;border:3px solid #d9a520;background:#3a2a16" referrerpolicy="no-referrer">'
  +'<div style="flex:1;min-width:0"><b>'+esc(c.name)+'</b> <small>$'+esc(c.symbol)+'</small>'+(c.verified?' <small style="color:#7dff9a">Verified</small>':'')+'</div><button data-lpc="'+esc(c.mint)+'">View</button></div>';
 const draw=()=>{MB.innerHTML='<h2>Launchpad</h2><p style="font-size:13px">Coins launched by players on memecapes.com. They are made by the people who launch them, not by MemeCapes: check who is behind a coin before you buy, and only put in what you are happy to lose.</p>'
  +(LPL==null?'<p>Loading...</p>':LPL.length?LPL.slice(0,12).map(row).join(''):'<p>No coins launched yet. Be the first.</p>')
  +'<div style="margin-top:10px"><button id="lpl">Launch a coin</button> <button id="lpa">See all coins</button> <button id="x">Close</button></div>';
  $('x').onclick=()=>M.style.display='none';
  $('lpl').onclick=()=>window.open('launch.html#/launch','_blank','noopener');$('lpa').onclick=()=>window.open('launch.html#/','_blank','noopener');
  MB.querySelectorAll('[data-lpc]').forEach(b=>b.onclick=()=>window.open('launch.html#/coin/'+encodeURIComponent(b.dataset.lpc),'_blank','noopener'))};
 draw();
 if(!SRV()){LPL=[];return draw()}
 if(LPL&&Date.now()-LPT<60000)return;
 fetch(SRVH()+'/lp/coins?limit=12&net=mainnet').then(r=>r.json()).then(j=>{LPL=(j&&j.coins)||[];LPT=Date.now();if(M.style.display!='none'&&$('lpl'))draw()}).catch(()=>{LPL=[];if(M.style.display!='none'&&$('lpl'))draw()})}
"""
rep("function ptTalk(o){", JS + "function ptTalk(o){")
# two clerks: beside the Stock Market broker in Gigachad Town, and in Stonks City
rep("xo(...fN(CX-6,CY-4),'ge');", "xo(...fN(CX-6,CY-4),'ge');xo(...fN(CX-9,CY-4),'lpad',{ry:1.57});{const sc=TW.find(t=>t.n==\"Stonks City\");if(sc)xo(...fN(sc.cx+4,sc.cy-3),'lpad')}")
rep("ge:['Trade','Stock Market broker'],", "ge:['Trade','Stock Market broker'],lpad:['Talk to','Launchpad clerk'],")
rep("ge:'She runs the Stock Market. Wall St. is coming.',", "ge:'She runs the Stock Market. Wall St. is coming.',lpad:'She lists the new coins launched on memecapes.com.',")
rep("ge:()=>geOpen(),", "ge:()=>geOpen(),lpad:()=>lpUI(),")
rep("DYNPP={capes:'richw',ge:'banker',saw:'cobbler'}", "DYNPP={capes:'richw',ge:'banker',saw:'cobbler',lpad:'richw'}")

open(PATH, 'w', encoding='utf-8').write(h)
print('launchpad patch applied')
