"""Match conditions table: local start time (night or day), dew region, and who is at home.
   Ball times in the data pack switch from IST to UTC around 1 March 2024; we pick the reading that gives a sensible local start."""
import pandas as pd, numpy as np
T = pd.read_pickle('outputs/rated_balls.pkl')
m = pd.read_csv('outputs/matches_enriched.csv').drop_duplicates('match_id').set_index('match_id')
m = m.loc[m.index.isin(T.match_id.unique())]
ts = pd.to_datetime(T.delivery_ist_time.str.replace(' UTC',''), errors='coerce')
s1 = ts[T.innings==1].groupby(T.match_id[T.innings==1]).quantile(0.02)
raw = (s1.dt.hour + s1.dt.minute/60).rename('raw')
off = {'India':5.5,'Sri Lanka':5.5,'Pakistan':5,'Bangladesh':6,'United Arab Emirates':4,'New Zealand':12.5,'Australia':9.5,'South Africa':2,'Zimbabwe':2,'United Kingdom':0.5,'Ireland':0.5,'West Indies':-4,'United States':-4.5}
c = m[['comp_name','comp_group','year','match_date','venue_id','venue_country','home_team','away_team','home_team_id','away_team_id','knock_out']].join(raw)
o = c.venue_country.map(off)
L_utc, L_ist = (c.raw + o) % 24, (c.raw - 5.5 + o) % 24
ok = lambda L: (L >= 9) & (L <= 21.6)
early = pd.to_datetime(c.match_date) < pd.Timestamp('2024-03-01')
pick = np.where(early, np.where(ok(L_ist), L_ist, L_utc), np.where(ok(L_utc), L_utc, L_ist))
c['local_start'] = pick
c['flipped'] = np.where(early, ~ok(L_ist), ~ok(L_utc))
c['night'] = (c.local_start >= 17.0).astype(int)
c['dew_region'] = c.venue_country.isin(['India','Sri Lanka','Bangladesh','Pakistan','United Arab Emirates']).astype(int)
print('flipped readings:', int(c.flipped.sum()), 'of', len(c), '| still implausible:', int((~ok(c.local_start)).sum()))
print('night share by country:'); print(c.groupby('venue_country').night.mean().round(2).to_string())
print('IPL local start slots:', c[c.comp_group=='IPL'].local_start.round(1).value_counts().head(6).to_dict())
# home: T20I = team plays in its own country; IPL = franchise at its main ground (most used home venue 2023-26)
ipl = c[c.comp_group=='IPL']
main = ipl[ipl.year>=2023].groupby('home_team_id').venue_id.agg(lambda x: x.value_counts().index[0])
def is_home(row, side):
    tid, tname = (row.home_team_id, row.home_team) if side=='h' else (row.away_team_id, row.away_team)
    if row.comp_group=='IPL': return int(main.get(tid, -1) == row.venue_id)
    cty = row.venue_country
    return int(tname == cty or (tname=='Ireland' and cty in ('Ireland','United Kingdom')))
c['home_is_home'] = c.apply(lambda r: is_home(r,'h'), axis=1); c['away_is_home'] = c.apply(lambda r: is_home(r,'a'), axis=1)
print('IPL games played at the home side\'s main ground:', round(c[c.comp_group=='IPL'].home_is_home.mean(),2), '| T20I games with a true home side:', round(c[c.comp_group!='IPL'].home_is_home.mean(),2))
c.to_pickle('outputs/v3/match_conditions.pkl')
