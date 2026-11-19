# Selector's War Room — design specification

The visual system for `docs/index.html`. Every value here is implemented in that file's
single `<style>` block and was measured, not estimated.

---

## 1. The world: Royals

The page is designed **for Rajasthan Royals specifically**, not for cricket generally and
not for a dashboard template. The identity is drawn from the client and the place: Royals
indigo and pink, Jaipur sandstone, marigold.

This matters beyond decoration. The entry is read by RR's selection panel. A page built in
their own colours argues, before a word is read, that the work was done for them.

**Mechanism in one sentence:** most deliveries cannot change a match, so rank players only
on the ones that can.

**The physical scene:** a selection panel reviewing candidates on a laptop or a meeting-room
screen, sometimes printed. That scene decides the light. The page **field** is deep indigo
so the artifact reads as branded and owned; the **data sits on sandstone sheets** so dense
numeric tables stay as legible and printable as a scorecard. Dark chrome, light data.

**Colour strategy: Committed.** One saturated field owns the surface; the sheets and the
pink carry everything else.

### What this replaced, and why

The previous version was navy chrome on a cream page with yellow accents, rounded cards and
floating pill tabs. It was competent and it was anonymous — the palette, the 14px radius,
the soft shadow and the pill nav are what any dashboard ships. The first pass at improving
it changed the typeface and rebuilt one tab but **kept that world**, which made it a
refinement wearing a redesign's name. This is the replacement.

### Directions considered and rejected

| Considered | Rejected because |
|---|---|
| Editorial serif on a cream ground | Cream + high-contrast serif + warm accent is the most recognisable generated-design cluster there is. |
| Floodlit night match: near-black with one neon accent | The second such cluster. Also loses printability for a panel that may print the page. |
| Scorebook: paper, ruled columns, scorer's red and black | Genuinely good, and the closest rival. Rejected only because it is the furthest from the client's own identity, which is this entry's strongest argument. |

---

## 2. Colour

Every pairing below was computed against WCAG before it was written into the file.

| Token | Hex | Role | Measured |
|---|---|---|---|
| `--field` | `#0E1B4D` | Royals indigo. The page field | — |
| `--field-d` | `#091233` | Header, deepest ground | — |
| `--sheet` | `#F4EDE4` | Jaipur sandstone. Every data surface | — |
| `--sheet-2` | `#EDE3D4` | Bar tracks, row hover, inset panels | — |
| `--rule` | `#DBCFBB` | Hairlines on sandstone | — |
| `--rule-d` | `#2B3B72` | Hairlines on indigo | — |
| `--ink` | `#101733` | Text on sandstone | 15.16:1 |
| `--ink-2` | `#555A70` | Secondary text on sandstone | 5.87:1 |
| `--on` | `#EDEAF5` | Text on indigo | 13.79:1 |
| `--on-2` | `#A3A9CE` | Secondary text on indigo | 7.11:1 |
| `--pink` | `#ED2E8A` | RR pink. Live state, active tab, fills | — |
| `--pink-ink` | `#C2186B` | Batter series: bars and text on sandstone | 4.97:1 |
| `--saff` | `#A34D0A` | Bowler series: marigold, bars and text | 4.99:1 |
| `--gold` | `#D9A441` | Identity accent, **on the indigo field only** | 7.28:1 |

### Three findings that changed the palette

- **Pink cannot be body text on indigo.** `#ED2E8A` on `#0E1B4D` is 4.18:1. It is used as a
  fill, or as large text, never as small text on the field.
- **Gold cannot be a bar on sandstone.** `#D9A441` on `#EDE3D4` is 1.77:1 — nearly invisible.
  Gold was therefore confined to the dark field, where it reaches 7.28:1.
- **The ≥75% stability chip is indigo, not gold.** Gold against sandstone edges at 1.94:1;
  indigo reaches 13.79:1 and reads like a scorer inking a name in. Gold's intended job was
  taken by the colour that could actually do it.

Dark text on pink is `#280517` (4.77:1). The obvious `#3D0A24` measured 4.23:1 and was
rejected. Dark text on the active tab is `#0A1024` (4.82:1); white would have been 3.92:1.

