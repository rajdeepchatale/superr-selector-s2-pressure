"""Update the report deck to the v3 model. Works from the live slide files (so earlier hand edits are kept):
regenerates the list, evidence and note slides from outputs/v3, edits numbers in prose slides, adds two new slides."""
import pandas as pd, numpy as np, json, re, html, os
D = 'deck/project/'; S = D + 'slides/'
FOOT = '<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>\n<p class="pnum"></p>'
Z80 = 1.2816
N = json.load(open('outputs/v3/deck_numbers.json'))
selb = pd.read_csv('outputs/v3/selection_bat_v3.csv', index_col=0).set_index('name')
selw = pd.read_csv('outputs/v3/selection_bowl_v3.csv', index_col=0).set_index('name')
oldb = pd.read_csv('outputs/final_bat.csv').set_index('name'); oldw = pd.read_csv('outputs/final_bowl.csv').set_index('name')
wins = pd.read_csv('outputs/v3/wins_shrunk.csv', index_col=[0, 1]).iloc[:, 0]
ex = pd.read_csv('outputs/v3/execution_bowlers.csv', index_col=0).set_index('name'); ex['exp_pct'] = ex.miss_P_pct - ex.miss_ae_P_pct
def e(s): return html.escape(s, quote=False).replace("'", '’')
def rd(path): return open(path, encoding='utf-8').read()
def wr(path, s): open(path, 'w', encoding='utf-8').write(s)
def sub1(s, old, new, path=''):
    n = s.count(old); assert n == 1, f'{path}: expected 1 match, found {n}: {old[:70]}'
    return s.replace(old, new)
def top10(sel): t = sel.sort_values('p_top10', ascending=False).head(10); return list(t.sort_values('rating', ascending=False).index)
BAT, BOWL = top10(selb), top10(selw)
BAT_MISS = selb.sort_values('p_top10', ascending=False).index[10]; BOWL_MISS = selw.sort_values('p_top10', ascending=False).index[10]
assert BAT_MISS == 'Cameron Green' and BOWL_MISS == 'Matheesha Pathirana', (BAT_MISS, BOWL_MISS)
def pc(x): return f'{round(100 * x):.0f}%'
def gcls(p): return ' g' if p >= 0.75 else ''
def bst(n):
    r = selb.loc[n]; o = oldb.loc[n]
    return dict(rating=r.rating, lo=r.rating - Z80 * r.se, hi=r.rating + Z80 * r.se, p=r.p_top10, Pb=int(o.Pb), srp=o.SR_P, srn=o.SR_N, bpd=o.BpD_P, wins=wins[('bat', n)])
def wst(n):
    r = selw.loc[n]; o = oldw.loc[n]
    return dict(rating=r.rating, lo=r.rating - Z80 * r.se, hi=r.rating + Z80 * r.se, p=r.p_top10, ov=o.Pb / 6, ecp=o.Econ_P, ecn=o.Econ_N, sr=o.SRb_P, wins=wins[('bowl', n)])
f1 = lambda v: f'{v:.1f}'; f2 = lambda v: f'{v:.2f}'
css = rd(D + 'deck.css')
for a, b in [('.trow { display: flex; align-items: center; gap: 4px; height: 40px;', '.trow { display: flex; align-items: center; gap: 4px; height: 38px;'),
             ('.c-plot { width: 520px; height: 40px; position: relative; }', '.c-plot { width: 400px; height: 38px; position: relative; }'),
             ('.base { position: absolute; left: 0; top: 19px; width: 520px;', '.base { position: absolute; left: 0; top: 18px; width: 400px;'),
             ('.bar { position: absolute; top: 15px;', '.bar { position: absolute; top: 14px;'),
             ('.dot { position: absolute; top: 9px;', '.dot { position: absolute; top: 8px;'),
             ('.c-axis { width: 520px;', '.c-axis { width: 400px;')]:
    css = sub1(css, a, b, 'deck.css')
wr(D + 'deck.css', css + '\n.c-wn { width: 120px; text-align: right; }\n')

