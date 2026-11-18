"""Charts for the report deck, drawn in Inter to match the slides. Sizes are in slide pixels / 100 at dpi 200,
so 17pt text shows at about 24px on a 1920-wide slide."""
import pandas as pd, numpy as np, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import font_manager as fm
for f in fm.findSystemFonts(fontpaths=['/usr/share/fonts/opentype/inter']): fm.fontManager.addfont(f)

PAPER, INK, INK2, GRID = '#F5F4EF', '#14213D', '#4A5263', '#DEDCD3'
BLUE, ORANGE = '#2A78D6', '#EB6834'
NAVY, LIGHT, LIGHT2, DGRID = '#14213D', '#F5F4EF', '#BFC8D8', '#2B3A5C'
BLUE_D, ORANGE_D = '#3987E5', '#D95926'
OUT = 'outputs/deck/'
import os; os.makedirs(OUT, exist_ok=True)
base = {'font.family': 'Inter', 'font.size': 16, 'axes.spines.top': False, 'axes.spines.right': False,
        'savefig.transparent': True, 'figure.facecolor': 'none', 'axes.facecolor': 'none'}

A = pd.read_pickle('outputs/rated_balls.pkl')

# 1) Chases, last 10 overs: average Pressure Index by required rate x wickets in hand
plt.rcParams.update(base | {'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2})
c = A[(A.innings == 2) & (A.balls_left <= 60)].copy()
c['rrr_b'] = pd.cut(c.rrr, [0, 6, 8, 10, 12, 14, 40], labels=['under 6', '6 to 8', '8 to 10', '10 to 12', '12 to 14', '14+'])
h = c.groupby(['rrr_b', 'wkts_in_hand'], observed=True).PI.mean().unstack().reindex(columns=range(1, 11))
n = c.groupby(['rrr_b', 'wkts_in_hand'], observed=True).PI.size().unstack().reindex(columns=range(1, 11))
MIN_N = 30   # cells built on fewer balls than this are greyed out, not shown as a number
hv = np.where(n.values >= MIN_N, h.values, np.nan)
SEQ = LinearSegmentedColormap.from_list('b', ['#EEF4FC', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'])
fig, ax = plt.subplots(figsize=(9.6, 6.3))
ax.pcolormesh(np.arange(11) + 0.5, np.arange(7) - 0.5, np.zeros_like(hv), cmap=LinearSegmentedColormap.from_list('g', ['#E2E0D8', '#E2E0D8']),
              edgecolors=PAPER, linewidth=3)
ax.pcolormesh(np.arange(11) + 0.5, np.arange(7) - 0.5, np.ma.masked_invalid(hv), cmap=SEQ, vmin=0, vmax=100,
              edgecolors=PAPER, linewidth=3)
for i in range(h.shape[0]):
    for j in range(h.shape[1]):
        v = hv[i, j]
        if not np.isnan(v):
            ax.text(j + 1, i, f'{v:.0f}', ha='center', va='center', fontsize=16, fontweight='600',
                    color='#F5F4EF' if v > 58 else INK)
ax.set_xticks(range(1, 11)); ax.set_yticks(range(6)); ax.set_yticklabels(h.index)
ax.tick_params(length=0, labelsize=16, pad=8)
ax.set_xlabel('Wickets in hand', fontsize=17, labelpad=10); ax.set_ylabel('Required run rate', fontsize=17, labelpad=10)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xlim(0.5, 10.5); ax.set_ylim(-0.5, 5.5)
fig.savefig(OUT + 'chase_pressure_map.png', dpi=200, bbox_inches='tight', pad_inches=0.05); plt.close(fig)

# 2) A real finish: RR chasing 202 against SRH, IPL 2024, last two overs. (Not an IPL 2026 game: 2026 scored
#    higher than any season the chase model was trained on, which pushes its late win chances up.)
plt.rcParams.update(base | {'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2,
                            'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'axes.axisbelow': True})
t = A[(A.match_id == 31268) & (A.innings == 2) & (A.balls_left <= 12)].copy()
lab_x, lab_o = [], []
for r in t.itertuples():
    ball = f'{int(r.over_no) - 1}.{int(r.legal_before % 6) + 1}'
    if r.is_wide: lab_x.append(ball + '\nwide'); lab_o.append('wd')
    elif r.is_noball: lab_x.append(ball + '\nno-ball'); lab_o.append(f'nb+{int(r.total_runs) - 1}')
    else: lab_x.append(ball); lab_o.append('W' if r.is_wicket else str(int(r.total_runs)))
fig, ax = plt.subplots(figsize=(16.4, 5.3))
x = np.arange(len(t)); wp = t.wp_after.values * 100
ax.axhline(50, color=INK2, lw=1.2, ls=(0, (4, 4)))
ax.plot(np.r_[-1, x], np.r_[t.wp_before.values[0] * 100, wp], color=BLUE, lw=3, zorder=3)
ax.scatter(np.r_[-1, x], np.r_[t.wp_before.values[0] * 100, wp], s=110, color=BLUE, edgecolor=PAPER, linewidth=2.5, zorder=4)
wk = [i for i, o in enumerate(lab_o) if o == 'W']
ax.scatter(x[wk], wp[wk], s=260, facecolor='none', edgecolor=ORANGE, linewidth=3, zorder=5)
for i, (o, y) in enumerate(zip(lab_o, wp)):
    big = o in ('W', '4', '6')
    ax.annotate(o, (i, y), textcoords='offset points', xytext=(0, 14), ha='center', fontsize=17 if big else 15,
                color=INK, fontweight='700' if big else '400')
ax.set_xticks(np.r_[-1, x]); ax.set_xticklabels(['start'] + lab_x, fontsize=14)
ax.set_ylim(-5, 104); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=15)
ax.set_ylabel('RR win chance', fontsize=16, labelpad=10); ax.tick_params(length=0)
ax.spines['left'].set_visible(False); ax.grid(axis='x', visible=False)
fig.savefig(OUT + 'real_finish.png', dpi=200, bbox_inches='tight', pad_inches=0.05); plt.close(fig)

# 3) What repeats (dark slide)
res = json.load(open('outputs/repeatability.json'))
plt.rcParams.update(base | {'axes.edgecolor': DGRID, 'xtick.color': LIGHT2, 'ytick.color': LIGHT2, 'axes.labelcolor': LIGHT2,
                            'axes.grid': True, 'grid.color': DGRID, 'grid.linewidth': 1, 'axes.axisbelow': True})
keys = ['ponly', 'rating', 'equal', 'gap']
labs = ['Pressure balls\nonly', 'My Pressure\nRating', 'Every ball\nequal', '“Clutch gap”\n(pressure\nminus normal)']
fig, ax = plt.subplots(figsize=(10.2, 6.1)); xx = np.arange(4)
for k, (role, col, lab) in enumerate([('bat', BLUE_D, 'Batters'), ('bowl', ORANGE_D, 'Bowlers')]):
    vals = [res[role][kk] for kk in keys]; xs = xx + (k - 0.5) * 0.36
    ax.bar(xs, vals, 0.33, color=col, label=lab, zorder=3)
    for xi, v in zip(xs, vals):
        ax.text(xi, v + (0.008 if v >= 0 else -0.012), f'{v:+.2f}'.replace('-', '−'), ha='center', va='bottom' if v >= 0 else 'top',
                fontsize=17, color=LIGHT, fontweight='600')
ax.axhline(0, color=LIGHT2, lw=1.2, zorder=4)
ax.set_xticks(xx); ax.set_xticklabels(labs, fontsize=16, color=LIGHT); ax.tick_params(length=0, pad=10)
ax.set_ylim(-0.13, 0.29); ax.set_yticks([]); ax.grid(False)
for sp in ax.spines.values(): sp.set_visible(False)
leg = ax.legend(frameon=False, loc='upper right', fontsize=17, labelcolor=LIGHT, handlelength=1.2)
fig.savefig(OUT + 'what_repeats_dark.png', dpi=200, bbox_inches='tight', pad_inches=0.05); plt.close(fig)
print(sorted(os.listdir(OUT)), h.round(0).to_string())
