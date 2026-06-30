"""place_of_performance - the "Place of Performance" data tab (combined, all programs).

The DoD contract-award announcements - the second key TAM variable - as one native
Excel table behind a coefficients headline, loaded from extracted/place_of_performance.csv.
Every row is a gated, BC-eligible, class-attributable announcement (GFE-directed scope
is dropped here; see Methodology). The announced construction MASTERS live here as rows
too (Virginia Block V, Columbia Build I, the DDG MYP masters) - they are themselves DoD
award announcements - each carrying its source citation; this is the single home for all
place-of-performance data (none of it sits in Assumptions).

The applied BC supplier coefficient = dollar-weighted (other-US + foreign) over the
DDG-51 BC-stream rows (master + disclosed): DDG-51 ~25.3% (MYP-corrected, FY23-27),
DDG FY2022 ~22% (FY18-22 vintage masters).

Promoted accessors (consumed by the DDG-51 TAM tab):
  ddg_bc_coeff_cell, ddg_bc_coeff_fy22_cell
  ddg_disclosed_coeff_ref_cell   (reference)
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_NUM_INPUT, S_PCT,
    S_PCT_INPUT, S_INT_INPUT,
)
from workbook_core.tables import WorksheetSpec, ExcelTable, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.cuts import load_rows, as_float, as_int
from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.tabs import TAB_POP

_GROUP = "data"
_HEADERS = ["Program", "Date", "PIID", "Prime", "Work Type", "Stream", "Master",
            "FY18-22 vintage", "$M", "Prime %", "Co-prime %", "Other US %",
            "Foreign %", "Source"]
_NC = len(_HEADERS)   # 14
_COL = {"program": 1, "date": 2, "piid": 3, "prime": 4, "work_type": 5, "stream": 6,
        "master": 7, "vintage": 8, "dollar": 9, "prime_pct": 10, "coprime_pct": 11,
        "other": 12, "foreign": 13, "source": 14}
# title(2)+italic(3)+2 blanks+§1 banner(6)+blank+headline(8..17)+2 blanks -> body at 20
# (DDG-51-only slice: the Virginia/Columbia BC and submarine AP/LLTM coeff rows are gone.)
_DATA_BASE = 20


def _build_table(base: int):
    rows = load_rows("place_of_performance")
    c = RowCursor(base)
    c.section("§2 - Award corpus", _NC)
    c.blank()
    header_row = c.write(_HEADERS, styles=[S_HEADER_LEFT] * 6 + [S_HEADER_CENTER] * 7 + [S_HEADER_LEFT])
    first_data = c.at()
    # master / FY18-22 vintage are 0/1 flags -> integer style (not the 1-decimal $ style)
    rs = ([S_DEFAULT] * 6 + [S_INT_INPUT, S_INT_INPUT, S_NUM_INPUT]
          + [S_PCT_INPUT] * 4 + [S_DEFAULT])
    for r in rows:
        c.write([r["program"], r["action_date"], r["piid"], r["prime"], r["work_type"],
                 r["stream"], as_int(r["master"]), as_int(r["vintage"]), as_float(r["dollar_m"]),
                 as_float(r["prime_pct"]), as_float(r["coprime_pct"]),
                 as_float(r["other_us_pct"]), as_float(r["foreign_pct"]), r["source"]],
                styles=rs)
    last_data = c.at() - 1
    table = ExcelTable(name="tbl_pop_corpus",
                       ref=f"B{header_row}:{col_letter(_NC)}{last_data}", headers=_HEADERS)
    return c.rows, c.at(), first_data, last_data, table


_T_ROWS, _T_AFTER, _FIRST, _LAST, _TABLE = _build_table(_DATA_BASE)


def _rng(key: str) -> str:
    col = col_letter(_COL[key])
    return f"'{TAB_POP}'!{col}{_FIRST}:{col}{_LAST}"


def _coeff_cells(mask: str) -> list:
    """The three visible, independently-auditable cells for one coefficient row:
    Eligible $M (denominator) | Supplier $M (numerator) | Coefficient = D/C. Same
    $-weighted SUMPRODUCT as before, just split so the numerator and denominator are
    readable cells instead of one opaque ratio. Coefficient reads its own row's C/D."""
    dol = _rng("dollar")
    eligible = f"=SUMPRODUCT({mask}*{dol})"
    supplier = f'=SUMPRODUCT({mask}*{dol}*({_rng("other")}+{_rng("foreign")}))'
    return [eligible, supplier, lambda r: f'=IF(C{r}=0,"",D{r}/C{r})']


