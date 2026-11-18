"""Yellow marks the one thing to read first on every main-report slide; bold carries the supporting phrases.
Slides keeps only colour, bold, italic and underline inside a line, so every yellow mark is a block:
a pill (.hl-y), a highlighted cell (.hlc), a yellow table row (.tt-row.y) or a tinted card (.card.y)."""
import re
D = 'deck/project/'; S = D + 'slides/'

def edit(sid, pairs, regex=()):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (sid, s.count(old), old[:80]); s = s.replace(old, new)
    for pat, rep, n in regex:
        s, k = re.subn(pat, rep, s); assert k == n, (sid, pat, k)
    open(p, 'w', encoding='utf-8').write(s)

css = open(D + 'deck.css', encoding='utf-8').read()
if '.hlc {' not in css:
    css += ('\n/* Highlights: yellow marks what to read first on each slide. */\n'
            '.lrow .pcw, .trow .pcw { display: flex; justify-content: flex-end; padding-right: 0; }\n'
            '.hlc { background: #FFE47A; color: #14213D; font-weight: 700; padding: 0 8px; border-radius: 4px; }\n'
            '.card.y { background: #FFF6CC; border-color: #EBC94A; }\n')
    open(D + 'deck.css', 'w', encoding='utf-8').write(css)

# 2 · the answer: the near-certain picks (75%+ of resamples) light up
edit('answer', [('bold = 75% or more.', 'highlighted = 75% or more.')],
     [(r'<p class="pc g">([^<]*)</p>', r'<div class="pc pcw"><p class="hlc">\1</p></div>', 6)])
# 15 and 17 · same mark on the evidence tables
edit('bat-evidence', [], [(r'<p class="c-pc g">([^<]*)</p>', r'<div class="c-pc pcw"><p class="hlc">\1</p></div>', 2)])
edit('bowl-evidence', [], [(r'<p class="c-pc g">([^<]*)</p>', r'<div class="c-pc pcw"><p class="hlc">\1</p></div>', 4)])

# 3 · method: the stress-testing line, plus the key phrase of each step
edit('method', [
    ('<p class="note"><b>Then I tried to break it:</b>', '<p class="hl-y" style="font-size:26px; line-height:1.4"><b>Then I tried to break it:</b>'),
    ('matched it against the official results.', '<b>matched it against the official results.</b>'),
    ('The top 20% are pressure balls.', '<b>The top 20% are pressure balls.</b>'),
    ('<p>Runs above an average player in the same situation,', '<p><b>Runs above an average player in the same situation</b>,'),
    ('Average value with each ball weighted by its Pressure Index,', 'Average value with <b>each ball weighted by its Pressure Index</b>,'),
    ('The ten players who stay in the top 10 most often', 'The ten players who <b>stay in the top 10 most often</b>')])

# 4 · data: the check against official results
edit('data', [(
    '<p style="font-size:26px; line-height:1.4">Before any modelling I rebuilt every innings total from the ball-by-ball rows. The winning margin matches the official result in <b>396 of 399</b> wins by runs and <b>395 of 396</b> wins by wickets. Three of the four misses are rain-affected games, which are left out anyway.</p>',
    '<div class="col" style="gap:12px">'
    '<p style="font-size:26px; line-height:1.4">Before any modelling I rebuilt every innings total from the ball-by-ball rows.</p>'
    '<p class="hl-y" style="font-size:26px; line-height:1.4">The winning margin matches the official result in <b>396 of 399</b> wins by runs<br>and <b>395 of 396</b> wins by wickets.</p>'
    '<p style="font-size:26px; line-height:1.4">Three of the four misses are rain-affected games, which are left out anyway.</p></div>')])

# 5 · the definition of a pressure ball
edit('pressure-def', [
    ('I let the scoreboard decide.</p>', '<b>I let the scoreboard decide.</b></p>'),
    ('<p>Ranking all balls by leverage gives the Pressure Index. <b>A pressure ball is one in the top 20% (Index 80 or more), about 48 a match.</b></p>',
     '<p>Ranking all balls by leverage gives the Pressure Index.</p><p class="hl-y"><b>A pressure ball is one in the top 20% (Index 80 or more),<br>about 48 a match.</b></p>')])

# 7 · the finish: the story, then the punchline that ties it to the Index
edit('finish', [(
    'IPL 2024, RR chasing 202 against SRH. Every ball in these two overs had a Pressure Index of 99.4 or more. RR’s win chance fell',
    'IPL 2024, RR chasing 202 against SRH. RR’s win chance fell'),
    ('and SRH won by one run.</p>',
     'and SRH won by one run.</p>\n<p class="hl-y" style="font-size:26px; line-height:1.4">Every ball in these two overs had a Pressure Index of 99.4 or more.</p>')])

# 9 · measuring: what the baseline is
edit('measure', [(
    '<p style="font-size:26px; line-height:1.4">The baseline is what an average player does in exactly that spot. Two models',
    '<p class="hl-y" style="font-size:26px; line-height:1.4">The baseline is what an average player does in exactly that spot.</p>\n<p style="font-size:26px; line-height:1.4">Two models')])

# 10 · adjustments: the one that earned its place, and the pitch conclusion in bold
edit('adjust', [
    ('<div class="tt-row"><p class="k" style="width:300px">Who was at the other end</p>',
     '<div class="tt-row y" style="padding:16px 12px; margin:0 -12px"><p class="k" style="width:300px">Who was at the other end</p>'),
    ('The baseline already reads the pitch from the score and the target, so a separate pitch adjustment adds nothing.</p>',
     '<b>The baseline already reads the pitch from the score and the target, so a separate pitch adjustment adds nothing.</b></p>')])

# 11 · rating: how much of the weight sits on pressure balls
edit('rating', [(
    'A ball at 95 counts 0.95 and a ball at 10 counts 0.10. Pressure balls are 20% of all balls but carry 36% of the weight.</p>',
    'A ball at 95 counts 0.95 and a ball at 10 counts 0.10.</p><p class="hl-y">Pressure balls are 20% of all balls but carry 36% of the weight.</p>')])

# 14 · fair comparisons: the pool, and the role point in bold
edit('fair', [
    ('<p style="font-size:26px"><b>102 batters and 74 bowlers qualify.</b></p>', '<p class="hl-y" style="font-size:26px"><b>102 batters and 74 bowlers qualify.</b></p>'),
    ('so a player’s role and phase don’t decide his rating.', '<b>so a player’s role and phase don’t decide his rating.</b>')])

# 18 · reliability: the headline number's caption, plus the two conclusions in bold
edit('stress', [
    ('<p class="bigcap">changes keep at least 8 of my 10 batters and 9 of my 10 bowlers</p>', '<p class="bigcap hl-y">changes keep at least 8 of my 10 batters<br>and 9 of my 10 bowlers</p>'),
    ('The last places in both lists are close calls, between 35% and 49%.', '<b>The last places in both lists are close calls, between 35% and 49%.</b>'),
    ('Bowling carries over from year to year; batting much less.', '<b>Bowling carries over from year to year; batting much less.</b>')])

# 19 · limits: the biggest limit card is tinted, and its advice is bold
edit('limits', [
    ('<div class="card" style="gap:10px"><p class="small" style="font-weight:600; letter-spacing:1px">BIGGEST LIMIT</p>',
     '<div class="card y" style="gap:10px"><p class="small" style="font-weight:600; letter-spacing:1px">BIGGEST LIMIT</p>'),
    ('Read the batting list as the best record so far, not a forecast.', '<b>Read the batting list as the best record so far, not a forecast.</b>')])
print('done')
