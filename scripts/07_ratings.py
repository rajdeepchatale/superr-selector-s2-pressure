import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_ratings import *
pd.set_option('display.width',260); pd.set_option('display.max_columns',40)
T = pd.read_pickle('outputs/rated_balls.pkl')
ctp = pd.read_csv('data/raw/competition_team_player_mapping.csv')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
last_team = ctp.merge(pd.read_csv('data/raw/competitions.csv')[['comp_id','season']], on='comp_id')
for role, unit, minp in [('bat',100,100), ('bowl',24,120)]:
    pm = player_match_table(T, role)
    a, pr = eb_ratings(pm, min_p=minp, min_inn=10)
    c, base = consistency(pm)
    a = a.join(c[['success_rate','raw_success','m','med','q25']])
    a['name'] = a.index.map(names)
    print(f'\n================ {role.upper()} | prior: muN={pr["muN"]*unit:.2f} muD={pr["muD"]*unit:.2f} sd_ability={np.sqrt(pr["tauN2"])*unit:.2f} sd_clutch={np.sqrt(pr["tauD2"])*unit:.2f} (per {unit} balls) | success base {base:.3f}')
    e = a[a.eligible].copy()
    for col in ['xP','xN','pressure_rating','rating_se','general_rating','clutch_shrunk','raw_delta']: e[col]=e[col]*unit
    e = e.sort_values('pressure_rating', ascending=False)
    print('eligible players:', len(e))
    print(e[['name','nP','innP','nN','xP','xN','raw_delta','general_rating','clutch_shrunk','pressure_rating','rating_se','success_rate','m']].head(30).round(2).to_string())
    e.to_csv(f'outputs/ratings_{role}.csv')
