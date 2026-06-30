"""supplier_year_activity - the (Program x Subawardee UEI x Federal FY) activity model.

The annual companion to the lifetime program-vendor / Domain Concentration views: one row per
supplier per program per federal fiscal year, so the workbook can express supplier status
(first observed / continued / reactivated), incumbency and parent concentration at the SAME
Program x Archetype x FY grain that the Where to Play sheet reads. Domain Concentration stays the
lifetime structural view; this sheet is the annual dynamics layer beneath it.

Two upstream dependencies, mirroring the program-vendor factory:
  - each program's Subaward Transactions leaf - Net Subaward $M is a single SUMIFS over the
    transaction constant-FY2026$ column keyed on this row's UEI + Federal FY; Reports is a COUNTIFS.
  - the Supplier Master - one hidden "SM Match Row" matches this row's "Program|UEI" key ONCE; the
    vendor name / resolved Parent Key / resolved Capability Domain (D) + Primary Output (P) INDEX
    that row.

Status & concentration use the POSITIVE-spend convention (Positive Supplier $M = MAX(Net, 0)),
matching Domain Concentration. Prior-Year / Earlier-Year Active are same-sheet COUNTIFS over this
UEI's OTHER fiscal-year rows (a cross-row reference, never a self-reference - no circular formula).
The parent helpers pre-aggregate each ultimate parent's positive FY2026$ within the row's
Program x FY x archetype so Where to Play can read Parent Top-1 / Parent HHI with plain SUMIFS,
once per axis (D and P). `model` group.

The row spine + the one distinct count are materialized by scripts/build_supplier_year_activity.py
(all fiscal years, so FY2022's "first observed" is defined against full history). `model` group.

Promoted accessor (imported by Where to Play + the Executive Summary): `supplier_year_cols`.
"""
from __future__ import annotations

from ddg.sheets.kit.flat import (
    make_flat_sheet, flat_header_letters, sm_match_row, sm_text, sm_value,
)
from ddg.sheets.kit.fiscal import TX_FED_FY, TX_REAL
from ddg.sheets.kit.tabs import TAB_SUPPLIER_YEAR
from ddg.sheets.kit.cuts import load_table
from ddg.sheets.supplier_master import supplier_master_cols
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.kit.widths import (
    W_PROGRAM, W_FY, W_UEI, W_VENDOR, W_DOLLAR, W_RANK,
)

_GROUP = "model"

# Program label (as materialized in the spine) -> its single transaction leaf accessor.
# DDG-51-only slice (the spine CSV is filtered to DDG rows).
_TX = {"DDG": ddg_tx_cols}

# Hidden formula-helper columns (sheet-only). SM Match Row hoists the one Supplier Master MATCH;
# the parent helpers pre-aggregate each ultimate parent's positive FY2026$ within the row's
# Program x FY x archetype, ONE set per axis (D, P), so Where to Play reads Parent Top-1 / Parent
# HHI with plain SUMIFS instead of a cross-sheet array expression that surfaces #VALUE! on recalc.
_HELPERS = [
    "SM Match Row", "UEI Positive $ Squared",
    "Parent D-FY $M", "Parent D HHI Numerator", "Parent D Firm Weight",
    "Parent P-FY $M", "Parent P HHI Numerator", "Parent P Firm Weight",
]

# CSV columns (Program | Federal FY | UEI | Distinct Subaward Numbers materialized; the rest blank,
# filled live below) + the 8 hidden helpers. widths must cover every column in this order.
_WIDTHS = [
    W_PROGRAM, W_FY, W_UEI, 18,            # Program, FY, Subawardee UEI, Distinct subawards
    W_VENDOR, W_UEI, 12, 12,               # Supplier, Parent UEI, Domain (D), Output (P)
    W_DOLLAR, W_DOLLAR, 10,                # Net $M, Positive $M, Reports
    15, 17, 16, 10,                        # Prior FY Active, Earlier FY Active, Activity Status, Active FYs
    W_RANK, W_DOLLAR,                       # SM Match Row, UEI Positive $ Squared (hidden)
    W_DOLLAR, W_DOLLAR, W_DOLLAR,           # Parent D-FY $M, Parent D HHI Num, Parent D Firm Weight (hidden)
    W_DOLLAR, W_DOLLAR, W_DOLLAR,           # Parent P-FY $M, Parent P HHI Num, Parent P Firm Weight (hidden)
]

