import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_columns',50)
out = {}
for role in ['bat','bowl']:
    f = pd.read_csv(f'outputs/final_{role}.csv', index_col=0)
    b = pd.read_csv(f'outputs/bootstrap_{role}_a1.csv', index_col=0)[['p_top10','rank_p10','rank_p90']]
    f = f.join(b)
    f['country'] = f.country.fillna('IPL only (no T20Is in data)')
    f['ipl_teams'] = f.ipl_teams.fillna('-')
    f['band_lo'] = f.rating - 1.28*f.rating_se; f['band_hi'] = f.rating + 1.28*f.rating_se
    f['confidence'] = np.select([f.p_top10>=0.75, f.p_top10>=0.5, f.p_top10>=0.3], ['Very likely top 10','Likely top 10','Borderline'], 'Outside')
    if role=='bat':
        cols = {'rank':'Rank','name':'Player','country':'Country','ipl_teams':'IPL teams (2022-26)','rating':'Pressure Rating (runs/100 balls)','band_lo':'Low (80%)','band_hi':'High (80%)',
                'p_top10':'P(top 10)','confidence':'Confidence','Pn':'Pressure balls faced','innP':'Pressure innings','SR_P':'SR under pressure','SR_N':'SR usual','Avg_P':'Avg under pressure','Avg_N':'Avg usual',
                'BpD_P':'Balls/dismissal pressure','BpD_N':'Balls/dismissal usual','xP':'Value/100 pressure balls','xN':'Value/100 usual balls','success_rate':'Pressure innings won (shrunk)','pwi_IPL':'IPL rating (raw)','pwi_T20I_FULL':'T20I rating (raw)'}
    else:
        cols = {'rank':'Rank','name':'Player','country':'Country','ipl_teams':'IPL teams (2022-26)','rating':'Pressure Rating (runs saved/4 overs)','band_lo':'Low (80%)','band_hi':'High (80%)',
                'p_top10':'P(top 10)','confidence':'Confidence','Pn':'Pressure balls bowled','innP':'Pressure spells','overs_P':'Pressure overs','wkts_P':'Pressure wickets','Econ_P':'Econ under pressure','Econ_N':'Econ usual',
                'SRb_P':'Balls/wkt pressure','SRb_N':'Balls/wkt usual','xP':'Value/24 pressure balls','xN':'Value/24 usual balls','success_rate':'Pressure spells won (shrunk)','pwi_IPL':'IPL rating (raw)','pwi_T20I_FULL':'T20I rating (raw)'}
    t = f[list(cols)].rename(columns=cols)
    for c in t.columns:
        if t[c].dtype.kind=='f': t[c] = t[c].round(2)
    t['P(top 10)'] = (f.p_top10*100).round(0).astype(int).astype(str)+'%'
    t[[c for c in t.columns if 'won' in c][0]] = (f.success_rate*100).round(0).astype(int).astype(str)+'%'
    out[role] = t
    t.to_csv(f'outputs/rankings_{role}_full.csv', index=False)
    print(f'\n===== {role.upper()} top 20'); print(t.head(20).to_string(index=False))
