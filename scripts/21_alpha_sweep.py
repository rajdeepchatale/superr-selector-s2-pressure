import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_pwi import *
T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
for role in ['bat','bowl']:
    d = role_frame(T, role); minp = 100 if role=='bat' else 120; im = 4 if role=='bat' else 6
    tops = {}
    for alpha in [0, 0.5, 1, 2, 3, 'hard']:
        if alpha=='hard':
            g = match_agg(d, alpha=1); g = g.assign(wv=g.Pv, w=g.Pn)
        else:
            g = match_agg(d, alpha=alpha)
        a, pr = ratings(g, minp, 10, inn_min=im)
        tops[alpha] = list(a[a.eligible].sort_values('rating', ascending=False).head(10).index)
    base = set(tops[1])
    print(f'\n===== {role.upper()} top-10 by pressure emphasis (overlap with alpha=1 default):')
    for k,v in tops.items(): print(f'  alpha={str(k):4s} overlap {len(base & set(v))}/10 : ' + ', '.join(names[p] for p in v))
