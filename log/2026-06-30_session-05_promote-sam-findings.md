# Session 05 — Promote DDG-51 SAM research findings into the workbook

**Date:** 2026-06-30
**Branch:** `promote-sam-findings-round1` (off `main`)
**Scope:** Promote the approved items from `ddg/docs/ddg_sam_research_findings.md` (staged last
session, nothing applied) into the curated workbook inputs, rebuild, and QA. Chosen scope: P3
full · P4 strong set · P2 full (provenance + 4 corrections + MIRS file) · P1 DDG-150 note.
**Outcome:** ✅ Applied and verified — 37 sheets, 0 LibreOffice recalc error cells, all
reconciliation checks OK.

---

## The load-bearing discovery (overrides the HANDOFF's central warning)

The HANDOFF warned that the factory renders *pre-computed* SWBS CSVs, so editing the crosswalk
would reclassify **$0** unless you regenerate upstream (`build_ddg_swbs_rollup.py` +
`tag_ddg_transactions_swbs.py`) and re-sync three CSVs across repos. That is true of the
**upstream** `ooxml_build_pipelines_light` workbook — but the **factory was re-architected to
compute SWBS live**, verified in-code:

- `sheets/ddg_swbs_rollup.py` leaves the `ddg_swbs_by_subsystem.csv` dollar cells empty and fills
  them with build-time `SUMIFS/COUNTIFS/MINIFS/MAXIFS` over the transactions sheet.
- `sheets/ddg_subaward_transactions.py` fills the `SWBS Subsystem/SWBS/SWBS basis` cells with live
  `INDEX/MATCH` (`kit/flat.py::swbs_from_row/swbs_match_row`, exact `MATCH(...,0)`) keyed on the
  already-**materialized** `HII Work-Item Code` (transactions CSV col 51).

So all four priorities reduced to **factory leaf-CSV edits + `python3 build_ddg.py`** — no upstream
regen, no cross-repo sync, no touching the known-broken base generator or the openpyxl archetype
generators. Verified 52 of the 55 target codes already carry factory transactions, so the crosswalk
edit moves dollars on rebuild.

## What changed (4 tracked CSVs + 1 source file)

- **`swbs/ddg_hii_swbs_crosswalk.csv`** (+55 rows): 46 observed (`X · code crosswalk (observed)`,
  Evidence = component text from the upstream `hii_ddg_record_components.csv`) + 9 curated
  (`C · curated inference`). Normalized the file to uniform CRLF (it was CRLF; the appended rows
  had come out LF).
- **`swbs/ddg_swbs_by_subsystem.csv`** (+1 row): new subsystem 572 spine row between 571 and 581.
- **`classification/ddg_vendor_archetype_overrides.csv`**: 12 in-place D/P updates + 11 new rows
  (all Program=DDG, all UEIs in `ddg_supplier_master.csv`). Round-tripped via csv preserving the
  multi-line quoted notes; obsolete "P0-hold" notes on updated rows replaced with the new rationale.
- **`hull/ddg_hull_master.csv`**: 18 rows touched — 6 primary re-cites, 9 MIRS re-cites, 4
  corrections (134/136 Start Fab blanked; 127 launch Oct→Jul 2024; 126 launch blanked
  christening≠launch), DDG 150 builder note. All dates kept "Mon YYYY" and monotonic.
- **`reference/MIRS_US Built_Destroyers.xlsx`**: copied in as the cited S&P Global source; added a
  `.gitignore` negation (`!ddg/data/workbook_inputs/reference/*.xlsx`) so this source artifact is
  tracked while build-output `*.xlsx` stay ignored.

## Guardrails that shaped the work (validated in-code before editing)

- `kit/integrity.py::assert_archetype_codes_valid` — D ∈ D0..D11, P ∈ P0..P6 (or blank), uppercase
  → hard build gate on the P4 codes.
- `kit/integrity.py::assert_hull_milestones_monotonic` — dates parsed "Mon YYYY", start ≤ launch ≤
  delivery → forced no day-level dates; provenance rides on the Source-URL columns.
- `sheets/checks.py` "SWBS rollup reconciles to HII universe" — stays balanced only if every
  subsystem a code maps to has a spine row; all 13 targets ∈ existing spine ∪ {572}.

## QA (before → after)

| bucket | baseline $M | final $M |
|---|---|---|
| U00 | 518.88 | **431.56** |
| 505 General piping | 29.79 | 93.57 |
| 504 Instruments | 10.33 | 18.59 |
| 631 Painting | 5.35 | 12.37 |
| 561 Steering | 112.33 | 114.76 |
| rollup total (invariant) | 3110.94 | 3110.94 |

- `python3 build_ddg.py` → 37 sheets, no assert failures, after every priority.
- LibreOffice headless recalc → **0** `t="e"` error cells.
- All §4 SAM reconciliation checks + §5 master check = OK.
- TAM untouched by construction (no TAM input CSV edited).

## Follow-ups / notes

- **P4 medium NAICS-only rows** (MMC Metrology $3.6M, NAG $2.5M, etc.) deferred per scope — the
  largest remaining unclassified $ (D0 = $147.8M / 137 vendors).
- **`T2VFE1NGR3G5` (DRS)** filled D6/P3 despite a possible intentional VLS launch-control
  sensitivity hold on P0 — revert if that was deliberate.
- **Subsystem 572** currently $0 in-window (01006-01 is pre-FY16); the mapping is correct and will
  populate if the FY window expands or new transactions arrive.
- Lifecycle intentionally **not** regenerated — factory Lifecycle Stage is frozen/materialized;
  hull-date edits are display-only (findings §P2 "model-neutral").
