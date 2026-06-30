"""swbs_coverage - visible applicability bridge for SWBS-based DDG cuts."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_INT, S_PCT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.styles import S_ITALIC
from ddg.sheets.kit.tabs import TAB_SWBS_COVERAGE
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols

_GROUP = "model"
_NCOLS = 5
_COLS = [34, 54, 14, 12, 12]

_BUILDER = ddg_tx_cols("Builder")
_SUBSYS = ddg_tx_cols("SWBS Subsystem")
_REAL = ddg_tx_cols(TX_REAL)
_TOTAL = f"SUM({_REAL})/1000000"
_HII = f'SUMIFS({_REAL},{_BUILDER},"HII-Ingalls")/1000000'


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_SWBS_COVERAGE, _NCOLS)
    c.caption("Where SWBS evidence applies: HII mapped, HII unmapped, and non-HII not-classified dollars.")
    c.blank(2)

    c.section("§1 - SWBS applicability bridge", _NCOLS)
    c.write(["SWBS is an HII-Ingalls work-item-code method.  GD-BIW rows are outside the method, not zero-spend."], styles=[S_ITALIC])
    c.blank()
    c.write(["Bucket", "Meaning", "Subaward $M", "Records", "% of DDG $"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])

    total_r = c.write(["Total observed DDG SAM", "All reported first-tier DDG subawards in the workbook.",
                       f'={_TOTAL}', f'=COUNT({_REAL})', '=1'],
                      styles=[S_BOLD, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.write(["HII-Ingalls SWBS universe", "Rows eligible for HII work-item-code SWBS classification.",
             f'={_HII}', f'=COUNTIFS({_BUILDER},"HII-Ingalls")', lambda r: f'=D{r}/D{total_r}'],
            styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.write(["HII mapped SWBS", "HII rows with a mapped SWBS subsystem outside U00.",
             f'=SUMIFS({_REAL},{_BUILDER},"HII-Ingalls",{_SUBSYS},"<>U00",{_SUBSYS},"<>")/1000000',
             f'=COUNTIFS({_BUILDER},"HII-Ingalls",{_SUBSYS},"<>U00",{_SUBSYS},"<>")',
             lambda r: f'=D{r}/D{total_r}'],
            styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.write(["HII U00 unmapped", "HII rows present, but the work-item code does not map to a known SWBS subsystem.",
             f'=SUMIFS({_REAL},{_BUILDER},"HII-Ingalls",{_SUBSYS},"U00")/1000000',
             f'=COUNTIFS({_BUILDER},"HII-Ingalls",{_SUBSYS},"U00")',
             lambda r: f'=D{r}/D{total_r}'],
            styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.write(["Non-HII not classified", "GD-BIW / other-builder rows outside the HII SWBS method.",
             f'=SUMIFS({_REAL},{_BUILDER},"<>HII-Ingalls")/1000000',
             f'=COUNTIFS({_BUILDER},"<>HII-Ingalls")', lambda r: f'=D{r}/D{total_r}'],
            styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])

    c.blank(2)
    c.section("§2 - Reader guardrail", _NCOLS)
    c.write(["Use SWBS views for ship-system visibility where HII evidence exists.  Do not interpret non-HII not-classified dollars as absence of ship-system work."], styles=[S_ITALIC])

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


SWBS_COVERAGE = SheetEntry(TAB_SWBS_COVERAGE, _GROUP, _render)
