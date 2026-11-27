import json, pandas as pd, numpy as np, os, shutil
B='/workspace/nebraska-reverse/'; RP=B+'repo/'; W=RP+'wiki/'
for d in ('wiki','graphics','data','scripts','verification','raw'): os.makedirs(RP+d,exist_ok=True)
RA=json.load(open(B+'passA/results.json')); RB=json.load(open(B+'passB/results.json')); A=RA['races']; H=RA['history']; N=RA['notes']
X=json.load(open(B+'passA/extra.json')); V=json.load(open(B+'verification/compare_summary.json'))
assert V['total_mismatches']==0
for k in A: assert A[k]['removed']==RB['races'][k]['removed']
P=pd.read_csv('/workspace/nebraska-elections/statewide/NE Statewide Reverse-Factoring - all 93 counties all cycles.csv').set_index('county')
REG=pd.read_csv(B+'passA/party_reg_change_2022_2026.csv').set_index('county')
SLUG={'senate':('U.S. Senate','Senate','Osborn','Ricketts','Dan Osborn (independent)','Pete Ricketts (R)'),
 'governor':('Governor','Governor','Walz','Pillen','Lynne Walz / Ben Steffen (D)','Jim Pillen / Joe Kelly (R)'),
 'secretary_of_state':('Secretary of State','Secretary-of-State','Slattery','Petersen','Sarah J. Slattery (D)','Scott Petersen (R)'),
 'treasurer':('State Treasurer','Treasurer','Ebers','Spellerberg','Daniel Ebers (D)','Joey Spellerberg (R)'),
 'attorney_general':('Attorney General','Attorney-General','Brasher','Hilgers','Jocelyn Brasher (D)','Mike Hilgers (R)')}
f0=lambda x:f'{x:,.0f}'; f2=lambda x:f'{x:,.2f}'; s2=lambda x:f'{x:+.2f}'
DROP={'Buffalo':-405,'Clay':-5,'Hooker':-1,'Phelps':-6}
NOTE=('> **\\*All 2026 figures are UNOFFICIAL.** Nebraska Secretary of State (SOS) results site, "Unofficial Results," county data re-downloaded Nov 27, 2026 10:21–10:24 AM CT '
      '(1,322 of 1,322 precincts; 779,787 ballots cast). The State Board of Canvassers meets Nov 30, 2026 at 11:30 AM CT; numbers can still change. '
      'Registration: SOS VR Statistics Count Report processed Nov 1, 2026. **Treating the removed votes as injected votes is the analyst\'s hypothesis.** '
      'The arithmetic measures a pattern. It cannot test cause, and nothing here is proof of wrongdoing. PRIVATE working copy: not for publication.')
