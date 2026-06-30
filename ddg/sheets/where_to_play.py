"""where_to_play - the annual Program x Archetype x FY "where to play" scorecard (live).

Size, concentration and supplier continuity at ONE grain, so a reader can ask whether a program
vertical is open, concentrated or incumbent-heavy in a given year. One row per (Axis, Program,
Archetype, Federal FY) for the FY2022-FY2025 window, both published axes (Capability Domain D and
Primary Output P).

Every metric is a live SUMIFS / COUNTIFS over the Supplier-Year Activity model, reusing the SAME
criteria (program key, federal FY, axis code) so the columns reconcile:
  - Net Subaward $M / Program Share / YoY $ Growth   - size and momentum (net spend).
  - Active Suppliers                                  - distinct UEIs with positive spend that FY.
  - Parent Top-1 / Parent HHI / Parent Eff Firms     - ultimate-parent concentration (positive spend).
  - Incumbent Vendors % / Incumbent $ %              - share of suppliers / dollars active last FY too.
  - Retention %                                       - prior-FY suppliers still active this FY.
  - First-observed $ % / Reactivated $ %             - dollars to brand-new / returning suppliers.
  - Structure Class (internal header "Observed Structure")  - a neutral MECE screen on active-
    supplier count, parent HHI and incumbent $: Low Count (< 3 suppliers), else one of HHI-{H,L} /
    Inc-{H,L} from the two thresholds (see _structure_classes and Methodology). A SCREEN, not proof
    of economic contestability.

Share / ratio columns render as true percentages (the flat-table builder's pct_cols). Domain
Concentration stays the lifetime structural view; this is its annual companion. `summary` group.

The program label shown is the display form ("DDG-51"); the SUMIFS filter uses the internal key
("DDG"), matching Supplier-Year Activity. The canonical internal header stays "Observed Structure"
(so the accessors and the Executive Summary lookup do not break); it is displayed as "Structure
Class". Promoted accessor: `where_to_play_cols`.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, flat_header_letters,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_WHERE_TO_PLAY
from workbook_award_classification_refactor.sheets._taxonomy import DOMAINS, OUTPUTS
from workbook_award_classification_refactor.sheets.supplier_year_activity import (
    supplier_year_cols,
)
from workbook_award_classification_refactor.sheets._widths import (
    W_RANK, W_CODE, W_TERM, W_PROGRAM, W_FY, W_DOLLAR, W_COUNT,
    W_RATIO, W_STATUS, W_METRIC, W_CLASS,
)
from workbook_award_classification_refactor.sheets._structure_classes import (
    MIN_ACTIVE_SUPPLIERS,
    HIGH_PARENT_HHI,
    HIGH_INCUMBENT_DOLLAR_SHARE,
    LOW_COUNT,
    HHI_H_INC_H,
    HHI_H_INC_L,
    HHI_L_INC_H,
    HHI_L_INC_L,
)

_GROUP = "summary"

FYS = (2022, 2023, 2024, 2025)
# (display label, internal program key). DDG shows as DDG-51 (Domain Concentration convention),
# but the spine keys it "DDG". DDG-51-only slice.
PROGRAMS = [("DDG-51", "DDG")]
AXES = [("D", DOMAINS), ("P", OUTPUTS)]

HEADERS = [
    "Axis", "Archetype Code", "Archetype Name", "Program", "Federal FY",
    "Net Subaward $M", "Program Share", "YoY $ Growth", "Active Suppliers",
    "Parent Top-1", "Parent HHI", "Parent Eff Firms",
    "Incumbent Vendors %", "Incumbent $ %", "Retention %",
    "First-observed $ %", "Reactivated $ %", "Observed Structure",
]
_STATIC = ["Axis", "Archetype Code", "Archetype Name", "Program", "Federal FY"]
_FORMULA_HEADERS = [h for h in HEADERS if h not in _STATIC]

_WIDTHS = [
    W_RANK,      # Axis
    W_CODE,      # Code
    W_TERM,      # Archetype
    W_PROGRAM,   # Program
    W_FY,        # FY
    W_DOLLAR,    # Net $M
    W_RATIO,     # Program Share
    W_RATIO,     # YoY Growth
    W_COUNT,     # Active UEIs
    W_RATIO,     # Parent Top-1
    W_DOLLAR,    # Parent HHI
    W_METRIC,    # Effective Parents
    W_STATUS,    # Incumbent UEI %
    W_RATIO,     # Incumbent $ %
    W_RATIO,     # Retention %
    W_STATUS,    # First-observed %
    W_RATIO,     # Reactivated %
    W_CLASS,     # Structure Class
]
assert len(_WIDTHS) == len(HEADERS)

# --- in-memory row spine + per-row context --------------------------------------------------
_ROWS = []
_CTX = []   # parallel (axis, code, program_key, fy) for each row, in emission order
for _axis, _taxonomy in AXES:
    for _disp, _key in PROGRAMS:
        for _fy in FYS:
            for _code, _name, _defn in _taxonomy:
                _ROWS.append([_axis, _code, _name, _disp, str(_fy)] + [""] * len(_FORMULA_HEADERS))
                _CTX.append((_axis, _code, _key, _fy))

_L = flat_header_letters(headers=HEADERS)
_FIRST = 9
_LAST = 8 + len(_ROWS)
_CTX_BY_ROW = {_FIRST + i: _CTX[i] for i in range(len(_CTX))}

# Supplier-Year Activity source ranges (read once; bounded $first:$last).
_SY_PROG = supplier_year_cols("Program")
_SY_FY = supplier_year_cols("Federal FY")
_SY_D = supplier_year_cols("Capability Domain (D)")
_SY_P = supplier_year_cols("Primary Output (P)")
_SY_NET = supplier_year_cols("Net Subaward $M")
_SY_POS = supplier_year_cols("Positive Supplier $M")
_SY_STATUS = supplier_year_cols("Activity Status")
_SY_PD_TOTAL = supplier_year_cols("Parent D-FY $M")
_SY_PD_HHI = supplier_year_cols("Parent D HHI Numerator")
_SY_PP_TOTAL = supplier_year_cols("Parent P-FY $M")
_SY_PP_HHI = supplier_year_cols("Parent P HHI Numerator")


def _cell(header: str, r: int) -> str:
    return f"${_L[header]}{r}"


def _ctx(r: int):
    axis, code, program, fy = _CTX_BY_ROW[r]
    axis_rng = _SY_D if axis == "D" else _SY_P
    ptot = _SY_PD_TOTAL if axis == "D" else _SY_PP_TOTAL
    phhi = _SY_PD_HHI if axis == "D" else _SY_PP_HHI
    return code, program, fy, axis_rng, ptot, phhi


def _crit(program: str, fy: int, axis_rng: str, code: str) -> str:
    """The shared (program, FY, axis code) SUMIFS/COUNTIFS criteria fragment."""
    return f'{_SY_PROG},"{program}",{_SY_FY},{fy},{axis_rng},"{code}"'


def _postot(program: str, fy: int, axis_rng: str, code: str) -> str:
    return f'SUMIFS({_SY_POS},{_crit(program, fy, axis_rng, code)})'


def _f_net(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    return f'=SUMIFS({_SY_NET},{_crit(program, fy, axis_rng, code)})'


def _f_prog_share(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    denom = f'SUMIFS({_SY_NET},{_SY_PROG},"{program}",{_SY_FY},{fy})'
    return f'=IFERROR({_cell("Net Subaward $M", r)}/{denom},"")'


def _f_yoy(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    prior = f'SUMIFS({_SY_NET},{_SY_PROG},"{program}",{_SY_FY},{fy - 1},{axis_rng},"{code}")'
    return f'=IFERROR({_cell("Net Subaward $M", r)}/{prior}-1,"")'


def _f_active(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    return f'=COUNTIFS({_crit(program, fy, axis_rng, code)},{_SY_POS},">0")'


def _f_parent_top1(r):
    code, program, fy, axis_rng, ptot, _ph = _ctx(r)
    maxp = f'_xlfn.MAXIFS({ptot},{_crit(program, fy, axis_rng, code)},{_SY_POS},">0")'
    return f'=IFERROR({maxp}/{_postot(program, fy, axis_rng, code)},"")'


def _f_parent_hhi(r):
    code, program, fy, axis_rng, _pt, phhi = _ctx(r)
    return (f'=IFERROR(SUMIFS({phhi},{_crit(program, fy, axis_rng, code)})'
            f'/{_postot(program, fy, axis_rng, code)}^2,"")')


def _f_parent_eff(r):
    return f'=IFERROR(1/{_cell("Parent HHI", r)},"")'


def _f_incumbent_vendors(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    cont = (f'COUNTIFS({_crit(program, fy, axis_rng, code)},'
            f'{_SY_STATUS},"Continued",{_SY_POS},">0")')
    return f'=IFERROR({cont}/{_cell("Active Suppliers", r)},"")'


def _f_incumbent_dollar(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    cont = f'SUMIFS({_SY_POS},{_crit(program, fy, axis_rng, code)},{_SY_STATUS},"Continued")'
    return f'=IFERROR({cont}/{_postot(program, fy, axis_rng, code)},"")'


def _f_retention(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    cont = (f'COUNTIFS({_crit(program, fy, axis_rng, code)},'
            f'{_SY_STATUS},"Continued",{_SY_POS},">0")')
    prior = (f'COUNTIFS({_SY_PROG},"{program}",{_SY_FY},{fy - 1},'
             f'{axis_rng},"{code}",{_SY_POS},">0")')
    return f'=IFERROR({cont}/{prior},"")'


def _f_firstobs_dollar(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    fo = f'SUMIFS({_SY_POS},{_crit(program, fy, axis_rng, code)},{_SY_STATUS},"First observed")'
    return f'=IFERROR({fo}/{_postot(program, fy, axis_rng, code)},"")'


def _f_react_dollar(r):
    code, program, fy, axis_rng, _pt, _ph = _ctx(r)
    re = f'SUMIFS({_SY_POS},{_crit(program, fy, axis_rng, code)},{_SY_STATUS},"Reactivated")'
    return f'=IFERROR({re}/{_postot(program, fy, axis_rng, code)},"")'


def _f_structure(r):
    active = _cell("Active Suppliers", r)
    hhi = _cell("Parent HHI", r)
    incumbent = _cell("Incumbent $ %", r)

    return (
        f'=IF({active}<{MIN_ACTIVE_SUPPLIERS},"{LOW_COUNT}",'
        f'IF({hhi}>={HIGH_PARENT_HHI},'
        f'IF({incumbent}>={HIGH_INCUMBENT_DOLLAR_SHARE},'
        f'"{HHI_H_INC_H}","{HHI_H_INC_L}"),'
        f'IF({incumbent}>={HIGH_INCUMBENT_DOLLAR_SHARE},'
        f'"{HHI_L_INC_H}","{HHI_L_INC_L}")))'
    )


_FORMULAS = {
    "Net Subaward $M": _f_net,
    "Program Share": _f_prog_share,
    "YoY $ Growth": _f_yoy,
    "Active Suppliers": _f_active,
    "Parent Top-1": _f_parent_top1,
    "Parent HHI": _f_parent_hhi,
    "Parent Eff Firms": _f_parent_eff,
    "Incumbent Vendors %": _f_incumbent_vendors,
    "Incumbent $ %": _f_incumbent_dollar,
    "Retention %": _f_retention,
    "First-observed $ %": _f_firstobs_dollar,
    "Reactivated $ %": _f_react_dollar,
    "Observed Structure": _f_structure,
}

WHERE_TO_PLAY, where_to_play_cols = make_flat_sheet(
    tab=TAB_WHERE_TO_PLAY, group=_GROUP,
    csv_name="where_to_play", table_name="WhereToPlay",
    table=(HEADERS, _ROWS),
    banner="§1 - Annual program-archetype screen",
    intro="Size, concentration and supplier continuity by program, archetype and fiscal year.",
    widths=_WIDTHS,
    int_cols=["Federal FY", "Active Suppliers"],
    float_cols=["Net Subaward $M", "Parent HHI", "Parent Eff Firms"],
    pct_cols=["Program Share", "YoY $ Growth", "Parent Top-1",
              "Incumbent Vendors %", "Incumbent $ %", "Retention %",
              "First-observed $ %", "Reactivated $ %"],
    formula_cols=_FORMULAS,
    display_headers={
        "Archetype Code": "Code",
        "Archetype Name": "Archetype",
        "Federal FY": "FY",
        "Net Subaward $M": "Net $M",
        "Active Suppliers": "Active UEIs",
        "Parent Eff Firms": "Effective Parents",
        "Incumbent Vendors %": "Incumbent UEI %",
        "First-observed $ %": "First-observed %",
        "Reactivated $ %": "Reactivated %",
        "Observed Structure": "Structure Class",
    },
)

# Guard: the data-row span the per-row context was built on must match what make_flat_sheet rendered.
assert (where_to_play_cols.first, where_to_play_cols.last) == (_FIRST, _LAST), (
    where_to_play_cols.first, where_to_play_cols.last, _FIRST, _LAST)
