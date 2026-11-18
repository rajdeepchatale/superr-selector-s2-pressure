"""Pressure-Weighted Impact (PWI): each ball's value above expected, weighted by its Pressure Index (PI/100)^alpha,
   shrunk by empirical Bayes (match-clustered noise), with eligibility gates on proven pressure exposure."""
import pandas as pd, numpy as np
UNIT = {'bat':100, 'bowl':24}
def role_frame(T, role):
    if role=='bat':
        d = T[T.faced].rename(columns={'striker_id':'pid','bat_val_adj':'val'}); d['ball']=1
    else:
        d = T.rename(columns={'bowler_id':'pid','bowl_val_adj':'val'}); d['ball']=d.legal.astype(int)
    return d
def match_agg(d, alpha=1.0, th=80, recency=None):
    w = (d.PI/100)**alpha
    if recency: w = w * 0.5**((2026 - d.year)/recency)
    d = d.assign(w=w, wv=w*d.val, isP=(d.PI>=th), Pv=np.where(d.PI>=th, d.val, 0.0), Nv=np.where(d.PI<th, d.val, 0.0),
                 Pb=((d.PI>=th)&(d.ball==1)).astype(int), Nb=((d.PI<th)&(d.ball==1)).astype(int),
                 Pn=(d.PI>=th).astype(int), Nn=(d.PI<th).astype(int))
    return d.groupby(['pid','match_id']).agg(wv=('wv','sum'), w=('w','sum'), Pv=('Pv','sum'), Pn=('Pn','sum'), Pb=('Pb','sum'),
                                             Nv=('Nv','sum'), Nn=('Nn','sum'), Nb=('Nb','sum'), year=('year','first'), comp=('comp_group','first')).reset_index()
def ratings(g, min_p, min_inn, inn_min=4, prior=None):
    a = g.groupby('pid').agg(wv=('wv','sum'), w=('w','sum'), Pv=('Pv','sum'), Pn=('Pn','sum'), Pb=('Pb','sum'), Nv=('Nv','sum'), Nn=('Nn','sum'), Nb=('Nb','sum'), matches=('match_id','nunique'))
    a['innP'] = g[g.Pn>=inn_min].groupby('pid').size().reindex(a.index).fillna(0)
    a['pwi'] = a.wv/a.w
    # cluster-robust sampling variance of the weighted mean
    gg = g.merge(a[['pwi']], left_on='pid', right_index=True)
    gg['r2'] = (gg.wv - gg.pwi*gg.w)**2
    a['V'] = gg.groupby('pid').r2.sum()/a.w**2
    a['eligible'] = (a.Pn>=min_p) & (a.innP>=min_inn)
    if prior is None:
        e = a[a.eligible]; wt = 1/(e.V + e.V.median())
        mu = np.average(e.pwi, weights=wt)
        tau2 = max(np.average((e.pwi-mu)**2, weights=wt) - np.average(e.V, weights=wt), 1e-9)
        prior = dict(mu=mu, tau2=tau2)
    B = prior['tau2']/(prior['tau2']+a.V)
    a['rating'] = prior['mu'] + B*(a.pwi - prior['mu'])
    a['rating_se'] = np.sqrt(B*a.V)
    a['shrink_B'] = B
    a['xP'] = a.Pv/a.Pn.replace(0,np.nan); a['xN'] = a.Nv/a.Nn.replace(0,np.nan); a['gap'] = a.xP - a.xN
    return a, prior
def consistency(g, inn_min=4, k=10):
    P = g[g.Pn>=inn_min]
    c = P.groupby('pid').agg(succ=('Pv', lambda x:(x>0).sum()), inns=('Pv','size'), med_inn=('Pv','median'))
    base = c.succ.sum()/c.inns.sum()
    c['success_rate'] = (c.succ + k*base)/(c.inns + k)
    return c, base
