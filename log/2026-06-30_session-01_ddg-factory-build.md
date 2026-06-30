# Session 01 — DDG-51 combined TAM+SAM workbook (workbook_factory bootstrap)

**Date:** 2026-06-30
**Goal:** Stand up a new self-contained `workbook_factory/` at the projects3 root, then build the
first per-program deliverable: a single workbook combining the **DDG-51 slice of TAM** and the
**DDG-51 slice of SAM**.
**Outcome:** ✅ Done and verified. Output:
`workbook_factory/ddg/20260630_Distributed Shipbuilding DDG51_v1.0.xlsx` (39 sheets, recalc-clean).

---

## What this factory is

Two upstream multi-program workbooks live in the original monorepo (untouched, used only as a copy
source):
- **TAM** — `ooxml_build_pipelines_light/projects/distributed_shipbuilding/tam/master` (12 tabs,
  market sizing for Virginia / Columbia / DDG-51).
- **SAM** — `.../sam/sam_awards_data/workbook_award_classification_refactor` (35 tabs, subaward
  vendor classification; heavily DDG-weighted with hull-linkage + lifecycle layers).

`workbook_factory/` splits both by program (vessel) and combines each program's TAM+SAM into **one**
workbook, one standalone folder per program. It is **self-contained**: a copy of the `workbook_core`
engine lives at the factory root, so there is no runtime dependency on the original monorepo path.

### Layout
```
workbook_factory/
  workbook_core/                 # COPIED engine (shared by all program folders)
  log/                           # session logs (this file)
  ddg/                           # DDG-51 combined workbook (this session)
    build_ddg.py                 # combiner + launcher  ->  python build_ddg.py
    tam/                         # DDG-sliced TAM pipeline
      build_workbook.py          #   standalone QA build of the TAM slice
      workbook_master_tam/       #   package (name kept => internal imports unchanged)
      extracted/                 #   TAM CSVs, filtered to DDG (LI 2122 / program "DDG-51")
    sam/                         # DDG-sliced SAM pipeline
      build_workbook.py          #   standalone QA build of the SAM slice
      workbook_award_classification_refactor/
      extracted/                 #   SAM CSVs, DDG subset (+ dimension tables filtered to "DDG")
      prime_contract_scope.csv   #   scope manifest read by the integrity guards
  # virginia/ and columbia/ to be added later by replicating ddg/
```

Each sub-package **keeps its original package name** so the dozens of internal
`from workbook_master_tam.sheets…` / `from workbook_award_classification_refactor.sheets…` imports
needed **zero** rewriting. Only `__init__.py` path math and (lightly) the sliced sheet modules changed.

---

## Build / rebuild

```bash
cd workbook_factory/ddg && python3 build_ddg.py      # the combined deliverable
# QA the halves independently:
cd workbook_factory/ddg/tam && python3 build_workbook.py
cd workbook_factory/ddg/sam && python3 build_workbook.py
```
Python 3.9; stdlib-only engine (no openpyxl in the build path). openpyxl + LibreOffice were used only
for QA.

---

## How the combine works (the load-bearing bits)

- The combiner `ddg/build_ddg.py` imports both DDG-sliced `SHEETS` registries and calls one
  `package_workbook(...)`.
- **Tab-block order:** SAM's `SheetEntry.group` values are re-tagged to `sam_*` keys (frozen-dataclass
  rebuild — no per-module edits), and `workbook_core.groups.GROUP_ORDER` is set **last** to
  `summary, guide, inputs, model, data, validation, sam_summary, sam_guide, sam_model, sam_inputs,
  sam_data`. Result: a clean **[TAM block] → [SAM block]** workbook. (`package_workbook` asserts each
  group is one contiguous run in `GROUP_ORDER` order.)
- **Palette:** the muted charcoal/teal/olive/slate/navy scheme the SAM+TAM books used is now baked in
  as the **factory `workbook_core` default** (`workbook_core/groups.py` `SHEET_GROUPS`), so every
  program folder inherits it. Tab color is baked at sheet import, so re-tagging groups for ordering
  does not change colors.

---

## ⚠️ Gotchas / landmines (READ before replicating for Virginia/Columbia)

1. **Tab-name collisions (3).** TAM and SAM both ship tabs named `Executive Summary`, `Methodology`,
   and `Deflators`. Excel forbids duplicate tab names. Fixed by renaming the **SAM** side in
   `sam/.../sheets/_tabs.py` → `SAM Executive Summary`, `Classification Method`, `Deflators (SAM)`.
   Renaming via the `_tabs.py` constant keeps every SAM formula valid (they reference tabs by the
   constant). Native **table** names did NOT collide (TAM has only `tbl_pop_corpus`).

2. **Shared-style sentinel collision (the build-breaker).** Both packages monkey-patch the shared
   `workbook_core.styles` lists at import, guarded by a sentinel attribute. They used the **same**
   sentinel names, so importing both in one process made the second skip registration and read the
   first's data. Fixed by making the SAM copies' sentinels package-unique:
   `_inputfill_registered → _sam_inputfill_registered` (TAM is a 3-tuple w/ a pct variant; SAM a
   4-tuple — this is what crashed), and `_italic_registered → _sam_italic_registered`. Neither package
   appends to `FONTS`/`BORDERS`, and `FILLS`/`CELL_XFS`/`DXFS` are append-only (indices captured at
   import never shift), so independent registration is safe.

