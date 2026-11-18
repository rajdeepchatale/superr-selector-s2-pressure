"""Win-probability models (both innings) + Leverage Index = how much the next ball can move the result."""
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
b = pd.read_pickle('outputs/balls.pkl')
U = b[b.usable].copy()

F1 = ['score_before','balls_left','wkts_before','par']; M1 = [1, 1, -1, -1]
F2 = ['runs_needed','balls_left','wkts_in_hand','par']; M2 = [-1, 1, 1, 1]
def expand(df):  # ties -> two rows weighted 0.5
    t = df[df.bat_team_won==0.5]; n = df[df.bat_team_won!=0.5]
    out = pd.concat([n.assign(y=n.bat_team_won.astype(int), w=1.0), t.assign(y=1, w=0.5), t.assign(y=0, w=0.5)])
    return out
HP = {1: dict(max_iter=200, max_leaf_nodes=15, min_samples_leaf=1000), 2: dict(max_iter=300, max_leaf_nodes=31, min_samples_leaf=200)}
def model(mono, inn): return HistGradientBoostingClassifier(learning_rate=0.05, l2_regularization=1.0, monotonic_cst=mono, random_state=0, **HP[inn])
from sklearn.linear_model import LogisticRegression
def logit(p): p=np.clip(p,1e-4,1-1e-4); return np.log(p/(1-p))
CAL = {}

models = {}
for inn, F, M in [(1,F1,M1),(2,F2,M2)]:
    d = expand(U[U.innings==inn])
    oof = np.zeros(len(d)); gkf = GroupKFold(n_splits=5)
    for tr, te in gkf.split(d, d.y, d.match_id):
        mdl = model(M, inn).fit(d.iloc[tr][F], d.iloc[tr].y, sample_weight=d.iloc[tr].w)
        oof[te] = mdl.predict_proba(d.iloc[te][F])[:,1]
    print(f'Innings {inn} WP model (5-fold, grouped by match): AUC={roc_auc_score(d.y,oof,sample_weight=d.w):.3f}  Brier={brier_score_loss(d.y,oof,sample_weight=d.w):.3f}  LogLoss={log_loss(d.y,oof,sample_weight=d.w):.3f}')
    cal = pd.DataFrame({'p':oof,'y':d.y,'w':d.w}); cal['bin']=pd.cut(cal.p, np.linspace(0,1,11))
    print(cal.groupby('bin',observed=True).apply(lambda x: pd.Series({'pred':np.average(x.p,weights=x.w),'actual':np.average(x.y,weights=x.w),'n':len(x)})).round(3).to_string())
    CAL[inn] = LogisticRegression().fit(logit(oof).reshape(-1,1), d.y, sample_weight=d.w)
    pc = CAL[inn].predict_proba(logit(oof).reshape(-1,1))[:,1]
    print(f'  after Platt calibration: Brier={brier_score_loss(d.y,pc,sample_weight=d.w):.4f}  slope={CAL[inn].coef_[0][0]:.3f}')
    cal['pc']=pc; print(cal.groupby('bin',observed=True).apply(lambda x: pd.Series({'pred_cal':np.average(x.pc,weights=x.w),'actual':np.average(x.y,weights=x.w)})).round(3).T.to_string())
    models[inn] = model(M, inn).fit(d[F], d.y, sample_weight=d.w)

def cal1(p): return CAL[1].predict_proba(logit(p).reshape(-1,1))[:,1]
def cal2(p): return CAL[2].predict_proba(logit(p).reshape(-1,1))[:,1]
def wp1(score, balls_left, wkts, par):
    """WP of batting-first side. Terminal states bridged through the chase model."""
    score, balls_left, wkts, par = map(np.asarray, (score, balls_left, wkts, par))
    out = np.empty(len(score), dtype=float)
    term = (balls_left<=0) | (wkts>=10)
    if (~term).any():
        out[~term] = cal1(models[1].predict_proba(pd.DataFrame({'score_before':score[~term],'balls_left':balls_left[~term],'wkts_before':wkts[~term],'par':par[~term]}))[:,1])
    if term.any():
        out[term] = 1 - cal2(models[2].predict_proba(pd.DataFrame({'runs_needed':score[term]+1,'balls_left':np.full(term.sum(),120),'wkts_in_hand':np.full(term.sum(),10),'par':par[term]}))[:,1])
    return out
