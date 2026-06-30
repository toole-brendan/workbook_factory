"""ddg_hull_spend_summary - one row per hull: the subaward $ assigned to that hull.

The hull analogue of the per-subsystem SWBS roll-up: one row per hull (spine + builder from the
DDG Hull Master), with the lifetime assigned subaward $, record count, first/last action date, and
the per-FY constant-FY2026$ split. Every measure is a live SUMIFS / COUNTIFS / MINIFS / MAXIFS over
the DDG Subaward Transactions leaf, keyed on that sheet's materialized `Assigned Hull` column - so
conflict / multi-hull / family-only rows (blank Assigned Hull) are excluded by construction, and
only the exact-hull (grade A/B) dollars roll up here. Hulls with no attributable subaward show zero.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula, first_last_or_na,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_SPEND
from workbook_award_classification_refactor.sheets._cuts import load_table
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)
from workbook_award_classification_refactor.sheets._widths import (
    W_SHORT_FLAG, W_SUPTYPE, W_DOLLAR, W_COUNT, W_DATE, W_FY,
)

# Hull | Builder | Assigned $M | Records | First | Last | ≤FY12..FY26
HEADERS = ["Hull", "Builder", "Assigned Subaward $M", "Published Subaward Records",
           "First Subaward", "Last Subaward", *FY_HEADERS]
_WIDTHS = [W_SHORT_FLAG, W_SUPTYPE, W_DOLLAR, W_COUNT, W_DATE, W_DATE, *([W_FY] * 15)]

# Roll-up keys over the hull-tagged DDG tx leaf, keyed on this sheet's Hull column (col B).
_AHULL = ddg_tx_cols("Assigned Hull")
_DATE = ddg_tx_cols("Subaward Date")
_REAL = ddg_tx_cols(TX_REAL)          # constant-FY2026$ amount, at transaction grain
_FEDFY = ddg_tx_cols(TX_FED_FY)       # federal FY, at transaction grain


def _spine():
    """(HEADERS, rows) from the DDG Hull Master: static Hull + Builder, every measure blank
    (a live formula). Sorted by hull number so the sheet reads in build order."""
    hm_headers, hm_rows = load_table("ddg_hull_master")
    hi, bi = hm_headers.index("Hull"), hm_headers.index("Builder")
    out = []
    for r in hm_rows:
        row = [""] * len(HEADERS)
        row[0] = r[hi] if hi < len(r) else ""
        row[1] = r[bi] if bi < len(r) else ""
        out.append(row)
    out.sort(key=lambda x: int("".join(ch for ch in x[0] if ch.isdigit()) or 0))
    return HEADERS, out


_FORMULAS = {
    "Assigned Subaward $M":       pv_lifetime_formula(_REAL, _AHULL),
    "Published Subaward Records": lambda r: f"=COUNTIFS({_AHULL},$B{r})",
    "First Subaward":             first_last_or_na(_DATE, _AHULL, "MIN"),
    "Last Subaward":              first_last_or_na(_DATE, _AHULL, "MAX"),
}
for _h in FY_HEADERS:
    _FORMULAS[_h] = pv_fy_formula(_REAL, _AHULL, _FEDFY, _h)

DDG_HULL_SPEND, hull_spend_cols = make_flat_sheet(
    tab=TAB_HULL_SPEND, group="model",
    csv_name="ddg_hull_spend_summary", table_name="DdgHullSpend",
    table=_spine(),
    banner="§1 - DDG-51 subaward $ assigned by hull",
    intro=("Exact-hull (grade A/B) subawards per hull, FY2026$ - not the full DDG universe "
           "(see DDG Hull Coverage)."),
    widths=_WIDTHS,
    int_cols=["Published Subaward Records"],
    float_cols=["Assigned Subaward $M", *FY_HEADERS],
    date_cols=["First Subaward", "Last Subaward"], formula_cols=_FORMULAS,
    input_cols=["Hull"],   # the roll-up key -> blue
    link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
)
