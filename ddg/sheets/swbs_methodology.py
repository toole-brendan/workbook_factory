"""swbs_methodology - how SWBS evidence is applied in the DDG SAM workbook."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets._layout import RowCursor
from ddg.sheets._italic import S_ITALIC
from ddg.sheets._tabs import (
    TAB_SWBS_METHOD, TAB_DDG_TX, TAB_SWBS_CROSSWALK, TAB_SWBS_COVERAGE,
    TAB_SWBS_ROLLUP, TAB_HULL_SWBS, TAB_VENDOR_HULL_SWBS,
)

_GROUP = "guide"
_NCOLS = 2
_COLS = [34, 84]


def _kv(c: RowCursor, topic: str, detail: str) -> int:
    return c.write([topic, detail], styles=[S_BOLD, S_DEFAULT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_SWBS_METHOD, _NCOLS)
    c.caption("How HII work-item evidence becomes Ship Work Breakdown Structure cuts.")
    c.blank(2)

    c.section("§1 - Scope", _NCOLS)
    c.write(["SWBS is a transaction-level application layer, not a supplier archetype."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Question", "Which ship system does a DDG subaward support?")
    _kv(c, "Eligible evidence", "HII-Ingalls DDG work-item codes joined to the HII SWBS crosswalk.")
    _kv(c, "Not eligible", "GD-BIW rows carry no comparable HII work-item code, so they are not SWBS-classified rather than zero-spend.")
    _kv(c, "Unmapped HII", "HII rows with no crosswalk match land in U00, the unmapped evidence bucket.")
    c.blank(2)

    c.section("§2 - Application rule", _NCOLS)
    c.write([f"The live formulas sit on '{TAB_DDG_TX}'."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Match once", "Each transaction uses one hidden SWBS Match Row helper to match HII Work-Item Code into the crosswalk.")
    _kv(c, "Return values", "SWBS Subsystem, SWBS display label and SWBS basis then INDEX the matched crosswalk row.")
    _kv(c, "Builder gate", "The formulas deliberately return n/a or blank for non-HII-Ingalls rows before any crosswalk lookup.")
    _kv(c, "Downstream use", "Roll-ups SUMIFS over the transaction sheet's live SWBS Subsystem / SWBS values, so crosswalk edits flow through the workbook.")
    c.blank(2)

    c.section("§3 - Read order", _NCOLS)
    c.write(["Read applicability before interpreting any SWBS cut."], styles=[S_ITALIC])
    c.blank()
    c.write(["Sheet", "Role"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for sheet, role in [
        (TAB_SWBS_COVERAGE, "management coverage view: HII mapped / HII U00 / non-HII not-classified"),
        (TAB_SWBS_ROLLUP, "SWBS subsystem roll-up across HII-Ingalls DDG rows"),
        (TAB_HULL_SWBS, "HII hull x SWBS major-group matrix for exact-hull rows"),
        (TAB_VENDOR_HULL_SWBS, "supplier x hull x SWBS subsystem drill-down"),
        (TAB_SWBS_CROSSWALK, "curated HII work-item code to SWBS mapping table"),
    ]:
        c.write([sheet, role], styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    c.section("§4 - Guardrail", _NCOLS)
    c.write(["SWBS supports ship-system visibility where evidence exists.  It should not be used as a complete DDG market split because GD-BIW rows are intentionally outside the HII work-item-code method."], styles=[S_ITALIC])

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


SWBS_METHODOLOGY = SheetEntry(TAB_SWBS_METHOD, _GROUP, _render)
