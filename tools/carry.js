const CARRYG={v:[[-.06,.97,.24],[-.08,.86,.5]]};   // blades and axes: the carry is baked into the motions (tools/carry_bake.py), the hand turns with them
const CARRYA={Attack:1,Stab:1,Punch:1,Kick:1,Chop:1,Mine:1,Fish:1,Cook:1,Cast:1,Pickup:1,Death:1};
function carryK(cl,t){if(!cl||cl=='Idle'||cl=='Walking'||cl=='Running')return 1;if(cl=='Hit')return .75;const A=NCL[cl];if(A){const s=Math.max(0,A[0]-A[2]),b=Math.min(1,Math.max(0,(t-s)/.15),Math.max(0,(A[1]-t)/.2));return 1-b}return CARRYA[cl]?0:1}
function carryM(M,ty,cl,t,left){if(left)return M;const G=CARRYG[ty];if(!G)return M;const k=carryK(cl,t);if(k<=0)return M;const g0=G[cl=='Running'?1:0];
 let c=[M[1],M[4],M[7]];const L=Math.hypot(c[0],c[1],c[2])||1;c=c.map(v=>v/L);let g=[c[0]+(g0[0]-c[0])*k,c[1]+(g0[1]-c[1])*k,c[2]+(g0[2]-c[2])*k];const gl_=Math.hypot(g[0],g[1],g[2])||1;g=g.map(v=>v/gl_);
 const v=[c[1]*g[2]-c[2]*g[1],c[2]*g[0]-c[0]*g[2],c[0]*g[1]-c[1]*g[0]],s2=v[0]*v[0]+v[1]*v[1]+v[2]*v[2],co=c[0]*g[0]+c[1]*g[1]+c[2]*g[2];if(s2<1e-9)return M;const f=(1-co)/s2;
 const K=[0,-v[2],v[1], v[2],0,-v[0], -v[1],v[0],0],Q=[1,0,0,0,1,0,0,0,1];for(let i=0;i<3;i++)for(let j=0;j<3;j++){let kk=0;for(let q=0;q<3;q++)kk+=K[i*3+q]*K[q*3+j];Q[i*3+j]+=K[i*3+j]+kk*f}
 const N=[0,0,0,0,0,0,0,0,0];for(let i=0;i<3;i++)for(let j=0;j<3;j++){let a=0;for(let q=0;q<3;q++)a+=Q[i*3+q]*M[q*3+j];N[i*3+j]=a}return N}