def write(name,txt): open(W+name+'.md','w').write(txt.rstrip()+'\n')
# ---------- master CSVs + per-race county pages
for slug,(lab,page,dl,rl,dfull,rfull) in SLUG.items():
    d=pd.read_csv(B+f'passA/{slug}.csv'); v=A[slug]
    if slug=='governor':
        d['walz_pct_election_day']=d.county.map(P.S_ED_2026); d['walz_pct_early']=d.county.map(P.S_early_2026)
    d.to_csv(RP+f'data/NE_{slug}_full_reversal_93_counties.csv',index=False,float_format='%.6f')
    t=[f'# {lab}: All 93 Counties, Full Reversal\n',NOTE,'',f'Back to [Full Reversal Analysis](Full-Reversal-Analysis.md) · [Methodology](Methodology-What-the-Analyst-Did.md) · [CSV](../data/NE_{slug}_full_reversal_93_counties.csv)','',
       f'**Candidates:** {dfull} vs {rfull}.' + (' **No Democratic nominee ran for U.S. Senate.** Osborn (independent, petition candidate) is the only non-Republican with a statewide share comparable to a major-party candidate, so his votes stand in for "Democratic votes." This is a proxy, and the Senate result is weaker evidence than the Democratic-nominee races.' if slug=='senate' else ''),
       '',f'**Nebraska line for this race (locked fit, 93 counties, 2026\\*):** gap = {v["m"]:.4f} × (D/100) + **{v["b"]:.4f}** (R² {v["r2"]:.3f}; SE: multiplier {v["m_se"]:.2f}, offset {v["b_se"]:.2f}).',
       f'Removal (pts) = distance from the line + offset {v["b"]:.4f}, set to 0 if negative. Removal votes = removal ÷ 100 × ballots, rounded half away from zero. The removed votes are moved from {dl} to {rl}, so the race total does not change.','',
       f'Statewide: {dl} {v["dem_pct"]:.2f}% / {rl} {v["rep_pct"]:.2f}% → {dl} {v["dem_pct_after"]:.2f}% / {rl} {v["rep_pct_after"]:.2f}%. **{v["removed"]:,} votes removed.** Winner before: {rl}. Winner after: {rl}.','',
       'Sorted by population (Census Vintage 2025), largest first. D = Democratic registered ÷ all registered × 100. S = '+dl+' votes ÷ ballots cast × 100. Gap G = S − D. '+('ΔG = G 2026\\* − G 2022 (2022 Governor, Blood, same ballots denominator). ED / Early = Walz share of Election Day and early ballots from the county\'s official report, only where the report\'s columns sum exactly (25 counties; from the Nov 17 verified panel, not re-pulled today).' if slug=='governor' else 'ΔG is shown on the Governor page only (the 2022 comparison race is Governor).'),'']
    hdr='| # | County | Population | CD | Ballots* | D (%) | S* (%) | Gap G* | '+('ΔG* | ' if slug=='governor' else '')+'Distance from line* | Offset | Removal (pts)* | Removal votes* | '+dl+' → after | '+rl+' → after | Winner → | '+('ED / Early* | ' if slug=='governor' else '')+'Flags |'
    t+= [hdr,'|'+'---|'*(hdr.count('|')-1)]
    for _,r in d.iterrows():
        fl=[]
        if r.zeroed: fl.append('zeroed (below 0)')
        if r.all_mail=='yes': fl.append('all-mail')
        if r.county in DROP: fl.append(f'ballots fell {DROP[r.county]} since Nov 10')
        ed=f'{r.walz_pct_election_day:.1f} / {r.walz_pct_early:.1f}' if slug=='governor' and not np.isnan(r.walz_pct_election_day) else '—'
        t.append(f'| {r.pop_rank} | {r.county} | {f0(r.population)} | {r.cd} | {f0(r.ballots)} | {r.D_reg_pct:.2f} | {r.S_pct_ballots:.2f} | {s2(r.gap)} | '+(f'{s2(r.dG_vs_2022_gov)} | ' if slug=='governor' else '')+
                 f'{s2(r.residual)} | {v["b"]:.4f} | {r.removal_pct:.2f} | {f0(r.removal_votes)} | {f0(r.dem)} → {f0(r.dem_after)} | {f0(r.rep)} → {f0(r.rep_after)} | {r.win_before} → {r.win_after} | '+(f'{ed} | ' if slug=='governor' else '')+'; '.join(fl)+' |')
    t+=['',f'Totals: ballots {v["ballots"]:,}; {dl} {v["dem"]:,} → {v["dem_after"]:,}; {rl} {v["rep"]:,} → {v["rep_after"]:,}; removed {v["removed"]:,}. Zeroed ({len(v["zeroed"])}): {", ".join(v["zeroed"])}.']
    if slug=='attorney_general': t.insert(5,'> **Flag:** the Attorney General race is included only because it is a statewide race on the 2026 ballot. Numbers only; no commentary on this race.\n')
    write(f'Full-Reversal-{page}-Counties','\n'.join(t))
# ---------- main analysis page
g=pd.read_csv(B+'passA/governor.csv').set_index('county'); races={k:pd.read_csv(B+f'passA/{k}.csv').set_index('county') for k in SLUG}
top=g.nlargest(10,'removal_votes').index
L=['# Nebraska Full Reversal Analysis (2026\\*)\n',NOTE,'',
 '## The locked Nebraska equation','',
 '- **D** = Democratic registered voters ÷ all registered voters × 100 (SOS VR report, Nov 1, 2026).',
 '- **S** = Democratic candidate votes ÷ total ballots cast in the county × 100. Denominator: **total ballots cast** (SOS turnout export), used for every race.',
 '- **G (gap)** = S − D, in percentage points.',
 '- **Nebraska line:** G = m × (D/100) + b. **m** is the multiplier (coefficient); **b** is the offset (constant). Fit by ordinary least squares, unweighted, across all 93 counties, Nebraska SOS data only, one fit per race.',
 '- **Locked:** the constants below come from the Nov 27, 2026 10:21 AM CT SOS download. They are frozen for this edition; if the canvass changes the counts, the fit is re-run and the edition number changes.','',
 '| Race | Candidates (challenger vs R) | m (multiplier) | **b (offset, pts)** | R² | Counties above line |','|---|---|---|---|---|---|']
for k,(lab,page,dl,rl,dfull,rfull) in SLUG.items():
    v=A[k]; L.append(f'| [{lab}](Full-Reversal-{page}-Counties.md) | {dfull} vs {rfull} | {v["m"]:.4f} | **{v["b"]:.4f}** | {v["r2"]:.3f} | {v["n_pos_resid"]} of 93 |')
