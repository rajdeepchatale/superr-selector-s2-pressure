"""Back to the brief: the Round 1 problem statement asks for pressure vs usual performance, two top-10s and a five-part
methodology report. RR squad fit is not in it, so the squad-fit slide and every mention of it come out."""
import json, re, os
D = 'deck/project/'; S = D + 'slides/'
dj = json.load(open(D + 'deck.json', encoding='utf-8'))
dj['order'] = [x for x in dj['order'] if x != 'squad-fit']
dj['sections']['s0']['description'] = 'The answer, the method in brief and the data'
dj['sections']['s4']['description'] = 'Evidence for both top 10s'
assert all(v['start'] != 'squad-fit' for v in dj['sections'].values())
json.dump(dj, open(D + 'deck.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
if os.path.exists(S + 'squad-fit.html'): os.remove(S + 'squad-fit.html')
pos = {sid: n for n, sid in enumerate(dj['order'], 1)}

def edit(sid, pat, rep, n=1):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read(); s, k = re.subn(pat, rep, s); assert k == n, (sid, pat, k)
    open(p, 'w', encoding='utf-8').write(s)
edit('bat-notes-5', r'Why he edges Green and Pooran is on slide \d+', f'Why he edges Green and Pooran is on slide {pos["kohli"]}')
edit('limits', r'Ground, pitch, dew and home are on slide \d+\.', f'Ground, pitch, dew and home are on slide {pos["adjust"]}.')
edit('bat-evidence', r'Notes on each batter: slides \d+ to \d+\.', f'Notes on each batter: slides {pos["bat-notes-1"]} to {pos["bat-notes-5"]}.')
edit('bowl-evidence', r'Notes on each bowler: slides \d+ to \d+\.', f'Notes on each bowler: slides {pos["bowl-notes-1"]} to {pos["bowl-notes-5"]}.')
edit('bat-notes-4', r'He’s already in RR’s 2026 squad\. ', '')
edit('reproduce', re.escape('<b>12_final_ratings</b>, <b>30</b> to <b>37</b>, <b>44</b> and <b>45</b>: player stats, the opponent and ground adjustments, the tests, 2,000 resamples, shot choice, the RR squad fit and every number in this deck.'),
     '<b>12_final_ratings</b>, <b>30</b> to <b>37</b> and <b>44</b>: player stats, the opponent and ground adjustments, the tests, 2,000 resamples, shot choice and every number in this deck.')
assert pos['kohli'] == pos['bat-evidence'] + 1 and pos['kohli'] == 16 and pos['adjust'] == 10
print(len(dj['order']), 'slides;', {k: pos[k] for k in ['method', 'adjust', 'clutch', 'bat-evidence', 'kohli', 'stress', 'limits', 'bat-notes-1', 'bowl-notes-5', 'reproduce', 'appendix']})
