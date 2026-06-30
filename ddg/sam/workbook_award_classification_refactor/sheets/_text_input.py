"""_text_input - blue text-input style for THIS workbook (scoped, per-build).

workbook_core reserves its blue 'input' font for NUMERIC / date hardcoded values
(S_NUM_INPUT, S_INT_INPUT, S_DATE_INPUT); it ships no blue *text* style, because the
house rule is 'color = numeric cells only'. The program-vendor sheets carry one
genuine hardcoded text input - the Subawardee UEI key (the row's identity, the only
column that is correctly a literal rather than a formula) - which should read as
source input, not derived text. So we register a blue text style ONCE by appending to
workbook_core.styles.CELL_XFS at build time, IN THIS PROCESS ONLY (the same scoping
trick lib.py uses for tab colors and _yn.py uses for the centered Y/N style).
build_styles_xml() reads CELL_XFS at build time, so appending here - at sheet import,
before packaging - is enough; no workbook_core source change, and every other
pipeline builds in its own process with unchanged style tables.

Exports S_TEXT_INPUT (a blue-input-font clone of S_DEFAULT: numFmt 0 / no fill / no
border, font id 3 = the blue input font).
"""
from __future__ import annotations

import workbook_core.styles as _styles

# Idempotent registration (guards against a double-import via different paths).
if not getattr(_styles, "_text_input_registered", None):
    _s_text_input = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    )
    _styles._text_input_registered = _s_text_input

S_TEXT_INPUT = _styles._text_input_registered
