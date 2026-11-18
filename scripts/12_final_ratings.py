import pandas as pd, numpy as np, sys, json
sys.path.insert(0,'scripts'); from lib_pwi import *
pd.set_option('display.width',280); pd.set_option('display.max_columns',40)
T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
ctp = pd.read_csv('data/raw/competition_team_player_mapping.csv').merge(pd.read_csv('data/raw/competitions.csv')[['comp_id','match_format']], on='comp_id')
intl = ctp[ctp.match_format=='T20I'].groupby('player_id').team_name.agg(lambda x: x.value_counts().index[0])
ipl = ctp[ctp.comp_name.str.startswith('IPL')].groupby('player_id').team_name.agg(lambda x: '/'.join(pd.unique(x)))
cfg = dict(alpha=1.0, th=80, min_bat=100, min_bowl=120, min_inn=10)
out = {}
for role in ['bat','bowl']:
    u = UNIT[role]; d = role_frame(T, role)
    g = match_agg(d, alpha=cfg['alpha'], th=cfg['th'])
    a, prior = ratings(g, cfg['min_bat'] if role=='bat' else cfg['min_bowl'], cfg['min_inn'], inn_min=4 if role=='bat' else 6)
    c, base = consistency(g, inn_min=4 if role=='bat' else 6)
    a = a.join(c)
    # traditional stats in pressure (top 20%) vs usual
    if role=='bat':
        s = d.assign(P=d.PI>=cfg['th']).groupby(['pid','P']).agg(runs=('bat_runs','sum'), balls=('ball','sum'), outs=('striker_out','sum'), fours=('is_four','sum'), sixes=('is_six','sum'), dots=('bat_runs', lambda x:(x==0).sum())).unstack('P')
        for k,lab in [(True,'P'),(False,'N')]:
            a[f'SR_{lab}'] = 100*s[('runs',k)]/s[('balls',k)]; a[f'Avg_{lab}'] = s[('runs',k)]/s[('outs',k)].replace(0,np.nan)
            a[f'BpD_{lab}'] = s[('balls',k)]/s[('outs',k)].replace(0,np.nan); a[f'Dot%_{lab}'] = 100*s[('dots',k)]/s[('balls',k)]
            a[f'Bdry%_{lab}'] = 100*(s[('fours',k)]+s[('sixes',k)])/s[('balls',k)]
        a['runs_P'] = s[('runs',True)]; a['outs_P'] = s[('outs',True)]
    else:
        s = d.assign(P=d.PI>=cfg['th']).groupby(['pid','P']).agg(runs=('bowler_runs','sum'), balls=('ball','sum'), wkts=('bowler_wkt','sum'), dots=('total_runs', lambda x:(x==0).sum())).unstack('P')
        for k,lab in [(True,'P'),(False,'N')]:
            a[f'Econ_{lab}'] = 6*s[('runs',k)]/s[('balls',k)]; a[f'SRb_{lab}'] = s[('balls',k)]/s[('wkts',k)].replace(0,np.nan)
            a[f'Dot%_{lab}'] = 100*s[('dots',k)]/s[('balls',k)]
        a['wkts_P'] = s[('wkts',True)]; a['overs_P'] = s[('balls',True)]/6
    # by competition (pressure-weighted, raw)
    for cg in ['IPL','T20I_FULL']:
        gc = g[g.comp==cg].groupby('pid')[['wv','w']].sum(); a[f'pwi_{cg}'] = (gc.wv/gc.w).reindex(a.index)*u; a[f'w_{cg}'] = gc.w.reindex(a.index)
    a['name'] = a.index.map(names); a['country'] = a.index.map(intl); a['ipl_teams'] = a.index.map(ipl)
    for col in ['pwi','rating','rating_se','xP','xN','gap','med_inn']: a[col] = a[col]*u
    e = a[a.eligible].sort_values('rating', ascending=False).copy(); e['rank'] = np.arange(1, len(e)+1)
    e['tau'] = np.sqrt(prior['tau2'])*u; e['mu'] = prior['mu']*u
    print(f'\n========== {role.upper()}: eligible {len(e)} | league-wide spread of true skill sd={np.sqrt(prior["tau2"])*u:.2f} per {u} balls | success base {base:.2f}')
    show = ['rank','name','country','Pn','innP','pwi','rating','rating_se','xP','xN','gap','success_rate','inns'] + (['SR_P','SR_N','Avg_P','Avg_N'] if role=='bat' else ['Econ_P','Econ_N','SRb_P','SRb_N','wkts_P'])
    print(e[show].head(25).round(2).to_string(index=False))
    e.to_csv(f'outputs/final_{role}.csv'); a.to_csv(f'outputs/all_{role}.csv')
    out[role] = prior
json.dump({k:{kk:float(vv) for kk,vv in v.items()} for k,v in out.items()}|{'cfg':cfg}, open('outputs/priors.json','w'), indent=1)
