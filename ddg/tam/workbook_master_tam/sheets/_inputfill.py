"""_inputfill - pale-yellow input-cell fill for THIS workbook (scoped, per-build).

The ICAEW Financial Modelling Code (Layout - "Make inputs easy to find") says to
distinguish input cells "using a defined cell fill colour and/or a cell border, not
just a defined font colour". workbook_core marks hardcoded inputs by blue FONT only
(S_*_INPUT, no fill). Register pale-yellow filled clones of the input styles ONCE by
appending a fill + cellXfs entries to workbook_core.styles at build time, IN THIS
PROCESS ONLY - the same per-build scoping trick _factor.py / _italic.py use.
build_styles_xml() reads FILLS / CELL_XFS at build time, so appending here (at sheet
import, before packaging) is enough; no workbook_core source change, and every other
pipeline builds in its own process with unchanged style tables. The append is fully
additive: existing FILLS / CELL_XFS indices (and every S_* constant) are unchanged -
xfs reference fills by id, so a new trailing fill perturbs nothing.

Scope: applied to the editable behavioral knobs on the Assumptions tab (the model's
single edit surface). Raw transcribed source values on the data tabs keep blue-font-
only styling - they are a data-storage appendix, not the levers a user manipulates,
and the Code cautions against heavy formatting inside data tables.

Exports S_NUM_INPUT_FILL / S_PCT_INPUT_FILL / S_INT_INPUT_FILL: blue input font on a
pale-yellow fill, otherwise identical to S_NUM_INPUT / S_PCT_INPUT / S_INT_INPUT.
"""
from __future__ import annotations

import workbook_core.styles as _styles

# Idempotent registration (guards against a double-import via different paths).
if not getattr(_styles, "_inputfill_registered", None):
    # Pale yellow - the editable-input marker. Distinct from the think-cell paste
    # fill (FFFACD): both read as "pale yellow", but the semantics differ, so they
    # get distinct fills rather than sharing one index.
    _C_INPUT_FILL = "FFF2CC"
    _fill = len(_styles.FILLS)
    _styles.FILLS.append(
        f'<fill><patternFill patternType="solid">'
        f'<fgColor rgb="FF{_C_INPUT_FILL}"/></patternFill></fill>'
    )
    # Filled clones of S_NUM_INPUT (164 / fontId 3 blue), S_PCT_INPUT (165 / fontId 6
    # blue italic) and S_INT_INPUT (168 / fontId 3 blue) - same numFmt + font, plus the
    # pale-yellow fill (applyFill="1").
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
    _styles._inputfill_registered = (_num, _pct, _int)

S_NUM_INPUT_FILL, S_PCT_INPUT_FILL, S_INT_INPUT_FILL = _styles._inputfill_registered
