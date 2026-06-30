"""deflators - one shared procurement deflator table for TAM and SAM."""
from __future__ import annotations

import re

from ddg.sheets._flat import make_flat_sheet
from ddg.sheets._tabs import TAB_DEFLATORS
from ddg.sheets._widths import W_FY, W_TEXT_WIDE

_GROUP = "inputs"
_WIDTHS = [W_FY, 17, 12, W_TEXT_WIDE]
_FIRST_DATA_ROW = 9
_IDX_COL = "C"
_FY2026_ROW = _FIRST_DATA_ROW + 14  # ≤FY12 + FY2013..FY2026 => FY2026 row

_FORMULAS = {
    "Factor to FY2026 $": lambda r: f"=${_IDX_COL}${_FY2026_ROW}/${_IDX_COL}{r}",
}

DEFLATORS, deflators_cols = make_flat_sheet(
    tab=TAB_DEFLATORS, group=_GROUP,
    csv_name="deflators", table_name="Deflators",
    banner="§1 - Procurement deflators",
    intro="Green Book Procurement TOA index and FY2026 conversion factor for TAM budget years and SAM transactions.",
    widths=_WIDTHS,
    float_cols=["Procurement TOA (FY2025=100)", "Factor to FY2026 $"],
    input_cols=["Procurement TOA (FY2025=100)"],
    input_fill=True,
    formula_cols=_FORMULAS,
    display_headers={
        "Procurement TOA (FY2025=100)": "Procurement Index",
        "Factor to FY2026 $": "FY26 Factor",
    },
)

_FAC_RANGE = deflators_cols("Factor to FY2026 $")
_FCOL = re.search(r"!\$([A-Z]+)\$", _FAC_RANGE).group(1)
_FFIRST = int(re.search(r"\$(\d+):", _FAC_RANGE).group(1))
assert _FFIRST == _FIRST_DATA_ROW, (_FFIRST, _FIRST_DATA_ROW)

_KEY_ORDER = ["≤FY12"] + [f"FY{y}" for y in range(2013, 2032)]

def deflator_factor_cell(fy_or_key) -> str:
    """Absolute factor cell for an integer FY or text key (≤FY12 / FY2013..FY2031)."""
    key = f"FY{fy_or_key}" if isinstance(fy_or_key, int) else str(fy_or_key)
    return f"'{TAB_DEFLATORS}'!${_FCOL}${_FFIRST + _KEY_ORDER.index(key)}"
