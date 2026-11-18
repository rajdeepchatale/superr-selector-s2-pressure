"""Under each chase-model variant from 26_sens_chase_par.py, rebuild ratings and rerun the 500-resample bootstrap,
then apply the same selection rule as the report (ten most often in the top 10, ordered by rating)."""
import pandas as pd, numpy as np, sys
sys.path.insert(0, 'scripts'); from lib_pwi import role_frame, match_agg, ratings
T = pd.read_pickle('outputs/rated_balls.pkl'); V = pd.read_pickle('outputs/pi_variants.pkl')
names = pd.concat([T[['striker_id', 'striker_name']].set_axis(['pid', 'name'], axis=1), T[['bowler_id', 'bowler_name']].set_axis(['pid', 'name'], axis=1)]).drop_duplicates('pid').set_index('pid').name
FINAL = {'bat': ['Suryakumar Yadav','Abhishek Sharma','Phil Salt','Reeza Hendricks','Heinrich Klaasen','Tim David','Glenn Phillips','Vaibhav Sooryavanshi','Namboori Tilak Varma','Virat Kohli'],
         'bowl': ['Sunil Narine','Jasprit Bumrah','Kuldeep Yadav','Josh Hazlewood','Rashid Khan','Varun Chakravarthy','Matheesha Pathirana','Wanindu Hasaranga','Mujeeb Ur Rahman','Krunal Pandya']}
WATCH = ['Vaibhav Sooryavanshi', 'Namboori Tilak Varma', 'Virat Kohli', 'Nicholas Pooran', 'Rinku Singh', 'Shashank Singh', 'Cameron Green']
for variant, newpi in V.items():
    TT = T.merge(newpi, on=['match_id', 'innings', 'innings_ball_num'], how='left'); TT['PI'] = TT.PI_new
    print(f'\n######## chase model: {variant}')
    for role in ['bat', 'bowl']:
        rng = np.random.default_rng(11)
        d = role_frame(TT, role); minp = 100 if role == 'bat' else 120; im = 4 if role == 'bat' else 6
        g = match_agg(d, alpha=1); a0, pr0 = ratings(g, minp, 10, inn_min=im)
        elig = a0[a0.eligible].index; ms = g.match_id.unique(); cnt = pd.Series(0.0, index=elig)
        for _ in range(500):
            wts = pd.Series(rng.poisson(1.0, len(ms)), index=ms); gb = g.assign(k=g.match_id.map(wts))
            for c in ['wv', 'w', 'Pv', 'Pn', 'Pb', 'Nv', 'Nn', 'Nb']: gb[c] = gb[c] * gb.k
            gb = gb[gb.k > 0]; ab, _ = ratings(gb, 0, 0, inn_min=im, prior=pr0)
            r = ab.reindex(elig).rating.rank(ascending=False); cnt[r[r <= 10].index] += 1
        tab = pd.DataFrame({'name': names.reindex(elig).values, 'rating': a0.loc[elig, 'rating'].values, 'p_top10': (cnt / 500).values}, index=elig)
        pick = tab.sort_values('p_top10', ascending=False).head(10).sort_values('rating', ascending=False)
        F = FINAL[role]; got = list(pick.name)
        print(f'  {role}: {len(set(F) & set(got))}/10 same as final | in: {", ".join(x for x in got if x not in F) or "-"} | out: {", ".join(x for x in F if x not in got) or "-"}')
        print('   picked:', ', '.join(f'{n} ({p:.0%})' for n, p in zip(pick.name, pick.p_top10)))
        if role == 'bat':
            w = tab[tab.name.isin(WATCH)].sort_values('p_top10', ascending=False)
            print('   watch:', ', '.join(f'{n} {r:.1f} / {p:.0%}' for n, r, p in zip(w.name, w.rating, w.p_top10)))