# ---------------- answer (slide 2)
def lst(title, names, st, fmt, cls):
    rows = ''.join(f'<div class="lrow"><p class="rk">{i}</p><p class="nm">{e(n)}</p><p class="rt">{fmt(st(n)["rating"])}</p><p class="pc{gcls(st(n)["p"])}">{pc(st(n)["p"])}</p></div>\n'
                   for i, n in enumerate(names, 1))
    return (f'<div class="col" style="flex:1; gap:10px">\n<h3 class="{cls}" style="font-size:36px">{title}</h3>\n<div class="list">\n'
            f'<div class="lhead"><p class="rk">#</p><p class="nm">Player</p><p class="rt">Rating</p><p class="pc">Top 10</p></div>\n{rows}</div>\n</div>')
body = ('<div class="head"><p class="eyebrow">THE SHORT VERSION</p><h2>My top 10s, ranked on what repeats under pressure</h2></div>\n'
        '<div class="row" style="gap:96px">\n' + lst('Batters', BAT, bst, f1, 'blue') + '\n' + lst('Bowlers', BOWL, wst, f2, 'orange') + '\n</div>\n'
        '<p class="small" style="margin-top:-12px">Rating: runs above an average player in the same situation and against the same opposition, per 100 balls faced (batters) or per 24 balls bowled (bowlers), with pressure balls counting most. Top 10: share of 2,000 resampled datasets in which he stays top 10; bold = 75% or more.</p>')
wr(S + 'answer.html', f'<section id="answer">\n{body}\n{FOOT}\n</section>\n')

# ---------------- evidence tables
W = 400
def evidence(sid, role, names, miss, st, axis_max, ticks, fmt, heads, cells, title, why, note):
    sc = W / axis_max
    def plot(s):
        lo, hi = max(s['lo'], 0), min(s['hi'], axis_max)
        return (f'<div class="c-plot"><div class="base"></div><div class="bar" style="left:{lo * sc:.0f}px; width:{(hi - lo) * sc:.0f}px"></div>'
                f'<div class="dot" style="left:{s["rating"] * sc - 11:.0f}px"></div></div>')
    tk = ''.join(f'<p class="tick" style="left:{t * sc - 30:.0f}px">{t}</p>' for t in ticks)
    head = (f'<div class="thead"><p class="c-rk">#</p><p class="c-nm">{"Batter" if role == "bat" else "Bowler"}</p>'
            f'<div class="c-axis"><p>Rating (dot), 80% range (bar)</p><div class="c-plot">{tk}</div></div>'
            f'<p class="c-rt">Rating</p><p class="c-pc">Top 10 in resamples</p><p class="c-wn">Wins a season</p>'
            f'<div class="c-grp"><p class="c-grp-t">On pressure balls (usual in brackets)</p><div class="c-grp-r">'
            + ''.join(f'<p class="{c}">{h}</p>' for c, h in zip(['c-n1', 'c-n2', 'c-n3'], heads)) + '</div></div></div>\n')
    rows = ''
    for i, n in enumerate(names + [miss], 1):
        s = st(n); k = 'miss' if n == miss else ('cut' if i == 10 else '')
        rows += (f'<div class="trow {k}"><p class="c-rk">{i}</p><p class="c-nm">{e(n)}</p>{plot(s)}'
                 f'<p class="c-rt">{fmt(s["rating"])}</p><p class="c-pc{"" if n == miss else gcls(s["p"])}">{pc(s["p"])}</p><p class="c-wn">{s["wins"]:.2f}</p>'
                 + ''.join(f'<p class="{c}">{v}</p>' for c, v in zip(['c-n1', 'c-n2', 'c-n3'], cells(s))) + '</div>\n')
    body = (f'<div class="head"><p class="eyebrow">4 · EVIDENCE: {"BATTERS" if role == "bat" else "BOWLERS"}</p><h2>{title}</h2></div>\n'
            f'<div class="col {role}" style="gap:0; margin-top:-14px">\n{head}{rows}<p class="why" style="margin-top:8px">{why}</p>\n<p class="small" style="margin-top:4px">{note}</p>\n</div>')
    wr(S + sid + '.html', f'<section id="{sid}">\n{body}\n{FOOT}\n</section>\n')
