import pandas as pd, numpy as np, sys, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0,'scripts'); from lib_pwi import *
S1, S2 = '#2a78d6', '#eb6834'; INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e6e5e0', '#fcfcfb'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.edgecolor':GRID,'axes.linewidth':0.8,'axes.labelcolor':INK2,
    'xtick.color':INK2,'ytick.color':INK2,'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.6,'axes.axisbelow':True,
    'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.titlesize':12,'axes.titlecolor':INK})
SEQ = LinearSegmentedColormap.from_list('blue', ['#f3f7fd','#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b'])
A = pd.read_pickle('outputs/rated_balls.pkl')
OUT='outputs/charts/'

# 1) Pressure map
fig, ax = plt.subplots(1,2, figsize=(12,4.6), gridspec_kw={'width_ratios':[1.15,1]})
c = A[(A.innings==2)&(A.balls_left<=60)].copy()
c['rrr_b'] = pd.cut(c.rrr, [0,6,8,10,12,14,40], labels=['<6','6-8','8-10','10-12','12-14','14+'])
h = c.groupby(['rrr_b', 'wkts_in_hand'], observed=True).PI.mean().unstack().reindex(columns=range(1,11))
im = ax[0].imshow(h.values, cmap=SEQ, vmin=0, vmax=100, aspect='auto', origin='lower')
ax[0].set_xticks(range(10)); ax[0].set_xticklabels(range(1,11)); ax[0].set_yticks(range(len(h))); ax[0].set_yticklabels(h.index)
ax[0].set_xlabel('Wickets in hand'); ax[0].set_ylabel('Required run rate (runs per over)'); ax[0].grid(False)
ax[0].set_title('Chases, last 10 overs: average Pressure Index', loc='left')
for i in range(h.shape[0]):
    for j in range(h.shape[1]):
        v = h.values[i,j]
        if not np.isnan(v): ax[0].text(j, i, f'{v:.0f}', ha='center', va='center', fontsize=8, color='white' if v>60 else INK)
