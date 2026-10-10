#!/usr/bin/env python3
"""Wearing a cape switches the character to the caped body (models/player_cape.json, playerf_cape.json),
made in Meshy with a plain grey cape. The game repaints that cape in the worn cape's colour, using the
cape mask stored in the model (tools/capemask.py). Until the caped body has loaded (or if there is none,
for example no female one yet) the old separate cape shape is drawn instead.
Run from the repo root after patch_net.py:  python3 tools/patch_capebody.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


CB = r"""
// ---- caped bodies: the cape is part of the character, painted in the worn cape's colour
const CBD={},CBL={},CBP={};
function capeCol(k){const it=ITM[k]||[];return /^#[0-9a-f]{6}$/i.test(it[2]||'')?it[2]:'#8c0c18'}
function capeBody(base,k){if(CAPEM[k])return null; // the MemeCape and Quest cape keep their own hooded models
 const src=base+'_cape',key='cb_'+src+'_'+k,m=MDL[key];if(m&&m.ok&&m.tex)return m;if(CBP[key])return null;
 if(!CBD[src]){if(!CBL[src]){CBL[src]=1;fetch('models/'+src+'.json').then(r=>r.ok?r.text():Promise.reject()).then(t=>{CBD[src]=t}).catch(()=>{CBL[src]=2})}return null}
 CBP[key]=1;const d=JSON.parse(CBD[src]);if(!d.cm)return null;capePaint(d,capeCol(k)).then(t=>{d.tex=t;delete d.cm;try{regMdl(key,d)}catch(e){}}).catch(()=>{});return null}
function capePaint(d,col){return new Promise((res,rej)=>{const a=new Image(),m=new Image();let n=0;const go=()=>{if(++n<2)return;
  const S=a.width,c=document.createElement('canvas');c.width=c.height=S;const x=c.getContext('2d');x.drawImage(a,0,0);const px=x.getImageData(0,0,S,S),p=px.data;
  const mc=document.createElement('canvas');mc.width=mc.height=S;const mx=mc.getContext('2d');mx.imageSmoothingEnabled=false;mx.drawImage(m,0,0,S,S);const mk=mx.getImageData(0,0,S,S).data;
  const q=parseInt(col.slice(1),16),R=q>>16,G=(q>>8)&255,B=q&255;
  for(let i=0;i<p.length;i+=4){const v=mk[i];if(v<60)continue;const hi=Math.max(p[i],p[i+1],p[i+2]),lo=Math.min(p[i],p[i+1],p[i+2]);if(v<200&&!(hi-lo<45&&hi>70))continue;
   const g=(p[i]+p[i+1]+p[i+2])/570;p[i]=Math.min(255,R*g+12*g);p[i+1]=Math.min(255,G*g+8*g);p[i+2]=Math.min(255,B*g+8*g)}
  x.putImageData(px,0,0);res(c.toDataURL('image/jpeg',.88))};a.onload=go;m.onload=go;a.onerror=m.onerror=rej;a.src=d.tex;m.src=d.cm})}
"""
rep("// ---- which animation to play:", CB + "// ---- which animation to play:")

# the player
rep("const PK=(st.ap&&st.ap.g)?'playerf':'player';needMdl(PK);needMdl('player');const PM=(MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player,",
    "const PK=(st.ap&&st.ap.g)?'playerf':'player';needMdl(PK);needMdl('player');const CBM=st.eq&&st.eq.cape&&st.body!==0?capeBody(PK,st.eq.cape):null;const PM=CBM||((MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player),")
rep("if(!(PC&&PC.n=='Death'))qCape(P.px+.5+Math.sin(pry)*la", "if(!(PC&&PC.n=='Death')&&!CBM)qCape(P.px+.5+Math.sin(pry)*la")

# other players
rep("const K=inf.g?'playerf':'player';needMdl(K);const PMo=(MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player;if(!PMo||!PMo.ok)continue;",
    "const K=inf.g?'playerf':'player';needMdl(K);const CBo=inf.c?capeBody(K,inf.c):null,PMo=CBo||((MDL[K]&&MDL[K].ok)?MDL[K]:MDL.player);if(!PMo||!PMo.ok)continue;")
rep("if(inf.c)qCape(o.px+.5,o.py+.5,o.r,inf.c)}", "if(inf.c&&!CBo)qCape(o.px+.5,o.py+.5,o.r,inf.c)}")

open(PATH, 'w', encoding='utf-8').write(h)
print('cape body patch applied')