g, p, s = selb.loc['Cameron Green'], selb.loc['Nicholas Pooran'], selb.loc['Shashank Singh']; k = selb.loc['Virat Kohli']
evidence('bat-evidence', 'bat', BAT, BAT_MISS, bst, 28, [0, 5, 10, 15, 20, 25], f1, ['Balls', 'SR', 'Balls per out'],
         lambda s: [f'{s["Pb"]}', f'{s["srp"]:.0f} ({s["srn"]:.0f})', f'{s["bpd"]:.1f}'],
         'Batters: the top 10 and how sure I am',
         f'<b>Missed the cut: Cameron Green.</b> He and Nicholas Pooran rate a touch higher than Kohli ({g.rating:.1f} and {p.rating:.1f} vs {k.rating:.1f}), but Kohli stays in the top 10 in more resamples ({pc(k.p_top10)} vs {pc(g.p_top10)} and {pc(p.p_top10)}), and that decides the last place. More on the next slide.',
         'Rating: runs above average per 100 balls. Wins a season: the rating as extra wins over 14 matches. Picked by the resample rule, ordered by rating.')
pa, mu = selw.loc['Matheesha Pathirana'], selw.loc['Mujeeb Ur Rahman']
evidence('bowl-evidence', 'bowl', BOWL, BOWL_MISS, wst, 5.6, [0, 1, 2, 3, 4, 5], f2, ['Overs', 'Economy', 'Balls per wicket'],
         lambda s: [f'{s["ov"]:.1f}', f'{s["ecp"]:.2f} ({s["ecn"]:.2f})', f'{s["sr"]:.1f}'],
         'Bowlers: the top 10 and how sure I am',
         f'<b>Missed the cut: Matheesha Pathirana.</b> He rates a hair above Mujeeb ({pa.rating:.2f} vs {mu.rating:.2f}), but Mujeeb stays in the top 10 in more resamples ({pc(mu.p_top10)} vs {pc(pa.p_top10)}). The ground cost him most: much of his best work came at Chepauk and in Sri Lanka, which help pace bowlers.',
         'Rating: runs saved per 24 balls. Wins a season: the rating as extra wins over 14 matches. Picked by the resample rule, ordered by rating.')

# ---------------- player notes: reorder cards to the new order, update ranks and resample shares, add execution for bowlers
cards = {}
for f in sorted(os.listdir(S)):
    if re.match(r'(bat|bowl)-notes-\d\.html', f):
        for line in rd(S + f).splitlines():
            if line.startswith('<div class="ncard"') or line.startswith('<div class="ncard bowl"'):
                cards[re.search(r'<h3>(.*?)</h3>', line).group(1)] = line
ELLIS = ('<div class="ncard bowl"><div class="nhead"><p class="nrank">0</p><div class="nname"><h3>Nathan Ellis</h3><p class="nrole">Right-arm fast · Australia · PBKS, CSK in 2025</p></div></div>'
         '<p class="nstats"><b>37.5</b> pressure overs · economy <b>9.68</b> (usual 7.71) · wicket every <b>14.1</b> balls · top 10 in <b>48%</b> of resamples</p>'
         '<p class="ntext">Ellis wins with changes of pace. A quarter of his pressure balls are back-of-the-hand slower balls, and he mixes in off-cutters, slower bouncers and yorkers, so batters have to guess every ball.</p>'
         '<p class="ntext str">His economy under pressure looks expensive, but 47% of those overs came at the death, often at batting grounds like Guwahati and Mohali and against strong line-ups. An average bowler in the same spots concedes the same runs and takes 14 wickets; Ellis took 16.</p>'
         '<p class="ntext">Left-handers find him hardest: 7.84 an over under pressure, with a wicket every 11 balls. His best day: 4 for 30 against RR at Guwahati in 2023, and PBKS won by five runs.</p></div>')
