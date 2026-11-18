import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_pwi import *
pd.set_option('display.width',250)
T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
rng = np.random.default_rng(11)
res = {}
for role in ['bat','bowl']:
    d = role_frame(T, role); minp = 100 if role=='bat' else 120; im = 4 if role=='bat' else 6
    tops = {}
    for alpha in [0, 0.5, 1, 2, 3, 'hard']:
        if alpha=='hard':
            g = match_agg(d, alpha=1); g = g.assign(wv=g.Pv, w=g.Pn)   # pressure balls only
        else:
            g = match_agg(d, alpha=alpha)
        a, pr = ratings(g, minp, 10, inn_min=im)
        tops[alpha] = list(a[a.eligible].sort_values('rating', ascending=False).head(10).index)
    base = set(tops[1])
    print(f'\n===== {role.upper()} top-10 by pressure emphasis (overlap with alpha=1 default):')
    for k,v in tops.items(): print(f'  alpha={str(k):4s} overlap {len(base & set(v))}/10 : ' + ', '.join(names[p] for p in v))
    # bootstrap (resample matches) for alpha=1 and alpha=2
    for alpha in [1, 2]:
        g = match_agg(d, alpha=alpha); a0, pr0 = ratings(g, minp, 10, inn_min=im)
        elig = a0[a0.eligible].index; ms = g.match_id.unique(); cnt = pd.Series(0, index=elig, dtype=float); ranks = {p:[] for p in elig}
        B = 500
        for bi in range(B):
            wts = pd.Series(rng.poisson(1.0, len(ms)), index=ms)
            gb = g.assign(k=g.match_id.map(wts))
            for c in ['wv','w','Pv','Pn','Pb','Nv','Nn','Nb']: gb[c] = gb[c]*gb.k
            gb = gb[gb.k>0]
            ab, _ = ratings(gb, 0, 0, inn_min=im, prior=pr0)      # keep the same eligible set and prior
            r = ab.reindex(elig).rating.rank(ascending=False)
            top = r[r<=10].index; cnt[top] += 1
            for p in elig: ranks[p].append(r.get(p, np.nan))
        tab = pd.DataFrame({'name':names.reindex(elig).values, 'rating':a0.loc[elig,'rating'].values*UNIT[role], 'p_top10':(cnt/B).values,
                            'rank_med':[np.nanmedian(ranks[p]) for p in elig], 'rank_p10':[np.nanpercentile(ranks[p],10) for p in elig], 'rank_p90':[np.nanpercentile(ranks[p],90) for p in elig]}, index=elig)
        tab = tab.sort_values('rating', ascending=False)
        tab.to_csv(f'outputs/bootstrap_{role}_a{alpha}.csv')
        print(f'\n  bootstrap alpha={alpha}: top 20 with P(top-10) and 80% rank range')
        print(tab.head(20).round(2).to_string())
