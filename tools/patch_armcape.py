#!/usr/bin/env python3
"""Capes over armour (Albert, Oct 29: a cape must still show when an armour set is worn).

Armour sets are whole 3D bodies, and capes are part of the caped bodies, so a player in armour had no cape. Now each
armour set has its own cape cloth (models/arm_lvNN_cape.json, tools/mkarmorcape.py) built round that armour's standing
pose. In the game the cloth borrows the armour's animation matrices (same rig and bind), so it swings with the armour,
and it is drawn right after the body: for you and for other players.
  - MemeCape: its meme-patch painting. Any other cape: the grey velvet tinted to the cape's colour (gold border kept).
    Cape skins painted for the caped bodies (cs_*) show as the cape's plain colour on armour for now.
  - The stiff fallback cape is never drawn over armour.
Run after patch_armor.py:  python3 tools/patch_armcape.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


AC = r"""const ACD={},ACP={};
function armCape(ak,k,sk){const a=ak&&ARMS[ak];if(!a||!k)return null;const am=MDL[a[0]];if(!am||!am.ok||!am.clips.Walking)return null;
 const col=k=='memecape'?null:capeCol(sk&&sk.startsWith('ptc_')?sk:k),key='ac_'+a[0]+'_'+(col||'memecape'),m=MDL[key];if(m&&m.ok&&m.tex)return m;if(ACP[key])return null;
 const src=a[0]+'_cape';if(!ACD[src]){if(!ACP[src]){ACP[src]=1;fetch('models/'+src+'.json').then(r=>r.ok?r.json():Promise.reject()).then(d=>{ACD[src]=d;delete ACP[src]}).catch(()=>{setTimeout(()=>{delete ACP[src]},8000)})}return null}
 ACP[key]=1;const d=ACD[src],an=[];for(const n in am.clips){const c=am.clips[n];if(c.raw)an.push({n,f:c.raw,fps:c.fps,hand:c.hand,handL:c.handL})}
 const geo={vb:d.vb,nb:d.nb,ub:d.ub,ib:d.ib,jb:d.jb,wb:d.wb,nj:d.nj,an};
 (col?capePaint({tex:d.texp,cm:d.cm},col):Promise.resolve(d.texm)).then(t=>{geo.tex=t;try{regMdl(key,geo)}catch(e){}}).catch(()=>{});return null}
"""
rep("function armBody(k){", AC + "function armBody(k){")

# you: no caped body while armour is on (the cape comes from armCape), no stiff fallback, cape drawn after the body
rep("CBM=(SKTC||st.eq&&st.eq.cape)&&st.body!==0?capeBody(PK,SKTC?'cape_try':st.eq.cape,capeSkin()):null;const ARMB=st.body!==0?armBody(armKey()):null,",
    "ARMB=st.body!==0?armBody(armKey()):null,CBM=!ARMB&&(SKTC||st.eq&&st.eq.cape)&&st.body!==0?capeBody(PK,SKTC?'cape_try':st.eq.cape,capeSkin()):null,")
rep("qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+sp,cl,ct);if(!(PC&&PC.n=='Death')&&!CBM)qCape(",
    "qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+sp,cl,ct);"
    "if(ARMB&&(SKTC||st.eq&&st.eq.cape)){const AC=armCape(armKey(),SKTC?'cape_try':st.eq.cape,capeSkin());if(AC)qMdl(AC,P.px+.5+Math.sin(pry)*la,0,P.py+.5+Math.cos(pry)*la,pry+sp,MDLSC.player,cl,ct,0,null,false,1)}"
    "if(!(PC&&PC.n=='Death')&&!CBM&&!ARMB)qCape(")
# other players
rep("  if(ck&&!CBo)qCape(x,z,o.r,ck);",
    "  if(AMo&&ck){const AC=armCape(c2[1],ck,csk);if(AC)qMdl(AC,x,0,z,o.r,MDLSC.player,cl,t0,0,null,false,1)}else if(ck&&!CBo)qCape(x,z,o.r,ck);")

open(PATH, 'w', encoding='utf-8').write(h)
print('armour cape patch applied')
