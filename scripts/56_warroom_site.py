"""Selector's War Room as a 16:9 click-through website (for GitHub Pages: docs/index.html).

Four tabs: the answer (click a player for his notes), how it works (the 8 steps),
what if (change a setting, lists update), how sure. Data: the War Room combos
(scripts 39-40), the report's top 10s (slide 2, checked against the selection
files here), and the player notes text from the deck. Player ratings only,
never ball-by-ball data.
"""
import html, json, pathlib, re
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
SLIDES = ROOT / "deck/project/slides"
OUT = ROOT / "site/index.html"

# ---------- War Room data, with the report's order ----------
wr = (ROOT / "warroom/index.html").read_text(encoding="utf-8")
D = json.loads(re.search(r"const D = (\{.*?\});\n", wr, re.S).group(1))
IDX = {n: i for i, n in enumerate(D["names"])}

ANS = {
    "bat": [("Suryakumar Yadav", "20.9", 96), ("Abhishek Sharma", "19.9", 92), ("Phil Salt", "17.0", 72),
            ("Heinrich Klaasen", "16.7", 73), ("Tim David", "15.5", 53), ("Reeza Hendricks", "15.1", 56),
            ("Vaibhav Sooryavanshi", "14.5", 44), ("Glenn Phillips", "13.8", 44),
            ("Namboori Tilak Varma", "13.4", 41), ("Virat Kohli", "12.2", 35)],
    "bowl": [("Sunil Narine", "3.83", 90), ("Kuldeep Yadav", "3.34", 82), ("Jasprit Bumrah", "3.33", 77),
             ("Rashid Khan", "3.20", 79), ("Josh Hazlewood", "3.18", 70), ("Varun Chakravarthy", "2.90", 66),
             ("Krunal Pandya", "2.58", 49), ("Wanindu Hasaranga", "2.50", 54), ("Nathan Ellis", "2.49", 48),
             ("Mujeeb Ur Rahman", "2.37", 41)],
}
NEXT = {"bat": ("Cameron Green", "12.8", 29), "bowl": ("Matheesha Pathirana", "2.39", 38)}

# check every shown number against the selection files
for role, f, nd in (("bat", "selection_bat_v3.csv", 1), ("bowl", "selection_bowl_v3.csv", 2)):
    sel = pd.read_csv(ROOT / "outputs/v3" / f).set_index("name")
    for name, rt, p in ANS[role] + [NEXT[role]]:
        assert f"{sel.loc[name, 'rating']:.{nd}f}" == rt, (name, rt)
        assert round(sel.loc[name, "p_top10"] * 100) == p, (name, p)
    D["final"][role] = [IDX[n] for n, _, _ in ANS[role]]
MINE_STR = {role: {IDX[n]: rt for n, rt, _ in ANS[role]} for role in ANS}

# ---------- player notes from the deck ----------
def clean(s):
    return re.sub(r"\s+", " ", s).strip()

P = {}
for role, prefix in (("bat", "bat-notes"), ("bowl", "bowl-notes")):
    for k in range(1, 6):
        s = (SLIDES / f"{prefix}-{k}.html").read_text(encoding="utf-8")
        for card in re.split(r'<div class="ncard[^"]*">', s)[1:]:
            name = re.search(r"<h3>(.*?)</h3>", card).group(1)
            P[name] = {
                "role": clean(re.search(r'<p class="nrole">(.*?)</p>', card).group(1)),
                "stats": clean(re.search(r'<p class="nstats">(.*?)</p>', card).group(1)),
                "notes": [[c.replace("ntext", "").strip(), clean(t)]
                          for c, t in re.findall(r'<p class="(ntext[^"]*)">(.*?)</p>', card)],
            }
assert len(P) == 20, len(P)

# ---------- static parts ----------
def ans_rows(role):
    out = []
    for i, (n, rt, p) in enumerate(ANS[role], 1):
        hi = " hi" if p >= 75 else ""
        out.append(f'<tr class="pl" data-p="{html.escape(n)}" tabindex="0"><td class="rk">{i}</td>'
                   f'<td class="nm">{html.escape(n)}<span class="go">Notes ›</span></td><td class="num">{rt}</td>'
                   f'<td class="sh"><div class="sbar"><span style="width:{p}%"></span></div>'
                   f'<span class="pct{hi}">{p}%</span></td></tr>')
    n, rt, p = NEXT[role]
    return "".join(out), f"Next in line: <b>{n}</b> ({rt}, top 10 in {p}% of resamples)"