def wp2(need, balls_left, wih, par):
    need, balls_left, wih, par = map(np.asarray, (need, balls_left, wih, par))
    out = np.empty(len(need), dtype=float)
    won = need<=0; lost = (~won) & ((wih<=0)|(balls_left<=0))
    tie = lost & (need==1) & (balls_left<=0)
    live = ~(won|lost)
    out[won]=1.0; out[lost]=0.0; out[tie]=0.5
    if live.any():
        out[live] = cal2(models[2].predict_proba(pd.DataFrame({'runs_needed':need[live],'balls_left':balls_left[live],'wkts_in_hand':wih[live],'par':par[live]}))[:,1])
    return out
def wp_state(inn, score, balls_left, wkts, par, target):
    return np.where(inn==1, wp1(score, balls_left, wkts, par), wp2(target-score, balls_left, 10-wkts, par)) if False else None

# WP before each ball and after the actual ball (batting side perspective)
A = b.copy()
A['wp_before'] = np.nan; A['wp_after'] = np.nan
for inn in [1,2]:
    s = A.innings==inn
    sc, bl, wk, pr = A.loc[s,'score_before'].values, A.loc[s,'balls_left'].values, A.loc[s,'wkts_before'].values, A.loc[s,'par'].values
    sc2 = sc + A.loc[s,'total_runs'].values; bl2 = bl - A.loc[s,'legal'].astype(int).values; wk2 = wk + A.loc[s,'is_wicket'].astype(int).values
    if inn==1:
        A.loc[s,'wp_before'] = wp1(sc,bl,wk,pr); A.loc[s,'wp_after'] = wp1(sc2,bl2,wk2,pr)
    else:
        tg = A.loc[s,'target'].values
        A.loc[s,'wp_before'] = wp2(tg-sc,bl,10-wk,pr); A.loc[s,'wp_after'] = wp2(tg-sc2,bl2,10-wk2,pr)
A['wpa'] = A.wp_after - A.wp_before

# outcome distribution by context, then expected |WP swing| = leverage
A['ob'] = pd.cut(A.over_no,[0,6,10,15,18,20],labels=False); A['wb']=pd.cut(A.wkts_before,[-1,1,3,5,7,9],labels=False)
def outcome(r):
    if r.is_wide: return 'WD'
    if r.is_wicket and r.legal: return 'W'
    if not r.legal: return 'NB'
    return {0:'0',1:'1',2:'2',3:'3',4:'4',5:'4',6:'6'}.get(int(r.total_runs), '1')
Uo = A[A.usable].copy()
Uo['oc'] = [outcome(r) for r in Uo[['is_wide','is_wicket','legal','total_runs']].itertuples(index=False)]
P = pd.crosstab([Uo.innings,Uo.ob,Uo.wb], Uo.oc, normalize='index')
OUT = {'0':(0,1,0),'1':(1,1,0),'2':(2,1,0),'3':(3,1,0),'4':(4,1,0),'6':(6,1,0),'W':(0,1,1),'WD':(1,0,0),'NB':(2,0,0)}
A['lev_raw'] = 0.0
for inn in [1,2]:
    s = (A.innings==inn).values
    sub = A.loc[s]
    probs = P.loc[inn].reindex(pd.MultiIndex.from_arrays([sub.ob.values, sub.wb.values])).fillna(0).values
    cols = list(P.columns)
    sc, bl, wk, pr = sub.score_before.values, sub.balls_left.values, sub.wkts_before.values, sub.par.values
    base = sub.wp_before.values; lev = np.zeros(s.sum())
    for j,c in enumerate(cols):
        r, lg, w = OUT[c]
        if inn==1: wp_o = wp1(sc+r, bl-lg, wk+w, pr)
        else: wp_o = wp2(sub.target.values-(sc+r), bl-lg, 10-(wk+w), pr)
        lev += probs[:,j]*np.abs(wp_o-base)
    A.loc[s,'lev_raw'] = lev
mean_lev = A.loc[A.usable,'lev_raw'].mean()
A['LI'] = A.lev_raw/mean_lev
A['PI'] = A.LI.rank(pct=True)*100   # Pressure Index: percentile of leverage, 0-100
A.loc[~A.usable, ['LI','PI']] = np.nan
A['PI'] = A.loc[A.usable,'LI'].rank(pct=True)*100
print('\nLeverage summary (usable):', A.loc[A.usable,'LI'].describe().round(3).to_dict())
print('Share of top-25% pressure balls by innings:', A[A.usable & (A.PI>=75)].innings.value_counts(normalize=True).round(3).to_dict())
print('Mean PI by innings x phase:'); print(A[A.usable].groupby(['innings','phase'],observed=True).PI.mean().round(1).unstack())
A.to_pickle('outputs/balls_wp.pkl')
import pickle; pickle.dump({'models':models,'CAL':CAL,'P':P,'mean_lev':mean_lev}, open('outputs/wp_models.pkl','wb'))