---

## 3. Typography

**Archivo, one superfamily, three widths.** A single family deployed deliberately across its
width axis reads as a system; two unrelated families read as a template. Archivo sits in the
signage and highway-lettering lineage — expanded and heavy it behaves like board lettering,
at normal width it is a neutral high-legibility data face.

```
https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&display=swap
```

| Role | Width | Weight | Tracking | Used on |
|---|---:|---:|---|---|
| Display | 125% | 700 | −0.025em | `h1.st`, wordmark, funnel figures, drawer rank |
| Sub-display | 112% | 700 | −0.02em | section headings, `.kept`, `.lv` |
| Data / UI | 100% | 400–700 | 0 | everything else |

**Numerals are tabular everywhere**, set on `:root` and never switched off. Verified in the
browser rather than assumed: `11111` and `00000` both render at exactly 45.45px, so rankings
cannot jitter as the What if? tab re-ranks.

---

## 4. Form

The old world's signature was the rounded floating card. This one's is **the sheet on the
field**: a flat sandstone plane laid on indigo, squared off, with no shadow doing work that
contrast already does.

- **Radius:** 4px on sheets, 3px on controls and chips. Nothing is a pill. The previous
  999px nav pills and stability pills are gone, and that single change carries much of the
  difference in feel.
- **Elevation:** only the drawer and the first-run cue cast a shadow, because only they
  genuinely float. Sheets sit flat.
- **Navigation:** one connected segmented control with hairline dividers, not four floating
  pills. The active tab is a solid pink plate.
- **Series identity:** a 2px rule under each sheet's title in that series' colour — pink for
  batters, marigold for bowlers — replacing the old 5px coloured card-top border.
- **No coloured `border-left` callouts**, no gradient text, no glass, no decorative blur.

---

## 5. The method tab

Eight identical cards of numbered-circle-plus-heading, joined by unicode arrows, each padded
to a 205px minimum so the short ones held visible dead air. It described the pipeline without
showing it.

It is now **a single proportional bar**: 35,172 pressure balls in pink against 140,690 that
could not swing a match. One graphic makes the whole argument.

Below it, two bars for where pressure actually falls. These are **two separate cuts, not
parts of one whole** — 77% in the chase and 45% in the middle overs do not sum to anything,
so they are never stacked into a single fake total. Then six steps on a hairline spine, no
card chrome. Step numbers survive here, and only here, because the content genuinely is an
ordered pipeline.

---

## 6. Icons

Drawn, never glyphs. One specification so the set reads as one hand:

- 24×24 viewBox, `fill: none`, `stroke: currentColor`
- `stroke-width: 1.8`, round caps and joins
- Coloured by `currentColor`, sized by the element, always `aria-hidden`

Set: cursor, arrow-right, sliders, close. The footer's `←` `→` remain as text because they
name physical keys rather than standing in for icons.

---

## 7. Motion

One authored moment per interaction; nothing ambient.

| Moment | Duration | Easing |
|---|---:|---|
| Tab change | 280ms | `ease-out` |
| Drawer open | 250ms | `ease-out` |
| First-run cue | 420ms | `cubic-bezier(.16,1,.3,1)` |
| State feedback | 120–150ms | `ease` |

All of it, including the tab entrance and the drawer slide, is disabled under
`prefers-reduced-motion: reduce`.

---

## 8. Browser surfaces

- `::selection` — pink ground, near-black text
- `:focus-visible` — 2.5px ring: gold on the indigo field, pink on batter rows, marigold on
  bowler rows
- Drawer scrollbar — themed thumb and track, not the browser default
- Tabular figures throughout

---

## 9. Quality floor

Measured on the built result:

- **0 contrast failures** across all four tabs, audited against computed styles in the
  browser rather than against the stylesheet
- **0 design-detector findings** (was 13 before this work began)
- 14 of 14 keyboard stops show a colour-correct focus ring
- Correct ARIA tablist wiring throughout
- No console errors; no overflow on any tab at the fixed 1600×900 stage
- The page works with `localStorage` blocked
