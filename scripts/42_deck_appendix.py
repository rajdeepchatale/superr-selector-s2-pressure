"""Move the player notes into an appendix so the main argument runs unbroken from slide 1 to 19."""
import json, re
D = 'deck/project/'; S = D + 'slides/'
NOTES = [f'bat-notes-{i}' for i in range(1, 6)] + [f'bowl-notes-{i}' for i in range(1, 6)]
dj = json.load(open(D + 'deck.json', encoding='utf-8'))
order = [x for x in dj['order'] if x not in NOTES]
i = order.index('reproduce'); order[i:i] = NOTES
dj['order'] = order
dj['sections'] = {
    's0': {'description': 'The answer, the method in brief and the data', 'start': 'cover'},
    's1': {'description': 'How I define pressure', 'start': 'pressure-def'},
    's2': {'description': 'How I measure performance and build the rating', 'start': 'measure'},
    's3': {'description': 'Keeping the comparisons fair', 'start': 'fair'},
    's4': {'description': 'Evidence for both top 10s', 'start': 'bat-evidence'},
    's5': {'description': 'Reliability and limitations', 'start': 'stress'},
    's6': {'description': 'Appendix: notes on every player, how to reproduce it, model details', 'start': 'bat-notes-1'}}
json.dump(dj, open(D + 'deck.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pos = {sid: n for n, sid in enumerate(order, 1)}
def edit(sid, pairs):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (sid, s.count(old), old[:70]); s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)
for sid in NOTES:
    lab = 'BATTER' if sid.startswith('bat') else 'BOWLER'
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    s, n = re.subn(rf'<p class="eyebrow">4 · EVIDENCE: {lab} NOTES · ', f'<p class="eyebrow">APPENDIX · {lab} NOTES · ', s); assert n == 1, sid
    open(p, 'w', encoding='utf-8').write(s)
edit('reproduce', [('<p class="eyebrow">5 · REPRODUCIBILITY</p>', '<p class="eyebrow">APPENDIX · REPRODUCIBILITY</p>')])
edit('bat-evidence', [('Picked by the resample rule, ordered by rating.', f'Notes on each batter: slides {pos["bat-notes-1"]} to {pos["bat-notes-5"]}.')])
edit('bowl-evidence', [('Picked by the resample rule, ordered by rating.', f'Notes on each bowler: slides {pos["bowl-notes-1"]} to {pos["bowl-notes-5"]}.')])
assert pos['kohli'] == 16   # the Kohli note points to slide 16
print(order)
