import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_pwi import *
T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
def wcorr(x,y,w):
    m=~(np.isnan(x)|np.isnan(y)); x,y,w=x[m],y[m],w[m]; mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def top10(d, role, **kw):
    minp = kw.pop('minp', 100 if role=='bat' else 120); im = 4 if role=='bat' else 6
    g = match_agg(d, **kw); a,_ = ratings(g, minp, 10, inn_min=im)
    return a[a.eligible].sort_values('rating', ascending=False)
base = {}
for role in ['bat','bowl']:
    d = role_frame(T, role); b = top10(d, role, alpha=1); base[role] = set(b.head(10).index)
    print(f'\n===== {role.upper()} sensitivity (top-10 overlap with final method)')
    tests = {}
    tests['recency half-life 2 yrs'] = top10(d, role, alpha=1, recency=2)
    tests['pressure line at 75 (eligibility)'] = top10(d, role, alpha=1, th=75)
    tests['pressure line at 85 (eligibility)'] = top10(d, role, alpha=1, th=85)
    tests['stricter sample (150/180 balls)'] = top10(d, role, alpha=1, minp=150 if role=='bat' else 180)
    dn = d.copy(); dn['val'] = dn.bat_v if role=='bat' else dn.bowl_v
    tests['no opponent adjustment'] = top10(dn, role, alpha=1)
    dw = d.copy()
    if role=='bat': dw['val'] = (dw.bat_runs-dw.E_bat_runs) - 11*(dw.striker_out.astype(int)-dw.P_out) - dw.adj_b
    else: dw['val'] = (dw.E_bowl_runs-dw.bowler_runs) + 11*(dw.bowler_wkt.astype(int)-dw.P_bwkt) - dw.adj_w
    tests['wicket = 11 runs (instead of 8)'] = top10(dw, role, alpha=1)
    for k,v in tests.items():
        t = list(v.head(10).index); print(f'  {k:36s}: {len(base[role]&set(t))}/10 same | new in: {", ".join(names[p] for p in t if p not in base[role]) or "-"}')
    # IPL-only vs T20I-only evidence (raw, smaller samples so lower min)
    for cg in ['IPL','T20I_FULL']:
        t = top10(d[d.comp_group==cg], role, alpha=1, minp=50 if role=='bat' else 60)
        print(f'  {cg+" only":36s}: {len(base[role]&set(t.head(10).index))}/10 same')
    # OUT-OF-TIME: does 2022-24 rating predict 2025-26 pressure performance?
    gtr = match_agg(d[d.year<=2024], alpha=1); gte = match_agg(d[d.year>=2025], alpha=1)
    atr,_ = ratings(gtr, 40 if role=='bat' else 50, 4, inn_min=4); ate,_ = ratings(gte, 40 if role=='bat' else 50, 4, inn_min=4)
    j = atr.join(ate, lsuffix='_tr', rsuffix='_te', how='inner'); j = j[(j.Pn_tr>=60)&(j.Pn_te>=40)]
    w = j.w_te.values
    print(f'  OUT-OF-TIME ({len(j)} players): 2022-24 PWI rating -> 2025-26 PWI: corr {wcorr(j.rating_tr.values, j.pwi_te.values, w):+.3f} | -> 2025-26 pressure-only value: {wcorr(j.rating_tr.values, j.xP_te.values, j.Pn_te.values.astype(float)):+.3f}')
    print(f'                         2022-24 pressure-only value -> 2025-26 pressure-only value: {wcorr(j.xP_tr.values, j.xP_te.values, j.Pn_te.values.astype(float)):+.3f}')
