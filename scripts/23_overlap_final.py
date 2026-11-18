"""Robustness of the FINAL lists (Kohli in for Pooran): top-10 overlap under each alternative setting."""
import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_pwi import *
T = pd.read_pickle('outputs/rated_balls.pkl')
names = pd.concat([T[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), T[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
FINAL = {'bat':['Suryakumar Yadav','Abhishek Sharma','Phil Salt','Reeza Hendricks','Heinrich Klaasen','Tim David','Glenn Phillips','Vaibhav Sooryavanshi','Namboori Tilak Varma','Virat Kohli'],
         'bowl':['Sunil Narine','Jasprit Bumrah','Kuldeep Yadav','Josh Hazlewood','Rashid Khan','Varun Chakravarthy','Matheesha Pathirana','Wanindu Hasaranga','Mujeeb Ur Rahman','Krunal Pandya']}
def top(d, role, minp=None, **kw):
    minp = minp or (100 if role=='bat' else 120); im = 4 if role=='bat' else 6
    g = match_agg(d, **kw); a,_ = ratings(g, minp, 10, inn_min=im)
    return [names[p] for p in a[a.eligible].sort_values('rating', ascending=False).head(10).index]
for role in ['bat','bowl']:
    d = role_frame(T, role); F = set(FINAL[role]); rows = []
    for al in [0.5, 1, 2]: rows.append((f'pressure weight alpha={al}', top(d, role, alpha=al)))
    g = match_agg(d, alpha=1).pipe(lambda g: g.assign(wv=g.Pv, w=g.Pn)); a,_ = ratings(g, 100 if role=='bat' else 120, 10, inn_min=4 if role=='bat' else 6)
    rows.append(('pressure balls only', [names[p] for p in a[a.eligible].sort_values('rating', ascending=False).head(10).index]))
    rows.append(('recency (2-year half-life)', top(d, role, alpha=1, recency=2)))
    rows.append(('pressure line at 75', top(d, role, alpha=1, th=75)))
    rows.append(('pressure line at 85', top(d, role, alpha=1, th=85)))
    rows.append(('stricter sample (+50%)', top(d, role, minp=150 if role=='bat' else 180, alpha=1)))
    dn = d.copy(); dn['val'] = dn.bat_v if role=='bat' else dn.bowl_v; rows.append(('no opponent adjustment', top(dn, role, alpha=1)))
    dw = d.copy()
    if role=='bat': dw['val'] = (dw.bat_runs-dw.E_bat_runs) - 11*(dw.striker_out.astype(int)-dw.P_out) - dw.adj_b
    else: dw['val'] = (dw.E_bowl_runs-dw.bowler_runs) + 11*(dw.bowler_wkt.astype(int)-dw.P_bwkt) - dw.adj_w
    rows.append(('wicket = 11 runs', top(dw, role, alpha=1)))
    print(f'\n== {role}')
    for k, t in rows:
        print(f'{k:30s} {len(F & set(t))}/10  in: {", ".join(x for x in t if x not in F) or "-"} | out: {", ".join(x for x in FINAL[role] if x not in t) or "-"}')
