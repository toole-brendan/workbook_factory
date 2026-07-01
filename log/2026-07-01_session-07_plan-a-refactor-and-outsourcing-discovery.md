# Session 07 — Plan A procurement-timing refactor + new-construction outsourcing discovery

**Date:** 2026-07-01
**Branch:** `promote-sam-findings-round1` (continues from sessions 05–06)
**Scope:** (a) Implement **Plan A** (`ddg/plan_a_procurement_timing_refactor.md`) — retire the
whole-program lifecycle-staging layer, keep **Procurement Timing** as the coverage anchor, and
replace the misleading program-wide stage exhibit with a scoped **DDG 125 & 128 Full-Span**
drill-down. (b) Use the surviving Procurement Timing dimension to hunt for grand-block-style
**outsourcing during new construction**, then corroborate against the SAM entity + Contract Awards
APIs.
**Outcome:** ✅ Refactor implemented and verified — **38 → 33 tabs**, 0 recalc error cells, all
Checks OK (incl. a new partition check), TAM untouched. Analysis: pinned genuine new-construction
**structural outsourcing ≈ $42M**, caught and corrected a **$9.5M CAPEX misclassification**, and
confirmed via the SAM Contract Awards API that the outsourcing yards hold **no unscoped DDG
new-construction primes** — i.e. the subaward corpus is complete for their DDG new-con work.

---

## 1. Plan A — the code change (factory-accurate, corrected against the plan)

Net **38 → 33 tabs** (delete 6 rendered lifecycle tabs + 1 unrendered guide module, add 1 drill-down).
The plan's headline "38 → 32" was off by one; see the corrections below.

