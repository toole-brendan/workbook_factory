"""fydp_outyears - the "FYDP Outyears" data tab (combined, all three programs).

PB2027 P-40 Resource Summary for Virginia (2013), Columbia (1045) and DDG-51 (2122):
the FYDP grid FY2025-FY2031, loaded from extracted/fydp_outyears.csv. FY2028-FY2031
are the budget-request outyears each program's TAM tab projects implied Outsourced BC
against; FY2025-FY2027 are carried so the exhibit ties to SCN Budget (FY2027 Total =
P-5c Total Ship Estimate). Then-year, with a constant-FY2026 block (x Green Book
deflator). Refresh at PB2028: re-tie FY2027 gross to SCN Budget and re-base the outyears.

Promoted accessors:
  fydp_gross_then_cell(li, fy)    then-year Gross/Weapon System Cost cell
  fydp_gross_cell(li, fy)         constant-FY2026 gross cell (the TAM tabs read this)
  fydp_qty_cell(li, fy)           procurement-quantity cell
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_BOLD, S_DEFAULT, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_NUM_INPUT,
    S_INT_INPUT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from sheets._tam_cuts import load_rows, as_float
from sheets._tam_layout import RowCursor
from sheets._tam_factor import S_FACTOR
from sheets._tabs import TAB_FYDP
from sheets.tam_deflators import deflator_factor_cell

_GROUP = "data"
_FY = [2025, 2026, 2027, 2028, 2029, 2030, 2031]
_FY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_FY)}     # C..I
_NCOLS = 1 + len(_FY)
_HDR_FY = [S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY)
_PROGRAMS = [(2122, "DDG-51")]   # DDG-51-only slice
_METRIC = [("gross_then_$M", "Gross / Weapon System Cost, then-year $M", S_BOLD),
           ("qty", "Procurement quantity (ships)", S_DEFAULT),
           ("net_proc_$M", "Net Procurement (P-1), then-year $M (memo)", S_DEFAULT),
           ("toa_$M", "Total Obligation Authority, then-year $M (memo)", S_DEFAULT)]


def _load():
    out: dict[int, dict[int, dict]] = {}
    for r in load_rows("fydp_outyears"):
        li, fy = int(r["li"]), int(r["fy"])
        out.setdefault(li, {})[fy] = r
    return out


def _make():
    data = _load()
    then: dict = {}    # then[li] = gross_then row
    qty: dict = {}     # qty[li]  = qty row
    const: dict = {}   # const[li] = gross_const row
    c = RowCursor(2)
    c.title(TAB_FYDP, _NCOLS)
    c.caption("PB2027 P-40 gross spend, FY2025-31")
    c.blank(2)
    c.section("§1 - PB2027 P-40 Resource Summary (then-year $M)", _NCOLS)
    c.blank()
    c.write(["Field", "Value"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    c.write(["Exhibit", "PB2027 Navy P-40 (1611N SCN)"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.write(["Period", "FY2025-31; FY2027 = Total (Base+OOC), FY2028-31 = outyears"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    sec = 2
    for li, name in _PROGRAMS:
        c.subsection(f"§{sec} - {name} (LI {li}), then-year $M", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        for key, label, base_style in _METRIC:
            vstyle = S_INT_INPUT if key == "qty" else S_NUM_INPUT
            vals = [label] + [as_float((data.get(li, {}).get(fy, {}) or {}).get(key)) for fy in _FY]
            row = c.write(vals, styles=[base_style] + [vstyle] * len(_FY))
            if key == "gross_then_$M":
                then[li] = row
            elif key == "qty":
                qty[li] = row
        c.blank()
        sec += 1
    c.blank()

    c.section("§3 - Constant FY2026 $M", _NCOLS)
    c.blank()
    c.write(["Class"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
    # Local deflator driver: link each FY's factor from Deflators ONCE; the class
    # rows below multiply by this row instead of one cross-sheet ref per cell.
    fac_r = c.write(["Constant-FY2026 factor (then-year x this; from Deflators)"]
                    + [f"={deflator_factor_cell(fy)}" for fy in _FY],
                    styles=[S_BOLD] + [S_FACTOR] * len(_FY))
    for li, name in _PROGRAMS:
        vals = [f"{name} (LI {li})"] + [f"={_FY_COL[fy]}{then[li]}*{_FY_COL[fy]}${fac_r}"
                                        for fy in _FY]
        const[li] = c.write(vals, styles=[S_BOLD] + [S_NUM] * len(_FY))

    def _chk(li, fy):
        if li not in then:
            raise ValueError(f"Unknown LI {li!r}")
        if fy not in _FY_COL:
            raise ValueError(f"FY {fy!r} outside {_FY!r}")

    def fydp_gross_then_cell(li, fy):
        _chk(li, fy); return f"'{TAB_FYDP}'!{_FY_COL[fy]}{then[li]}"

    def fydp_gross_cell(li, fy):
        _chk(li, fy); return f"'{TAB_FYDP}'!{_FY_COL[fy]}{const[li]}"

    def fydp_qty_cell(li, fy):
        _chk(li, fy); return f"'{TAB_FYDP}'!{_FY_COL[fy]}{qty[li]}"

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=[48, 12, 12, 12, 12, 12, 12, 12],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False)
        return WorksheetSpec(ws)

    return (SheetEntry(TAB_FYDP, _GROUP, render),
            fydp_gross_then_cell, fydp_gross_cell, fydp_qty_cell)


(FYDP_OUTYEARS, fydp_gross_then_cell, fydp_gross_cell, fydp_qty_cell) = _make()
