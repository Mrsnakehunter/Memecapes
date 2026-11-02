#!/usr/bin/env python3
"""Spell and arrow effects that look next level (Albert, Nov 1: "the mage attacks really need to be next level").

A light 2D effects layer over the 3D view: glowing additive particles projected from world space every frame, so they
sit on the battlefield and follow the camera. Every spell has its own look:
  Spark          crackling yellow lightning ball, electric arcs on impact
  Pump           green orb throwing up little green candles, a candle burst on impact
  FOMO Blast     roaring orange fireball with smoke, fiery explosion
  Rug Pull       purple vortex that swirls in, then yanks the rug: a spinning ring under the target
  Moon Beam      a silver beam of light straight down from the sky onto the target
  Diamond Storm  a fan of spinning crystal diamonds, glittering shatter
  Whale Wave     a teal wave rolling at the target with spray, splash ring
  Moonfire       pink-white flames round a crescent, burning flare
  Legend Nova    crimson-gold star, huge shockwave, rays and a screen flash
Every cast starts with a charge-up in the caster's hands; arrows leave a bright streak and a spark on hit.
Nov 2 (Albert): spell effects drawn at 3/4 size (drawP), arrows at half the earlier size.
Pure canvas 2D (no new shaders), capped at 700 particles so phones keep up.
Run after patch_classes.py:  python3 tools/patch_vfx.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


JS = r"""
// ---- spell + arrow effects (tools/patch_vfx.py): additive particles projected from the 3D world
const FX=(()=>{let cv=null,c=null,last=0;const T=()=>performance.now()*(window.__fxs||1);const PS=[],EM=[];const R=Math.random,TAU=Math.PI*2;
 const prj=(x,y,z)=>{const p=[x-E[0],y-E[1],z-E[2]],zz=d3(p,Fw);if(zz<=.2)return null;return [(d3(p,Rt)/(zz*TH*asp)+1)/2*CW,(1-d3(p,Up)/(zz*TH))/2*CH,CH/(zz*TH*2)]};
 function init(){if(cv)return;cv=document.createElement('canvas');cv.id='fxc';cv.style.cssText='position:fixed;left:0;top:0;pointer-events:none;z-index:2';document.body.appendChild(cv);c=cv.getContext('2d');requestAnimationFrame(loop)}
 const add=p=>{if(PS.length<700)PS.push(Object.assign({t0:T(),life:500,s:.1,vx:0,vy:0,vz:0,g:0,dr:1,a:1,k:'g',rot:R()*TAU,vr:0},p))};
 function glow(x,y,r,col,a){if(r<.6)return;const g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,'rgba(255,255,255,'+a+')');g.addColorStop(.25,col.replace('A',a*.9));g.addColorStop(1,col.replace('A',0));c.fillStyle=g;c.fillRect(x-r,y-r,r*2,r*2)}
 const rgba=h=>{const n=parseInt(h.slice(1),16);return 'rgba('+(n>>16&255)+','+(n>>8&255)+','+(n&255)+',A)'};
 function loop(){requestAnimationFrame(loop);const now=T();if(!c)return;const W=CW||innerWidth,H=CH||innerHeight;if(cv.width!=W||cv.height!=H){cv.width=W;cv.height=H}
  const dt=Math.min(.05,(now-(last||now))/1000);last=now;c.clearRect(0,0,W,H);if(!PS.length&&!EM.length)return;c.globalCompositeOperation='lighter';
  for(let i=EM.length-1;i>=0;i--){const e=EM[i],f=(now-e.t0)/e.dur;if(f>=1){EM.splice(i,1);e.end&&e.end();continue}if(f>=0)e.tick(f,now,dt)}
  for(let i=PS.length-1;i>=0;i--){const p=PS[i],f=(now-p.t0)/p.life;if(f>=1){PS.splice(i,1);continue}if(f<0)continue;
   p.vy-=p.g*dt;p.vx*=p.dr;p.vy*=p.dr;p.vz*=p.dr;p.x+=p.vx*dt;p.y+=p.vy*dt;p.z+=p.vz*dt;p.rot+=p.vr*dt;
   drawP(p,p.a*(f<.15?f/.15:1-(f-.15)/.85),f)}
  c.globalCompositeOperation='source-over'}
 function drawP(p,a,f){const q=prj(p.x,p.y,p.z);if(!q)return;const r=(p.s||.1)*q[2]*(p.grow?1+f*p.grow:1)*(p.sc==null?.75:p.sc);p.c=p.c||'#fff';p.k=p.k||'g';
   if(p.k=='g')glow(q[0],q[1],r*2.2,p.c,a);
   else if(p.k=='d'){c.save();c.translate(q[0],q[1]);c.rotate(p.rot);c.globalAlpha=a;c.fillStyle=p.c;c.beginPath();c.moveTo(0,-r);c.lineTo(r*.6,0);c.lineTo(0,r);c.lineTo(-r*.6,0);c.closePath();c.fill();c.globalAlpha=a*.8;c.fillStyle='#fff';c.beginPath();c.moveTo(0,-r*.7);c.lineTo(r*.25,-r*.1);c.lineTo(0,r*.2);c.lineTo(-r*.2,-r*.1);c.fill();c.restore()}
   else if(p.k=='c'){c.globalAlpha=a;c.fillStyle=p.c;c.fillRect(q[0]-r*.25,q[1]-r,r*.5,r*2);c.fillRect(q[0]-r*.06,q[1]-r*1.6,r*.12,r*3.2);c.globalAlpha=1}
   else if(p.k=='ring'){c.globalAlpha=a;c.strokeStyle=p.c;c.lineWidth=Math.max(1,r*.12);c.beginPath();c.ellipse(q[0],q[1],r,r*.38,0,0,TAU);c.stroke();c.globalAlpha=1}
   else if(p.k=='moon'){c.globalAlpha=a;c.fillStyle=p.c;c.beginPath();c.arc(q[0],q[1],r,0,TAU);c.fill();c.globalCompositeOperation='destination-out';c.beginPath();c.arc(q[0]+r*.45,q[1]-r*.2,r*.85,0,TAU);c.fill();c.globalCompositeOperation='lighter';c.globalAlpha=1}}
 const core=(p)=>drawP(p,p.a==null?1:p.a,0);
 const sp=(dt,r)=>Math.floor(r*dt+R());
 function bolt(q1,q2,col,w){c.strokeStyle=col;c.lineWidth=w;c.beginPath();c.moveTo(q1[0],q1[1]);const n=6;for(let i=1;i<n;i++){const t=i/n;c.lineTo(q1[0]+(q2[0]-q1[0])*t+(R()-.5)*18,q1[1]+(q2[1]-q1[1])*t+(R()-.5)*18)}c.lineTo(q2[0],q2[1]);c.stroke()}
 function flash(col,a){const d=document.createElement('div');d.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:3;background:radial-gradient(circle at 50% 45%,'+col+' 0%,transparent 70%);opacity:'+a+';transition:opacity .5s ease-out';document.body.appendChild(d);requestAnimationFrame(()=>requestAnimationFrame(()=>{d.style.opacity=0}));setTimeout(()=>d.remove(),600)}
 const burst=(x,y,z,n,o)=>{n=Math.round(n*1.6);for(let i=0;i<n;i++){const th=R()*TAU,ph=R()*Math.PI-.3,sp=(o.sp||3)*(.4+R()*.8);add(Object.assign({x,y,z,vx:Math.cos(th)*Math.cos(ph)*sp,vy:Math.sin(ph)*sp*(o.up||1),vz:Math.sin(th)*Math.cos(ph)*sp,life:(o.life||600)*(.6+R()*.6),s:(o.s||.12)*(.6+R()*.8),c:o.c,g:o.g||0,dr:o.dr||.92},o.x2||{}))}};
 // spell looks: c1 core colour, c2 trail colour, size, trail kind, impact
 const LOOK=[{c1:'#fff27a',c2:'#ffd23f',s:.4,tr:'spark',hit:'zap'},{c1:'#9dffc8',c2:'#3ee08a',s:.42,tr:'candle',hit:'candles'},
  {c1:'#ffd08a',c2:'#ff6a1a',s:.6,tr:'fire',hit:'boom'},{c1:'#e6b3ff',c2:'#9a3cff',s:.48,tr:'vortex',hit:'rug'},
  {c1:'#ffffff',c2:'#cfe0ff',s:.3,tr:'beam',hit:'moonhit'},{c1:'#e8fbff',c2:'#7fd6ff',s:.45,tr:'shards',hit:'shatter'},
  {c1:'#bff8ff',c2:'#1fb6c8',s:.55,tr:'wave',hit:'splash'},{c1:'#fff0fb',c2:'#ff7ad9',s:.52,tr:'moonfire',hit:'flare'},
  {c1:'#fff2c0',c2:'#ff2a4a',s:.75,tr:'nova',hit:'nova'}];
 function impact(L,x,y,z,q){const c1=rgba(L.c1),c2=rgba(L.c2);add({x,y,z,s:L.s*3,life:320,c:c1});add({x,y,z,s:L.s*5,life:500,c:c2,a:.5});add({x,y:hgt(x,z)+.05,z,s:.5,life:700,c:L.c2,k:'ring',grow:2.2});
  if(L.hit=='zap'){burst(x,y,z,26,{c:c1,sp:4,s:.07,life:380});EM.push({t0:T(),dur:300,tick:()=>{const a=prj(x,y,z);if(!a)return;for(let k=0;k<3;k++){const th=R()*TAU;bolt(a,[a[0]+Math.cos(th)*a[2]*1.2,a[1]+Math.sin(th)*a[2]*.9],'rgba(255,250,180,.9)',2)}}})}
  if(L.hit=='candles'){for(let i=0;i<14;i++)add({x:x+(R()-.5)*1.2,y:y-.6,z:z+(R()-.5)*1.2,vy:1.5+R()*2.5,life:700+R()*400,s:.09+R()*.08,c:R()<.8?'#3ee08a':'#ff4a5a',k:'c',dr:.97});burst(x,y,z,18,{c:c2,sp:2.5,s:.1})}
  if(L.hit=='boom'){burst(x,y,z,40,{c:c2,sp:5,s:.16,life:600,g:-1.5});burst(x,y,z,20,{c:c1,sp:3,s:.1,life:400});burst(x,y+.2,z,12,{c:'rgba(90,60,40,A)',sp:1.5,s:.3,life:1100,g:-1,x2:{grow:2,a:.5}});add({x,y:y-.8,z,s:.7,life:500,c:'#ffb050',k:'ring',grow:2.5})}
  if(L.hit=='rug'){for(let i=0;i<3;i++)add({x,y:y-.9,z,s:.4+i*.25,life:700,c:'#c77dff',k:'ring',grow:1.5,t0:T()+i*90});burst(x,y,z,30,{c:c2,sp:3.5,s:.11})}
  if(L.hit=='moonhit'){burst(x,y-.6,z,30,{c:c1,sp:3,s:.1,life:700});add({x,y:y-.9,z,s:.6,life:700,c:'#ffffff',k:'ring',grow:2})}
  if(L.hit=='shatter'){for(let i=0;i<22;i++){const th=R()*TAU,sp=2+R()*4;add({x,y,z,vx:Math.cos(th)*sp,vy:1+R()*3,vz:Math.sin(th)*sp,g:6,life:800,s:.07+R()*.07,c:R()<.5?'#e8fbff':'#7fd6ff',k:'d',vr:(R()-.5)*14,dr:.98})}burst(x,y,z,20,{c:c1,sp:2,s:.06})}
  if(L.hit=='splash'){for(let i=0;i<30;i++){const th=R()*TAU,sp=1.5+R()*3;add({x,y:y-.5,z,vx:Math.cos(th)*sp,vy:2+R()*3.5,vz:Math.sin(th)*sp,g:9,life:800,s:.06+R()*.06,c:R()<.5?c1:c2,dr:.99})}for(let i=0;i<2;i++)add({x,y:y-.9,z,s:.5,life:800,c:'#5ff0ff',k:'ring',grow:2.5,t0:T()+i*120})}
  if(L.hit=='flare'){burst(x,y,z,36,{c:c2,sp:4,s:.13,g:-2,life:800});add({x,y:y+.4,z,s:.35,life:700,c:'#fff0fb',k:'moon',vy:1})}
  if(L.hit=='nova'){burst(x,y,z,70,{c:c2,sp:7,s:.16,life:900});burst(x,y,z,40,{c:'rgba(255,215,80,A)',sp:4,s:.12,life:800});for(let i=0;i<3;i++)add({x,y:y-.7,z,s:.6,life:900,c:i?'#ffd23f':'#ff3050',k:'ring',grow:4,t0:T()+i*110});
   EM.push({t0:T(),dur:450,tick:f=>{const a=prj(x,y,z);if(!a)return;c.strokeStyle='rgba(255,220,120,'+(1-f)+')';c.lineWidth=3;for(let k=0;k<12;k++){const th=k/12*TAU+f;c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(a[0]+Math.cos(th)*a[2]*(1+f*5),a[1]+Math.sin(th)*a[2]*(1+f*5)*.6);c.stroke()}}});if(!q)flash('rgba(255,90,60,.55)',.9)}}
 function spell(i,x0,z0,x1,z1,q){init();const L=LOOK[i]||LOOK[0],y0=hgt(x0,z0)+1.25,y1=hgt(x1,z1)+1.0,t0=T(),C=150,F=300,c1=rgba(L.c1),c2=rgba(L.c2);
  // charge-up: sparks spiral into the hands
  EM.push({t0,dur:C,tick:(f,now,dt)=>{for(let k=0,n=sp(dt,180);k<n;k++){const th=R()*TAU,r=.7*(1-f)+.1;add({x:x0+Math.cos(th)*r,y:y0+(R()-.3)*.5,z:z0+Math.sin(th)*r,vx:-Math.cos(th)*r*5,vz:-Math.sin(th)*r*5,vy:0,life:180,s:.06,c:c2})}core({x:x0,y:y0,z:z0,s:L.s*(.4+f),c:c1});core({x:x0,y:y0-.3,z:z0,s:.9*f,c:c2,a:.35});if(f>.5)core({x:x0,y:hgt(x0,z0)+.05,z:z0,s:.5+f*.4,c:L.c2,k:'ring',a:.8})}});
  if(L.tr=='beam'){EM.push({t0:t0+C,dur:F+200,tick:(f,now,dt)=>{const a=prj(x1,y1+9,z1),b=prj(x1,y1-.9,z1);if(!a||!b)return;const w=b[2]*.5*(f<.3?f/.3:1-(f-.3)/.7);const g=c.createLinearGradient(a[0]-w,0,a[0]+w,0);g.addColorStop(0,'rgba(190,210,255,0)');g.addColorStop(.5,'rgba(255,255,255,.95)');g.addColorStop(1,'rgba(190,210,255,0)');c.fillStyle=g;c.beginPath();c.moveTo(a[0]-w*.3,a[1]);c.lineTo(a[0]+w*.3,a[1]);c.lineTo(b[0]+w,b[1]);c.lineTo(b[0]-w,b[1]);c.fill();for(let k=0,n=sp(dt,50);k<n;k++)add({x:x1+(R()-.5)*.6,y:y1+R()*3,z:z1+(R()-.5)*.6,vy:-3,life:400,s:.07,c:c1})},end:()=>impact(L,x1,y1,z1,q)});return}
  EM.push({t0:t0+C,dur:F,end:()=>impact(L,x1,y1,z1,q),lf:0,tick:function(f,now,dt){const PO=g=>[x0+(x1-x0)*g,y0+(y1-y0)*g+Math.sin(g*Math.PI)*.35,z0+(z1-z0)*g],lf=this.lf;this.lf=f;const x=x0+(x1-x0)*f,z=z0+(z1-z0)*f,y=y0+(y1-y0)*f+Math.sin(f*Math.PI)*.35,dx=x1-x0,dz=z1-z0,dl=Math.hypot(dx,dz)||1;
   if(L.tr=='shards'){for(let k=-2;k<=2;k++){const ox=-dz/dl*k*.35*Math.sin(f*Math.PI),oz=dx/dl*k*.35*Math.sin(f*Math.PI);core({x:x+ox,y:y+Math.abs(k)*.08,z:z+oz,s:.16,c:k%2?'#7fd6ff':'#e8fbff',k:'d',rot:now/90+k})}}
   else core({x,y,z,s:L.s,c:c1});core({x,y,z,s:L.s*2.2,c:c2,a:.5});
   const tr=L.tr;for(let k=0,n=sp(dt,tr=='nova'?600:400);k<n;k++){const [x,y,z]=PO(lf+(f-lf)*R());
    if(tr=='spark')add({x,y,z,vx:(R()-.5)*4,vy:(R()-.5)*4,vz:(R()-.5)*4,life:220,s:.05,c:c1});
    if(tr=='candle')add({x,y,z,vy:1+R()*2,life:450,s:.06,c:R()<.85?'#3ee08a':'#ff4a5a',k:'c'});
    if(tr=='fire'){add({x:x+(R()-.5)*.2,y,z:z+(R()-.5)*.2,vy:1+R(),life:380,s:.14+R()*.1,c:R()<.5?c2:'rgba(255,200,80,A)',grow:-.5});if(R()<.4)add({x,y,z,vy:.8,life:800,s:.18,c:'rgba(80,60,50,A)',a:.35,grow:2})}
    if(tr=='vortex'){const th=now/60+k*1.57,r=.45;add({x:x+Math.cos(th)*r,y:y+Math.sin(th)*r*.6,z:z+Math.sin(th)*r,life:260,s:.07,c:k%2?c1:c2})}
    if(tr=='wave'){const off=(k-1.5)*.25;add({x:x-dz/dl*off,y:y-.3+Math.abs(off)*.4,z:z+dx/dl*off,vy:1.5+R(),g:5,life:420,s:.08,c:R()<.5?c1:c2})}
    if(tr=='moonfire')add({x:x+(R()-.5)*.25,y,z:z+(R()-.5)*.25,vy:1.2+R(),life:420,s:.11,c:R()<.5?c2:'rgba(255,240,251,A)',grow:-.6});
    if(tr=='nova')add({x,y,z,vx:(R()-.5)*3,vy:(R()-.5)*3,vz:(R()-.5)*3,life:500,s:.12,c:R()<.5?c2:'rgba(255,215,80,A)'});
    if(tr=='shards')add({x,y,z,vx:(R()-.5)*2,vy:(R()-.5)*2,vz:(R()-.5)*2,life:300,s:.04,c:c1})}
   if(tr=='spark'&&R()<.6){const a=prj(x,y,z);if(a){for(let k=0;k<2;k++){const th=R()*TAU;bolt(a,[a[0]+Math.cos(th)*a[2]*.6,a[1]+Math.sin(th)*a[2]*.6],'rgba(255,250,190,.85)',1.5)}}}
   if(tr=='moonfire')core({x,y:y+.05,z,s:L.s*.8,c:'#fff0fb',k:'moon'})}})}
 // a real arrow: wooden shaft, steel head and fletching, drawn along its own flight arc; it sticks where it lands
 function arw(h,t,a,col,gc){const qh=prj(h[0],h[1],h[2]),qt=prj(t[0],t[1],t[2]);if(!qh||!qt)return;let ux=qh[0]-qt[0],uy=qh[1]-qt[1];const L=Math.hypot(ux,uy)||1;ux/=L;uy/=L;const px=-uy,py=ux,k=qh[2];
  const w=Math.max(1.2,k*.0225),hl=Math.max(4,k*.085),hw=hl*.42,fl=Math.max(3,k*.075);
  const G=rgba(gc||'#ffd36a');c.lineCap='round';c.globalAlpha=1;c.strokeStyle=G.replace('A',.22*a);c.lineWidth=w*6;c.beginPath();c.moveTo(qt[0],qt[1]);c.lineTo(qh[0],qh[1]);c.stroke();c.strokeStyle=G.replace('A',.45*a);c.lineWidth=w*2.6;c.stroke();glow(qh[0]+ux*hl*.5,qh[1]+uy*hl*.5,hl*1.7,G,.75*a);
  c.globalCompositeOperation='source-over';c.globalAlpha=a;
  c.strokeStyle='rgba(0,0,0,.55)';c.lineWidth=w+1.6;c.beginPath();c.moveTo(qt[0],qt[1]);c.lineTo(qh[0],qh[1]);c.stroke();
  c.strokeStyle='#8a5a2e';c.lineWidth=w;c.beginPath();c.moveTo(qt[0],qt[1]);c.lineTo(qh[0],qh[1]);c.stroke();
  c.fillStyle=col||'#e9e4da';c.strokeStyle='rgba(0,0,0,.5)';c.lineWidth=1;
  for(const sg of[1,-1]){c.beginPath();c.moveTo(qt[0]+ux*fl*.9,qt[1]+uy*fl*.9);c.lineTo(qt[0]+px*sg*fl*.45-ux*fl*.15,qt[1]+py*sg*fl*.45-uy*fl*.15);c.lineTo(qt[0]+ux*fl*.25,qt[1]+uy*fl*.25);c.closePath();c.fill();c.stroke()}
  c.fillStyle='#d5dde3';c.strokeStyle='#2a2f35';c.lineWidth=1.2;c.beginPath();c.moveTo(qh[0]+ux*hl,qh[1]+uy*hl);c.lineTo(qh[0]+px*hw,qh[1]+py*hw);c.lineTo(qh[0]-ux*hl*.15,qh[1]-uy*hl*.15);c.lineTo(qh[0]-px*hw,qh[1]-py*hw);c.closePath();c.fill();c.stroke();
  c.globalAlpha=1;c.globalCompositeOperation='lighter'}
 function arrow(x0,z0,x1,z1,col,gy,gc){gc=gc||'#ffd36a';const GC=rgba(gc);init();const y0=hgt(x0,z0)+1.35,y1=hgt(x1,z1)+(gy==null?.95:gy),t0=T(),D=Math.hypot(x1-x0,z1-z0),F=Math.max(280,D*60),ARC=Math.min(1.1,.15+D*.07),AL=.5;
  const pos=f=>[x0+(x1-x0)*f,y0+(y1-y0)*f+Math.sin(f*Math.PI)*ARC,z0+(z1-z0)*f];
  const tail=(f,h)=>{const b=pos(Math.max(0,f-.02)),e=f<.02?pos(.02):h,d=[e[0]-b[0],e[1]-b[1],e[2]-b[2]],n=Math.hypot(d[0],d[1],d[2])||1;return [h[0]-d[0]/n*AL,h[1]-d[1]/n*AL,h[2]-d[2]/n*AL]};
  EM.push({t0,dur:F,end:()=>{burst(x1,y1,z1,12,{c:GC,sp:2.4,s:.06,life:380,x2:{sc:.5}});const h=pos(1),tl=tail(1,h),sh=[h[0]+(h[0]-tl[0])*.3,h[1]+(h[1]-tl[1])*.3,h[2]+(h[2]-tl[2])*.3],st=[tl[0]+(h[0]-tl[0])*.3,tl[1]+(h[1]-tl[1])*.3,tl[2]+(h[2]-tl[2])*.3];
    EM.push({t0:T(),dur:gy==null?450:1800,tick:f=>arw(sh,st,(f<.6?1:1-(f-.6)/.4)*(.75+.25*Math.sin(f*30)),col,gc)})},
   tick:(f,now,dt)=>{const h=pos(f),tl=tail(f,h);for(let k=0,n=sp(dt,45);k<n;k++)add({x:tl[0]+(R()-.5)*.08,y:tl[1]+(R()-.5)*.08,z:tl[2]+(R()-.5)*.08,s:.05,life:260,c:GC,a:.6,vy:.2,sc:.5});arw(h,tl,1,col,gc)}})}
 return {spell,arrow}})();
"""
rep("function doAct(){", JS + "function doAct(){")
# magic: the effect replaces the plain orb (arrows keep the 3D arrow and get a streak); the hit number waits for the impact
rep("PJ.push({x0:P.px+.5,z0:P.py+.5,x1:gb.px+.5,z1:gb.py+.5,t0:performance.now(),c:col,k:s});\n setTimeout(()=>{fl(gb.x,gb.y,d,d?'#d22':'#39f');if(d)gb.hitT=performance.now()},390);",
    "if(s=='mg')FX.spell(SPL.indexOf(sp),P.px+.5,P.py+.5,gb.px+.5,gb.py+.5);else{PJ.push({x0:P.px+.5,z0:P.py+.5,x1:gb.px+.5,z1:gb.py+.5,t0:performance.now(),c:col,k:s});FX.arrow(P.px+.5,P.py+.5,gb.px+.5,gb.py+.5)}\n"
    " setTimeout(()=>{fl(gb.x,gb.y,d,d?'#d22':'#39f');if(d)gb.hitT=performance.now()},s=='mg'?(sp&&sp[0]=='Moon Beam'?820:600):390);")

open(PATH, 'w', encoding='utf-8').write(h)
print('vfx patch applied')