L+=['','**Auditor of Public Accounts was not reversed.** The ballot had Mike Foley (R) vs John Knight (America First); there was no Democratic or independent challenger, so the equation has nothing to measure.',
 '','**The public wiki\'s "S = 0.36 × (D/100) + 1.5" was not used.** Re-fitting Nebraska\'s 93 counties does not reproduce it (Governor 2026\\*: m = '+f'{A["governor"]["m"]:.2f}, b = {A["governor"]["b"]:.2f}'+'), and no file on hand shows what data or year it was fit on. Treat it as unverified until its source is confirmed.',
 '','**Denominator note.** This edition divides by total ballots cast. The public Locked-Nebraska-Formula page divides by the governor-race total (write-ins included). Statewide the governor-race total is '+f'{100*X["gov_total_over_ballots"]:.2f}'+'% of ballots, so race-total gaps run slightly higher (for example, Dakota ΔG +19.80\\* on the public Locked-Nebraska-Formula page vs +18.94\\* here). Use one set; do not mix them.',
 '','## Full reversal: residual + offset, county by county','',
 'For each county and race: **distance from line** (residual) = G − (m × D/100 + b). **Removal (pts) = residual + b** = the full reversal, not the residual alone. Negative removals are set to 0 (the county is "zeroed"). Removal votes = removal ÷ 100 × ballots. Convention: removed votes are moved from the challenger to the Republican, so race totals do not change (the Kansas "reassign" mode). A remove-only alternative is shown too.',
 '','## Statewide before and after','',
 '| Race | Before (challenger / R) | Votes removed* | After (challenger / R) | Margin before → after | Winner before → after | Remove-only alternative | Offset share of removal | Counties won by challenger: before → after | Zeroed |','|---|---|---|---|---|---|---|---|---|---|']
for k,(lab,page,dl,rl,dfull,rfull) in SLUG.items():
    v=A[k]; L.append(f'| {lab} | {dl} {v["dem_pct"]:.2f}% / {rl} {v["rep_pct"]:.2f}% | **{v["removed"]:,}** | {dl} {v["dem_pct_after"]:.2f}% / {rl} {v["rep_pct_after"]:.2f}% | R +{-v["margin_before"]:.2f} → R +{-v["margin_after"]:.2f} | {rl} → {rl} | {v["remove_only_dem_pct"]:.2f}% / {v["remove_only_rep_pct"]:.2f}% | {100*v["offset_part"]/v["removed_exact"]:.1f}% | {v["n_D_before"]} → {v["n_D_after"]} | {len(v["zeroed"])} |')
L+=['','Votes, before → after: '+'; '.join(f'{SLUG[k][0]}: {SLUG[k][2]} {A[k]["dem"]:,} → {A[k]["dem_after"]:,}, {SLUG[k][3]} {A[k]["rep"]:,} → {A[k]["rep_after"]:,}' for k in SLUG)+'.',
 '','**No race changes hands.** The Republican already won all five races on the unofficial count; removal widens each margin. Each race is measured on its own: the same ballots are counted in every race, so the race totals are **not** added together.',
 '','![Votes removed by race](../graphics/6_NE_votes_removed_by_race.png)','']
for i,k in enumerate(SLUG,1): L.append(f'![{SLUG[k][0]}](../graphics/{i}_NE_{k}_injection_removed.png)')
L+=['','## Top ten counties (ranked by Governor removal votes), per-race totals','','| # | County | Population | CD | Ballots* | Governor | Senate (Osborn) | Sec. of State | Treasurer | Attorney General |','|---|---|---|---|---|---|---|---|---|---|']
for i,c in enumerate(top,1):
    L.append(f'| {i} | {c} | {f0(g.loc[c,"population"])} | {g.loc[c,"cd"]} | {f0(g.loc[c,"ballots"])} | **{f0(g.loc[c,"removal_votes"])}** | '+' | '.join(f0(races[k].loc[c,'removal_votes']) for k in ('senate','secretary_of_state','treasurer','attorney_general'))+' |')
