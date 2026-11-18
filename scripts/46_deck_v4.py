"""Deck v4: RR squad fit (new slide 18), shot choice (idea 6, Kohli row, batter notes), and the small fixes from the rules check."""
import json, re
D = 'deck/project/'; S = D + 'slides/'
SH = json.load(open('outputs/v3/shot_choice.json')); SQ = json.load(open('outputs/v3/squad_fit.json'))

def edit(sid, pairs):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (sid, s.count(old), old[:80]); s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

ORD = {1: '1st', 2: '2nd', 3: '3rd'}
ordn = lambda n: ORD.get(n, f'{n}th')
cell = {(c['role'], c['phase']): c for c in SQ['rr_cells']}
for c in SQ['rr_cells']:
    assert c['teams'] == 10

# ---------- 1. new slide: how the picks fit RR's pressure gaps
def grid_cell(role, ph):
    r = cell[(role, ph)]['rr_rank']
    inner = f'<p class="hlc">{ordn(r)}</p>' if r >= 8 else f'<p>{ordn(r)}</p>'
    return f'<div class="gr-c">{inner}</div>'
players = SQ['players']
most_after6 = sum(p['share_7_20'] > 0.5 for p in players)
def bars(role, cls):
    ps = sorted([p for p in players if p['role'] == role], key=lambda p: -p['share_7_20'])
    out = []
    for p in ps:
        nm = p['name'] + ('*' if p['in_rr_2026'] else '')
        w = round(130*p['share_7_20'])
        out.append(f'<div class="sqrow"><p class="sq-nm">{nm}</p><div class="sq-bar"><div class="sq-fill {cls}" style="width:{w}px"></div></div>'
                   f'<p class="sq-v">{100*p["share_7_20"]:.0f}%</p></div>')
    return '\n'.join(out)
bat_mid, bat_d = cell[('bat', 'MID')]['rr_rank'], cell[('bat', 'DEATH')]['rr_rank']
bowl_mid, bowl_d = cell[('bowl', 'MID')]['rr_rank'], cell[('bowl', 'DEATH')]['rr_rank']
squad = f'''<section id="squad-fit">
<div class="head"><p class="eyebrow">4 · EVIDENCE: SQUAD FIT</p><h2>How my picks would strengthen RR</h2></div>
<div class="row" style="gap:64px">
<div class="col" style="width:600px; gap:20px">
<p class="small" style="font-weight:600; letter-spacing:1px">RR UNDER PRESSURE, IPL 2025–26 · RANK OF 10 TEAMS</p>
<div class="col" style="gap:0">
<div class="gr-row gr-head"><p class="gr-k">RR</p><p class="gr-c">Overs 1–6</p><p class="gr-c">7–15</p><p class="gr-c">16–20</p></div>
<div class="gr-row"><p class="gr-k">Batting</p>{grid_cell('bat', 'PP')}{grid_cell('bat', 'MID')}{grid_cell('bat', 'DEATH')}</div>
<div class="gr-row"><p class="gr-k">Bowling</p>{grid_cell('bowl', 'PP')}{grid_cell('bowl', 'MID')}{grid_cell('bowl', 'DEATH')}</div>
</div>
<p class="small">Ranked on the same pressure-weighted value as my ratings, phase by phase. Highlighted: 8th or worse.</p>
<p class="hl-y" style="font-size:26px; line-height:1.4">RR lose ground after over 6: {ordn(bat_mid)} and {ordn(bat_d)} with the bat, {ordn(bowl_mid)} and {ordn(bowl_d)} with the ball. {most_after6} of my 20 picks do most of their pressure work there.</p>
</div>
<div class="row" style="flex:1; gap:40px">
<div class="col" style="flex:1; gap:0">
<p class="sq-h">BATTERS</p>
{bars('bat', 'bat')}
</div>
<div class="col" style="flex:1; gap:0">
<p class="sq-h">BOWLERS</p>
{bars('bowl', 'bowl')}
</div>
</div>
</div>
<p class="small">Bar: share of his pressure balls that come in overs 7–20. * Already in RR’s 2026 squad. Not an auction list: it shows where each pick’s pressure work meets RR’s weak spots.</p>
<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>
<p class="pnum"></p>
</section>
'''
open(S + 'squad-fit.html', 'w', encoding='utf-8').write(squad)

