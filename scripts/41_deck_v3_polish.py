"""Final pass after the v3 update: cover and method slides describe the final model; two wording fixes for precision."""
S = 'deck/project/slides/'
def edit(sid, pairs):
    p = S + sid + '.html'; s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (sid, s.count(old), old[:70]); s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)
edit('cover', [
 ('<p class="cv-sub">I scored every ball by how far it could swing the match, then ranked the batters and bowlers who deliver on the balls that matter most.</p>',
  '<p class="cv-sub" style="width:1520px">I scored every ball by how far it could swing the match, tested which pressure skills repeat, and rated each player against the opponents he faced.</p>'),
 ('<p class="cv-scope">IPL 2022–26 and T20Is between full members · 735 matches · 175,862 balls</p>',
  '<p class="cv-scope">IPL 2022–26 and T20Is between full members · 735 matches · 175,862 balls · 2,000 resamples</p>')])
edit('method', [
 ('<div class="card" style="flex:1"><p class="num">2</p><h3>Win chance</h3><p>A model gives the batting side’s chance of winning before and after every ball.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">3</p><h3>Pressure Index</h3><p>How far the win chance could move on that ball, ranked from 0 to 100. The top 20% are pressure balls.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">4</p><h3>Value</h3><p>Runs above an average player in the same situation and against the same opposition, with a wicket worth 8 runs.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">5</p><h3>Pressure Rating</h3><p>Average value with each ball weighted by its Pressure Index, pulled toward average when the sample is small.</p></div>',
  '<div class="card" style="flex:1"><p class="num">2</p><h3>Pressure Index</h3><p>A model gives the batting side’s chance of winning before every ball. The Index ranks how far that ball could move it, from 0 to 100. The top 20% are pressure balls.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">3</p><h3>Value</h3><p>Runs above an average player in the same situation, with a wicket worth 8 runs. Then adjusted for the player at the other end, and for the ground if he bowls.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">4</p><h3>Pressure Rating</h3><p>Average value with each ball weighted by its Pressure Index, pulled toward average when the sample is small.</p></div>\n'
  '<div class="card" style="flex:1"><p class="num">5</p><h3>Pick the ten</h3><p>The ten players who stay in the top 10 most often when I resample the matches 2,000 times.</p></div>'),
 ('<b>Then I tried to break it:</b> 2,000 resampled datasets, ten changes to the settings, ten more pressure ideas tested, and a test of whether ratings from 2022–24 predict 2025–26.',
  '<b>Then I tried to break it:</b> ten changes to the settings, ten more pressure ideas, and a test of 2022–24 ratings against 2025–26.')])
edit('adjust', [
 ('<p style="flex:1">Steadier for bowlers. For batters it was less steady, probably because a ground and its home batters are hard to separate</p>',
  '<p style="flex:1">For bowlers it predicts 2025–26 better (0.25 → 0.29). For batters it made ratings less steady, probably because a ground and its home batters are hard to separate</p>')])
edit('repeats', [('about 15%, the same as any other season.', 'about 15%, no more than any other season.')])
print('done')
