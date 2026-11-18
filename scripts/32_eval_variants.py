"""Does each adjustment make the rating more repeatable? Split-half (random halves of matches, 40 splits)
   and out-of-time (2022-24 rating -> 2025-26 value). Same pressure weighting as the rating (PI/100)."""
import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_pwi import match_agg, ratings
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
def wcorr(x,y,w):
    x,y,w=map(np.asarray,(x,y,w)); mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def frame(role, col):
    if role=='bat': d = R[R.faced].rename(columns={'striker_id':'pid'}); d['ball']=1
    else: d = R.rename(columns={'bowler_id':'pid'}); d['ball']=d.legal.astype(int)
    d['val'] = d[col]; return d
VARS = {'bat': {'no adjustment':'bat_v', 'current (T20I team adj)':'bat_val_adj', '+ who they faced':'bat_v_opp', '+ conditions':'bat_v_cond', '+ both':'bat_v_full'},
        'bowl':{'no adjustment':'bowl_v','current (T20I team adj)':'bowl_val_adj','+ who they faced':'bowl_v_opp','+ conditions':'bowl_v_cond','+ both':'bowl_v_full'}}
rng = np.random.default_rng(5); ms = R.match_id.unique(); splits = [set(rng.choice(ms, len(ms)//2, replace=False)) for _ in range(40)]
for role in ['bat','bowl']:
    minp = 100 if role=='bat' else 120
    print(f'\n===== {role.upper()}')
    for lab, col in VARS[role].items():
        d = frame(role, col); g = match_agg(d, alpha=1)
        tot = g.groupby('pid').Pn.sum(); g = g[g.pid.isin(tot[tot>=minp].index)]
        sh=[]
        for h in splits:
            a = g[g.match_id.isin(h)].groupby('pid')[['wv','w']].sum(); b = g[~g.match_id.isin(h)].groupby('pid')[['wv','w']].sum()
            j = a.join(b, lsuffix='1', rsuffix='2', how='inner'); j=j[(j.w1>0)&(j.w2>0)]
            sh.append(wcorr(j.wv1/j.w1, j.wv2/j.w2, np.sqrt(j.w1*j.w2)))
        atr,_ = ratings(match_agg(d[d.year<=2024], alpha=1), 40 if role=='bat' else 50, 4, inn_min=4)
        ate,_ = ratings(match_agg(d[d.year>=2025], alpha=1), 40 if role=='bat' else 50, 4, inn_min=4)
        j = atr.join(ate, lsuffix='_tr', rsuffix='_te', how='inner'); j = j[(j.Pn_tr>=60)&(j.Pn_te>=40)]
        oot = wcorr(j.rating_tr, j.pwi_te, j.w_te)
        print(f'  {lab:26s} split-half r = {np.mean(sh):.3f} (sd over splits {np.std(sh):.3f}) | out-of-time r = {oot:+.3f} (n={len(j)}) | players {len(tot[tot>=minp])}')