cards['Nathan Ellis'] = ELLIS
def fix_card(line, rank, name, role):
    line = re.sub(r'<p class="nrank">\d+</p>', f'<p class="nrank">{rank}</p>', line, count=1)
    sel = selb if role == 'bat' else selw
    line, n = re.subn(r'top 10 in <b>\d+%</b> of resamples', f'top 10 in <b>{pc(sel.loc[name].p_top10)}</b> of resamples', line); assert n == 1, name
    if role == 'bowl':
        r = ex.loc[name]
        line = sub1(line, ' of resamples</p>', f' of resamples · full tosses, wides, no‑balls <b>{r.miss_P_pct:.0f}%</b> ({r.exp_pct:.0f}% expected)</p>', name)
    return line
EDITS = {  # small text changes inside cards
 'Tim David': [(' at the death and the game is over, especially when dew makes bowlers miss their lengths.', ' at the death and the game is over.')],
 'Virat Kohli': [('Why he edges Pooran is on slide 14:', 'Why he edges Green and Pooran is on slide 16:')],
 'Jasprit Bumrah': [('He’s the same bowler in the 1st over and the 19th.', 'He’s the same bowler in the 1st over and the 19th. He misses his length more than most, mostly full tosses, and batters still can’t score off him.')],
}
for role, names in [('bat', BAT), ('bowl', BOWL)]:
    for k5 in range(5):
        pair = []
        for j in (0, 1):
            i = 2 * k5 + j; n = names[i]; line = fix_card(cards[n], i + 1, n, role)
            for old, new in EDITS.get(n, []): line = sub1(line, old, new, n)
            pair.append(line)
        lab = 'BATTER' if role == 'bat' else 'BOWLER'
        body = (f'<p class="eyebrow">4 · EVIDENCE: {lab} NOTES · {2 * k5 + 1} AND {2 * k5 + 2} OF 10</p>\n'
                f'<div class="ncards" style="margin-top:-20px">\n{pair[0]}\n{pair[1]}\n</div>')
        wr(S + f'{role}-notes-{k5 + 1}.html', f'<section id="{role}-notes-{k5 + 1}">\n{body}\n{FOOT}\n</section>\n')

# ---------------- prose slides with numbers
def edit(sid, pairs):
    s = rd(S + sid + '.html')
    for old, new in pairs: s = sub1(s, old, new, sid)
    wr(S + sid + '.html', s)
ex_s, ex_h = N['ex_Suryakumar'], N['ex_Shashank']
edit('rating', [('raw +30.6 runs per 100 balls, rating +19.7. With 566 pressure balls he keeps 53% of his edge over the average qualified batter.',
                 f'raw +{ex_s["raw"]:.1f} runs per 100 balls, rating +{ex_s["rating"]:.1f}. With 566 pressure balls he keeps {ex_s["kept"]}% of his edge over the average qualified batter.'),
                ('raw +37.7, rating +12.2. With 120 pressure balls he keeps only 15%, which is why he sits outside my top 10.',
                 f'raw +{ex_h["raw"]:.1f}, rating +{ex_h["rating"]:.1f}. With 120 pressure balls he keeps only {ex_h["kept"]}%, and he makes the top 10 in just {pc(selb.loc["Shashank Singh"].p_top10)} of resamples.')])
# clutch slide: new values, dot positions (x = 239 + 1600 v, dot left = x - 13, starts from the zero line)
rb, rw = N['bat_repeat_v3'], N['bowl_repeat_v3']
s = rd(S + 'clutch.html')
rows = re.findall(r'<div class="cl-dot bat" style="left:\d+px; --dx:-?\d+px; --i:(\d)"></div><div class="cl-dot bowl" style="left:\d+px; --dx:-?\d+px; --i:\d"></div></div><p class="cl-v">[^<]*</p><p class="cl-v">[^<]*</p>', s)
assert len(rows) == 4
def fmtv(v): return '0.00' if abs(v) < 0.005 else ('+' if v >= 0 else '−') + f'{abs(v):.2f}'
for (key, i) in zip(['gap', 'P', 'rating', 'equal'], rows):
    vb, vw = rb[key], rw[key]; lb, lw = round(239 + 1600 * vb - 13), round(239 + 1600 * vw - 13)
    s, n = re.subn(r'<div class="cl-dot bat" style="left:\d+px; --dx:-?\d+px; --i:' + i + r'"></div><div class="cl-dot bowl" style="left:\d+px; --dx:-?\d+px; --i:' + i + r'"></div></div><p class="cl-v">[^<]*</p><p class="cl-v">[^<]*</p>',
                   f'<div class="cl-dot bat" style="left:{lb}px; --dx:{227 - lb}px; --i:{i}"></div><div class="cl-dot bowl" style="left:{lw}px; --dx:{227 - lw}px; --i:{i}"></div></div><p class="cl-v">{fmtv(vb)}</p><p class="cl-v">{fmtv(vw)}</p>', s)
    assert n == 1
