"""ddg_swbs_rollup - DDG SWBS by Ship-System roll-up."""
from __future__ import annotations

from ddg.lib import SAM_TX_WINDOW_LABEL, SAM_PARTIAL_NOTE
from ddg.sheets.kit.flat import make_flat_sheet
from ddg.sheets.kit.fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula,
)
from ddg.sheets.kit.tabs import TAB_SWBS_ROLLUP
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.kit.widths import (
    W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_DATE, W_FY,
)

# SWBS Subsystem | Major Group | SWBS (display) | $M | Records | First | Last | FY-window $M
_WIDTHS = [W_CODE, W_CODE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_DATE, W_DATE,
           *([W_FY] * len(FY_HEADERS))]

_SUBSYS = ddg_tx_cols("SWBS Subsystem")
_DATE = ddg_tx_cols("Subaward Date")
_REAL = ddg_tx_cols(TX_REAL)
_FEDFY = ddg_tx_cols(TX_FED_FY)

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
    intro=(f"HII-Ingalls DDG-51 subawards by SWBS subsystem; {SAM_TX_WINDOW_LABEL}, "
           f"constant FY2026$ ({SAM_PARTIAL_NOTE})."),
    widths=_WIDTHS,
    int_cols=["Published Subaward Records"], float_cols=["Subaward $M", *FY_HEADERS],
    date_cols=["First Subaward", "Last Subaward"], formula_cols=_FORMULAS,
    input_cols=["SWBS Subsystem"],
    link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
)