**Deleted (7 modules):** `ddg_cd_lifecycle_candidates.py`, `ddg_cd_lifecycle_rollup.py`,
`ddg_cd_lifecycle_coverage.py`, `ddg_archetype_lifecycle.py`, `ddg_vendor_hull_lifecycle.py`,
`ddg_hull_lifecycle_stage.py` (the 6 rendered lifecycle tabs, incl. the "87% long-lead" culprit),
plus `lifecycle_methodology.py` (a `SheetEntry` never registered in `SHEETS` → **not a rendered
tab**, so its deletion changes 0 tabs — that's the off-by-one).

**Transaction leaf slimmed 77 → 72:** physically stripped the 5 frozen lifecycle columns
(`Lifecycle Stage / …Basis / Date Source Confidence / Narrowing Result / Lifecycle Confidence`,
CSV cols 60–64) from `ddg_subaward_transactions.csv` (5007 rows preserved, CRLF round-trip). There
is **no local tagger** to retire — those columns were ported in frozen from upstream
`ooxml_build_pipelines_light`; the factory just carried them. Width assert 77→72; docstring trimmed.

**Guard retired (the real build-breaker):** removed `assert_lifecycle_columns_consistent` from
`kit/integrity.py` **and** its call at `build_workbook.py:43`. The plan named a non-existent
`assert_lifecycle_labels_known` (an upstream symbol); following it literally would have hard-failed
the build (the guard `.index("Lifecycle Stage")`s the dropped column and `load_table`s the deleted
rollup/candidates CSVs).

**Referencing sheets fixed** so nothing throws `#REF!`/KeyError:
- `checks.py` — dropped 3 imports + 4 range vars + 3 lifecycle reconciliations + the C/D-rollup
  row-count check; **added** "Full-span drill-down stages partition each hull's total".
- `executive_summary.py` §6 — removed the two C/D narrowing/lifecycle-confidence rows; **added** a
  rendered "Advance / long-lead share" row (= 63.3%) so the load-bearing whole-program figure stays
  visible.
- `market_bridge.py` — removed the two §2 ladder rows + edited §3 "Family-level C/D" good-for text.
- `hull_mapping_methodology.py` — removed the `TAB_LIFECYCLE_METHOD` import (ImportError risk once
  the const is pruned) and rewrote §6 to preserve the load-bearing negative (timing-narrowing tested
  on the C/D bulk rarely resolves below 4+ candidates → no per-hull $ allocated). *(This module is
  unrendered, so the visible home for the negative is the Exec Summary advance-share row + the
  Procurement Timing intro.)*
- `kit/cuts.py`, `kit/tabs.py`, `sheets/__init__.py`, `lib.py` — pruned constants / registry / CSV
  aliases; deleted the 2 orphaned lifecycle CSVs.
- **Stale-text sweep:** fixed 4 lingering "lifecycle rollup" references (2 rendered:
  `executive_summary` §6, `market_bridge` §3; 2 docstrings: `ddg_hull_master`, `ddg_vendor_hull`).

**New: `ddg_full_span_drilldown.py` → "DDG 125 & 128 Full-Span"** (model group). Built in the exact
`make_flat_sheet(table=…)` idiom of the sheet it replaces (`ddg_hull_lifecycle_stage`), so it needs
no CSV and no `lib.py` alias. **No stage column reintroduced** — each stage cell is a date-window
`SUMIFS` over the transaction leaf keyed on `Assigned Hull` + a band bounded by **that hull's own**
Start Fabrication / Launch / Delivery, pulled live from Hull Master. Milestone "Mon YYYY" text →
serial via a **locale-proof** `DATE(RIGHT(x,4), MATCH(LEFT(x,3), {"Jan";…;"Dec"}, 0), 1)` (chosen
over `DATEVALUE`, which is fussy in LibreOffice headless). Bands + an Undated residual partition each
hull's total; a Checks reconciliation asserts it. Tab name uses **`&`** not `/` (Excel forbids `/`).

**Verified drill-down values (FY2026$):** DDG 125 = **$27.26M** (Long-lead 10.06 / Constr 2.42 /
Outfit 4.19 / Post 10.59 / Undated 0), 157 recs; DDG 128 = **$17.56M** (7.41 / 0.59 / 9.55 / 0 / 0),
155 recs. Both partitions reconcile exactly. DDG 125's $27.3M matches the plan's FY2026$ expectation;
DDG 128's $17.6M matches the shipped Hull-Lifecycle figure (not the $21.2M nominal coverage memo).

**Skipped (deliberately):** the optional `Earliest Keel → Earliest Fab Start` rename. The PIID-map
`Earliest Keel` = `min(Start Fabrication)` over the family, and the milestones are **MIRS-sourced**
(S&P Global / IHS Sea-web) — a defensible label. Verified the frozen `Earliest Keel` still equals the
live `min(Start Fabrication)` for both hulls (DDG 125 = Oct 2015 / DDG 117; DDG 128 = Jan 2021 /
DDG 129), so keeping the label introduces **no** numeric/staleness discrepancy.

## 2. Methodology clarifications (for the deck / next author)

- **Procurement Timing is a coverage fix**: it reframes the unanswerable "which hull?" (exact-hull
  caps ~35%) into "when in the buy cycle?" (a family-schedule property every row has → ~100%
  coverage, grain-safe). The load-bearing figure: **~63% of observed SAM is advance/LLTM** (before
  the block's earliest keel).
- **63% is a FLOOR, not a point.** The "before the *earliest* keel" test misses advance material for
  **later hulls in the block** (a hull-6 gear bought mid-build reads In-build), so it undercounts
  advance — a one-directional, conservative bias (defensible as "at least 63%").
- **own-keel vs group-keel seam:** the drill-down uses each hull's *own* keel; Procurement Timing
  uses the *family envelope*. For the same DDG 125 row these differ by ~4 yr (own Nov 2019 vs family
  Oct 2015), so the two sheets classify the same dollar differently **by design** — do not reconcile
  drill-down "Long-lead" to the program 63%.
- **A schedule-state weight to recover the downstream LLTM is NOT sound** as a point estimate: the
  equal-spread-across-active-hulls assumption fails hardest for the lumpy per-hull LLTM lots it's
  meant to capture, the bias is systematic (LLTM is bought early by definition), and it's
  unfalsifiable on its own data. Material-vs-construction is answered by **nature (vendor
  archetype/SWBS), not timing** — that's Plan B.

## 3. New-construction outsourcing discovery (the analytical thread)

- **Grand blocks classify as In-build (verified in the workbook):** Gulf Copper / BAE Jacksonville /
  Eastern all read **In-build window**, 0% Advance — they're 2025 buys on the FY18-22 MYP (earliest
  keel Jan 2021). Their **SWBS = U00 "No SWBS Evidence"** — they carry no HII work-item code and are
  coded by internal **PWBS block zones** in the description (`D11-D52`, `GB A16/B13/B15/B43`,
  `C15GB`). **SWBS is blind to grand blocks**; the real signature is `In-build + U00 + "UNIT
  OUTSOURCING"/block-code tokens`.
- **Discovery method = phase-anomaly hunting**: for each timing phase write the expected content,
  surface the violators. The In-build bucket's violator is *outsourced construction*. The clean net
  is **`In-build ∩ construction-nature`**.
- **Vendor-nature scan** (name patterns + curated US-yard list + **cached SAM NAICS**) lifted the
  identifiable figure from **~$31M** (description-token only, high-precision/low-recall — your
  "undercount" point, ~2×) to **~$70M gross** across shipyards+fabricators, cleanly separated from
  the $362M "U00 × In-build" material haystack.
- **NEW structural-outsourcing candidates** (beyond the 3 known grand-block yards):
  **Southcoast Welding** (Chula Vista CA, ~$8.7M In-build — hatches/scuttles/structural doors,
  SWBS-100, dual-sourced with **Pacific Ship Repair** San Diego CA ~$4.6M); **ArtCraft Fabricators**
  (Portsmouth VA, ~$6.2M, "SCHIEB PROJECT", opaque). A West-Coast structural-closure pipeline (~$13M)
  is a distinct story from the Gulf grand blocks.
- **CAPEX correction (caught a false positive):** `"CAPEX: SOW FOR [vendor]"` is a systematic
  **~$106M supplier-*capacity* investment program** (NAVSEA HQ funded, on the construction MYPs)
  across 34 suppliers (York A/C, Marmon, Espey, Buffalo Pump, Milwaukee Valve, …) — **industrial-base
  capex, not outsourcing**. **SteelFab's $9.5M was a false positive** (SAM NAICS 332312 Fabricated
  Structural Metal, but the row is capex, not a fab SOW) → removed from the outsourcing tally.