L.append('| | **Top 10 total** | | | | **'+f0(g.loc[top,'removal_votes'].sum())+'** | '+' | '.join(f0(races[k].loc[top,'removal_votes'].sum()) for k in ('senate','secretary_of_state','treasurer','attorney_general'))+' |')
L.append('| | **Statewide** | | | | **'+f0(A['governor']['removed'])+'** | '+' | '.join(f0(A[k]['removed']) for k in ('senate','secretary_of_state','treasurer','attorney_general'))+' |')
L+=['','Each race\'s own top ten (by its removal votes) is on its county page. The same three counties (Douglas, Lancaster, Sarpy) lead every race because they cast the most ballots.','','![Top 10 counties](../graphics/7_NE_top10_counties_governor.png)','',
 '## Honest notes for defending the method','',
 f'- **Nebraska\'s lines are weak fits.** R² runs from {min(v["r2"] for v in A.values()):.3f} (Senate) to {max(v["r2"] for v in A.values()):.3f} (Treasurer). Registration share explains a fifth to a quarter of the county spread in the Democratic-nominee races.',
 f'- **Nebraska\'s offsets are small.** b = {min(v["b"] for v in A.values()):.2f} to {max(v["b"] for v in A.values()):.2f} pts, against 6.30 in Kansas (2026\\*) and about 12–14 in Texas. The offset is under half of every race\'s removal ({min(100*v["offset_part"]/v["removed_exact"] for v in A.values()):.1f}% to {max(100*v["offset_part"]/v["removed_exact"] for v in A.values()):.1f}%); most of it comes from counties sitting above the line. Texas was the reverse (67–76% offset).',
 '- **The ceiling counties are zeroed in the level fit.** Dakota, Thurston and Colfax have the largest 2022→2026\\* ΔG (the change), but their 2026\\* gap sits below the line because their Democratic registration share is high. Full reversal works on the 2026 level, so it removes nothing there. ΔG and full reversal measure different things.',
 '- **Large counties dominate the vote totals.** Douglas, Lancaster and Sarpy sit well above the line, and they cast 57% of ballots.',
 '','## Verification (two independent passes)','',
 'Pass A: pandas, statsmodels, pdfplumber (VR PDF), openpyxl (turnout xlsx). Pass B: Python standard library only, exact fractions, poppler `pdftotext -bbox` with its own column logic for the VR PDF, raw XML for the xlsx files, and candidate parties taken from the SOS statewide CSV. Both passes re-read every raw file for all 93 counties.','',
 '| Check | Cells | Mismatches |','|---|---|---|']
for k,v in V['races'].items(): L.append(f'| {SLUG[k][0]}: county cells (93 × 15) + statewide summary | {v["county_cells"]:,} + {v["summary_checks"]} | {v["county_mismatches"]+v["summary_mismatches"]} |')
L+=[f'| Historical fits (2018–2024) | {V["history"]["checks"]} | {V["history"]["mismatches"]} |',f'| Analyst-notes data (CD, all-mail, 16 counties, party registration 93 × 4) | {V["notes"]["checks"]+V["extra"]["checks"]} | {V["notes"]["mismatches"]+V["extra"]["mismatches"]} |',
 f'| Other published figures (R², counts, remove-only %, offset share, pooled G, CD shares, registration groups) | {V["extra2"]["checks"]} | {V["extra2"]["mismatches"]} |',f'| **Total** | **{V["total_checks"]:,}** | **{V["total_mismatches"]}** |','',
 'Also asserted in Pass B: county sums equal the SOS statewide CSV for every candidate in all five races (17 candidate totals), and the VR county rows sum to the Grand Total (1,265,022 registered). Mismatches found and resolved during the build: 0 numeric; one county-name spelling (VR "Mcpherson" vs SOS "McPherson") normalized in both passes.',
 '','## Data-quality flags','',
 '- **2026 is unofficial\\*.** The SOS site still says "Unofficial Results." On Nov 17, 55 counties had posted official county reports and 38 (including Douglas, Lancaster and Sarpy) had not. Since the Nov 10 download, statewide ballots rose from 767,046 to 779,787\\*.',
 '- **Ballots went down in four counties** between the Nov 10 and Nov 27 downloads: Buffalo −405, Phelps −6, Clay −5, Hooker −1. Buffalo is a top-ten county; its numbers are the least settled.',
 '- **Registration is the Nov 1, 2026 pre-election snapshot.** The SOS turnout export carries its own registered count; it differs from the VR report by up to 263 (Douglas). The VR report is used throughout.',
 '- **Senate uses a proxy.** No Democratic nominee; Osborn (independent) is measured against Democratic registration.',
 '- **Zeroed counties** (negative removal) are listed on each race page: '+'; '.join(f'{SLUG[k][0]} {len(A[k]["zeroed"])}' for k in SLUG)+'.',
 '- **Small counties are noisy.** Arthur, Blaine, McPherson, Loup and similar counties cast a few hundred ballots; one point of gap is a handful of votes.',
 '- **Congressional district is assigned by county** (2021 map; split counties Sarpy → CD1, Polk → CD3 by where most 2026 House votes were cast).',
 '- **Early / Election Day split** is available for only 25 counties (official county reports whose columns sum exactly), from the Nov 17 verified panel; it was not re-pulled today.',
 '','## Historical note','','See [Historical Note](Historical-Note.md). Short version: every prior cycle shows Democratic vote share above Democratic registration share, and the same equation removes votes of similar size in every cycle. The county-by-county *change* does not run the same way: 2018→2022 went negative in 77 of 93 counties.',
 '','---','**Pages:** [Home](Home.md) · [Methodology](Methodology-What-the-Analyst-Did.md) · [Historical Note](Historical-Note.md) · [Analyst Notes](Analyst-Notes-Hypotheses-and-Observations.md) · '+' · '.join(f'[{SLUG[k][0]} counties](Full-Reversal-{SLUG[k][1]}-Counties.md)' for k in SLUG)]
