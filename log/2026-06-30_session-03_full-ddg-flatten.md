# Session 03 — Full DDG runtime flatten

## Scope

Follow-up to the initial consolidation branch.  This branch removes the old TAM/SAM runtime
folder split and makes `ddg/sheets/` the single sheet implementation surface.

## Changes

- Delete the historical `ddg/tam/` and `ddg/sam/` runtime trees from the branch.
- Move/re-expose the sheet modules under `ddg/sheets/` with a single registry.
- Add import compatibility aliases inside `ddg.sheets` so the formula-heavy copied modules continue
  to resolve their producer modules while future edits happen in one folder.
- Collapse the TAM and SAM deflator tabs into one shared `Deflators` sheet backed by
  `data/workbook_inputs/reference/ref_procurement_deflators_fy2026.csv`.
- Keep the new merged `Executive Summary` as the front door and keep detailed analytical sheets
  separate for later sheet-consolidation sessions.

## Validation note

This branch still needs a local workbook build plus LibreOffice recalc QA before merge.
