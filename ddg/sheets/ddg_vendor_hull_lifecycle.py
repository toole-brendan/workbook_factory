"""ddg_vendor_hull_lifecycle - exact-hull supplier x hull activity by lifecycle stage.

A lifecycle-stage matrix over the existing exact-hull vendor exposure spine: one row per
Subawardee UEI x Assigned Hull pair, with dollar columns for Long-lead / Construction /
Outfit-test / Post-delivery. The row spine is generated upstream by
scripts/build_ddg_vendor_hull.py and only contains exact-hull (A/B) rows; the stage dollars
are live SUMIFS over DDG Subaward Transactions keyed on Subawardee UEI, Assigned Hull, and
Lifecycle Stage.

This is the supplier-facing companion to DDG Hull x Lifecycle Stage. C/D family-level rows
remain outside this sheet because they have no single assigned hull; read DDG C-D Lifecycle
Coverage / Rollup / Candidates for evidence-based narrowing of those rows.
"""
from __future__ import annotations

from ddg.sheets.kit.flat import make_flat_sheet, flat_header_letters, sm_match_row, sm_value
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.kit.tabs import TAB_VENDOR_HULL_LIFECYCLE
from ddg.sheets.kit.cuts import load_table
from ddg.sheets.supplier_master import supplier_master_cols
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.kit.widths import (
    W_UEI, W_SHORT_FLAG, W_VENDOR, W_SUPTYPE, W_CATEGORY, W_DOLLAR,
    W_COUNT, W_DATE, W_CODE, W_RANK,
)

_STAGES = ["Long-lead", "Construction", "Outfit / test", "Post-delivery"]
_HELPERS = ["SM Match Row"]
HEADERS = [
    "Subawardee UEI", "Hull", "Subawardee Vendor Name", "Builder", "Predominant SWBS",
    "Capability Domain (D)", "Primary Output (P)",
    *_STAGES, "Total $M", "Records", "First Subaward", "Last Subaward", "Confidence",
]
_WIDTHS = [
    W_UEI, W_SHORT_FLAG, W_VENDOR, W_SUPTYPE, W_CATEGORY, W_SHORT_FLAG, W_SHORT_FLAG,
    *([W_DOLLAR] * len(_STAGES)), W_DOLLAR, W_COUNT, W_DATE, W_DATE, W_CODE,
    W_RANK,
]

_L = flat_header_letters(headers=HEADERS, extra_cols=_HELPERS)
_UEI_COL = _L["Subawardee UEI"]
_HULL_COL = _L["Hull"]
_SMROW_COL = _L["SM Match Row"]

_UEI = ddg_tx_cols("Subawardee UEI")
_AHULL = ddg_tx_cols("Assigned Hull")
_STAGE = ddg_tx_cols("Lifecycle Stage")
_DATE = ddg_tx_cols("Subaward Date")
_REAL = ddg_tx_cols(TX_REAL)

_SM_KEY = supplier_master_cols("Key")
_SM_D = supplier_master_cols("Capability Domain (D)")
_SM_P = supplier_master_cols("Primary Output (P)")


def _spine():
    """Reuse the exact-hull vendor exposure spine, adding lifecycle-stage formula columns."""
    src_headers, src_rows = load_table("ddg_vendor_hull_exposure")
    src = {h: src_headers.index(h) for h in src_headers}
    copy_cols = [
        "Subawardee UEI", "Hull", "Subawardee Vendor Name", "Builder", "Predominant SWBS",
        "Confidence",
    ]
    out = []
    for src_row in src_rows:
        row = [""] * len(HEADERS)
        for h in copy_cols:
            if h in src and h in HEADERS:
                row[HEADERS.index(h)] = src_row[src[h]]
        out.append(row)
    return HEADERS, out


def _crit(r: int) -> str:
    return f"{_UEI},${_UEI_COL}{r},{_AHULL},${_HULL_COL}{r}"


def _smrow(r: int) -> str:
    return f"${_SMROW_COL}{r}"


_FORMULAS = {
    "SM Match Row": lambda r: sm_match_row(f'"DDG|"&${_UEI_COL}{r}', _SM_KEY),
    "Capability Domain (D)": lambda r: sm_value(_smrow(r), _SM_D, "D0"),
    "Primary Output (P)": lambda r: sm_value(_smrow(r), _SM_P, "P0"),
}
_FORMULAS.update({
    stage: (lambda crit: lambda r:
            f'=SUMIFS({_REAL},{_crit(r)},{_STAGE},"{crit}")/1000000')(stage)
    for stage in _STAGES
})
_FORMULAS["Total $M"] = lambda r: f"=SUMIFS({_REAL},{_crit(r)})/1000000"
_FORMULAS["Records"] = lambda r: f"=COUNTIFS({_crit(r)})"
_FORMULAS["First Subaward"] = lambda r: f"=_xlfn.MINIFS({_DATE},{_crit(r)})"
_FORMULAS["Last Subaward"] = lambda r: f"=_xlfn.MAXIFS({_DATE},{_crit(r)})"

DDG_VENDOR_HULL_LIFECYCLE, vendor_hull_lifecycle_cols = make_flat_sheet(
    tab=TAB_VENDOR_HULL_LIFECYCLE, group="model",
    csv_name="ddg_vendor_hull_lifecycle", table_name="DdgVendorHullLifecycle",
    table=_spine(),
    banner="§1 - DDG-51 vendor x hull lifecycle exposure",
    intro="One row per supplier x assigned hull; A/B exact-hull subawards split by construction stage.",
    widths=_WIDTHS,
    int_cols=["Records", "SM Match Row"], float_cols=[*_STAGES, "Total $M"],
    date_cols=["First Subaward", "Last Subaward"], formula_cols=_FORMULAS,
    input_cols=["Subawardee UEI", "Hull"],
    link_cols=["Records", "First Subaward", "Last Subaward"],
    extra_cols=_HELPERS, hidden_headers=_HELPERS,
    display_headers={
        "Subawardee Vendor Name": "Vendor", "Predominant SWBS": "Top SWBS group",
        "Capability Domain (D)": "Domain (D)", "Primary Output (P)": "Output (P)",
    },
)
