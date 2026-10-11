#!/usr/bin/env python3
"""See-through: only massive structures ever turn see-through when they block the camera.

Before, the "See-through walls" option hid far too much: every small object between the camera and the player
(fences, booths, crates, lamps, signposts, bridges, the procedural props) was cut away by a half-plane, and every 3D
model near the line of sight got a hole cut through it. Albert: only massive structures should do that; bushes,
flowers, trees, Meme Telly booths, small houses and the like must stay; the player moves the camera himself.

The rule now:
  - Massive = the castle (walls, towers, gate, keep) and buildings at least 6 tiles tall, or at least 5 tiles tall
    with a footprint of 64 square tiles or more (spires, clock and bell towers, windmill, church, chapel, manor,
    colosseum, exchange, gantry, the biggest banks, the bath house and the dome).
  - Massive structures: a round see-through hole around the player, and the whole building fades a little when the
    line from the camera to the player passes through it (as before).
  - Everything else never disappears. Shadows always stay whole.
The castle's procedural walls carry a "massive" flag in their vertex material (+32) so the shader can tell them apart.
Run from the repo root after the other patches:  python3 tools/patch_seethru.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# a material flag for massive static geometry (only the castle)
rep("let MAT=0;", "let MAT=0,BIGM=0;")
rep("const mf=1+MAT+(INH?16:0);", "const mf=1+MAT+(INH?16:0)+BIGM;")
rep("if(L.ca)castleObj(CA,0)}", "if(L.ca){BIGM=32;castleObj(CA,0);BIGM=0}}")
# object shader: decode the flag; cut only flagged (massive) geometry, with a round hole around the player
rep("vm=floor(nl+.5)-1.;float mv=vm-16.*step(15.5,vm);", "vm=floor(nl+.5)-1.;float mv=vm-32.*step(31.5,vm);mv-=16.*step(15.5,mv);")
rep("float hul=step(15.5,vm);float m=vm-16.*hul;if(cutR>0.){vec3 d=tgt-eye;float dd=dot(d,d);float t=dot(vp-eye,d)/dd;bool veg=(m>3.5&&m<6.5)||m>8.5;if(veg){if(m>9.5&&t>.02&&t<.985){float r=distance(vp,eye+d*t);float R=cutR*(.15+.85*t);if(smoothstep(R*.55,R,r)<bayer(gl_FragCoord.xy))discard;}}else{vec2 dh=tgt.xz-eye.xz;float pd=length(dh);float al=dot(vp.xz-eye.xz,dh)/max(pd,.001);if(smoothstep(pd-.25,pd+.7,al)<bayer(gl_FragCoord.xy))discard;}}",
    "float bg=step(31.5,vm);float vm2=vm-32.*bg;float hul=step(15.5,vm2);float m=vm2-16.*hul;if(cutR>0.&&bg>.5){vec3 d=tgt-eye;float dd=dot(d,d);float t=dot(vp-eye,d)/dd;if(t>.02&&t<.985){float r=distance(vp,eye+d*t);float R=cutR*(.15+.85*t);if(smoothstep(R*.55,R,r)<bayer(gl_FragCoord.xy))discard;}}")
# shadow pass: decode the flag, never cut (shadows stay whole)
rep("vm=floor(nl+.5)-1.;vm-=16.*step(15.5,vm);", "vm=floor(nl+.5)-1.;vm-=32.*step(31.5,vm);vm-=16.*step(15.5,vm);")
rep("gl.uniform1f(uScut,(started&&st.xr!==0)?3.2:0)", "gl.uniform1f(uScut,0)")
# 3D building models: only massive ones get the hole and the fade
rep("if(started&&st.xr!==0&&!(HX[c[0]][2]!=null&&HX[c[0]][2]*c[4]<1.3)){",
    "if(c[8]==null){const hx=HX[c[0]],H=hx[2]!=null?hx[2]*c[4]:99,A=4*hx[0]*hx[1]*c[4]*c[4];c[8]=H>=6||(H>=5&&A>=64)?1:0}if(started&&st.xr!==0&&c[8]){")
rep("qMdl(m,c[1],0,c[2],c[3],c[4],null,0,1,sm,gh)", "qMdl(m,c[1],0,c[2],c[3],c[4],null,0,c[8]?1:0,sm,gh)")
# the option's name says what it does now
rep("See-through walls: '+(st.xr===0?'Off':'On')", "See-through big buildings: '+(st.xr===0?'Off':'On')")

open(PATH, 'w', encoding='utf-8').write(h)
print('see-through patch applied')
