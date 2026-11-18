"""Data for the Selector's War Room page: the top 10s under every combination of settings a judge might question.
Each combination is rebuilt from scratch and picked with the same resample rule (200 match resamples; the default
combination uses the final 2,000-resample result). Output holds player names, ratings and shares only, no raw data."""
import pandas as pd, numpy as np, sys, json, itertools, time
sys.path.insert(0, 'scripts'); from lib_pwi import match_agg, ratings, UNIT
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
names = pd.concat([R[['striker_id', 'striker_name']].set_axis(['pid', 'name'], axis=1), R[['bowler_id', 'bowler_name']].set_axis(['pid', 'name'], axis=1)]).drop_duplicates('pid').set_index('pid').name
WEIGHTS = {'eq': 0, 'sqrt': 0.5, 'idx': 1, 'idx2': 2, 'ponly': 'hard'}
RECENCY = {'none': None, 'hl2': 2, 'hl1': 1}
WICKET = {'5': 5, '8': 8, '11': 11}
ADJ = {'on': {'bat': 'bat_v_opp', 'bowl': 'bowl_v_full'}, 'off': {'bat': 'bat_val_adj', 'bowl': 'bowl_val_adj'}}
B = 200; rng = np.random.default_rng(23)
frames = {}
for role in ['bat', 'bowl']:
    d = R[R.faced].rename(columns={'striker_id': 'pid'}) if role == 'bat' else R.rename(columns={'bowler_id': 'pid'})
    d = d.copy(); d['ball'] = 1 if role == 'bat' else d.legal.astype(int)
    d['wk'] = (d.striker_out.astype(int) - d.P_out) if role == 'bat' else (d.bowler_wkt.astype(int) - d.P_bwkt)
    frames[role] = d
def pick(role, wkey, rkey, wic, akey):
    d = frames[role]; sign = -1 if role == 'bat' else 1
    val = d[ADJ[akey][role]] + sign * (WICKET[wic] - 8) * d.wk
    dd = d.assign(val=val)
    minp, im = (100, 4) if role == 'bat' else (120, 6)
    if WEIGHTS[wkey] == 'hard':
        g = match_agg(dd[dd.PI >= 80], alpha=0, recency=RECENCY[rkey])
    else:
        g = match_agg(dd, alpha=WEIGHTS[wkey], recency=RECENCY[rkey])
    a0, pr0 = ratings(g, minp, 10, inn_min=im)
    elig = a0[a0.eligible].index; ms = g.match_id.unique(); cnt = pd.Series(0.0, index=elig)
    for _ in range(B):
        wts = pd.Series(rng.poisson(1.0, len(ms)), index=ms); gb = g.assign(k=g.match_id.map(wts))
        for c in ['wv', 'w', 'Pv', 'Pn', 'Pb', 'Nv', 'Nn', 'Nb']: gb[c] = gb[c] * gb.k
        gb = gb[gb.k > 0]; ab, _ = ratings(gb, 0, 0, inn_min=im, prior=pr0)
        r = ab.reindex(elig).rating.rank(ascending=False); cnt[r[r <= 10].index] += 1
    t = pd.DataFrame({'name': names.reindex(elig).values, 'rating': a0.loc[elig, 'rating'].values * UNIT[role], 'p': (cnt / B).values}, index=elig)
    return t.sort_values('p', ascending=False).head(14)
out = {'final': {}, 'combos': {}}
final = {r: pd.read_csv(f'outputs/v3/selection_{r}_v3.csv', index_col=0).sort_values('p_top10', ascending=False) for r in ['bat', 'bowl']}
for r in ['bat', 'bowl']: out['final'][r] = list(final[r].head(10).name)
t0 = time.time()
for wkey, rkey, wic, akey in itertools.product(WEIGHTS, RECENCY, WICKET, ADJ):
    key = f'{wkey}|{rkey}|{wic}|{akey}'; out['combos'][key] = {}
    for role in ['bat', 'bowl']:
        if key == 'idx|none|8|on':
            t = final[role].head(14).rename(columns={'p_top10': 'p'})[['name', 'rating', 'p']]
        else:
            t = pick(role, wkey, rkey, wic, akey)
        out['combos'][key][role] = [[n, round(float(rt), 2), round(float(p), 3)] for n, rt, p in t[['name', 'rating', 'p']].itertuples(index=False)]
    print(key, f'{time.time() - t0:.0f}s', flush=True)
json.dump(out, open('outputs/v3/warroom.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print('done', len(out['combos']))
