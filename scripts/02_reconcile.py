import pandas as pd, numpy as np, re
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
R='data/raw/'
bbb = pd.read_csv(R+'ball_by_ball.csv', low_memory=False)
mat = pd.read_csv(R+'matches.csv'); comp = pd.read_csv(R+'competitions.csv')
# inspect extras semantics
cols=['runs','extras_type','extras1_runs','extras_2_runs','is_wicket','dismissal_type','over_ball_num']
for et in ['wide','legbyes','Overstep','byes','other','Penalty']:
    sub=bbb[bbb.extras_type==et]
    print(f'\n--- {et} n={len(sub)}'); print(sub[['runs','extras1_runs','extras_2_runs']].value_counts().head(8).to_string())
print('\nextras_2_runs>0 rows:'); print(bbb[bbb.extras_2_runs>0][['match_id','innings','overid','over_ball_num','runs','extras_type','extras1_runs','extras_2_runs']].head(12).to_string())
print('\nruns>0 with extras_type wide:', ((bbb.extras_type=='wide')&(bbb.runs>0)).sum())
# legal balls per over check
bbb['legal'] = ~bbb.extras_type.isin(['wide','Overstep'])
lb = bbb[bbb.innings<=2].groupby(['match_id','innings','overid']).legal.sum()
print('\nlegal balls per over distribution:', lb.value_counts().sort_index().to_dict())
# Does over_ball_num count all deliveries? compare to count
cnt = bbb[bbb.innings<=2].groupby(['match_id','innings','overid']).size()
mx = bbb[bbb.innings<=2].groupby(['match_id','innings','overid']).over_ball_num.max()
print('over_ball_num max == deliveries count share:', (cnt==mx).mean())
# innings totals
bbb['tot'] = bbb.runs + bbb.extras1_runs + bbb.extras_2_runs
inn = bbb[bbb.innings<=2].groupby(['match_id','innings']).agg(team=('batting_team_id','first'), runs=('tot','sum'), wkts=('is_wicket','sum'), legal=('legal','sum')).reset_index()
w = inn.pivot(index='match_id', columns='innings')
w.columns=[f'{a}{b}' for a,b in w.columns]; w=w.reset_index()
m = mat.merge(w, on='match_id', how='left').merge(comp[['comp_id','match_format','comp_name']], on='comp_id')
def parse(r):
    s=str(r)
    mm=re.search(r'Won by (\d+)\s*(run|wicket)', s, re.I)
    if mm: return int(mm.group(1)), mm.group(2).lower()
    return None, None
m[['margin','mtype']] = m.result.apply(lambda s: pd.Series(parse(s)))
m['dls'] = m.revised_target.notna() | m.first_inn_revised_overs.notna()
ok = m.runs1.notna() & m.runs2.notna()
r = m[ok & (m.mtype=='run') & ~m.dls]
r_ok = (r.runs1 - r.runs2 == r.margin)
print(f'\nRUNS-margin matches (no DLS): {len(r)}; exact match {r_ok.sum()} ({r_ok.mean():.1%})')
print(r[~r_ok][['match_id','comp_name','result','runs1','runs2','margin']].head(15).to_string())
wk = m[ok & (m.mtype=='wicket') & ~m.dls]
wk_ok = (10 - wk.wkts2 == wk.margin)
print(f'\nWICKET-margin matches (no DLS): {len(wk)}; exact match {wk_ok.sum()} ({wk_ok.mean():.1%})')
print(wk[~wk_ok][['match_id','comp_name','result','runs1','runs2','wkts2','margin']].head(15).to_string())
chase_ok = (wk.runs2 > wk.runs1)
print('chasing team passed target in wicket wins:', chase_ok.mean())
# winner consistency
m['bat1']=m.team1; m['bat2']=m.team2
w_ok = m[ok & m.win_team_id.notna() & ~m.dls]
pred_winner = np.where(w_ok.runs1>w_ok.runs2, w_ok.bat1, np.where(w_ok.runs2>w_ok.runs1, w_ok.bat2, -1))
print('\nwinner = higher scorer (no DLS):', (pred_winner==w_ok.win_team_id).mean(), 'n=', len(w_ok))
bad = w_ok[pred_winner!=w_ok.win_team_id]; print(bad[['match_id','comp_name','result','runs1','runs2','win_team_id','bat1','bat2']].to_string())
print('\nDLS/revised matches:', m.dls.sum()); print(m[m.dls][['match_id','comp_name','first_inn_revised_overs','second_inn_revised_overs','revised_target','runs1','runs2','legal1','legal2','result']].to_string())
print('\nmatches without bbb:'); print(m[m.runs1.isna()][['match_id','comp_name','result']].to_string())
print('\nties/super overs:'); print(m[m.result.str.contains('Tie|Super|tie|super', na=False)][['match_id','comp_name','result']].to_string())
print('\nno result but has bbb:', (m.result.str.contains('No Result|Abandon',na=False) & m.runs1.notna()).sum())
print('innings 2 missing but innings1 present:', (m.runs1.notna() & m.runs2.isna()).sum())
m.to_csv('outputs/match_summary.csv', index=False)
