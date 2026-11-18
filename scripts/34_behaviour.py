"""Behaviour under pressure, not just results. For each measure: is it a repeatable trait? (split-half by matches)
   A) Bowlers' execution: missed deliveries (full toss, beamer, wide, no-ball) above what's normal for that over, and pace change.
   B) Bad-day rate: how often a player has a costly pressure innings or spell (bottom 10% of all pressure performances).
   C) Batters under a dot-ball squeeze: what happens after 2+ dots in a row on pressure balls."""
import pandas as pd, numpy as np, json
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
rng = np.random.default_rng(21); MS = R.match_id.unique(); SPLITS = [set(rng.choice(MS, len(MS)//2, replace=False)) for _ in range(100)]
def wcorr(x,y,w):
    x,y,w=map(np.asarray,(x,y,w)); mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def split_half(df, pid, num, den, players):
    """df rows = (player, match) with numerator/denominator sums; returns mean split-half correlation of num/den"""
    df = df[df[pid].isin(players)]; out=[]
    for h in SPLITS:
        a = df[df.match_id.isin(h)].groupby(pid)[[num,den]].sum(); b = df[~df.match_id.isin(h)].groupby(pid)[[num,den]].sum()
        j = a.join(b, lsuffix='1', rsuffix='2', how='inner'); j = j[(j[den+'1']>0)&(j[den+'2']>0)]
        out.append(wcorr(j[num+'1']/j[den+'1'], j[num+'2']/j[den+'2'], np.sqrt(j[den+'1']*j[den+'2'])))
    return float(np.mean(out)), float(np.mean(np.array(out)>0))
OUT = {}
sel_b = pd.read_csv('outputs/v3/selection_bowl_v3.csv', index_col=0); sel_a = pd.read_csv('outputs/v3/selection_bat_v3.csv', index_col=0)
BOWLERS, BATTERS = set(sel_b.index), set(sel_a.index)          # the eligible pools (120+ / 100+ pressure balls)
P = R.PI >= 80
# ---------- A) execution
R['miss'] = (R.delivery_style.isin(['Full Toss','Beamer']) | R.is_wide.astype(bool) | R.is_noball.astype(bool)).astype(int)
R['exp_miss'] = R.groupby(['over_no','spin','comp_group']).miss.transform('mean')
R['miss_ae'] = R.miss - R.exp_miss
bw = R.assign(P=P).groupby(['bowler_id','match_id','P']).agg(m=('miss_ae','sum'), n=('miss','size')).reset_index()
bP = bw[bw.P]; bN = bw[~bw.P]
OUT['exec_P_repeat'] = split_half(bP, 'bowler_id', 'm', 'n', BOWLERS)
OUT['exec_N_repeat'] = split_half(bN, 'bowler_id', 'm', 'n', BOWLERS)
gap = bP.merge(bN, on=['bowler_id','match_id'], how='outer', suffixes=('P','N')).fillna(0)
# pressure execution gap: rate on pressure balls minus rate on normal balls (needs both in each half)
def gap_repeat(players):
    df = gap[gap.bowler_id.isin(players)]; out=[]
    for h in SPLITS:
        r=[]
        for part in [df[df.match_id.isin(h)], df[~df.match_id.isin(h)]]:
            s = part.groupby('bowler_id')[['mP','nP','mN','nN']].sum(); s = s[(s.nP>=30)&(s.nN>=60)]; r.append(s.mP/s.nP - s.mN/s.nN)
        j = pd.concat(r, axis=1, join='inner'); out.append(np.corrcoef(j.iloc[:,0], j.iloc[:,1])[0,1])
    return float(np.mean(out)), float(np.mean(np.array(out)>0))
OUT['exec_gap_repeat'] = gap_repeat(BOWLERS)
# results repeatability on the same split scheme, for comparison (pressure value per pressure ball)
R['bowl_Pv'] = np.where(P, R.bowl_v_full, 0.0); R['bat_Pv'] = np.where(P & R.faced, R.bat_v_opp, 0.0)
rb = R[P].groupby(['bowler_id','match_id']).agg(v=('bowl_v_full','sum'), n=('bowl_v_full','size')).reset_index()
OUT['results_P_repeat_bowl'] = split_half(rb, 'bowler_id', 'v', 'n', BOWLERS)
# does execution go with results? (bowler level, pressure balls)
e = bP.groupby('bowler_id')[['m','n']].sum(); e = e.loc[e.index.intersection(list(BOWLERS))]
res = rb.groupby('bowler_id')[['v','n']].sum().reindex(e.index)
OUT['exec_vs_results_corr'] = float(wcorr(e.m/e.n, res.v/res.n, e.n))
OUT['league_miss_rate_P'] = float(R[P].miss.mean()); OUT['league_miss_rate_N'] = float(R[~P].miss.mean())
OUT['league_miss_ae_P'] = float(R[P].miss_ae.mean())
# pace change under pressure (pace bowlers, real speeds only), within the same over number
sp = pd.to_numeric(R.bowl_speed, errors='coerce'); R['spd'] = sp.where((sp>=95)&(sp<=165))
pc = R[(R.spin==0)&R.spd.notna()].copy(); pc['spd_rel'] = pc.spd - pc.groupby(['bowler_id','over_no']).spd.transform('mean')
pw = pc.assign(P=pc.PI>=80).groupby(['bowler_id','match_id','P']).agg(s=('spd_rel','sum'), n=('spd_rel','size')).reset_index()
OUT['pace_P_repeat'] = split_half(pw[pw.P], 'bowler_id', 's', 'n', BOWLERS)
OUT['league_pace_change_P'] = float(pc[pc.PI>=80].spd_rel.mean())
# per-bowler table
tabA = pd.DataFrame({'name': R.drop_duplicates('bowler_id').set_index('bowler_id').bowler_name.reindex(e.index),
                     'miss_P_pct': 100*R[P].groupby('bowler_id').miss.mean().reindex(e.index),
                     'miss_N_pct': 100*R[~P].groupby('bowler_id').miss.mean().reindex(e.index),
                     'miss_ae_P_pct': 100*(e.m/e.n), 'nP': e.n,
                     'pace_change_P': pc[pc.PI>=80].groupby('bowler_id').spd_rel.mean().reindex(e.index),
                     'pace_nP': pc[pc.PI>=80].groupby('bowler_id').spd_rel.size().reindex(e.index)})
k = 150  # shrink miss-above-expected toward 0 with 150 balls of prior weight
tabA['miss_ae_P_shrunk'] = 100*(e.m/(e.n+k))
tabA.to_csv('outputs/v3/execution_bowlers.csv')
# ---------- B) bad-day rate
for role, pid, col, minb in [('bat','striker_id','bat_v_opp',4), ('bowl','bowler_id','bowl_v_full',6)]:
    D = R[P & R.faced] if role=='bat' else R[P]
    pm = D.groupby([pid,'match_id']).agg(v=(col,'sum'), n=(col,'size')).reset_index(); pm = pm[pm.n>=minb]
    lo, hi = pm.v.quantile(0.10), pm.v.quantile(0.90)
    pm['bad'] = (pm.v<=lo).astype(int); pm['good'] = (pm.v>=hi).astype(int); pm['one'] = 1
    pool = BATTERS if role=='bat' else BOWLERS
    OUT[f'badday_threshold_{role}'] = float(lo)
    OUT[f'badday_repeat_{role}'] = split_half(pm, pid, 'bad', 'one', pool)
    OUT[f'goodday_repeat_{role}'] = split_half(pm, pid, 'good', 'one', pool)
    OUT[f'avg_inn_repeat_{role}'] = split_half(pm, pid, 'v', 'one', pool)
    t = pm[pm[pid].isin(pool)].groupby(pid).agg(bad=('bad','sum'), good=('good','sum'), inns=('one','sum'))
    t['bad_rate'] = (t.bad + 10*0.10)/(t.inns+10); t['good_rate'] = (t.good + 10*0.10)/(t.inns+10)
    t.to_csv(f'outputs/v3/badday_{role}.csv')
# ---------- C) dot-ball squeeze (batters)
F = R[R.faced].sort_values(['match_id','innings','innings_ball_num']).copy()
F['dot'] = ((F.bat_runs==0)&(~F.striker_out.astype(bool))).astype(int)
F['prev_dots'] = 0
grp = F.groupby(['match_id','innings','striker_id'])
# consecutive dots faced by this striker right before this ball
def run_len(s):
    out=np.zeros(len(s),dtype=int); c=0
    for i,v in enumerate(s.values):
        out[i]=c; c = c+1 if v==1 else 0
    return pd.Series(out, index=s.index)
F['prev_dots'] = grp.dot.transform(run_len)
FP = F[F.PI>=80]
sq = FP[FP.prev_dots>=2]; nsq = FP[FP.prev_dots==0]
OUT['squeeze_balls'] = int(len(sq))
OUT['squeeze_out_rate'] = float(sq.striker_out.mean()); OUT['squeeze_exp_out'] = float(sq.P_out.mean())
OUT['nosq_out_rate'] = float(nsq.striker_out.mean()); OUT['nosq_exp_out'] = float(nsq.P_out.mean())
OUT['squeeze_runs'] = float(sq.bat_runs.mean()); OUT['squeeze_exp_runs'] = float(sq.E_bat_runs.mean())
OUT['nosq_runs'] = float(nsq.bat_runs.mean()); OUT['nosq_exp_runs'] = float(nsq.E_bat_runs.mean())
sqm = sq.assign(o=sq.striker_out.astype(int)-sq.P_out, v=sq.bat_v_opp).groupby(['striker_id','match_id']).agg(o=('o','sum'), v=('v','sum'), n=('o','size')).reset_index()
OUT['squeeze_out_repeat'] = split_half(sqm, 'striker_id', 'o', 'n', BATTERS)
OUT['squeeze_value_repeat'] = split_half(sqm, 'striker_id', 'v', 'n', BATTERS)
ts = sqm[sqm.striker_id.isin(BATTERS)].groupby('striker_id')[['o','v','n']].sum()
ts['name'] = R.drop_duplicates('striker_id').set_index('striker_id').striker_name.reindex(ts.index)
ts.to_csv('outputs/v3/squeeze_batters.csv')
json.dump(OUT, open('outputs/v3/behaviour_summary.json','w'), indent=1)
for k,v in OUT.items(): print(f'{k:28s}', v if not isinstance(v,float) else round(v,4))
