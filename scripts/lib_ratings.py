"""Core rating engine (reused by ratings, validation, bootstrap, sensitivity)."""
import pandas as pd, numpy as np

def player_match_table(T, role, th=80, val_col=None, weight_by_li=False):
    """Aggregate to player x match: pressure / normal sums and ball counts."""
    if role=='bat':
        d = T[T.faced]; pid='striker_id'; val = val_col or 'bat_val_adj'; ball = d.faced
    else:
        d = T; pid='bowler_id'; val = val_col or 'bowl_val_adj'; ball = d.legal
    d = d.assign(P=(d.PI>=th), v=d[val], b=ball.astype(int), one=1)
    if weight_by_li:
        d = d.assign(wv=np.where(d.P, d.v*d.LI, d.v), wb=np.where(d.P, d.LI, 1.0))
    g = d.groupby([pid,'match_id','P']).agg(v=('v','sum'), n=('one','sum'), legal=('b','sum'), year=('year','first'), comp=('comp_group','first')).reset_index()
    g = g.rename(columns={pid:'pid'})
    return g

def eb_ratings(pm, min_p=100, min_inn=10, prior=None, inn_min_balls=4):
    """Hierarchical empirical Bayes: true pressure level = general ability + clutch adjustment, each shrunk by evidence."""
    P = pm[pm.P]; N = pm[~pm.P]
    a = pd.DataFrame({'nP':P.groupby('pid').n.sum(), 'sP':P.groupby('pid').v.sum(), 'legalP':P.groupby('pid').legal.sum(),
                      'nN':N.groupby('pid').n.sum(), 'sN':N.groupby('pid').v.sum()}).fillna(0)
    a['innP'] = P[P.n>=inn_min_balls].groupby('pid').size().reindex(a.index).fillna(0)
    a['xP'] = a.sP/a.nP.replace(0,np.nan); a['xN'] = a.sN/a.nN.replace(0,np.nan)
    a['eligible'] = (a.nP>=min_p) & (a.innP>=min_inn) & (a.nN>=min_p)
    if prior is None:
        # per-ball noise (pooled within-player variance), estimated from ball-level sums of squares is not stored -> use match-level dispersion
        e = a[a.eligible]
        # per-ball variance approximated from match-level sums: Var(sum over n balls) ~ n*s2
        def s2(df):
            x = df.v - df.n*df.pid.map((a.sP/a.nP) if df is P else (a.sN/a.nN)).fillna(0)
            return (x**2).sum()/df.n.sum()
        s2P, s2N = s2(P[P.pid.isin(e.index)]), s2(N[N.pid.isin(e.index)])
        w = e.nP
        muN = np.average(e.xN, weights=e.nN); D = e.xP - e.xN; muD = np.average(D, weights=w)
        tauN2 = max(np.average((e.xN-muN)**2, weights=e.nN) - np.average(s2N/e.nN, weights=e.nN), 1e-6)
        tauD2 = max(np.average((D-muD)**2, weights=w) - np.average(s2P/e.nP + s2N/e.nN, weights=w), 0.0)
        prior = dict(s2P=s2P, s2N=s2N, muN=muN, muD=muD, tauN2=tauN2, tauD2=tauD2)
    p = prior
    vN = p['s2N']/a.nN.clip(lower=1); vP = p['s2P']/a.nP.clip(lower=1)
    tN, tD = p['tauN2'], p['tauD2']
    # joint Gaussian posterior for pi = theta + delta given xN, xP
    S11 = tN+vN; S12 = tN; S22 = tN+tD+vP; det = S11*S22 - S12**2
    c1, c2 = tN, tN+tD                          # Cov(pi, xN), Cov(pi, xP)
    dN = a.xN.fillna(p['muN']) - p['muN']; dP = a.xP.fillna(p['muN']+p['muD']) - (p['muN']+p['muD'])
    w1 = (c1*S22 - c2*S12)/det; w2 = (-c1*S12 + c2*S11)/det
    a['pressure_rating'] = (p['muN']+p['muD']) + w1*dN + w2*dP
    post_var = (tN+tD) - (c1*w1 + c2*w2)
    a['rating_se'] = np.sqrt(post_var)
    # theta (general ability) posterior using both obs too
    t1, t2 = tN, tN
    a['general_rating'] = p['muN'] + ((t1*S22 - t2*S12)/det)*dN + ((-t1*S12 + t2*S11)/det)*dP
    a['clutch_shrunk'] = a.pressure_rating - a.general_rating - p['muD']
    a['raw_delta'] = (a.xP - a.xN) - p['muD']
    return a, prior

def consistency(pm, inn_min_balls=4, prior_k=10):
    P = pm[pm.P & (pm.n>=inn_min_balls)]
    c = P.groupby('pid').agg(k=('v', lambda x: (x>0).sum()), m=('v','size'), med=('v','median'), q25=('v', lambda x: x.quantile(.25)))
    base = c.k.sum()/c.m.sum()
    c['success_rate'] = (c.k + prior_k*base)/(c.m + prior_k)
    c['raw_success'] = c.k/c.m
    return c, base
