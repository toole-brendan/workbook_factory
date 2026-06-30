"""deflators - the "Deflators" data tab (one module = one sheet).

Renders the Green Book Procurement TOA deflator series (FY2025 = 100) and the rebased
constant-FY2026 factor, loaded from extracted/deflators.csv (generated from
workbook_core.deflators by build_extracted.py). The factor is a real numeric value
shown to two decimals (S_FACTOR), so the budget sheets' ``then-year * factor`` is a
plain numeric multiply - the displayed factor is exactly the multiplier used.

Promoted accessor:
  deflator_factor_cell(fy) -> 'Deflators'!<factor-col><row>  (a live cell the budget
                              sheets multiply by, not a baked constant)
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM_INPUT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from workbook_master_tam.sheets._cuts import load_rows
from workbook_master_tam.sheets._layout import RowCursor
from workbook_master_tam.sheets._factor import S_FACTOR
from workbook_master_tam.sheets._tabs import TAB_DEFLATORS
from workbook_master_tam.sheets import _widths as W

_GROUP = "data"
_NCOLS = 4
_FAC_COL = col_letter(3)   # B=FY label, C=index, D=factor, E=basis


def _make():
    rows = load_rows("deflators")
    fac_row: dict[int, int] = {}
    c = RowCursor(2)
    c.title(TAB_DEFLATORS, _NCOLS)
    c.caption("Procurement deflators rebased to FY2026")
    c.blank(2)
    c.section("§1 - Procurement deflators", _NCOLS)
    c.blank()
    c.write(["FY", "Procurement deflator (FY2025=100)", "Factor to constant FY2026 $", "Basis"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_LEFT])
    for r in rows:
        fy = int(r["fy"])
        # factor is a real float shown to 2 decimals (S_FACTOR) - a plain numeric multiply
        fac_row[fy] = c.write(
            [f"FY{fy}", float(r["procurement_index_fy2025_100"]),
             float(r["factor_const_fy2026"]), r["basis"]],
            styles=[S_BOLD, S_NUM_INPUT, S_FACTOR, S_DEFAULT])
    c.blank(2)
    c.section("§2 - Source", _NCOLS)
    c.blank()
    c.write(["Series", "Source"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    c.write(["Procurement TOA",
             "OSD National Defense Budget Estimates for FY2025 (Green Book), Table 5-4 "
             "Procurement TOA, FY2025=100; rebased to FY2026=1.000"],
            styles=[S_BOLD, S_DEFAULT])
    c.write(["FY2030-31",
             "Extrapolated at 2.1%/yr (Green Book Table 5-3 steady-state purchases inflation)"],
            styles=[S_BOLD, S_DEFAULT])

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=[10, W.W_TEXT, 30, 28],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False)
        return WorksheetSpec(ws)

    def deflator_factor_cell(fy: int) -> str:
        if fy not in fac_row:
            raise ValueError(f"FY {fy!r} not in Deflators tab")
        return f"'{TAB_DEFLATORS}'!{_FAC_COL}{fac_row[fy]}"

    return SheetEntry(TAB_DEFLATORS, _GROUP, render), deflator_factor_cell


(DEFLATORS, deflator_factor_cell) = _make()
