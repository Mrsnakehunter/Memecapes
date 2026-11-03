#!/usr/bin/env python3
"""NPCs out of awkward spots (Albert, Nov 3: "random NPCs in very weird awkward places": Farmer Ted inside a pine,
the Partner standing on the hay nest, the launchpad clerk in a forge, people pressed against lamp posts).

Runs once after the whole world is laid out (towns, roads, building facing, signs), just before the castle kit:
  1. any tree on the 8 tiles round a standing NPC is cleared (pines are wider than their tile, so an NPC next to one
     looks like he is standing inside it). Same tree-clearing the castle and towns already do (o.gone).
  2. an NPC closer to a prop than that prop's size (lamp, stall, well, fountain, forge, range, sign, chest, meme ring,
     quest objects) is moved to the nearest free tile that is clear of every prop and tree, keeping his facing.
  3. no bush grows within two tiles of a standing NPC (the broker stood inside one).
"""
import re, sys

P = 'play.html'
h = open(P).read()


def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (old[:80], h.count(old))
    h = h.replace(old, new)


A = "const CKIT=(()=>{"
JS = r"""{const NK=new Set(['sq_chef','sq_w1','sq_w2','sq_w3','sq_farmer','sq_nemo','sq_scroll','slayer','ge','lpad','trader','saw','capes','pt_npc']);
 const PZ=[];const pp=(a,r)=>a&&PZ.push([a[0],a[1],r]);PR.lamps.forEach(a=>pp(a,.95));PR.stalls.forEach(a=>pp(a,1.7));PR.wells.forEach(a=>pp(a,1.3));PR.fount.forEach(a=>pp(a,2.7));PR.forges.forEach(a=>pp(a,1.5));PR.ranges.forEach(a=>pp(a,1.2));PR.signs.forEach(a=>pp(a,.9));pp(PR.chest,1);
 const XR={ring:1.9,pt_bb:1.2,sq_nest:1.1,sq_flour:1.2,sq_churn:1.1,patch:.9,altar:1.2,brazier:1.1,agi:1.2,hot:1};XO.forEach(o=>{if(XR[o.k])PZ.push([o.x+.5,o.y+.5,XR[o.k]])});
 const clrT=(x,y)=>{for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const a=x+dx,b=y+dy;if(!ok(a,b))continue;const t=ob[b][a];if(t&&t.k=='tree'&&!t.gone){t.gone=1;ob[b][a]=null}}};
 const treeNear=(x,y)=>{for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const a=x+dx,b=y+dy;if(ok(a,b)&&ob[b][a]&&ob[b][a].k=='tree'&&!ob[b][a].gone)return 1}return 0};
 const propHit=(x,y,self)=>PZ.some(p=>p!==self&&Math.hypot(p[0]-x-.5,p[1]-y-.5)<p[2]);
 const NPCS=XO.filter(o=>NK.has(o.k));const others=o=>NPCS.some(n=>n!==o&&Math.hypot(n.x-o.x,n.y-o.y)<1.5);
 window.__npcMoved=[];
 for(const o of NPCS){if(propHit(o.x,o.y)||others(o)){let best=null;for(let q=1;q<=5&&!best;q++)for(let dy=-q;dy<=q&&!best;dy++)for(let dx=-q;dx<=q;dx++){if(Math.max(Math.abs(dx),Math.abs(dy))!=q)continue;const a=o.x+dx,b=o.y+dy;
   if(!ok(a,b)||solid(a,b)||ob[b][a]||tile[b][a]==1||propHit(a,b)||NPCS.some(n=>n!==o&&Math.hypot(n.x-a,n.y-b)<1.5))continue;if(treeNear(a,b)&&q<5)continue;best=[a,b];break}
  if(best){window.__npcMoved.push([o.k,o.x,o.y,best[0],best[1]]);ob[o.y][o.x]=null;o.x=best[0];o.y=best[1];ob[o.y][o.x]=o}}
  clrT(o.x,o.y)}
 self.NPCNB=new Set();for(const o of NPCS)for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++)NPCNB.add((o.y+dy)*W+o.x+dx);
 PR.guards.forEach(a=>clrT(Math.floor(a[0]),Math.floor(a[1])));SB.forEach(s=>clrT(Math.floor(s.nx),Math.floor(s.nz)))}
"""
rep(A, JS + A)
rep("if(tile[y][x]!=0||ob[y][x])continue;const q=th(x,y);", "if(tile[y][x]!=0||ob[y][x]||(self.NPCNB&&NPCNB.has(y*W+x)))continue;const q=th(x,y);", 2)
open(P, 'w').write(h)
print('npc spots patched')