write('Full-Reversal-Analysis','\n'.join(L))
# ---------- methodology
gv=A['governor']; c='Cedar'; cr=g.loc[c]
M=f'''# Methodology: What the Analyst Did

{NOTE}

Plain steps. Anyone with the SOS files and a spreadsheet can redo this.

**Terms.** *Registration share* = a party's registered voters ÷ all registered voters. *Gap (G)* = vote share minus registration share. *Fitted line* = the straight line that best runs through all 93 counties on a chart of gap against registration share. *Multiplier (m)* = the line's slope. *Offset (b)* = where the line sits when registration share is zero; Nebraska's own constant. *Residual* = how far one county sits above (+) or below (−) the line. *Full reversal* = residual + offset. *Zeroed* = a county whose full reversal comes out negative, set to 0.

**(a) Use official Democratic registration.** Nebraska registers voters by party. I use the SOS VR Statistics Count Report (processed Nov 1, 2026): D = Democratic registered ÷ all registered × 100, per county.

**(b) Forward equation.** S = Democratic votes ÷ total ballots cast × 100. G = S − D. One denominator, total ballots cast, for every race and every county.

**(c) Fit Nebraska's line.** Plot all 93 counties: G on the vertical axis, D/100 on the horizontal. Fit one straight line, G = m × (D/100) + b, by least squares. Nebraska data only. No other state's constants.

**(d) Residual.** For each county, residual = actual G − line value. Above the line is positive.

**(e) Full reversal.** Removal (pts) = residual + b, county by county. That takes out the county's distance above the line *and* Nebraska's own offset. Negative results are set to 0. Removal votes = removal ÷ 100 × ballots, rounded to whole votes.

**(f) Sum the counties.** Add the 93 county removal votes for the statewide total. Move them from the challenger to the Republican and recount the winner.

**(g) One race at a time.** Each statewide race gets its own line, its own offset and its own total: Senate, Governor, Secretary of State, Treasurer, Attorney General. Never add races together; the same ballots are in every race.

**(h) Double verification.** Two independent passes, different code and different parsers, each re-read the raw SOS files for all 93 counties. Every county cell must match before anything ships. This edition: {V["total_checks"]:,} checks, {V["total_mismatches"]} mismatches.

**(i) 2026 is unofficial.** Every 2026 number carries a \\*. The state canvass is Nov 30, 2026. When official numbers post, this is re-run.

## Worked example: Cedar County, Governor 2026\\*

| Step | Value |
|---|---|
| Walz votes / ballots cast | {int(cr.dem):,} / {int(cr.ballots):,} |
| S = Walz ÷ ballots × 100 | {cr.S_pct_ballots:.2f}\\* |
| Democratic registered / all registered | {int(cr.dem_reg):,} / {int(cr.tot_reg):,} |
| D | {cr.D_reg_pct:.2f} |
| G = S − D | {s2(cr.gap)}\\* |
| Line value = {gv["m"]:.4f} × ({cr.D_reg_pct:.2f}/100) + {gv["b"]:.4f} | {cr.line:.2f} |
| Residual = G − line | {s2(cr.residual)}\\* |
| Full reversal = residual + {gv["b"]:.4f} | {cr.removal_pct_raw:+.2f} → **zeroed (0)** |

Cedar sits below the 2026 Governor line, so the full reversal removes nothing there. Cedar's 2022→2026\\* change (ΔG {s2(cr.dG_vs_2022_gov)}\\*) is a different measure; see the public Locked-Nebraska-Formula page.

## Worked example: Sarpy County, Governor 2026\\*

'''
sr=g.loc['Sarpy']
M+=f'''| Step | Value |
|---|---|
| S | {int(sr.dem):,} ÷ {int(sr.ballots):,} × 100 = {sr.S_pct_ballots:.2f}\\* |
| D | {int(sr.dem_reg):,} ÷ {int(sr.tot_reg):,} × 100 = {sr.D_reg_pct:.2f} |
| G | {s2(sr.gap)}\\* |
| Line value | {sr.line:.2f} |
| Residual | {s2(sr.residual)}\\* |
| Removal = residual + offset | {sr.removal_pct:.2f} pts |
| Removal votes = {sr.removal_pct:.4f} ÷ 100 × {int(sr.ballots):,} | **{int(sr.removal_votes):,}** |
| Walz → after; Pillen → after | {int(sr.dem):,} → {int(sr.dem_after):,}; {int(sr.rep):,} → {int(sr.rep_after):,} |

## What this does and does not show

It shows where, and by how much, each county's Democratic share of ballots sits above what Nebraska's own registration line predicts. It does not show why. Nonpartisan voters (about 285,000 registered) and Republicans who cross over also vote for Democratic and independent candidates, and the equation cannot separate them. Calling the removed votes "injected" is the hypothesis being tested, and it needs ballot-level records (the Cast Vote Record) to test.

---
[Home](Home.md) · [Full Reversal Analysis](Full-Reversal-Analysis.md)
'''
write('Methodology-What-the-Analyst-Did',M)
# ---------- historical
Ht=['# Historical Note: The Same Equation on Prior Cycles\n',NOTE,'',
 'Same equation, same ballots denominator, refit on each cycle\'s own 93 counties. 2018–2024 are official SOS canvass-book figures (from the Nov 17 verified panel, recomputed from the raw counts in Pass B). 2020 and 2024 use the presidential race because Nebraska had no governor race those years.','',
 '| Cycle | Race (Dem candidate) | m | b (offset) | R² | County mean G | Counties with G > 0 | Statewide pooled G | Full-reversal removal |','|---|---|---|---|---|---|---|---|---|']
