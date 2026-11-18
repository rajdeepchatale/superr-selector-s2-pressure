# Most reliable under pressure

**Ranking T20 batters and bowlers on the balls that decide matches.**

Entry for Rajasthan Royals' SupeRR Selector Season 2, Round 1. Built from IPL 2022–26 and
T20Is between full members: 883 matches audited, **735 rated, 175,862 balls**.

[![Live dashboard](https://img.shields.io/badge/Live-Selector's_War_Room-FFE47A?style=flat-square&labelColor=14213D)](https://rajdeepchatale.github.io/superr-selector-s2-pressure/)
[![Python](https://img.shields.io/badge/Python-3.9+-3987E5?style=flat-square&labelColor=14213D)](https://www.python.org/)
[![Pipeline](https://img.shields.io/badge/Pipeline-53_scripts-EB6834?style=flat-square&labelColor=14213D)](scripts/)

**→ [Open the Selector's War Room](https://rajdeepchatale.github.io/superr-selector-s2-pressure/)**

---

## Contents

- [The idea](#the-idea)
- [Results](#results)
- [How the ranking works](#how-the-ranking-works)
- [How I tested it](#how-i-tested-it)
- [The dashboard](#the-dashboard)
- [Repository layout](#repository-layout)
- [Reproducing the results](#reproducing-the-results)
- [Data policy](#data-policy)
- [Author](#author)

---

## The idea

Performance under pressure is mostly noise. The "clutch gap", hot form, bad days and the
dot-ball squeeze all fail to repeat from one season to the next.

So the ranking ignores them. It scores what *does* repeat: **quality on the balls that can
swing a match, measured against the players each man actually faced.**

## Results

**Rating** is runs above an average player in the same situation and against the same
opposition — per 100 balls faced for batters, per 24 balls bowled for bowlers — with
pressure balls weighted most. **Stability** is how often a player stays in the top 10
across 2,000 match resamples.

### Batters

| # | Player | Rating | Stability |
|---:|---|---:|---:|
| 1 | Suryakumar Yadav | 20.9 | 96% |
| 2 | Abhishek Sharma | 19.9 | 92% |
| 3 | Phil Salt | 17.0 | 72% |
| 4 | Heinrich Klaasen | 16.7 | 73% |
| 5 | Tim David | 15.5 | 53% |
| 6 | Reeza Hendricks | 15.1 | 56% |
| 7 | Vaibhav Sooryavanshi | 14.5 | 44% |
| 8 | Glenn Phillips | 13.8 | 44% |
| 9 | Namboori Tilak Varma | 13.4 | 41% |
| 10 | Virat Kohli | 12.2 | 35% |

*Next in line: Cameron Green (12.8, 29%)*

### Bowlers

| # | Player | Rating | Stability |
|---:|---|---:|---:|
| 1 | Sunil Narine | 3.83 | 90% |
| 2 | Kuldeep Yadav | 3.34 | 82% |
| 3 | Jasprit Bumrah | 3.33 | 77% |
| 4 | Rashid Khan | 3.20 | 79% |
| 5 | Josh Hazlewood | 3.18 | 70% |
| 6 | Varun Chakravarthy | 2.90 | 66% |
| 7 | Krunal Pandya | 2.58 | 49% |
| 8 | Wanindu Hasaranga | 2.50 | 54% |
| 9 | Nathan Ellis | 2.49 | 48% |
| 10 | Mujeeb Ur Rahman | 2.37 | 41% |

*Next in line: Matheesha Pathirana (2.39, 38%)*

Each list is the ten players who stay in the top 10 most often, ordered by rating. The top
few picks are close to immovable; places 7–10 are genuine close calls, and the stability
column says so rather than hiding it.

## How the ranking works

| Step | Stage | What happens |
|---:|---|---|
| 1 | **Win chance** | Gradient-boosted models give the batting side's chance of winning before and after every ball. |
| 2 | **Pressure Index** | How far the win chance could move on that ball, ranked 0–100 against every other ball. The top 20% are *pressure balls* — about 48 a match. |
| 3 | **Ball value** | Runs above an average player in that exact situation, with a wicket worth 8 runs. |
| 4 | **Fair comparison** | Every ball adjusted for the opponent at the other end; bowlers also for ground, dew and home side. The pitch on the day is already absorbed by the baseline. |
| 5 | **Pressure Rating** | Each ball weighted by its Index, then shrunk toward average on small samples (empirical Bayes). |
| 6 | **Selection** | The ten players who stay in the top 10 most often across 2,000 match resamples, ordered by rating. |

Pressure is not just the death overs: **77%** of pressure balls come in the chase, and
**45%** fall in the middle overs.

## How I tested it

The ranking was built to be attacked, not defended:

- **Ten changes to the method** — reweighting pressure, recency, wicket value, and removing
  the opponent adjustment. Eight of the ten keep at least 8 of the 10 batters and 9 of the
  10 bowlers.
- **Six alternative definitions of pressure**, including shot choice and execution.
- **Out-of-sample test** — 2022–24 ratings used to predict 2025–26. Correlation of **+0.29
  for bowlers** and **+0.05 for batters**: bowling skill under pressure carries over, batting
  much less. This is a finding, not a flaw, and it is reported rather than buried.

Every variant is re-runnable from the dashboard's **What if?** tab.

## The dashboard

The **[Selector's War Room](https://rajdeepchatale.github.io/superr-selector-s2-pressure/)**
is a 16:9 companion to the methodology report, in four tabs:

| Tab | What it shows |
|---|---|
| **1. The answer** | Both top 10s. Click any player for his notes. |
| **2. How it works** | The eight steps from ball-by-ball data to the rankings. |
| **3. What if?** | Change a setting — pressure weight, recency, wicket value, opponent adjustment — and watch who survives. |
| **4. How sure** | How often each pick holds up across resamples and across every what-if. |

It is a single self-contained file (`docs/index.html`) with no build step, no backend and no
analytics. It ships **player ratings only — never ball-by-ball data.**

## Repository layout

```
.
├── docs/
│   └── index.html    Selector's War Room — served by GitHub Pages from /docs
├── scripts/          Full pipeline, numbered in run order (53 scripts + 2 shared libs)
│   ├── lib_pwi.py        Pressure-Weighted Impact: ball value above expected,
│   │                     weighted by Pressure Index, empirical-Bayes shrunk
│   └── lib_ratings.py    Core rating engine, shared by the validation,
│                         bootstrap and sensitivity runs
└── data/raw/         Empty by design — the data pack goes here and is git-ignored
```

## Reproducing the results

**Requirements:** Python 3.9+ with pandas, NumPy, scikit-learn and matplotlib.

```bash
pip install pandas numpy scikit-learn matplotlib
```

Place the six data-pack CSVs in `data/raw/`:

```
ball_by_ball.csv    matches.csv       competitions.csv
playing_eleven.csv  teams.csv         competition_team_player_mapping.csv
```

Scripts resolve paths relative to the repository root, so run them from there:

```bash
python scripts/01_audit.py
```

Then work through the pipeline in order:

| Stage | Scripts | Purpose |
|---:|---|---|
| 1 | `01_audit`, `02_reconcile` | Data integrity; rebuilds every innings total and matches it to the official result |
| 2 | `03_features` | Match state before every ball; flags rain-hit and no-result games |
| 3 | `04_wp_model` | Win-chance models and the Pressure Index |
| 4 | `05_expected`, `10_value_v2` | Baselines and the value of every ball |
| 5 | `12_final_ratings` | Player stats on pressure balls and first-pass ratings |
| 6 | `30_conditions_table` → `33_ratings_v3` | Conditions, opponent and ground adjustments, and final ratings with 2,000 resamples |
| 7 | `34_behaviour`, `35_form_model`, `36_wins` | Alternative pressure definitions, the form model, wins per season |
| 8 | `37_deck_numbers_v3`, `39_warroom_data`, `40_warroom_page`, `56_warroom_site` | Every number in the report, and the dashboard build |
| 9 | `44_shot_choice`, `49_paired_splits` | Shot choice and execution; the 200-split test behind the opponent adjustment |

The remaining scripts (`06`–`09`, `11`, `13`–`27`, `38`, `41`–`43`, `45`–`48`, `50`–`54`) are
earlier iterations, validation tests, charts and report builds. They are kept deliberately so
that every number can be traced back to the step that produced it.

## Data policy

The SupeRR Selector Season 2 data pack is licensed for this competition only and must not be
shared or published. **It is not in this repository and never should be** — `data/raw/` is
git-ignored, and so is every intermediate file derived ball-by-ball from it.

The dashboard was built to respect the same rule: it carries aggregated player ratings only.

## Author

**Rajdeep Chatale** — submitted for Rajasthan Royals' SupeRR Selector Season 2, Round 1.

This repository accompanies the full methodology report, which carries the complete
derivations, formulas and validation tables.
