"""Builds the Selector's War Room page (one self-contained HTML file) from outputs/v3/warroom.json.
Made for first-time viewers: a 3-step explainer, one-click "what if" buttons, a plain-language result line,
a glossary, and the full settings tucked under "Mix your own settings"."""
import json, os
W = json.load(open('outputs/v3/warroom.json'))
final = W['final']; combos = W['combos']
names = sorted({n for c in combos.values() for r in ('bat', 'bowl') for n, _, _ in c[r]} | set(final['bat']) | set(final['bowl']))
idx = {n: i for i, n in enumerate(names)}
packed = {k: {r: [[idx[n], rt, round(p, 2)] for n, rt, p in v[r]] for r in ('bat', 'bowl')} for k, v in combos.items()}
surv = {}
for r in ('bat', 'bowl'):
    for n in final[r]:
        surv[n] = sum(n in [x[0] for x in v[r][:10]] for v in combos.values()) / len(combos)
data = {'names': names, 'final': {r: [idx[n] for n in final[r]] for r in final}, 'combos': packed,
        'surv': {r: sorted([[idx[n], round(surv[n], 3)] for n in final[r]], key=lambda x: -x[1]) for r in final}, 'n': len(combos)}
js = json.dumps(data, separators=(',', ':'))
page = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Selector's War Room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  /* One light world, matching the report deck: cream paper, navy ink, blue for batters, orange for bowlers.
     Layout: explainer, then what-if buttons, then the answer (one sentence + two lists), then detail further down. */
  --bg: #F5F4EF; --paper: #FCFBF8; --ink: #14213D; --text: #3B4252; --muted: #5F6675; --line: #E2E0D8;
  --bat: #2A78D6; --bowl: #EB6834; --hl: #FFE47A; --warn: #A15C07;
  --display: 'Space Grotesk', 'Segoe UI', Arial, sans-serif; --body: 'Inter', 'Segoe UI', Arial, sans-serif;
  color-scheme: light;
}
* { box-sizing: border-box; margin: 0; }
html, body { background: var(--bg); color: var(--text); font-family: var(--body); font-size: 16px; line-height: 1.5; }
.wrap { max-width: 1160px; margin: 0 auto; padding: 32px 20px 56px; display: flex; flex-direction: column; gap: 26px; }
.eyebrow { font-size: 13px; font-weight: 600; letter-spacing: 1.5px; color: var(--muted); text-transform: uppercase; }
h1 { font-family: var(--display); font-size: 42px; line-height: 1.05; color: var(--ink); letter-spacing: -0.5px; text-wrap: balance; }
h2 { font-family: var(--display); font-size: 22px; color: var(--ink); text-wrap: balance; }
h3 { font-family: var(--display); font-size: 18px; color: var(--ink); }
.lede { font-size: 18px; max-width: 68ch; }
header { display: flex; flex-direction: column; gap: 10px; }
.card { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px; display: flex; flex-direction: column; gap: 14px; }
.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.step { display: flex; gap: 12px; }
.step .n { font-family: var(--display); font-size: 26px; font-weight: 700; color: var(--ink); line-height: 1; min-width: 22px; }
.step p { font-size: 15px; }
.step b { color: var(--ink); }
.hint { font-size: 15px; color: var(--muted); }
.whatifs { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
.wi { text-align: left; font: inherit; background: var(--bg); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; cursor: pointer; display: flex; flex-direction: column; gap: 2px; }
.wi:hover { border-color: #A9A69C; }
.wi .t { font-weight: 600; color: var(--ink); font-size: 15px; }
.wi .d { font-size: 13px; color: var(--muted); }
.wi[aria-pressed="true"] { background: var(--ink); border-color: var(--ink); }
.wi[aria-pressed="true"] .t { color: #FFFFFF; } .wi[aria-pressed="true"] .d { color: #C9D2E3; }
button:focus-visible, summary:focus-visible { outline: 3px solid var(--hl); outline-offset: 2px; }
.answer { font-size: 18px; color: var(--ink); background: #FFF6CC; border-left: 5px solid var(--hl); border-radius: 8px; padding: 14px 16px; }
.answer b { font-weight: 700; }
.summary { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.tile { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 14px 20px; display: flex; align-items: baseline; gap: 14px; }
.tile.bat { border-top: 4px solid var(--bat); } .tile.bowl { border-top: 4px solid var(--bowl); }
.tile .big { font-family: var(--display); font-size: 38px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
.tile .cap { font-size: 15px; }
.lists { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
.list { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px 18px; display: flex; flex-direction: column; gap: 8px; }
.list h2.bat { color: #1D5BA8; } .list h2.bowl { color: #B4471A; }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th { text-align: left; font-size: 12px; font-weight: 600; letter-spacing: .4px; color: var(--muted); text-transform: uppercase; padding: 6px; border-bottom: 1px solid #C9C6BB; }
td { padding: 7px 6px; border-bottom: 1px solid var(--line); font-size: 15px; vertical-align: middle; }
td.rk { width: 30px; color: var(--muted); } td.nm { color: var(--ink); font-weight: 500; }
td.num, th.num { text-align: right; width: 60px; }
td.share { width: 200px; }
.sw { display: flex; align-items: center; gap: 8px; } .sw .sbar { flex: 1; }
.sbar { position: relative; height: 8px; border-radius: 4px; background: var(--line); }
.sbar span { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px; }
.bat .sbar span { background: var(--bat); } .bowl .sbar span { background: var(--bowl); }
.pct { width: 40px; text-align: right; font-size: 14px; font-variant-numeric: tabular-nums; }
.chip { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .4px; border-radius: 999px; padding: 2px 8px; margin-left: 8px; vertical-align: 2px; background: var(--hl); color: var(--ink); }
.dropped { font-size: 14px; color: var(--muted); padding-top: 6px; }
.dropped b { color: var(--warn); font-weight: 600; }
details.card > summary { cursor: pointer; font-family: var(--display); font-size: 18px; font-weight: 600; color: var(--ink); list-style: none; display: flex; justify-content: space-between; align-items: center; }
details.card > summary::-webkit-details-marker { display: none; }
details.card > summary::after { content: '+'; font-size: 24px; color: var(--muted); }
details[open].card > summary::after { content: '−'; }
.ctrl { display: grid; grid-template-columns: 240px 1fr; gap: 12px; align-items: center; }
.ctrl .lab { font-weight: 600; color: var(--ink); font-size: 15px; }
.ctrl .lab small { display: block; font-weight: 400; color: var(--muted); font-size: 13px; }
.seg { display: flex; flex-wrap: wrap; gap: 6px; }
.seg button { font: 500 14px/1 var(--body); color: var(--ink); background: var(--bg); border: 1px solid var(--line); border-radius: 999px; padding: 9px 14px; cursor: pointer; }
.seg button[aria-pressed="true"] { background: var(--ink); color: #FFFFFF; border-color: var(--ink); }
.mine { font-size: 11px; font-weight: 600; letter-spacing: .4px; margin-left: 6px; opacity: .75; }
.reset { align-self: flex-start; font: 600 14px/1 var(--body); color: var(--ink); background: var(--hl); border: 0; border-radius: 999px; padding: 10px 16px; cursor: pointer; }
.surv { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.srow { display: grid; grid-template-columns: 190px 1fr 48px; gap: 10px; align-items: center; font-size: 14px; padding: 4px 0; }
.srow .n { color: var(--ink); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.srow .v { text-align: right; font-variant-numeric: tabular-nums; }
dl.gloss { display: grid; grid-template-columns: 230px 1fr; gap: 10px 18px; }
dl.gloss dt { font-weight: 600; color: var(--ink); }
dl.gloss dd { font-size: 15px; }
.notes { font-size: 13px; color: var(--muted); max-width: 90ch; display: flex; flex-direction: column; gap: 6px; }
@media (max-width: 820px) {
  h1 { font-size: 32px; } .steps, .summary, .lists, .surv { grid-template-columns: 1fr; }
  .ctrl, dl.gloss { grid-template-columns: 1fr; gap: 6px; }
  td.share { width: 120px; } .srow { grid-template-columns: 130px 1fr 44px; }
}
@media (prefers-reduced-motion: no-preference) { .sbar span { transition: width .35s ease; } }
</style>
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow">SupeRR Selector Season 2 · companion to my methodology report</p>
<h1>Selector's War Room</h1>
<p class="lede">Test my top 10s yourself. Click a "what if" below and see which players stay and who comes in.</p>
</header>

<section class="card" aria-label="How the ranking works">
<h2>How my ranking works, in 3 steps</h2>
<div class="steps">
<div class="step"><p class="n">1</p><p><b>Every ball gets a Pressure Index from 0 to 100:</b> how much that ball could swing the match. The top 20% are pressure balls.</p></div>
<div class="step"><p class="n">2</p><p><b>Every player gets a rating:</b> runs above an average player in the same spot, with the tight balls counting more.</p></div>
<div class="step"><p class="n">3</p><p><b>My top 10 are the players who stay top 10 most often</b> when I reshuffle the matches 2,000 times. That way luck can't sneak anyone in.</p></div>
</div>
</section>

<section class="card" aria-label="What if">
<h2>Pick a what if</h2>
<p class="hint">Each button changes one thing from my report. The lists below update straight away.</p>
<div class="whatifs" id="whatifs"></div>
</section>

<p class="answer" id="answer" aria-live="polite"></p>

<section class="summary">
<div class="tile bat"><p class="big" id="sum-bat">10/10</p><p class="cap">of my ten batters stay in the top 10</p></div>
<div class="tile bowl"><p class="big" id="sum-bowl">10/10</p><p class="cap">of my ten bowlers stay in the top 10</p></div>
</section>

<section class="lists">
<div class="list bat"><h2 class="bat">Batters</h2><table><thead><tr><th>#</th><th>Player</th><th>Top 10 in reshuffles</th><th class="num">Rating</th></tr></thead><tbody id="t-bat"></tbody></table><p class="dropped" id="d-bat"></p></div>
<div class="list bowl"><h2 class="bowl">Bowlers</h2><table><thead><tr><th>#</th><th>Player</th><th>Top 10 in reshuffles</th><th class="num">Rating</th></tr></thead><tbody id="t-bowl"></tbody></table><p class="dropped" id="d-bowl"></p></div>
</section>

<details class="card" id="mix">
<summary>Mix your own settings</summary>
<p class="hint">Change several things at once. There are 90 combinations in all.</p>
<div class="ctrl"><p class="lab" id="l-w">How much pressure counts<small>the weight of each ball</small></p><div class="seg" role="group" aria-labelledby="l-w" data-key="w"></div></div>
<div class="ctrl"><p class="lab" id="l-r">Recent seasons<small>2022 to 2026</small></p><div class="seg" role="group" aria-labelledby="l-r" data-key="r"></div></div>
<div class="ctrl"><p class="lab" id="l-k">A wicket is worth<small>in runs</small></p><div class="seg" role="group" aria-labelledby="l-k" data-key="k"></div></div>
<div class="ctrl"><p class="lab" id="l-a">Who they faced and the ground<small>opponent and ground adjustments</small></p><div class="seg" role="group" aria-labelledby="l-a" data-key="a"></div></div>
<button class="reset" id="reset" type="button">Back to my settings</button>
</details>

<section class="card">
<h2 id="surv-h">How sure am I about each pick?</h2>
<p class="hint" id="surv-p"></p>
<div class="surv"><div class="bat" id="s-bat"></div><div class="bowl" id="s-bowl"></div></div>
</section>

<section class="card" aria-label="Words used on this page">
<h2>Words used on this page</h2>
<dl class="gloss">
<dt>Pressure Index</dt><dd>0 to 100. How far one ball could move the batting side's chance of winning, ranked against every other ball. 80 or more is a pressure ball.</dd>
<dt>Rating</dt><dd>Runs a player adds above an average player in the same spot: per 100 balls faced for batters, runs saved per 24 balls for bowlers. Pressure balls count more.</dd>
<dt>Top 10 in reshuffles</dt><dd>I rebuild the data 2,000 times by picking matches at random, then rank everyone again. This is how often a player lands in the top 10. 50% is a coin flip.</dd>
<dt>Recent seasons count more</dt><dd>A "2-year half-life" means a season counts half as much as the season two years after it, so 2024 counts half as much as 2026.</dd>
<dt>Who they faced and the ground</dt><dd>Runs off Jasprit Bumrah count for more than runs off a weak bowler. Bowlers also get credit for bowling at batting-friendly grounds.</dd>
<dt>NEW</dt><dd>A player who is not in my top 10 in the report.</dd>
</dl>
</section>

<section class="notes">
<p>"Only the tensest balls" and "1-year half-life" use the least information, so they move the lists the most. The report explains why I don't rank on them.</p>
<p>My settings use 2,000 reshuffles, as in the report. Every other option uses 200, so players near the cut can move a few points between runs.</p>
<p>The stress-test slide in my report counts a straight sort by rating. This page picks with the reshuffle rule, so a few counts differ from that slide.</p>
<p>Built from the SupeRR Selector Season 2 data pack: IPL 2022 to 2026 and T20Is between full members. This page holds player ratings only, never ball-by-ball data.</p>
</section>
</div>
<script>
const D = __DATA__;
const MINE = {w: 'idx', r: 'none', k: '8', a: 'on'};
const WHATIFS = [
  ['mine', 'My settings', 'The version in my report.', {}],
  ['more', 'Pressure counts even more', 'Tight balls get much more weight.', {w: 'idx2'}],
  ['equal', 'Every ball counts the same', 'Ignore pressure completely.', {w: 'eq'}],
  ['tense', 'Only the tensest balls', 'Use just the top 20% of balls.', {w: 'ponly'}],
  ['recent', 'Recent seasons count more', '2026 counts double 2024.', {r: 'hl2'}],
  ['wicket', 'A wicket is worth more', '11 runs instead of 8.', {k: '11'}],
  ['noadj', 'Ignore who they faced', 'No opponent or ground adjustment.', {a: 'off'}]
];
const OPTS = {
  w: [['eq', 'Every ball equal'], ['sqrt', 'A little'], ['idx', 'By the Index', 1], ['idx2', 'A lot'], ['ponly', 'Tensest balls only']],
  r: [['none', 'Count equally', 1], ['hl2', '2-year half-life'], ['hl1', '1-year half-life']],
  k: [['5', '5'], ['8', '8', 1], ['11', '11']],
  a: [['on', 'On', 1], ['off', 'Off']]
};
let state = {...MINE};
const key = s => [s.w, s.r, s.k, s.a].join('|');
const esc = s => s.replace(/[&<>]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]));
const nm = i => esc(D.names[i]);
function list(arr) { return arr.length < 2 ? arr.join('') : arr.slice(0, -1).join(', ') + ' and ' + arr[arr.length - 1]; }
function buildButtons() {
  const box = document.getElementById('whatifs');
  WHATIFS.forEach(([id, t, d, ch]) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'wi'; b.id = 'wi-' + id;
    b.innerHTML = `<span class="t">${t}</span><span class="d">${d}</span>`;
    b.addEventListener('click', () => { state = {...MINE, ...ch}; render(); });
    box.appendChild(b);
  });
  document.querySelectorAll('.seg').forEach(g => {
    const k = g.dataset.key;
    OPTS[k].forEach(([val, text, mine]) => {
      const b = document.createElement('button'); b.type = 'button'; b.id = `opt-${k}-${val}`;
      b.innerHTML = text + (mine ? '<span class="mine">MINE</span>' : '');
      b.addEventListener('click', () => { state[k] = val; render(); });
      g.appendChild(b);
    });
  });
}
function render() {
  const c = D.combos[key(state)];
  const active = WHATIFS.find(([, , , ch]) => key({...MINE, ...ch}) === key(state));
  document.querySelectorAll('.wi').forEach(b => b.setAttribute('aria-pressed', active && b.id === 'wi-' + active[0] ? 'true' : 'false'));
  document.querySelectorAll('.seg button').forEach(b => { const [, k, v] = b.id.split('-'); b.setAttribute('aria-pressed', state[k] === v ? 'true' : 'false'); });
  const parts = [];
  for (const role of ['bat', 'bowl']) {
    const mine = new Set(D.final[role]); const rows = c[role].slice(0, 10); const top = new Set(rows.map(r => r[0]));
    const kept = D.final[role].filter(i => top.has(i)); const out = D.final[role].filter(i => !top.has(i)); const inn = rows.filter(r => !mine.has(r[0])).map(r => r[0]);
    document.getElementById('sum-' + role).textContent = `${kept.length}/10`;
    document.getElementById('t-' + role).innerHTML = rows.map((r, i) => {
      const [id, rt, p] = r; const pc = Math.round(p * 100);
      return `<tr><td class="rk">${i + 1}</td><td class="nm">${nm(id)}${mine.has(id) ? '' : '<span class="chip">NEW</span>'}</td>` +
        `<td class="share"><div class="sw"><div class="sbar"><span style="width:${pc}%"></span></div><span class="pct">${pc}%</span></div></td>` +
        `<td class="num">${role === 'bat' ? rt.toFixed(1) : rt.toFixed(2)}</td></tr>`;
    }).join('');
    document.getElementById('d-' + role).innerHTML = out.length ? `<b>Dropped from my ten:</b> ${list(out.map(nm))}` : 'All ten of my picks are still here.';
    const who = role === 'bat' ? 'batters' : 'bowlers';
    parts.push(out.length === 0 ? `all 10 of my ${who} stay` :
      `${kept.length} of my 10 ${who} stay (${list(out.map(nm))} ${out.length === 1 ? 'drops' : 'drop'} out; ${list(inn.map(nm))} ${inn.length === 1 ? 'comes' : 'come'} in)`);
  }
  const title = active ? active[1] : 'Your mix';
  document.getElementById('answer').innerHTML = active && active[0] === 'mine'
    ? '<b>My settings:</b> these are the two top 10s in my report. Click a what if to see what changes.'
    : `<b>${title}:</b> ${parts[0]}, and ${parts[1]}.`;
}
function survivors() {
  document.getElementById('surv-p').textContent = `How often each of my picks stays in the top 10 across all ${D.n} combinations of settings on this page. The top of each list holds almost everywhere; the last few places are the close calls.`;
  for (const role of ['bat', 'bowl']) {
    document.getElementById('s-' + role).innerHTML = `<h3 style="margin-bottom:6px">${role === 'bat' ? 'Batters' : 'Bowlers'}</h3>` +
      D.surv[role].map(([id, s]) => `<div class="srow"><p class="n">${nm(id)}</p><div class="sbar"><span style="width:${Math.round(s * 100)}%"></span></div><p class="v">${Math.round(s * 100)}%</p></div>`).join('');
  }
}
document.getElementById('reset').addEventListener('click', () => { state = {...MINE}; render(); });
buildButtons(); render(); survivors();
</script>
</body>
</html>
'''
page = page.replace('__DATA__', js)
os.makedirs('warroom', exist_ok=True)
open('warroom/index.html', 'w', encoding='utf-8').write(page)
print('page bytes', len(page.encode()))
