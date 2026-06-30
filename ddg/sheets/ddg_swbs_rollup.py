"""ddg_swbs_rollup - DDG SWBS by Ship-System: the per-subsystem roll-up (model group).

The SWBS sibling of the program-vendor sheets: one row per SWBS subsystem (+ a U00 unmapped
row), with the same column skeleton - Subaward $M, records, first/last, and the per-FY
≤FY12..FY26 split in CONSTANT FY2026$. Each per-FY cell is a single SUMIFS over the SWBS-tagged
DDG Subaward Transactions leaf's constant-FY2026$ column, keyed on that sheet's `SWBS Subsystem`
column + Federal FY (the deflation lives at the transaction grain - see _fiscal) - the same
mechanism as the program-vendor sheets, with the subsystem as the key instead of the UEI.
HII-Ingalls-only falls out automatically: GD-BIW transactions carry a blank SWBS Subsystem, so
they never match a real subsystem or U00.

Spine = extracted/ddg_swbs_by_subsystem.csv (scripts/build_ddg_swbs_rollup.py); the static
subsystem label columns are hardcoded, every dollar/count/date is a live formula.

Promoted accessor (imported by executive_summary): `swbs_rollup_cols`.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_SWBS_ROLLUP
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)
from workbook_award_classification_refactor.sheets._widths import (
    W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_DATE, W_FY,
)

# SWBS Subsystem | Major Group | SWBS (display) | $M | Records | First | Last | ≤FY12..FY26
_WIDTHS = [W_CODE, W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_DATE, W_DATE,
           *([W_FY] * 15)]

# Roll-up keys over the SWBS-tagged DDG tx leaf, keyed on this sheet's SWBS Subsystem (col B).
_SUBSYS = ddg_tx_cols("SWBS Subsystem")
_DATE = ddg_tx_cols("Subaward Date")
_REAL = ddg_tx_cols(TX_REAL)          # constant-FY2026$ amount, at transaction grain
_FEDFY = ddg_tx_cols(TX_FED_FY)       # federal FY, at transaction grain

_FORMULAS = {
    "Subaward $M":      pv_lifetime_formula(_REAL, _SUBSYS),
    "Published Subaward Records": lambda r: f"=COUNTIFS({_SUBSYS},$B{r})",
    "First Subaward":   lambda r: f"=_xlfn.MINIFS({_DATE},{_SUBSYS},$B{r})",
    "Last Subaward":    lambda r: f"=_xlfn.MAXIFS({_DATE},{_SUBSYS},$B{r})",
}
for _h in FY_HEADERS:
    _FORMULAS[_h] = pv_fy_formula(_REAL, _SUBSYS, _FEDFY, _h)

DDG_SWBS_ROLLUP, swbs_rollup_cols = make_flat_sheet(
    tab=TAB_SWBS_ROLLUP, group="model",
    csv_name="ddg_swbs_by_subsystem", table_name="DdgSwbsBySubsystem",
    banner="§1 - DDG-51 subaward $ by ship-system (SWBS)",
    intro="HII-Ingalls DDG-51 subawards by SWBS subsystem; constant FY2026$.",
    widths=_WIDTHS,
    int_cols=["Published Subaward Records"], float_cols=["Subaward $M", *FY_HEADERS],
    date_cols=["First Subaward", "Last Subaward"], formula_cols=_FORMULAS,
    input_cols=["SWBS Subsystem"],   # the roll-up key -> blue
    link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
)
