"""ddg_cd_lifecycle_coverage - how far build-timing narrows the family-level (C/D) DDG subaward $.

The management view of the C/D timing analysis: §1 buckets the family-level subaward $ by narrowing
result (Single candidate / 2-3 / Still family-level / Exception / No schedule data); §2 by the
Lifecycle Confidence grade. Every measure is a live SUMIFS / COUNTIFS over the DDG Subaward
Transactions leaf keyed on the materialized `Narrowing Result` / `Lifecycle Confidence` columns (which
are populated for C/D rows only), so both tables total to the same family-level universe and stay
current. It exists so the timing-narrowing is never over-read: most C/D $ stays at 4+ candidate hulls;
timing meaningfully narrows only a minority - and it narrows the candidate SET, never splitting a
dollar across hulls (the wall, briefing §6).
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_NUM, S_INT, S_PCT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._widths import (
    header_styles, W_STATUS, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_RATIO,
)
from workbook_award_classification_refactor.sheets._fiscal import TX_REAL
from workbook_award_classification_refactor.sheets._tabs import TAB_CD_LC_COVERAGE
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)

_GROUP = "model"
_NCOLS = 5
_COLS = [W_STATUS, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_RATIO]

_NARROW = ddg_tx_cols("Narrowing Result")
_LCONF = ddg_tx_cols("Lifecycle Confidence")
_REAL = ddg_tx_cols(TX_REAL)

# (narrowing-result bucket, what it means). MUST match scripts/_lifecycle.NR_* (the materialized
# values); _integrity.assert_lifecycle_labels_known fails the build on any drift.
_BUCKETS = [
    ("Single candidate", "Timing narrows the family to one hull"),
    ("2-3 candidates", "Narrowed to 2-3 hulls in build at the time"),
    ("Still family-level", "4+ hulls plausible - timing barely narrows"),
    ("Exception (no window match)", "Date outside every candidate hull's build window"),
    ("No schedule data", "No family hull carries milestone dates yet"),
]
# (lifecycle-confidence grade, what it means). MUST match scripts/_lifecycle.LC_*.
_GRADES = [
    ("High", "One hull, in active construction, on actual dates"),
    ("Medium", "2-3 hulls, or one on long-lead / projected dates"),
    ("Low", "4+ candidate hulls - little narrowing"),
    ("Flagged", "No window match, or no schedule data - review"),
]
_HDRS = ["Result", "Meaning", "Subaward $M", "Records", "% of C/D $"]
_GHDRS = ["Confidence", "Meaning", "Subaward $M", "Records", "% of C/D $"]
_NUMERIC = {"Subaward $M", "Records", "% of C/D $"}


def _bucket_table(c: RowCursor, hdrs, rows_def, key_range, banner):
    """Emit a §-banner + header + one SUMIFS/COUNTIFS row per bucket + a TOTAL (the shared shape of
    both tables). % is each row's $ over the section TOTAL (the C/D universe partitions the buckets)."""
    c.section(banner, _NCOLS)
    c.blank()
    hdr = c.write(hdrs, styles=header_styles(hdrs, center_headers=_NUMERIC))
    first = hdr + 1
    total = first + len(rows_def)
    for i, (key, label) in enumerate(rows_def):
        r = first + i
        c.write([key, label,
                 f'=SUMIFS({_REAL},{key_range},"{key}")/1000000',
                 f'=COUNTIFS({key_range},"{key}")',
                 f"=D{r}/D{total}"],
                styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_INT, S_PCT])
    c.total(["TOTAL", "All family-level (C/D) subawards",
             f"=SUM(D{first}:D{total - 1})",
             f"=SUM(E{first}:E{total - 1})",
             f"=D{total}/D{total}"],
            styles=[S_BOLD, S_DEFAULT, S_NUM, S_INT, S_PCT], n_cols=_NCOLS)


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_CD_LC_COVERAGE, _NCOLS)
    c.caption("How far purchase-date timing narrows the $2.75B family-level (C/D) subawards toward "
              "individual hulls. Narrowing the candidate SET only - never a per-hull dollar split.")
    c.blank(2)
    _bucket_table(c, _HDRS, _BUCKETS, _NARROW, "§1 - By timing-narrowing result")
    c.blank(2)
    _bucket_table(c, _GHDRS, _GRADES, _LCONF, "§2 - By lifecycle confidence")

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


DDG_CD_LC_COVERAGE = SheetEntry(TAB_CD_LC_COVERAGE, _GROUP, _render)
