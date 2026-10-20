#!/usr/bin/env python3
"""Partners: players holding at least 3% of $CAPEZ for 14 days get, free for as long as they keep it,
  - a billboard with their picture in every meme town (8 billboards; with more than 8 partners they take turns),
  - an NPC beside each billboard with their name, their line and their link, in a cape of their colour,
  - that cape colour for their own character (Wardrobe).
The server decides who is live (server/server.js, "partners"): an admin approves each ad first, and everything
comes down at the first check below 3% (partners are checked every 15 minutes).
In the game: a "Partners" box at every bank to make or change the ad; admins get a review screen from
/partner view Name. Needs online play; nothing shows offline.
Run from the repo root after patch_holder.py:  python3 tools/patch_partner.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""
// ---- partners (tools/patch_partner.py; the rules live on the server)
const PTN=8,SRVH=()=>SRV().replace(/^ws/,'http').replace(/\/ws\/?$/,'');
const ptList=()=>window.__PTL||[],ptById=id=>ptList().find(p=>p.id==id);
function ptAt(i){const L=ptList(),n=L.length;if(!n)return null;return n<=PTN?L[i%n]:L[(i+PTN*Math.floor(Date.now()/60000))%n]}
function ptGeom(){const v=[],n=[],uv=[],ix=[],W=[.03,.83,.97,.97];
 const face=(P,N,R)=>{const b=v.length/3,e1=[P[1][0]-P[0][0],P[1][1]-P[0][1],P[1][2]-P[0][2]],e2=[P[2][0]-P[0][0],P[2][1]-P[0][1],P[2][2]-P[0][2]],cr=[e1[1]*e2[2]-e1[2]*e2[1],e1[2]*e2[0]-e1[0]*e2[2],e1[0]*e2[1]-e1[1]*e2[0]],fl=cr[0]*N[0]+cr[1]*N[1]+cr[2]*N[2]<0;
  const T=[[R[0],R[1]],[R[2],R[1]],[R[2],R[3]],[R[0],R[3]]];P.forEach((p,k)=>{v.push(...p);n.push(...N);uv.push(...T[k])});ix.push(...(fl?[b,b+2,b+1,b,b+3,b+2]:[b,b+1,b+2,b,b+2,b+3]))};
 const box=(x0,x1,y0,y1,z0,z1,F)=>{face([[x0,y1,z1],[x1,y1,z1],[x1,y0,z1],[x0,y0,z1]],[0,0,1],F||W);face([[x1,y1,z0],[x0,y1,z0],[x0,y0,z0],[x1,y0,z0]],[0,0,-1],W);
  face([[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]],[0,1,0],W);face([[x0,y0,z1],[x1,y0,z1],[x1,y0,z0],[x0,y0,z0]],[0,-1,0],W);
  face([[x1,y1,z1],[x1,y1,z0],[x1,y0,z0],[x1,y0,z1]],[1,0,0],W);face([[x0,y1,z0],[x0,y1,z1],[x0,y0,z1],[x0,y0,z0]],[-1,0,0],W)};
 box(-1.35,1.35,1.0,2.45,-.06,.06,[0,0,1,.8]);box(-1.08,-.94,0,2.55,-.2,-.06);box(.94,1.08,0,2.55,-.2,-.06);box(-1.45,1.45,2.45,2.56,-.14,.14);
 return {v,n,uv,i:ix}}
function ptBoard(p){const key='ptb_'+p.id+'_'+p.v;if(MDL[key])return MDL[key].tex?MDL[key]:null;if(MLOAD[key])return null;MLOAD[key]=1;
 try{regMdl(key,ptGeom())}catch(e){return null}
 const im=new Image();im.crossOrigin='anonymous';im.onload=()=>{const c=document.createElement('canvas');c.width=c.height=512;const x=c.getContext('2d'); // a power-of-two size, so WebGL can mipmap it
  x.fillStyle='#6b4423';x.fillRect(0,0,512,512);x.fillStyle='#c9a24a';x.fillRect(9,9,494,392);
  const A=1.89,ia=im.width/im.height,sw=ia>A?im.height*A:im.width,sh=ia>A?im.height:im.width/A; // the board face is 2.7 by 1.45: crop the picture to that shape
  x.drawImage(im,(im.width-sw)/2,(im.height-sh)/2,sw,sh,14,14,484,382);
  for(let k=0;k<23;k++){x.fillStyle=k%2?'#7a5030':'#6b4423';x.fillRect(0,418+k*4,512,2)}
  const t=gl.createTexture();gl.activeTexture(gl.TEXTURE4);gl.bindTexture(gl.TEXTURE_2D,t);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,c);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.generateMipmap(gl.TEXTURE_2D);gl.activeTexture(gl.TEXTURE0);
  if(MDL[key])MDL[key].tex=t};im.src=SRVH()+'/partners/'+p.id+'.jpg?v='+p.v;return null}
function ptDraw(vis){const S=window.PTS;if(!S||!ptList().length)return;const tn=performance.now()/1000;
 S.forEach((s,i)=>{const p=ptAt(i);if(!p)return;if(s.bb){s.bb.nm=p.brand+' billboard';if(vis(s.bb.x+.5,s.bb.y+.5,45)){const m=ptBoard(p);if(m){YO=hgt(s.bb.x+.5,s.bb.y+.5);qMdl(m,s.bb.x+.5,0,s.bb.y+.5,s.bb.ry,1,null,0);YO=0}}}
  if(s.npc){s.npc.nm=p.brand;if(vis(s.npc.x+.5,s.npc.y+.5,45)){const base=p.g?'playerf':'player';needMdl(base);const cb=capeBody(base,'ptc_'+p.id+'_'+p.v),m=cb||(MDL[base]&&MDL[base].ok?MDL[base]:null);
   if(m){YO=hgt(s.npc.x+.5,s.npc.y+.5);qMdl(m,s.npc.x+.5,0,s.npc.y+.5,s.npc.ry,MDLSC.player,'Idle',tn+i);YO=0}}}})}
function ptTalk(o){const p=ptAt(o.pi);if(!p)return;M.style.display='flex';MB.onclick=null;
 MB.innerHTML='<h2>'+esc(p.brand)+'</h2>'+(p.line?'<p style="font-size:15px">"'+esc(p.line)+'"</p>':'')+'<p style="font-size:12px;color:#ccc">A MemeCapes partner: holds 3% or more of $CAPEZ.</p>'
  +(p.link?'<button id="ptv">Visit '+esc(p.link.replace(/^https:\/\//,'').split('/')[0])+'</button> ':'')+'<button id="x">Close</button><div id="ptw" style="font-size:12px;margin-top:8px"></div>';
 $('x').onclick=()=>M.style.display='none';
 if(p.link)$('ptv').onclick=()=>{$('ptw').innerHTML='This opens <b>'+esc(p.link)+'</b> outside MemeCapes. Partner sites are run by the partner, not by us. Never enter your seed phrase or private key anywhere.<br><button id="ptgo" style="margin-top:6px">Open it</button>';$('ptgo').onclick=()=>{window.open(p.link,'_blank','noopener,noreferrer');M.style.display='none'}}}
function baReview(m){M.style.display='flex';MB.onclick=null;
 MB.innerHTML='<h2>Website ad '+esc(m.name)+': '+esc(m.brand)+'</h2><img src="'+m.img+'" style="width:100%;max-width:380px;border:1px solid #c9a24a"><p style="font-size:13px">For the memecapes.com home page. Status: '+esc(m.status)+'.<br>Line: "'+esc(m.line)+'"<br>Link: '+esc(m.link||'none')+'<br>Wallet: '+esc(m.wallet)+'<br>Nothing is burned yet: after you approve, they burn and paste the burn, and it goes up by itself.</p>'
  +'<button id="pra">Approve</button> <input id="prn" placeholder="Reason if you reject" style="width:50%"> <button id="prr">Reject</button> <button id="x">Close</button>';
 $('x').onclick=()=>M.style.display='none';$('pra').onclick=()=>{netSend({t:'chat',text:'/burnad approve '+m.id});M.style.display='none'};
 $('prr').onclick=()=>{netSend({t:'chat',text:'/burnad reject '+m.id+' '+($('prn').value||'')});M.style.display='none'}}
// the bank box
function partnerHTML(){const P=NETS.partner,H=HPK();if(!SRV()||!NETS.on||!H||!H.on)return '';const need=P?P.need:3,days=P?P.days:14;
 let h='<div id="ptk" style="margin-top:12px;padding-top:10px;border-top:1px dashed #fff4"><b style="color:#ffd23f">Partners</b><br><span style="font-size:12px">Hold '+need+'% or more of all $CAPEZ for '+days+' days: your project gets a billboard and an NPC in every meme town, and a cape in your colour, free for as long as you keep '+need+'%. Under '+need+'% they come down.</span><br>';
 if(!P||!P.over)return h+'</div>';const A=P.ad;
 if(P.live)h+='<span style="color:#7dff9a;font-size:12px">Your ad is live in all 8 towns.</span><br>';
 else if(A&&A.status=='approved')h+='<span style="font-size:12px">Approved. It goes live on '+hpkDate(P.liveAt)+', after '+days+' days at '+need+'%.</span><br>';
 else if(A&&A.status=='pending')h+='<span style="font-size:12px">Your ad is waiting for approval.</span><br>';
 else if(A&&A.status=='rejected')h+='<span style="color:#ff7a59;font-size:12px">Not approved: '+esc(A.note||'')+'</span><br>';
 else h+='<span style="font-size:12px">You hold enough. Make your ad (it goes live after approval and '+days+' days at '+need+'%).</span><br>';
 return h+'<button data-pt="form">'+(A?'Change my ad':'Make my ad')+'</button></div>'}
function partnerWire(){MB.querySelectorAll('[data-pt]').forEach(b=>b.onclick=()=>ptForm())}
function ptForm(){const A=(NETS.partner&&NETS.partner.ad)||{};let img='';M.style.display='flex';MB.onclick=null;
 const inp=(id,ph,v,mx)=>'<input id="'+id+'" maxlength="'+mx+'" placeholder="'+ph+'" value="'+esc(v||'')+'" style="width:100%;box-sizing:border-box;margin:3px 0 8px">';
 MB.innerHTML='<h2>Your partner ad</h2><span style="font-size:12px">Project name</span>'+inp('ptb','e.g. Moon Frogs',A.brand,24)+'<span style="font-size:12px">What your NPC says</span>'+inp('ptl','e.g. gm! Come say hi in our Discord.',A.line,80)
  +'<span style="font-size:12px">Link (https://...)</span>'+inp('ptu','https://',A.link,100)
  +'<span style="font-size:12px">Cape colour</span> <input id="ptc" type="color" value="'+(A.color||'#22aa44')+'"> <span style="font-size:12px;margin-left:10px">NPC</span> <select id="ptg"><option value="0">man</option><option value="1"'+(A.g?' selected':'')+'>woman</option></select><br><br>'
  +'<span style="font-size:12px">Billboard picture (wide works best, it shows at 2 by 1)</span><br><input id="ptf" type="file" accept="image/png,image/jpeg,image/webp"><br><canvas id="ptp" width="512" height="256" style="width:100%;max-width:340px;margin-top:6px;border:1px solid #c9a24a;background:#2a0a10"></canvas>'
  +'<p style="font-size:11px;color:#ccc">Only your own project and art. No scams, adult content, other people\'s brands or promises of profit. Every ad is approved by hand before it shows.</p><div id="ptr" style="font-size:12px;color:#ff7a59"></div><button id="pts">Send for approval</button> <button id="x">Back</button>';
 $('x').onclick=()=>modal('bank');
 $('ptf').onchange=e=>{const f=e.target.files[0];if(!f)return;const u=URL.createObjectURL(f),im=new Image();im.onload=()=>{const c=$('ptp'),x=c.getContext('2d'),r=Math.max(512/im.width,256/im.height),w=im.width*r,hh=im.height*r;x.fillStyle='#2a0a10';x.fillRect(0,0,512,256);x.drawImage(im,(512-w)/2,(256-hh)/2,w,hh);img=c.toDataURL('image/jpeg',.85);URL.revokeObjectURL(u)};im.onerror=()=>{$('ptr').textContent='That picture could not be opened.'};im.src=u};
 $('pts').onclick=()=>{if(!img)return $('ptr').textContent='Add a picture for the billboard.';const lk=$('ptu').value.trim();
  netSend({t:'partnerSave',brand:$('ptb').value.trim(),line:$('ptl').value.trim(),link:lk=='https://'?'':lk,color:$('ptc').value,g:+$('ptg').value,img});$('pts').disabled=true;$('pts').textContent='Sending...';setTimeout(()=>{if(M.style.display!='none'&&$('pts'))modal('bank')},1500)}}
function ptReview(m){if(m.kind=='burn')return baReview(m);M.style.display='flex';MB.onclick=null;
 MB.innerHTML='<h2>Partner ad: '+esc(m.brand)+'</h2><img src="'+m.img+'" style="width:100%;max-width:380px;border:1px solid #c9a24a"><p style="font-size:13px">From <b>'+esc(m.name)+'</b>, holding '+m.pct+'% for '+m.heldDays+' days. Status: '+esc(m.status)+'.<br>NPC says: "'+esc(m.line)+'"<br>Link: '+esc(m.link||'none')+'<br>Cape colour: <span style="display:inline-block;width:14px;height:14px;background:'+esc(m.color)+';vertical-align:middle"></span> '+esc(m.color)+', '+(m.g?'woman':'man')+'</p>'
  +'<button id="pra">Approve</button> <input id="prn" placeholder="Reason if you reject" style="width:50%"> <button id="prr">Reject</button> <button id="x">Close</button>';
 $('x').onclick=()=>M.style.display='none';$('pra').onclick=()=>{netSend({t:'chat',text:'/partner approve '+m.name});M.style.display='none'};
 $('prr').onclick=()=>{netSend({t:'chat',text:'/partner reject '+m.name+' '+($('prn').value||'')});M.style.display='none'}}
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", JS + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", 1)
# the server's messages
rep("holder(m){NETS.holder=m;hpkRefresh()},",
    "holder(m){NETS.holder=m;const k=JSON.stringify([m.on,m.wallet,m.pct,m.member,m.canClaim,m.claimAt,!!m.err]);if(k!==NETS.hk){NETS.hk=k;hpkRefresh()}},partners(m){window.__PTL=m.list||[]},"
    "partner(m){NETS.partner=m;const k=JSON.stringify([m.over,m.eligible,m.live,m.ad&&m.ad.status,m.ad&&m.ad.v]);if(k!==NETS.pk){NETS.pk=k;if(M.style.display!='none'&&$('ptk'))modal('bank')}},partnerReview(m){ptReview(m)},")
# the slots: a billboard and an NPC in each of the 8 meme towns, facing the town centre
WORLD = r"""
{const PTS=window.PTS=[];for(let i=0;i<8&&i<TW.length;i++){const T=TW[i];const b=fN(Math.round(T.cx+5),Math.round(T.cy-5),8);
 const ry=Math.atan2(T.cx-b[0],T.cy-b[1]),bb=xo(b[0],b[1],'pt_bb',{pi:i,pt:1,ry,nm:'Billboard'});
 const q=fN(Math.round(b[0]+Math.cos(ry)*2.2),Math.round(b[1]-Math.sin(ry)*2.2),3),npc=xo(q[0],q[1],'pt_npc',{pi:i,pt:1,ry,nm:'Partner'});
 if(bb){bb.hide=()=>!ptAt(i)}if(npc){npc.hide=()=>!ptAt(i)}PTS.push({bb,npc})}}
