"""Wins, not runs: turn each player's value into win probability, using how much one run moves the win chance at that moment
   (estimated from the win-probability model, by Pressure Index band). Reported per 14-match season vs an average player."""
import pandas as pd, numpy as np, json
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
R['band'] = pd.qcut(R.PI, 20, labels=False, duplicates='drop')
rate = {}
for b, x in R[R.usable].groupby('band'):
    X = np.column_stack([np.ones(len(x)), x.total_runs.values, x.is_wicket.astype(float).values])
    coef, *_ = np.linalg.lstsq(X, x.wpa.values, rcond=None); rate[b] = coef[1]
R['wp_per_run'] = R.band.map(rate)
print('win chance per run (percentage points) by Pressure Index band:', {int(k): round(v*100,2) for k,v in list(rate.items())[::4]}, '... top band', round(rate[max(rate)]*100,2))
OUT = {}
for role, pid, col in [('bat','striker_id','bat_v_opp'), ('bowl','bowler_id','bowl_v_full')]:
    D = R[R.faced] if role=='bat' else R
    D = D.assign(wins = D[col]*D.wp_per_run)
    g = D.groupby(pid).agg(wins=('wins','sum'), m=('match_id','nunique'), name=(('striker_name' if role=='bat' else 'bowler_name'),'first'))
    g['wins_per_season'] = g.wins/g.m*14
    sel = pd.read_csv(f'outputs/v3/selection_{role}_v3.csv', index_col=0)
    t = g.loc[g.index.intersection(sel.index)].sort_values('wins_per_season', ascending=False)
    t.to_csv(f'outputs/v3/wins_{role}.csv')
    top = sel.head(10).index
    print(f'\n{role.upper()}: wins added per 14-match season vs an average player (top 10 by the v3 selection rule)')
    print(g.loc[top, ['name','wins_per_season','m']].round(2).to_string())
    OUT[role] = g.loc[top, ['name','wins_per_season']].round(3).to_dict('records')
json.dump(OUT, open('outputs/v3/wins_summary.json','w'), indent=1)
