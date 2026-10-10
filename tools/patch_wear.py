#!/usr/bin/env python3
"""Every cape is worn in 3D, not only the MemeCape and the Quest cape.

The game paints a cape texture for each cape item (its own colour, a MemeCapes medallion on the back,
a pattern of its own, a gold border when it is trimmed or rare) onto one shared cape shape
(models/c_plain.json, made by tools/mkcape.py plain). Skill capes, the Chad cape, the Meme cape,
the Treasure cape and custom capes from the shop all use it.
Run from the repo root after patch_launch.py:  python3 tools/patch_wear.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


NEW = r"""const CAPEM={memecape:'c_memecape',qcape:'c_qcape'},CAPEP={};let CPD=null,CPDL=0;
function capeShade(c,f){const n=parseInt(c.slice(1),16);let r=n>>16,g=(n>>8)&255,b=n&255;const m=v=>Math.max(0,Math.min(255,Math.round(f<0?v*(1+f):v+(255-v)*f)));return 'rgb('+m(r)+','+m(g)+','+m(b)+')'}
function mkCape(k,name){if(!CPD){if(!CPDL){CPDL=1;fetch('models/c_plain.json').then(r=>r.json()).then(d=>{CPD=d}).catch(()=>{CPDL=0})}delete CAPEP[name];return}
 const it=ITM[k]||[],col=/^#[0-9a-f]{6}$/i.test(it[2]||'')?it[2]:'#8c0c18',gold=name.endsWith('_t')||(it[4]||0)>=3,S=512,F=384,cv=document.createElement('canvas');cv.width=cv.height=S;const x=cv.getContext('2d');
 let hs=0;for(const ch of k)hs=(hs*31+ch.charCodeAt(0))>>>0;const pat=hs%5;
 const gr=x.createLinearGradient(0,0,0,F);gr.addColorStop(0,capeShade(col,.18));gr.addColorStop(.55,col);gr.addColorStop(1,capeShade(col,-.38));x.fillStyle=gr;x.fillRect(0,0,S,S);
 x.globalAlpha=.22;x.fillStyle=capeShade(col,.5);x.strokeStyle=capeShade(col,.5);x.lineWidth=14;
 if(pat==1){x.fillRect(F/2-26,0,52,F)}else if(pat==2){for(let y=170;y<F;y+=56){x.beginPath();x.moveTo(0,y);x.lineTo(F/2,y+40);x.lineTo(F,y);x.stroke()}}
 else if(pat==3){x.beginPath();x.moveTo(-20,F*.95);x.lineTo(F+20,F*.25);x.lineWidth=42;x.stroke()}else if(pat==4){x.lineWidth=4;for(let i=-F;i<F*2;i+=48){x.beginPath();x.moveTo(i,0);x.lineTo(i+F,F);x.stroke();x.beginPath();x.moveTo(i+F,0);x.lineTo(i,F);x.stroke()}}
 x.globalAlpha=1;const tr=gold?'#e8b830':capeShade(col,-.55);x.fillStyle=tr;x.fillRect(0,0,13,F);x.fillRect(F-13,0,13,F);x.fillRect(0,F-20,F,20);if(gold){x.fillStyle='#7a5208';x.fillRect(13,0,3,F-20);x.fillRect(F-16,0,3,F-20);x.fillRect(13,F-23,F-26,3)}
 x.fillStyle=capeShade(col,-.6);x.fillRect(F+4,0,S-F-4,S);
 const fin=()=>{const d=Object.assign({},CPD,{tex:cv.toDataURL('image/jpeg',.9)});try{regMdl(name,d)}catch(e){delete CAPEP[name]}};
 const im=new Image();im.onload=()=>{const cx=F/2,cy=118,r=62;x.save();x.beginPath();x.arc(cx,cy,r+9,0,7);x.fillStyle=gold?'#e8b830':'#c9a03a';x.fill();x.beginPath();x.arc(cx,cy,r,0,7);x.clip();x.drawImage(im,cx-r,cy-r,r*2,r*2);x.restore();fin()};im.onerror=fin;im.src=BRAND.logo}
function qCape(x,z,yaw){const k=st.eq&&st.eq.cape;if(!k)return;let cm=CAPEM[k];if(cm)needMdl(cm);else{cm='cp_'+k+(st.trim&&k.startsWith('cape_')?'_t':'');if(!MDL[cm]&&!CAPEP[cm]){CAPEP[cm]=1;mkCape(k,cm)}}const M=MDL[cm];if(!M||!M.ok||!M.tex)return;qMdl(M,x,0,z,yaw,MDLSC.player,null,0,0,null,false,0)}"""

rep("const CAPEM={memecape:'c_memecape',qcape:'c_qcape'};function qCape(x,z,yaw){const k=st.eq&&st.eq.cape,cm=k&&CAPEM[k];if(!cm)return;needMdl(cm);const M=MDL[cm];if(!M||!M.ok)return;qMdl(M,x,0,z,yaw,MDLSC.player,null,0,0,null,false,0)}",
    NEW)

open(PATH, 'w', encoding='utf-8').write(h)
print('wear patch applied')
