"""All numbers the deck needs for the v3 model, in one place (outputs/v3/deck_numbers.json)."""
import pandas as pd, numpy as np, sys, json
sys.path.insert(0,'scripts'); from lib_pwi import match_agg, ratings, UNIT
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl')
names = pd.concat([R[['striker_id','striker_name']].set_axis(['pid','name'],axis=1), R[['bowler_id','bowler_name']].set_axis(['pid','name'],axis=1)]).drop_duplicates('pid').set_index('pid').name
COL = {'bat':'bat_v_opp','bowl':'bowl_v_full'}; OLDCOL = {'bat':'bat_val_adj','bowl':'bowl_val_adj'}
def wcorr(x,y,w):
    x,y,w=map(np.asarray,(x,y,w)); mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def frame(role, col, src=R):
    if role=='bat': d = src[src.faced].rename(columns={'striker_id':'pid'}); d['ball']=1
    else: d = src.rename(columns={'bowler_id':'pid'}); d['ball']=d.legal.astype(int)
    d = d.copy(); d['val'] = d[col]; return d
def top10(d, role, minp=None, **kw):
    minp = minp or (100 if role=='bat' else 120); im = 4 if role=='bat' else 6
    a,_ = ratings(match_agg(d, **kw), minp, 10, inn_min=im); e = a[a.eligible].sort_values('rating', ascending=False)
    return [names[p] for p in e.index], e
