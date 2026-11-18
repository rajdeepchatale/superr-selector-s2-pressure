"""v3 Pressure Rating: same engine (PI-weighted value, empirical Bayes, same gates), on upgraded per-ball values:
   batters = adjusted for who they faced; bowlers = adjusted for who they faced + ground, dew and home.
   Selection rule unchanged: the ten players most often in the top 10 across 500 match resamples."""
import pandas as pd, numpy as np, sys, json
sys.path.insert(0,'scripts'); from lib_pwi import match_agg, ratings, UNIT
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
names = pd.concat([R[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), R[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
COL = {'bat': sys.argv[1] if len(sys.argv)>1 else 'bat_v_opp', 'bowl': sys.argv[2] if len(sys.argv)>2 else 'bowl_v_full'}
TAG = sys.argv[3] if len(sys.argv)>3 else 'v3'
B = int(sys.argv[4]) if len(sys.argv)>4 else 500
rng = np.random.default_rng(int(sys.argv[5]) if len(sys.argv)>5 else 11)
OLD = {'bat':['Suryakumar Yadav','Abhishek Sharma','Phil Salt','Reeza Hendricks','Heinrich Klaasen','Tim David','Glenn Phillips','Vaibhav Sooryavanshi','Namboori Tilak Varma','Virat Kohli'],
       'bowl':['Sunil Narine','Jasprit Bumrah','Kuldeep Yadav','Josh Hazlewood','Rashid Khan','Varun Chakravarthy','Matheesha Pathirana','Wanindu Hasaranga','Mujeeb Ur Rahman','Krunal Pandya']}
res = {}
for role in ['bat','bowl']:
    if role=='bat': d = R[R.faced].rename(columns={'striker_id':'pid'}); d['ball']=1
    else: d = R.rename(columns={'bowler_id':'pid'}); d['ball']=d.legal.astype(int)
    d['val'] = d[COL[role]]
    minp = 100 if role=='bat' else 120; im = 4 if role=='bat' else 6; u = UNIT[role]
    g = match_agg(d, alpha=1); a0, pr0 = ratings(g, minp, 10, inn_min=im)
    elig = a0[a0.eligible].index; ms = g.match_id.unique(); cnt = pd.Series(0.0, index=elig); ranks = {p:[] for p in elig}
    for bi in range(B):
        wts = pd.Series(rng.poisson(1.0, len(ms)), index=ms); gb = g.assign(k=g.match_id.map(wts))
        for c in ['wv','w','Pv','Pn','Pb','Nv','Nn','Nb']: gb[c] = gb[c]*gb.k
        gb = gb[gb.k>0]; ab,_ = ratings(gb, 0, 0, inn_min=im, prior=pr0)
        r = ab.reindex(elig).rating.rank(ascending=False); cnt[r[r<=10].index] += 1
        for p in elig: ranks[p].append(r.get(p, np.nan))
    tab = pd.DataFrame({'name':names.reindex(elig).values, 'rating':a0.loc[elig,'rating'].values*u, 'se':a0.loc[elig,'rating_se'].values*u, 'Pn':a0.loc[elig,'Pn'].values,
                        'p_top10':(cnt/B).values, 'rank_p10':[np.nanpercentile(ranks[p],10) for p in elig], 'rank_p90':[np.nanpercentile(ranks[p],90) for p in elig]}, index=elig)
    tab['rating_rank'] = tab.rating.rank(ascending=False).astype(int)
    tab = tab.sort_values('p_top10', ascending=False); tab['pick_rank'] = range(1, len(tab)+1)
    tab.to_csv(f'outputs/v3/selection_{role}_{TAG}.csv')
    top = list(tab.name.head(10)); res[role] = top
    print(f'\n===== {role.upper()} ({COL[role]}): {len(elig)} eligible | tau {np.sqrt(pr0["tau2"])*u:.2f}')
    print(tab.head(14)[['name','rating','rating_rank','p_top10','rank_p10','rank_p90','Pn']].round(2).to_string(index=False))
    print('  OUT vs current list:', [n for n in OLD[role] if n not in top], '| IN:', [n for n in top if n not in OLD[role]])
json.dump(res, open(f'outputs/v3/lists_{TAG}.json','w'), indent=1)
