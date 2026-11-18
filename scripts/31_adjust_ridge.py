"""Upgrade v3: adjust every ball for (a) who was at the other end, (b) the ground, (c) dew, (d) home side,
   and (e) how the pitch played that day, read from everyone else in the match (leave-one-player-out).
   Step 1: ridge regression of per-ball value on batter + bowler + venue-by-pace/spin + dew-by-pace/spin + home.
   Step 2: matchday pitch = shrunk mean of step-1 residuals of OTHER players in the same match and bowling type."""
import pandas as pd, numpy as np, scipy.sparse as sp, scipy.linalg as la, json
T = pd.read_pickle('outputs/rated_balls.pkl')
C = pd.read_pickle('outputs/v3/match_conditions.pkl')
T = T.join(C[['venue_id','night','dew_region','home_team_id','away_team_id','home_is_home','away_is_home']].rename(columns={'venue_id':'venue'}), on='match_id')
T['dew'] = ((T.night==1)&(T.dew_region==1)&(T.innings==2)).astype(int)
bat_home = np.where(T.batting_team_id==T.home_team_id, T.home_is_home, np.where(T.batting_team_id==T.away_team_id, T.away_is_home, 0))
bowl_home = np.where(T.bowling_team_id==T.home_team_id, T.home_is_home, np.where(T.bowling_team_id==T.away_team_id, T.away_is_home, 0))
T['home_sign'] = bat_home.astype(int) - bowl_home.astype(int)
T['ipl'] = (T.comp_group=='IPL').astype(int)
T['vt'] = T.venue.astype(str) + '_' + T.spin.astype(str)
T['mt'] = T.match_id.astype(str) + '_' + T.spin.astype(str)

def mom_tau2(y, key, s2, nmin=50):
    g = pd.DataFrame({'y':y,'k':key}).groupby('k').y.agg(['mean','count']); g = g[g['count']>=nmin]
    return max(np.average((g['mean']-np.average(g['mean'],weights=g['count']))**2, weights=g['count']) - np.average(s2/g['count'], weights=g['count']), 1e-6)

def fit(D, y, own, opp, boot_seed=None):
    """ridge on: own player, opponent player, venue x type, dew x type, home x comp, intercept x comp"""
    s2 = y.var()
    blocks = [('own', D[own].astype(str)), ('opp', D[opp].astype(str)), ('vt', D.vt)]
    lam = {b: s2/mom_tau2(y.values, k.values, s2) for b,k in blocks}
    cols, rows, vals, pen, names = [], [], [], [], []
    n = len(D); r = np.arange(n); off = 0
    for b,k in blocks:
        cat = pd.Categorical(k); m = len(cat.categories)
        rows.append(r); cols.append(off + cat.codes); vals.append(np.ones(n)); pen += [lam[b]]*m; names += [(b,c) for c in cat.categories]; off += m
    for b, v in [('dew_pace', D.dew*(1-D.spin)), ('dew_spin', D.dew*D.spin), ('home_ipl', D.home_sign*D.ipl), ('home_t20i', D.home_sign*(1-D.ipl)), ('int_ipl', D.ipl), ('int_t20i', 1-D.ipl)]:
        rows.append(r); cols.append(np.full(n, off)); vals.append(v.values.astype(float)); pen.append(1.0); names.append((b,'')); off += 1
    X = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, off))
    A = (X.T @ X).toarray() + np.diag(pen); bvec = X.T @ y.values
    beta = la.solve(A, bvec, assume_a='pos')
    B = pd.Series(beta, index=pd.MultiIndex.from_tuples(names))
    return B, X, lam, s2

