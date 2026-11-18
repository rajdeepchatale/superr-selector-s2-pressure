"""Slide 4 (method): the method on one page as a flow diagram.

Eight steps in two rows (left to right, a return arrow between rows), each with
the slides that explain it, then the robustness line. Replaces the five-card
version in place (same id and position), so slide numbers do not change.
All numbers are the ones already in the deck (data, pressure-def, rating,
stress slides).
"""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SLIDE = ROOT / "deck/project/slides/method.html"
CSS = ROOT / "deck/project/deck.css"
BACKUP = ROOT / "deck_backup_method_cards.html"
if not BACKUP.exists():
    shutil.copy(SLIDE, BACKUP)

BOX_W, GAP = 380, 48            # 4 boxes + 3 arrows = 1664px
ARROW = ('<svg class="fl-arrow fl-a" style="--i:{i}" aria-label="then" width="48" height="24" viewBox="0 0 48 24">'
         '<path d="M4 12 H34" stroke="#6B7280" stroke-width="3" stroke-linecap="round" fill="none"/>'
         '<path d="M32 4 L45 12 L32 20 Z" fill="#6B7280"/></svg>')

STEPS = [  # number, title, detail (inline <b> allowed), slides, extra block, highlight
    (1, "The data", "883 matches, ball by ball. <b>735 rated</b>: IPL 2022–26 and full-member T20Is.", "Slide 5", "", False),
    (2, "Win chance", "A model gives the batting side’s <b>chance of winning before every ball</b>.",
        "Slide 6", "", False),
    (3, "Pressure Index", "How far a ball can swing that chance, ranked 0 to 100.",
        "Slides 6–8", '<p class="fl-pill">Top 20% = pressure balls</p>', False),
    (4, "Ball value", "<b>Runs above an average player</b> in that exact spot. A wicket is worth 8 runs.",
        "Slides 9–10", "", False),
    (5, "Fair comparison", "Adjusted for who they faced. Bowlers also for ground, dew and home side.",
        "Slides 11, 15", "", False),
    (6, "Pressure Rating", "Every ball <b>weighted by its Index</b>, then small samples pulled toward average.",
        "Slides 12–13", "", False),
    (7, "2,000 resamples", "Redraw the matches 2,000 times and count each player’s top-10 finishes.",
        "Slide 19", "", False),
    (8, "Two top 10s", "The ten who make the top 10 <b>most often</b>, ordered by rating.",
        "Slides 2, 16–18", "", True),
]


def box(n, title, detail, refs, extra, hi, i):
    return (f'<div class="fl-box{" y" if hi else ""} fl-a" style="--i:{i}">'
            f'<div class="fl-top"><p class="fl-n">{n}</p><h3 class="fl-t">{title}</h3></div>'
            f'<p class="fl-d">{detail}</p>{extra}<div class="fl-sp"></div>'
            f'<p class="fl-r">{refs}</p></div>')


def row(steps, start):
    parts = []
    for k, s in enumerate(steps):
        if k:
            parts.append(ARROW.format(i=start + k))
        parts.append(box(*s, start + k))
    return '<div class="fl-row">' + "".join(parts) + "</div>"


c4 = 3 * (BOX_W + GAP) + BOX_W // 2   # centre of box 4
c5 = BOX_W // 2                       # centre of box 5
RETURN = (f'<svg class="fl-ret fl-a" style="--i:4" aria-label="then on to step 5" width="1664" height="44" '
          f'viewBox="0 0 1664 44"><path d="M{c4} 0 V10 Q{c4} 22 {c4 - 12} 22 H{c5 + 12} Q{c5} 22 {c5} 34 V33" '
          f'stroke="#6B7280" stroke-width="3" stroke-linecap="round" fill="none"/>'
          f'<path d="M{c5 - 9} 32 L{c5} 44 L{c5 + 9} 32 Z" fill="#6B7280"/></svg>')

html = (
    '<section id="method">\n'
    '<div class="head"><p class="eyebrow">THE METHOD ON ONE PAGE</p>'
    '<h2>How the model turns ball-by-ball data into two top 10s</h2></div>\n'
    '<div class="fl-flow">\n'
    + row(STEPS[:4], 0) + "\n" + RETURN + "\n" + row(STEPS[4:], 5) + "\n"
    '</div>\n'
    '<p class="hl-y fl-a" style="--i:10; font-size:26px; line-height:1.4"><b>Then I tried to break it:</b> '
    'ten changes to the settings, six more pressure ideas, and a test of 2022–24 ratings against 2025–26.</p>\n'
    '<p class="foot">Most reliable under pressure · SupeRR Selector Season 2</p>\n'
    '<p class="pnum"></p></section>\n'
)

NEW_CSS = f"""
/* slide 4: method flow diagram */
@keyframes flIn {{ from {{ opacity: 0; transform: translateY(12px); }} }}
.fl-a {{ animation: flIn 380ms cubic-bezier(0.2, 0.7, 0.2, 1) both; animation-delay: calc(var(--i) * 70ms); }}
.fl-flow {{ display: flex; flex-direction: column; flex-shrink: 0; }}
.fl-row {{ display: flex; align-items: stretch; flex-shrink: 0; }}
.fl-arrow {{ align-self: center; width: 48px; height: 24px; }}
.fl-box {{ width: {BOX_W}px; box-sizing: border-box; background: #FCFBF8; border: 2px solid #E2E0D8; border-radius: 16px; padding: 20px 22px; display: flex; flex-direction: column; gap: 10px; }}
.fl-box.y {{ background: #FFF6CC; border-color: #EBC94A; }}
.fl-top {{ display: flex; align-items: center; gap: 14px; }}
.fl-n {{ width: 40px; height: 40px; border-radius: 20px; background: #14213D; color: #F5F4EF; font-family: 'Space Grotesk', Arial, sans-serif; font-size: 24px; font-weight: 600; line-height: 40px; text-align: center; }}
.fl-t {{ font-size: 28px; line-height: 1.2; color: #14213D; }}
.fl-d {{ font-size: 24px; line-height: 1.35; color: #3B4252; }}
.fl-pill {{ align-self: flex-start; font-size: 24px; font-weight: 700; line-height: 1.3; color: #14213D; background: #FFE47A; padding: 2px 10px; border-radius: 6px; }}
.fl-sp {{ flex: 1; }}
.fl-r {{ font-size: 24px; line-height: 1.2; color: #6B7280; }}
.fl-ret {{ width: 1664px; height: 44px; flex-shrink: 0; }}
"""

css = CSS.read_text(encoding="utf-8")
lines = [l for l in css.splitlines()
         if not (l.lstrip().startswith(".fl-") or l.startswith("@keyframes flIn")
                 or l.startswith("/* slide 4: method flow"))]
css = "\n".join(lines).rstrip("\n") + "\n" + NEW_CSS.lstrip("\n")
CSS.write_text(css, encoding="utf-8")
SLIDE.write_text(html, encoding="utf-8")
print("wrote", SLIDE.name, "| box centres", c4, c5)