STEPS = [
    ("The data", "883 matches, ball by ball. <b>735 rated</b>: IPL 2022–26 and full-member T20Is."),
    ("Win chance", "A model gives the batting side’s <b>chance of winning before every ball</b>."),
    ("Pressure Index", "How far a ball can swing that chance, ranked 0 to 100. <span class='hl'>Top 20% = pressure balls</span>"),
    ("Ball value", "<b>Runs above an average player</b> in that exact spot. A wicket is worth 8 runs."),
    ("Fair comparison", "Adjusted for who they faced. Bowlers also for ground, dew and home side."),
    ("Pressure Rating", "Every ball <b>weighted by its Index</b>, then small samples pulled toward average."),
    ("2,000 resamples", "Redraw the matches 2,000 times and count each player’s top-10 finishes."),
    ("Two top 10s", "The ten who make the top 10 <b>most often</b>, ordered by rating."),
]
def step_html(i, t, d):
    y = " y" if i == 8 else ""
    return f'<div class="step{y}"><div class="stop"><p class="sn">{i}</p><h3>{t}</h3></div><p>{d}</p></div>'
ARROW = '<div class="arr" aria-hidden="true">→</div>'
row1 = ARROW.join(step_html(i + 1, *STEPS[i]) for i in range(4))
row2 = ARROW.join(step_html(i + 1, *STEPS[i]) for i in range(4, 8))

bat_rows, bat_next = ans_rows("bat")
bowl_rows, bowl_next = ans_rows("bowl")

