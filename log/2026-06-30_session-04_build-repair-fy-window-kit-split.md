# Session 04 — Build repair, FY-window data hygiene, shared-infra cleanup

## Scope

Three follow-on threads from the post-flatten branch (session 03): get `ddg/build_ddg.py`
building again, align the underlying CSVs with the FY2016-FY2025 SAM window introduced by
same-day, unlogged "follow SAM window" commits, and pull DDG's non-tab helper modules out of
the flat `ddg/sheets/` namespace into their own subpackage.

## 1. Build repair (root-caused the flatten regression)

- `ddg/sheets/_layout.py` had been collapsed during the flatten to the simpler TAM-side
  `RowCursor` (no `mark=`/`marked()`, no `text_col`/`start_col`), but `_flat.py` and
  `domain_concentration.py` are SAM-derived and need the fuller feature set. Restored it.
- ~35 modules still imported sibling sheets through the pre-flatten alias paths
  (`workbook_award_classification_refactor.sheets.X` / `workbook_master_tam.sheets.X`), which
  `ddg/sheets/__init__.py` shims onto itself. Depending on import order this silently
  double-executed some modules under two module identities and crashed outright on
  `naics6_archetype_map` (`KeyError` in the init-time aliasing step). Rewrote all 156
  occurrences to the real `ddg.sheets.X` path.
- A same-day, unlogged commit ("Make SWBS rollup FY columns follow SAM window") narrowed
  `ddg_swbs_rollup.py`'s expected FY columns to FY16-FY25 (17 cols) without regenerating
  `ddg_swbs_by_subsystem.csv`, which still had the old `≤FY12..FY26` header (22 cols). Fixed by
  adding a column-trim at load time (see §2) instead of hand-editing the sheet code.
- Verified clean: `python3 build_ddg.py` succeeds; LibreOffice headless recalc shows 0
  `#REF!/#NAME?/#VALUE!/#DIV0!/#NUM!/#NULL!/#N/A` cells across all 34 sheets.

## 2. FY-window data hygiene

Policy: pre-FY2016 data is gone for good; FY2016-FY2025 stays the visible calc window;
FY2026+ data stays archived in the CSVs (not deleted) for future use.

- `ddg_subaward_transactions.csv`: 6,020 -> 5,006 rows (deleted 1,014 pre-FY2016 rows, incl. one
  stray FY2002 row). FY2016-FY2026 stays physically in the file.
- `ddg_supplier_year_activity.csv`: 1,817 -> 1,428 rows (389 pre-FY2016 rows deleted), same
  retention.
- `ddg_swbs_by_subsystem.csv` (wide/pivoted format, one column per FY): physically dropped the
  `≤FY12`/`FY13`-`FY15` columns; kept `FY16`-`FY26` columns on disk. Added
  `ddg/sheets/kit/cuts.py::_trim_fy_columns` (a `load_table` hook scoped to this one CSV) so the
  sheet builder still only sees FY16-FY25 - the same "archive stays full, accessor narrows"
  pattern the row-level SAM-window filter already used for the transaction-grain tables.
- Verified the canonical upstream originals
  (`ooxml_build_pipelines_light/projects/distributed_shipbuilding/sam/.../extracted/`) are
  untouched before any deletion (byte-identical MD5 on the transactions file) - full history is
  recoverable from there if ever needed.
- Left dimension/identity tables alone (`ddg_hull_master.csv` Award FY, `ddg_prime_awards.csv`
  Date Signed, the report-ID-filtered lifecycle/candidates files) since their "FY" isn't a
  transaction window - deleting there would drop whole hulls/contracts, not trim a calc window.

## 3. Shared-infra cleanup

- Deleted `ddg/sheets/_sam_integrity.py` (dead compat shim, no importers) and
  `ddg/sheets/README.md` (stale, described the pre-flatten alias approach).
- Merged the four per-build style shims (`_italic.py`, `_text_input.py`, `_inputfill.py`,
  `_factor.py` - all the same "sentinel-guarded append to workbook_core.styles" pattern) into
  one `kit/styles.py`.
- Moved the 13 remaining non-tab helper modules (`_cuts`, `_widths`, `_taxonomy`, `_tabs`,
  `_structure_classes`, `_program_vendors`, `_program_tam`, `_periods`, `_layout`, `_integrity`,
  `_hulls`, `_flat`, `_fiscal`) into `ddg/sheets/kit/`, dropping the leading underscore.
  `ddg/sheets/` now holds only the 37 modules that actually produce a workbook tab.
- Removed the now-fully-dead `_ROOT_ALIASES`/`_install_package_aliases`/`_alias_many` machinery
  from `ddg/sheets/__init__.py` - with every import now a real path, Python's normal recursive
  import resolution handles the kit/ dependency graph without any manual ordering/aliasing.
- Deliberately did NOT fold `kit/` into `workbook_core/`: `workbook_core/sheet_snippets.md`
  documents RowCursor / the flat-sheet builder as "copy-from, not import" specifically so each
  program can diverge without lockstep coupling, and most of `kit/` (CSV names, the FY window,
  tab names, integrity guards, taxonomy, hull formulas) hardcodes DDG-specific decisions that
  shouldn't leak into the program-agnostic shared engine.

## Verification

- `python3 build_ddg.py`: 34 sheets, clean, re-run after every structural change.
- LibreOffice headless recalc: 0 error cells.
- Confirmed no leftover references to the old alias import paths or pre-move module names
  anywhere under `ddg/`.

## Output

Build now writes a single `20260630_Distributed Shipbuilding DDG51_vS.xlsx`
(`ddg/lib.py::OUT` updated; the two stale `v1.1`/`v2.0` outputs were deleted).

## Open items / follow-ups (out of scope this session)

- Virginia & Columbia folders still not started (see session 01's open items).
- The `flatten-ddg-sheets-data` branch on origin has diverged further (a `tam_deflators.py` /
  `sam_deflators.py` split not present on `main`) - not reconciled here; this session's work
  landed on `main` only.
