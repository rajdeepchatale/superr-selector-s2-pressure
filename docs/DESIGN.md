# Selector's War Room — design specification

The visual system for `docs/index.html`. Every rule here is implemented in that file's
single `<style>` block. This document exists so the next change is a decision, not a guess.

---

## 1. Direction: the scorebook

The design is grounded in cricket's own visual vernacular — the ruled scorebook and the
match-day board — rather than in dashboard convention. That means **ruled columns, tabular
figures, and ink on paper**, not cards floating on a grey field.

Three consequences that govern everything below:

1. **Rules beat boxes.** A hairline separating two things is preferred to a container
   enclosing each of them. Card chrome is spent only where a genuine panel exists.
2. **Numerals are the subject.** This is a ranking. Figures get the tabular treatment, the
   alignment and the weight; labels get out of the way.
3. **One loud thing per screen.** Each tab has exactly one element allowed to shout. The
   rest is quiet.

### Rejected directions, and why

| Considered | Rejected because |
|---|---|
| Editorial serif display on the cream page | Cream ground + high-contrast serif + warm accent is the single most recognisable generated-design cluster. The existing cream is defensible on its own; adding the serif would have completed the tell. |
| Inverting to a dark "broadcast" ground | Dense numeric tables read worse reversed out, and the real use scene is a lit selection meeting, often printed or screenshotted. |
| Keeping Inter + Space Grotesk | Both are on the overused list; two grotesques together also give no real contrast, so the hierarchy was doing no work. |

---

## 2. Typography

**One superfamily, two widths.** Archivo, variable, width axis 62–125 and weight axis
400–700. A single family deployed deliberately at two widths reads as a system; two
unrelated families read as a template.

Archivo is a grotesque in the signage and highway lettering lineage. Expanded and heavy it
behaves like scoreboard lettering; at normal width it is a neutral, high-legibility data
face. That range is exactly the two jobs this page has.

```
https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&display=swap
```

| Role | Family | Width | Weight | Tracking | Used on |
|---|---|---:|---:|---|---|
| Display | Archivo | 112 | 700 | −0.02em | `h1.st`, `.brand .t`, `.drk`, `.dnm`, `.kept`, funnel figures |
| Data / UI | Archivo | 100 | 400–600 | 0 | everything else |
| Column heads | Archivo | 100 | 600 | 0.06em | `th`, `.shead` |

**Numerals.** `font-variant-numeric: tabular-nums` is set globally on `:root` and never
switched off. Every rating, percentage and rank sits in a fixed-width column; proportional
figures would make the rankings jitter between states in the What if? tab.

**Scale.** 36 / 26 / 23 / 19 / 17 / 15 / 14 / 13 px. Steps are large enough to be read as
intentional. Nothing between 19 and 23.

---

## 3. Colour

The palette is unchanged — it was the page's strongest existing asset and is not a default.
Only the muted grey moved, for contrast.

| Token | Hex | Role |
|---|---|---|
| Navy | `#14213D` | Header, ink, inverted panels |
| Paper | `#F5F4EF` | Page ground |
| Panel | `#FCFBF8` | Raised surfaces |
| Rule | `#E2E0D8` | Hairlines, borders |
| Yellow | `#FFE47A` | The single accent. Marks *the answer* and nothing else |
| Batter blue | `#2A78D6` | Batter column identity |
| Bowler orange | `#D4572A` | Bowler column identity |
| Ink | `#3B4252` | Body text |
| Muted | `#5A6273` | Secondary text — **darkened from `#6B7280`** |
| Funnel track | `#EAE7DC` | The "everything else" ground in the method bar |
| Funnel figure | `#7E7763` | De-emphasised figure on that track (3.60:1) |
| Funnel caption | `#69624E` | De-emphasised caption on that track (4.91:1) |

**Why the muted grey changed.** `#6B7280` on `#FCFBF8` computes to 4.67:1 — technically a
pass for 14px body text, but with no margin, and it was carrying `.fine`, `.nextl`, `.drop`
and the footer. `#5A6273` computes to **5.92:1** on the same ground.