# Supplier Master source ranges (each attribute resolved once per UEI x program over there).
_SM_KEY = supplier_master_cols("Key")
_SM_NAME = supplier_master_cols("Subawardee Vendor Name")
_SM_PARENT = supplier_master_cols("Parent UEI")
_SM_D = supplier_master_cols("Capability Domain (D)")
_SM_P = supplier_master_cols("Primary Output (P)")

# Row spine (for the per-row program -> transaction-leaf map) + this sheet's column letters.
_HEADERS, _ROWS = load_table("supplier_year_activity")
_L = flat_header_letters("supplier_year_activity", extra_cols=_HELPERS)

# make_flat_sheet with an intro: title 2, caption 3, blanks 4-5, banner 6, blank 7, header 8 ->
# data starts at 9 (asserted against the post-build accessor below).
_FIRST = 9
_LAST = 8 + len(_ROWS)
_PROGRAM_AT = _HEADERS.index("Program")
_PROGRAM_BY_ROW = {_FIRST + i: row[_PROGRAM_AT] for i, row in enumerate(_ROWS)}


def _cell(header: str, r: int) -> str:
    return f"${_L[header]}{r}"


def _rng(header: str) -> str:
    c = _L[header]
    return f"${c}${_FIRST}:${c}${_LAST}"


# Same-sheet bounded ranges the status / parent helpers aggregate over.
_PROG_R = _rng("Program")
_FY_R = _rng("Federal FY")
_UEI_R = _rng("Subawardee UEI")
_POS_R = _rng("Positive Supplier $M")
_PKEY_R = _rng("Parent Key")
_D_R = _rng("Capability Domain (D)")
_P_R = _rng("Primary Output (P)")


def _tx_for(r: int):
    return _TX[_PROGRAM_BY_ROW[r]]


def _smrow(r: int) -> str:
    return _cell("SM Match Row", r)


def _net(r: int) -> str:
    tx = _tx_for(r)
    return (f'=SUMIFS({tx(TX_REAL)},{tx("Subawardee UEI")},{_cell("Subawardee UEI", r)},'
            f'{tx(TX_FED_FY)},{_cell("Federal FY", r)})/1000000')


def _reports(r: int) -> str:
    tx = _tx_for(r)
    return (f'=COUNTIFS({tx("Subawardee UEI")},{_cell("Subawardee UEI", r)},'
            f'{tx(TX_FED_FY)},{_cell("Federal FY", r)})')


def _parent_key(r: int) -> str:
    m = _smrow(r)
    uei = _cell("Subawardee UEI", r)
    p = f"INDEX({_SM_PARENT},{m})"
    return f'=IF({m}=0,{uei},IF(OR({p}="",{p}="-"),{uei},{p}))'


def _prior_active(r: int) -> str:
    return (f'=--(COUNTIFS({_PROG_R},{_cell("Program", r)},{_UEI_R},{_cell("Subawardee UEI", r)},'
            f'{_FY_R},{_cell("Federal FY", r)}-1,{_POS_R},">0")>0)')


def _earlier_active(r: int) -> str:
    return (f'=--(COUNTIFS({_PROG_R},{_cell("Program", r)},{_UEI_R},{_cell("Subawardee UEI", r)},'
            f'{_FY_R},"<"&{_cell("Federal FY", r)},{_POS_R},">0")>0)')


def _active_fys(r: int) -> str:
    return (f'=COUNTIFS({_PROG_R},{_cell("Program", r)},{_UEI_R},{_cell("Subawardee UEI", r)},'
            f'{_POS_R},">0")')


def _status(r: int) -> str:
    pos = _cell("Positive Supplier $M", r)
    prior = _cell("Prior-Year Active", r)
    earlier = _cell("Earlier-Year Active", r)
    return (f'=IF({pos}<=0,"Adjustment-only",'
            f'IF({earlier}=0,"First observed",'
            f'IF({prior}=1,"Continued","Reactivated")))')


def _parent_total(r: int, axis_range: str, axis_cell: str) -> str:
    """The row's ultimate parent's positive FY2026$ within its Program x FY x archetype."""
    return (f'=SUMIFS({_POS_R},{_PROG_R},{_cell("Program", r)},{_FY_R},{_cell("Federal FY", r)},'
            f'{axis_range},{axis_cell},{_PKEY_R},{_cell("Parent Key", r)},{_POS_R},">0")')


