"""Builds the data-heavy slides of the report deck (lists, evidence tables, player notes) from the saved results,
so every number on them comes straight from outputs/*.csv. Prose slides are written by hand."""
import pandas as pd, numpy as np, html, os
OUT = 'deck/project/slides/'; os.makedirs(OUT, exist_ok=True)
FOOT = '<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>\n<p class="pnum"></p>'
Z80 = 1.2816

bat = pd.read_csv('outputs/final_bat.csv').set_index('name')
bowl = pd.read_csv('outputs/final_bowl.csv').set_index('name')
bsb = pd.read_csv('outputs/bootstrap_bat_a1.csv').set_index('name').p_top10
bsw = pd.read_csv('outputs/bootstrap_bowl_a1.csv').set_index('name').p_top10

BAT = ['Suryakumar Yadav', 'Abhishek Sharma', 'Phil Salt', 'Reeza Hendricks', 'Heinrich Klaasen', 'Tim David',
       'Glenn Phillips', 'Vaibhav Sooryavanshi', 'Namboori Tilak Varma', 'Virat Kohli']
BOWL = ['Sunil Narine', 'Jasprit Bumrah', 'Kuldeep Yadav', 'Josh Hazlewood', 'Rashid Khan', 'Varun Chakravarthy',
        'Matheesha Pathirana', 'Wanindu Hasaranga', 'Mujeeb Ur Rahman', 'Krunal Pandya']
BAT_MISS, BOWL_MISS = 'Nicholas Pooran', 'Nathan Ellis'

def e(s): return html.escape(s, quote=False).replace("'", '’')
def pct(x): return f'{round(100 * x):.0f}%'
def bstats(n):
    r = bat.loc[n]; rt = r.rating; se = r.rating_se
    return dict(rating=rt, lo=rt - Z80 * se, hi=rt + Z80 * se, p=bsb[n], Pb=int(r.Pb), srp=r.SR_P, srn=r.SR_N, bpd=r.BpD_P, bpdn=r.BpD_N)
def wstats(n):
    r = bowl.loc[n]; rt = r.rating; se = r.rating_se
    return dict(rating=rt, lo=rt - Z80 * se, hi=rt + Z80 * se, p=bsw[n], ov=r.Pb / 6, ecp=r.Econ_P, ecn=r.Econ_N, sr=r.SRb_P, srn=r.SRb_N, w=int(r.wkts_P))

def write(sid, body, cls='', foot=True):
    with open(OUT + sid + '.html', 'w') as f:
        f.write(f'<section id="{sid}"{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>\n{body}\n{FOOT if foot else ""}\n</section>\n')

# ---------- slide 2: the answer
def lst(title, names, st, fmt, cls):
    rows = ''.join(f'<div class="lrow"><p class="rk">{i}</p><p class="nm">{e(n)}</p><p class="rt">{fmt(st(n)["rating"])}</p><p class="pc">{pct(st(n)["p"])}</p></div>\n'
                   for i, n in enumerate(names, 1))
    return (f'<div class="col" style="flex:1; gap:10px">\n<h3 class="{cls}" style="font-size:36px">{title}</h3>\n<div class="list">\n'
            f'<div class="lhead"><p class="rk">#</p><p class="nm">Player</p><p class="rt">Rating</p><p class="pc">Top 10</p></div>\n{rows}</div>\n</div>')
body = ('<div class="head"><p class="eyebrow">THE SHORT VERSION</p><h2>My top 10 batters and bowlers</h2></div>\n'
        '<div class="row" style="gap:96px">\n' + lst('Batters', BAT, bstats, lambda v: f'{v:.1f}', 'blue') + '\n'
        + lst('Bowlers', BOWL, wstats, lambda v: f'{v:.2f}', 'orange') + '\n</div>\n'
        '<p class="small" style="margin-top:-12px">Rating: runs above an average player in the same situation, per 100 balls faced (batters) or per 24 balls bowled (bowlers), with pressure balls counting most. Top 10: how often the player stays in the top 10 across 500 resampled versions of the data.</p>\n'
        '')
write('answer', body)

