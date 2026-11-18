# Most reliable under pressure

My entry for Rajasthan Royals' SupeRR Selector Season 2, Round 1: find the most reliable batters and bowlers under pressure, using IPL 2022–26 and T20Is between full members (735 matches, 175,862 balls).

## Live dashboard

**Selector's War Room:** https://rajdeepchatale.github.io/superr-selector-s2-pressure/

A 16:9 click-through companion to my methodology report, in four tabs:

1. **The answer:** both top 10s. Click any player to read his notes.
2. **How it works:** the eight steps from ball-by-ball data to the rankings.
3. **What if?:** change one setting (more weight on pressure, recent seasons, wicket value, no opponent adjustment) and see who stays.
4. **How sure:** how often each pick stays in the top 10.

It is one self-contained file, `docs/index.html`, and holds player ratings only, never ball-by-ball data.

## The idea in one line

Results under pressure are mostly noise: the "clutch gap", hot form, bad days and the dot-ball squeeze don't repeat. So I rank on what does repeat: quality on the balls that can swing a match, measured against the players each person actually faced.

## How the ranking works

1. **Win chance:** gradient-boosted models give the batting side's chance of winning before and after every ball.
2. **Pressure Index (0–100):** how far the win chance could move on that ball, ranked against every other ball. The top 20% are pressure balls.
3. **Value:** runs above an average player in the same situation, with a wicket worth 8 runs.
4. **Fair comparison:** every ball is adjusted for the player at the other end (batters and bowlers); bowlers also for the ground, dew and home side (dew and home are tiny). The pitch on the day is already read by the baseline.
5. **Pressure Rating:** each ball weighted by its Index, then shrunk toward average when the sample is small (empirical Bayes).
6. **Selection:** the ten players who stay in the top 10 most often across 2,000 match resamples, ordered by rating.

## Final lists

| # | Batters | Bowlers |
|---|---|---|
| 1 | Suryakumar Yadav | Sunil Narine |
| 2 | Abhishek Sharma | Kuldeep Yadav |
| 3 | Phil Salt | Jasprit Bumrah |
| 4 | Heinrich Klaasen | Rashid Khan |
| 5 | Tim David | Josh Hazlewood |
| 6 | Reeza Hendricks | Varun Chakravarthy |
| 7 | Vaibhav Sooryavanshi | Krunal Pandya |
| 8 | Glenn Phillips | Wanindu Hasaranga |
| 9 | Namboori Tilak Varma | Nathan Ellis |
| 10 | Virat Kohli | Mujeeb Ur Rahman |

## What's in this repo

| Folder | What it holds |
|---|---|
| `scripts/` | The full pipeline, numbered in run order (see below) |
| `docs/index.html` | The Selector's War Room dashboard, served by GitHub Pages. Player ratings only, no ball-by-ball data |
| `data/raw/` | Empty on purpose. Put the six data-pack CSVs here to run the code; git ignores them |

## How to reproduce

Python 3 with pandas, NumPy, scikit-learn and matplotlib. Run from the repo folder, in this order:

| Step | Scripts | What they do |
|---|---|---|
| 1 | `01_audit`, `02_reconcile` | Data checks; rebuilds every innings total and matches it to the official result |
| 2 | `03_features` | Match state before every ball; flags rain-hit and no-result games |
| 3 | `04_wp_model` | Win-chance models and the Pressure Index |
| 4 | `05_expected`, `10_value_v2` | Baselines and the value of every ball |
| 5 | `12_final_ratings` | Player stats on pressure balls and the original ratings |
| 6 | `30_conditions_table` to `33_ratings_v3` | Match conditions, opponent and ground adjustments, the tests behind them, final ratings with 2,000 resamples |
| 7 | `34_behaviour`, `35_form_model`, `36_wins` | The extra pressure ideas I tested, the form model, wins a season |
| 8 | `37_deck_numbers_v3`, `39_warroom_data`, `40_warroom_page`, `56_warroom_site` | Every number in the report, and the War Room dashboard (`docs/index.html`) |
| 9 | `44_shot_choice`, `49_paired_splits` | Shot choice and execution under pressure (the sixth idea); the 200-split test behind the opponent adjustment |

The other scripts (`06`–`09`, `11`, `13`–`27`, `38`, `41`–`43`, `45`–`48`, `50`–`54`) are earlier versions, validation tests, charts and the report build, kept so every step can be traced.

## Data rule

The data pack is for this competition only and must not be shared or published, so it is not in this repo and never should be.

## Deploy the dashboard

In this repo on GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main`, folder `/docs` → Save.** After a minute or two the dashboard is live at the link above.
