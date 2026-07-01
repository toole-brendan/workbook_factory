# Session 08 — Full milestone chain + FY2013 window extension + Hull Full-Span expansion

**Date:** 2026-07-01
**Branch:** `promote-sam-findings-round1` (continues from sessions 05–07); **merged to `main`** mid-session (bc9f02a)
**Scope:** (a) Restructure `ddg_hull_master` into the full DDG-51 milestone chain — split the
mislabeled start-fab/keel column into **true first-steel** + **keel** — and make **DDG Hull Full-Span**
a 5-band exhibit. (b) Extend the observed SAM transaction window **FY2016 → FY2013** to recover the
pre-2015 subaward front-end that a deliberate size-cut had been hiding. (c) Expand Full-Span from 2 → 7
hulls and add a **Flight** column.
**Outcome:** ✅ All verified, recalc-clean, all Checks reconcile. Observed subaward universe
**$3.18B → $3.96B (+25%)**, Advance/LLTM **65% → 72%**, exact-hull full-build-stage coverage **2 → 7
hulls**. Milestone chain + window extension are **committed & merged to main (bc9f02a)**; the Full-Span
7-hull expansion + Flight column are **uncommitted** (on top of main).

---

## 1. The load-bearing data-model fix — full milestone chain in `ddg_hull_master`

