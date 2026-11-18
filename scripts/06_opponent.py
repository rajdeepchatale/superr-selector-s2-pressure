"""Opponent-strength adjustment for T20Is: runs vs a weak attack count for less (and vice versa).
   Team effect = mean value of all balls against that team (T20I full-member games), shrunk toward 0."""
import pandas as pd, numpy as np
U = pd.read_pickle('outputs/balls_val.pkl')
T = U[U.comp_group.isin(['IPL','T20I_FULL'])].copy()
K = 3000  # shrinkage: a team needs ~3000 balls of evidence to get half its raw effect
def team_eff(df, val, team_col):
    g = df.groupby(team_col)[val].agg(['sum','count'])
    return (g['sum']/(g['count']+K)).rename(f'adj_{val}')
t = T[T.comp_group=='T20I_FULL']
bat_vs_bowlteam = team_eff(t[t.faced], 'bat_val', 'bowling_team_id')    # batters do better vs weak bowling teams
bowl_vs_batteam = team_eff(t, 'bowl_val', 'batting_team_id')            # bowlers do better vs weak batting teams
names = pd.read_csv('data/raw/teams.csv').drop_duplicates('team_id').set_index('team_id').team_name
show = pd.DataFrame({'bat_val_vs_their_bowling(per100)': bat_vs_bowlteam*100, 'bowl_val_vs_their_batting(per24)': bowl_vs_batteam*24})
show.index = show.index.map(names); print(show.round(2).sort_values(show.columns[0]).to_string())
T = T.merge(bat_vs_bowlteam, left_on='bowling_team_id', right_index=True, how='left').merge(bowl_vs_batteam, left_on='batting_team_id', right_index=True, how='left')
T.loc[T.comp_group=='IPL', ['adj_bat_val','adj_bowl_val']] = 0.0
T[['adj_bat_val','adj_bowl_val']] = T[['adj_bat_val','adj_bowl_val']].fillna(0)
T['bat_val_adj'] = T.bat_val - T.adj_bat_val
T['bowl_val_adj'] = T.bowl_val - T.adj_bowl_val
T.to_pickle('outputs/rated_balls.pkl')
print('rated balls saved:', len(T))
