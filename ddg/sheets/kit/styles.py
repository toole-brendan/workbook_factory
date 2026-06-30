"""Per-build style registrations for THIS workbook (scoped, process-local).

workbook_core ships only the style primitives every pipeline needs in common; a few
cell treatments here are DDG-specific (or simply missing upstream) and are registered
ONCE by appending to the relevant workbook_core.styles list at build time, IN THIS
PROCESS ONLY - the same scoping trick every block below uses, each guarded by its own
idempotent sentinel attribute (so a double-import via two different paths is a no-op).
build_styles_xml() reads these lists at build time, so appending here - at sheet
import, before packaging - is enough; no workbook_core source change, and every other
pipeline builds in its own process with unchanged style tables.
"""
from __future__ import annotations

import workbook_core.styles as _styles

# --- S_ITALIC -----------------------------------------------------------------
# workbook_core ships no plain italic-black text style (its only italic body font is
# S_NOTE's gray italic). The Taxonomy intros read as italicized captions sitting
# directly under each section banner.
#
# Exports S_ITALIC (an italic-black clone of S_DEFAULT: numFmt 0 / no fill / no
# border, font id 5 = italic black).
if not getattr(_styles, "_sam_italic_registered", None):
    _s_italic = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        '<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    )
    _styles._sam_italic_registered = _s_italic

S_ITALIC = _styles._sam_italic_registered

# --- S_TEXT_INPUT ---------------------------------------------------------------
# workbook_core reserves its blue 'input' font for NUMERIC / date hardcoded values
# (S_NUM_INPUT, S_INT_INPUT, S_DATE_INPUT); it ships no blue *text* style, because
# the house rule is 'color = numeric cells only'. The program-vendor sheets carry
# one genuine hardcoded text input - the Subawardee UEI key (the row's identity,
# the only column that is correctly a literal rather than a formula) - which should
# read as source input, not derived text.
#
# Exports S_TEXT_INPUT (a blue-input-font clone of S_DEFAULT: numFmt 0 / no fill /
# no border, font id 3 = the blue input font).
if not getattr(_styles, "_text_input_registered", None):
    _s_text_input = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    )
    _styles._text_input_registered = _s_text_input

S_TEXT_INPUT = _styles._text_input_registered

# --- S_*_INPUT_FILL (pale-yellow editable inputs) --------------------------------
# Unified pale-yellow editable-input styles for the flattened DDG workbook.
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

# --- S_FACTOR -------------------------------------------------------------------
# workbook_core ships #,##0.0 (numFmt 164, ONE decimal) but no plain two-decimal
# format - which the deflator factors need: 1.10 / 1.07 / 1.05 collapse to "1.1" at
# one decimal, so the displayed value would no longer be the exact multiplier.
#
# Exports S_FACTOR (numFmt '0.00;-0.00;"-"', default black font; zero renders "-").
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
