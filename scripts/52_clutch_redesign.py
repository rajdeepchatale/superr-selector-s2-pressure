"""Slide 13 (clutch) redesign: small-multiple bar charts, one panel per role.

Reads the split-half results from outputs/v3/deck_numbers.json (script 37),
draws each bar from the exact value and labels it to two decimals.
Rewrites deck/project/slides/clutch.html and swaps the old .cl-* rules in
deck/project/deck.css for the new .cg-* rules. Numbers are unchanged.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
NUM = json.loads((ROOT / "outputs/v3/deck_numbers.json").read_text())
SLIDE = ROOT / "deck/project/slides/clutch.html"
CSS = ROOT / "deck/project/deck.css"

bat, bowl = NUM["bat_repeat_v3"], NUM["bowl_repeat_v3"]
ROWS = [  # name, description, key, hero
    ("Clutch gap", "Pressure minus usual level. My first idea.", "gap", False),
    ("Pressure balls only", "The top 20% of balls, nothing else.", "P", False),
    ("Pressure Rating", "Every ball, weighted by its Index.", "rating", True),
    ("Every ball equal", "Steadier for batters, but ignores pressure.", "equal", False),
]

# panel geometry (px): same scale and zero in both panels
P_W, ROW_H, BAR_H = 500, 80, 28
SCALE = 850          # px per 1.0 of split-half agreement
X0 = 156             # zero line inside each panel
LAB_W, LAB_GAP = 80, 12
V_TOP = 25           # 26px text, line-height 1.2, centred on the bar


def fmt(v):
    r = round(v, 2)
    return ("+" if r > 0 else "−" if r < 0 else "") + f"{abs(r):.2f}"


def panel(v, role, extra=""):
    w = round(abs(v) * SCALE)
    if v >= 0:
        bar = f'<div class="cg-bar {role}" style="left:{X0}px; width:{w}px"></div>'
        lab = f'<p class="cg-v" style="left:{X0 + w + LAB_GAP}px">{fmt(v)}</p>'
    else:
        bar = f'<div class="cg-bar {role} neg" style="left:{X0 - w}px; width:{w}px"></div>'
        lab = f'<p class="cg-v neg" style="left:{X0 - w - LAB_GAP - LAB_W}px">{fmt(v)}</p>'
    assert (X0 - w - LAB_GAP - LAB_W >= 0) if v < 0 else (X0 + w + LAB_GAP + LAB_W <= P_W), (v, role)
    return f'<div class="cg-pan{extra}">{bar}{lab}<div class="cg-zero"></div></div>'


rows_html = []
for i, (name, desc, key, hero) in enumerate(ROWS):
    if hero:
        title = (f'<div class="cg-nrow"><p class="cg-name">{name}</p>'
                 f'<p class="cg-pill">What I rank on</p></div>')
    else:
        title = f'<p class="cg-name">{name}</p>'
    rows_html.append(
        f'<div class="cg-row{" pick" if hero else ""} cg-a" style="--i:{i + 2}">'
        f'<div class="cg-lab">{title}<p class="cg-desc">{desc}</p></div>'
        f'{panel(bat[key], "bat")}{panel(bowl[key], "bowl", " p2")}</div>')

axis_pan = ('<div class="cg-pan cg-axp{}"><div class="cg-zero"></div>'
            '<p class="cg-zl">0 = chance</p></div>')

html = (
    '<section id="clutch" class="dark">\n'
    '<div class="head"><p class="eyebrow">2 · WHAT I LEARNED BUILDING IT</p>'
    '<h2>The “clutch gap” doesn’t repeat</h2></div>\n'
    '<p class="cg-dek cg-a" style="--i:0">The test: I split each player’s matches into two random halves, '
    '40 times, and checked how well the halves agree.<br>A real skill shows up in both.</p>\n'
    '<div class="cg-chart">\n'
    '<div class="cg-row cg-hd cg-a" style="--i:1"><div class="cg-lab"><p class="cg-colh">What I measured</p></div>'
    '<div class="cg-ph"><div class="cg-sw bat"></div><p>Batters</p></div>'
    '<div class="cg-ph p2"><div class="cg-sw bowl"></div><p>Bowlers</p></div></div>\n'
    + "\n".join(rows_html) + "\n"
    '<div class="cg-row cg-ax cg-a" style="--i:6"><div class="cg-lab"></div>'
    + axis_pan.format("") + axis_pan.format(" p2") + '</div>\n'
    '</div>\n'
    '<p class="hl-y cg-take cg-a" style="--i:10">Pressure Rating is more than twice as steady as '
    'pressure balls alone, and still leans on the tight moments.</p>\n'
    '<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>\n'
    '<p class="pnum"></p></section>\n'
)

NEW_CSS = f"""
/* slide 13: clutch-gap repeatability, one bar panel per role */
@keyframes cgGrow {{ from {{ transform: scaleX(0); }} }}
@keyframes cgFade {{ from {{ opacity: 0; }} }}
.cg-a {{ animation: clIn 420ms cubic-bezier(0.2, 0.7, 0.2, 1) both; animation-delay: calc(var(--i) * 70ms); }}
.cg-dek {{ font-size: 26px; line-height: 1.4; color: #BFC8D8; }}
.cg-chart {{ display: flex; flex-direction: column; }}
.cg-row {{ display: flex; align-items: center; height: {ROW_H}px; padding: 0 20px; border-radius: 10px; box-sizing: border-box; }}
.cg-row.pick {{ background: #1F3156; animation: clIn 420ms cubic-bezier(0.2, 0.7, 0.2, 1) both, clBand 420ms ease-out both; animation-delay: calc(var(--i) * 70ms), 640ms; }}
.cg-hd {{ height: 50px; align-items: flex-start; border-bottom: 2px solid #22314F; border-radius: 0; }}
.cg-ax {{ height: 46px; align-items: flex-start; }}
.cg-lab {{ width: 520px; margin-right: 40px; display: flex; flex-direction: column; gap: 2px; }}
.cg-colh {{ font-size: 24px; font-weight: 600; line-height: 1.2; color: #9AA6BC; }}
.cg-nrow {{ display: flex; align-items: center; gap: 14px; }}
.cg-name {{ font-size: 28px; font-weight: 600; line-height: 1.2; color: #F5F4EF; }}
.cg-desc {{ font-size: 24px; line-height: 1.3; color: #9AA6BC; }}
.cg-pill {{ font-size: 24px; font-weight: 700; line-height: 1.2; color: #14213D; background: #FFE47A; padding: 2px 10px; border-radius: 6px; }}
.cg-ph {{ width: {P_W}px; padding-left: {X0 - 8}px; box-sizing: border-box; display: flex; align-items: center; gap: 10px; }}
.cg-ph p {{ font-size: 24px; font-weight: 600; line-height: 1.2; color: #F5F4EF; }}
.cg-sw {{ width: 16px; height: 16px; border-radius: 4px; }}
.cg-pan {{ width: {P_W}px; height: {ROW_H}px; position: relative; }}
.cg-ph.p2, .cg-pan.p2 {{ margin-left: 64px; }}
.cg-axp {{ height: 46px; }}
.cg-zero {{ position: absolute; left: {X0 - 1}px; top: 0; width: 2px; height: {ROW_H}px; background: #7F8BA3; }}
.cg-axp .cg-zero {{ height: 10px; }}
.cg-zl {{ position: absolute; left: {X0 - 90}px; top: 12px; width: 180px; text-align: center; font-size: 24px; line-height: 1.2; color: #9AA6BC; }}
.cg-bar {{ position: absolute; top: {(ROW_H - BAR_H) // 2}px; height: {BAR_H}px; border-radius: 4px; transform-origin: left center; animation: cgGrow 480ms cubic-bezier(0.2, 0.7, 0.2, 1) both; animation-delay: calc(var(--i) * 70ms + 140ms); }}
.cg-bar.neg {{ transform-origin: right center; }}
.cg-bar.bat, .cg-sw.bat {{ background: #3987E5; }}
.cg-bar.bowl, .cg-sw.bowl {{ background: #EA6632; }}
.cg-v {{ position: absolute; top: {V_TOP}px; width: {LAB_W}px; font-size: 26px; font-weight: 600; line-height: 1.2; color: #C9D1DE; font-variant-numeric: tabular-nums; animation: cgFade 240ms ease-out both; animation-delay: calc(var(--i) * 70ms + 420ms); }}
.cg-v.neg {{ text-align: right; }}
.cg-row.pick .cg-v {{ color: #F5F4EF; font-weight: 700; }}
.cg-take {{ font-size: 28px; line-height: 1.4; }}
"""

css = CSS.read_text(encoding="utf-8")
lines = css.splitlines()
keep = [l for l in lines if not (l.lstrip().startswith(".cl-") or l.startswith("@keyframes clDot")
                                or l.lstrip().startswith(".cg-") or l.startswith("@keyframes cg")
                                or l.startswith("/* slide 13: clutch-gap"))]
css = "\n".join(keep).rstrip("\n") + "\n" + NEW_CSS.lstrip("\n")
assert "@keyframes clIn" in css and "@keyframes clBand" in css
CSS.write_text(css, encoding="utf-8")
SLIDE.write_text(html, encoding="utf-8")
print("wrote", SLIDE.name, "and", CSS.name)
print({r[2]: (fmt(bat[r[2]]), fmt(bowl[r[2]])) for r in ROWS})