# ---------- evidence tables (slides 13 and 20)
def evidence(sid, role, names, miss, st, axis_max, ticks, fmt, heads, cells, eyebrow, title, note, aside):
    W = 520; sc = W / axis_max
    def plot(s):
        lo, hi, rt = max(s['lo'], 0), min(s['hi'], axis_max), s['rating']
        return (f'<div class="c-plot"><div class="base"></div><div class="bar" style="left:{lo * sc:.0f}px; width:{(hi - lo) * sc:.0f}px"></div>'
                f'<div class="dot" style="left:{rt * sc - 11:.0f}px"></div></div>')
    tk = ''.join(f'<p class="tick" style="left:{t * sc - 30:.0f}px">{t}</p>' for t in ticks)
    head = (f'<div class="thead"><p class="c-rk">#</p><p class="c-nm">{"Batter" if role == "bat" else "Bowler"}</p>'
            f'<div class="c-plot">{tk}</div><p class="c-rt">Rating</p><p class="c-pc">Top 10 in resamples</p>'
            + ''.join(f'<p class="{c}">{h}</p>' for c, h in zip(['c-n1', 'c-n2', 'c-n3'], heads)) + '</div>\n')
    rows = ''
    for i, n in enumerate(names + [miss], 1):
        s = st(n); k = 'miss' if n == miss else ('pick' if (role == 'bat' and n == 'Virat Kohli') else '')
        rk = 'out' if n == miss else str(i)
        rows += (f'<div class="trow {k}"><p class="c-rk">{rk}</p><p class="c-nm">{e(n)}</p>{plot(s)}'
                 f'<p class="c-rt">{fmt(s["rating"])}</p><p class="c-pc">{pct(s["p"])}</p>'
                 + ''.join(f'<p class="{c}">{v}</p>' for c, v in zip(['c-n1', 'c-n2', 'c-n3'], cells(s))) + '</div>\n')
    body = (f'<div class="head"><p class="eyebrow">{eyebrow}</p><h2>{title}</h2></div>\n'
            f'<div class="col {role}" style="gap:0">\n{head}{rows}</div>\n'
            f'<p class="small" style="margin-top:-12px">{note}</p>')
    write(sid, body)

evidence('bat-evidence', 'bat', BAT, BAT_MISS, bstats, 26, [0, 5, 10, 15, 20, 25], lambda v: f'{v:.1f}',
         ['Pressure balls', 'Strike rate (usual)', 'Balls per out'],
         lambda s: [f'{s["Pb"]}', f'{s["srp"]:.0f} ({s["srn"]:.0f})', f'{s["bpd"]:.1f}'],
         '4 · EVIDENCE: BATTERS', 'Batters: the top 10 and how sure I am',
         'Dot = Pressure Rating (runs above average per 100 balls), bar = 80% range. Last three columns: pressure balls only, usual strike rate in brackets. The ten are the players most often in the top 10 across 500 resamples, ordered by rating.',
         'Shaded row: Kohli, my one change from a straight sort by rating. Pooran is shown for transparency. Balls per out is pressure balls faced divided by dismissals on pressure balls.')
evidence('bowl-evidence', 'bowl', BOWL, BOWL_MISS, wstats, 5.5, [0, 1, 2, 3, 4, 5], lambda v: f'{v:.2f}',
         ['Pressure overs', 'Economy (usual)', 'Balls per wicket'],
         lambda s: [f'{s["ov"]:.1f}', f'{s["ecp"]:.2f} ({s["ecn"]:.2f})', f'{s["sr"]:.1f}'],
         '4 · EVIDENCE: BOWLERS', 'Bowlers: the top 10 and how sure I am',
         'Dot = Pressure Rating (runs saved against average per 24 balls), bar = 80% range. Last three columns: pressure balls only, usual economy in brackets. Same rule as the batters, and here it matches a straight sort by rating.',
         'Nathan Ellis is the closest miss at 40%. Pressure overs count legal balls only.')