_BC = f'({_rng("stream")}="BC")'
_AP = f'({_rng("stream")}="AP_LLTM")'
_CUR = f'({_rng("vintage")}=0)'      # current window (excludes the DDG FY18-22 masters)
_FY18 = f'({_rng("vintage")}=1)'     # the DDG FY18-22 vintage masters
_DISC = f'({_rng("master")}=0)'      # disclosed-only (masters excluded)


def _prog(name: str) -> str:
    return f'({_rng("program")}="{name}")'


def _build_headline(base: int):
    P: dict = {}
    c = RowCursor(base)
    _hdr = ["Basis", "Eligible $M", "Supplier $M", "Coefficient"]
    _hsty = [S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER]
    c.subsection("§1a - Applied coefficients", 7)
    c.blank()
    c.write(_hdr, styles=_hsty)
    P["ddg"] = c.write(["DDG-51 BC, FY23-27"]
                       + _coeff_cells(f"{_prog('DDG-51')}*{_BC}*{_CUR}"),
                       styles=[S_BOLD, S_NUM, S_NUM, S_PCT])
    P["ddg22"] = c.write(["DDG-51 BC, FY2022"]
                         + _coeff_cells(f"{_prog('DDG-51')}*{_BC}*{_FY18}"),
                         styles=[S_BOLD, S_NUM, S_NUM, S_PCT])
    c.blank()
    c.subsection("§1b - Reference coefficients", 7)
    c.blank()
    c.write(_hdr, styles=_hsty)
    P["ddg_disc"] = c.write(["DDG-51 disclosed"]
                            + _coeff_cells(f"{_prog('DDG-51')}*{_BC}*{_CUR}*{_DISC}"),
                            styles=[S_DEFAULT, S_NUM, S_NUM, S_PCT])
    return c.rows, c.at(), P


_H_ROWS, _H_AFTER, _HP = _build_headline(8)


def ddg_bc_coeff_cell() -> str: return f"'{TAB_POP}'!E{_HP['ddg']}"
def ddg_bc_coeff_fy22_cell() -> str: return f"'{TAB_POP}'!E{_HP['ddg22']}"
def ddg_disclosed_coeff_ref_cell() -> str: return f"'{TAB_POP}'!E{_HP['ddg_disc']}"


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_POP, _NC)
    c.caption("Award place of performance and supplier coefficients")
    c.blank(2)
    c.section("§1 - Supplier coefficients", 7)
    c.blank()
    assert c.at() == 8, f"headline base mismatch: {c.at()} != 8"
    c.feed(_H_ROWS, _H_AFTER)
    c.blank(2)
    assert c.at() == _DATA_BASE, f"corpus base mismatch: {c.at()} != {_DATA_BASE}"
    c.feed(_T_ROWS, _T_AFTER)
    ws = worksheet(
        c.rows,
        cols=[20, 12, 18, 24, 18, 10, 8, 13, 12, 10, 11, 10, 10, 52],
        tab_color=group_color(_GROUP), with_gutter=True,
        show_outline_symbols=False)
    return WorksheetSpec(ws, tables=[_TABLE])


PLACE_OF_PERFORMANCE = SheetEntry(TAB_POP, _GROUP, _render)
