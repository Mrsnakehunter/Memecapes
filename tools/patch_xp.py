#!/usr/bin/env python3
"""XP curve and levels: skills go to level 100, and level 100 takes 20,000,000 XP.
Hitpoints starts at level 12 (2,201 XP). Capes of Accomplishment are for level 100 and cost 100,000 Meme Coins.
Run from the repo root as part of the build:  python3 tools/patch_xp.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


HP12 = 2201  # XT[11] with the divisor below: the XP for Hitpoints level 12
# ---- the table: levels 1..100, level 100 = 20,000,000
rep("const XT=[0];{let p=0;for(let l=1;l<99;l++){p+=Math.floor(l+300*Math.pow(2,l/7));XT.push(Math.floor(p/4))}}",
    "const XT=[0];{let p=0;for(let l=1;l<100;l++){p+=Math.floor(l+300*Math.pow(2,l/7));XT.push(Math.floor(p/2.8782321))}}")
rep("const lvl=x=>{let l=1;while(l<99&&x>=XT[l])l++;return l};", "const lvl=x=>{let l=1;while(l<100&&x>=XT[l])l++;return l};")
# ---- progress bars and the skills tab: level 100 is the top
rep("const L=lvl(st.xp[k]),pc=L>=99?100:Math.max(0,Math.min(100,Math.round(100*(st.xp[k]-XT[L-1])/(XT[L]-XT[L-1]))));",
    "const L=lvl(st.xp[k]),pc=L>=100?100:Math.max(0,Math.min(100,Math.round(100*(st.xp[k]-XT[L-1])/(XT[L]-XT[L-1]))));")
rep("l=lvl(st.xp[k]),lo=XT[l-1],hi=l<99?XT[l]:lo+1;$('xpf').style.width=(l>=99?100:100*(st.xp[k]-lo)/(hi-lo))+'%';",
    "l=lvl(st.xp[k]),lo=XT[l-1],hi=l<100?XT[l]:lo+1;$('xpf').style.width=(l>=100?100:100*(st.xp[k]-lo)/(hi-lo))+'%';")
rep("const l=lvl(st.xp[k]),lo=XT[l-1],hi=l<99?XT[l]:lo+1,pc=l>=99?100:Math.floor(100*(st.xp[k]-lo)/(hi-lo));",
    "const l=lvl(st.xp[k]),lo=XT[l-1],hi=l<100?XT[l]:lo+1,pc=l>=100?100:Math.floor(100*(st.xp[k]-lo)/(hi-lo));")
rep("' / '+(l<99?hi:'max')+' xp</div>", "' / '+(l<100?hi:'max')+' xp</div>")
# combat rolls scale over 1..100
rep("const sk256=(lo,hi,l)=>(1+Math.floor(lo*(99-l)/98+hi*(l-1)/98+.5))/256;", "const sk256=(lo,hi,l)=>(1+Math.floor(lo*(100-l)/99+hi*(l-1)/99+.5))/256;")
# ---- cape merchant: level 100, 100,000 Meme Coins
rep("capes:'He sells Capes of Accomplishment to level 99 masters.'", "capes:'He sells Capes of Accomplishment to level 100 masters.'")
rep("const n99=Object.keys(NM).filter(k=>lvl(st.xp[k])>=99).length;", "const n99=Object.keys(NM).filter(k=>lvl(st.xp[k])>=100).length;")
rep("\"Reach level 99 in a skill and I will sell you its Cape of Accomplishment for 99,000 Meme Coins.'+(n99>=2?' With two or more 99s, your capes come trimmed.\"':'\"')",
    "\"Reach level 100 in a skill and I will sell you its Cape of Accomplishment for 100,000 Meme Coins.'+(n99>=2?' With two or more at 100, your capes come trimmed.\"':'\"')")
rep("' <small>('+l+'/99)</small></span>'+(l>=99?'<button data-cp=\"'+k+'\">Buy (99,000)</button>'",
    "' <small>('+l+'/100)</small></span>'+(l>=100?'<button data-cp=\"'+k+'\">Buy (100,000)</button>'")
rep("if(st.coins<99000)return say('You need 99,000 Meme Coins for that.','#c00');", "if(st.coins<100000)return say('You need 100,000 Meme Coins for that.','#c00');")
rep("burn(99000,'skill cape');", "burn(100000,'skill cape');")
# ---- Hitpoints starts at level 12
rep("xp:{wc:0,mi:0,fi:0,at:0,hp:1154,ck:0,sm:0,str:0,def:0},inv:[],hp:10,run:0,en:100,flow:[]};",
    "xp:{wc:0,mi:0,fi:0,at:0,hp:%d,ck:0,sm:0,str:0,def:0},inv:[],hp:12,run:0,en:100,flow:[]};" % HP12)
# old saves: bring Hitpoints up to level 12 once
rep("if(!st.hp10){if((st.xp.hp||0)<1154)st.xp.hp=(st.xp.hp||0)+1154;st.hp10=1}",
    "if(!st.hp10){if((st.xp.hp||0)<1154)st.xp.hp=(st.xp.hp||0)+1154;st.hp10=1}if(!st.hp12){if((st.xp.hp||0)<%d)st.xp.hp=%d;if(st.hp<12)st.hp=12;st.hp12=1}" % (HP12, HP12))
# ---- our own level-up line
rep("say('Congratulations, you just advanced '+(/^[AEIOU]/.test(NM[k])?'an ':'a ')+NM[k]+' level! You are now level '+a+'. (+'+bo+' Meme Coins)','#0a0')",
    "say('LEVEL UP! '+NM[k]+' is now '+a+(a>=100?' - maxed!':'.')+' (+'+bo+' Meme Coins)','#0a0')")

open(PATH, 'w', encoding='utf-8').write(h)
print('xp patch applied: 100 levels, level 100 = 20,000,000 xp, Hitpoints starts at 12')
