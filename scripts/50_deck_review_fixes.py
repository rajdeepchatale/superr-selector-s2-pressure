"""Final review fixes (18 Nov). Every change below was checked against the data or the code:
 1  Slide 9: Powell's lbw came three balls after his four (balls 3 and 6 of the over), not two.
 2  Bowler overs: shown in cricket notation (overs.balls) from exact legal pressure balls, not balls/6 decimals.
 3  Slide 10: opponent adjustment, 200 paired splits (49_paired_splits): batters 200/200, bowlers 133/200.
 4  Bowlers are adjusted for ground, dew and home side (31_adjust_ridge, bowl_v_full); say so everywhere.
 5  Slide 15: four batters out-rate Kohli on straight rating, not two.
 6  Slide 10: Chepauk is the biggest IPL ground effect for pace (a Bangladesh ground is bigger overall).
 7  Slide 24: Kohli's IPL 2026 strike rate is 166.7, so 167.
 8  Slide 13: only two habits repeat; neither predicts next season.
 9  Slide 30: qualification is on pressure balls.
11  Slide 24: drop the Orange Cap clause (reputation, and 2016 is outside the data)."""
import json, re
import pandas as pd
D = 'deck/project/'; S = D + 'slides/'

def edit(sid, pairs):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (sid, s.count(old), old[:90]); s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# 1
edit('measure', [('Two balls later Powell is lbw', 'Three balls later Powell is lbw')])

# 2  exact legal pressure balls -> overs.balls
R = pd.read_pickle('outputs/v3/rated_balls_v3.pkl'); P = R[(R.PI >= 80) & (R.legal == 1)]
lb = P.groupby('bowler_name').size()
names = ['Sunil Narine', 'Kuldeep Yadav', 'Jasprit Bumrah', 'Rashid Khan', 'Josh Hazlewood', 'Varun Chakravarthy', 'Krunal Pandya',
         'Wanindu Hasaranga', 'Nathan Ellis', 'Mujeeb Ur Rahman', 'Matheesha Pathirana']
ov = {n: f'{lb[n]//6}.{lb[n]%6}' for n in names}
s = open(S + 'bowl-evidence.html', encoding='utf-8').read()
for n in names:
    i = s.find(f'<p class="c-nm">{n}</p>'); assert i > 0, n
    m = re.compile(r'<p class="c-n1">([0-9.]+)</p>').search(s, i); assert m and m.start() - i < 900, n
    s = s[:m.start(1)] + ov[n] + s[m.end(1):]
open(S + 'bowl-evidence.html', 'w', encoding='utf-8').write(s)
for k in range(1, 6):
    sid = f'bowl-notes-{k}'; s = open(S + sid + '.html', encoding='utf-8').read(); done = 0
    for n in names:
        i = s.find(f'<h3>{n}</h3>')
        if i < 0: continue
        m = re.compile(r'<b>([0-9.]+)</b> pressure overs').search(s, i); assert m, (sid, n)
        s = s[:m.start(1)] + ov[n] + s[m.end(1):]; done += 1
    assert done == 2, (sid, done)
    open(S + sid + '.html', 'w', encoding='utf-8').write(s)

# 3, 4 (slide 10), 6
pr = json.load(open('outputs/v3/paired_splits.json'))
edit('adjust', [
    ('Steadier ratings in 200 of 200 split tests for batters and 194 of 200 for bowlers',
     f'Steadier ratings in {pr["bat"]["steadier"]} of 200 split tests for batters and {pr["bowl"]["steadier"]} of 200 for bowlers'),
    ('<p class="k" style="width:170px">No need</p>', '<p class="k" style="width:170px">Bowlers, tiny</p>'),
    ('<p class="k" style="width:170px">Yes, tiny</p>', '<p class="k" style="width:170px">Bowlers, tiny</p>'),
    ('Biggest ground effect for pace:', 'Biggest IPL ground effects for pace:')])
# 4 (elsewhere)
edit('method', [('Then adjusted for the player at the other end, and for the ground if he bowls.',
                 'Then adjusted for the player at the other end and, for bowlers, the ground, dew and home side.')])
edit('measure', [('Bowlers are also adjusted for the ground.', 'Bowlers are also adjusted for the ground, dew and home side.')])
edit('limits', [('I adjust for opponents, and bowlers for the ground, but', 'I adjust for opponents, and bowlers for the ground, dew and home side, but')])
edit('appendix', [('Each ball is then adjusted for the player at the other end, and bowlers also for the ground.',
                   'Each ball is then adjusted for the player at the other end, and bowlers also for the ground, dew and home side.')])
# 5
sel = pd.read_csv('outputs/v3/selection_bat_v3.csv', index_col=0).sort_values('rating', ascending=False)
k_rt = sel.loc[sel.name == 'Virat Kohli', 'rating'].iloc[0]
above = sel[(sel.rating > k_rt) & (sel.pick_rank > 10)]
assert list(above.name) == ['Shashank Singh', 'Cameron Green', 'Nicholas Pooran', 'Rinku Singh'], list(above.name)
lo, hi = round(100*above.p_top10.min()), round(100*above.p_top10.max())
edit('bat-evidence', [(
    'He and Nicholas Pooran rate a touch higher than Kohli (12.8 and 12.6 vs 12.2), but Kohli stays in the top 10 in more resamples (35% vs 29% and 27%), and that decides the last place.',
    f'Four batters rate a touch above Kohli’s 12.2 (Shashank Singh 13.1, Green 12.8, Pooran 12.6, Rinku Singh 12.5), but Kohli stays in the top 10 in more resamples (35% vs {lo}–{hi}%), and that decides the last place.')])
# 7, 11
edit('bat-notes-5', [('His IPL strike rate has gone from 116 in 2022 to 166 in 2026, and he won the Orange Cap in 2016 and 2024.',
                      'His IPL strike rate has gone from 116 in 2022 to 167 in 2026.')])
# 8
edit('repeats', [('Habits are steady, results are noisy, and no habit predicted next season, so I rank on results, weighted by pressure.',
                  'Two habits repeat, but neither predicts next season, so I rank on results, weighted by pressure.')])
# 9, and the new test script in the reproduce steps
edit('reproduce', [('>100+ balls, 10+ innings<', '>100+ pressure balls, 10+ innings<'), ('>120+ balls, 10+ spells<', '>120+ pressure balls, 10+ spells<'),
                   ('<b>30</b> to <b>37</b> and <b>44</b>:', '<b>30</b> to <b>37</b>, <b>44</b> and <b>49</b>:')])
print('overs:', ov); print('paired:', pr['bat']['steadier'], pr['bowl']['steadier']); print('above Kohli:', list(above.name), lo, hi)