3. **`GROUP_ORDER` is mutated in-process.** SAM's `lib.py` **clears+rebuilds** `GROUP_ORDER` at import;
   TAM's only updates colors. The combiner therefore sets the final `GROUP_ORDER`/`_COLOR` **after**
   both registries are imported (in `build()`), mutating the dicts **in place** (workbook_core.lib
   imported `GROUP_ORDER` by reference).

4. **`set_normalize_dashes(True)` before importing sheets.** The flat SAM sheets build cell XML eagerly
   at import, so the combiner sets dash-normalization on *before* the registry imports, not just at
   package time.

5. **Hardcoded layout rows in TAM data sheets.** `scn_budget.py` (`_FACTOR_ROW`/`_DETAIL_BASE`),
   `place_of_performance.py` (`_DATA_BASE`), and `fydp_outyears.py` (a hardcoded `const[2013]/[1045]`
   submarine-portfolio total) assume 3 program rows. Trimming to DDG shifts those rows — update the
   constants too. These sheets carry runtime `assert`s that catch a wrong recompute, so they're
   self-validating.

6. **Import-time coupling (kills the build before any formula).** A DDG sheet that *imports* a
   VA/COL module dies at import if you drop that module. The real ones hit this session:
   - TAM `executive_summary` / `checks` import `virginia_tam`/`columbia_tam`.
   - TAM `assumptions` reads `scn_cell(2013,…)` → must trim with `scn_budget` in the same pass.
   - SAM `supplier_year_activity` imports the VA/COL tx leaves → trim its imports + `_TX` dict, else
     `where_to_play` + the SAM exec summary die at import.
   - SAM `executive_summary` / `domain_concentration` import `virginia_pv_cols`/`columbia_pv_cols`.

7. **Integrity guards assume all 3 programs.** SAM `_integrity.py` `_PROGRAMS` drives 4 set-equality
   guards; trim to `[("ddg","DDG")]`. They also require **DDG-only** `supplier_master.csv` and
   `supplier_year_activity.csv` — so filter the shared dimension CSVs (below), not just the code.

---

## What was sliced (per phase)

**TAM → DDG (all sheets kept; 12 → 10 tabs):** dropped `virginia_tam`/`columbia_tam`; trimmed the
`_PROGRAMS` loops in `executive_summary`, `checks`, `scn_budget`, `obbba`, `fydp_outyears`,
`assumptions`; cleaned `place_of_performance` (removed VA/COL/sub-AP coeff rows, recomputed
`_DATA_BASE`); de-VA/COL'd `methodology` prose. CSVs `scn_budget`/`place_of_performance`/`obbba`/
`fydp_outyears` filtered to `DDG-51` (`ap_lltm`, `deflators` kept whole).

**SAM → DDG (35 → 29 tabs):** dropped `subaward_activity` (no consumers; needs a spine-CSV regen) and
`market_bridge` (structurally submarine-only); dropped the VA/COL program-vendor + transaction sheets;
trimmed `PROGRAMS`/`_TX` in `executive_summary`, `domain_concentration`, `where_to_play`,
`supplier_year_activity`; renamed 3 tabs in `_tabs.py`; set `_integrity._PROGRAMS` to DDG; de-VA/COL'd
the `Classification Method` prose. CSVs: kept the `ddg_*` + program-agnostic ones; **filtered to
`DDG`**: `supplier_master` (1567→399), `supplier_year_activity` (5363→1817),
`vendor_archetype_overrides` (292→101), `prime_awards` (13→8); deleted all `virginia_*`/`columbia_*`
and the two dropped-sheet CSVs.

---

## Verification (this session)

- ✅ Combined build: **39 sheets**, no duplicate-name error. TAM block (1–10) then SAM block (11–39).
- ✅ SAM integrity guards (DDG-scoped) pass in both the standalone SAM build and the combined build.
- ✅ LibreOffice headless full recalc → **0** `#REF!/#NAME?/#VALUE!/#DIV0/#NUM/#NULL/#N/A` cells.
- ✅ **0** program-style (`Virginia-class`/`Columbia TAM`/…) references anywhere. The remaining
  "Virginia/Columbia" strings are **geographic** (vendor state/location) in the raw DDG transaction
  data — legitimate.
- ✅ DDG headline sanity: Cumulative TAM (FY22-27) **$6,421.7M**; applied BC coeff **0.2529** (~25.3%,
  matches methodology); OBBBA overlay **$857.8M**; AP/LLTM **$1,042.3M**; outyear low/high
  **$726.3M / $805.9M** per year.

---

## Open items / follow-ups (out of scope this session)

- **Virginia & Columbia folders** — replicate `ddg/` (simpler: those programs have no hull/lifecycle
  layers). Re-apply gotchas #1–#7. Each folder gets its own copies (own sentinel renames, own filtered
  CSVs).
- **TAM↔SAM bridge** — user chose *physical combine* for v1; the analytic reconciliation tab is
  deferred.
- **`subaward_activity`** — re-add to SAM if wanted (needs DDG-only spine CSVs regenerated).
- **Deflators dedup** — the combined book carries both `Deflators` (TAM) and `Deflators (SAM)`;
  collapse later once cell-ref layouts are reconciled.
- **Minor cosmetic** — the TAM `Assumptions` tab still shows a now-inert "FY2027 execution spillover"
  knob (Virginia OBBBA artifact, harmless); TAM `scn_budget` §1 keeps a "Portfolio" total over the
  single DDG program (= DDG). Both intentionally left to minimize risk.
- **Unread leftover CSVs** — a few research-artifact CSVs (`classifications.csv`,
  `*_archetype_results*.csv`, `vendor_context.csv`, `parent_concentration.csv`, etc.) remain in
  `sam/extracted/`; not read by the build, safe to prune later.
