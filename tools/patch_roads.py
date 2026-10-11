#!/usr/bin/env python3
"""Road surfaces: not every road is dirt. Each road tile gets a surface from where it is and how important that place is.

  concrete slabs  the rich and modern places: Stonks City (the finance hub), Wall St., Moon Landing (the space base),
                  Diamond Hands (marble palaces)
  cobblestone     the old stone towns: Castle Gigachad and Gigachad Town (the capital) and the King's Road from the
                  castle to Wow Landing, HODL Heights (mountain monastery), Chad Falls (Roman villas), Rugpull Ridge
                  (cobbles with stones missing: it got rugged)
  dirt            villages and the wild: Wow Landing (only its market square is cobbled), Froggo's Pond (swamp mud),
                  every country road between towns, Ember Coast and the Trenches
At a town's edge the paving thins out into dirt over a few tiles. The stones and slabs are drawn by the ground
terrain shader from world position (materials 11 = cobblestone, 12 = concrete), so there are no extra textures to load.
The minimap and world map show the surfaces too (grey for paved).
Run from the repo root after patch_partner.py:  python3 tools/patch_roads.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


SURF = r"""
// ---- road surfaces (tools/patch_roads.py): 1 dirt, 2 cobblestone, 3 concrete
// town: [surface, radius it reaches from the centre, share of cobbles missing]
const RST={'Stonks City':[3,22],'Moon Landing':[3,22],'Diamond Hands':[3,20],'Chad Falls':[2,17],'HODL Heights':[2,17],'Rugpull Ridge':[4,15],'Wow Landing':[2,6],"Froggo's Pond":[1,0]};
const RSC=['#8f887d','#847d72'].map(col),RSK=['#b9b5ac','#afaba2'].map(col),RSF=new Uint8Array(W*H).fill(255);
function surfAt(x,y){if(x<0||y<0||x>=W||y>=H)return 0;const k=y*W+x;let s=RSF[k];if(s!=255)return s;s=0;
 if(tile[y][x]==2){s=1;
  if(x>=134&&x<=184&&y>=104&&y<=162)s=2;                       // Castle Gigachad and Gigachad Town
  else if(x>=386&&x<=448&&y>=188&&y<=270)s=3;                   // Wall St.
  else if(x>=148&&x<=166&&y>162&&y<=176)s=2;                    // the King's Road down to Wow Landing
  else for(const t of TW){const R=RST[t.n];if(!R||R[0]<2)continue;const dx=x-t.cx,dy=y-t.cy,d=Math.hypot(dx,dy),a=Math.atan2(dy,dx);
   const e=R[1]+(R[1]>8?1.8*Math.sin(a*3+t.cx)+1.2*Math.sin(a*5+t.cy):.8*Math.sin(a*4));                   // a slightly uneven edge, not a perfect circle
   if(d<=e){s=R[0];break}}}
 RSF[k]=s;return s}