"""
rep("xo(...fN(CX-7,CY+6),'saw');", "xo(...fN(CX-7,CY+6),'saw');" + WORLD)
rep("const LBL={", "const LBL={pt_bb:['Look at','Billboard'],pt_npc:['Talk to','Partner'],")
rep("const EXM={", "const EXM={pt_bb:'A partner billboard.',pt_npc:'A MemeCapes partner.',")
rep("const XA={", "const XA={pt_bb:o=>ptTalk(o),pt_npc:o=>ptTalk(o),")
rep("if(!window.__dxo)window.__dxo=", "ptDraw(vis);if(!window.__dxo)window.__dxo=")
# hidden things can't be clicked, and an empty partner slot doesn't block the way
rep("const o=ob[ty]&&ob[ty][tx];if(o&&LBL[o.k])return", "const o=ob[ty]&&ob[ty][tx];if(o&&LBL[o.k]&&!(o.hide&&o.hide()))return")
rep("solid=(x,y)=>x<0||y<0||x>=W||y>=H||tile[y][x]==1||ob[y][x];",
    "solid=(x,y)=>x<0||y<0||x>=W||y>=H||tile[y][x]==1||(!!ob[y][x]&&!(ob[y][x].pt&&!(window.__PTL&&window.__PTL.length)));")
# cape colours: partner NPCs, and the partner's own cape ('ptc' in the Wardrobe)
rep("function capeCol(k){", "function capeCol(k){if(k&&k.startsWith('ptc_')){const p=ptById(+k.split('_')[1]);return p&&/^#[0-9a-f]{6}$/i.test(p.color)?p.color:'#8c0c18'}")
rep("(sk?Promise.resolve('models/skins/'", "(sk&&sk.startsWith('ptc_')?capePaint(d,capeCol(sk)):sk?Promise.resolve('models/skins/'")
rep("function capeSkin(){const id=st.wear&&st.wear.cape;", "function capeSkin(){const id=st.wear&&st.wear.cape;if(id==='ptc'){const me=NETS.partner,p=me&&me.live&&ptById(me.id);return p?'ptc_'+p.id+'_'+p.v:null}")
rep("return depHTML1()+holderHTML()}", "return depHTML1()+holderHTML()+partnerHTML()}")
rep("function depWire(){holderWire();", "function depWire(){holderWire();partnerWire();")
# Wardrobe: wear your partner cape colour
rep("if(HC)h+='<div", "{const me=NETS.partner;if(me&&me.live){const on=W.cape==='ptc';h+='<div class=\"row\"><span><b style=\"color:#ffd23f\">Partner cape</b> <small>(Capes, while you hold 3%)</small></span><button data-pw=\"1\">'+(on?'Take off':'Wear')+'</button></div>'}}if(HC)h+='<div")
rep(" MB.querySelectorAll('[data-hc]').forEach(", " MB.querySelectorAll('[data-pw]').forEach(b=>b.onclick=()=>{st.wear=st.wear||{};st.wear.cape=st.wear.cape==='ptc'?null:'ptc';save();ui();wardrobeUI()});MB.querySelectorAll('[data-hc]').forEach(")

open(PATH, 'w', encoding='utf-8').write(h)
print('partners patch applied')
