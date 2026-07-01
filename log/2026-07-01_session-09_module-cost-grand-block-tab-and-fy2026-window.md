# Session 09 — Module-cost + grand-block tab, FY2026 window lift, named fiscal windows

**Date:** 2026-07-01
**Branch:** `main` (uncommitted; sits on top of session-08's uncommitted milestone-chain work)
**Scope:** (a) Consolidate the sibling `ooxml_build_pipelines_light/.../ddg_module_cost` workbook
(per-ship BC → 4 modules → 21 grand blocks → 72 units cascade + SAM-to-module bridge) **plus** the
session-07 grand-block outsourcing evidence into ONE new tab in this factory's DDG workbook.
(b) Quantify FY2026 subaward coverage, lift the FY2026 exclusion, and rework the workbook's year
handling into **named, derived fiscal windows**.
**Outcome:** ✅ 33 → **34 tabs** ("DDG Module Cost & Grand Blocks", model group), 0 recalc error
cells, all Checks OK (incl. 3 new). FY2026 included and flagged partial throughout; all 22
grand-block actions now tie live to the transaction leaf ($54.95M then-yr = $54.95M leaf tie;
$55.58M FY2026$). No frozen year-range literals remain.

---

## 1. Grand-block evidence — now in BOTH workbooks

- **Sibling first (wrong target, kept deliberately):** the standalone `ddg_module_cost` workbook
  (ooxml repo) got its own "DDG Grand-Block Outsourcing" guide tab + Bridge §5 cross-ref +
  `validate_workbook.py` tie-outs (6 → 7 sheets, validates clean). Hardcoded curated table in the
  `outfit_context.py` idiom; cost anchor live off its Assumptions (per-block = $1,573.6M/21 =
  $74.9M).
- **This factory (the real target):** one consolidated tab carries everything, live.

## 2. New tab — "DDG Module Cost & Grand Blocks" (`sheets/ddg_module_cost.py`, model group)

Consolidates all six ddg_module_cost tabs into one sheet; registered after DDG Hull Full-Span.

- **§1 Hierarchy** — ship → 4 modules → 21 grand blocks → 72 units (counts `S_INT_INPUT`), HII
  verbatim quote, PWBS-vs-SWBS note.
- **§2 Cost anchor (LIVE)** — `scn_cell(2122, 2025, 'basic')` (SCN Budget, const FY2026$)
  ÷ `fydp_qty_cell(2122, 2025)` = **$1,575.1M/ship** (matches sibling's $1,573.6M within 0.1%);
  FY2027 single-ship memo row. No transcription — moves with the budget CSVs.
- **§3 Even-split cascade** — module $393.8M / **grand block $75.0M** / unit $21.9M.
- **§4 Evidence table** — the 22 curated grand-block actions (CSV copied to
  `data/workbook_inputs/sam_awards/hull/ddg_grand_block_subawards.csv`, lib alias added). Columns:
  Yard | Report ID (text, `S_TEXT_INPUT`) | Date | Hull | Grand Block (Python-derived from the SOW
  text) | Then-yr $M | **FY2026 $M (live)** | **Leaf $M (live)** | verbatim description. The two
  live columns are `SUMIFS` over the transaction leaf keyed on `Subaward Report ID` — **the leaf
  stores Report ID as TEXT** (not in int_cols), so the criteria cell must be text too.
- **§5 Roll-ups (live over §4)** — by yard (Gulf Copper $31.59M/17 · BAE Jax $17.72M/2 · Eastern
  $5.65M/3), by hull (DDG 137 **$49.2M** / 139 $4.8M / 135 $0.9M), DDG 137 by named block (B15
  17.72 / D52 10.88 net of the −$7.19M Oct-2025 rescope / A16&A21 5.37 / C15 5.31 / B43&B13 5.01 /
  D41-D42 2.51 / D11-D31 1.68 / unlabeled 0.74).
- **§6 Anchor vs observed** — largest outsourced block (GB B15 $17.7M) = **23.6%** of the model
  per-block allocation; framed as a FLOOR (bare structural fab; erection/outfit/integration/test
  stay at the prime) and an order-of-magnitude band (even split; A/B/C/D structure blocks likely
  below-average). *Bug caught in recalc verification: §6 initially referenced column C (the count,
  21) instead of D (the $75.0M) of the §3 grand-block row → share read 84%; fixed to D.*
- **§7 Bridge discipline** — SWBS functional vs PWBS physical; attribute-to-block only on explicit
  text; this lens sees only the OUTSOURCED tail of make-vs-buy; SWBS mix lives on DDG SWBS by
  Ship-System.
- **Checks (3 new, §4 SAM reconciliation):** grand-block leaf tie (Σ then-yr − Σ leaf = 0), DDG 137
  block rollup partitions its hull total, per-ship BC anchor band ($1,450–1,700M). **Guard:**
  `assert_grand_block_ids_in_leaf()` (window-aware) in `kit/integrity.py` + `_run_guards()`.

## 3. The FY2026 discovery (the new guard earned its keep immediately)

First build FAILED: **7 of the 22 grand-block actions are dated Oct–Dec 2025 = federal FY2026**,
outside the then-window (FY2013–FY2025 excludes the in-progress FY). Interim treatment shipped
(all 22 shown, live ties for the 15 in-window, explicit in-window subtotal $30.0M on Checks), then
superseded by the window lift below.

**FY2026 coverage quantified** (raw pull, latest subaward date 2026-05-27; both repos carry the
identical pull): **176 rows / $65.6M net** vs FY2025's 712 / $683.7M. Monthly: Oct $17.8M / Nov
$14.4M / Dec $23.8M, then a cliff (Jan $6.6M, Feb $0.7M, Mar $1.1M, Apr $0, May $1.2M) — classic
FSRS reporting lag, not decline. Like-for-like Oct–May: FY2025 435 rows/$275M vs FY2026 176/$65.6M.
**38% of reported FY2026 $ is the grand-block program**; top FY2026 vendors are literally Gulf
Copper ($15.5M) and BAE Jax ($9.4M). Excluding FY2026 hid the newest chapter of the outsourcing
story (incl. the second $9.45M GB B15 award).

## 4. Named fiscal windows (`ddg/lib.py` = single source of truth)

Design principles (agreed): per-FY is the default presentation grain; pools survive only for
supplier-STRUCTURE metrics and must be named + derived; TAM's budget-year frame constrains nothing
except the bridge (two-universe wall).

- **Constants:** `SAM_TX_FY_END = 2026` (window now includes the in-progress FY),
  `SAM_LAST_COMPLETE_FY = 2025`, `SAM_REPORTED_THROUGH = "May 2026"` (**update per re-pull** — it
  drives every partial-year footnote), `SAM_PARTIAL_NOTE`, `SAM_TX_WINDOW_LABEL(_FULL)`,
  `BRIDGE_FYS = (2022..SAM_TX_FY_END)`, `POOL_N = 4`,
  `POOL_FYS = trailing 4 COMPLETE FYs` (= 2022–2025 today, rolls automatically), `POOL_LABEL`.
- **Safe by construction (verified before the flip):** dimension CSVs were built unwindowed — all 6
  FY2026-only UEIs already in supplier_master + program_vendors; spine has 87 FY2026 rows (= tx
  exactly); deflators cover FY2026 → `assert_universes_aligned` and the fiscal-axis guard stay
  green. `kit/fiscal.py` derives `FY_YEARS`/`FY_BIN_KEYS`/`FY_HEADERS` from the lib constants, so
  the leaf filter, tx computed columns, Deflators split, and every per-FY "$M" column
  (Program Vendors, Hull Spend, SWBS Rollup) auto-extended.
- **Bridge sheets:** `market_bridge.py` + `executive_summary.py` swapped local
  `_BRIDGE_FY=(2022..2025)` for `BRIDGE_FYS`; the partial year renders **"2026\*" / "FY2026\*"**
  with footnotes (FSRS lag + the asymmetry: TAM FY2026 is enacted/complete-as-plan, SAM is partial
  → ratio biased low, not comparable). Exec §3 gained the FY2026\* column (fits `_NCOLS=8`
  exactly); "FY25 active UEIs" and the §5 where-to-play year now derive from
  `SAM_LAST_COMPLETE_FY`.
- **Pools:** `where_to_play.py` `FYS = POOL_FYS` + `POOL_LABEL` intro with the rationale (a
  partially-reported year would read reporting lag as supplier churn). `program_tam.py`'s
  "FY22-25 average penetration" look-back left numerically as-is (TAM-frame, complete overlap).
- **Stale-prose sweep:** the three intros still saying "FY2016-FY2025" (hull_spend_summary,
  procurement_timing, swbs_rollup — already wrong after session-08's FY2013 extension) now
  f-string `SAM_TX_WINDOW_LABEL` + `SAM_PARTIAL_NOTE`; `kit/cuts.py` + `kit/fiscal.py`
  docstrings reference lib constants instead of literals.
- **Module-cost tab de-special-cased:** the out-of-window intro parenthetical, "of which" subtotal
  row, and §5 carve-out note are now conditional on `n_out > 0` (currently 0 → clean sheet; the
  machinery reactivates automatically if a future pull carries post-window actions).

## Verification

- `python3 build_workbook.py` → **34 sheets**, all guards pass (incl. the new grand-block guard).
- LibreOffice headless recalc → **0** error cells; **Checks master OK**, zero FAILs.
- Market Bridge row "2026\*": TAM $1,929.2M vs observed SAM $65.6M → 3.4% (flagged).
- Exec Summary §3: FY2022..FY2026\* = 163.2 / 289.4 / 567.6 / 698.1 / 65.6; Lifetime $4,021.9M;
  FY25 active UEIs 141.
- Module Cost totals: then-yr **54.95** / FY2026$ **55.58** / leaf tie **54.95** (delta 0); DDG 137
  49.21 = block rollup 49.21; per-ship BC 1,575.14; per-block 75.01; B15 share 23.6%.
- `grep "FY2016-FY2025\|FY2013-FY2025"` → no hits; no un-derived FY25/2025 window literals.

## Files changed (branch `main`, uncommitted; session-08's milestone-chain edits also pending)

- **New:** `sheets/ddg_module_cost.py`;
  `data/workbook_inputs/sam_awards/hull/ddg_grand_block_subawards.csv` (copy of the root curated
  artifact, 22 rows)
- **Modified:** `lib.py` (window constants), `build_workbook.py` (guard call), `sheets/__init__.py`,
  `sheets/kit/tabs.py` (TAB_MODULE_COST), `sheets/kit/integrity.py` (grand-block guard),
  `sheets/kit/fiscal.py` + `sheets/kit/cuts.py` (docstrings), `sheets/checks.py` (3 checks),
  `sheets/market_bridge.py`, `sheets/executive_summary.py`, `sheets/where_to_play.py`,
  `sheets/ddg_hull_spend_summary.py`, `sheets/ddg_procurement_timing.py`,
  `sheets/ddg_swbs_rollup.py`
- **Sibling repo (ooxml, separate):** `ddg_module_cost/` gained the standalone grand-block tab
  (7 sheets, validates clean) — kept per user decision.

## Open items / follow-ups

- **Re-pull discipline:** update `SAM_REPORTED_THROUGH` in `lib.py` with every FSRS re-pull; the
  partial-year cliff (Feb+ ≈ unreported) will fill in over the coming months.
- **Deck caveat:** any FY2026 figure needs the "partial — reported through May 2026" flag; the full
  $55M grand-block story now includes ~$25M of FY2026 activity.
- **Plan B (material-vs-construction nature tagging)** still open — the 2×2 timing × nature engine
  (`ddg/plan_b_material_vs_construction_tagging.md`).
- **ArtCraft** ($6.2M "SCHIEB PROJECT", UEI H4ZMPGLLZ8D9) still unresolved; `"* OUTSOURCING"`
  machinery/pipe tokens (Boland) unchased; the $106M CAPEX supplier-capacity program still
  slide-worthy.
- Consider a Checks/Exec row surfacing FY2026 reported-to-date vs FY2025 same-months as a
  reporting-completeness tripwire for future pulls.
