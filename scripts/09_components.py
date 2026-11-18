import pandas as pd, numpy as np, sys
sys.path.insert(0,'scripts'); from lib_ratings import *
T = pd.read_pickle('outputs/rated_balls.pkl')
T['bat_runs_ae'] = np.where(T.faced, T.bat_runs - T.E_bat_runs - T.adj_bat_val, np.nan)
T['bat_outs_ae'] = np.where(T.faced, -(T.striker_out.astype(int) - T.P_out), np.nan)          # + = fewer outs than expected
T['bat_wkt_part'] = np.where(T.faced, -T.wkt_cost*(T.striker_out.astype(int)-T.P_out), np.nan)
T['bat_runs_raw'] = np.where(T.faced, T.bat_runs, np.nan); T['bat_out_raw'] = np.where(T.faced, -T.striker_out.astype(int), np.nan)
T['bat_val_half'] = np.where(T.faced, (T.bat_runs-T.E_bat_runs) - 0.5*T.wkt_cost*(T.striker_out.astype(int)-T.P_out) - T.adj_bat_val, np.nan)
T['bowl_runs_ae'] = T.E_bowl_runs - T.bowler_runs - T.adj_bowl_val
T['bowl_wkts_ae'] = T.bowler_wkt.astype(int) - T.P_bwkt
T['bowl_wkt_part'] = T.wkt_cost*(T.bowler_wkt.astype(int) - T.P_bwkt)
T['bowl_econ_raw'] = -T.bowler_runs; T['bowl_wkt_raw'] = T.bowler_wkt.astype(int)
rng = np.random.default_rng(1)
def rel(role, col, minp, scope='P', splits=40):
    pm = player_match_table(T, role, val_col=col)
    pm = pm[pm.P] if scope=='P' else pm
    a = pm.groupby('pid').n.sum(); keep = a[a>=minp].index; pm = pm[pm.pid.isin(keep)]
    ms = pm.match_id.unique(); out=[]
    for s in range(splits):
        h = set(rng.choice(ms, len(ms)//2, replace=False))
        g1 = pm[pm.match_id.isin(h)].groupby('pid')[['v','n']].sum(); g2 = pm[~pm.match_id.isin(h)].groupby('pid')[['v','n']].sum()
        j = g1.join(g2, lsuffix='1', rsuffix='2', how='inner'); j=j[(j.n1>=minp/4)&(j.n2>=minp/4)]
        x, y, w = j.v1/j.n1, j.v2/j.n2, np.sqrt(j.n1*j.n2)
        mx,my=np.average(x,weights=w),np.average(y,weights=w)
        out.append(np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w)))
    return np.mean(out), len(keep)
print('Split-half reliability (corr between two random halves of matches). Higher = more stable skill.')
for role, cols, minps in [('bat',['bat_val_adj','bat_v','bat_val_half','bat_runs_ae','bat_outs_ae','bat_wkt_part','bat_runs_raw','bat_out_raw'],[100,200]),
                          ('bowl',['bowl_val_adj','bowl_v','bowl_runs_ae','bowl_wkts_ae','bowl_wkt_part','bowl_econ_raw','bowl_wkt_raw'],[120,240])]:
    for scope in ['P','ALL']:
        for mp in minps:
            mp2 = mp if scope=='P' else mp*5
            row = []
            for c in cols:
                r, n = rel(role, c, mp2, scope); row.append(f'{c}={r:+.2f}')
            print(f'{role} | scope={scope:3s} | min balls {mp2:4d} | players {n:3d} | ' + '  '.join(row))