css = open(D + 'deck.css', encoding='utf-8').read()
if '.gr-row {' not in css:
    css += ('\n/* Squad fit: RR rank grid and share-of-pressure bars. */\n'
            '.gr-row { display: flex; align-items: center; height: 56px; border-bottom: 2px solid #E2E0D8; }\n'
            '.gr-row p { font-size: 28px; line-height: 1.2; color: #14213D; font-variant-numeric: tabular-nums; }\n'
            '.gr-head p { font-size: 24px; font-weight: 600; color: #5F6675; }\n'
            '.gr-k { width: 170px; font-weight: 600; }\n'
            '.gr-c { width: 140px; display: flex; justify-content: center; text-align: center; }\n'
            '.sq-h { font-size: 24px; font-weight: 600; letter-spacing: 1px; line-height: 1.2; color: #5F6675; padding-bottom: 8px; border-bottom: 2px solid #E2E0D8; }\n'
            '.sqrow { display: flex; align-items: center; gap: 10px; height: 38px; border-bottom: 2px solid #E2E0D8; }\n'
            '.sqrow p { font-size: 24px; line-height: 1.2; font-variant-numeric: tabular-nums; }\n'
            '.sq-nm { width: 270px; color: #14213D; font-weight: 500; white-space: nowrap; }\n'
            '.sq-bar { width: 130px; height: 14px; background: #E8E6DE; border-radius: 7px; overflow: hidden; }\n'
            '.sq-fill { height: 14px; border-radius: 7px; }\n'
            '.sq-fill.bat { background: #3987E5; }\n'
            '.sq-fill.bowl { background: #EB6834; }\n'
            '.sq-v { width: 56px; text-align: right; color: #14213D; }\n')
    open(D + 'deck.css', 'w', encoding='utf-8').write(css)

dj = json.load(open(D + 'deck.json', encoding='utf-8'))
if 'squad-fit' not in dj['order']:
    i = dj['order'].index('bowl-evidence') + 1; dj['order'].insert(i, 'squad-fit')
