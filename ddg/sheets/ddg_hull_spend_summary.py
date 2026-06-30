"""ddg_hull_spend_summary - one row per hull: the subaward $ assigned to that hull."""
from __future__ import annotations

from ddg.sheets.kit.flat import make_flat_sheet
from ddg.sheets.kit.fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula, first_last_or_na,
)
from ddg.sheets.kit.tabs import TAB_HULL_SPEND
from ddg.sheets.kit.cuts import load_table
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.kit.widths import (
    W_SHORT_FLAG, W_SUPTYPE, W_DOLLAR, W_COUNT, W_DATE, W_FY,
)

HEADERS = ["Hull", "Builder", "Assigned Subaward $M", "Published Subaward Records",
           "First Subaward", "Last Subaward", *FY_HEADERS]
_WIDTHS = [W_SHORT_FLAG, W_SUPTYPE, W_DOLLAR, W_COUNT, W_DATE, W_DATE,
           *([W_FY] * len(FY_HEADERS))]

_AHULL = ddg_tx_cols("Assigned Hull")
_DATE = ddg_tx_cols("Subaward Date")
_REAL = ddg_tx_cols(TX_REAL)
_FEDFY = ddg_tx_cols(TX_FED_FY)


def _spine():
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
    intro=("Exact-hull (grade A/B) subawards per hull, FY2016-FY2025, constant FY2026$ - "
           "not the full DDG universe (see DDG Hull Coverage)."),
    widths=_WIDTHS,
    int_cols=["Published Subaward Records"],
    float_cols=["Assigned Subaward $M", *FY_HEADERS],
    date_cols=["First Subaward", "Last Subaward"], formula_cols=_FORMULAS,
    input_cols=["Hull"],
    link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
)
