# Session 02 — DDG-51 true merge: flatten + merged summary + prune

**Date:** 2026-06-30
**Goal:** Turn the session-01 *physical combine* (two `SHEETS` registries packaged together
via `build_ddg.py`) into a *true merge*: one `ddg/sheets/` package holding every module, one
merged Executive Summary, one consolidated DDG-scoped `ddg/data/` tree, old scaffolding gone.
**Outcome:** ✅ Done in three commits. Output: `ddg/20260630_Distributed Shipbuilding DDG51_v1.1.xlsx`
(38 sheets, recalc-clean).

---

## Three commits

**Commit 1 — flatten + consolidate data (no analytical change).**
- `ddg/sheets/` is the only sheet package now: all 60 modules from the two pipelines, copied
  with import paths rewritten to the flat `sheets` / `lib`. Colliding helpers split by
  provenance (`_tam_*` / `_sam_*` for cuts, inputfill, italic, layout, widths); one merged
  `_tabs.py` (SAM's three colliding tab constants → `TAB_SAM_EXEC_SUMMARY` /
  `TAB_CLASSIFICATION_METHOD` / `TAB_SAM_DEFLATORS`).
- `ddg/lib.py` (thin: OUT / DATA_DIR / docProps), `ddg/build_workbook.py` (canonical
  `workbook_core` group order — **no** `sam_*` retag; the muted palette is the engine default).
- `ddg/data/`: `workbook_inputs/{tam_budget, sam_awards/<category>}/` with `ddg_*` program
  universes + `ref_*` deflators; `audit/` for guard-only CSVs. 25 inputs; the 9 unread research
  artifacts dropped. `sheets/_data.py` resolves each module's terse logical stem → its `ddg_`/
  `ref_` file (side-aware, so the two `deflators` stems disambiguate). `data/manifest.yaml` +
  `README.md` document it.
- **Guard change:** `_sam_integrity.assert_universes_aligned` now compares the two real runtime
  sources (`ddg_subaward_transactions` ↔ `supplier_master`); `ddg_program_vendors.csv` dropped
  entirely (the program-vendor sheet builds its rows in-memory, so it was never a sheet input).

**Commit 2 — merge the two exec summaries.**
- One `sheets/executive_summary.py`: §1 scope · §2 addressable TAM (incl. cumulative headline) ·
  §3 observed SAM · **§4 TAM-to-SAM bridge (the deferred reconciliation, now a live row per FY)** ·
  §5 where-to-play by capability domain · §6 hull/SWBS visibility. All live formulas into the
  model sheets. SAM Executive Summary tab dropped → 38 tabs.
- TAM method tab renamed `Methodology` → `TAM Methodology` (SAM's is `Classification Method`).

**Commit 3 — prune.**
- `git rm -r ddg/tam ddg/sam ddg/build_ddg.py` + cleared the gitignored remnants. The flat build
  is self-contained (rebuilds from the pruned tree).

---

## Provenance note (parallel codex branch)

A parallel `codex/merge-ddg-sheets-data` branch (draft PR #1) did a **non-destructive** version:
a new registry + merged summary, but the sheet modules stayed in `tam/`/`sam/` as compat shells.
It independently converged on the **same** `ddg/data/` tree (good cross-check) and its merged
`executive_summary.py` was adopted here (adapted to the flat imports, plus the cumulative-TAM line).
This branch supersedes PR #1 by also doing the physical flatten + the program-vendor guard change.

## Verification

- ✅ Build = **38 sheets**; canonical order summary → guide → inputs → model → data → validation.
- ✅ LibreOffice full recalc (OOXMLRecalcMode=Always) → **0** error cells, all three commits.
- ✅ Headlines unchanged from session 01: cumulative TAM (FY22-27) **$6,421.7M**, BC coeff **0.2529**,
  OBBBA **$857.8M**, AP/LLTM **$1,042.3M**, outyear low/high bands. Bridge ratios FY22-25
  0.34 / 0.23 / 0.65 / 0.56.
- ✅ Zero references to the old package names remain anywhere under `ddg/`.

## Follow-ups

- **Deflators dedup** — `Deflators` (TAM) + `Deflators (SAM)` are now adjacent in *inputs*; collapse
  once the row layouts are reconciled.
- **Virginia / Columbia** — replicate `ddg/` per program; each adds its own `_data.py` rows + files
  (the manifest makes silent reuse of a `ddg_*` file impossible).
