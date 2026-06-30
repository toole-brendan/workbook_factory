"""ddg_archetype_lifecycle - exact-hull lifecycle spend by D/P archetype.

Evidence-limited lifecycle rollup by the two published supplier archetype axes. The sheet reads the
exact-hull Vendor x Hull Lifecycle view, so it covers A/B assigned-hull dollars only. C/D family-level
subawards remain in the C-D lifecycle coverage / rollup / candidates sheets and are not allocated to
single hulls or stages here.
"""
from __future__ import annotations

from ddg.sheets.kit.flat import make_flat_sheet, flat_header_letters
from ddg.sheets.kit.tabs import TAB_ARCHETYPE_LIFECYCLE
from ddg.sheets.kit.taxonomy import DOMAINS, OUTPUTS
from ddg.sheets.ddg_vendor_hull_lifecycle import vendor_hull_lifecycle_cols
from ddg.sheets.kit.widths import W_RANK, W_CODE, W_TERM, W_DOLLAR, W_RATIO

_STAGES = ["Long-lead", "Construction", "Outfit / test", "Post-delivery"]
HEADERS = ["Axis", "Archetype Code", "Archetype Name", *_STAGES, "Total $M", "Share of Exact Lifecycle $"]
_WIDTHS = [W_RANK, W_CODE, W_TERM, *([W_DOLLAR] * len(_STAGES)), W_DOLLAR, W_RATIO]

_ROWS = []
_CTX = []
for _axis, _taxonomy in [("D", DOMAINS), ("P", OUTPUTS)]:
    for _code, _name, _defn in _taxonomy:
        _ROWS.append([_axis, _code, _name] + [""] * (len(_STAGES) + 2))
        _CTX.append((_axis, _code))

_L = flat_header_letters(headers=HEADERS)
_FIRST = 9
_CTX_BY_ROW = {_FIRST + i: _CTX[i] for i in range(len(_CTX))}

_VHL_D = vendor_hull_lifecycle_cols("Capability Domain (D)")
_VHL_P = vendor_hull_lifecycle_cols("Primary Output (P)")
_VHL_TOTAL = vendor_hull_lifecycle_cols("Total $M")
_VHL_STAGE = {stage: vendor_hull_lifecycle_cols(stage) for stage in _STAGES}


def _cell(header: str, r: int) -> str:
    return f"${_L[header]}{r}"


def _axis_range(r: int) -> str:
    axis, _code = _CTX_BY_ROW[r]
    return _VHL_D if axis == "D" else _VHL_P


def _code(r: int) -> str:
    _axis, code = _CTX_BY_ROW[r]
    return code


def _f_stage(stage: str):
    return lambda r: f'=SUMIFS({_VHL_STAGE[stage]},{_axis_range(r)},"{_code(r)}")'


def _f_total(r: int) -> str:
    return f'=SUMIFS({_VHL_TOTAL},{_axis_range(r)},"{_code(r)}")'


def _f_share(r: int) -> str:
    return f'=IFERROR({_cell("Total $M", r)}/SUM({_VHL_TOTAL}),"")'


_FORMULAS = {stage: _f_stage(stage) for stage in _STAGES}
_FORMULAS["Total $M"] = _f_total
_FORMULAS["Share of Exact Lifecycle $"] = _f_share

DDG_ARCHETYPE_LIFECYCLE, archetype_lifecycle_cols = make_flat_sheet(
    tab=TAB_ARCHETYPE_LIFECYCLE, group="model",
    csv_name="ddg_archetype_lifecycle", table_name="DdgArchetypeLifecycle",
    table=(HEADERS, _ROWS),
    banner="§1 - Exact-hull lifecycle-visible SAM by archetype",
    intro="D/P archetype x build stage for A/B exact-hull subawards only; C/D family-level dollars are not allocated here.",
    widths=_WIDTHS,
    float_cols=[*_STAGES, "Total $M"], pct_cols=["Share of Exact Lifecycle $"],
    formula_cols=_FORMULAS,
    display_headers={
        "Archetype Code": "Code",
        "Archetype Name": "Archetype",
        "Share of Exact Lifecycle $": "Share",
    },
)