- **Bottom line — genuine new-construction structural outsourcing ≈ $42M**: grand blocks $30.7M +
  Southcoast (ex-capex door) ~$6.6M + Pacific Ship Repair $4.6M; **+ ArtCraft $6.2M unresolved** →
  $42–48M. Still a floor (opaque/generically-named fabricators escape).
- **New non-structural token:** Boland Marine — "DDG131/133 MACHINERY OUTSOURCING" (a separate
  outsourcing category to chase).

## 4. Corpus completeness — SAM Contract Awards API (#3)

- The whole $3,175M observed SAM rides on **7 construction PIIDs** (the FY13-17 / FY18-22 / FY23-27
  MYP block-buys); `n/a` timing = $0 and 0 orphan PIIDs → **internally complete for new-construction
  subawards**.
- **Checked whether the outsourcing yards hold their own unscoped DDG new-construction primes — they
  do not.** Their independent Navy footprints are entirely ship **repair/maintenance** (RMCs, MSC,
  naval-shipyard IMFs) or unrelated: **Eastern = $1.06B Coast Guard OPC prime**; BAE Jax = $135M SE
  RMC repair; Southcoast = $17.5M SW RMC; Pacific Ship Repair = Puget Sound/SW RMC; **SteelFab &
  Metals USA have no federal prime footprint at all** (pure subs). Gulf Copper's only shipbuilding-
  office PIIDs are 1990s "Conversion & Repair," not new construction.