**Accent discipline.** Yellow means "this is the answer". It is allowed on: the selected
tab, the stability figures at or above 75%, the primary call to action, and the final stage
of the method funnel. It is not decoration anywhere else.

---

## 4. What was removed

Simplification was a brief requirement, so removals are specified as precisely as additions.

| Removed | Count | Reason |
|---|---:|---|
| `.eb` eyebrow above every heading | 4 | A tracked all-caps kicker above a heading is template chrome. The headings carry themselves. |
| Middle-dot meta string in the header | 1 | `A · B · C` is generated-page furniture. Replaced with a plain subtitle and the author set apart. |
| `.turn` "↓ then" connector | 1 | A unicode arrow doing a job the layout already does. |
| Eight-card method grid | 8 cards | Same-size cards of number + heading + text, used as the page structure, is the clearest generated-design tell on the site. Replaced per §5. |
| Three navy stat tiles | 3 | The hero-metric template: big number, small label, accent colour. Replaced with a ruled ledger. |
| Unicode glyphs as icons | `›` `→` `↓` `×` | Replaced by a drawn icon set, §6. The footer's `←` `→` stay: they name physical keys. |
| Tracked all-caps UI labels | 2 | `PICK A WHAT IF` / `OR MIX YOUR OWN` are template chrome. Now sentence case, weighted. Table column heads keep caps — that is scorecard convention, not decoration. |

---

## 5. The method tab, rebuilt

The old screen was eight equal cards in a 4×2 grid joined by arrows, each card padded to a
205px minimum so the short ones held visible dead air, with the lower third of the stage
empty. It described the pipeline without ever showing it.

It is replaced by **a funnel that shows the actual data reduction, with the real counts**:

```
883 matches audited
  └ 735 rated ............................ IPL 2022–26 + full-member T20Is
      └ 175,862 balls
          └ 35,172 pressure balls ........ top 20% of the Index, ~48 a match
```

- The funnel is a **single full-width proportional bar**: 175,862 balls, with the top 20%
  filled in yellow. This is the one loud element on the tab, and it is a real data graphic
  rather than a decorative shape.
- Beneath it the six modelling steps run as **one row separated by vertical hairlines**, no
  card chrome at all: number, title, one line of explanation.
- Step numbers are kept here, and only here, because the content genuinely is an ordered
  pipeline — each step consumes the previous step's output.

---

## 6. Icons

A drawn set, not glyphs. All icons share one specification so they read as one hand:

- 24×24 viewBox, `fill: none`, `stroke: currentColor`
- `stroke-width: 1.8`, `stroke-linecap: round`, `stroke-linejoin: round`
- Sized by the element, coloured by `currentColor`, never given their own colour
- Always `aria-hidden="true"` — every icon sits beside a real text label

Set: cursor (click affordance), arrow-right (navigation), sliders (settings), close.

---

## 7. Motion

**One authored moment per interaction, nothing ambient.** No entrance animation plays
without a user action behind it.

| Moment | Duration | Easing |
|---|---:|---|
| Tab change | 280ms | `ease-out` |
| Drawer open | 250ms | `ease-out` |
| First-run cue | 420ms | `cubic-bezier(.16,1,.3,1)` |
| Hover / state feedback | 120–150ms | `ease` |

Everything above is disabled under `prefers-reduced-motion: reduce`, including the tab
entrance and the drawer slide — not just the decorative cue.

---

## 8. Browser surfaces

The parts not drawn by hand still belong to the design:

- `::selection` — navy on yellow
- Drawer elevation — neutral `rgba(0,0,0,.16)`, offset and blurred; never a tinted halo
- `:focus-visible` — 2.5px ring, blue on light ground, yellow on navy, offset 2px
- Drawer scrollbar — 10px, rule-coloured thumb on panel track
- Table figures — tabular numerals throughout

---

## 9. Quality floor

Checked on the built result, not intended:

- Body text ≥ 4.5:1, large text and non-text UI ≥ 3:1
- Every interactive element reachable and visibly focused by keyboard
- Correct ARIA tablist wiring: `aria-controls`, `aria-labelledby`, `aria-selected`
- No console errors
- No overflow on any tab at the fixed 1600×900 stage
- `localStorage` access wrapped in `try/catch` — the page works with storage blocked
