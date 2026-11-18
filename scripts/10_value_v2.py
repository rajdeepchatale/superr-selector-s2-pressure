"""Final per-ball value: runs above expected + 8 runs per wicket above expected (WP-derived exchange rate),
   with opponent-strength adjustment for T20Is."""
import pandas as pd, numpy as np
W = 8.0
U = pd.read_pickle('outputs/balls_val.pkl')
T = U[U.comp_group.isin(['IPL','T20I_FULL'])].copy()
T['bat_v'] = np.where(T.faced, (T.bat_runs - T.E_bat_runs) - W*(T.striker_out.astype(int) - T.P_out), np.nan)
T['bowl_v'] = (T.E_bowl_runs - T.bowler_runs) + W*(T.bowler_wkt.astype(int) - T.P_bwkt)
K = 3000
t = T[T.comp_group=='T20I_FULL']
eb = t[t.faced].groupby('bowling_team_id').bat_v.agg(['sum','count']); eb = (eb['sum']/(eb['count']+K)).rename('adj_b')
ew = t.groupby('batting_team_id').bowl_v.agg(['sum','count']); ew = (ew['sum']/(ew['count']+K)).rename('adj_w')
T = T.drop(columns=[c for c in ['adj_b','adj_w'] if c in T]).merge(eb, left_on='bowling_team_id', right_index=True, how='left').merge(ew, left_on='batting_team_id', right_index=True, how='left')
T.loc[T.comp_group=='IPL', ['adj_b','adj_w']] = 0.0; T[['adj_b','adj_w']] = T[['adj_b','adj_w']].fillna(0)
T['bat_val_adj'] = T.bat_v - T.adj_b
T['bowl_val_adj'] = T.bowl_v - T.adj_w
names = pd.read_csv('data/raw/teams.csv').drop_duplicates('team_id').set_index('team_id').team_name
print('opponent adj (bat per100 vs their bowling | bowl per24 vs their batting):')
print(pd.DataFrame({'bat':eb*100,'bowl':ew*24}).rename(index=names).round(2).sort_values('bat').T.to_string())
T.to_pickle('outputs/rated_balls.pkl'); print('saved', len(T))