DATA = {"D": D, "P": P, "ANS": ANS, "MINE_STR": MINE_STR}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Selector's War Room · Most reliable under pressure</title>
<meta name="description" content="Rajdeep Chatale's SupeRR Selector Season 2 dashboard: the most reliable batters and bowlers under pressure, how the model works, and what-if tests.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0D1628;overflow:hidden;font-family:Inter,Arial,sans-serif;-webkit-font-smoothing:antialiased}
p,h1,h2,h3{margin:0}
button{font-family:inherit}
#stage{position:absolute;left:0;top:0;width:1600px;height:900px;transform-origin:0 0;background:#F5F4EF;color:#3B4252;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 10px 60px rgba(0,0,0,.35)}
header{height:76px;flex:none;background:#14213D;display:flex;align-items:center;padding:0 40px;gap:24px}
.brand .t{font-family:'Space Grotesk',Arial,sans-serif;font-weight:600;font-size:26px;color:#F5F4EF;line-height:1.1}
.brand .s{font-size:14px;color:#9AA6BC;margin-top:3px;letter-spacing:.3px}
nav{margin-left:auto;display:flex;gap:10px}
nav button{font-weight:600;font-size:16px;color:#D5DCE8;background:transparent;border:1.5px solid #34466B;border-radius:999px;padding:10px 20px;cursor:pointer;transition:background-color .15s,color .15s,border-color .15s}
nav button:hover{border-color:#9AA6BC;color:#F5F4EF}
nav button[aria-selected=true]{background:#FFE47A;border-color:#FFE47A;color:#14213D}
nav button .n{opacity:.65;margin-right:7px}
main{flex:1;position:relative;min-height:0}
.screen{position:absolute;inset:0;padding:30px 40px 22px;display:none;flex-direction:column;gap:20px}
.screen.on{display:flex;animation:in .28s ease-out}
@keyframes in{from{opacity:0;transform:translateY(8px)}}
footer{height:38px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 40px;font-size:13px;color:#6B7280;border-top:1px solid #E2E0D8}
.eb{font-size:13px;font-weight:600;letter-spacing:2px;color:#6B7280;text-transform:uppercase}
h1.st{font-family:'Space Grotesk',Arial,sans-serif;font-weight:600;font-size:36px;color:#14213D;line-height:1.1;margin-top:6px;letter-spacing:-.3px}
.hrow{display:flex;align-items:flex-end;justify-content:space-between;gap:24px}
.hint{font-size:15px;color:#14213D;background:#FFE47A;border-radius:6px;padding:6px 12px;font-weight:600;white-space:nowrap}
.lead{font-size:17px;line-height:1.45;color:#5F6675;max-width:1100px}
.fine{font-size:14px;line-height:1.45;color:#6B7280}
.two{display:grid;grid-template-columns:1fr 1fr;gap:24px;min-height:0}
.card{background:#FCFBF8;border:1.5px solid #E2E0D8;border-radius:14px;padding:20px 24px}
.list{border-top:5px solid #3987E5}
.list.bowl{border-top-color:#EB6834}
.lh{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px}
.list h2{font-family:'Space Grotesk',Arial,sans-serif;font-size:24px;font-weight:600;color:#2A78D6}
.list.bowl h2{color:#D4572A}
table{width:100%;border-collapse:collapse}
th{font-size:12px;font-weight:600;letter-spacing:1px;color:#6B7280;text-transform:uppercase;text-align:left;padding:6px 8px;border-bottom:1.5px solid #E2E0D8}
th.r,td.num{text-align:right}
td{font-size:17px;padding:0 8px;height:44px;border-bottom:1px solid #EEECE5;color:#14213D}
tr:last-child td{border-bottom:none}
td.rk{width:36px;color:#6B7280;font-variant-numeric:tabular-nums}
td.nm{font-weight:600}
td.num{font-variant-numeric:tabular-nums;font-weight:600;width:70px}
td.sh{width:230px}
.sbar{display:inline-block;vertical-align:middle;width:150px;height:8px;border-radius:4px;background:#E6E3DA;overflow:hidden;margin-right:10px}
.sbar span{display:block;height:100%;border-radius:4px;background:#3987E5}
.bowl .sbar span{background:#EB6834}
.pct{font-variant-numeric:tabular-nums;font-size:15px;font-weight:600;color:#3B4252;padding:2px 6px;border-radius:5px}
.pct.hi{background:#FFE47A;color:#14213D}
tr.pl{cursor:pointer;transition:background-color .12s}
tr.pl:hover,tr.pl:focus{background:#F1EEE4;outline:none}
.go{margin-left:10px;font-size:13px;font-weight:600;color:#2A78D6;opacity:0;transition:opacity .12s}
.bowl .go{color:#D4572A}
tr.pl:hover .go,tr.pl:focus .go{opacity:1}
.nextl{font-size:14px;color:#6B7280;margin-top:10px}
/* drawer */
#scrim{position:absolute;inset:0;background:rgba(20,33,61,.32);z-index:5}
#drawer{position:absolute;top:0;right:0;bottom:0;width:660px;background:#FCFBF8;border-left:1.5px solid #E2E0D8;box-shadow:-12px 0 40px rgba(20,33,61,.18);z-index:6;padding:28px 34px;overflow:auto;animation:dr .25s ease-out}
@keyframes dr{from{transform:translateX(40px);opacity:0}}
#drawer .x{position:absolute;top:18px;right:20px;width:40px;height:40px;border-radius:20px;border:1.5px solid #E2E0D8;background:#fff;font-size:22px;line-height:1;cursor:pointer;color:#14213D}
.dhead{display:flex;gap:16px;align-items:center;padding-right:50px}
.drk{font-family:'Space Grotesk',Arial,sans-serif;font-size:48px;font-weight:600;line-height:1;color:#2A78D6}
.dbowl .drk{color:#D4572A}
.dnm{font-family:'Space Grotesk',Arial,sans-serif;font-size:30px;font-weight:600;color:#14213D;line-height:1.1}
.drole{font-size:15px;color:#6B7280;margin-top:4px}
.dnums{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:20px 0 14px}
.dnum{background:#F5F4EF;border-radius:10px;padding:12px 16px}
.dnum .big{font-family:'Space Grotesk',Arial,sans-serif;font-size:34px;font-weight:600;color:#14213D;line-height:1.1}
.dnum .lbl{font-size:13px;color:#6B7280;margin-top:2px}
.dstats{font-size:15px;line-height:1.5;color:#3B4252;padding:12px 0 14px;border-bottom:1.5px solid #E2E0D8}
.dstats b{color:#14213D}
.dnotes p{font-size:16px;line-height:1.55;color:#3B4252;margin-top:12px}
.dnotes p.str{background:#FFF6CC;border:1.5px solid #EBC94A;border-radius:8px;padding:10px 14px;color:#14213D;font-weight:600}
.dnotes p.cav{font-style:italic;color:#5F6675}
/* how it works */
.flow{display:flex;flex-direction:column;gap:18px;margin-top:6px}
.frow{display:flex;align-items:stretch}
.step{flex:1;background:#FCFBF8;border:1.5px solid #E2E0D8;border-radius:14px;padding:22px 22px;display:flex;flex-direction:column;gap:12px;min-height:205px}
.step.y{background:#FFF6CC;border-color:#EBC94A}
.stop{display:flex;align-items:center;gap:12px}
.step .sn{width:38px;height:38px;border-radius:19px;line-height:1;background:#14213D;color:#F5F4EF;font-family:'Space Grotesk',Arial,sans-serif;font-weight:600;font-size:18px;display:flex;align-items:center;justify-content:center;flex:none}
.step h3{font-family:'Space Grotesk',Arial,sans-serif;font-size:23px;font-weight:600;color:#14213D}
.step p{font-size:18px;line-height:1.45;color:#3B4252}
.step b{color:#14213D}
.hl{display:inline-block;margin-top:8px;background:#FFE47A;color:#14213D;font-weight:700;padding:2px 8px;border-radius:5px}
.arr{flex:none;width:44px;display:flex;align-items:center;justify-content:center;font-size:26px;color:#6B7280}
.turn{display:flex;justify-content:flex-end;padding-right:12%;color:#6B7280;font-size:14px;font-weight:600;letter-spacing:.5px}
.bar-y{background:#FFE47A;color:#14213D;border-radius:8px;padding:12px 18px;font-size:18px;align-self:flex-start;margin-top:6px}
/* what if */
.wiwrap{display:flex;gap:26px;min-height:0;flex:1}
.wileft{width:440px;flex:none;display:flex;flex-direction:column;gap:8px}
.lbl2{font-size:13px;font-weight:600;letter-spacing:1.5px;color:#6B7280;text-transform:uppercase;margin-top:4px}
.wigrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.wi{text-align:left;background:#FCFBF8;border:1.5px solid #E2E0D8;border-radius:10px;padding:7px 11px;cursor:pointer;transition:background-color .12s,border-color .12s}
.wi:hover{border-color:#9AA3B5}
.wi .t{display:block;font-size:14px;font-weight:600;color:#14213D}
.wi .d{display:block;font-size:12px;color:#6B7280;margin-top:1px}
.wi[aria-pressed=true]{background:#14213D;border-color:#14213D}
.wi[aria-pressed=true] .t{color:#F5F4EF}.wi[aria-pressed=true] .d{color:#BFC8D8}
.grp p{font-size:13px;font-weight:600;color:#3B4252;margin-bottom:4px}
.seg{display:flex;flex-wrap:wrap;gap:6px}
.seg button{font-size:12.5px;font-weight:600;color:#3B4252;background:#FCFBF8;border:1.5px solid #E2E0D8;border-radius:999px;padding:5px 9px;cursor:pointer}
.seg button[aria-pressed=true]{background:#14213D;border-color:#14213D;color:#F5F4EF}
.mine{font-size:10px;font-weight:700;letter-spacing:.8px;margin-left:5px;color:#B8860B}
.seg button[aria-pressed=true] .mine{color:#FFE47A}
#reset{align-self:flex-start;margin-top:4px;font-size:14px;font-weight:600;color:#14213D;background:#FFE47A;border:none;border-radius:8px;padding:8px 14px;cursor:pointer}
.wiright{flex:1;display:flex;flex-direction:column;gap:14px;min-width:0}
.ans{font-size:16px;line-height:1.45;color:#14213D;background:#FFF6CC;border:1.5px solid #EBC94A;border-radius:10px;padding:10px 16px;min-height:70px}
.wiright td{height:34px;font-size:15px;white-space:nowrap}
.wiright td.sh{width:150px}
.wiright .sbar{width:80px;margin-right:8px}
.wiright .card{padding:16px 18px}
.kept{font-family:'Space Grotesk',Arial,sans-serif;font-size:20px;font-weight:600;color:#14213D}
.kept small{font-family:Inter,Arial,sans-serif;font-size:13px;font-weight:500;color:#6B7280;margin-left:4px}
.chip{display:inline-block;margin-left:8px;font-size:10px;font-weight:700;letter-spacing:.8px;background:#FFE47A;color:#14213D;border-radius:4px;padding:2px 6px;vertical-align:2px}
.drop{font-size:14px;color:#6B7280;margin-top:8px}
.drop b{color:#B45309}
/* how sure */
.srow{display:grid;grid-template-columns:230px 1fr 64px 92px;align-items:center;gap:12px;height:36px;border-bottom:1px solid #EEECE5}
.srow:last-child{border-bottom:none}
.srow .n{font-size:16px;font-weight:600;color:#14213D}
.srow .v{font-size:16px;font-weight:600;font-variant-numeric:tabular-nums;color:#14213D;text-align:right}
.srow .c{font-size:14px;color:#6B7280;text-align:right;font-variant-numeric:tabular-nums}
.srow .sbar{width:100%;margin:0}
.shead{display:grid;grid-template-columns:230px 1fr 64px 92px;gap:12px;font-size:12px;font-weight:600;letter-spacing:1px;color:#6B7280;text-transform:uppercase;padding-bottom:6px;border-bottom:1.5px solid #E2E0D8}
.shead span:nth-child(3),.shead span:nth-child(4){text-align:right}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.tile{background:#14213D;border-radius:12px;padding:12px 18px;color:#D5DCE8;font-size:14px;line-height:1.4}
.tile b{display:block;font-family:'Space Grotesk',Arial,sans-serif;font-size:24px;color:#FFE47A;line-height:1.15;margin-bottom:2px}
</style>
</head>
<body>
<div id="stage" role="application" aria-label="Selector's War Room">
<header>
  <div class="brand"><p class="t">Selector’s War Room</p><p class="s">SupeRR Selector Season 2 · Most reliable under pressure · Rajdeep Chatale</p></div>
  <nav role="tablist">
    <button role="tab" id="tab-answer" aria-selected="true"><span class="n">1</span>The answer</button>
    <button role="tab" id="tab-how" aria-selected="false"><span class="n">2</span>How it works</button>
    <button role="tab" id="tab-whatif" aria-selected="false"><span class="n">3</span>What if?</button>
    <button role="tab" id="tab-sure" aria-selected="false"><span class="n">4</span>How sure</button>
  </nav>
</header>
<main>
  <section class="screen on" id="sc-answer" role="tabpanel">
    <div class="hrow"><div><p class="eb">The short version</p><h1 class="st">My top 10s, ranked on what repeats under pressure</h1></div><p class="hint">Click any player to read his notes</p></div>
    <div class="two">
      <div class="card list bat"><div class="lh"><h2>Batters</h2></div>
        <table><thead><tr><th>#</th><th>Player</th><th class="r">Rating</th><th>Top 10 in resamples</th></tr></thead><tbody>__BATROWS__</tbody></table>
        <p class="nextl">__BATNEXT__</p></div>
      <div class="card list bowl"><div class="lh"><h2>Bowlers</h2></div>
        <table><thead><tr><th>#</th><th>Player</th><th class="r">Rating</th><th>Top 10 in resamples</th></tr></thead><tbody>__BOWLROWS__</tbody></table>
        <p class="nextl">__BOWLNEXT__</p></div>
    </div>
    <p class="fine"><b>Rating:</b> runs above an average player in the same situation and against the same opposition, per 100 balls faced (batters) or per 24 balls bowled (bowlers), with pressure balls counting most. <b>Top 10 in resamples:</b> how often he stays top 10 when I redraw the matches 2,000 times; yellow = 75% or more. Each list is the ten who stay top 10 most often, ordered by rating.</p>
  </section>

  <section class="screen" id="sc-how" role="tabpanel">
    <div><p class="eb">The method on one page</p><h1 class="st">How the model turns ball-by-ball data into two top 10s</h1></div>
    <div class="flow">
      <div class="frow">__ROW1__</div>
      <p class="turn">↓ then</p>
      <div class="frow">__ROW2__</div>
    </div>
    <p class="bar-y"><b>Then I tried to break it:</b> ten changes to the settings, six more pressure ideas, and a test of 2022–24 ratings against 2025–26.</p>
    <p class="fine">A pressure ball is one in the top 20% of the Pressure Index (80 or more), about 48 a match. 77% of them come in the chase, and 45% in the middle overs, not only at the death. Full detail, formulas and checks are in my methodology report.</p>
  </section>

  <section class="screen" id="sc-whatif" role="tabpanel">
    <div><p class="eb">Test my ranking</p><h1 class="st">Change one setting and watch who stays</h1></div>
    <div class="wiwrap">
      <div class="wileft">
        <p class="lbl2">Pick a what if</p>
        <div class="wigrid" id="whatifs"></div>
        <p class="lbl2">Or mix your own</p>
        <div class="grp"><p>Weight on pressure balls</p><div class="seg" data-key="w"></div></div>
        <div class="grp"><p>Recent seasons</p><div class="seg" data-key="r"></div></div>
        <div class="grp"><p>A wicket is worth (runs)</p><div class="seg" data-key="k"></div></div>
        <div class="grp"><p>Adjust for opponent and ground</p><div class="seg" data-key="a"></div></div>
        <button id="reset" type="button">Back to my settings</button>
      </div>
      <div class="wiright">
        <p class="ans" id="answer"></p>
        <div class="two">
          <div class="card list bat"><div class="lh"><h2>Batters</h2><p class="kept" id="sum-bat"></p></div>
            <table><thead><tr><th>#</th><th>Player</th><th class="r">Rating</th><th>Top 10 in reshuffles</th></tr></thead><tbody id="t-bat"></tbody></table>
            <p class="drop" id="d-bat"></p></div>
          <div class="card list bowl"><div class="lh"><h2>Bowlers</h2><p class="kept" id="sum-bowl"></p></div>
            <table><thead><tr><th>#</th><th>Player</th><th class="r">Rating</th><th>Top 10 in reshuffles</th></tr></thead><tbody id="t-bowl"></tbody></table>
            <p class="drop" id="d-bowl"></p></div>
        </div>
        <p class="fine">My settings use 2,000 reshuffles, as in the report. Every other setting is a quick run of 200, so the last places can differ by a player or two from the 2,000-reshuffle tests in my report. <span class="chip">NEW</span> = not in my top 10.</p>
      </div>
    </div>
  </section>

  <section class="screen" id="sc-sure" role="tabpanel">
    <div><p class="eb">Reliability</p><h1 class="st">How sure am I about each pick?</h1></div>
    <p class="lead">The bar is how often a player stays in the top 10 when I redraw the matches 2,000 times. The last column counts how many of the 90 what-if settings on this page keep him in the top 10.</p>
    <div class="two">
      <div class="card list bat"><div class="lh"><h2>Batters</h2></div><div class="shead"><span>Player</span><span>Top 10 in 2,000 resamples</span><span></span><span>What-ifs</span></div><div id="s-bat"></div></div>
      <div class="card list bowl"><div class="lh"><h2>Bowlers</h2></div><div class="shead"><span>Player</span><span>Top 10 in 2,000 resamples</span><span></span><span>What-ifs</span></div><div id="s-bowl"></div></div>
    </div>
    <div class="tiles">
      <div class="tile"><b>8 of 10</b>changes to my method keep at least 8 of my 10 batters and 9 of my 10 bowlers.</div>
      <div class="tile"><b>+0.29 bowlers · +0.05 batters</b>how well 2022–24 ratings predict 2025–26. Bowling carries over; batting much less.</div>
      <div class="tile"><b>35% to 49%</b>the close calls at the bottom of both lists. The top picks almost never move.</div>
    </div>
  </section>

  <div id="scrim" hidden></div>
  <aside id="drawer" hidden tabindex="-1" aria-label="Player notes">
    <button class="x" type="button" aria-label="Close">×</button>
    <div class="dhead"><p class="drk" id="dr-rk"></p><div><h2 class="dnm" id="dr-nm"></h2><p class="drole" id="dr-role"></p></div></div>
    <div class="dnums"><div class="dnum"><p class="big" id="dr-rt"></p><p class="lbl" id="dr-rtl"></p></div><div class="dnum"><p class="big" id="dr-p"></p><p class="lbl">Top 10 in 2,000 resamples</p></div></div>
    <p class="dstats" id="dr-stats"></p>
    <div class="dnotes" id="dr-notes"></div>
  </aside>
</main>
<footer><span>Companion to my methodology report. Built from the SupeRR Selector Season 2 data pack: player ratings only, never ball-by-ball data.</span><span>Use ← → to switch tabs</span></footer>
</div>
<script>
const DATA = __DATA__;
const {D, P, ANS, MINE_STR} = DATA;
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
  w: [['eq', 'Every ball equal'], ['sqrt', 'A little'], ['idx', 'By the Index', 1], ['idx2', 'A lot'], ['ponly', 'Tensest only']],
  r: [['none', 'Count equally', 1], ['hl2', '2-year half-life'], ['hl1', '1-year half-life']],
  k: [['5', '5'], ['8', '8', 1], ['11', '11']],
  a: [['on', 'On', 1], ['off', 'Off']]
};
let state = {...MINE};
const key = s => [s.w, s.r, s.k, s.a].join('|');
const esc = s => String(s).replace(/[&<>]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]));
const nm = i => esc(D.names[i]);
const list = a => a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];

/* fit the 16:9 stage to the window */
const stage = document.getElementById('stage');
function fit() {
  const s = Math.min(innerWidth / 1600, innerHeight / 900);
  stage.style.transform = `scale(${s})`;
  stage.style.left = ((innerWidth - 1600 * s) / 2) + 'px';
  stage.style.top = ((innerHeight - 900 * s) / 2) + 'px';
}
addEventListener('resize', fit); fit();

/* tabs */
const TABS = ['answer', 'how', 'whatif', 'sure'];
let cur = 'answer';
function show(t) {
  TABS.forEach(x => {
    document.getElementById('sc-' + x).classList.toggle('on', x === t);
    document.getElementById('tab-' + x).setAttribute('aria-selected', x === t ? 'true' : 'false');
  });
  cur = t; closeDrawer();
  try { history.replaceState(null, '', '#' + t); } catch (e) {}
}
TABS.forEach(t => document.getElementById('tab-' + t).addEventListener('click', () => show(t)));
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeDrawer(); return; }
  if (!document.getElementById('drawer').hidden) return;
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    const i = TABS.indexOf(cur);
    show(TABS[(i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length]);
  }
});

/* player notes drawer */
const drawer = document.getElementById('drawer'), scrim = document.getElementById('scrim');
function openPlayer(name) {
  const role = ANS.bat.some(r => r[0] === name) ? 'bat' : 'bowl';
  const i = ANS[role].findIndex(r => r[0] === name), row = ANS[role][i], p = P[name];
  drawer.classList.toggle('dbowl', role === 'bowl');
  document.getElementById('dr-rk').textContent = i + 1;
  document.getElementById('dr-nm').textContent = name;
  document.getElementById('dr-role').textContent = p.role;
  document.getElementById('dr-rt').textContent = row[1];
  document.getElementById('dr-rtl').textContent = role === 'bat' ? 'Pressure Rating: runs above average per 100 balls' : 'Pressure Rating: runs saved per 24 balls';
  document.getElementById('dr-p').textContent = row[2] + '%';
  document.getElementById('dr-stats').innerHTML = p.stats;
  document.getElementById('dr-notes').innerHTML = p.notes.map(([c, t]) => `<p class="${c}">${t}</p>`).join('');
  drawer.hidden = false; scrim.hidden = false; drawer.scrollTop = 0; drawer.focus();
}
function closeDrawer() { drawer.hidden = true; scrim.hidden = true; }
drawer.querySelector('.x').addEventListener('click', closeDrawer);
scrim.addEventListener('click', closeDrawer);
document.querySelectorAll('tr.pl').forEach(tr => {
  tr.addEventListener('click', () => openPlayer(tr.dataset.p));
  tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPlayer(tr.dataset.p); } });
});

/* what if */
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
  document.getElementById('reset').addEventListener('click', () => { state = {...MINE}; render(); });
}
function render() {
  const c = D.combos[key(state)];
  const isMine = key(state) === key(MINE);
  const active = WHATIFS.find(([, , , ch]) => key({...MINE, ...ch}) === key(state));
  document.querySelectorAll('.wi').forEach(b => b.setAttribute('aria-pressed', active && b.id === 'wi-' + active[0] ? 'true' : 'false'));
  document.querySelectorAll('.seg button').forEach(b => { const [, k, v] = b.id.split('-'); b.setAttribute('aria-pressed', state[k] === v ? 'true' : 'false'); });
  const parts = [];
  for (const role of ['bat', 'bowl']) {
    const mine = new Set(D.final[role]);
    const rows = c[role].slice(0, 10).sort((a, b) => b[1] - a[1]);   // the ten most often top 10, ordered by rating
    const top = new Set(rows.map(r => r[0]));
    const kept = D.final[role].filter(i => top.has(i)), out = D.final[role].filter(i => !top.has(i));
    const inn = rows.filter(r => !mine.has(r[0])).map(r => r[0]);
    document.getElementById('sum-' + role).innerHTML = `${kept.length}/10<small>of mine stay</small>`;
    document.getElementById('t-' + role).innerHTML = rows.map((r, i) => {
      const [id, rt, p] = r, pc = Math.round(p * 100);
      const shown = isMine ? MINE_STR[role][id] : (role === 'bat' ? rt.toFixed(1) : rt.toFixed(2));
      return `<tr><td class="rk">${i + 1}</td><td class="nm">${nm(id)}${mine.has(id) ? '' : '<span class="chip">NEW</span>'}</td>` +
        `<td class="num">${shown}</td><td class="sh"><div class="sbar"><span style="width:${pc}%"></span></div><span class="pct">${pc}%</span></td></tr>`;
    }).join('');
    document.getElementById('d-' + role).innerHTML = out.length ? `<b>Dropped from my ten:</b> ${list(out.map(nm))}` : 'All ten of my picks are still here.';
    const who = role === 'bat' ? 'batters' : 'bowlers';
    parts.push(out.length === 0 ? `all 10 of my ${who} stay` :
      `${kept.length} of my 10 ${who} stay (${list(out.map(nm))} ${out.length === 1 ? 'drops' : 'drop'} out; ${list(inn.map(nm))} ${inn.length === 1 ? 'comes' : 'come'} in)`);
  }
  const title = active ? active[1] : 'Your mix';
  document.getElementById('answer').innerHTML = isMine
    ? '<b>My settings:</b> these are exactly the two top 10s in my report. Click a what if to see what changes.'
    : `<b>${title}:</b> ${parts[0]}, and ${parts[1]}.`;
}

/* how sure */
function survivors() {
  for (const role of ['bat', 'bowl']) {
    const surv = Object.fromEntries(D.surv[role].map(([id, s]) => [D.names[id], s]));
    document.getElementById('s-' + role).innerHTML = ANS[role].map(([n, , p]) =>
      `<div class="srow"><p class="n">${esc(n)}</p><div class="sbar"><span style="width:${p}%"></span></div><p class="v">${p}%</p><p class="c">${Math.round(surv[n] * D.n)} of ${D.n}</p></div>`).join('');
  }
}

buildButtons(); render(); survivors();
const start = location.hash.slice(1); if (TABS.includes(start)) show(start);
</script>
</body>
</html>
"""

page = (PAGE.replace("__BATROWS__", bat_rows).replace("__BOWLROWS__", bowl_rows)
        .replace("__BATNEXT__", bat_next).replace("__BOWLNEXT__", bowl_next)
        .replace("__ROW1__", row1).replace("__ROW2__", row2)
        .replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print("wrote", OUT, len(page) // 1024, "KB")
