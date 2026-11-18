"""How each pick could strengthen the RR squad (the rules page asks for this).
   1) Where RR lost most under pressure in IPL 2025-26: team pressure value by phase, batting and bowling, against the other nine teams.
   2) Where each top-10 player does his pressure work (phase share) and how well (his own value there).
   3) Who is already in RR's IPL 2026 squad (from the data pack's squad lists).
   Values are the rating's own per-ball values (batting: bat_v_opp, bowling: bowl_v_full), weighted by Pressure Index/100."""
import pandas as pd, numpy as np, json
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl'); R = R[R.PI.notna()]
R['w'] = R.PI/100
RR = 3; PH = ['PP', 'MID', 'DEATH']; UNIT = {'bat': 100, 'bowl': 24}
I = R[(R.ipl == 1) & (R.year >= 2025)]
OUT = {'seasons': 'IPL 2025-26'}
cells = []
for role, team, col, rows in [('bat', 'batting_team_id', 'bat_v_opp', I[I.faced]), ('bowl', 'bowling_team_id', 'bowl_v_full', I)]:
    g = rows.assign(wv=rows.w*rows[col]).groupby([team, 'phase'])[['wv', 'w']].sum()
    lg = rows.assign(wv=rows.w*rows[col]).groupby('phase')[['wv', 'w']].sum(); lg_rate = lg.wv/lg.w
    for ph in PH:
        t = g.xs(ph, level='phase'); rate = (t.wv/t.w - lg_rate[ph])*UNIT[role]          # vs the league average in that phase
        total = (t.wv - lg_rate[ph]*t.w)                                                  # runs, pressure-weighted, over the two seasons
        rank = int(rate.rank(ascending=False)[RR])
        cells.append(dict(role=role, phase=ph, rr_rate=float(rate[RR]), rr_rank=rank, teams=int(len(rate)),
                          rr_total_runs=float(total[RR]), best_rate=float(rate.max()), worst_rate=float(rate.min())))
OUT['rr_cells'] = cells
# RR results in those seasons, for context
m = pd.read_csv('data/raw/matches.csv'); c = pd.read_csv('data/raw/competitions.csv')
mm = m.merge(c[['comp_id', 'comp_name']], on='comp_id'); mm = mm[mm.comp_name.isin(['IPL 2025', 'IPL 2026']) & ((mm.home_team_id == RR) | (mm.away_team_id == RR))]
mm = mm[mm.result.astype(str).str.lower().str.contains('won|win|beat|tie|super', regex=True) | mm.win_team_id.notna()]
OUT['rr_matches'] = {s: dict(played=int((g.comp_name == s).sum()), won=int((g.win_team_id == RR).sum())) for s, g in mm.groupby('comp_name')}
# close games: matches decided by the last over or by 10 runs or fewer would need margins; keep simple: count balls RR played at PI>=95
# players
sel = {'bat': pd.read_csv('outputs/v3/selection_bat_v3.csv', index_col=0), 'bowl': pd.read_csv('outputs/v3/selection_bowl_v3.csv', index_col=0)}
sq = pd.read_csv('data/raw/competition_team_player_mapping.csv'); sq = sq[sq.comp_name.eq('IPL 2026') & sq.team_id.eq(RR)]
OUT['rr_squad_2026_size'] = int(len(sq))
players = []
for role, pid, col, rows in [('bat', 'striker_id', 'bat_v_opp', R[R.faced]), ('bowl', 'bowler_id', 'bowl_v_full', R)]:
    top = sel[role].sort_values('pick_rank').head(10)
    lg = rows.assign(wv=rows.w*rows[col]).groupby('phase')[['wv', 'w']].sum(); lg_rate = lg.wv/lg.w
    for p, r in top.iterrows():
        x = rows[rows[pid] == p].assign(wv=lambda d: d.w*d[col]); g = x.groupby('phase')[['wv', 'w']].sum().reindex(PH).fillna(0)
        share = g.w/g.w.sum()
        k = 8.0                                            # shrink each phase toward his overall level with 8 balls of pressure weight
        overall = g.wv.sum()/g.w.sum()
        rate = ((g.wv + k*overall)/(g.w + k) - lg_rate)*UNIT[role]
        spin = None if role == 'bat' else float(x.spin.mean())
        pb = x[x.PI >= 80].phase.value_counts().reindex(PH).fillna(0)                     # pressure balls (Index 80+) by phase
        players.append(dict(role=role, pid=int(p), name=r['name'], pick=int(r.pick_rank), rating=float(r.rating),
                            pballs={ph: int(pb[ph]) for ph in PH}, share_7_20=float((pb['MID'] + pb['DEATH'])/pb.sum()),
                            share={ph: float(share[ph]) for ph in PH}, rate={ph: float(rate[ph]) for ph in PH},
                            main_phase=str(share.idxmax()), spin_share=spin, in_rr_2026=bool(p in set(sq.player_id))))
OUT['players'] = players
json.dump(OUT, open('outputs/v3/squad_fit.json', 'w'), indent=1)
print('RR, IPL 2025-26, pressure value vs league average in that phase (bat per 100 balls, bowl per 24), rank of 10')
for c_ in cells: print(f"  {c_['role']:4s} {c_['phase']:5s} {c_['rr_rate']:+6.2f}  rank {c_['rr_rank']:2d}/{c_['teams']}  total {c_['rr_total_runs']:+6.1f} runs  (best {c_['best_rate']:+.2f}, worst {c_['worst_rate']:+.2f})")
print(OUT['rr_matches'])
for p in players:
    sh = ' '.join(f"{ph} {100*p['share'][ph]:3.0f}%/{p['rate'][ph]:+5.1f}" for ph in PH)
    print(f"  {p['role']:4s} {p['pick']:2d} {p['name']:22s} main {p['main_phase']:5s} | {sh} | spin {p['spin_share'] if p['spin_share'] is None else round(p['spin_share'],2)} | RR 2026 {p['in_rr_2026']}")