// how much of the paving reaches a tile corner: 1 inside, less at the edge (stones thin out there)
const surfCorner=(x,y,s)=>((surfAt(x-1,y-1)==s)+(surfAt(x,y-1)==s)+(surfAt(x-1,y)==s)+(surfAt(x,y)==s))/4;
const surfCol=(x,y)=>{const s=surfAt(x,y);return s==2||s==4?RSC[hh(x,y)>.5|0]:s==3?RSK[hh(x,y)>.5|0]:PA[hh(x,y)>.5|0]};
"""
rep("const CS=32,CN=Math.ceil(W/CS),chunks={};", SURF + "const CS=32,CN=Math.ceil(W/CS),chunks={};")
# vertex colours: a paved tile pulls its corners to stone grey instead of dirt tan
rep("const c=tile[ty][tx]==2?PA[hh(tx,ty)>.5|0]:GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;",
    "const c=tile[ty][tx]==2?surfCol(tx,ty):GR[hh(tx,ty)*4|0],wgt=tile[ty][tx]==2?3:1;")
# the tile's material rides in the length of its normals (material + 1)
rep("else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1);[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>pvt(x+i,gh(x+i,y+j),y+j,V[3][0],V[3][1],V[3][2],V))}",
    "else{const A=vcol(x,y),B=vcol(x+1,y),C=vcol(x,y+1),D=vcol(x+1,y+1),sf=t==2?surfAt(x,y):0,mm=sf==2?12:sf==3?13:sf==4?15:1;[[0,0,A],[1,0,B],[0,1,C],[1,0,B],[1,1,D],[0,1,C]].forEach(([i,j,V])=>{const L=mm>1?mm+.45*surfCorner(x+i,y+j,sf):1;pvt(x+i,gh(x+i,y+j),y+j,V[3][0]*L,V[3][1]*L,V[3][2]*L,V)})}")
# terrain shader (pg3): cobblestones and concrete slabs, drawn from world position; the material rides in the normal length
rep("varying vec3 vwp;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);",
    "varying vec3 vwp;varying float vm,ve;void main(){gl_Position=M*vec4(p,1.);vec3 nn=normalize(n);float nl=length(n);vm=floor(nl+.02)-1.;ve=clamp((nl-vm-1.)/.45,0.,1.);")
rep("varying vec2 vl;varying vec3 vwp;uniform vec3 PL[8];", "varying vec2 vl;varying vec3 vwp;varying float vm,ve;float hs(vec3 p){return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453);}uniform vec3 PL[8];")
PAT = ("vec3 pv=vec3(mix(gp,sp,sand));"
       "if((vm>10.5&&vm<11.5)||(vm>13.5&&vm<14.5)){vec2 q=vw*2.5;float rw=floor(q.y);q.x+=fract(rw*.5);vec2 cl=floor(q),f=fract(q)-.5;float r=hs(vec3(cl,7.)),r2=hs(vec3(cl,9.));"
       "vec2 j=f*vec2(1.,1.1);float rd=length(max(abs(j)-.17,0.));float st=1.-smoothstep(.17,.25,rd);"
       "float keep=hs(vec3(cl,13.))<ve*1.4-(vm>13.5?.32:0.)?1.:0.;"
       "float sg=.88+.26*r;vec3 sc=vec3(sg*(1.+.05*r2),sg,sg*(.94+.04*r))*(.93+.14*d)*(1.06-.4*dot(j,j));"
       "vec3 dirt=vec3(1.05,.93,.7)*mix(gp,sp,.6);pv=mix(mix(dirt,vec3(.56,.52,.47),.35+.4*keep),sc,st*keep);}"
       "else if(vm>11.5&&vm<12.5){vec2 g=fract(vw);float w=.045;float se=1.-min(min(smoothstep(0.,w,g.x),smoothstep(0.,w,1.-g.x)),min(smoothstep(0.,w,g.y),smoothstep(0.,w,1.-g.y)));"
       "pv=vec3(.93+.1*d)*(.93+.12*hs(vec3(floor(vw),3.)))*(1.-.3*se);}")
rep("c*=mix(gp,sp,sand);c+=vc/max(lm,.05)*mix(gp,sp,sand)*plt(vwp,vec3(0.,1.,0.));", PAT + "c*=pv;c+=vc/max(lm,.05)*pv*plt(vwp,vec3(0.,1.,0.));")

# minimap and world map: paved streets show grey
rep("tile[y][x]==2?'#c2a066':b?", "tile[y][x]==2?['#c2a066','#c2a066','#8f887d','#b9b5ac'][surfAt(x,y)]:b?", 2)
rep("t==2?(q<3?'#c9a86c':'#c2a066'):", "t==2?[q<3?'#c9a86c':'#c2a066',q<3?'#c9a86c':'#c2a066',q<3?'#979085':'#8f887d',q<3?'#c0bcb3':'#b9b5ac'][surfAt(x,y)]:")

open(PATH, 'w', encoding='utf-8').write(h)
print('road surfaces patch applied')