dj['sections']['s4']['description'] = 'Evidence for both top 10s, and how they fit RR'
json.dump(dj, open(D + 'deck.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pos = {sid: n for n, sid in enumerate(dj['order'], 1)}
assert pos['kohli'] == 16 and pos['adjust'] == 10

# ---------- 2. shot choice: idea 6, Kohli row, batter notes
rep = SH['bat_choice_repeat'][0]
edit('repeats', [('<h2>Five more pressure ideas, tested the same way</h2>', '<h2>Six more pressure ideas, tested the same way</h2>'),
                 ('Under pressure, results are noisy and habits are steady. Even the one habit that repeats doesn’t tell you who wins games, so I rank on results, weighted by pressure.', 'Habits are steady, results are noisy, and no habit predicted next season, so I rank on results, weighted by pressure.'),
                 ('<p style="width:300px">Shown in my bowler notes</p></div>\n</div>',
                  '<p style="width:300px">Shown in my bowler notes</p></div>\n'
                  '<div class="tt-row"><p class="k" style="width:380px">Good batters pick safer shots</p>'
                  f'<p style="flex:1">How risky a batter’s shots are, against others in the same spot, repeats strongly (+{rep:.2f}) but doesn’t predict next season’s results.</p>'
                  '<p style="width:300px">Shown in my batter notes</p></div>\n</div>')])
s = open(S + 'repeats.html', encoding='utf-8').read()
s, k = re.subn(r'<div class="tt-row">', '<div class="tt-row" style="padding:8px 0">', s); assert k == 6
open(S + 'repeats.html', 'w', encoding='utf-8').write(s)
edit('method', [('ten more pressure ideas', 'six more pressure ideas')])

kgp = SH['kohli_green_pooran']; bpo = lambda r: 100/r['shot_risk_pct']
k_, g_, p_ = (bpo(kgp[n]) for n in ['Virat Kohli', 'Cameron Green', 'Nicholas Pooran'])
edit('kohli', [
    ('<p style="width:150px; text-align:right">20.5</p></div>\n<div class="tt-row" style="padding:13px 0"><p style="flex:1">Runs above average per 100 balls</p>',
     '<p style="width:150px; text-align:right">20.5</p></div>\n'
     f'<div class="tt-row" style="padding:13px 0"><p style="flex:1">An average batter, same shots</p><p class="k" style="width:150px; text-align:right">{k_:.1f}</p><p style="width:150px; text-align:right">{g_:.1f}</p><p style="width:150px; text-align:right">{p_:.1f}</p></div>\n'
     '<div class="tt-row" style="padding:13px 0"><p style="flex:1">Runs above average per 100 balls</p>'),
    ('Green every 27 and Pooran every 21.', f'Green every 27 and Pooran every 21. An average batter playing Kohli’s shots would last {k_:.0f}.')])

top = {r['name']: r for r in SH['top10']}
for n in range(1, 6):
    sid = f'bat-notes-{n}'; s = open(S + sid + '.html', encoding='utf-8').read()
    for name, r in top.items():
        i = s.find(f'<h3>{name}</h3>')
        if i < 0: continue
        m = re.compile(r'out every <b>([0-9.]+)</b> balls').search(s, i)
        assert m, (sid, name)
        add = f' (an average batter playing his shots: every <b>{100/r["shot_risk_pct"]:.1f}</b>)'
        s = s[:m.end()] + add + s[m.end():]
    open(S + sid + '.html', 'w', encoding='utf-8').write(s)

# ---------- 3. small fixes
edit('bat-notes-4', [('He’s already in RR colours, and I’m glad. ', 'He’s already in RR’s 2026 squad. ')])
edit('bowl-notes-4', [('He’s done it in an RR shirt too. In 2025 he took 4 for 35', 'He did it for RR in 2025 too: 4 for 35')])
edit('limits', [
    ('<h3>No T20 World Cup games</h3><p>The data pack has Asia Cups but no World Cup matches, so the biggest stage is missing from this pressure test.</p>',
     '<h3>No World Cups, few knockouts</h3><p>The data pack has Asia Cups but no World Cup matches, and only 31 knockout games: too few to rate on. The Index scores the tight moments in every game instead.</p>'),
    ('<h3>No line, length or field data</h3><p>I can’t tell a good ball from a bad shot. Delivery tags feed the missed-delivery check in my bowler notes, not the rating.</p>',
     '<h3>Little line or length data</h3><p>Only extreme lengths are tagged (yorkers, full tosses, bouncers: 12% of balls). Line and field placings aren’t recorded, so I can’t tell a good ball from a bad shot. Ground, pitch, dew and home are on slide 10.</p>')])
edit('data', [('which are left out anyway.</p></div>',
               'which are left out anyway.</p>\n<p class="small">Public information is used only for ground names and player background in my notes. Every number comes from the data pack.</p></div>')])
s = open(S + 'data.html', encoding='utf-8').read(); s, k = re.subn(r'<div class="tt-row" style="padding:12px 0">', '<div class="tt-row" style="padding:9px 0">', s); assert k == 6
open(S + 'data.html', 'w', encoding='utf-8').write(s)
edit('reproduce', [('<p><b>12_final_ratings</b> and <b>30</b> to <b>37</b>: player stats, the opponent and ground adjustments, the tests, 2,000 resamples and every number in this deck.</p>',
                    '<p><b>12_final_ratings</b>, <b>30</b> to <b>37</b>, <b>44</b> and <b>45</b>: player stats, the opponent and ground adjustments, the tests, 2,000 resamples, shot choice, the RR squad fit and every number in this deck.</p>')])
nb = f'Notes on each batter: slides {pos["bat-notes-1"]} to {pos["bat-notes-5"]}.'; nw = f'Notes on each bowler: slides {pos["bowl-notes-1"]} to {pos["bowl-notes-5"]}.'
for sid, pat, new in [('bat-evidence', r'Notes on each batter: slides \d+ to \d+\.', nb), ('bowl-evidence', r'Notes on each bowler: slides \d+ to \d+\.', nw)]:
    s = open(S + sid + '.html', encoding='utf-8').read(); s, k = re.subn(pat, new, s); assert k == 1, sid
    open(S + sid + '.html', 'w', encoding='utf-8').write(s)
print(dj['order']); print(nb, nw, 'most after over 6:', most_after6, 'Kohli/Green/Pooran', round(k_, 1), round(g_, 1), round(p_, 1))
