"""Is 'pressure performance' a stable, predictable trait?  (1) split-half reliability  (2) out-of-time prediction."""
import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_ratings import *
T = pd.read_pickle('outputs/rated_balls.pkl')
rng = np.random.default_rng(0)

def summarize(pm, ids=None):
    P=pm[pm.P]; N=pm[~pm.P]
    a=pd.DataFrame({'nP':P.groupby('pid').n.sum(),'sP':P.groupby('pid').v.sum(),'nN':N.groupby('pid').n.sum(),'sN':N.groupby('pid').v.sum()}).fillna(0)
    a['xP']=a.sP/a.nP.replace(0,np.nan); a['xN']=a.sN/a.nN.replace(0,np.nan); a['xA']=(a.sP+a.sN)/(a.nP+a.nN); a['D']=a.xP-a.xN
    return a
def wcorr(x,y,w):
    m=~(np.isnan(x)|np.isnan(y)); x,y,w=x[m],y[m],w[m]
    mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))

for role, minp in [('bat',100),('bowl',120)]:
    pm = player_match_table(T, role)
    # (1) split-half by match, 50 random splits
    tot = summarize(pm); keep = tot[(tot.nP>=minp)&(tot.nN>=minp)].index
    pm_k = pm[pm.pid.isin(keep)]
    matches = pm_k.match_id.unique(); r = {'xP':[], 'xN':[], 'xA':[], 'D':[], 'xN_predicts_xP':[], 'xA_predicts_xP':[]}
    for s in range(50):
        half = set(rng.choice(matches, len(matches)//2, replace=False))
        a1 = summarize(pm_k[pm_k.match_id.isin(half)]); a2 = summarize(pm_k[~pm_k.match_id.isin(half)])
        j = a1.join(a2, lsuffix='1', rsuffix='2', how='inner'); w = np.sqrt(j.nP1*j.nP2).values
        for k in ['xP','xN','xA','D']: r[k].append(wcorr(j[k+'1'].values, j[k+'2'].values, w))
        r['xN_predicts_xP'].append(wcorr(j['xN1'].values, j['xP2'].values, w))
        r['xA_predicts_xP'].append(wcorr(j['xA1'].values, j['xP2'].values, w))
    print(f'\n===== {role.upper()}: split-half reliability across 50 random splits of matches ({len(keep)} players)')
    for k,v in r.items(): print(f'  corr {k:16s}: mean {np.mean(v):+.3f}  (5-95%: {np.percentile(v,5):+.3f} .. {np.percentile(v,95):+.3f})')
    # (2) out-of-time: 2022-24 -> 2025-26
    tr = summarize(pm[pm.year<=2024]); te = summarize(pm[pm.year>=2025])
    j = tr.join(te, lsuffix='_tr', rsuffix='_te', how='inner')
    j = j[(j.nP_tr>=minp*0.6)&(j.nP_te>=minp*0.4)&(j.nN_tr>=minp*0.6)]
    w = j.nP_te.values
    print(f'  OUT-OF-TIME (train 2022-24 -> test 2025-26), {len(j)} players; target = test-period pressure value')
    for k in ['xP_tr','xN_tr','xA_tr','D_tr']:
        print(f'    predictor {k:7s}: corr {wcorr(j[k].values, j.xP_te.values, w):+.3f}')
    print(f'    delta persistence  D_tr -> D_te: corr {wcorr(j.D_tr.values, j.D_te.values, w):+.3f}')
    # blend search: lambda*pressure_shrunk + (1-lambda)*all_shrunk
    for lam in [0,0.25,0.5,0.75,1.0]:
        pred = lam*j.xP_tr + (1-lam)*j.xA_tr
        print(f'    blend lambda={lam:.2f} (weight on pressure-only evidence): corr {wcorr(pred.values, j.xP_te.values, w):+.3f}')
