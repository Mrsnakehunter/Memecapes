# Weapons hang naturally while standing, walking and running: the right-hand weapon's length axis is turned toward a
# carry direction in the body's frame (sword/club/axe tip down by the leg, trailing back when running; staff upright),
# pivoting at the grip, so the wrist's swing no longer points the blade forward like a lance. Swings keep the
# animation's own grip (the carry fades out over 0.15 s as an attack starts and back in as it ends).
import re
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()
def rep(a, b, n=1):
    global h
    c = h.count(a); assert c == n, (c, a[:90]); h = h.replace(a, b)
CARRY = open('tools/carry.js').read().strip()
rep("M[i*3+j]=s*sP}const ws=cf[0]/(WHT[wk]||2),gy=cf[1]*cf[0];const px=(left?0:PALM[0])*sP",
    "M[i*3+j]=s*sP}{const M2=carryM(M,cf[2],clip,t,left);for(let i=0;i<9;i++)M[i]=M2[i]}const ws=cf[0]/(WHT[wk]||2),gy=cf[1]*cf[0];const px=(left?0:PALM[0])*sP")
rep("function qHold(PM,x,z,yaw,clip,t,wk,left,sc,dd){", CARRY + "\nfunction qHold(PM,x,z,yaw,clip,t,wk,left,sc,dd){")
open(PATH, 'w', encoding='utf-8').write(h)
print('carry patch applied')