**The bug:** the single `Start Fabrication` column was a **start-fab/keel mongrel** — for some hulls it
held the true first-steel date, for others the keel (memory + the module docstring admitted "keel-laying
proxy"). Concretely: DDG 125's value was its **keel (Nov 2019)**; its true first-steel is **May 2018**;
DDG 129's value was its true **first-steel (Jan 2021)**, keel is Spring 2022. So the live `DDG 125/128
Full-Span` band split was **over-labeling Long-lead** (folding the fabrication phase into it).

**The fix:** restructured the CSV (13 → 16 cols) to the canonical chain
`MYP Base Award | Start Fabrication (true first-steel) | Keel Laid | Launch | Delivery | Commissioned`
(+ `Schedule Confidence` + hover-note). Hulls **118–133** populated from the user's curated SAR /
NAVSEA-SNA-2022-deck / navy.mil table (day-level normalized to `Mon YYYY`, the format the in-formula
parser needs; day-level + source kept in the note). Added DDG 120 (new row; 36 total). Non-user hulls
113/114/117 → keel from the MIRS crosswalk, first-steel blank; future hulls keep their projected value
in `Start Fabrication`.

**Procurement-timing stayed KEEL-basis** (explicit user choice). `ddg_piid_hull_map` Earliest Keel /
Latest Delivery recomputed = `min(Keel else Start Fab)` / `max(Delivery)` per family. Only 3 envelopes
shifted, and **FY13-17 HII (N0002413C2307, DDG 125's family) is UNCHANGED at Oct-2015 keel** (DDG 117 is
its earliest and its keel didn't move) — so 125's classification is stable. Shifts: FY18-22 HII
Jan→Jun 2021 (+5mo), FY18-22 BIW May 2021→Aug 2024 (few BIW subawards), FY13-17 BIW May→Mar 2018,
FY13-17 HII latest delivery Jun→Apr 2023 (125's corrected delivery).

**Full-Span → 5 bands:** added **Fabrication (first-steel → keel)** between Long-lead and Construction
in `ddg_full_span_drilldown.py`; milestone serials became `$C/$D/$E/$F`; `checks.py` partition +=
Fabrication; `assert_hull_milestones_monotonic` extended to `award ≤ start-fab ≤ keel ≤ launch ≤
delivery ≤ commissioned`. Initial 2-hull values (FY2026$): DDG 125 = **$27.26M** (LL 5.59 / **Fab 4.32**
/ Con 2.57 / Out 3.49 / Post 11.29) — confirming ~half the old "long-lead" was really fabrication.

**Data caveats baked into notes (source anomalies I did NOT silently accept):**
- **DDG 119** — user table had Delivered Nov 2021 *before* Commissioned Sep 2020 (impossible) → kept
  existing **Apr 2020** delivery; keel via MIRS **Jun 2016** (user "~2017").
- **DDG 128** — used user keel **Jun 2021** (MIRS says Mar 2022); **kept its Dec 2025 delivery** even
  though the user table showed "—" (it IS delivered — and it's a Full-Span hull, so blanking it would
  break the post-delivery band).
- **DDG 127** — MYP Base Award aligned to its FY13-17 block (user table listed the FY18-22 date).

## 2. Extend the observed SAM window FY2016 → FY2013 (recover the pre-2015 front-end)

**The floor was a deliberate size-cut, NOT a data limit.** The full-history FSRS pull lives at
`ooxml_build_pipelines_light/.../tam/ddg_research/research/sam_subawards_fullhistory` (back to 2001).
The window is **one constant `SAM_TX_FY_START` in `ddg/lib.py`** that drives **both** the `cuts.py`
`_in_sam_window` row filter **and** the `fiscal.py` per-FY axis (`FY_YEARS` / `FY_BIN_KEYS` /
`FY_HEADERS`) — flip it and everything follows.

Flipping 2016 → 2013 recovered **1,013 pre-2015 rows** (back to Apr 2013) under the 7 in-scope primes:
**N0002413C2307 (FY13-17 HII) +779, DDG 114 +132, DDG 113 +102** (the lone 2001 stray under a BIW PIID
dropped). Appended to `ddg_subaward_transactions.csv` (**5,006 → 6,019**), column-aligned from the
original 64-col tx (`HII Work-Item Code` + `Builder` already materialized; SWBS cols are blank/formula-
filled by design, so no re-tag needed). Re-sorted by (UEI, date).

**Two downstream breaks the guards caught (and I fixed):**
- **Wide baked-per-FY CSV** `ddg_swbs_by_subsystem.csv` — its widths derive from `FY_YEARS` (now 13
  years) but the CSV only had FY16–26 columns → added blank **FY13/14/15 $M** columns (formula-filled).
- **`ddg_supplier_year_activity.csv`** — the `assert_supplier_year_activity_spine` guard requires the
  spine to exactly equal the tx universe. **Regenerated** it from the extended tx (+388 vendor-years:
  FY13 114, FY14 129, FY15 145).
- Deflators already covered `≤FY12 / FY2013 / FY2014 / FY2015`, so constant-$ conversion needed no new
  inputs.

**GOTCHA:** `sum(1 for _ in open(csv))` != csv row-count here — `Subaward Description` fields carry
embedded newlines, so `open()` line-count reads ~2× the true rows. Use `csv.reader`. (Cost me one
false "the build overwrote my CSV" diagnosis; the append was intact at 6,019.)

**Effect (recalc, FY2026$):** observed universe **$3,175.5M → $3,956.3M**; Advance/LLTM **$2,072.6M
(65.3%) → $2,842.4M (71.8%)**, In-build 33.7% → 27.3%, Post-delivery 1.0% → 0.8%. All recovered $ is
the older hulls' pre-keel long-lead, so it reinforces the front-loaded / advance-procurement headline.

## 3. Coverage analysis + Full-Span expansion 2 → 7 hulls + Flight column

**Per-stage hull coverage** (exact-hull A/B, staged on each hull's own chain; offline scripts): 24
distinct hulls carry exact-hull attribution (21 HII + 3 BIW stragglers of 1–3 rows). Hulls with data in
**all four build phases**: pre-recovery **5** (121/123/125/128/129) → post-recovery **6** (DDG 119
joined — gained Long-lead) → **7** after adding DDG 117's first-steel. Full **5-stage** span (incl.
post-delivery) = **6** (117/119/121/123/125/128; 129 not yet delivered). 113/114 still miss the
**Fabrication** band — we have their keel but not their true first-steel.

**Expanded `DDG 125 & 128 Full-Span` → all 7 hulls; renamed tab → "DDG Hull Full-Span"** (`tabs.py`;
the `full_span_cols` accessor auto-follows). `_HULLS` = 117/119/121/123/125/128/129; docstring + intro
rewritten with honest coverage caveats (117 front lightly clipped by the FY2013 floor; 129 empty
post-delivery). Added **DDG 117 first-steel = Sep 30 2014** (user, NAVSEA; first FY13-17 MYP ship to
start fab) → 117 gained its Fabrication band and completed the 4-build-phase set.

**DDG 117's $61.3M Long-lead (FY2026$) is legitimate, not an artifact** — it's the lead ship's major
LLTM, surfaced by the recovery: **Rolls-Royce SSGTG $21.4M**, York A/C plants $16.6M, L-3 Westwood
switchboards $3.7M, Alfa Laval fuel purifiers — all ordered Jun–Jul 2013, ~15 mo before first-steel.
(Possibly inflated by lead-ship EOQ covering follow-hulls; items are real.) It's the single biggest
thing the pre-2015 pull exposed.

**Added a `Flight` column** to Full-Span (after Hull; milestone serials shifted `$C/$D/$E/$F → $D/$E/$F/$G`,
verified by unchanged $). Live text lookup from Hull Master's accurate **`Flight IIA` / `Flight III`**
labels (NOT a simplified "Flight II" — there are no true Flight II ships here). Split: **IIA =
117/119/121/123**, **III = 125/128/129**, dividing at DDG 125 (first Flight III).

## Verification

- `python3 build_workbook.py` + LibreOffice headless recalc (OOXMLRecalcMode=0 temp profile) →
  **0 error cells**, all reconciliation **Checks OK** (incl. the Full-Span partition for all 7 hulls,
  and Procurement-timing phases = observed universe).
- Milestone monotonicity holds for all 36 hulls across the full 6-event chain.
- Envelope changes localized (only 3 families; 125's family unchanged).
- Adding the Flight column left every hull's stage $ identical → the column-ref shift is correct.
- Workbook 3.49 MB → 4.10 MB (the +1,013 tx rows are genuinely built in; tx sheet 4,838 → 5,851 rows).

## Files changed

**Committed & merged to main — bc9f02a** (12 files): `ddg_hull_master.csv`, `ddg_piid_hull_map.csv`,
`ddg_supplier_year_activity.csv`, `ddg_swbs_by_subsystem.csv`, `ddg_subaward_transactions.csv`,
`ddg/lib.py`, `sheets/checks.py`, `sheets/ddg_full_span_drilldown.py`, `sheets/ddg_hull_master.py`,
`sheets/kit/integrity.py`, `.gitignore`, + the built `.xlsx`. The `.gitignore` now **tracks the built
DDG-51 deliverable** (un-ignored `ddg/*.xlsx`, overriding the repo's CSV-only convention — user
request) and **ignores `ddg/prime_obligations/`** (a separate prime-contract-obligation analysis, not
this workstream).

**Uncommitted (on top of main):** `sheets/ddg_full_span_drilldown.py` (7-hull expansion + Flight
column), `sheets/kit/tabs.py` (tab rename → "DDG Hull Full-Span"; note tabs.py also carries a parallel
`TAB_MODULE_COST` + 31-char assert added outside this workstream), + the rebuilt `.xlsx`.

## Analysis tooling / data (external — NOT read by the build)

- Offline coverage/timeline scripts in the session scratchpad (per-stage hull coverage, quarterly
  binning vs milestones, the 7-hull $ sample). Replicate `_hull_logic.resolve()` (A/B/C/D/X) +
  `_lifecycle.stage_for()` against the current CSVs.
- Source of the recovered data: the full-history FSRS pull dir named above; deflators reach `≤FY12`.

## Open items / follow-ups

- **Commit + push the Full-Span 7-hull expansion + Flight column** to main (pending; asked, user moved
  to the next request).
- **113/114 first-steel dates** would give them a Fabrication band → **9** full-build-stage hulls.
- **Refresh stale docs:** `HANDOFF.md` / `DDG51_SAM_KEY_TAKEAWAYS.md` still cite ~63% advance (now
  71.8%) and the FY2016 window label (now FY2013).
- **Original ooxml workbook** (`workbook_award_classification_refactor`) still has the mongrel Start Fab
  + its own `_lifecycle.py` engine — the fix was NOT propagated upstream.
- **DDG 117 EOQ** — confirm whether its large Jun-2013 LLTM (esp. Rolls-Royce SSGTG) includes follow-
  hull economic-order quantities before quoting it as strictly 117's per-hull long-lead.
