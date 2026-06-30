"""Merged DDG-51 Executive Summary."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER,
    S_NUM, S_PCT, S_INT, S_LINK_NUM, S_LINK_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.styles import S_ITALIC
from ddg.sheets.kit.tabs import TAB_EXEC_SUMMARY
from ddg.sheets.kit import periods as _periods
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets import ddg_tam as TAM
from ddg.sheets.kit.taxonomy import DOMAINS
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.ddg_program_vendors import ddg_pv_cols
from ddg.sheets.supplier_year_activity import supplier_year_cols
from ddg.sheets.where_to_play import where_to_play_cols
from ddg.sheets.ddg_swbs_rollup import swbs_rollup_cols
from ddg.sheets.ddg_hull_spend_summary import hull_spend_cols

_GROUP = "summary"
_FIRM_FY = _periods.FY
_BRIDGE_FY = (2022, 2023, 2024, 2025)
_OY = _periods.OY
_NCOLS = 8

_SY_PROG = supplier_year_cols("Program")
_SY_FY = supplier_year_cols("Federal FY")
_SY_POS = supplier_year_cols("Positive Supplier $M")
_W_AXIS = where_to_play_cols("Axis")
_W_CODE = where_to_play_cols("Archetype Code")
_W_PROGRAM = where_to_play_cols("Program")
_W_FY = where_to_play_cols("Federal FY")

_TX_REAL = ddg_tx_cols(TX_REAL)
_TX_CONF = ddg_tx_cols("Hull Confidence")
_TX_NARROW = ddg_tx_cols("Narrowing Result")
_TX_LCONF = ddg_tx_cols("Lifecycle Confidence")


def _fy_label(fy: int) -> str:
    return f"FY{fy}" + ("E" if fy > 2025 else "")


def _sam_fy_total(fy: int) -> str:
    return f"=SUM({ddg_pv_cols(f'FY{str(fy)[-2:]} $M')})"


def _wtp(metric: str, code: str) -> str:
    vals = where_to_play_cols(metric)
    match = (f'MATCH(1,INDEX(({_W_AXIS}="D")*({_W_PROGRAM}="DDG-51")'
             f'*({_W_FY}=2025)*({_W_CODE}="{code}"),0),0)')
    return f'=IFERROR(INDEX({vals},{match}),"")'


def _sum_conf(*grades: str) -> str:
    return "+".join(f'SUMIFS({_TX_REAL},{_TX_CONF},"{g}")' for g in grades)


def _sum_narrow(*buckets: str) -> str:
    return "+".join(f'SUMIFS({_TX_REAL},{_TX_NARROW},"{b}")' for b in buckets)


def _sum_lconf(*grades: str) -> str:
    return "+".join(f'SUMIFS({_TX_REAL},{_TX_LCONF},"{g}")' for g in grades)


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_EXEC_SUMMARY, _NCOLS)
    c.caption("DDG-51 addressable TAM + observed first-tier SAM, constant FY2026 $M")
    c.blank(2)

    c.section("§1 - Scope and denominator", _NCOLS)
    c.blank()
    c.write(["Program", "DDG-51 / Arleigh Burke (LI 2122)"], styles=[S_BOLD, S_DEFAULT])
    c.write(["TAM", "Supplier-addressable outsourced new-construction opportunity"], styles=[S_BOLD, S_DEFAULT])
    c.write(["Observed SAM", "Reported first-tier subaward evidence; not the full outsourced-market total."], styles=[S_BOLD, S_DEFAULT])
    c.write(["Bridge caveat", "Observed SAM / TAM is a reporting-and-reach bridge, not market penetration."], styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    c.section("§2 - Addressable DDG-51 TAM", _NCOLS)
    c.blank()
    c.write(["Metric"] + [_fy_label(fy) for fy in _FIRM_FY] + ["Memo"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FIRM_FY) + [S_HEADER_LEFT])
    c.write(["TAM $M"] + [f"={TAM.tam_cell(fy)}" for fy in _FIRM_FY] + [""],
            styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FIRM_FY) + [S_DEFAULT])
    c.write(["BC coefficient"] + [""] * len(_FIRM_FY) + [f"={TAM.applied_coeff_cell()}"],
            styles=[S_DEFAULT] + [S_DEFAULT] * len(_FIRM_FY) + [S_LINK_PCT])
    c.write(["OBBBA overlay"] + [""] * len(_FIRM_FY) + [f"={TAM.obbba_tam_cell()}"],
            styles=[S_DEFAULT] + [S_DEFAULT] * len(_FIRM_FY) + [S_LINK_NUM])
    c.blank()
    c.write(["Outyear outlook"] + [_fy_label(fy) for fy in _OY],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_OY))
    c.write(["Low"] + [f"={TAM.outyear_low_cell(fy)}" for fy in _OY], styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
    c.write(["High"] + [f"={TAM.outyear_high_cell(fy)}" for fy in _OY], styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
    c.blank(2)

    c.section("§3 - Observed SAM / reported supplier activity", _NCOLS)
    c.blank()
    c.write(["Metric"] + [f"FY{fy}" for fy in _BRIDGE_FY] + ["Lifetime", "FY25 active UEIs"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_BRIDGE_FY) + [S_HEADER_LEFT, S_HEADER_LEFT])
    c.write(["Reported subaward $M"] + [_sam_fy_total(fy) for fy in _BRIDGE_FY]
            + [f"=SUM({ddg_pv_cols('Subaward $M')})", f'=COUNTIFS({_SY_PROG},"DDG",{_SY_FY},2025,{_SY_POS},">0")'],
            styles=[S_DEFAULT] + [S_LINK_NUM] * len(_BRIDGE_FY) + [S_LINK_NUM, S_INT])
    c.write(["Observed SAM caveat", "Reported first-tier subaward evidence; not the full outsourced-market total."],
            styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    c.section("§4 - TAM-to-SAM bridge", _NCOLS)
    c.blank()
    c.write(["FY", "TAM $M", "Observed SAM $M", "Observed SAM / TAM"], styles=[S_HEADER_LEFT] * 4)
    for fy in _BRIDGE_FY:
        c.write([fy, f"={TAM.tam_cell(fy)}", _sam_fy_total(fy), lambda r: f'=IFERROR(D{r}/C{r},"")'],
                styles=[S_INT, S_LINK_NUM, S_LINK_NUM, S_PCT])
    c.write(["Bridge uses reported first-tier subawards only; exclusions and retained in-house scope remain outside observed SAM."], styles=[S_ITALIC])
    c.blank(2)

    c.section("§5 - FY2025 where-to-play by capability domain", _NCOLS)
    c.blank()
    c.write(["Domain", "FY25 $M", "Program Share", "Active UEIs", "Parent Top-1", "Parent HHI", "Incumbent $", "Class"],
            styles=[S_HEADER_LEFT] * 8)
    for code, name, _defn in DOMAINS:
        c.write([f"{code}  {name}", _wtp("Net Subaward $M", code), _wtp("Program Share", code),
                 _wtp("Active Suppliers", code), _wtp("Parent Top-1", code), _wtp("Parent HHI", code),
                 _wtp("Incumbent $ %", code), _wtp("Observed Structure", code)],
                styles=[S_DEFAULT, S_LINK_NUM, S_PCT, S_INT, S_PCT, S_NUM, S_PCT, S_DEFAULT])
    c.blank(2)

    c.section("§6 - Coverage / visibility scorecard", _NCOLS)
    c.blank()
    swbs_total = f"SUM({swbs_rollup_cols('Subaward $M')})"
    swbs_grp = swbs_rollup_cols("SWBS Major Group")
    swbs_amt = swbs_rollup_cols("Subaward $M")
    assigned = f"SUM({hull_spend_cols('Assigned Subaward $M')})"
    lifetime = f"SUM({ddg_pv_cols('Subaward $M')})"
    ab_raw = f"({_sum_conf('A', 'B')})"
    cd_raw = f"({_sum_conf('C', 'D')})"
    x_raw = f"({_sum_conf('X')})"
    narrowed_raw = f"({_sum_narrow('Single candidate', '2-3 candidates')})"
    high_med_raw = f"({_sum_lconf('High', 'Medium')})"
    c.write(["Measure", "Value", "Interpretation"], styles=[S_HEADER_LEFT] * 3)
    c.write(["Observed SAM total $M", f"={lifetime}", "Reported DDG first-tier subawards; evidence layer, not full outsourced market."], styles=[S_DEFAULT, S_LINK_NUM, S_DEFAULT])
    c.write(["HII SWBS-classified $M", f"={swbs_total}", "SWBS is HII-Ingalls DDG only; GD-BIW rows carry no SWBS."], styles=[S_DEFAULT, S_LINK_NUM, S_DEFAULT])
    c.write(["SWBS mapped share", f'=IFERROR(1-SUMIFS({swbs_amt},{swbs_grp},"U00")/{swbs_total},"")', "Share of HII SWBS dollars outside the unmapped U00 bucket."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["Exact-hull A/B $M", f"={assigned}", "A/B rows assigned to a single hull."], styles=[S_DEFAULT, S_LINK_NUM, S_DEFAULT])
    c.write(["Exact-hull A/B share", f'=IFERROR({assigned}/{lifetime},"")', "Share of observed SAM that can support hull x lifecycle rollups."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["Family-level C/D share", f'=IFERROR({cd_raw}/1000000/{lifetime},"")', "PIID-family rows: candidate narrowing only, no per-hull allocation."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["Conflict / X share", f'=IFERROR({x_raw}/1000000/{lifetime},"")', "Conflict, multi-hull, or review rows."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["C/D narrowed to 1-3 candidates", f'=IFERROR({narrowed_raw}/{cd_raw},"")', "Share of family-level C/D $ where timing narrows to single or 2-3 candidates."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])
    c.write(["C/D high/medium lifecycle confidence", f'=IFERROR({high_med_raw}/{cd_raw},"")', "Timing-readiness screen; separate from hull confidence."], styles=[S_DEFAULT, S_PCT, S_DEFAULT])

    ws = worksheet(c.rows, cols=[34, 13, 13, 13, 13, 13, 13, 22], tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)

EXECUTIVE_SUMMARY = SheetEntry(TAB_EXEC_SUMMARY, _GROUP, _render)
