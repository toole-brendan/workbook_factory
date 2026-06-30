"""_inputfill - pale-yellow editable-input cell styles for THIS workbook (scoped).

workbook_core marks a hardcoded input cell with a blue FONT only (S_NUM_INPUT /
S_INT_INPUT / S_DATE_INPUT, and this workbook's S_TEXT_INPUT). On the curated
INPUTS-group sheets (the NAICS-6 archetype map, the (Program x UEI) overrides, the
HII->SWBS crosswalk, the deflators) we additionally paint the editable cells a pale
yellow, so the reader sees AT A GLANCE which cells are theirs to change vs. the live
formulas around them - the ICAEW Financial Modelling Code "mark your inputs" convention
the Master TAM workbook uses on its Assumptions tab.

This registers ONE new fill (FFF2CC) plus a FILLED clone of each input style this
workbook uses, by appending to workbook_core.styles.FILLS / CELL_XFS at build time,
IN THIS PROCESS ONLY - the same scoping trick lib.py (tab colors), _text_input.py and
_italic.py use. build_styles_xml() reads those lists at build time, so appending here
(at sheet import, before packaging) is enough; no workbook_core source change, and every
other pipeline builds in its own process with unchanged style tables.

Each filled clone is byte-for-byte its non-filled counterpart (same numFmtId / fontId 3 =
the blue input font) with only the new fillId added:
    S_NUM_INPUT_FILL  <- S_NUM_INPUT   (numFmt 164, float)
    S_INT_INPUT_FILL  <- S_INT_INPUT   (numFmt 168, integer)
    S_DATE_INPUT_FILL <- S_DATE_INPUT  (numFmt 169, date serial)
    S_TEXT_INPUT_FILL <- S_TEXT_INPUT  (numFmt 0,  blue text)
(No percent variant - this workbook has no editable percent inputs.)
"""
from __future__ import annotations

import workbook_core.styles as _styles

# Idempotent registration (guards against a double-import via different paths).
if not getattr(_styles, "_sam_inputfill_registered", None):
    _C_INPUT_FILL = "FFF2CC"   # pale yellow (matches the Master TAM input fill)

    _fill = len(_styles.FILLS)
    _styles.FILLS.append(
        '<fill><patternFill patternType="solid">'
        f'<fgColor rgb="FF{_C_INPUT_FILL}"/>'
        '</patternFill></fill>'
    )

    _num = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="164" fontId="3" fillId="{_fill}" borderId="0" xfId="0" '
        'applyNumberFormat="1" applyFont="1" applyFill="1"/>'
    )

    _int = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="168" fontId="3" fillId="{_fill}" borderId="0" xfId="0" '
        'applyNumberFormat="1" applyFont="1" applyFill="1"/>'
    )

    _date = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="169" fontId="3" fillId="{_fill}" borderId="0" xfId="0" '
        'applyNumberFormat="1" applyFont="1" applyFill="1"/>'
    )

    _text = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="0" fontId="3" fillId="{_fill}" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
    )

    _styles._sam_inputfill_registered = (_num, _int, _date, _text)

S_NUM_INPUT_FILL, S_INT_INPUT_FILL, S_DATE_INPUT_FILL, S_TEXT_INPUT_FILL = (
    _styles._sam_inputfill_registered
)
