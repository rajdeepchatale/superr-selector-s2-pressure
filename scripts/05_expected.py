"""Context models: what does an AVERAGE batter/bowler produce in this exact situation?
   + resource model: how many runs a wicket costs at this moment. Cross-fitted by match (no leakage)."""
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, mean_absolute_error, r2_score
A = pd.read_pickle('outputs/balls_wp.pkl')
U = A[A.usable].copy()
U['cg'] = U.comp_group.map({'IPL':0,'T20I_FULL':1,'T20I_ASSOC':2,'A_TEAM':3})
U['spin'] = (U.pace_or_spin=='Spin').astype(int)
U['inn2'] = (U.innings==2).astype(int)
U['rn'] = U.runs_needed.fillna(-1); U['rr'] = U.rrr.fillna(-1)
CTX = ['inn2','balls_left','wkts_before','score_before','rn','rr','par','cg','year','spin']
CAT = [False,False,False,False,False,False,False,True,False,False]

# ---- resource model: expected runs still to come in the innings (1st innings, complete innings)
fi = U[U.innings==1].copy()
fi['inn_total'] = fi.groupby('match_id').total_runs.transform('sum')
fi['remaining'] = fi.inn_total - fi.score_before
RF = ['balls_left','wkts_before','par']
res = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=300, monotonic_cst=[1,-1,1], random_state=0).fit(fi[RF], fi.remaining)
print('resource model R2 (in-sample):', round(r2_score(fi.remaining, res.predict(fi[RF])),3))
def R(bl, wk, par):
    bl=np.asarray(bl); wk=np.asarray(wk); out=np.zeros(len(bl))
    ok=(bl>0)&(wk<10)
    out[ok]=res.predict(pd.DataFrame({'balls_left':bl[ok],'wkts_before':wk[ok],'par':np.asarray(par)[ok]}))
    return out
bl_after = U.balls_left.values - 1
U['wkt_cost'] = R(bl_after, U.wkts_before.values, U.par.values) - R(bl_after, U.wkts_before.values+1, U.par.values)
U.loc[U.wkts_before>=9, 'wkt_cost'] = R(bl_after[U.wkts_before.values>=9], np.full((U.wkts_before>=9).sum(),9), U.par.values[U.wkts_before.values>=9])
print('wicket cost (runs) by phase/wkts:'); print(U.groupby([U.phase, pd.cut(U.wkts_before,[-1,2,5,9])],observed=True).wkt_cost.mean().round(1).unstack())

# ---- cross-fitted context models
def cross_fit(df, y, kind, feats, w=None):
    oof = np.zeros(len(df)); gkf = GroupKFold(n_splits=5)
    for tr, te in gkf.split(df, y, df.match_id):
        if kind=='reg':
            m = HistGradientBoostingRegressor(loss='poisson', max_iter=300, learning_rate=0.05, min_samples_leaf=300, categorical_features=CAT, random_state=0)
            m.fit(df.iloc[tr][feats], y.iloc[tr]); oof[te] = m.predict(df.iloc[te][feats])
        else:
            m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, min_samples_leaf=300, categorical_features=CAT, random_state=0)
            m.fit(df.iloc[tr][feats], y.iloc[tr]); oof[te] = m.predict_proba(df.iloc[te][feats])[:,1]
    return oof
fb = U[U.faced].copy()                       # batter's balls (no wides)
fb['E_bat_runs'] = cross_fit(fb, fb.bat_runs, 'reg', CTX)
fb['P_out'] = cross_fit(fb, fb.striker_out.astype(int), 'clf', CTX)
print('\nbatter models: runs MAE', round(mean_absolute_error(fb.bat_runs, fb.E_bat_runs),3), '| calib: mean actual', round(fb.bat_runs.mean(),4), 'mean pred', round(fb.E_bat_runs.mean(),4),
      '| out AUC', round(roc_auc_score(fb.striker_out, fb.P_out),3), 'actual', round(fb.striker_out.mean(),4), 'pred', round(fb.P_out.mean(),4))
U['E_bowl_runs'] = cross_fit(U, U.bowler_runs, 'reg', CTX)
U['P_bwkt'] = cross_fit(U, U.bowler_wkt.astype(int), 'clf', CTX)
print('bowler models: actual runs/delivery', round(U.bowler_runs.mean(),4), 'pred', round(U.E_bowl_runs.mean(),4), '| wkt AUC', round(roc_auc_score(U.bowler_wkt, U.P_bwkt),3), 'actual', round(U.bowler_wkt.mean(),4), 'pred', round(U.P_bwkt.mean(),4))
U = U.merge(fb[['match_id','innings','innings_ball_num','E_bat_runs','P_out']], on=['match_id','innings','innings_ball_num'], how='left')

# ---- per-ball value above expected (runs)
U['bat_val'] = np.where(U.faced, (U.bat_runs - U.E_bat_runs) - U.wkt_cost*(U.striker_out.astype(int) - U.P_out), np.nan)
U['bowl_val'] = (U.E_bowl_runs - U.bowler_runs) + U.wkt_cost*(U.bowler_wkt.astype(int) - U.P_bwkt)
print('\nmean bat_val (should be ~0):', round(U.bat_val.mean(),4), '| mean bowl_val:', round(U.bowl_val.mean(),4))
print('mean value by pressure band (bat / bowl):')
U['band'] = pd.cut(U.PI,[0,50,80,90,100],labels=['0-50','50-80','80-90','90-100'])
print(U.groupby('band',observed=True)[['bat_val','bowl_val']].mean().round(4))
U.to_pickle('outputs/balls_val.pkl')
import pickle; pickle.dump(res, open('outputs/resource_model.pkl','wb'))
