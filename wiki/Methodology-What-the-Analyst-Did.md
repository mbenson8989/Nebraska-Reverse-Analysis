# Methodology: What the Analyst Did

> **\*All 2026 figures are UNOFFICIAL.** Nebraska Secretary of State (SOS) results site, "Unofficial Results," county data re-downloaded Nov 27, 2026 10:21–10:24 AM CT (1,322 of 1,322 precincts; 779,787 ballots cast). The State Board of Canvassers meets Nov 30, 2026 at 11:30 AM CT; numbers can still change. Registration: SOS VR Statistics Count Report processed Nov 1, 2026. **Treating the removed votes as injected votes is the analyst's hypothesis.** The arithmetic measures a pattern. It cannot test cause, and nothing here is proof of wrongdoing.

Plain steps. Anyone with the SOS files and a spreadsheet can redo this.

**Terms.** *Registration share* = a party's registered voters ÷ all registered voters. *Gap (G)* = vote share minus registration share. *Fitted line* = the straight line that best runs through all 93 counties on a chart of gap against registration share. *Multiplier (m)* = the line's slope. *Offset (b)* = where the line sits when registration share is zero; Nebraska's own constant. *Residual* = how far one county sits above (+) or below (−) the line. *Full reversal* = residual + offset. *Zeroed* = a county whose full reversal comes out negative, set to 0.

**(a) Use official Democratic registration.** Nebraska registers voters by party. I use the SOS VR Statistics Count Report (processed Nov 1, 2026): D = Democratic registered ÷ all registered × 100, per county.

**(b) Forward equation.** S = Democratic votes ÷ total ballots cast × 100. G = S − D. One denominator, total ballots cast, for every race and every county.

**(c) Fit Nebraska's line.** Plot all 93 counties: G on the vertical axis, D/100 on the horizontal. Fit one straight line, G = m × (D/100) + b, by least squares. Nebraska data only. No other state's constants.

**(d) Residual.** For each county, residual = actual G − line value. Above the line is positive.

**(e) Full reversal.** Removal (pts) = residual + b, county by county. That takes out the county's distance above the line *and* Nebraska's own offset. Negative results are set to 0. Removal votes = removal ÷ 100 × ballots, rounded to whole votes.

**(f) Sum the counties.** Add the 93 county removal votes for the statewide total. Move them from the challenger to the Republican and recount the winner.

**(g) One race at a time.** Each statewide race gets its own line, its own offset and its own total: Senate, Governor, Secretary of State, Treasurer, Attorney General. Never add races together; the same ballots are in every race.

**(h) Double verification.** Two independent passes, different code and different parsers, each re-read the raw SOS files for all 93 counties. Every county cell must match before anything ships. This edition: 7,546 checks, 0 mismatches.

**(i) 2026 is unofficial.** Every 2026 number carries a \*. The state canvass is Nov 30, 2026. When official numbers post, this is re-run.

## Worked example: Cedar County, Governor 2026\*

| Step | Value |
|---|---|
| Walz votes / ballots cast | 681 / 4,050 |
| S = Walz ÷ ballots × 100 | 16.81\* |
| Democratic registered / all registered | 826 / 5,777 |
| D | 14.30 |
| G = S − D | +2.52\* |
| Line value = 27.3807 × (14.30/100) + 3.1747 | 7.09 |
| Residual = G − line | -4.57\* |
| Full reversal = residual + 3.1747 | -1.40 → **zeroed (0)** |

Cedar sits below the 2026 Governor line, so the full reversal removes nothing there. Cedar's 2022→2026\* change (ΔG +7.91\*) is a different measure; see the public Locked-Nebraska-Formula page.

## Worked example: Sarpy County, Governor 2026\*

| Step | Value |
|---|---|
| S | 38,666 ÷ 81,633 × 100 = 47.37\* |
| D | 34,521 ÷ 133,068 × 100 = 25.94 |
| G | +21.42\* |
| Line value | 10.28 |
| Residual | +11.15\* |
| Removal = residual + offset | 14.32 pts |
| Removal votes = 14.3201 ÷ 100 × 81,633 | **11,690** |
| Walz → after; Pillen → after | 38,666 → 26,976; 36,464 → 48,154 |

## What this does and does not show

It shows where, and by how much, each county's Democratic share of ballots sits above what Nebraska's own registration line predicts. It does not show why. Nonpartisan voters (about 285,000 registered) and Republicans who cross over also vote for Democratic and independent candidates, and the equation cannot separate them. Calling the removed votes "injected" is the hypothesis being tested, and it needs ballot-level records (the Cast Vote Record) to test.

---
[Home](Home.md) · [Full Reversal Analysis](Full-Reversal-Analysis.md)
