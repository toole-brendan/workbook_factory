"""deflators - the "Deflators" tab: Green Book Procurement TOA index, rebased to FY2026.

A small back-of-book reference table: one row per fiscal-year bin used by the program-vendor
$ columns (≤FY12 + FY2013..FY2026). Each row carries the OSD Green Book Procurement TOA
deflator (FY2025=100, a hardcoded blue input) and a derived constant-FY2026 conversion factor
(a live formula, = 102.10 / that row's index). The program-vendor sheets multiply each per-FY
nominal $ roll-up by the matching factor cell here to render constant FY2026 dollars - the
calendar->FY->deflator conversion lives entirely in formulas, with no change to the raw
transaction sheets.

Source: OSD National Defense Budget Estimates for FY2025 ("Green Book"), Table 5-4 "DoD
Deflators - TOA by Public Law Title", Procurement column (FY2025=100; base rebased to
FY2026=102.10). SCN/procurement subawards inherit the Procurement deflator. This is a
PROJECT-LOCAL table (extended back to FY2013, which the shared workbook_core.deflators - scoped
to FY2022..FY2031 budget years - does not cover); workbook_core.deflators is left untouched.
The ≤FY12 bin uses the FY2002 index, the year of the sole pre-FY2013 record (2001-10-22 -> FY2002).

Promoted accessor (imported by the program-vendor sheets):
  deflator_factor_cell(fy_key) -> "'Deflators'!$D$<row>" for fy_key in
  {"≤FY12","FY2013",...,"FY2026"} - the absolute factor cell for that fiscal-year bin.
"""
from __future__ import annotations

import re

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._fiscal import FY_BIN_KEYS as _FY_ROW_ORDER
from workbook_award_classification_refactor.sheets._tabs import TAB_DEFLATORS
from workbook_award_classification_refactor.sheets._widths import (
    W_FY, W_TEXT_WIDE,
)

# FY (text) | Procurement TOA (FY2025=100, blue input) | Factor to FY2026 $ (formula) | Basis (text)
# Displayed headers are shortened (Procurement Index / FY26 Factor), so the columns size to the
# label, not the verbose canonical name.
_WIDTHS = [W_FY, 17, 12, W_TEXT_WIDE]

# Row order MUST match extracted/deflators.csv. The FY2026 base-index row is DERIVED from the
# first data row + the FY2026 position (not a hardcoded row or base number), so re-basing to a
# different year is a one-row data edit, not a formula change. First data row of a make_flat_sheet
# WITH an intro caption: title banner (2) -> intro (3) -> blank x2 -> §1 banner (6) -> blank ->
# header (8) -> data (9); asserted against the rendered range below so a layout change fails loudly.
# Row order = _fiscal.FY_BIN_KEYS (the single FY-axis source), MUST match extracted/deflators.csv.
_FIRST_DATA_ROW = 9
_IDX_COL = "C"                                                  # Procurement TOA input column
_FY2026_ROW = _FIRST_DATA_ROW + _FY_ROW_ORDER.index("FY2026")   # the constant-FY2026 base cell

# The factor is a live full-precision formula: the FY2026 base index / this row's index. Black
# derived cell; the displayed value equals what the program-vendor $ multiply by.
_FORMULAS = {
    "Factor to FY2026 $": lambda r: f"=${_IDX_COL}${_FY2026_ROW}/${_IDX_COL}{r}",
}

DEFLATORS, deflators_cols = make_flat_sheet(
    tab=TAB_DEFLATORS, group="inputs",
    csv_name="deflators", table_name="Deflators",
    banner="§1 - Procurement deflators",
    intro="Green Book Procurement TOA index and FY2026 conversion factor.",
    widths=_WIDTHS,
    float_cols=["Procurement TOA (FY2025=100)", "Factor to FY2026 $"],
    input_cols=["Procurement TOA (FY2025=100)"],   # editable Green Book index -> pale-yellow fill
    input_fill=True,
    formula_cols=_FORMULAS,                          # derived factor -> black formula
    display_headers={
        "Procurement TOA (FY2025=100)": "Procurement Index",
        "Factor to FY2026 $": "FY26 Factor",
    },
)

# --- promoted per-FY factor-cell accessor --------------------------------------------------
# Parse the factor column + first data row from the rendered range, and assert the first data row
# and index column match the assumptions the factor formula was built on (above) - so a banner/
# intro layout change or a column reorder fails the build rather than silently mis-referencing the
# FY2026 base cell.
_FAC_RANGE = deflators_cols("Factor to FY2026 $")    # e.g. "'Deflators'!$D$9:$D$23"
_FCOL = re.search(r"!\$([A-Z]+)\$", _FAC_RANGE).group(1)
_FFIRST = int(re.search(r"\$(\d+):", _FAC_RANGE).group(1))
_IDX_RANGE = deflators_cols("Procurement TOA (FY2025=100)")
assert _FFIRST == _FIRST_DATA_ROW, (_FFIRST, _FIRST_DATA_ROW)
assert f"!${_IDX_COL}$" in _IDX_RANGE, (_IDX_COL, _IDX_RANGE)


def deflator_factor_cell(fy_key: str) -> str:
    """Absolute factor cell on the Deflators tab for `fy_key` (≤FY12 / FY2013 .. FY2026)."""
    return f"'{TAB_DEFLATORS}'!${_FCOL}${_FFIRST + _FY_ROW_ORDER.index(fy_key)}"
