"""A first-time reader's map: slide 3 lists what the Round 1 problem statement asks for, my one-line answer,
and where each part is. Slide numbers are computed from the deck order, and every later reference is renumbered."""
import json, re
D = 'deck/project/'; S = D + 'slides/'
dj = json.load(open(D + 'deck.json', encoding='utf-8'))
if 'guide' not in dj['order']:
    dj['order'].insert(dj['order'].index('answer') + 1, 'guide')
dj['sections']['s0']['description'] = 'The answer, how the report follows the brief, the method in brief and the data'
json.dump(dj, open(D + 'deck.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pos = {sid: n for n, sid in enumerate(dj['order'], 1)}
rng = lambda a, b: f'{pos[a]}–{pos[b]}'
rows = [
    ('Pressure definition', 'Every ball gets a Pressure Index: how far it could swing the chance of winning. The top 20% are pressure balls.', rng('pressure-def', 'pressure-value')),
    ('Performance measurement', 'Runs above an average player in the same spot and against the same opponent, with a wicket worth 8 runs. Each ball counts in proportion to its Index.', rng('measure', 'rating')),
    ('Pressure vs usual level', 'I measured it first. It doesn’t repeat from match to match, so I rank on steady performance across tight balls instead.', rng('clutch', 'repeats')),
    ('Fair comparisons', 'Same-situation baselines, opponent and ground adjustments, full-member T20Is only, minimum samples and shrinkage.', f'{pos["adjust"]}, {pos["fair"]}'),
    ('Evidence for my top 10', 'Ratings with 80% ranges, 2,000 resamples, the Kohli call, and notes on all 20 players.', f'{rng("bat-evidence", "bowl-evidence")}, {rng("bat-notes-1", "bowl-notes-5")}'),
    ('Reliability and limitations', 'Ten changes to the method, a 2022–24 vs 2025–26 test, and what the model can’t see.', rng('stress', 'limits')),
    ('Reproducible', 'The scripts in order, every setting, and the model details.', rng('reproduce', 'appendix'))]
row_open = lambda a: '<div class="tt-row y" style="padding:16px 12px; margin:0 -12px">' if a == 'Pressure vs usual level' else '<div class="tt-row">'
body = '\n'.join(f'{row_open(a)}<p class="k" style="width:360px">{a}</p><p style="flex:1">{b}</p><p class="k" style="width:220px; text-align:right">{c}</p></div>' for a, b, c in rows)
open(S + 'guide.html', 'w', encoding='utf-8').write(f'''<section id="guide">
<div class="head"><p class="eyebrow">THE SHORT VERSION</p><h2>How this report answers the brief</h2></div>
<div class="ttable tt-sm">
<div class="tt-head"><p style="width:360px">The brief asks for</p><p style="flex:1">My answer in one line</p><p style="width:220px; text-align:right">Slides</p></div>
{body}
</div>
<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>
<p class="pnum"></p></section>
''')
def edit(sid, pat, rep):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read(); s, k = re.subn(pat, rep, s); assert k == 1, (sid, pat, k)
    open(p, 'w', encoding='utf-8').write(s)
edit('bat-notes-5', r'Why he edges Green and Pooran is on slide \d+', f'Why he edges Green and Pooran is on slide {pos["kohli"]}')
edit('limits', r'Ground, pitch, dew and home are on slide \d+\.', f'Ground, pitch, dew and home are on slide {pos["adjust"]}.')
edit('bat-evidence', r'Notes on each batter: slides \d+ to \d+\.', f'Notes on each batter: slides {pos["bat-notes-1"]} to {pos["bat-notes-5"]}.')
edit('bowl-evidence', r'Notes on each bowler: slides \d+ to \d+\.', f'Notes on each bowler: slides {pos["bowl-notes-1"]} to {pos["bowl-notes-5"]}.')
assert pos['kohli'] == pos['bat-evidence'] + 1
print(len(dj['order']), 'slides'); [print(' ', a, '->', c) for a, _, c in rows]
