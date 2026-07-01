"""ddg_procurement_timing - DDG subaward $ by procurement-timing phase.

Splits the observed first-tier subaward evidence by WHEN it was placed relative to its PIID
family's construction envelope (Earliest Keel / Latest Delivery on the PIID->Hull map): advance
procurement / long-lead / EOQ (dated before any candidate hull's keel), the in-build window, or
post-delivery. The phase is a family-schedule property resolved LIVE on the transaction sheet
(the Procurement Timing column), so it covers the C/D majority that the hull grade leaves blank -
surfacing that the bulk of DDG supplier spend is front-loaded, not hull-specific.

Grain note: 'Advance / LLTM' means the subaward predates the block's EARLIEST keel - it is NOT a
per-hull assignment and does not allocate any family dollars to a hull. EOQ bought DURING
construction reads as In-build, so this is a FLOOR on advance procurement, not the full share.

Reconciled on the Checks tab: the four phases partition the observed subaward universe.
Promoted accessor (Checks): proc_timing_cols(header) -> "'DDG Procurement Timing'!$X$first:$X$last".
"""
from __future__ import annotations

from ddg.lib import SAM_TX_WINDOW_LABEL, SAM_PARTIAL_NOTE
from ddg.sheets.kit.flat import make_flat_sheet
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.kit.tabs import TAB_PROC_TIMING
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.kit.widths import (
    W_SUPTYPE, W_TEXT_WIDE, W_DOLLAR, W_COUNT, W_DATE, W_FY,
)

# Phase | Detail  (CSV spine)  ||  $M | % | Records | HII $M | BIW $M | First | Last  (computed)
_EXTRA = ["Subaward $M", "% of observed", "Published Records",
          "HII-Ingalls $M", "GD-BIW $M", "First Subaward", "Last Subaward"]
_WIDTHS = [W_SUPTYPE, W_TEXT_WIDE,
           W_DOLLAR, W_FY, W_COUNT, W_DOLLAR, W_DOLLAR, W_DATE, W_DATE]

_TIMING = ddg_tx_cols("Procurement Timing")
_REAL = ddg_tx_cols(TX_REAL)
_DATE = ddg_tx_cols("Subaward Date")
_BUILDER = ddg_tx_cols("Builder")

# All SUMIFS/COUNTIFS/MINIFS key on the phase label in column B, over the transaction-grain
# Procurement Timing column; the four spine rows partition the observed universe (see Checks).
_FORMULAS = {
    "Subaward $M":       lambda r: f"=SUMIFS({_REAL},{_TIMING},$B{r})/1000000",
    "% of observed":     lambda r: f"=IFERROR(SUMIFS({_REAL},{_TIMING},$B{r})/SUM({_REAL}),0)",
    "Published Records": lambda r: f"=COUNTIFS({_TIMING},$B{r})",
    "HII-Ingalls $M":    lambda r: f'=SUMIFS({_REAL},{_TIMING},$B{r},{_BUILDER},"HII-Ingalls")/1000000',
    "GD-BIW $M":         lambda r: f'=SUMIFS({_REAL},{_TIMING},$B{r},{_BUILDER},"GD-BIW")/1000000',
    "First Subaward":    lambda r: f"=_xlfn.MINIFS({_DATE},{_TIMING},$B{r})",
    "Last Subaward":     lambda r: f"=_xlfn.MAXIFS({_DATE},{_TIMING},$B{r})",
}

DDG_PROC_TIMING, proc_timing_cols = make_flat_sheet(
    tab=TAB_PROC_TIMING, group="model",
    csv_name="ddg_procurement_timing", table_name="DdgProcurementTiming",
    banner="§1 - DDG-51 subaward $ by procurement-timing phase",
    intro="Observed subawards by when placed vs the PIID family's construction envelope; "
          f"{SAM_TX_WINDOW_LABEL}, constant FY2026$ ({SAM_PARTIAL_NOTE}). 'Advance / LLTM' "
          "predates the block's earliest keel - a floor on advance procurement (EOQ bought "
          "in-build reads as In-build), not a per-hull allocation.",
    widths=_WIDTHS,
    float_cols=["Subaward $M", "HII-Ingalls $M", "GD-BIW $M"], pct_cols=["% of observed"],
    int_cols=["Published Records"],
    date_cols=["First Subaward", "Last Subaward"],
    formula_cols=_FORMULAS, extra_cols=_EXTRA,
    link_cols=["Published Records", "First Subaward", "Last Subaward"],
)