- **Implication:** DDG new-construction outsourcing flows HII/BIW → yard as a **subaward**, never
  Navy → yard as a separate prime — so the subaward lens is the right and complete instrument, and
  the ~$42M figure needs no prime-side addition. (Larger gaps — GFE combat systems, mod/repair,
  sub-tier — are real but out of scope for *new-construction* outsourcing.)

## Verification

- `python3 build_ddg.py` → **33 sheets** (was 38), no assert failures.
- LibreOffice headless recalc → **0** `t="e"` error cells; **all Checks OK** incl. master,
  "Procurement timing phases reconcile", and the new "Full-span drill-down stages partition each
  hull's total".
- TAM untouched (no TAM input CSV edited).

## Files changed (branch `promote-sam-findings-round1`, uncommitted)

- **Modified:** `build_workbook.py`, `lib.py`, `sheets/__init__.py`, `checks.py`,
  `ddg_subaward_transactions.py`, `ddg_hull_master.py`, `ddg_vendor_hull.py`, `executive_summary.py`,
  `hull_mapping_methodology.py`, `market_bridge.py`, `kit/cuts.py`, `kit/integrity.py`, `kit/tabs.py`,
  `data/…/transactions/ddg_subaward_transactions.csv`
- **Deleted:** the 6 lifecycle sheet modules + `lifecycle_methodology.py`; the 2 orphaned lifecycle
  CSVs
- **New:** `sheets/ddg_full_span_drilldown.py`; `plan_a_…md` / `plan_b_…md` (design docs)

## Analysis tooling / data (external — NOT read by the build)

- Cached SAM entity enrichment (authoritative NAICS/business-type per UEI):
  `ooxml_build_pipelines_light/projects/distributed_shipbuilding/sam/sam_awards_data/sam_entity_enrichment/{uei_naics_long.csv, unique_uei_sam_enrichment.csv}` — resolves vendor nature with **no API call**.
- **SAM Contract Awards API** `https://api.sam.gov/contract-awards/v1/search` (key in
  `ooxml_build_pipelines_light/.env` as `SAM_API_KEY`; ~20 requests, well under the 1,000/day quota).
  Gotchas: **max `limit=100`** (1000 → 400), `totalRecords` may be a string, filter by
  `awardeeUniqueEntityId` (the workhorse); helpers in `.../army/research/contracts/scripts/_common.py`
  (IPv4 monkeypatch, key reader, 429→halt). See `ooxml_build_pipelines_light/Federal_Awards_API_HowTo.md`.

## Open items / follow-ups

- **Plan B — material-vs-construction nature tagging** (`ddg/plan_b_material_vs_construction_tagging.md`):
  the real refinement. It's the **engine** that turns the In-build interrogation from manual
  eyeballing into a rankable filter (`In-build ∩ construction-nature`), separates the $106M CAPEX +
  downstream material from genuine outsourced construction, and raises the effective advance share
  above the 63% floor. Tag by vendor archetype/SWBS (nature), ideally as a **2×2 timing × nature**.
- **Resolve ArtCraft** (swing factor $42M↔$48M): UEI `H4ZMPGLLZ8D9`, SAM NAICS **332710 Machine
  Shops**, "SCHIEB PROJECT"; likely one firm double-spelled ("ARTCRAFT"/"ART CRAFT") → possible
  double-count. Corroborate what it builds.
- **Chase the `"* OUTSOURCING"` tokens** (machinery — Boland Marine; pipe) to complete the
  non-structural new-construction outsourcing map.
- **The $106M "CAPEX: SOW FOR [supplier]" program** is itself a slide-worthy finding — DDG
  industrial-base / supplier-capacity investment, distinct from outsourcing.
