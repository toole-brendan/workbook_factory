"""_factor - a two-decimal numeric style for THIS workbook (scoped, per-build).

workbook_core ships #,##0.0 (numFmt 164, ONE decimal) but no plain two-decimal
format - which the deflator factors need: 1.10 / 1.07 / 1.05 collapse to "1.1" at
one decimal, so the displayed value would no longer be the exact multiplier. Register
a two-decimal numFmt + style ONCE by appending to workbook_core.styles.NUM_FMTS /
CELL_XFS at build time, IN THIS PROCESS ONLY - the same per-build scoping trick
_italic.py uses. build_styles_xml() reads both lists at build time, so appending here
(at sheet import, before packaging) is enough; no workbook_core source change, and
every other pipeline builds in its own process with unchanged style tables.

Exports S_FACTOR (numFmt '0.00;-0.00;"-"', default black font; zero renders "-").
"""
from __future__ import annotations

import workbook_core.styles as _styles

# Idempotent registration (guards against a double-import via different paths).
if not getattr(_styles, "_factor2dp_registered", None):
    _FMT_ID = 170   # 164-169 are taken by workbook_core; 170 is the first free id.
    _styles.NUM_FMTS.append((_FMT_ID, '0.00;-0.00;"-"'))
    _s_factor = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="{_FMT_ID}" fontId="0" fillId="0" borderId="0" xfId="0" '
        'applyNumberFormat="1"/>'
    )
    _styles._factor2dp_registered = _s_factor

S_FACTOR = _styles._factor2dp_registered