f = A[A.innings==1].copy()
h2 = f.groupby(['over_no', pd.cut(f.wkts_before,[-1,1,3,5,10],labels=['0-1','2-3','4-5','6+'])], observed=True).PI.mean().unstack()
ax[1].imshow(h2.T.values, cmap=SEQ, vmin=0, vmax=100, aspect='auto', origin='lower')
ax[1].set_yticks(range(4)); ax[1].set_yticklabels(h2.columns); ax[1].set_xticks(range(0,20,2)); ax[1].set_xticklabels(range(1,21,2))
ax[1].set_xlabel('Over'); ax[1].set_ylabel('Wickets lost'); ax[1].grid(False)
ax[1].set_title('Batting first: average Pressure Index', loc='left')
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02); cb.set_label('Pressure Index (0-100)'); cb.outline.set_visible(False)
fig.savefig(OUT+'fig1_pressure_map.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# 2) Pressure vs normal: what changes
f = A[A.faced].assign(P=A.PI>=80)
s = f.groupby('P').agg(rr=('bat_runs','mean'), dot=('bat_runs', lambda x:(x==0).mean()), bd=('bat_runs', lambda x:x.isin([4,6]).mean()), out=('striker_out','mean'))
metrics = [('Strike rate', s['rr']*100, '{:.0f}'), ('Dot-ball %', s['dot']*100, '{:.1f}%'), ('Boundary %', s['bd']*100, '{:.1f}%'), ('Balls per dismissal', 1/s['out'], '{:.1f}')]
fig, ax = plt.subplots(1,4, figsize=(12,3.2))
for k,(lab, v, fmt) in enumerate(metrics):
    vals = [v.loc[False], v.loc[True]]
    ax[k].bar([0,1], vals, color=[MUTE, S1], width=0.55)
    for i,x in enumerate(vals): ax[k].text(i, x, fmt.format(x), ha='center', va='bottom', fontsize=10, color=INK)
    ax[k].set_xticks([0,1]); ax[k].set_xticklabels(['Normal\n(80% of balls)','Pressure\n(top 20%)']); ax[k].set_title(lab, loc='left', fontsize=11)
    ax[k].set_ylim(0, max(vals)*1.18); ax[k].grid(axis='x', visible=False)
fig.suptitle('Pressure balls play differently: faster scoring, but wickets fall more often', x=0.01, ha='left', fontweight='bold', color=INK)
fig.tight_layout(); fig.savefig(OUT+'fig2_pressure_vs_normal.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# 3) A real finish, ball by ball
mid = 50359; t = A[(A.match_id==mid)&(A.innings==2)&(A.balls_left<=12)].copy()
t['lab'] = [('W' if w else str(int(r))) for r,w in zip(t.total_runs, t.is_wicket)]
fig, ax = plt.subplots(figsize=(11,3.8))
x = np.arange(len(t)); wp_after = t.wp_after.values*100
ax.plot(np.r_[-1, x], np.r_[t.wp_before.values[0]*100, wp_after], color=S1, lw=2, marker='o', ms=6, markerfacecolor=S1, markeredgecolor=SURF, markeredgewidth=1.5)
for i,(lab, y) in enumerate(zip(t.lab, wp_after)):
    ax.annotate(lab, (i, y), textcoords='offset points', xytext=(0,9), ha='center', fontsize=9, color=('#d03b3b' if lab=='W' else INK), fontweight='bold' if lab in ('W','4','6') else 'normal')
ax.axhline(50, color=MUTE, lw=0.8)
ax.set_xticks(np.r_[-1,x]); ax.set_xticklabels(['start']+[f'{int(o)-1}.{k}' for o,k in zip(t.over_no, t.groupby("over_no").cumcount()+1)], fontsize=8)
ax.set_ylim(0,100); ax.set_ylabel('Chasing side win chance (%)')
ax.set_title('What pressure looks like: IPL 2026, LSG chasing KKR, last 12 balls (every ball scored Pressure Index 97+)', loc='left')
fig.savefig(OUT+'fig3_real_finish.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# 4) Clutch is noise: split-half scatter
rng = np.random.default_rng(5)
d = role_frame(A, 'bat'); g = match_agg(d, alpha=1); a,_ = ratings(g, 100, 10)
keep = a[a.eligible].index; gk = g[g.pid.isin(keep)]
ms = gk.match_id.unique(); h = set(rng.choice(ms, len(ms)//2, replace=False))
def halves(gx):
    q = gx.groupby('pid')[['Pv','Pn','Nv','Nn','wv','w']].sum()
    return pd.DataFrame({'gap': (q.Pv/q.Pn - q.Nv/q.Nn)*100, 'skill': q.wv/q.w*100})
j = halves(gk[gk.match_id.isin(h)]).join(halves(gk[~gk.match_id.isin(h)]), lsuffix='_A', rsuffix='_B').dropna()
fig, ax = plt.subplots(1,2, figsize=(11,4.4))
for k,(col, title) in enumerate([('skill','Overall pressure-weighted impact'), ('gap','"Clutch gap" (pressure minus usual)')]):
    xx, yy = j[col+'_A'], j[col+'_B']; r = np.corrcoef(xx,yy)[0,1]
    ax[k].scatter(xx, yy, s=26, color=S1 if k==0 else S2, alpha=0.75, edgecolor=SURF, linewidth=0.8)
    lim = np.percentile(np.r_[xx,yy],[2,98]); ax[k].set_xlim(lim); ax[k].set_ylim(lim)
    ax[k].set_xlabel('Half A of matches (runs per 100 balls)'); ax[k].set_ylabel('Half B of matches')
    ax[k].set_title(f'{title}\ncorrelation between halves r = {r:+.2f}', loc='left', fontsize=11)
fig.suptitle('Same 102 batters, matches split randomly in two: skill repeats, the "clutch gap" does not', x=0.01, ha='left', fontweight='bold', color=INK)
fig.tight_layout(); fig.savefig(OUT+'fig4_clutch_noise.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# 5/6) Top-15 with uncertainty and P(top 10)
for role, unit_lab, fn in [('bat','runs above average per 100 balls','fig5_top_batters.png'), ('bowl','runs saved vs average per 4 overs','fig6_top_bowlers.png')]:
    fr = pd.read_csv(f'outputs/final_{role}.csv', index_col=0).head(15)
    bs = pd.read_csv(f'outputs/bootstrap_{role}_a1.csv', index_col=0)
    fr = fr.join(bs[['p_top10']])
    fig, ax = plt.subplots(figsize=(10,6.2)); y = np.arange(len(fr))[::-1]
    lo, hi = fr.rating - 1.28*fr.rating_se, fr.rating + 1.28*fr.rating_se
    col = [S1 if r<=10 else MUTE for r in fr['rank']]
    ax.hlines(y, lo, hi, color=col, lw=2, alpha=0.55)
    ax.scatter(fr.rating, y, s=70, color=col, zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.set_yticks(y); ax.set_yticklabels([f"{int(r)}. {n}" for r,n in zip(fr['rank'], fr.name)])
    ax.axvline(0, color=MUTE, lw=0.8); ax.grid(axis='y', visible=False)
    xm = hi.max()*1.04
    for yi, p in zip(y, fr.p_top10): ax.text(xm, yi, f'{p:.0%}', va='center', fontsize=9, color=INK2)
    ax.text(xm, y.max()+1, 'In top 10 in\nresampled data', fontsize=8.5, color=INK2, va='bottom')
    ax.set_xlim(min(0, lo.min())-0.5, xm*1.12)
    ax.set_xlabel(f'Pressure rating ({unit_lab}); bar = 80% uncertainty range')
    ax.set_title(f'Top 15 {"batters" if role=="bat" else "bowlers"} by Pressure Rating (top 10 in blue)', loc='left')
    fig.savefig(OUT+fn, dpi=200, bbox_inches='tight'); plt.close(fig)

# 7) Why weight by pressure: relevance vs reliability
lab = ['Pressure balls only\n(top 20%)', 'Weighted by\nPressure Index', 'Every ball\nequal']
share = [100, 36, 20]; rel_bat=[0.08, 0.20, 0.25]; rel_bowl=[0.05, 0.22, 0.19]
fig, ax = plt.subplots(1,2, figsize=(11,3.6))
ax[0].bar(range(3), share, color=[MUTE, S1, MUTE], width=0.55); ax[0].set_title('How much the top-20% pressure balls count (%)', loc='left', fontsize=11)
for i,v in enumerate(share): ax[0].text(i, v, f'{v}%', ha='center', va='bottom', color=INK)
xx = np.arange(3); ax[1].bar(xx-0.16, rel_bat, 0.3, color=S1, label='Batters'); ax[1].bar(xx+0.16, rel_bowl, 0.3, color=S2, label='Bowlers')
ax[1].set_title('How stable the result is (split-half reliability)', loc='left', fontsize=11); ax[1].legend(frameon=False, loc='upper left')
for k in range(2): ax[k].set_xticks(range(3)); ax[k].set_xticklabels(lab, fontsize=9); ax[k].grid(axis='x', visible=False)
ax[1].set_ylim(0,0.32); ax[0].set_ylim(0,115)
fig.suptitle('Pressure weighting keeps the focus on big moments without throwing away 80% of the evidence', x=0.01, ha='left', fontweight='bold', color=INK)
fig.tight_layout(); fig.savefig(OUT+'fig7_weighting_tradeoff.png', dpi=200, bbox_inches='tight'); plt.close(fig)
print('charts done')
