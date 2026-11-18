"""Shot choice and execution under pressure (uses the data pack's 'stroke' column, filled for 97% of balls).
   Shot risk  = how often that shot (vs pace or spin) gets a batter out, across all balls.
   Choice     = his shot risk minus the average batter's in the same spot (innings, phase, wickets, Pressure Index band, chase rate).
   Execution  = how often he actually gets out minus the risk of the shots he played.
   Tested like the other ideas: split-half on the same 100 splits as 34_behaviour, and 2022-24 -> 2025-26 like 32_eval_variants."""
import pandas as pd, numpy as np, json, sys
sys.path.insert(0, 'scripts'); from lib_pwi import match_agg, ratings
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
rng = np.random.default_rng(21); MS = R.match_id.unique(); SPLITS = [set(rng.choice(MS, len(MS)//2, replace=False)) for _ in range(100)]
def wcorr(x, y, w):
    x, y, w = map(np.asarray, (x, y, w)); mx, my = np.average(x, weights=w), np.average(y, weights=w)
    return np.average((x-mx)*(y-my), weights=w)/np.sqrt(np.average((x-mx)**2, weights=w)*np.average((y-my)**2, weights=w))
def split_half(df, pid, num, den, players):
    df = df[df[pid].isin(players)]; out = []
    for h in SPLITS:
        a = df[df.match_id.isin(h)].groupby(pid)[[num, den]].sum(); b = df[~df.match_id.isin(h)].groupby(pid)[[num, den]].sum()
        j = a.join(b, lsuffix='1', rsuffix='2', how='inner'); j = j[(j[den+'1'] > 0) & (j[den+'2'] > 0)]
        out.append(wcorr(j[num+'1']/j[den+'1'], j[num+'2']/j[den+'2'], np.sqrt(j[den+'1']*j[den+'2'])))
    return float(np.mean(out)), float(np.mean(np.array(out) > 0))
sel_a = pd.read_csv('outputs/v3/selection_bat_v3.csv', index_col=0); sel_b = pd.read_csv('outputs/v3/selection_bowl_v3.csv', index_col=0)
BATTERS, BOWLERS = set(sel_a.index), set(sel_b.index)
OUT = {}
F = R[R.faced & R.stroke.notna() & R.PI.notna()].copy()
F['out'] = F.striker_out.astype(float)
OUT['stroke_fill'] = float(R[R.faced].stroke.notna().mean())
risk = F.groupby(['stroke', 'spin']).out.mean(); F['risk'] = [risk[(s, p)] for s, p in zip(F.stroke, F.spin)]
F['pib'] = pd.cut(F.PI, [-0.1, 20, 40, 60, 80, 85, 90, 95, 100.1], labels=False)
F['wb'] = pd.cut(F.wkts_in_hand, [-1, 3, 6, 10], labels=False)
F['rb'] = np.where(F.inn2 == 1, pd.cut(F.rrr.fillna(0), [-1e9, 8, 10, 12, 1e9], labels=False), -1)
F['risk_exp'] = F.groupby(['inn2', 'phase', 'wb', 'pib', 'rb']).risk.transform('mean')
F['choice'] = F.risk - F.risk_exp; F['exe'] = F.out - F.risk
P = F[F.PI >= 80]; N = F[F.PI < 80]
OUT['league'] = dict(risk_P=float(P.risk.mean()), out_P=float(P.out.mean()), risk_N=float(N.risk.mean()), out_N=float(N.out.mean()))
# split-half: batters on pressure balls (choice, execution); bowlers: the shots batters choose against them
bm = P.groupby(['striker_id', 'match_id']).agg(c=('choice', 'sum'), e=('exe', 'sum'), n=('out', 'size')).reset_index()
OUT['bat_choice_repeat'] = split_half(bm, 'striker_id', 'c', 'n', BATTERS)
OUT['bat_exec_repeat'] = split_half(bm, 'striker_id', 'e', 'n', BATTERS)
wm = P.groupby(['bowler_id', 'match_id']).agg(c=('choice', 'sum'), e=('exe', 'sum'), n=('out', 'size')).reset_index()
OUT['bowl_forced_choice_repeat'] = split_half(wm, 'bowler_id', 'c', 'n', BOWLERS)
OUT['bowl_exec_against_repeat'] = split_half(wm, 'bowler_id', 'e', 'n', BOWLERS)
# results on the same splits, for comparison
rb_ = R[R.faced & (R.PI >= 80)].groupby(['striker_id', 'match_id']).agg(v=('bat_v_opp', 'sum'), n=('bat_v_opp', 'size')).reset_index()
OUT['bat_results_P_repeat'] = split_half(rb_, 'striker_id', 'v', 'n', BATTERS)
# player level, all seasons, and link with the rating
tot = bm[bm.striker_id.isin(BATTERS)].groupby('striker_id')[['c', 'e', 'n']].sum()
tot['choice'] = tot.c/tot.n; tot['exe'] = tot.e/tot.n
tot = tot.join(sel_a[['name', 'rating', 'pick_rank']])
OUT['choice_vs_rating'] = float(wcorr(tot.choice, tot.rating, tot.n)); OUT['exec_vs_rating'] = float(wcorr(tot.exe, tot.rating, tot.n))
# out of time: 2022-24 shot measures -> 2025-26 pressure value (same filters as the rating's own test)
d = R[R.faced].rename(columns={'striker_id': 'pid'}); d['ball'] = 1; d['val'] = d.bat_v_opp
atr, _ = ratings(match_agg(d[d.year <= 2024], alpha=1), 40, 4, inn_min=4)
ate, _ = ratings(match_agg(d[d.year >= 2025], alpha=1), 40, 4, inn_min=4)
j = atr.join(ate, lsuffix='_tr', rsuffix='_te', how='inner'); j = j[(j.Pn_tr >= 60) & (j.Pn_te >= 40)]
tr = P[P.year <= 2024].groupby('striker_id').agg(c=('choice', 'mean'), e=('exe', 'mean'), n=('out', 'size'))
j = j.join(tr, how='inner'); j = j[j.n >= 40]
OUT['oot'] = dict(n=int(len(j)), rating=float(wcorr(j.rating_tr, j.pwi_te, j.w_te)),
                  choice=float(wcorr(j.c, j.pwi_te, j.w_te)), execution=float(wcorr(j.e, j.pwi_te, j.w_te)))
# tables for the deck
def prof(pid):
    x = P[P.striker_id == pid]
    return dict(name=x.striker_name.iloc[0], balls=int(len(x)), out_pct=float(100*x.out.mean()), shot_risk_pct=float(100*x.risk.mean()),
                choice_pp=float(100*x.choice.mean()), exec_pp=float(100*x.exe.mean()))
OUT['top10'] = [prof(p) for p in sel_a.sort_values('pick_rank').index[:10]]
names = R.drop_duplicates('striker_id').set_index('striker_id').striker_name
OUT['kohli_green_pooran'] = {n: prof(int(names[names == n].index[0])) for n in ['Virat Kohli', 'Cameron Green', 'Nicholas Pooran']}
pool = tot.sort_values('choice'); OUT['choice_rank_of_top10'] = {r['name']: int(pool.index.get_loc(i))+1 for i, r in tot[tot.pick_rank <= 10].iterrows()}
OUT['pool_size'] = int(len(tot))
json.dump(OUT, open('outputs/v3/shot_choice.json', 'w'), indent=1)
for k, v in OUT.items():
    if k in ('top10', 'kohli_green_pooran'):
        for r in (v if isinstance(v, list) else v.values()): print(f"  {r['name']:22s} balls {r['balls']:4d} out {r['out_pct']:4.1f}% shot risk {r['shot_risk_pct']:4.1f}% choice {r['choice_pp']:+5.2f} exec {r['exec_pp']:+5.2f}")
    else: print(f'{k:26s}', v)