s = sub1(s, 'Weighting every ball by its Index is about twice as steady and still leans on the tight moments.',
         'Weighting every ball by its Index is more than twice as steady and still leans on the tight moments.', 'clutch')
wr(S + 'clutch.html', s)
# Kohli slide: three columns (Kohli, Green, Pooran)
kh = rd(S + 'kohli.html')
kt = '''<div class="ttable" style="width:1010px">
<div class="tt-head"><p style="flex:1">On pressure balls, 2022–26</p><p style="width:150px; text-align:right">Kohli</p><p style="width:150px; text-align:right">Green</p><p style="width:150px; text-align:right">Pooran</p></div>
ROWS</div>'''
R3 = [('Pressure balls faced', '440', '215', '431', ''), ('Strike rate', '150', '171', '155', ''), ('Balls per dismissal', '62.9', '26.9', '20.5', 'y'),
      ('Runs above average per 100 balls', '+30.6', '+38.1', '+20.5', ''), ('Pressure innings above average', '77%', '81%', '64%', ''),
      ('Top 10 in 2,000 resamples', pc(k.p_top10), pc(g.p_top10), pc(p.p_top10), ''), ('Top 10, more weight on pressure', '3 of 3', '1 of 3', '0 of 3', 'y')]
rws = ''
for lab, a, b, c, y in R3:
    st = ' style="padding:13px 12px; margin:0 -12px"' if y else ' style="padding:13px 0"'
    rws += f'<div class="tt-row{" y" if y else ""}"{st}><p style="flex:1">{lab}</p><p class="k" style="width:150px; text-align:right">{a}</p><p style="width:150px; text-align:right">{b}</p><p style="width:150px; text-align:right">{c}</p></div>\n'
kh = re.sub(r'<div class="ttable" style="width:960px">.*?\n</div>\n(?=<div class="col")', kt.replace('ROWS', rws), kh, flags=re.S)
kh = sub1(kh, '<h2>Why Kohli and not Pooran at No. 10</h2>', '<h2>Why Kohli takes No. 10</h2>', 'kohli')
kh = re.sub(r'<div class="col" style="flex:1; gap:22px">.*?</div>\n</div>', '<div class="col" style="flex:1; gap:22px">\n'
            f'<p style="font-size:26px; line-height:1.4">The resample rule gives Kohli the last spot ({pc(k.p_top10)}). Green ({pc(g.p_top10)}) and Pooran ({pc(p.p_top10)}) are next, so I checked it the cricket way, not on reputation.</p>\n'
            f'<p style="font-size:26px; line-height:1.4">Both rate a touch higher overall ({g.rating:.1f} and {p.rating:.1f} to {k.rating:.1f}). But in tight moments Kohli gets out once every 63 balls, Green every 27 and Pooran every 21. Green’s numbers are strong, on half as many balls.</p>\n'
            '<p style="font-size:26px; line-height:1.4">The more weight I put on pressure, the clearer it gets: Kohli makes the top 10 in all three tests, Green in one, Pooran in none.</p>\n'
            '<p class="small">The three tests: weight each ball by Index², by Index³, and pressure balls only.</p>\n</div>\n</div>', kh, count=1, flags=re.S)