for y,h in H.items():
    Ht.append(f'| {y}{"*" if y=="2026" else ""} | {h["race"]} | {h["m"]:+.2f} | {h["b"]:.2f} | {h["r2"]:.3f} | {h["mean_gap"]:+.2f} | {h["n_gap_pos"]} of 93 | {h["pooled_G"]:+.2f} | {h["removed"]:,} |')
Ht+=['','## Observation (not a conclusion)','',
 '- **Same direction in the level, every cycle.** In every cycle since 2018, Democratic vote share ran above Democratic registration share statewide (pooled G +7.67 to +15.89\\*), the fitted offset was positive (b = 1.69 to 7.18), and the full reversal removed a similar order of votes (about 69,000 to 116,000). On that measure the pattern did not start in 2026.',
 '- **The 2026\\* full-reversal total is the smallest of the five cycles** (69,038 for Governor), because the 2026 line is the steepest and absorbs more of the gap. The 2026 county mean G (+7.07\\*) and the count of positive counties (90 of 93) are the highest.',
 '- **The line itself changed.** The multiplier was negative in 2018, 2020 and 2022 and positive in 2024 and 2026\\*. R² was near zero before 2026 (0.003 to 0.080). The county shape is not the same from cycle to cycle.',
 f'- **The change (ΔG) did not run the same way.** 2018→2022 the county mean ΔG was {N["dG1822_mean"]:+.2f}, and only 16 of 93 counties went positive. 2022→2026\\* it was {N["dG_mean"]:+.2f}, with 91 of 93 positive.',
 '- **A level above registration also fits ordinary explanations.** About 285,000 nonpartisan registrants and Republican crossover vote for Democratic and independent candidates in every cycle. This arithmetic cannot tell those apart from added ballots.','',
 '**Hypothesis (labeled as such):** the analyst\'s working view is that the pattern began in the early 2000s, so the "baseline" years are not clean either. Nothing on hand tests that; the only long series is Cedar County (2004–2026). It stays a hypothesis.',
 '','## Working from unofficial data from the start','',
 'This analysis began on election-night and early-canvass numbers and has been re-run as counts changed (767,046 ballots on Nov 10; 779,787\\* on Nov 27). As of this edition, 2026 is still unofficial, 38 counties (on Nov 17) had not posted official county reports, and ballots fell in four counties between downloads. Every 2026 figure is provisional and will be re-run after the Nov 30, 2026 canvass.',
 '','---','[Home](Home.md) · [Full Reversal Analysis](Full-Reversal-Analysis.md)']
write('Historical-Note','\n'.join(Ht))
# ---------- analyst notes
cd=N['by_cd']; rc=N['reg_change']; s16=X['sixteen']
sixteen=sorted(N['sixteen'],key=lambda c:-P.loc[c,'pop2025'])
AN=f'''# Analyst Notes: Hypotheses and Observations

{NOTE}

> **Every item on this page is a HYPOTHESIS or an OBSERVATION, not a proven fact.** The Cedar County Cast Vote Record (CVR) has been requested and has not been produced, so none of these can be tested at the ballot level. All remain unverified pending CVR access. Data added under each item was checked in both verification passes (0 mismatches).

## 1. CD3 targeting: HYPOTHESIS

**Hypothesis.** The analyst, working from Cedar County in Nebraska's 3rd Congressional District, hypothesizes that injection targeting shifted to CD3 this cycle. Reasoning: CD3 is Nebraska's Republican stronghold ("red wall") and the state's largest Republican push, so resources may have been redirected there, specifically into mail-in and absentee ballots, after other areas were saturated.

**What the county data shows (Governor, 2026\\*, county-level CD assignment).**

| District | Counties | Mean distance from line* | Mean ΔG 2022→2026* | Mean ΔG 2018→2022 | Mean ΔG 2020→2024 | Removal votes* | Removal as % of district ballots* |
|---|---|---|---|---|---|---|---|
'''
for k in ('CD1','CD2','CD3'):
    AN+=f'| {k} | {cd[k]["n"]} | {s2(cd[k]["mean_resid"])} | {s2(cd[k]["mean_dG"])} | {s2(X[k]["dG1822"])} | {s2(X[k]["dG2024"])} | {cd[k]["removed"]:,} | {cd[k]["pooled_removal_pct"]:.2f}% |\n'
