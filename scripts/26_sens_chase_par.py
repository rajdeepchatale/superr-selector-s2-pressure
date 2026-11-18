"""Sensitivity: does the season scoring level (par) in the chase win-chance model drive the rankings?
The chase model jumps for IPL 2026 (par 195.8, the highest season in the data): e.g. 28 off 12 with 4 wickets
goes from 26% (par 192) to 50%. Refit the chase model (a) without par and (b) with par capped at 192.3,
rebuild the Pressure Index, rerun the ratings, and compare the top 10s with the final lists."""
import pandas as pd, numpy as np, pickle, sys
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
sys.path.insert(0, 'scripts'); from lib_pwi import role_frame, match_agg, ratings

b = pd.read_pickle('outputs/balls.pkl'); U = b[b.usable].copy()
CAP = float(b[(b.comp_group=='IPL') & (b.year==2025)].par.iloc[0])   # treat IPL 2026 like IPL 2025, the next-highest scoring season
OLD = pickle.load(open('outputs/wp_models.pkl', 'rb')); P = OLD['P']
def logit(p): p = np.clip(p, 1e-4, 1 - 1e-4); return np.log(p / (1 - p))
def expand(df):
    t = df[df.bat_team_won == 0.5]; n = df[df.bat_team_won != 0.5]
    return pd.concat([n.assign(y=n.bat_team_won.astype(int), w=1.0), t.assign(y=1, w=0.5), t.assign(y=0, w=0.5)])
HP2 = dict(max_iter=300, max_leaf_nodes=31, min_samples_leaf=200)

FINAL = {'bat': ['Suryakumar Yadav','Abhishek Sharma','Phil Salt','Reeza Hendricks','Heinrich Klaasen','Tim David','Glenn Phillips','Vaibhav Sooryavanshi','Namboori Tilak Varma','Virat Kohli'],
         'bowl': ['Sunil Narine','Jasprit Bumrah','Kuldeep Yadav','Josh Hazlewood','Rashid Khan','Varun Chakravarthy','Matheesha Pathirana','Wanindu Hasaranga','Mujeeb Ur Rahman','Krunal Pandya']}

def run(variant):
    A = b.copy()
    if variant == 'cap': A['par2'] = A.par.clip(upper=CAP)
    F2 = ['runs_needed', 'balls_left', 'wkts_in_hand'] + (['par2'] if variant == 'cap' else []); M2 = [-1, 1, 1] + ([1] if variant == 'cap' else [])
    d = expand(A[A.usable & (A.innings == 2)])
    mk = lambda: HistGradientBoostingClassifier(learning_rate=0.05, l2_regularization=1.0, monotonic_cst=M2, random_state=0, **HP2)
    oof = np.zeros(len(d))
    for tr, te in GroupKFold(n_splits=5).split(d, d.y, d.match_id):
        oof[te] = mk().fit(d.iloc[tr][F2], d.iloc[tr].y, sample_weight=d.iloc[tr].w).predict_proba(d.iloc[te][F2])[:, 1]
    cal2m = LogisticRegression().fit(logit(oof).reshape(-1, 1), d.y, sample_weight=d.w)
    m2 = mk().fit(d[F2], d.y, sample_weight=d.w)
    def cal2(p): return cal2m.predict_proba(logit(p).reshape(-1, 1))[:, 1]
    def frame2(need, bl, wih, par):
        f = pd.DataFrame({'runs_needed': need, 'balls_left': bl, 'wkts_in_hand': wih})
        if variant == 'cap': f['par2'] = np.minimum(par, CAP)
        return f
    def wp1(score, bl, wk, par):
        score, bl, wk, par = map(np.asarray, (score, bl, wk, par)); out = np.empty(len(score))
        term = (bl <= 0) | (wk >= 10)
        if (~term).any():
            p = OLD['models'][1].predict_proba(pd.DataFrame({'score_before': score[~term], 'balls_left': bl[~term], 'wkts_before': wk[~term], 'par': par[~term]}))[:, 1]
            out[~term] = OLD['CAL'][1].predict_proba(logit(p).reshape(-1, 1))[:, 1]
        if term.any():
            out[term] = 1 - cal2(m2.predict_proba(frame2(score[term] + 1, np.full(term.sum(), 120), np.full(term.sum(), 10), par[term]))[:, 1])
        return out
    def wp2(need, bl, wih, par):
        need, bl, wih, par = map(np.asarray, (need, bl, wih, par)); out = np.empty(len(need))
        won = need <= 0; lost = (~won) & ((wih <= 0) | (bl <= 0)); tie = lost & (need == 1) & (bl <= 0); live = ~(won | lost)
        out[won] = 1.0; out[lost] = 0.0; out[tie] = 0.5
        if live.any(): out[live] = cal2(m2.predict_proba(frame2(need[live], bl[live], wih[live], par[live]))[:, 1])
        return out
    A['wp_before'] = np.nan
    for inn in [1, 2]:
        s = A.innings == inn
        sc, bl, wk, pr = A.loc[s, 'score_before'].values, A.loc[s, 'balls_left'].values, A.loc[s, 'wkts_before'].values, A.loc[s, 'par'].values
        A.loc[s, 'wp_before'] = wp1(sc, bl, wk, pr) if inn == 1 else wp2(A.loc[s, 'target'].values - sc, bl, 10 - wk, pr)
    A['ob'] = pd.cut(A.over_no, [0, 6, 10, 15, 18, 20], labels=False); A['wb'] = pd.cut(A.wkts_before, [-1, 1, 3, 5, 7, 9], labels=False)
    OUT = {'0': (0, 1, 0), '1': (1, 1, 0), '2': (2, 1, 0), '3': (3, 1, 0), '4': (4, 1, 0), '6': (6, 1, 0), 'W': (0, 1, 1), 'WD': (1, 0, 0), 'NB': (2, 0, 0)}
    A['lev'] = 0.0
    for inn in [1, 2]:
        s = (A.innings == inn).values; sub = A.loc[s]
        probs = P.loc[inn].reindex(pd.MultiIndex.from_arrays([sub.ob.values, sub.wb.values])).fillna(0).values
        sc, bl, wk, pr = sub.score_before.values, sub.balls_left.values, sub.wkts_before.values, sub.par.values
        base = sub.wp_before.values; lev = np.zeros(s.sum())
        for j, c in enumerate(P.columns):
            r, lg, w = OUT[c]
            wp_o = wp1(sc + r, bl - lg, wk + w, pr) if inn == 1 else wp2(sub.target.values - (sc + r), bl - lg, 10 - (wk + w), pr)
            lev += probs[:, j] * np.abs(wp_o - base)
        A.loc[s, 'lev'] = lev
    A['PI_new'] = np.nan; A.loc[A.usable, 'PI_new'] = A.loc[A.usable, 'lev'].rank(pct=True) * 100
    chk = wp2(np.array([28, 8, 12]), np.array([12, 4, 5]), np.array([4, 3, 3]), np.array([195.8] * 3))
    return A[['match_id', 'innings', 'innings_ball_num', 'PI_new']], chk