wr(S + 'kohli.html', kh)
# stress slide
st_b, st_w = N['bat_stress'], N['bowl_stress']
ROWS = [('More weight on pressure (Index²)', 'More weight on pressure (Index²)'), ('Less weight on pressure (√Index)', 'Less weight on pressure (√Index)'),
        ('Recent seasons count more (2-year half-life)', 'Recent seasons count more (2-year half-life)'), ('Pressure line at the top 25% of balls', 'Pressure line at the top 25% of balls'),
        ('Pressure line at the top 15% of balls', 'Pressure line at the top 15% of balls'), ('Sample minimum raised by half', 'Sample minimum raised by half'),
        ('Without the new adjustments', 'Without the new adjustments (old values)'), ('A wicket worth 11 runs instead of 8', 'A wicket worth 11 runs instead of 8'),
        ('Pressure balls only, no weighting', 'Pressure balls only, no weighting'), ('IPL 2026 scoring level capped at 2025’s †', 'IPL 2026 scoring level capped at 2025’s')]
tr = ''
for lab, key in ROWS:
    b, w = st_b[key]['same'], st_w[key]['same']; star = '*' if key.startswith('Pressure line at the top 15%') else ''
    tr += f'<div class="tt-row" style="padding:5px 0"><p style="flex:1">{lab}</p><p class="k" style="width:150px; text-align:right">{b}/10{star}</p><p class="k" style="width:150px; text-align:right">{w}/10</p></div>\n'
nb8 = sum(st_b[k2]['same'] >= 8 and st_w[k2]['same'] >= 9 for _, k2 in ROWS)
sh = rd(S + 'stress.html')
sh = re.sub(r'(<div class="tt-head">.*?</div>\n)(?:<div class="tt-row".*?</div>\n)+', lambda m: m.group(1) + tr, sh, count=1, flags=re.S)
sh = sub1(sh, '* Hendricks, Phillips and Sooryavanshi drop below the sample minimum at this line. Their ratings stay at top-10 level. † IPL 2026 scored higher than any season before it, which pushed the model’s late win chances in 2026 chases up.',
          '* Hendricks, Phillips and Sooryavanshi fall below the sample minimum at this line. Kohli is in by the resample rule, not a straight sort, so several tests drop him. † IPL 2026 scored higher than any season before it.', 'stress')
sh = sub1(sh, '<p class="mid">7 of 10</p><p class="bigcap">changes keep at least 9 of my 10 batters and 9 of my 10 bowlers</p>',
          f'<p class="mid">{nb8} of 10</p><p class="bigcap">changes keep at least 8 of my 10 batters and 9 of my 10 bowlers</p>', 'stress')
sh = sub1(sh, '<h3 style="font-size:28px; line-height:1.25">500 resampled datasets</h3><p style="font-size:24px">I redrew the matches at random 500 times and rebuilt every rating. Suryakumar (96%) and Abhishek (94%) almost never leave the top 10, and Narine is the safest bowler (87%). The last places in both lists are close calls, between 32% and 50%.</p>',
          f'<h3 style="font-size:28px; line-height:1.25">2,000 resampled datasets</h3><p style="font-size:24px">I redrew the matches at random 2,000 times and rebuilt every rating. Suryakumar ({pc(selb.loc["Suryakumar Yadav"].p_top10)}) and Abhishek ({pc(selb.loc["Abhishek Sharma"].p_top10)}) almost never leave the top 10, and Narine is the safest bowler ({pc(selw.loc["Sunil Narine"].p_top10)}). The last places in both lists are close calls, between {pc(k.p_top10)} and {pc(selw.loc["Krunal Pandya"].p_top10)}.</p>', 'stress')
sh = sub1(sh, 'Ratings built on 2022–24 only, checked against pressure value in 2025–26: +0.24 for bowlers, +0.02 for batters. Bowling under pressure carries over from year to year. Batting form carries over much less.',
          f'Ratings built on 2022–24, checked against 2025–26: +{N["bowl_oot_v3"]:.2f} for bowlers and +{N["bat_oot_v3"]:.2f} for batters, up from +0.24 and +0.02 before the new adjustments. Bowling carries over from year to year; batting much less.', 'stress')
wr(S + 'stress.html', sh)
edit('method', [('Runs above an average player in exactly the same situation, with a wicket worth 8 runs.', 'Runs above an average player in the same situation and against the same opposition, with a wicket worth 8 runs.'),
                ('500 resampled datasets, ten changes to the settings, and a test of whether ratings from 2022–24 predict 2025–26.', '2,000 resampled datasets, ten changes to the settings, ten more pressure ideas tested, and a test of whether ratings from 2022–24 predict 2025–26.')])