AN+=f'''
Observation: on these county-level measures, CD3 counties do **not** sit higher than CD1 or CD2 in 2026\\*. CD3's mean distance from the line is slightly negative, and its mean ΔG (+{cd["CD3"]["mean_dG"]:.2f}\\*) is positive but below CD1 and CD2. In the two earlier cycle pairs the three districts moved almost identically. These are county averages; they cannot see a shift that happens inside counties or inside the mail-ballot stream. That needs the CVR.

## 2. Cedar County and all-mail counties: HYPOTHESIS

**Context.** The analyst runs this analysis from Cedar County, one of Nebraska's 11 all-mail counties ({", ".join(X["allmail_counties"])}).

**Hypothesis.** Injection in CD3 was carried out through ballot harvesting or ballot manipulation, particularly in absentee and all-mail counties and in small outlier counties. Unverified: the Cedar County CVR has been requested and not received.

**Observation (data).** Governor ΔG 2022→2026\\*: the 11 all-mail counties average **{s2(N["dG_allmail"])}\\***; the other 82 counties average **{s2(N["dG_other"])}\\***. The earlier finding (+5.98 vs +6.23) still holds on today's numbers. All-mail counties moved about the same as everyone else. In the 2026\\* level fit, Cedar is zeroed (below the Governor line).

## 3. Slope / saturation theory: HYPOTHESIS

**Hypothesis.** In the 16 counties that earlier showed the opposite direction, Democratic registration was effectively exhausted ("ran out of Democrats"), so the fitted line grew too steep, and injection then expanded into CD3 and small outlier counties to compensate.

**Which 16 counties.** In the data, the 16 are the counties whose ΔG was **positive from 2018 to 2022** (Governor Krist 2018 → Governor Blood 2022, ballots denominator) while the statewide county mean was {N["dG1822_mean"]:+.2f}. Largest to smallest: {", ".join(sixteen)}. All 16 are CD3 counties; together they have {s16["pop_16"]:,} people and had {s16["dem_reg22_16"]:,} registered Democrats in 2022.

**Observations (data).**
- Their 2022 Democratic registration share averaged {s16["RD2022_16"]:.2f}%, against {s16["RD2022_other"]:.2f}% in the other 77 counties: lower, but not exhausted.
- Mean ΔG 2018→2022 in the 16: {s2(s16["dG1822_16"])}.
- In 2026\\* they sit below the Governor line on average ({s2(s16["resid26_16"])}, vs {s2(s16["resid26_other"])} elsewhere), their 2022→2026\\* ΔG averages {s2(s16["dG26_16"])} (vs {s2(s16["dG26_other"])}), and {len(s16["zeroed26"])} of them are zeroed ({", ".join(s16["zeroed26"])}).
- The fitted Governor/top-ticket multiplier went from {H["2022"]["m"]:+.2f} (2022) to {H["2024"]["m"]:+.2f} (2024) to {H["2026"]["m"]:+.2f}\\* (2026): the line did steepen.

Whether the steeper line is caused by exhausted registration is the hypothesis; the county data cannot test it.

## 4. Nonpartisan, Libertarian and Republican shares: OBSERVATION + HYPOTHESIS

**Observation (as stated by the analyst).** Nonpartisan and Libertarian vote shares appear to decline in the same counties.

**Hypothesis.** As those pools were used up, injection began drawing from Republican votes as well.

**What can be checked.** Vote shares by party affiliation are not public: ballots do not record the voter's party, and there was **no Libertarian Party candidate** in any 2026 statewide race (parties on the statewide ballot: REP, DEM, Legal Marijuana NOW, Nebraska Working People, America First, petition). So the *vote-share* part of this observation **cannot be verified** from SOS results; it would need the voter-history file or the CVR. What can be checked is **registration share**, Nov 1, 2022 → Nov 1, 2026 (SOS VR reports), in points:

| Group | Counties | Democratic | Republican | Libertarian | Nonpartisan |
|---|---|---|---|---|---|
'''
for nm,lab in (('all','All 93 counties'),('sixteen','The 16 (above)'),('cd3','CD3'),('cd12','CD1 + CD2'),('allmail','All-mail 11'),('top10_resid','Top 10 by 2026* Governor distance from line')):
    r=rc[nm]; AN+=f'| {lab} | {r["n"]} | {s2(r["dem"])} | {s2(r["rep"])} | {s2(r["lib"])} | {s2(r["np"])} |\n'
