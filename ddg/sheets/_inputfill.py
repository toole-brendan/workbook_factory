"""Unified pale-yellow editable-input styles for the flattened DDG workbook."""
from __future__ import annotations

import workbook_core.styles as _styles

if not getattr(_styles, "_ddg_inputfill_registered", None):
    _fill = len(_styles.FILLS)
    _styles.FILLS.append(
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill>'
    )
    _num = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="164" fontId="3" fillId="{_fill}" borderId="0" xfId="0" '
        'applyNumberFormat="1" applyFont="1" applyFill="1"/>'
    )
    _pct = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        f'<xf numFmtId="165" fontId="6" fillId="{_fill}" borderId="0" xfId="0" '
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
    _styles._ddg_inputfill_registered = (_num, _pct, _int, _date, _text)

S_NUM_INPUT_FILL, S_PCT_INPUT_FILL, S_INT_INPUT_FILL, S_DATE_INPUT_FILL, S_TEXT_INPUT_FILL = (
    _styles._ddg_inputfill_registered
)