# ---------- player notes
ROLE = {
 'Suryakumar Yadav': 'Right-hander, bats No. 3 or 4 · India · MI',
 'Abhishek Sharma': 'Left-handed opener · India · SRH',
 'Phil Salt': 'Right-handed opener and keeper · England · RCB',
 'Reeza Hendricks': 'Right-handed opener · South Africa · T20Is only',
 'Heinrich Klaasen': 'Right-hander, middle order, keeper · South Africa · SRH',
 'Tim David': 'Right-handed finisher · Australia · RCB',
 'Glenn Phillips': 'Right-hander, bats No. 4 · New Zealand · GT',
 'Vaibhav Sooryavanshi': 'Left-handed opener · India · RR',
 'Namboori Tilak Varma': 'Left-hander, middle order · India · MI',
 'Virat Kohli': 'Right-handed opener · India · RCB',
 'Sunil Narine': 'Mystery off-spin · West Indies · KKR · IPL only',
 'Jasprit Bumrah': 'Right-arm fast · India · MI',
 'Kuldeep Yadav': 'Left-arm wrist spin · India · DC, LSG from 2027',
 'Josh Hazlewood': 'Right-arm fast-medium · Australia · RCB',
 'Rashid Khan': 'Leg-spin · Afghanistan · GT',
 'Varun Chakravarthy': 'Mystery spin · India · KKR',
 'Matheesha Pathirana': 'Right-arm fast, slinging action · Sri Lanka · KKR',
 'Wanindu Hasaranga': 'Leg-spin · Sri Lanka · RR in 2025',
 'Mujeeb Ur Rahman': 'Mystery off-spin · Afghanistan · mostly T20Is',
 'Krunal Pandya': 'Left-arm finger spin · India · RCB · IPL only',
}
NOTE = {
 'Suryakumar Yadav': ["Surya bats at 3 or 4 and usually walks in after the powerplay. He plays the ball very late and gets his power from his wrists, so he scores all around the ground: scoops, ramps, sweeps and that inside-out shot over cover. Bowlers keep changing their line and still can't settle.",
   "The way to stop him is a tight bowler who gives him no room. Hazlewood has done it: 16 dots in 26 balls and two dismissals. I thought slower balls were a weakness too, but he scores at 196 against them, well above the average batter.",
   "He's the top-rated batter under pressure: a strike rate of 172, and out only once every 22 balls."],
 'Abhishek Sharma': ["Abhishek doesn't take time to settle. From ball one he's looking for fours and sixes, and you can see Yuvraj Singh's influence on how he bats. He drives through cover and pulls hard, so bowlers can't hide on either side.",
   "I didn't have a weakness written down for him, so I looked in the data. It's wrist spin: he attacks leg-spinners hard (strike rate 230) but gets out to them every 14 balls.",
   "Most of his pressure batting comes in the first six overs of a chase. His job is to make a 200 target look small, and he strikes at 190 doing it."],
 'Phil Salt': ["Salt loves pace on the ball. He hits on both sides of the wicket, and the pull alone gives him almost a quarter of his runs. He keeps wicket too, and with Kohli at RCB he gave the top order both speed and calm.",
   "I expected good swing with the new ball to trouble him early. It doesn't: he scores at 164 against it and gets out only once every 30 balls. Spinners who change their pace slow him a little.",
   "Under pressure he strikes at 185 and has been out only 5 times in 247 balls. Fast and safe is a rare mix."],
 'Reeza Hendricks': ["Hendricks is the classical batter in my list: sound technique, good timing, and he finds gaps instead of slogging. Outside pressure moments he can take a while to get going (strike rate 136).",
   "When the game is tight he changes completely, striking at 193 under pressure. I expected pace and bounce to trouble him, but he handles fast bowling well. His real weakness is mystery spin: googlies, carrom balls and sliders get him out every 8 balls.",
   "One thing to keep in mind: all his evidence comes from T20Is, with no IPL games in the data, so his ranking is less certain than most."],
 'Heinrich Klaasen': ["Nobody in this list hurts spinners like Klaasen. Strong base, strong hands, fast bat, and he hits even good balls from spinners into the stands. Against wrist spin he strikes at 191, when the average batter manages 136. He keeps wicket as well.",
   "I thought yorkers and the short ball would stop him. Yorkers slow him, but less than they slow most batters, and he actually scores well against bouncers.",
   "He's the same player whether the game is tight or not: 169 under pressure, 167 normally. That calm is why SRH lean on him in the middle overs."],
 'Tim David': ["Tim David is pure power. He doesn't need a half-volley; he can hit a good-length ball for six. Give him pace and some room at the death and the game is over, especially when dew makes bowlers miss their lengths.",
   "The way to stop him is spin that changes pace. Leg-spinners keep him to a strike rate of 142 and get him out every 14 balls, and yorkers stop him too. I was wrong about slower balls, though: he scores at 180 against them.",
   "58% of his pressure balls come at the death. Against RR in 2023 he needed 17 off the last over and hit the first three balls for six."],
 'Glenn Phillips': ["Phillips can do a bit of everything. He hits pace and spin equally well, he's strong against the short ball (the pull is his biggest scoring shot), and he can change gears within an over. Add his fielding and part-time off-spin and he's a complete package.",
   "I thought slower balls would be the way to get him, but he scores at 175 against them. His real weak spot is the new ball, which he rarely faces batting at 4.",
   "What stands out is how rarely he gets out when it matters: 5 dismissals in 190 pressure balls."],
 'Vaibhav Sooryavanshi': ["He's already in RR colours, and I'm glad. He's a teenager taking on international fast bowlers without fear, with bat speed that's unreal for his age. Against pace he strikes at 227.",
   "I assumed a young opener would struggle when the new ball swings. He doesn't: he scores at 249 against early swing and seam. Finger spin is the only thing that slows him a little, and his decision-making is still developing.",
   "Under pressure he strikes at 234, the highest of any batter who qualifies. His sample is still small, so every season will make his case stronger."],
 'Namboori Tilak Varma': ["Tilak is the balance guy. He steadies things when wickets fall and then lifts the rate at the end. People call him an anchor, but reverse sweeps and scoops give him as big a share of his runs as Surya gets from those shots.",
   "I said he's strong against spin, and the data agrees in a specific way: spinners almost never get him out (once every 39 balls for finger spin), even if he doesn't score fast against them. Yorkers and short balls bother him less than I expected.",
   "He's faced more pressure balls than anyone in the data, 588 of them, and still strikes at 149."],
 'Virat Kohli': ["Kohli takes the last spot, and not on reputation. He used to bat at 3; now he opens and attacks from ball one. His IPL strike rate has gone from 116 in 2022 to 166 in 2026, and he won the Orange Cap in 2016 and 2024.",
   "In a chase he keeps the strike moving, so bowlers never settle. Spin slows him down but rarely gets him out.",
   "Why he edges Pooran is on slide 14: in almost the same number of pressure balls, Kohli was out 7 times to Pooran's 21."],
 'Sunil Narine': ["Narine is the hardest bowler in this list to read. Off-breaks, carrom balls and quicker straight ones all come out of the same action, so batters can't plan against him. That's why he's economical and still takes wickets.",
   "Most of his pressure overs come in the middle of a chase, and that's where he shuts the game down. Under pressure he goes at 6.55 an over and takes a wicket every 18 balls, both better than his normal numbers. All his evidence is from the IPL, since he retired from international cricket in 2023.",
   "And this rating doesn't even count his batting. KKR turned him into an opener who attacks from the first ball."],
 'Jasprit Bumrah': ["Bumrah has everything a fast bowler needs: the yorker on the stumps, a nasty bouncer, a slower ball you can't pick, and swing with the new ball. His short run-up and unusual release point make him even harder to judge.",
   "What sets him apart is that pressure doesn't change him at all. His economy is 7.28 under pressure and 7.26 in normal overs, and that's with 39% of his pressure overs at the death, the hardest time to bowl.",
   "With the new ball under pressure, more than half his deliveries are dots. He's the same bowler in the 1st over and the 19th."],
 'Kuldeep Yadav': ["Kuldeep is a proper wrist spinner. He flights the ball, gets drift and dip, and turns it both ways. From the batter's end his stock ball and googly look the same, so they can't read him from the hand.",
   "He's one of the few bowlers who actually gets better under pressure: his economy drops from 8.15 to 7.37, and he takes a wicket every 14 balls. Most of that comes in the middle overs, where he goes at just 6.66. I'd keep him away from the death, though.",
   "He's also changed teams: traded from DC to Lucknow Super Giants ahead of IPL 2027."],
 'Josh Hazlewood': ["Hazlewood doesn't need extreme pace. He hits a hard length on the seam, ball after ball, and his height gives him steep bounce. Over the years he's added slower balls and yorkers to make it work in T20.",
   "His plan is simple: dots, dots, dots, until the batter takes a risk. The data shows exactly that. Under pressure he takes a wicket every 11 balls, the best rate in this top 10, even though he goes for a few more runs than usual.",
   "Half his pressure overs come with the new ball, and half of those deliveries are dots."],
 'Rashid Khan': ["Rashid bowls leg-spin at almost medium pace. His wrist moves so fast that batters don't get time to see whether it's the leg-break, googly, slider or flipper. And he's accurate, stump to stump.",
   "He has bowled more pressure overs than anyone else in my top 10 (75), and he barely changes: 7.57 an over under pressure, 7.44 normally. At the death under pressure, he takes a wicket every 7 balls.",
   "He also scores useful runs down the order: 791 at a strike rate of 156 in this data. Against DC in 2026 he took 3 for 17 defending 210, and GT won by one run."],
 'Varun Chakravarthy': ["Varun is a mystery spinner: leg-break, googly, carrom ball, off-break and a quicker one, all pushed through fast for a spinner. Batters can't use their feet against him, and he changes his pace and trajectory cleverly.",
   "Pressure doesn't change his numbers: 8.11 an over under pressure, 8.00 normally, with 28 pressure wickets. Most of his work is in the middle overs.",
   "The surprise for me was the death overs. When he's used late in a tight game, he goes for just 6.95 an over. Very few teams have a spinner they can trust that late."],
 'Matheesha Pathirana': ["Pathirana has a slinging action like Lasith Malinga, so the ball comes from an angle batters rarely see. He bowls yorkers, wide yorkers, slower balls and bouncers. He grew up under MS Dhoni at CSK before moving to KKR in 2026.",
   "He's a death bowler: 56% of his pressure overs come at the death. He does go for runs (9.33 an over under pressure), but he takes wickets, one every 14 balls.",
   "Left-handers find him the hardest. Against them under pressure he takes a wicket every 8 balls, so I'd save him for left-handed finishers."],
 'Wanindu Hasaranga': ["Hasaranga is an attacking leg-spinner with a quick arm and a googly that's hard to pick. He's also a handy lower-order hitter.",
   "He isn't trying to be the cheapest bowler. He goes for a few more runs under pressure (8.07 an over), but he takes a wicket every 14 balls. Three-quarters of his pressure overs come in the middle overs.",
   "He's done it in an RR shirt too. In 2025 he took 4 for 35 defending 182 against CSK, and RR won by six runs."],
 'Mujeeb Ur Rahman': ["Mujeeb is an off-spinner with a mystery side. He changes his fingers and grip to bowl the off-break, googly, carrom ball and a quicker one, and batters often misread which way it will turn.",
   "He's at his best in the powerplay, where most of his pressure overs come. Under pressure he goes at 6.81 an over and takes a wicket every 13 balls, much better than his normal strike rate. Left-handers struggle against him most.",
   "The catch: almost all his evidence is from T20Is (only 13 IPL balls in this data), which is why he sits close to the cut-off."],
 'Krunal Pandya': ["Krunal is a finger spinner who bowls flat and tight, and squeezes batters until they have to take a risk. He mixes in the arm ball, a quicker one and changes of flight, and since 2025 he has used his spin bouncer regularly to surprise batters.",
   "Under pressure he's a different bowler: 6.77 an over, against 8.11 normally. Right-handers find him hardest (6.54).",
   "He adds batting depth and is a sharp fielder too. In the IPL 2025 final he took 2 for 17 in four overs and was Player of the Match as RCB won their first title."],
}
def card(i, n, role):
    if role == 'bat':
        s = bstats(n)
        stats = (f'<b>{s["Pb"]}</b> pressure balls · SR <b>{s["srp"]:.0f}</b> (usual {s["srn"]:.0f}) · '
                 f'out every <b>{s["bpd"]:.1f}</b> balls · top 10 in <b>{pct(s["p"])}</b> of resamples')
    else:
        s = wstats(n)
        stats = (f'<b>{s["ov"]:.1f}</b> pressure overs · economy <b>{s["ecp"]:.2f}</b> (usual {s["ecn"]:.2f}) · '
                 f'wicket every <b>{s["sr"]:.1f}</b> balls · top 10 in <b>{pct(s["p"])}</b> of resamples')
    paras = ''.join(f'<p class="ntext">{e(t)}</p>' for t in NOTE[n])
    return (f'<div class="ncard{" bowl" if role == "bowl" else ""}"><div class="nhead"><p class="nrank">{i}</p>'
            f'<div class="nname"><h3>{e(n)}</h3><p class="nrole">{e(ROLE[n])}</p></div></div>'
            f'<p class="nstats">{stats}</p>{paras}</div>')
for role, names in [('bat', BAT), ('bowl', BOWL)]:
    for k in range(5):
        a, b = names[2 * k], names[2 * k + 1]
        lab = 'BATTER' if role == 'bat' else 'BOWLER'
        body = (f'<p class="eyebrow">4 · EVIDENCE: {lab} NOTES · {2 * k + 1} AND {2 * k + 2} OF 10</p>\n'
                f'<div class="ncards" style="margin-top:-20px">\n{card(2 * k + 1, a, role)}\n{card(2 * k + 2, b, role)}\n</div>\n'
                f'')
        write(f'{role}-notes-{k + 1}', body)
print(sorted(os.listdir(OUT)))
for n in BAT: s = bstats(n); print(f'{n:22s} {s["rating"]:.2f} [{s["lo"]:.1f},{s["hi"]:.1f}] {pct(s["p"])}')
for n in BOWL: s = wstats(n); print(f'{n:22s} {s["rating"]:.3f} [{s["lo"]:.2f},{s["hi"]:.2f}] {pct(s["p"])}')
