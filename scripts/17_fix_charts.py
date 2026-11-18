import pandas as pd, numpy as np, sys, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0,'scripts'); from lib_pwi import *
exec(open('scripts/15_charts.py').read().split("A = pd.read_pickle")[0].split("from lib_pwi import *")[1])
A = pd.read_pickle('outputs/rated_balls.pkl'); OUT='outputs/charts/'
# --- fig3: correct ball labels (legal ball number; extras marked)
t = A[(A.match_id==50359)&(A.innings==2)&(A.balls_left<=12)].copy()
lab_x, lab_o = [], []
for r in t.itertuples():
    ball = f'{int(r.over_no)-1}.{int(r.legal_before % 6)+1}'
    if r.is_wide: lab_x.append(ball+'\nwide'); lab_o.append(f'wd+{int(r.total_runs)-1}' if r.total_runs>1 else 'wd')
    elif r.is_noball: lab_x.append(ball+'\nno-ball'); lab_o.append(f'nb+{int(r.total_runs)-1}')
    else: lab_x.append(ball); lab_o.append('W' if r.is_wicket else str(int(r.total_runs)))
fig, ax = plt.subplots(figsize=(11.5,4))
x = np.arange(len(t)); wp = t.wp_after.values*100
ax.plot(np.r_[-1,x], np.r_[t.wp_before.values[0]*100, wp], color=S1, lw=2, marker='o', ms=6, markerfacecolor=S1, markeredgecolor=SURF, markeredgewidth=1.5)
for i,(o,y) in enumerate(zip(lab_o, wp)):
    ax.annotate(o, (i,y), textcoords='offset points', xytext=(0,9), ha='center', fontsize=9, color=('#d03b3b' if o=='W' else INK), fontweight='bold' if o in ('W','4','6') else 'normal')
ax.axhline(50, color=MUTE, lw=0.8); ax.set_xticks(np.r_[-1,x]); ax.set_xticklabels(['start']+lab_x, fontsize=7.5)
ax.set_ylim(0,100); ax.set_ylabel('Chasing side win chance (%)')
ax.set_title('What pressure looks like: IPL 2026, LSG chasing KKR, last two overs (match tied; every ball Pressure Index 97+)', loc='left', fontsize=11)
fig.savefig(OUT+'fig3_real_finish.png', dpi=200, bbox_inches='tight'); plt.close(fig)
# --- fig4: one consistent repeatability chart (same eligible players, same procedure, 40 splits)
rng = np.random.default_rng(21)
def wcorr(x,y,w):
    m=~(np.isnan(x)|np.isnan(y)); x,y,w=x[m],y[m],w[m]; mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
res = {}
for role in ['bat','bowl']:
    d = role_frame(A, role); g1 = match_agg(d, alpha=1); g0 = match_agg(d, alpha=0)
    a,_ = ratings(g1, 100 if role=='bat' else 120, 10, inn_min=4 if role=='bat' else 6); keep = a[a.eligible].index
    g1 = g1[g1.pid.isin(keep)]; g0 = g0[g0.pid.isin(keep)].rename(columns={'wv':'wv0','w':'w0'})[['pid','match_id','wv0','w0']]
    g = g1.merge(g0, on=['pid','match_id']); ms = g.match_id.unique(); r = {k:[] for k in ['ponly','rating','equal','gap']}
    cols = ['wv','w','wv0','w0','Pv','Pn','Nv','Nn']
    for s in range(40):
        h = set(rng.choice(ms, len(ms)//2, replace=False))
        q1 = g[g.match_id.isin(h)].groupby('pid')[cols].sum(); q2 = g[~g.match_id.isin(h)].groupby('pid')[cols].sum()
        j = q1.join(q2, lsuffix='1', rsuffix='2', how='inner'); j = j[(j.Pn1>0)&(j.Pn2>0)&(j.Nn1>0)&(j.Nn2>0)]; w = np.sqrt(j.w1*j.w2).values
        r['rating'].append(wcorr((j.wv1/j.w1).values,(j.wv2/j.w2).values,w)); r['equal'].append(wcorr((j.wv01/j.w01).values,(j.wv02/j.w02).values,w))
        r['ponly'].append(wcorr((j.Pv1/j.Pn1).values,(j.Pv2/j.Pn2).values,w)); r['gap'].append(wcorr((j.Pv1/j.Pn1-j.Nv1/j.Nn1).values,(j.Pv2/j.Pn2-j.Nv2/j.Nn2).values,w))
    res[role] = {k: float(np.mean(v)) for k,v in r.items()}
print(res); json.dump(res, open('outputs/repeatability.json','w'), indent=1)
labs = ['Pressure balls only\n(top 20%; 100% weight)', 'Our Pressure Rating\n(weighted by Pressure Index;\n36% weight on top 20%)', 'Every ball equal\n(20% weight on top 20%)', '"Clutch gap"\n(pressure minus usual)']
keys = ['ponly','rating','equal','gap']
fig, ax = plt.subplots(figsize=(11,4.4)); x = np.arange(4)
for k,(role,col,lab) in enumerate([('bat',S1,'Batters'),('bowl',S2,'Bowlers')]):
    vals = [res[role][kk] for kk in keys]; xs = x + (k-0.5)*0.32
    ax.bar(xs, vals, 0.3, color=col, label=lab)
    for xi,v in zip(xs, vals): ax.text(xi, v + (0.005 if v>=0 else -0.018), f'{v:+.2f}', ha='center', fontsize=9, color=INK)
ax.axhline(0, color=MUTE, lw=0.8); ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.5); ax.grid(axis='x', visible=False)
ax.set_ylabel('Agreement between two random\nhalves of matches (correlation)'); ax.legend(frameon=False, loc='upper right')
ax.set_title('What repeats? Each player\'s matches split in two, 40 times. Pressure weighting stays stable; the "clutch gap" does not', loc='left', fontsize=11)
fig.savefig(OUT+'fig4_what_repeats.png', dpi=200, bbox_inches='tight'); plt.close(fig)
import os
for f in ['fig4_clutch_noise.png','fig7_weighting_tradeoff.png']:
    if os.path.exists(OUT+f): os.remove(OUT+f)
print(sorted(os.listdir(OUT)))