edit('measure', [('In T20Is I also adjust for the opponent, so runs against a weak attack count a little less. IPL sides are close in strength, so there is no adjustment there.',
                  'Then each ball is adjusted for the player at the other end, in the IPL and T20Is alike, so runs off a weak bowler count a little less. Bowlers are also adjusted for the ground.')])
edit('fair', [('Competition, year and scoring level are part of the baseline, and T20Is get an opponent-strength adjustment. I also checked IPL-only and T20I-only ratings.',
               'Competition, year and scoring level are part of the baseline, and every ball is adjusted for the player at the other end. I also checked IPL-only and T20I-only ratings.')])
edit('limits', [('Batters’ 2022–24 ratings barely predict their 2025–26 pressure value (+0.02).', f'Batters’ 2022–24 ratings barely predict their 2025–26 pressure value (+{N["bat_oot_v3"]:.2f}).'),
                ('I can’t tell a good ball from a bad shot. Delivery-type tags are used only in my player notes, not in the rating.', 'I can’t tell a good ball from a bad shot. Delivery tags feed the missed-delivery check in my bowler notes, not the rating.'),
                ('<h3>Pressure comes from the scoreboard</h3><p>The model doesn’t know the venue, dew, team strength or the Impact Player rule, only the match situation.</p>',
                 '<h3>Team context is missing</h3><p>I adjust for opponents, and bowlers for the ground, but the model doesn’t know the Impact Player rule, team plans or injuries.</p>')])
edit('appendix', [('<div class="tt-row"><p class="k" style="width:330px">Opponent adjustment</p><p style="flex:1">T20Is only. Each team’s average value conceded or scored, shrunk with 3,000 balls of prior weight.</p></div>',
                   '<div class="tt-row"><p class="k" style="width:330px">Opponents and grounds</p><p style="flex:1">Ridge regression of every ball’s value on batter, bowler, ground (by pace or spin), dew and home side, with penalties set from the data. Each ball is then adjusted for the player at the other end, and bowlers also for the ground.</p></div>')])
edit('reproduce', [('<div class="step"><p class="sn">6</p><div class="sb"><p><b>12_final_ratings</b>, <b>13_stability</b> and <b>14_sensitivity</b>: ratings, the 500 resamples and the stress tests.</p></div></div>',
                    '<div class="step"><p class="sn">6</p><div class="sb"><p><b>12_final_ratings</b> and <b>30</b> to <b>37</b>: player stats, the opponent and ground adjustments, the tests, 2,000 resamples and every number in this deck.</p></div></div>'),
                   ('<p style="font-weight:600; color:#14213D">500, by match, seed 11</p>', '<p style="font-weight:600; color:#14213D">2,000, by match, seed 11</p>')])

