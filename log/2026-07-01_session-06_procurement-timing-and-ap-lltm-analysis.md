# Session 06 — Procurement-timing (AP/LLTM) dimension + hull-attribution analysis

**Date:** 2026-07-01
**Branch:** `promote-sam-findings-round1` (continues from session 05; pushed to origin)
**Scope:** After the round-1 promotion (session 05), (a) investigated whether the exact-hull
attribution % can be raised, (b) built a live **Procurement Timing (AP/LLTM)** dimension into the
workbook, and (c) produced a set of analysis artifacts (grand-block outsourcing, coverage
reconciliation, methodology advice).
**Outcome:** ✅ Procurement Timing tab added and verified (38 sheets, 0 recalc error cells, all
reconciliation checks OK). Committed `ce23c9e`, pushed to `origin`.

---

## 1. Hull-attribution investigation (lever #1: prime CLIN / funding linkage) — NEGATIVE result

Tested whether linking subawards to the prime contract's funding actions could move C/D
family-level rows to exact-hull. Pulled the full per-mod transaction history for all 9 DDG prime
PIIDs from **USAspending** (`/transactions/`, no key): **3,734 mods**; HII contracts richly name
hulls (FY13-17: 704/1105; FY18-22: 496/780), BIW barely (13/287).

**Verdict: it does NOT meaningfully bump the exact-hull %.** Applying per-hull prime-funding
windows to the 2,861 C/D subawards narrowed only **3 rows / $1.2M** to a single hull. Three walls:
(1) no join key — prime mods carry WF/TTN/ECP work-item tokens, subawards carry none; (2) the
hull-naming subawards are already A/B; (3) block-buy overlap — 5-7 hulls build concurrently over
~7 years, so timing can't isolate one. Distilled artifact saved (noisy, not wired in):
`ddg/data/research_worklists/ddg_prime_mod_hull_funding_windows.csv`. Raw pulls live in the
session scratchpad only.

## 2. Procurement Timing (AP/LLTM) dimension — the code change

Same leaf-input + live-formula idiom as the SWBS crosswalk (no upstream regen). A **grain-safe**
timing phase computed off each PIID family's construction envelope — a block-schedule property,
NOT a hull assignment — so it covers the C/D majority the hull grade leaves blank.

- **`ddg_piid_hull_map`**: +2 derived columns **Earliest Keel / Latest Delivery** (= min start-fab
  / max delivery over the PIID's hulls, from `ddg_hull_master`). Rendered as date cols.
- **`ddg_subaward_transactions`**: +1 live column **Procurement Timing** (`kit/hulls.
  procurement_timing`, reusing the existing `PIID Map Row` MATCH): `Advance / LLTM` if date <
  family earliest keel, `Post-delivery` if > latest delivery, else `In-build window`, `n/a` off-scope.
  (+1 width, assert 76→77.)
- **New tab `ddg_procurement_timing.py`** ("DDG Procurement Timing", model group): SUMIFS the
  real-$ by phase (+ % of observed, records, first/last, **HII vs BIW split**). Spine =
  `lifecycle/ddg_procurement_timing.csv` (4 phase rows). Registered in `sheets/__init__.py`; tab
  const in `kit/tabs.py`; alias in `lib.py`.
- **`checks.py`**: +reconciliation "Procurement timing phases reconcile to observed subaward $"
  (the four phases partition the universe).

**Result (constant FY2026$):** Advance/LLTM **$2,010M (63.3%)** · In-build $1,134M (35.7%) ·
Post-delivery $31M (1.0%) · n/a $0. Builder split shows BIW's sparse reporting (In-build
HII $1,070M vs BIW $64M).

## 3. Key analytical findings (for the deck / next author)

- **~2/3 of observed SAM is advance/long-lead procurement** (dated before the block's first keel) —
  the load-bearing story: it's why exact-hull attribution caps ~35%, and why observed SAM is a
  supplier-and-timing map, not a per-hull ledger.
- **Denominator ladder** (same $3.2B of subawards, three denominators): ~**10%** of the basic
  construction contract obligation ($28-34B, from the USAspending prime pull); ~**15-20%** of
  yard-side outsourcing (deck framing); ~**50%** of the modeled supplier-addressable TAM ($6.42B).
  All consistent (50% × ~20% ≈ 10%).
- **Grand-block outsourcing (~$55M, 22 rows):** HII outsourcing whole hull grand-blocks to three
  outside yards — **Gulf Copper** ($31.6M, TX), **BAE Jacksonville** ($17.7M, FL), **Eastern
  Shipbuilding** ($5.7M, FL) — for **DDG 135/137/139** (DDG 137 ~a dozen blocks). Publicly
  corroborated (Gulf Copper 5-yr Strategic Sourcing Agreement; Eastern barging blocks; USNI
  "accelerating outsourcing"; "outsource the simpler modules" strategy). SOW documents are NOT in
  the corpus (FFATA carries only the 1-line description). A/B/C/D block zones are HII-internal PWBS,
  not publicly decodable. See `ddg/ddg_grand_block_outsourcing_findings.txt` + `..._subawards.csv`.
- **Labeling caveat (material vs construction):** the "before-keel = advance" test conflates advance
  MATERIAL (turbines/gears — real AP/LLTM) with pre-erection CONSTRUCTION (grand blocks — real
  construction labor). Under the group-earliest-keel rule (the new tab) grand blocks correctly read
  **In-build**; under each hull's OWN keel (the materialized `Lifecycle Stage`) the DDG 137/139
  blocks mis-read **Long-lead**. Small magnitude (~$49M) but a real seam.

## 4. Methodology recommendation (`ddg/ddg_analysis_methodology_advice.txt`)

**Anchor whole-program claims on Procurement Timing** (group-keel, all rows, reconciled,
grain-safe). Use **Lifecycle Stage** (own-keel, A/B exact-hull only, ~35% coverage) as a *scoped
drill-down* for the per-hull build-sequence + stage-level vendor stories. **Trap:** never quote the
lifecycle "87% Long-lead" as a program-level figure — it is 87% of the 35% exact-hull slice; the
whole-program advance share is 63%. Suggested upgrade: add a material-vs-construction split to the
timing frame.

## Verification

- `python3 build_ddg.py`: **38 sheets** (was 37; +1 Procurement Timing tab), no assert failures.
- LibreOffice headless recalc: **0** error cells; **Procurement timing phases reconcile = OK**;
  all §4 SAM reconciliation + §5 master checks OK.
- TAM untouched (no TAM input edited).

## Output / artifacts (in `ddg/`, standalone — NOT read by the build)

- `ddg_grand_block_outsourcing_findings.txt` + `ddg_grand_block_subawards.csv` (22 rows × 64 fields)
- `ddg_analysis_methodology_advice.txt`
- `DDG51_SAM_KEY_TAKEAWAYS.md` (slide-source)
- `data/research_worklists/ddg_prime_mod_hull_funding_windows.csv`
- `ddg_full_coverage_hulls_subawards.csv` + `ddg_subaward_lifecycle_coverage_findings.txt`
  (coverage analysis)

## Open items / follow-ups

- **Material-vs-construction split** on Procurement Timing (separate advance material from
  outsourced/early construction by vendor type + SWBS) — the one real refinement of the anchor.
- **BAE Jacksonville** new-construction block work is in FFATA but uncorroborated in open sources
  (public coverage shows repair/modernization only) — revisit.
- SWBS-major-group and D-archetype cross-cuts on the Procurement Timing tab (Builder split done).
- Prime CLIN linkage is closed as not-viable; do not re-open without subaward-level hull refs.
