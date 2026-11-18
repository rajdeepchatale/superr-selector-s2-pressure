import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
T = pd.read_pickle('outputs/rated_balls.pkl')   # IPL + full-member T20Is, 2022-26
f = T[T.faced].copy()
wrist = f.bowling_type.str.contains('Leg-Break|Chinaman|legbreak', case=False, na=False)
finger = (f.pace_or_spin=='Spin') & ~wrist
slower = f.delivery_style.isin(['Off Cutter','Leg Cut','Knuckle','Slow Ball','Slow Bouncer'])
cats = {'pace': f.pace_or_spin=='Pace', 'finger spin': finger, 'wrist spin': wrist,
        'slower balls': slower, 'yorkers': f.delivery_style.isin(['Yorker','Wide Yorker']), 'wide yorker': f.delivery_style.eq('Wide Yorker'),
        'bouncers': f.delivery_style.isin(['Bouncer']), 'early swing/seam (ov1-6)': (f.pace_or_spin=='Pace') & (f.over_no<=6) & f.delivery_style.isin(['Inswing','Out Swing','Seamed In','Seamed Out','Reverse Swing In','Reverse Swing Out']),
        'variation spin (googly/carrom/flipper/slider)': f.delivery_style.isin(['Googly','Carrom','Flipper','Slider','Back of Hand'])}
UNCONV = ['Paddle Scoop','Reverse Paddle Scoop','Reverse Sweep','Switch','UpperCut','Paddle Sweep']
ids = {'Suryakumar Yadav':1699,'Abhishek Sharma':6281,'Phil Salt':5553,'Reeza Hendricks':768,'Heinrich Klaasen':4260,'Tim David':6396,
       'Glenn Phillips':4853,'Vaibhav Sooryavanshi':50284,'Namboori Tilak Varma':7897,'Virat Kohli':47}
# league baseline for each category (all batters) to judge "good/bad" fairly
def line(d):
    b=len(d); return (round(100*d.bat_runs.sum()/b) if b else np.nan, round(b/max(d.striker_out.sum(),1),1) if b else np.nan, b)
print('LEAGUE baseline (SR, balls/dismissal):', {k: line(f[m])[:2] for k,m in cats.items()})
for nm,pid in ids.items():
    d = f[f.striker_id==pid]; sr, bpd, n = line(d)
    print(f'\n=== {nm}: overall SR {sr}, balls/dismissal {bpd} ({n} balls)')
    for k,m in cats.items():
        s = line(d[m.loc[d.index]])
        if s[2]>=25: print(f'   {k:45s} SR {s[0]:>4}  balls/dismissal {s[1]:>5}  ({s[2]} balls)')
    st = d.stroke.value_counts(); runs_by = d.groupby('stroke').bat_runs.sum()
    unc = d[d.stroke.isin(UNCONV)]
    print(f'   unconventional shots (scoop/ramp/reverse/switch/upper-cut): {len(unc)} balls = {len(unc)/n:.1%} of balls, {unc.bat_runs.sum()} runs = {unc.bat_runs.sum()/d.bat_runs.sum():.1%} of runs, SR {round(100*unc.bat_runs.sum()/max(len(unc),1))}')
    top = (runs_by.sort_values(ascending=False).head(6)/d.bat_runs.sum()*100).round(0)
    print('   top run-scoring shots (% of runs):', top.to_dict())
    for s in ['Pull shot','Sweep Shot','Reverse Sweep','Paddle Scoop','Inside out','Slog Sweep']:
        x = d[d.stroke==s]
        if len(x)>=10: print(f'     {s}: {len(x)} balls, SR {round(100*x.bat_runs.sum()/len(x))}, outs {int(x.striker_out.sum())}')
lg = f.groupby('striker_id').apply(lambda d: d.stroke.isin(UNCONV).mean())
cnt = f.groupby('striker_id').size(); lg = lg[cnt>=800].sort_values(ascending=False)
names = f.drop_duplicates('striker_id').set_index('striker_id').striker_name
print('\nMost unconventional batters (share of balls, min 800 balls):', [(names[i], round(v*100,1)) for i,v in lg.head(6).items()])
