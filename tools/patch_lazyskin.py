#!/usr/bin/env python3
"""Animations are prepared when they are first played, not all at load time.

Before, every frame of every animation was skinned and uploaded to the graphics card as soon as a
character loaded. With 40 animations per character that is far too much memory and a long freeze.
Now Walking and Running are prepared at load (they are used all the time) and any other animation
the first time it plays. Clips can also be stored packed (16-bit numbers, "fb") to keep files small.
Run from the repo root after patch_capebody.py:  python3 tools/patch_lazyskin.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


a = h.find("if(d.sk&&d.an){const J=d.sk.j,Wt=d.sk.w;for(const c of d.an){const F=[];")
end = "m.clips[c.n]={f:F,fps:c.fps,hand:c.hand,handL:c.handL}}"
b = h.find(end, a)
assert a > 0 and b > a
old_block = h[a:b + len(end)]
new_block = ("if(d.sk&&d.an){m.skin={V,N0,J:d.sk.j,W:d.sk.w,nv};for(const c of d.an){const raw=c.fb?clipUnpack(c):c.f;"
             "m.clips[c.n]={raw,nf:raw.length,fps:c.fps,hand:c.hand,handL:c.handL,f:null};"
             "if(c.n=='Walking'||c.n=='Running')skinClip(m,m.clips[c.n],1)}"
             "const w0=m.clips.Walking||m.clips[Object.keys(m.clips)[0]];if(w0&&!w0.f)skinClip(m,w0,1);")
h = h[:a] + new_block + h[b + len(end):]

HELP = r"""
// ---- animations are skinned the first time they play
function clipUnpack(c){const b=atob(c.fb),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);const q=new Int16Array(u.buffer),n=c.nj*12,F=[],sr=c.qs[0]/32767,st=c.qs[1]/32767;
 for(let f=0;f<q.length/n;f++){const a=new Float32Array(n);for(let i=0;i<n;i++){const v=q[f*n+i];a[i]=(i%4==3)?v*st:v*sr}F.push(a)}return F}
function skinClip(m,c,keepP){const S=m.skin,V=S.V,N0=S.N0,J=S.J,Wt=S.W,nv=S.nv,F=[];
 for(const fm of c.raw){const P=new Float32Array(nv*3),N=new Float32Array(nv*3);for(let v=0;v<nv;v++){const x=V[v*3],y=V[v*3+1],z=V[v*3+2],nx=N0[v*3],ny=N0[v*3+1],nz=N0[v*3+2];let px=0,py=0,pz=0,qx=0,qy=0,qz=0;for(let k=0;k<4;k++){const w=Wt[v*4+k];if(!w)continue;const b=J[v*4+k]*12;px+=w*(fm[b]*x+fm[b+1]*y+fm[b+2]*z+fm[b+3]);py+=w*(fm[b+4]*x+fm[b+5]*y+fm[b+6]*z+fm[b+7]);pz+=w*(fm[b+8]*x+fm[b+9]*y+fm[b+10]*z+fm[b+11]);qx+=w*(fm[b]*nx+fm[b+1]*ny+fm[b+2]*nz);qy+=w*(fm[b+4]*nx+fm[b+5]*ny+fm[b+6]*nz);qz+=w*(fm[b+8]*nx+fm[b+9]*ny+fm[b+10]*nz)}const l=Math.hypot(qx,qy,qz)||1;P[v*3]=px;P[v*3+1]=py;P[v*3+2]=pz;N[v*3]=qx/l;N[v*3+1]=qy/l;N[v*3+2]=qz/l}F.push(keepP?{g:packFrame(m,P,N),P}:{g:packFrame(m,P,N)})}
 c.f=F}
"""
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){", HELP + "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){")
# prepare a clip the first time it is drawn
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){const c=m.clips[clip]||m.clips[clip=='Running'?'Walking':null];",
    "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){const c=m.clips[clip]||m.clips[clip=='Running'?'Walking':null];if(c&&!c.f)skinClip(m,c);")
# clip lengths come from the frame count, which is known before skinning
rep("const c=PM.clips[n],dur=(c.f.length-1)/c.fps,", "const c=PM.clips[n],dur=(c.nf-1)/c.fps,")
rep("if(cc)pAnim.d=Math.max(1200,cc.f.length/cc.fps*1000)}", "if(cc)pAnim.d=Math.max(1200,cc.nf/cc.fps*1000)}")
# a swing, kick or flinch lasts about as long as its animation (a little faster), never longer than the time between attacks
rep("function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){const c=m.clips[clip]",
    "function aDur(k,d0,mx){const PX=MDL[(st.ap&&st.ap.g)?'playerf':'player'];if(!PX||!PX.clips)return d0;for(const n of(ACL[k]||[])){const c=PX.clips[n];if(c)return Math.max(d0,Math.min(mx,(c.nf-1)/c.fps*1000/1.15))}return d0}\n"
    "function qMdl(m,x,y,z,yaw,s,clip,t,cut,sm,gh,pl){const c=m.clips[clip]")
rep("['punch','kick','punch','punch'][cs],t0:performance.now(),d:900}}", "['punch','kick','punch','punch'][cs],t0:performance.now(),d:900};pAnim.d=aDur(pAnim.k,900,(atkCd||4)*540)}")
rep("pAnim={k:'block',t0:performance.now(),d:500}", "pAnim={k:'block',t0:performance.now(),d:aDur('block',500,1000)}")
# the weapon drops out of sight once the character hits the ground
rep("function qHeld(PM,x,z,yaw,clip,t){const wk=heldKey();", "function qHeld(PM,x,z,yaw,clip,t){if(clip=='Death'&&t>1.3)return;const wk=heldKey();")
# the idle pose search only needs the Walking clip (skinned with positions kept)
rep("for(const c in m.clips)for(const fr of m.clips[c].f)delete fr.P}}", "for(const c in m.clips)if(m.clips[c].f)for(const fr of m.clips[c].f)delete fr.P}}")

open(PATH, 'w', encoding='utf-8').write(h)
print('lazy skin patch applied')