T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id', 'striker_name']].set_axis(['pid', 'name'], axis=1), T[['bowler_id', 'bowler_name']].set_axis(['pid', 'name'], axis=1)]).drop_duplicates('pid').set_index('pid').name
SAVE = {}
for variant in ['nopar', 'cap']:
    newpi, chk = run(variant); SAVE[variant] = newpi
    TT = T.merge(newpi, on=['match_id', 'innings', 'innings_ball_num'], how='left')
    assert TT.PI_new.notna().all() and len(TT) == len(T)
    corr = np.corrcoef(TT.PI, TT.PI_new)[0, 1]; agree = ((TT.PI >= 80) == (TT.PI_new >= 80)).mean()
    TT['PI'] = TT.PI_new
    print(f'\n=== chase model {variant}: IPL 2026 example win chances (28 off 12 4w, 8 off 4 3w, 12 off 5 3w) = {np.round(chk, 2)}')
    print(f'    Pressure Index vs original: corr {corr:.3f}; same pressure/non-pressure call on {agree:.1%} of balls')
    for role in ['bat', 'bowl']:
        d = role_frame(TT, role); minp = 100 if role == 'bat' else 120; im = 4 if role == 'bat' else 6
        a, _ = ratings(match_agg(d, alpha=1), minp, 10, inn_min=im)
        top = [names[p] for p in a[a.eligible].sort_values('rating', ascending=False).head(12).index]
        F = FINAL[role]
        print(f'    {role}: {len(set(F) & set(top[:10]))}/10 same as final | in: {", ".join(x for x in top[:10] if x not in F) or "-"} | out: {", ".join(x for x in F if x not in top[:10]) or "-"} | 11-12: {", ".join(top[10:12])}')
        if role == 'bat':
            rk = {n: i + 1 for i, n in enumerate([names[p] for p in a[a.eligible].sort_values('rating', ascending=False).index])}
            print(f'    Kohli rank {rk.get("Virat Kohli")}, Pooran rank {rk.get("Nicholas Pooran")}')

pd.to_pickle(SAVE, 'outputs/pi_variants.pkl'); print('saved PI variants; cap =', CAP)