# ---------------- new slides
adjust = f'''<section id="adjust">
<div class="head"><p class="eyebrow">2 · MEASURING PERFORMANCE</p><h2>The scoreboard already reads the pitch</h2></div>
<div class="row" style="gap:48px">
<div class="tile" style="flex:none; width:520px; gap:12px"><p class="tl">PITCH ON THE DAY</p><p class="tv">0.32 → 0.00</p><p class="tc">How closely a match’s two innings agree on runs per ball: 0.32 in raw runs, 0.00 once each ball is compared with my baseline. The baseline already reads the pitch from the score and the target, so a separate pitch adjustment adds nothing.</p></div>
<div class="ttable tt-sm" style="flex:1">
<div class="tt-head"><p style="width:300px">What I tested</p><p style="flex:1">What the data said</p><p style="width:170px">Kept?</p></div>
<div class="tt-row"><p class="k" style="width:300px">Who was at the other end</p><p style="flex:1">Steadier ratings in 200 of 200 split tests for batters and 194 of 200 for bowlers</p><p class="k" style="width:170px">Yes</p></div>
<div class="tt-row"><p class="k" style="width:300px">The ground, for pace and spin</p><p style="flex:1">Steadier for bowlers. For batters it was less steady, probably because a ground and its home batters are hard to separate</p><p class="k" style="width:170px">Bowlers only</p></div>
<div class="tt-row"><p class="k" style="width:300px">Dew in night chases</p><p style="flex:1">Less than 1 run per 100 balls</p><p class="k" style="width:170px">No need</p></div>
<div class="tt-row"><p class="k" style="width:300px">Playing at home</p><p style="flex:1">About 1 run per 100 balls, in T20Is only</p><p class="k" style="width:170px">Yes, tiny</p></div>
</div>
</div>
<p class="note">Hardest bowler to face: <b>Jasprit Bumrah</b>, 22 runs per 100 balls below average. Hardest batter to bowl at: <b>Abhishek Sharma</b>. Biggest ground effect for pace: Chepauk saves about 2 runs every 4 overs, Eden Gardens costs about 2.</p>
{FOOT}
</section>
'''
wr(S + 'adjust.html', adjust)
bs = json.load(open('outputs/v3/behaviour_summary.json')); fm = json.load(open('outputs/v3/form_summary.json'))
sq = bs['squeeze_out_rate'] / bs['squeeze_exp_out'] - 1
repeats = f'''<section id="repeats">
<div class="head"><p class="eyebrow">2 · WHAT I LEARNED BUILDING IT</p><h2>Five more pressure ideas, tested the same way</h2></div>
<div class="ttable tt-sm">
<div class="tt-head"><p style="width:380px">The idea</p><p style="flex:1">What the data said (numbers: how well two halves of a player’s matches agree)</p><p style="width:300px">What I did</p></div>
<div class="tt-row"><p class="k" style="width:380px">Hot form matters most</p><p style="flex:1">I let the data decide how much last season should count: about {round(50 * (fm["bat"]["weight_last_season"] + fm["bowl"]["weight_last_season"])):.0f}%, the same as any other season.</p><p style="width:300px">Every season counts equally</p></div>
<div class="tt-row"><p class="k" style="width:380px">Some players have bad days</p><p style="flex:1">How often a player has a costly pressure innings or spell doesn’t repeat ({fmtv(bs["badday_repeat_bat"][0])} batters, {fmtv(bs["badday_repeat_bowl"][0])} bowlers).</p><p style="width:300px">Not used</p></div>
<div class="tt-row"><p class="k" style="width:380px">Dot balls build pressure</p><p style="flex:1">After two dots on pressure balls, batters get out {round(100 * sq):.0f}% more often than expected. That could be chance, and it doesn’t repeat by player ({fmtv(bs["squeeze_out_repeat"][0])}).</p><p style="width:300px">Not used</p></div>
<div class="tt-row"><p class="k" style="width:380px">Fast bowlers slow down</p><p style="flex:1">Pace on pressure balls changes by {bs["league_pace_change_P"]:+.1f} km/h on average, and it doesn’t repeat ({fmtv(bs["pace_P_repeat"][0])}).</p><p style="width:300px">Not used</p></div>
<div class="tt-row"><p class="k" style="width:380px">Bowlers miss their length</p><p style="flex:1">Full tosses, wides and no-balls above the normal rate for that over repeat strongly ({fmtv(bs["exec_P_repeat"][0])}), but they don’t predict next season’s results.</p><p style="width:300px">Shown in my bowler notes</p></div>
</div>
<p class="hl-y" style="font-size:26px; line-height:1.4">Under pressure, results are noisy and habits are steady. Even the one habit that repeats doesn’t tell you who wins games, so I rank on results, weighted by pressure.</p>
{FOOT}
</section>
'''
wr(S + 'repeats.html', repeats)
# ---------------- deck order
dj = json.load(open(D + 'deck.json'))
o = [x for x in dj['order'] if x not in ('adjust', 'repeats')]
o.insert(o.index('measure') + 1, 'adjust'); o.insert(o.index('clutch') + 1, 'repeats'); dj['order'] = o
json.dump(dj, open(D + 'deck.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('order:', o)
print('BAT', BAT, '\nBOWL', BOWL)
