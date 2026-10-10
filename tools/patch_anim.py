#!/usr/bin/env python3
"""Real animations for the 3D characters, as soon as a model has them.

The game picks a clip by what the character is doing and plays it if the model has one with that name
(added with tools/addclips.py); if not, it does exactly what it did before. Clip names:
  player: Idle, Attack (sword/stab/slash), Punch, Kick, Hit, Death, Chop, Mine, Fish, Cook, Cast (home Telly),
          Jump (agility), and one per emote, named like the emote (Stonks, GG, Ratio, Wave, Dance, ...)
  monsters: Idle, Attack, Hit, Death
Run from the repo root after patch_wear.py:  python3 tools/patch_anim.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


HELP = r"""
// ---- which animation to play: the clip for what the character is doing, if the model has it
const ACL={stab:['Attack'],slash:['Attack'],punch:['Punch','Attack'],kick:['Kick','Punch','Attack'],block:['Hit'],die:['Death'],home:['Cast'],agi:['Jump'],chop:['Chop'],mine:['Mine'],net:['Fish','Pickup'],cook:['Cook','Pickup'],guard:['Idle']};
function pClip(PM,skA,mvg,now){if(!PM||!PM.clips)return null;const has=n=>PM.clips[n]?n:null;
 if(pAnim){const k=pAnim.k,el=(now-pAnim.t0)/1000;const L=k.startsWith('em:')?[k.slice(3)]:(ACL[k]||[]);for(const n of L)if(has(n)){const c=PM.clips[n],dur=(c.f.length-1)/c.fps;return{n,t:k=='die'?Math.min(el,dur):el,once:k=='die'}}}
 if(skA&&!mvg)for(const n of(ACL[skA]||[]))if(has(n))return{n,t:now/1000};
 if(mvg)return null;return has('Idle')?{n:'Idle',t:now/1000}:null}
"""
rep("function qCape(x,z,yaw){", HELP + "function qCape(x,z,yaw){")

# the player: draw the model with the chosen clip; with a Death clip, the model falls instead of the old blocky figure
rep("const PM=(MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player;if(PM&&PM.ok&&st.body!==0&&!(po&&po.fall)){const la=po&&po.lunge||0;qMdl(PM,P.px+.5+Math.sin(pry)*la,0,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),MDLSC.player,mvg?(pspd>2.4?'Running':'Walking'):null,now/1000,0,null,false,1);qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0),mvg?(pspd>2.4?'Running':'Walking'):null,now/1000);qCape(P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+(po&&po.spin||0))}",
    "const PM=(MDL[PK]&&MDL[PK].ok)?MDL[PK]:MDL.player,PC=PM&&PM.ok?pClip(PM,skA,mvg,now):null;if(PM&&PM.ok&&st.body!==0&&(!(po&&po.fall)||PC)){const la=PC?0:po&&po.lunge||0,sp=PC?0:po&&po.spin||0,cl=PC?PC.n:mvg?(pspd>2.4?'Running':'Walking'):null,ct=PC?PC.t:now/1000;qMdl(PM,P.px+.5+Math.sin(pry)*la,0,P.py+.5+Math.cos(pry)*la,pry+sp,MDLSC.player,cl,ct,0,null,false,1);qHeld(PM,P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+sp,cl,ct);if(!(PC&&PC.n=='Death'))qCape(P.px+.5+Math.sin(pry)*la,P.py+.5+Math.cos(pry)*la,pry+sp)}")

# an emote lasts as long as its animation
rep("function playEmote(e){if(dieT)return;pAnim={k:'em:'+e,t0:performance.now(),d:3000};",
    "function playEmote(e){if(dieT)return;pAnim={k:'em:'+e,t0:performance.now(),d:3000};{const PX=MDL[(st.ap&&st.ap.g)?'playerf':'player'],cc=PX&&PX.clips&&PX.clips[e];if(cc)pAnim.d=Math.max(1200,cc.f.length/cc.fps*1000)}")

# monsters: Attack when they swing, Idle when standing, if the model has them
rep("qMdl(mm,x+ldx/ll*la,0,z+ldz/ll*la,gb.ry||0,(MDLSC[mm.k]||1)*(MSK[MT[gb.t].k]||1),d?'Walking':null,(gb.ph||0)/4);return}}",
    "const mA=gb.atkT&&now-gb.atkT<900&&mm.clips.Attack,mcl=mA?'Attack':d?'Walking':mm.clips.Idle?'Idle':null,mt=mA?(now-gb.atkT)/1000:mcl=='Idle'?now/1000:(gb.ph||0)/4;qMdl(mm,x+(mA?0:ldx/ll*la),0,z+(mA?0:ldz/ll*la),gb.ry||0,(MDLSC[mm.k]||1)*(MSK[MT[gb.t].k]||1),mcl,mt);return}}")

open(PATH, 'w', encoding='utf-8').write(h)
print('anim patch applied')
