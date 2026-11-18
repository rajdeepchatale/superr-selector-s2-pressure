"""Out-of-fold accuracy of the win-probability models (same setup as 04_wp_model.py), for the report."""
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, brier_score_loss
b = pd.read_pickle('outputs/balls.pkl'); U = b[b.usable].copy()
F1 = ['score_before','balls_left','wkts_before','par']; M1 = [1, 1, -1, -1]
F2 = ['runs_needed','balls_left','wkts_in_hand','par']; M2 = [-1, 1, 1, 1]
def expand(df):
    t = df[df.bat_team_won==0.5]; n = df[df.bat_team_won!=0.5]
    return pd.concat([n.assign(y=n.bat_team_won.astype(int), w=1.0), t.assign(y=1, w=0.5), t.assign(y=0, w=0.5)])
HP = {1: dict(max_iter=200, max_leaf_nodes=15, min_samples_leaf=1000), 2: dict(max_iter=300, max_leaf_nodes=31, min_samples_leaf=200)}
def model(mono, inn): return HistGradientBoostingClassifier(learning_rate=0.05, l2_regularization=1.0, monotonic_cst=mono, random_state=0, **HP[inn])
for inn, F, M in [(1,F1,M1),(2,F2,M2)]:
    d = expand(U[U.innings==inn]); oof = np.zeros(len(d))
    for tr, te in GroupKFold(n_splits=5).split(d, d.y, d.match_id):
        oof[te] = model(M, inn).fit(d.iloc[tr][F], d.iloc[tr].y, sample_weight=d.iloc[tr].w).predict_proba(d.iloc[te][F])[:,1]
    base = np.average(d.y, weights=d.w)
    print(f'inn{inn}: AUC {roc_auc_score(d.y,oof,sample_weight=d.w):.3f} Brier {brier_score_loss(d.y,oof,sample_weight=d.w):.3f} (coin-flip baseline {brier_score_loss(d.y,np.full(len(d),base),sample_weight=d.w):.3f}) n={len(d)} matches={d.match_id.nunique()}')
    c = pd.DataFrame({'p':oof,'y':d.y,'w':d.w}); c['bin']=pd.cut(c.p,[0,.2,.4,.6,.8,1])
    print(c.groupby('bin',observed=True).apply(lambda x: pd.Series({'pred':np.average(x.p,weights=x.w),'actual':np.average(x.y,weights=x.w)})).round(3).T.to_string())
