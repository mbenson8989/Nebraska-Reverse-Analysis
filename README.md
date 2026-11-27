# Nebraska Reverse Analysis (PRIVATE)

**Private working repository. Not for publication.** Visibility must stay private until the owner explicitly decides otherwise.

Full Kansas-style reverse-factoring reversal of Nebraska's 2026\* statewide races (U.S. Senate, Governor, Secretary of State, State Treasurer, Attorney General) across all 93 counties.

\*All 2026 figures are **unofficial** (Nebraska SOS results site, downloaded Nov 27, 2026 ~10:21–10:24 AM CT). The state canvass is Nov 30, 2026. Treating the removed votes as injected votes is a **hypothesis**; the arithmetic measures a pattern and cannot test cause.

- **Wiki pages:** [`wiki/Home.md`](wiki/Home.md) (GitHub wikis are not used for this private repo; the pages live in `/wiki`).
- **Graphics:** `graphics/` (one per race, votes removed by race, top ten counties)
- **County tables (all 93):** `data/`
- **Raw inputs:** `raw/` (SOS county race JSON, SOS statewide CSV, 93 county turnout exports, VR reports Nov 2022 and Nov 2026, Census V2025, Nov 17 verified 2018–2026 panel)
- **Code and verification:** `scripts/` (passA.py, passB.py, compare.py, graphics.py, build_wiki.py), `verification/` (cell-by-cell comparison: 7,546 checks, 0 mismatches)

Scripts use absolute paths from the build machine (`/workspace/nebraska-reverse/...`); point them at `raw/` to re-run.
