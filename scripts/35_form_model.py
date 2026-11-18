"""Form, done properly: each player's true level can drift from year to year (a random walk), and each season's number
   is that level plus noise. The data picks how much the level drifts (maximum likelihood across all players).
   Output: how much weight the latest season deserves, each player's current level and trend, and an out-of-time check."""
import pandas as pd, numpy as np, sys, json
sys.path.insert(0,'scripts'); from lib_pwi import match_agg, ratings, UNIT
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
COL = {'bat':'bat_v_opp','bowl':'bowl_v_full'}; YRS = [2022,2023,2024,2025,2026]
def wcorr(x,y,w):
    x,y,w=map(np.asarray,(x,y,w)); mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def player_years(d):
    d = d.assign(w=d.PI/100); d['wv']=d.w*d.val; d['w2']=d.w**2
    s2 = d.val.var()
    m = d.groupby(['pid','year','match_id']).agg(wv=('wv','sum'), w=('w','sum'), w2=('w2','sum')).reset_index()
    py = m.groupby(['pid','year']).agg(wv=('wv','sum'), w=('w','sum'), w2=('w2','sum'))
    py['y'] = py.wv/py.w
    m = m.join(py[['y']], on=['pid','year']); m['r2'] = (m.wv - m.y*m.w)**2
    py['V'] = np.maximum(m.groupby(['pid','year']).r2.sum()/py.w**2, s2*py.w2/py.w**2)
    return py
def kalman(Y, V, mu, tau2, q):
    n, T = Y.shape; m = np.full(n, mu); P = np.full(n, tau2); LL = 0.0; M = np.zeros((n,T)); PP = np.zeros((n,T))
    for t in range(T):
        if t>0: P = P + q
        obs = ~np.isnan(Y[:,t])
        S = P[obs] + V[obs,t]; e = Y[obs,t] - m[obs]
        LL += np.sum(-0.5*(np.log(2*np.pi*S) + e**2/S))
        K = P[obs]/S; m[obs] = m[obs] + K*e; P[obs] = (1-K)*P[obs]
        M[:,t] = m; PP[:,t] = P
    return LL, M, PP
OUT = {}
for role in ['bat','bowl']:
    if role=='bat': d = R[R.faced].rename(columns={'striker_id':'pid'}); d['ball']=1
    else: d = R.rename(columns={'bowler_id':'pid'}); d['ball']=d.legal.astype(int)
    d['val'] = d[COL[role]]; u = UNIT[role]; minp = 100 if role=='bat' else 120
    a0, pr = ratings(match_agg(d, alpha=1), minp, 10, inn_min=4 if role=='bat' else 6)
    elig = a0[a0.eligible].index
    py = player_years(d)
    Y = py.y.unstack().reindex(index=elig, columns=YRS).values; V = py.V.unstack().reindex(index=elig, columns=YRS).values
    mu, tau2 = pr['mu'], pr['tau2']
    grid = tau2*np.array([0, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0])
    lls = [kalman(Y, V, mu, tau2, q)[0] for q in grid]
    qbest = grid[int(np.argmax(lls))]
    # finer search around the best
    fine = np.linspace(max(qbest-0.25*tau2,0), qbest+0.25*tau2, 21); lls2 = [kalman(Y, V, mu, tau2, q)[0] for q in fine]; qbest = fine[int(np.argmax(lls2))]
    LL0 = kalman(Y, V, mu, tau2, 0.0)[0]; LLb = kalman(Y, V, mu, tau2, qbest)[0]
    _, M, PP = kalman(Y, V, mu, tau2, qbest)
    # typical weight on the latest season for a regular: K for a median-V season after 4 prior seasons
    medV = np.nanmedian(V[:,-1]); Pss = tau2
    for _ in range(4): Pss = (Pss + qbest)*medV/(Pss+qbest+medV) if True else Pss
    w_last = (Pss+qbest)/(Pss+qbest+medV)
    names = pd.concat([R[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), R[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
    tab = pd.DataFrame({'name':names.reindex(elig).values, 'rating_v3':a0.loc[elig,'rating'].values*u, 'level_2026':M[:,-1]*u, 'level_se':np.sqrt(PP[:,-1])*u,
                        'level_2024':M[:,2]*u}, index=elig)
    tab['trend'] = tab.level_2026 - tab.rating_v3
    tab.to_csv(f'outputs/v3/form_{role}.csv')
    # out-of-time: filter 2022-24 only (same q) -> 2025-26 pressure value; compare with q=0 and with the plain rating
    te = d[d.year>=2025]; ate,_ = ratings(match_agg(te, alpha=1), 40 if role=='bat' else 50, 4, inn_min=4)
    atr,_ = ratings(match_agg(d[d.year<=2024], alpha=1), 40 if role=='bat' else 50, 4, inn_min=4)
    keep = atr[atr.Pn>=60].index.intersection(ate[ate.Pn>=40].index)
    Y3 = py.y.unstack().reindex(index=keep, columns=YRS[:3]).values; V3 = py.V.unstack().reindex(index=keep, columns=YRS[:3]).values
    res = {}
    for lab, q in [('equal weight (q=0)', 0.0), ('data-chosen drift', qbest), ('heavy recency (q=tau2)', tau2)]:
        res[lab] = wcorr(kalman(Y3, V3, mu, tau2, q)[1][:,-1], ate.loc[keep,'pwi'], ate.loc[keep,'w'])
    res['plain 2022-24 rating'] = wcorr(atr.loc[keep,'rating'], ate.loc[keep,'pwi'], ate.loc[keep,'w'])
    OUT[role] = dict(q_over_tau2=float(qbest/tau2), drift_sd_per_year=float(np.sqrt(qbest)*u), tau=float(np.sqrt(tau2)*u), LL_gain=float(LLb-LL0), weight_last_season=float(w_last), oot={k:float(v) for k,v in res.items()}, n_oot=int(len(keep)))
    print(f'\n===== {role.upper()}: drift q = {qbest/tau2:.2f} x tau2 (drift sd {np.sqrt(qbest)*u:.2f} per year vs spread of players {np.sqrt(tau2)*u:.2f}) | log-lik gain vs no drift {LLb-LL0:.1f}')
    print(f'  weight a regular\'s latest season gets: {w_last:.0%}')
    print('  out-of-time r:', {k: round(v,3) for k,v in res.items()}, f'(n={len(keep)})')
    print(tab.sort_values('level_2026', ascending=False).head(14).round(2).to_string())
json.dump(OUT, open('outputs/v3/form_summary.json','w'), indent=1)
