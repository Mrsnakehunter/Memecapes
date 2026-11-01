import json,base64,numpy as np,sys,os
NECK=float(os.environ.get('NECK','.07'));LOW=float(os.environ.get('LOW','.42'));XM=float(os.environ.get('XM','.10'))
def dec(s,t): return np.frombuffer(base64.b64decode(s),dtype=t)
def load(k):
    d=json.load(open('/home/claude/memecapes/models/%s.json'%k))
    V=dec(d['vb'],np.int16).astype(np.float32).reshape(-1,3)/1000
    N=dec(d['nb'],np.int8).astype(np.float32).reshape(-1,3)/127
    UV=dec(d['ub'],np.uint16); I=dec(d['ib'],np.uint16).reshape(-1,3)
    J=dec(d['jb'],np.uint8).reshape(-1,4); W=dec(d['wb'],np.uint8).astype(np.float32).reshape(-1,4)/255
    c=[c for c in d['an'] if c['n']=='Idle'][0]
    if 'fb' in c:
        q=dec(c['fb'],np.int16).astype(np.float32); n=c['nj']*12; F=q[:n].copy()
        sc=np.where(np.arange(n)%4==3,c['qs'][1],c['qs'][0]); F=F*sc/32767
    else: F=np.array(c['f'][0],np.float32)
    F=F.reshape(-1,3,4)
    return d,V,N,UV,I,J,W,F
def skin(V,N,J,W,F):
    P=np.zeros_like(V);Q=np.zeros_like(N)
    for k in range(4):
        M=F[J[:,k]]; w=W[:,k:k+1]
        P+=w*(np.einsum('vij,vj->vi',M[:,:,:3],V)+M[:,:,3]); Q+=w*np.einsum('vij,vj->vi',M[:,:,:3],N)
    return P,Q
def run(k,out,ylo=None,yhi=None,armr=.16):
    d,V,N,UV,I,J,W,F=load(k); P,Q=skin(V,N,J,W,F)
    wb=np.zeros((len(V),28),np.float32)
    for c in range(4): np.add.at(wb,(np.arange(len(V)),J[:,c]),W[:,c])
    torso=wb[:,[0,1,2,3,8,13]].sum(1); head=wb[:,[4,5,6,7]].sum(1); arm=wb[:,[9,14]].sum(1)
    low=wb[:,[10,11,12,15,16,17]+list(range(18,28))].sum(1)
    # joint positions from inverse bind: shoulder ~ arm bone origin; estimate from weighted mean of arm vertices nearest torso
    ys=P[:,1]; sh=np.median(ys[wb[:,[8,13]].sum(1)>.5]); neck_y=sh+NECK; hip_y=sh-LOW
    xs=np.abs(P[:,0]); xsh=np.percentile(xs[(wb[:,[8,13]].sum(1)>.5)],95)
    keep=(low<.5)&(ys<neck_y)&(ys>hip_y)&(xs<xsh+XM)&~((head>.5)&(ys>neck_y-.06))
    t=keep[I].all(1); I2=I[t]
    used=np.unique(I2); m=-np.ones(len(V),np.int64); m[used]=np.arange(len(used))
    P2=P[used]; P2-= (P2.max(0)+P2.min(0))/2
    Q2=Q[used]/np.maximum(np.linalg.norm(Q[used],axis=1,keepdims=True),1e-6)
    UV2=UV.reshape(-1,2)[used]
    o={'vb':base64.b64encode(np.round(P2*1000).astype(np.int16).tobytes()).decode(),
       'nb':base64.b64encode(np.round(Q2*127).astype(np.int8).tobytes()).decode(),
       'ub':base64.b64encode(UV2.astype(np.uint16).tobytes()).decode(),
       'ib':base64.b64encode(m[I2].astype(np.uint16).tobytes()).decode(),'tex':d['tex']}
    json.dump(o,open(out,'w')); print(k,len(I),'->',len(I2),'tris; size',P2.max(0)-P2.min(0), 'sh',sh)
if __name__=='__main__':
    for n in ['01','10','20','30','40','50','60','70','80']:
        run('arm_lv'+n,'/home/claude/memecapes/tools/dev/charview/icut_%s.json'%n)
