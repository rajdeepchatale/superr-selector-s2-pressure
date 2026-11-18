import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts')
T = pd.read_pickle('outputs/rated_balls.pkl'); rng=np.random.default_rng(3)
def pm_table(role, wcol):
    if role=='bat': d=T[T.faced]; pid='striker_id'; val='bat_val_adj'
    else: d=T; pid='bowler_id'; val='bowl_val_adj'
    w = d[wcol] if wcol else pd.Series(1.0, index=d.index)
    g = d.assign(wv=d[val]*w, w=w, P=(d.PI>=80)).groupby([pid,'match_id']).agg(v=('wv','sum'), n=('w','sum'), nP=('P','sum')).reset_index().rename(columns={pid:'pid'})
    return g
T['w_P'] = (T.PI>=80).astype(float)
T['w_LIcap'] = T.LI.clip(upper=4)
T['w_sqrtLI'] = np.sqrt(T.LI.clip(upper=9))
T['w_pct'] = T.PI/100
T['w_one'] = 1.0
def rel(role, wcol, minP):
    g = pm_table(role, wcol); tot = g.groupby('pid').nP.sum(); g = g[g.pid.isin(tot[tot>=minP].index)]
    ms = g.match_id.unique(); out=[]
    for s in range(40):
        h=set(rng.choice(ms,len(ms)//2,replace=False))
        g1=g[g.match_id.isin(h)].groupby('pid')[['v','n']].sum(); g2=g[~g.match_id.isin(h)].groupby('pid')[['v','n']].sum()
        j=g1.join(g2,lsuffix='1',rsuffix='2',how='inner'); j=j[(j.n1>0)&(j.n2>0)]
        x,y,w=j.v1/j.n1,j.v2/j.n2,np.sqrt(j.n1*j.n2); mx,my=np.average(x,weights=w),np.average(y,weights=w)
        out.append(np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w)))
    return np.mean(out), len(tot[tot>=minP])
print('Split-half reliability by weighting scheme (players with enough PRESSURE balls):')
for role, minP in [('bat',100),('bowl',120)]:
    print(role, {wc: round(rel(role,wc,minP)[0],3) for wc in ['w_P','w_LIcap','w_sqrtLI','w_pct','w_one']})
# How concentrated is each weighting on pressure balls?
for wc in ['w_P','w_LIcap','w_sqrtLI','w_pct','w_one']:
    print(f'{wc:9s}: share of total weight on top-20% pressure balls = {T.loc[T.PI>=80, wc].sum()/T[wc].sum():.0%}')
