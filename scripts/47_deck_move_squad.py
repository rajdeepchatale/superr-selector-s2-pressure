"""Move the squad-fit slide up to slide 3, so slides 2 to 4 answer all three things the rules ask for:
the picks, how each could strengthen RR, and the method. Slide-number references are recomputed."""
import json, re
D = 'deck/project/'; S = D + 'slides/'
dj = json.load(open(D + 'deck.json', encoding='utf-8'))
old = {sid: n for n, sid in enumerate(dj['order'], 1)}
order = [x for x in dj['order'] if x != 'squad-fit']; order.insert(order.index('answer') + 1, 'squad-fit')
dj['order'] = order
dj['sections']['s0']['description'] = 'The answer, how the picks fit RR, the method in brief and the data'
dj['sections']['s4']['description'] = 'Evidence for both top 10s'
json.dump(dj, open(D + 'deck.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pos = {sid: n for n, sid in enumerate(order, 1)}

def edit(sid, pat, rep, n=1):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read(); s, k = re.subn(pat, rep, s); assert k == n, (sid, pat, k)
    open(p, 'w', encoding='utf-8').write(s)
edit('squad-fit', r'<p class="eyebrow">[^<]*</p>', '<p class="eyebrow">THE SHORT VERSION · SQUAD FIT</p>')
edit('bat-notes-5', r'Why he edges Green and Pooran is on slide \d+', f'Why he edges Green and Pooran is on slide {pos["kohli"]}')
edit('limits', r'Ground, pitch, dew and home are on slide \d+\.', f'Ground, pitch, dew and home are on slide {pos["adjust"]}.')
edit('bat-evidence', r'Notes on each batter: slides \d+ to \d+\.', f'Notes on each batter: slides {pos["bat-notes-1"]} to {pos["bat-notes-5"]}.')
edit('bowl-evidence', r'Notes on each bowler: slides \d+ to \d+\.', f'Notes on each bowler: slides {pos["bowl-notes-1"]} to {pos["bowl-notes-5"]}.')
assert pos['kohli'] == pos['bat-evidence'] + 1          # "More on the next slide" on the batter table still points at Kohli
print({k: (old[k], pos[k]) for k in ['answer', 'squad-fit', 'method', 'data', 'pressure-def', 'adjust', 'kohli', 'bowl-evidence', 'stress', 'limits']})
