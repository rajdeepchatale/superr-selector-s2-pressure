"""Build one row per delivery with the match state BEFORE the ball and the outcome OF the ball."""
import pandas as pd, numpy as np, re
R='data/raw/'
b = pd.read_csv(R+'ball_by_ball.csv', low_memory=False)
mat = pd.read_csv(R+'matches.csv'); comp = pd.read_csv(R+'competitions.csv')

FULL = {'India','Australia','England','South Africa','New Zealand','Pakistan','Sri Lanka',
        'West Indies','Bangladesh','Afghanistan','Ireland','Zimbabwe'}
m = mat.merge(comp[['comp_id','comp_name','match_format']], on='comp_id')
m['year'] = pd.to_datetime(m.match_date).dt.year
def group(r):
    if r.comp_name.startswith('IPL'): return 'IPL'
    if r.match_format=='T20': return 'A_TEAM'          # Emerging / Rising Stars (A sides + associates)
    return 'T20I_FULL' if (r.home_team in FULL and r.away_team in FULL) else 'T20I_ASSOC'
m['comp_group'] = m.apply(group, axis=1)
res = m.result.fillna('')
m['is_tie'] = res.str.contains(r'tie|super over|eliminator', case=False)
m['is_dls'] = m[['first_inn_revised_overs','second_inn_revised_overs','revised_target']].notna().any(axis=1) | res.str.contains(r'D/L|DLS', case=False)
m['no_result'] = res.str.contains(r'no result|abandon', case=False) | (m.win_team_id.isna() & ~m.is_tie)

b = b[b.innings<=2].copy()
b = b.merge(m[['match_id','comp_id','comp_name','comp_group','year','match_date','is_tie','is_dls','no_result','win_team_id','knock_out','stage','venue_id']], on='match_id', how='left')
b = b.sort_values(['match_id','innings','innings_ball_num']).reset_index(drop=True)

ILLEGAL = ['wide','Overstep','other']
b['legal'] = ~b.extras_type.isin(ILLEGAL)
b['is_wide'] = b.extras_type.eq('wide')
b['is_noball'] = b.extras_type.isin(['Overstep','other'])
b['total_runs'] = b.runs + b.extras1_runs + b.extras_2_runs
b['bat_runs'] = b.runs
b['bowler_runs'] = b.runs + np.where(b.extras_type.isin(ILLEGAL), b.extras1_runs, 0)
b['faced'] = ~b.is_wide                      # balls faced by striker (no-balls count, wides don't)
BOWLER_W = ['Caught','Bowled','LBW','Stump','Hit Wicket']
b['bowler_wkt'] = b.is_wicket & b.dismissal_type.isin(BOWLER_W)
b['striker_out'] = b.is_wicket & (b.dismissed_player_id==b.striker_id)
b['nonstriker_out'] = b.is_wicket & (b.dismissed_player_id==b.non_striker_id)

g = b.groupby(['match_id','innings'])
b['score_before'] = g.total_runs.cumsum() - b.total_runs
b['wkts_before'] = g.is_wicket.cumsum() - b.is_wicket.astype(int)
b['legal_before'] = g.legal.cumsum() - b.legal.astype(int)
b['balls_left'] = 120 - b.legal_before
b['over_no'] = b.legal_before//6 + 1
b['phase'] = pd.cut(b.over_no, [0,6,15,20], labels=['PP','MID','DEATH'])

inn_tot = b.groupby(['match_id','innings']).agg(inn_runs=('total_runs','sum'), inn_wkts=('is_wicket','sum'), inn_legal=('legal','sum'), bat_team=('batting_team_id','first')).reset_index()
first = inn_tot[inn_tot.innings==1].rename(columns={'inn_runs':'first_total','bat_team':'team_bat_first'})[['match_id','first_total','team_bat_first']]
b = b.merge(first, on='match_id', how='left')
b['target'] = np.where(b.innings==2, b.first_total+1, np.nan)
b['runs_needed'] = b.target - b.score_before
b['rrr'] = np.where(b.innings==2, b.runs_needed / np.maximum(b.balls_left,1) * 6, np.nan)
b['crr'] = b.score_before / np.maximum(b.legal_before,1) * 6
b['wkts_in_hand'] = 10 - b.wkts_before

# league-season par first-innings total (completed, non-DLS 1st innings of full 120 balls or all out)
fi = inn_tot[inn_tot.innings==1].merge(m[['match_id','comp_group','year','is_dls','no_result']], on='match_id')
fi = fi[~fi.is_dls & ~fi.no_result & ((fi.inn_legal>=120)|(fi.inn_wkts>=10))]
par = fi.groupby(['comp_group','year']).inn_runs.agg(['mean','count']).reset_index().rename(columns={'mean':'par'})
print('par by league-season:\n', par.to_string())
b = b.merge(par[['comp_group','year','par']], on=['comp_group','year'], how='left')
b['par'] = b.par.fillna(fi.inn_runs.mean())

# outcome label from batting team's perspective (regulation time: tie = 0.5)
b['bat_team_won'] = np.where(b.is_tie, 0.5, (b.win_team_id==b.batting_team_id).astype(float))
b.loc[b.no_result, 'bat_team_won'] = np.nan
b['usable'] = ~b.is_dls & ~b.no_result & b.win_team_id.notna() | (b.is_tie & ~b.is_dls)
b.loc[b.no_result, 'usable'] = False
print('usable deliveries:', b.usable.sum(), 'of', len(b), '| usable matches:', b[b.usable].match_id.nunique())
print(b[b.usable].groupby('comp_group').match_id.nunique())
b.to_pickle('outputs/balls.pkl')
m.to_csv('outputs/matches_enriched.csv', index=False)