out = {}
for role in ['bat','bowl']:
    D = T[T.faced].copy() if role=='bat' else T.copy()
    y = D.bat_v if role=='bat' else D.bowl_v
    own, opp = ('striker_id','bowler_id') if role=='bat' else ('bowler_id','striker_id')
    B, X, lam, s2 = fit(D, y, own, opp)
    pred_all = X @ B.values
    own_part = B['own'].reindex(D[own].astype(str)).values
    opp_part = B['opp'].reindex(D[opp].astype(str)).values
    vt_part  = B['vt'].reindex(D.vt).values
    dew_part = D.dew*(1-D.spin)*B[('dew_pace','')] + D.dew*D.spin*B[('dew_spin','')]
    home_part= D.home_sign*D.ipl*B[('home_ipl','')] + D.home_sign*(1-D.ipl)*B[('home_t20i','')]
    int_part = D.ipl*B[('int_ipl','')] + (1-D.ipl)*B[('int_t20i','')]
    resid = y.values - pred_all
    # step 2: matchday pitch from OTHER players (same match, same bowling type), shrunk
    tau2_m = mom_tau2(resid, D.mt.values, s2, nmin=30); lam_m = s2/tau2_m
    key_mp = D.mt + '|' + D[own].astype(str)
    S_m = pd.Series(resid).groupby(D.mt.values).agg(['sum','count']); S_mp = pd.Series(resid).groupby(key_mp.values).agg(['sum','count'])
    sm = S_m.reindex(D.mt.values); smp = S_mp.reindex(key_mp.values)
    md_part = (sm['sum'].values - smp['sum'].values) / (sm['count'].values - smp['count'].values + lam_m)
    D['cond'] = vt_part + dew_part.values + home_part.values + int_part.values + md_part
    D['oppq'] = opp_part
    D['v_cond'] = y.values - D.cond.values
    D['v_opp']  = y.values - D.oppq.values - int_part.values
    D['v_full'] = y.values - D.cond.values - D.oppq.values
    # re-centre: the adjustments shift every ball by a near-constant amount (good players bowl and bat more balls),
    # so put the average ball back at 0. This changes no ranking; ratings stay 'runs above an average player'.
    for c in ['v_cond','v_opp','v_full']: D[c] = D[c] - D[c].mean()
    u = 100 if role=='bat' else 24
    print(f'\n===== {role.upper()} (per-ball value: {"runs per 100 balls" if role=="bat" else "runs per 24 balls"})')
    print(f'  penalties: own {lam["own"]:.0f}, opponent {lam["opp"]:.0f}, venue x type {lam["vt"]:.0f}, matchday {lam_m:.0f} | residual sd {np.sqrt(s2):.2f}')
    print(f'  spread (sd) of adjustments per ball x{u}: opponent {np.std(opp_part)*u:.2f} | venue {np.std(vt_part)*u:.2f} | matchday {np.std(md_part)*u:.2f} | dew {np.std(dew_part)*u:.2f} | home {np.std(home_part)*u:.2f}')
    print(f'  dew effect x{u}: pace {B[("dew_pace","")]*u:+.2f}, spin {B[("dew_spin","")]*u:+.2f} | home effect x{u}: IPL {B[("home_ipl","")]*u:+.2f}, T20I {B[("home_t20i","")]*u:+.2f}')
    out[role] = D[['match_id','innings','innings_ball_num','v_cond','v_opp','v_full','cond','oppq']].copy()
    json.dump({k:float(v) for k,v in lam.items()}|{'matchday':float(lam_m),'s2':float(s2), 'dew_pace':float(B[('dew_pace','')]), 'dew_spin':float(B[('dew_spin','')]),
               'home_ipl':float(B[('home_ipl','')]), 'home_t20i':float(B[('home_t20i','')])}, open(f'outputs/v3/ridge_{role}.json','w'), indent=1)
    vt = B['vt']; vt.index = vt.index.str.split('_').map(lambda x:(int(x[0]),int(x[1])))
    vt.to_pickle(f'outputs/v3/venue_effects_{role}.pkl')
# merge back
K = ['match_id','innings','innings_ball_num']
R = T.merge(out['bat'].rename(columns={c:'bat_'+c for c in ['v_cond','v_opp','v_full','cond','oppq']}), on=K, how='left') \
     .merge(out['bowl'].rename(columns={c:'bowl_'+c for c in ['v_cond','v_opp','v_full','cond','oppq']}), on=K, how='left')
R.to_pickle('outputs/v3/rated_balls_v3.pkl'); print('\nsaved', len(R))
