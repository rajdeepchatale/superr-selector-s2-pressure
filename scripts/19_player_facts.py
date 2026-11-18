import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
T = pd.read_pickle('outputs/rated_balls.pkl')            # IPL + full-member T20Is, usable matches
B = pd.read_pickle('outputs/balls.pkl')                  # all balls (for season totals)
p11 = pd.read_csv('data/raw/playing_eleven.csv'); mat = pd.read_csv('outputs/matches_enriched.csv')
teams = pd.read_csv('data/raw/teams.csv').drop_duplicates('team_id').set_index('team_id').team_name
names = {'Suryakumar Yadav':1699,'Abhishek Sharma':6281,'Phil Salt':5553,'Reeza Hendricks':768,'Heinrich Klaasen':4260,'Tim David':6396,
         'Glenn Phillips':4853,'Vaibhav Sooryavanshi':50284,'Namboori Tilak Varma':7897,'Nicholas Pooran':3125}
rows=[]
for nm,pid in names.items():
    f = T[(T.striker_id==pid)&T.faced]; P = f[f.PI>=80]; N = f[f.PI<80]
    hand = B[B.striker_id==pid].batting_type.mode().iat[0]
    pl = p11[(p11.player_id==pid)&(p11.is_played==True)]
    wk = (pl.is_wk.astype(str).str.lower()=='true').mean()
    bo = B[(B.striker_id==pid)].groupby('match_id').batting_order.first().value_counts(normalize=True).sort_index()
    pos = ', '.join(f'#{int(k)} {v:.0%}' for k,v in bo.head(8).items() if v>=0.08)
    sr = lambda d: 100*d.bat_runs.sum()/max(len(d),1)
    ph = P.phase.value_counts(normalize=True)
    chase = (P.innings==2).mean()
    # best pressure innings
    g = P.groupby('match_id').agg(val=('bat_val_adj','sum'), pb=('faced','sum'))
    best = g.sort_values('val', ascending=False).head(2).index
    best_txt=[]
    for m in best:
        inn = B[(B.match_id==m)&(B.striker_id==pid)&B.faced]; tot = B[(B.match_id==m)&(B.striker_id==pid)]
        mm = mat[mat.match_id==m].iloc[0]; r = inn.bat_runs.sum(); bl = len(inn)
        out = B[(B.match_id==m)&(B.dismissed_player_id==pid)&B.is_wicket].shape[0]>0
        team = teams.get(inn.batting_team_id.iat[0]); opp = teams.get(inn.bowling_team_id.iat[0]); innings = inn.innings.iat[0]
        best_txt.append(f"{r}{'' if out else '*'} off {bl} ({team} v {opp}, {mm.comp_name}, {'chasing '+str(int(inn.target.iat[0])) if innings==2 else 'batting first'}; result: {mm.result})")
    rows.append(dict(name=nm, hand=hand, wk_share=round(wk,2), positions=pos, P_balls=len(P), P_SR=round(sr(P)), N_SR=round(sr(N)),
                     P_SR_pace=round(sr(P[P.pace_or_spin=='Pace'])), P_SR_spin=round(sr(P[P.pace_or_spin=='Spin'])), N_SR_pace=round(sr(N[N.pace_or_spin=='Pace'])), N_SR_spin=round(sr(N[N.pace_or_spin=='Spin'])),
                     P_chase_share=round(chase,2), P_phase=', '.join(f'{k} {v:.0%}' for k,v in ph.items()), P_outs=int(P.striker_out.sum()), P_runs=int(P.bat_runs.sum()),
                     best1=best_txt[0], best2=best_txt[1] if len(best_txt)>1 else ''))
df = pd.DataFrame(rows)
for r in df.to_dict('records'):
    print('\n'+'='*100); [print(f'{k:14s}: {v}') for k,v in r.items()]
# season facts
def season(pid, comp):
    d = B[(B.striker_id==pid)&(B.comp_name==comp)&B.faced]
    per = d.groupby('match_id').bat_runs.sum()
    outs = B[(B.comp_name==comp)&(B.dismissed_player_id==pid)&B.is_wicket].shape[0]
    return dict(inns=per.size, runs=int(per.sum()), SR=round(100*d.bat_runs.sum()/max(len(d),1),1), hundreds=int((per>=100).sum()), fifties=int(((per>=50)&(per<100)).sum()), outs=outs)
print('\nSooryavanshi IPL 2025:', season(50284,'IPL 2025'), '| IPL 2026:', season(50284,'IPL 2026'))
print('Pooran IPL 2024:', season(3125,'IPL 2024'), '| IPL 2025:', season(3125,'IPL 2025'), '| IPL 2026:', season(3125,'IPL 2026'))
top = B[B.comp_name=='IPL 2026'].groupby('striker_name').bat_runs.sum().sort_values(ascending=False).head(5); print('IPL 2026 top run scorers (bat runs):', top.to_dict())
top = B[B.comp_name=='IPL 2025'].groupby('striker_name').bat_runs.sum().sort_values(ascending=False).head(5); print('IPL 2025 top run scorers:', top.to_dict())
# Abhishek & Phillips bowling
for nm,pid in [('Abhishek Sharma',6281),('Glenn Phillips',4853)]:
    d = B[B.bowler_id==pid]
    print(nm, 'bowling:', {c: dict(balls=int(x.legal.sum()), wkts=int(x.bowler_wkt.sum()), econ=round(6*x.bowler_runs.sum()/max(x.legal.sum(),1),2)) for c,x in d.groupby(d.comp_group)})
# Hendricks: any IPL? teams played for
print('Hendricks teams in data:', B[B.striker_id==768].batting_team_id.map(teams).value_counts().to_dict())
print('Rickelton in data:', B[B.striker_name.str.contains('Rickelton', na=False)][['striker_name','batting_type']].drop_duplicates().to_dict('records'))