N = {}
for role in ['bat','bowl']:
    u = UNIT[role]; sel = pd.read_csv(f'outputs/v3/selection_{role}_v3.csv', index_col=0)
    ten = sel.head(10).sort_values('rating', ascending=False); nxt = sel.iloc[10:12]
    old = pd.read_csv(f'outputs/final_{role}.csv').set_index('pid')
    rows = []
    for pid, r in pd.concat([ten, nxt]).iterrows():
        o = old.loc[pid]
        row = dict(name=r['name'], rating=round(r.rating, 2 if role=='bowl' else 1), lo=round(r.rating-1.2816*r.se, 2), hi=round(r.rating+1.2816*r.se, 2),
                   p_top10=round(r.p_top10*100), Pn=int(r.Pn), rating_rank=int(r.rating_rank))
        if role=='bat': row.update(SR_P=round(o.SR_P), SR_N=round(o.SR_N), BpD_P=round(o.BpD_P,1))
        else: row.update(overs_P=round(o.overs_P,1), Econ_P=round(o.Econ_P,2), Econ_N=round(o.Econ_N,2), SRb_P=round(o.SRb_P,1))
        rows.append(row)
    N[f'{role}_table'] = rows
    # rating slide examples (raw pressure-weighted value vs shrunk rating)
    d = frame(role, COL[role]); a, pr = ratings(match_agg(d, alpha=1), 100 if role=='bat' else 120, 10, inn_min=4 if role=='bat' else 6)
    N[f'{role}_mu'] = round(pr['mu']*u, 2); N[f'{role}_tau'] = round(np.sqrt(pr['tau2'])*u, 2)
    if role=='bat':
        for nm in ['Suryakumar Yadav','Shashank Singh']:
            pid = names[names==nm].index[0]; x = a.loc[pid]
            N[f'ex_{nm.split()[0]}'] = dict(raw=round(x.pwi*u,1), rating=round(x.rating*u,1), kept=round(100*x.shrink_B), Pn=int(x.Pn))
    # repeatability of the four measures, old values vs v3 values (40 random half-splits, players with enough pressure balls)
    rng = np.random.default_rng(3); minp = 100 if role=='bat' else 120
    for tag, col in [('old', OLDCOL[role]), ('v3', COL[role])]:
        d = frame(role, col); d['P'] = d.PI>=80; d['w'] = d.PI/100; d['wv'] = d.w*d.val
        pm = d.groupby(['pid','match_id']).agg(vP=('val', lambda s: s[d.loc[s.index,'P']].sum()), nP=('P','sum'), vA=('val','sum'), nA=('val','size'), wv=('wv','sum'), w=('w','sum')).reset_index()
        pm['vN'] = pm.vA - pm.vP; pm['nN'] = pm.nA - pm.nP
        tot = pm.groupby('pid').nP.sum(); pm = pm[pm.pid.isin(tot[tot>=minp].index)]; ms = pm.match_id.unique(); out = {k:[] for k in ['gap','P','rating','equal']}
        for s in range(40):
            h = set(rng.choice(ms, len(ms)//2, replace=False))
            A = pm[pm.match_id.isin(h)].groupby('pid').sum(numeric_only=True); B = pm[~pm.match_id.isin(h)].groupby('pid').sum(numeric_only=True)
            j = A.join(B, lsuffix='1', rsuffix='2', how='inner'); j = j[(j.nP1>=10)&(j.nP2>=10)&(j.nN1>=20)&(j.nN2>=20)]
            f = {'P': lambda k: j[f'vP{k}']/j[f'nP{k}'], 'rating': lambda k: j[f'wv{k}']/j[f'w{k}'], 'equal': lambda k: j[f'vA{k}']/j[f'nA{k}'],
                 'gap': lambda k: j[f'vP{k}']/j[f'nP{k}'] - j[f'vN{k}']/j[f'nN{k}']}
            for k,fn in f.items(): out[k].append(wcorr(fn(1), fn(2), np.sqrt(j.nA1*j.nA2)))
        N[f'{role}_repeat_{tag}'] = {k: round(float(np.mean(v)),3) for k,v in out.items()}
    # out-of-time (2022-24 rating -> 2025-26 pressure-weighted value)
    for tag, col in [('old', OLDCOL[role]), ('v3', COL[role])]:
        d = frame(role, col)
        atr,_ = ratings(match_agg(d[d.year<=2024], alpha=1), 40 if role=='bat' else 50, 4, inn_min=4); ate,_ = ratings(match_agg(d[d.year>=2025], alpha=1), 40 if role=='bat' else 50, 4, inn_min=4)
        j = atr.join(ate, lsuffix='_tr', rsuffix='_te', how='inner'); j = j[(j.Pn_tr>=60)&(j.Pn_te>=40)]
        N[f'{role}_oot_{tag}'] = round(float(wcorr(j.rating_tr, j.pwi_te, j.w_te)),3)
    # stress tests vs the final v3 ten (straight sort of each variant)
    FINAL = list(ten.name); d = frame(role, COL[role]); st = {}
    st['More weight on pressure (Index²)'] = top10(d, role, alpha=2)[0]
    st['Less weight on pressure (√Index)'] = top10(d, role, alpha=0.5)[0]
    st['Recent seasons count more (2-year half-life)'] = top10(d, role, alpha=1, recency=2)[0]
    st['Pressure line at the top 25% of balls'] = top10(d, role, alpha=1, th=75)[0]
    st['Pressure line at the top 15% of balls'] = top10(d, role, alpha=1, th=85)[0]
    st['Sample minimum raised by half'] = top10(d, role, minp=150 if role=='bat' else 180, alpha=1)[0]
    st['Without the new adjustments (old values)'] = top10(frame(role, OLDCOL[role]), role, alpha=1)[0]
    dw = d.copy()
    dw['val'] = d.val - 3*(d.striker_out.astype(int)-d.P_out) if role=='bat' else d.val + 3*(d.bowler_wkt.astype(int)-d.P_bwkt)
    st['A wicket worth 11 runs instead of 8'] = top10(dw, role, alpha=1)[0]
    g = match_agg(d, alpha=1); g = g.assign(wv=g.Pv, w=g.Pn); a2,_ = ratings(g, 100 if role=='bat' else 120, 10, inn_min=4 if role=='bat' else 6)
    st['Pressure balls only, no weighting'] = [names[p] for p in a2[a2.eligible].sort_values('rating', ascending=False).index]
    cap = pd.read_pickle('outputs/pi_variants.pkl')['cap']; Rc = R.merge(cap, on=['match_id','innings','innings_ball_num'], how='left'); Rc['PI'] = Rc.PI_new
    st['IPL 2026 scoring level capped at 2025’s'] = top10(frame(role, COL[role], Rc), role, alpha=1)[0]
    N[f'{role}_stress'] = {k: dict(same=len(set(v[:10])&set(FINAL)), new_in=[x for x in v[:10] if x not in FINAL], out=[x for x in FINAL if x not in v[:10]]) for k,v in st.items()}
    if role=='bat':   # Kohli vs nearest rivals under heavier pressure weighting
        tests = {'Index²': top10(d, role, alpha=2)[0][:10], 'Index³': top10(d, role, alpha=3)[0][:10], 'pressure only': st['Pressure balls only, no weighting'][:10]}
        N['kohli_tests'] = {nm: sum(nm in v for v in tests.values()) for nm in ['Virat Kohli','Cameron Green','Nicholas Pooran','Shashank Singh']}
# who-you-faced: opponent quality on pressure vs other balls
P = R.PI>=80
N['opp_on_pressure'] = dict(bat_per100_P=round(float(-R[P&R.faced].bat_oppq.mean()*100),2), bat_per100_N=round(float(-R[~P&R.faced].bat_oppq.mean()*100),2),
                            bowl_per24_P=round(float(-R[P].bowl_oppq.mean()*24),2), bowl_per24_N=round(float(-R[~P].bowl_oppq.mean()*24),2))
json.dump(N, open('outputs/v3/deck_numbers.json','w'), indent=1, ensure_ascii=False)
for k,v in N.items():
    if k.endswith('_table'): print(k); [print('  ', r) for r in v]
    elif k.endswith('_stress'): print(k); [print('   ', kk, vv) for kk,vv in v.items()]
    else: print(k, v)
