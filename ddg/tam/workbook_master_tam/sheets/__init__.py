"""Sheet registry - the tab order and grouping for the master_v2 workbook.

ONE module per rendered sheet (one file = one tab). Tab order = the order of
SHEETS below. Each module exposes a single tables.SheetEntry declaring its group
(see workbook_core.groups); the packager keeps each group contiguous and in
groups.SHEET_GROUPS order (summary -> guide -> inputs -> model -> data).

Layers:
  - summary : the cross-program answer page (Executive Summary).
  - guide   : the framing + method + sources (Methodology).
  - inputs  : the single edit surface (Assumptions).
  - model   : one self-contained TAM tab PER PROGRAM (Virginia, Columbia, DDG-51) -
              each: BC x coeff + OBBBA (+ DDG AP/LLTM) + folded FY28-31 outyears.
  - data    : the live-formula spine, combined by type across all three programs
              (SCN Budget, Place of Performance, OBBBA Mandatory, FYDP Outyears,
              Deflators).
  - validation : live in-workbook checks + master check (Checks), sorts last.

Shared NON-sheet helpers (imported by the sheet modules; NOT registered here):
  _layout (RowCursor) · _tabs (canonical names) · _widths · _cuts (CSV access).
"""
from __future__ import annotations

from . import (
    # summary
    executive_summary,
    # guide
    methodology,
    # inputs
    assumptions,
    # model (DDG-51 only in this slice)
    ddg_tam,
    # data (combined by type)
    scn_budget,
    place_of_performance,
    obbba,
    fydp_outyears,
    deflators,
    # validation
    checks,
)


SHEETS: list = [
    # --- Summary ---
    executive_summary.EXECUTIVE_SUMMARY,
    # --- Guide ---
    methodology.METHODOLOGY,
    # --- Inputs ---
    assumptions.ASSUMPTIONS,
    # --- Model (DDG-51 only in this slice) ---
    ddg_tam.DDG_TAM,
    # --- Data (combined by type) ---
    scn_budget.SCN_BUDGET,
    place_of_performance.PLACE_OF_PERFORMANCE,
    obbba.OBBBA,
    fydp_outyears.FYDP_OUTYEARS,
    deflators.DEFLATORS,
    # --- Validation ---
    checks.CHECKS,
]