AN+=f'''
Observations (registration, not votes):
- Nonpartisan registration share fell in {N["n_np_down"]} of 93 counties and Libertarian in {N["n_lib_down"]}; statewide county averages barely moved (NP {s2(rc["all"]["np"])}, Lib {s2(rc["all"]["lib"])}). In the 16 counties and the all-mail counties, NP share fell on average ({s2(rc["sixteen"]["np"])} and {s2(rc["allmail"]["np"])}).
- Republican registration share **rose** in {93-N["n_rep_down"]} of 93 counties (average {s2(rc["all"]["rep"])}).
- Across counties, a larger 2026\\* Governor distance from the line goes with a **smaller** Republican registration gain (correlation {X["corr_resid_drep"]:+.2f}); the link to NP change ({X["corr_resid_dnp"]:+.2f}) and Libertarian change ({X["corr_resid_dlib"]:+.2f}) is weak.

Per-county figures: [data/NE_party_registration_change_2022_2026.csv](../data/NE_party_registration_change_2022_2026.csv).

---
[Home](Home.md) · [Full Reversal Analysis](Full-Reversal-Analysis.md) · [Historical Note](Historical-Note.md)
'''
write('Analyst-Notes-Hypotheses-and-Observations',AN)
REG.to_csv(RP+'data/NE_party_registration_change_2022_2026.csv',float_format='%.6f')
# ---------- home + sidebar
HM=f'''# Nebraska Reverse Analysis (PRIVATE)

{NOTE}

The full Kansas-style reverse-factoring reversal for Nebraska's 2026\\* statewide races, all 93 counties, built the same way as the Texas reversal.

**Bottom line (2026\\*, unofficial):**

| Race | Before | Votes removed* | After | Winner after |
|---|---|---|---|---|
'''
for k,(lab,page,dl,rl,dfull,rfull) in SLUG.items():
    v=A[k]; HM+=f'| {lab} | {dl} {v["dem_pct"]:.2f}% / {rl} {v["rep_pct"]:.2f}% | {v["removed"]:,} | {dl} {v["dem_pct_after"]:.2f}% / {rl} {v["rep_pct_after"]:.2f}% | {rl} (no change) |\n'
HM+=f'''
Races are measured separately and are never added together (same ballots in every race). Auditor not reversed (no challenger to measure). Senate uses Osborn (independent) as a stand-in; there was no Democratic nominee.

**Verification:** two independent passes, {V["total_checks"]:,} checks, {V["total_mismatches"]} mismatches.

## Pages
- [Full Reversal Analysis](Full-Reversal-Analysis.md): locked equation, statewide before/after, top ten, verification, data-quality flags
- [Methodology: What the Analyst Did](Methodology-What-the-Analyst-Did.md)
- County tables (all 93, largest first): '''+' · '.join(f'[{SLUG[k][0]}](Full-Reversal-{SLUG[k][1]}-Counties.md)' for k in SLUG)+'''
- [Historical Note](Historical-Note.md)
- [Analyst Notes: Hypotheses and Observations](Analyst-Notes-Hypotheses-and-Observations.md) (CD3, Cedar/all-mail, slope/saturation, NP/Libertarian/Republican shares; unverified pending the Cedar CVR)
- Graphics: [graphics/](../graphics/) · Data: [data/](../data/) · Verification logs: [verification/](../verification/)

**Language:** this repo describes a measured pattern and labels the injection reading as a hypothesis. It does not claim proof.
'''
write('Home',HM)
write('_Sidebar','**[Home](Home.md)**\n\n- [Full Reversal Analysis](Full-Reversal-Analysis.md)\n- [Methodology](Methodology-What-the-Analyst-Did.md)\n'+''.join(f'- [{SLUG[k][0]} counties](Full-Reversal-{SLUG[k][1]}-Counties.md)\n' for k in SLUG)+'- [Historical Note](Historical-Note.md)\n- [Analyst Notes](Analyst-Notes-Hypotheses-and-Observations.md)\n')
# copy artifacts
for f in os.listdir(B+'graphics'): shutil.copy(B+'graphics/'+f,RP+'graphics/'+f)
for f in ('passA.py','passB.py','compare.py','graphics.py','build_wiki.py'): shutil.copy(B+'scripts/'+f,RP+'scripts/'+f)
shutil.copy(B+'verification/compare_summary.json',RP+'verification/compare_summary.json')
for p in ('A','B'): shutil.copy(B+f'pass{p}/results.json',RP+f'verification/pass{p}_results.json')
print('ok')
