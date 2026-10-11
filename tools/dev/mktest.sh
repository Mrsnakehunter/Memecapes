#!/bin/sh
# build scratch/site/test.html (play.html + test hooks) and copy models
python3 - <<'P'
h=open('/home/claude/memecapes/play.html').read()
a="PT.x=PT.px=x;PT.y=PT.py=y+1;PT.tr=[]};"
assert h.count(a)==1
h=h.replace(a,a+"window.__tp=tpTo;window.__cam=(a,b,c)=>{yaw=a;pit=b;dist=distT=c};window.__T=tile;window.__O=ob;window.__P=P;")
open('/home/claude/scratch/site/test.html','w').write(h)
P
python3 - <<'P'
h=open('/home/claude/scratch/site/test.html').read()
a="window.__P=P;"
assert h.count(a)==1
h=h.replace(a,a+"window.__g=()=>({TW,PR,CKIT,MDL,HS,SB,st,ct,IN,ITM,slotOf,IC,heldKey,capeUI,QD,say,gobs,MT,PT,ringUI,modal,XO,questVisit,EX,NM,SLOT,ITM,RAR,AB,WST,SELL,MDLFOR,MDLSC,PETN,P,geOpen,p2pOpen,mkTick,p2pTheirs});")
open('/home/claude/scratch/site/test2.html','w').write(h)
P
# test3: no fog, wide visibility (for aerial review shots)
python3 - <<'P'
h=open('/home/claude/scratch/site/test2.html').read()
h=h.replace('clamp((vf-26.)/24.,0.,1.)','clamp((vf-140.)/60.,0.,1.)')
import re
h=re.sub(r'RADS=\[[^\]]*\]','RADS=[80,80,80,80]',h,count=1)
assert h.count('let budget=frameN<4?40:1;')==1
h=h.replace('let budget=frameN<4?40:1;','let budget=frameN<4?40:12;')
a="const vis=(x,y,r)=>Math.abs(x-P.px)<(r||38)&&Math.abs(y-P.py)<(r||38);"
assert h.count(a)==1
h=h.replace(a,"const vis=(x,y,r)=>Math.abs(x-P.px)<Math.max(r||38,70)&&Math.abs(y-P.py)<Math.max(r||38,70);")
open('/home/claude/scratch/site/test3.html','w').write(h)
P
# test7: test2 + __S() for shot scripts
python3 - <<'P'
h=open('/home/claude/scratch/site/test2.html').read()
a="window.__P=P;"
assert h.count(a)==1
h=h.replace(a,a+"window.__S=()=>({tgt,go,gobs,MT,trees,fish,rocks,st,TW,CA,P,SQO:window.SQO,fires,save,ui,pa:(k,d)=>{pAnim={k,t0:performance.now(),d:d||900}},pc:()=>pAnim});")
open('/home/claude/scratch/site/test7.html','w').write(h)
P
