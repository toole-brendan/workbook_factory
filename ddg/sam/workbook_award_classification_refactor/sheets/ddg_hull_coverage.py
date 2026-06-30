"""ddg_hull_coverage - how much of the DDG subaward universe is pinned to a hull, by grade.

The management coverage view: one row per hull-confidence grade (A..X) plus a TOTAL, with the
subaward $, record count, and share of the DDG total. Every measure is a live SUMIFS / COUNTIFS over
the DDG Subaward Transactions leaf keyed on the materialized `Hull Confidence` column, so the split
between EXACT (A/B, the only grades that roll up to a hull), INFERRED (C/D, family-level), and
CONFLICT (X) attribution is always current. It exists so the assigned-hull roll-ups are never
mistaken for the whole DDG market - most subaward $ is family-level, not exact-hull.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_NUM, S_INT, S_PCT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._widths import (
    header_styles, W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_RATIO,
)
from workbook_award_classification_refactor.sheets._fiscal import TX_REAL
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_COVERAGE
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)

_GROUP = "model"
_NCOLS = 5
_COLS = [W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_RATIO]

_CONF = ddg_tx_cols("Hull Confidence")
_REAL = ddg_tx_cols(TX_REAL)

# (grade, what it means). The order is the coverage ladder: exact -> inferred -> conflict.
_GRADES = [
    ("A", "Official exact - single-ship PIID"),
    ("B", "Direct subaward text - in-family"),
    ("C", "Prime requirement text only"),
    ("D", "PIID family only"),
    ("X", "Conflict / multi-hull (review)"),
]
_HDRS = ["Grade", "Evidence", "Subaward $M", "Records", "% of DDG $"]
_NUMERIC = {"Subaward $M", "Records", "% of DDG $"}


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_HULL_COVERAGE, _NCOLS)
    c.caption("Exact (A/B) vs inferred (C/D) vs conflict (X) hull attribution, by subaward $.")
    c.blank(2)
    c.section("§1 - Hull attribution coverage", _NCOLS)
    c.blank()
    hdr = c.write(_HDRS, styles=header_styles(_HDRS, center_headers=_NUMERIC))
    first = hdr + 1
    total = first + len(_GRADES)        # the TOTAL row, referenced by each grade's % cell
    for i, (g, label) in enumerate(_GRADES):
        r = first + i
        c.write([g, label,
                 f'=SUMIFS({_REAL},{_CONF},"{g}")/1000000',
                 f'=COUNTIFS({_CONF},"{g}")',
                 f"=D{r}/D{total}"],
                styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.total(["TOTAL", "All DDG subawards",
             f"=SUM(D{first}:D{total - 1})",
             f"=SUM(E{first}:E{total - 1})",
             f"=D{total}/D{total}"],
            styles=[S_BOLD, S_DEFAULT, S_NUM, S_INT, S_PCT], n_cols=_NCOLS)

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


DDG_HULL_COVERAGE = SheetEntry(TAB_HULL_COVERAGE, _GROUP, _render)
