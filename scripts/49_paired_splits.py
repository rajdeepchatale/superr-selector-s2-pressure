"""Slide 10, 'Who was at the other end': in how many of 200 random half-splits of the matches is the
opponent-adjusted rating steadier (higher split-half agreement) than the unadjusted one? Same weighting and
qualification as 32_eval_variants; the two versions are compared on the SAME split each time."""
import pandas as pd, numpy as np, sys, json
sys.path.insert(0, 'scripts'); from lib_pwi import match_agg
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
def wcorr(x, y, w):
    x, y, w = map(np.asarray, (x, y, w)); mx, my = np.average(x, weights=w), np.average(y, weights=w)
    return np.average((x-mx)*(y-my), weights=w)/np.sqrt(np.average((x-mx)**2, weights=w)*np.average((y-my)**2, weights=w))
def frame(role, col):
    if role == 'bat': d = R[R.faced].rename(columns={'striker_id': 'pid'}); d['ball'] = 1
    else: d = R.rename(columns={'bowler_id': 'pid'}); d['ball'] = d.legal.astype(int)
    d['val'] = d[col]; return d
rng = np.random.default_rng(200); ms = R.match_id.unique(); splits = [set(rng.choice(ms, len(ms)//2, replace=False)) for _ in range(200)]
def per_split(role, col, minp):
    g = match_agg(frame(role, col), alpha=1); tot = g.groupby('pid').Pn.sum(); g = g[g.pid.isin(tot[tot >= minp].index)]
    out = []
    for h in splits:
        a = g[g.match_id.isin(h)].groupby('pid')[['wv', 'w']].sum(); b = g[~g.match_id.isin(h)].groupby('pid')[['wv', 'w']].sum()
        j = a.join(b, lsuffix='1', rsuffix='2', how='inner'); j = j[(j.w1 > 0) & (j.w2 > 0)]
        out.append(wcorr(j.wv1/j.w1, j.wv2/j.w2, np.sqrt(j.w1*j.w2)))
    return np.array(out)
OUT = {}
for role, raw, adj, minp in [('bat', 'bat_v', 'bat_v_opp', 100), ('bowl', 'bowl_v', 'bowl_v_opp', 120), ('bowl_full', 'bowl_v', 'bowl_v_full', 120),
                              ('bat_vs_old', 'bat_val_adj', 'bat_v_opp', 100), ('bowl_vs_old', 'bowl_val_adj', 'bowl_v_opp', 120), ('bowl_full_vs_old', 'bowl_val_adj', 'bowl_v_full', 120)]:
    r0 = per_split(role.split('_')[0], raw, minp); r1 = per_split(role.split('_')[0], adj, minp)
    OUT[role] = dict(splits=len(splits), steadier=int((r1 > r0).sum()), mean_raw=float(r0.mean()), mean_adj=float(r1.mean()))
    print(role, OUT[role])
json.dump(OUT, open('outputs/v3/paired_splits.json', 'w'), indent=1)
