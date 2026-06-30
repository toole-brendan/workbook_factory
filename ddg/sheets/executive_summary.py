"""Merged DDG-51 Executive Summary - the one front door.

Replaces the separate TAM and SAM executive summaries with a single answer page:
addressable TAM, observed first-tier reported SAM, a TAM-to-SAM bridge, and the
highest-value where-to-play / hull-visibility callouts. Every value is a live
formula into the model sheets (nothing is hardcoded here).
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER,
    S_NUM, S_PCT, S_INT, S_LINK_NUM, S_LINK_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from sheets._tam_layout import RowCursor
from sheets._tam_italic import S_ITALIC
from sheets import _tam_periods as _periods
from sheets import ddg_tam as TAM
from sheets._tabs import TAB_EXEC_SUMMARY

from sheets._sam_taxonomy import DOMAINS
from sheets.ddg_program_vendors import ddg_pv_cols
from sheets.supplier_year_activity import supplier_year_cols
from sheets.where_to_play import where_to_play_cols
from sheets.ddg_swbs_rollup import swbs_rollup_cols
from sheets.ddg_hull_spend_summary import hull_spend_cols

_GROUP = "summary"
_FIRM_FY = _periods.FY           # FY2022-2027
_BRIDGE_FY = (2022, 2023, 2024, 2025)
_OY = _periods.OY                # FY2028-2031
_NCOLS = 8

_SY_PROG = supplier_year_cols("Program")
_SY_FY = supplier_year_cols("Federal FY")
_SY_POS = supplier_year_cols("Positive Supplier $M")

_W_AXIS = where_to_play_cols("Axis")
_W_CODE = where_to_play_cols("Archetype Code")
_W_PROGRAM = where_to_play_cols("Program")
_W_FY = where_to_play_cols("Federal FY")


def _fy_label(fy: int) -> str:
    return f"FY{fy}" + ("E" if fy > 2025 else "")


def _sam_fy_total(fy: int) -> str:
    return f"=SUM({ddg_pv_cols(f'FY{str(fy)[-2:]} $M')})"


def _wtp(metric: str, code: str) -> str:
    """Live INDEX/MATCH into Where to Play for the FY2025 DDG row of one D-domain."""
    vals = where_to_play_cols(metric)
    match = (
        f'MATCH(1,INDEX(({_W_AXIS}="D")*({_W_PROGRAM}="DDG-51")'
        f'*({_W_FY}=2025)*({_W_CODE}="{code}"),0),0)'
    )
    return f'=IFERROR(INDEX({vals},{match}),"")'


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_EXEC_SUMMARY, _NCOLS)
    c.caption("DDG-51 addressable TAM + observed first-tier SAM, constant FY2026 $M")
    c.blank(2)

    c.section("§1 - Scope and denominator", _NCOLS)
    c.blank()
    c.write(["Program", "DDG-51 / Arleigh Burke (LI 2122)"], styles=[S_BOLD, S_DEFAULT])
    c.write(["TAM", "Supplier-addressable outsourced new-construction opportunity"],
            styles=[S_BOLD, S_DEFAULT])
    c.write(["SAM", "Observed reported first-tier hull-builder subawards"],
            styles=[S_BOLD, S_DEFAULT])
    c.write(["Bridge caveat",
             "Observed SAM / TAM is a reporting-and-reach bridge, not full market penetration."],
            styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    c.section("§2 - Addressable DDG-51 TAM", _NCOLS)
    c.blank()
    c.write(["Metric"] + [_fy_label(fy) for fy in _FIRM_FY] + ["Memo"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FIRM_FY) + [S_HEADER_LEFT])
    c.write(["TAM $M"] + [f"={TAM.tam_cell(fy)}" for fy in _FIRM_FY] + [""],
            styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FIRM_FY) + [S_DEFAULT])
    c.write(["Cumulative TAM, FY2022-27 $M", f"={TAM.cum_tam_cell()}"],
            styles=[S_BOLD, S_LINK_NUM])
    c.write(["BC coefficient"] + [""] * len(_FIRM_FY) + [f"={TAM.applied_coeff_cell()}"],
            styles=[S_DEFAULT] + [S_DEFAULT] * len(_FIRM_FY) + [S_LINK_PCT])
    c.write(["OBBBA overlay"] + [""] * len(_FIRM_FY) + [f"={TAM.obbba_tam_cell()}"],
            styles=[S_DEFAULT] + [S_DEFAULT] * len(_FIRM_FY) + [S_LINK_NUM])
    c.blank()
    c.write(["Outyear outlook"] + [_fy_label(fy) for fy in _OY],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_OY))
    c.write(["Low"] + [f"={TAM.outyear_low_cell(fy)}" for fy in _OY],
            styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
    c.write(["High"] + [f"={TAM.outyear_high_cell(fy)}" for fy in _OY],
            styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
    c.blank(2)

    c.section("§3 - Observed SAM / reported supplier activity", _NCOLS)
    c.blank()
    c.write(["Metric"] + [f"FY{fy}" for fy in _BRIDGE_FY] + ["Lifetime", "FY25 active UEIs"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_BRIDGE_FY) + [S_HEADER_LEFT, S_HEADER_LEFT])
    c.write(
        ["Reported subaward $M"]
        + [_sam_fy_total(fy) for fy in _BRIDGE_FY]
        + [f"=SUM({ddg_pv_cols('Subaward $M')})",
           f'=COUNTIFS({_SY_PROG},"DDG",{_SY_FY},2025,{_SY_POS},">0")'],
        styles=[S_DEFAULT] + [S_LINK_NUM] * len(_BRIDGE_FY) + [S_LINK_NUM, S_INT],
    )
    c.blank(2)

    c.section("§4 - TAM-to-SAM bridge", _NCOLS)
    c.blank()
    c.write(["FY", "TAM $M", "Observed SAM $M", "Observed SAM / TAM"], styles=[S_HEADER_LEFT] * 4)
    for fy in _BRIDGE_FY:
        c.write([fy, f"={TAM.tam_cell(fy)}", _sam_fy_total(fy),
                 lambda r: f'=IFERROR(D{r}/C{r},"")'],
                styles=[S_INT, S_LINK_NUM, S_LINK_NUM, S_PCT])
    c.write(["Bridge uses reported first-tier subawards only; exclusions and retained "
             "in-house scope remain outside observed SAM."], styles=[S_ITALIC])
    c.blank(2)

    c.section("§5 - FY2025 where-to-play by capability domain", _NCOLS)
    c.blank()
    c.write(["Domain", "FY25 $M", "Program Share", "Active UEIs", "Parent Top-1",
             "Parent HHI", "Incumbent $", "Class"], styles=[S_HEADER_LEFT] * 8)
    for code, name, _defn in DOMAINS:
        c.write([f"{code}  {name}",
                 _wtp("Net Subaward $M", code),
                 _wtp("Program Share", code),
                 _wtp("Active Suppliers", code),
                 _wtp("Parent Top-1", code),
                 _wtp("Parent HHI", code),
                 _wtp("Incumbent $ %", code),
                 _wtp("Observed Structure", code)],
                styles=[S_DEFAULT, S_LINK_NUM, S_PCT, S_INT, S_PCT, S_NUM, S_PCT, S_DEFAULT])
    c.blank(2)

    c.section("§6 - Hull / SWBS visibility", _NCOLS)
    c.blank()
    swbs_total = f"SUM({swbs_rollup_cols('Subaward $M')})"
    swbs_grp = swbs_rollup_cols("SWBS Major Group")
    swbs_amt = swbs_rollup_cols("Subaward $M")
    assigned = f"SUM({hull_spend_cols('Assigned Subaward $M')})"
    lifetime = f"SUM({ddg_pv_cols('Subaward $M')})"
    c.write(["Measure", "Value", "Interpretation"], styles=[S_HEADER_LEFT] * 3)
    c.write(["HII SWBS-classified $M", f"={swbs_total}",
             "SWBS is HII-Ingalls DDG only; GD-BIW rows carry no SWBS."],
            styles=[S_DEFAULT, S_LINK_NUM, S_DEFAULT])
    c.write(["SWBS mapped share",
             f'=IFERROR(1-SUMIFS({swbs_amt},{swbs_grp},"U00")/{swbs_total},"")',
             "Share of HII SWBS dollars outside the unmapped U00 bucket."],
            styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["Exact-hull assigned $M", f"={assigned}",
             "A/B rows assigned to a single hull; C/D family-level dollars are not allocated."],
            styles=[S_DEFAULT, S_LINK_NUM, S_DEFAULT])
    c.write(["Exact-hull share of observed SAM", f'=IFERROR({assigned}/{lifetime},"")',
             "Share of total DDG observed SAM that is exact-hull attributable."],
            styles=[S_DEFAULT, S_PCT, S_DEFAULT])

    ws = worksheet(
        c.rows,
        cols=[34, 13, 13, 13, 13, 13, 13, 22],
        tab_color=group_color(_GROUP),
        with_gutter=True,
        show_outline_symbols=False,
    )
    return WorksheetSpec(ws)


EXECUTIVE_SUMMARY = SheetEntry(TAB_EXEC_SUMMARY, _GROUP, _render)