def _parent_hhi_num(r: int, total_header: str) -> str:
    pos = _cell("Positive Supplier $M", r)
    return f'=IF({pos}>0,{pos}*{_cell(total_header, r)},0)'


def _parent_firm_weight(r: int, axis_range: str, axis_cell: str) -> str:
    pos = _cell("Positive Supplier $M", r)
    count = (f'COUNTIFS({_PROG_R},{_cell("Program", r)},{_FY_R},{_cell("Federal FY", r)},'
             f'{axis_range},{axis_cell},{_PKEY_R},{_cell("Parent Key", r)},{_POS_R},">0")')
    return f'=IF({pos}>0,1/MAX(1,{count}),0)'


_FORMULAS = {
    "SM Match Row": lambda r: sm_match_row(
        f'{_cell("Program", r)}&"|"&{_cell("Subawardee UEI", r)}', _SM_KEY),
    "Subawardee Vendor Name": lambda r: sm_text(_smrow(r), _SM_NAME),
    "Parent Key": _parent_key,
    "Capability Domain (D)": lambda r: sm_value(_smrow(r), _SM_D, "D0"),
    "Primary Output (P)": lambda r: sm_value(_smrow(r), _SM_P, "P0"),
    "Net Subaward $M": _net,
    "Positive Supplier $M": lambda r: f'=MAX({_cell("Net Subaward $M", r)},0)',
    "Reports": _reports,
    "Prior-Year Active": _prior_active,
    "Earlier-Year Active": _earlier_active,
    "Activity Status": _status,
    "Active FYs": _active_fys,
    "UEI Positive $ Squared": lambda r: (
        f'=IF({_cell("Positive Supplier $M", r)}>0,{_cell("Positive Supplier $M", r)}^2,0)'),
    "Parent D-FY $M": lambda r: _parent_total(r, _D_R, _cell("Capability Domain (D)", r)),
    "Parent D HHI Numerator": lambda r: _parent_hhi_num(r, "Parent D-FY $M"),
    "Parent D Firm Weight": lambda r: _parent_firm_weight(r, _D_R, _cell("Capability Domain (D)", r)),
    "Parent P-FY $M": lambda r: _parent_total(r, _P_R, _cell("Primary Output (P)", r)),
    "Parent P HHI Numerator": lambda r: _parent_hhi_num(r, "Parent P-FY $M"),
    "Parent P Firm Weight": lambda r: _parent_firm_weight(r, _P_R, _cell("Primary Output (P)", r)),
}

SUPPLIER_YEAR_ACTIVITY, supplier_year_cols = make_flat_sheet(
    tab=TAB_SUPPLIER_YEAR, group=_GROUP,
    csv_name="supplier_year_activity", table_name="SupplierYearActivity",
    banner="§1 - Supplier activity by fiscal year",
    intro="Program-supplier activity by federal fiscal year.",
    widths=_WIDTHS,
    int_cols=["Federal FY", "Distinct Subaward Numbers", "Reports",
              "Prior-Year Active", "Earlier-Year Active", "Active FYs", "SM Match Row"],
    float_cols=["Net Subaward $M", "Positive Supplier $M", "UEI Positive $ Squared",
                "Parent D-FY $M", "Parent D HHI Numerator", "Parent D Firm Weight",
                "Parent P-FY $M", "Parent P HHI Numerator", "Parent P Firm Weight"],
    input_cols=["Subawardee UEI"],
    link_cols=["Reports"],                 # a COUNTIFS surfacing a tx-sheet count -> green link
    formula_cols=_FORMULAS, extra_cols=_HELPERS,
    hidden_headers=_HELPERS,
    display_headers={
        "Federal FY": "FY",
        "Distinct Subaward Numbers": "Distinct subawards",
        "Subawardee Vendor Name": "Supplier",
        "Parent Key": "Parent UEI",
        "Net Subaward $M": "Net $M",
        "Positive Supplier $M": "Positive $M",
        "Prior-Year Active": "Prior FY Active",
        "Earlier-Year Active": "Earlier FY Active",
        "Capability Domain (D)": "Domain (D)",
        "Primary Output (P)": "Output (P)",
    },
)

# Guard: the data-row span the same-sheet helpers were built on must match what make_flat_sheet
# rendered (else the status / parent-concentration SUMIFS/COUNTIFS ranges drift).
assert (supplier_year_cols.first, supplier_year_cols.last) == (_FIRST, _LAST), (
    supplier_year_cols.first, supplier_year_cols.last, _FIRST, _LAST)
