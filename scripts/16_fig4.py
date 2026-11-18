import pandas as pd, numpy as np, sys, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'scripts'); from lib_pwi import *
from matplotlib.colors import LinearSegmentedColormap
exec(open('scripts/15_charts.py').read().split("A = pd.read_pickle")[0].split("from lib_pwi import *")[1])
A = pd.read_pickle('outputs/rated_balls.pkl'); rng = np.random.default_rng(21)
def wcorr(x,y,w):
    m=~(np.isnan(x)|np.isnan(y)); x,y,w=x[m],y[m],w[m]; mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
res = {}
for role in ['bat','bowl']:
    d = role_frame(A, role); g = match_agg(d, alpha=1); a,_ = ratings(g, 100 if role=='bat' else 120, 10, inn_min=4 if role=='bat' else 6)
    gk = g[g.pid.isin(a[a.eligible].index)]; ms = gk.match_id.unique(); r = {'rating':[], 'ponly':[], 'gap':[]}
    for s in range(40):
        h = set(rng.choice(ms, len(ms)//2, replace=False))
        q1 = gk[gk.match_id.isin(h)].groupby('pid')[['wv','w','Pv','Pn','Nv','Nn']].sum(); q2 = gk[~gk.match_id.isin(h)].groupby('pid')[['wv','w','Pv','Pn','Nv','Nn']].sum()
        j = q1.join(q2, lsuffix='1', rsuffix='2', how='inner'); j = j[(j.Pn1>0)&(j.Pn2>0)&(j.Nn1>0)&(j.Nn2>0)]
        w = np.sqrt(j.Pn1*j.Pn2).values
        r['rating'].append(wcorr((j.wv1/j.w1).values, (j.wv2/j.w2).values, w))
        r['ponly'].append(wcorr((j.Pv1/j.Pn1).values, (j.Pv2/j.Pn2).values, w))
        r['gap'].append(wcorr((j.Pv1/j.Pn1 - j.Nv1/j.Nn1).values, (j.Pv2/j.Pn2 - j.Nv2/j.Nn2).values, w))
    res[role] = {k: np.mean(v) for k,v in r.items()}
print(res)
labs = ['Pressure Rating\n(pressure-weighted)', 'Pressure balls only', '"Clutch gap"\n(pressure minus usual)']
fig, ax = plt.subplots(figsize=(9.5,4.2)); x = np.arange(3)
for k,(role,col,lab) in enumerate([('bat',S1,'Batters'),('bowl',S2,'Bowlers')]):
    vals = [res[role]['rating'], res[role]['ponly'], res[role]['gap']]
    ax.bar(x + (k-0.5)*0.32, vals, 0.3, color=col, label=lab)
    for xi, v in zip(x + (k-0.5)*0.32, vals): ax.text(xi, v + (0.006 if v>=0 else -0.02), f'{v:+.2f}', ha='center', fontsize=9, color=INK)
ax.axhline(0, color=MUTE, lw=0.8); ax.set_xticks(x); ax.set_xticklabels(labs); ax.grid(axis='x', visible=False)
ax.set_ylabel('Agreement between two random\nhalves of matches (correlation)'); ax.legend(frameon=False, loc='upper right')
ax.set_title('What repeats? Split every player\'s matches in two, 40 times: the "clutch gap" never repeats', loc='left')
fig.savefig('outputs/charts/fig4_clutch_noise.png', dpi=200, bbox_inches='tight'); plt.close(fig)
import json; json.dump(res, open('outputs/repeatability.json','w'), indent=1)
