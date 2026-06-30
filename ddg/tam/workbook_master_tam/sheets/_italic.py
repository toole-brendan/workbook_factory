"""_italic - italic body-text style for THIS workbook (scoped, per-build).

workbook_core ships no plain italic-black text style (its only italic body font is
S_NOTE's gray italic). The title-caption intro reads as an italicized note sitting
directly under the sheet banner, so we register an italic-black style ONCE by
appending to workbook_core.styles.CELL_XFS at build time, IN THIS PROCESS ONLY - the
same scoping trick the award_classification _italic.py uses. build_styles_xml() reads
CELL_XFS at build time, so appending here (at sheet import, before packaging) is
enough; no workbook_core source change, and every other pipeline builds in its own
process with unchanged style tables.

Exports S_ITALIC (an italic-black clone of S_DEFAULT: numFmt 0 / no fill / no border,
font id 5 = italic black).
"""
from __future__ import annotations

import workbook_core.styles as _styles

# Idempotent registration (guards against a double-import via different paths).
if not getattr(_styles, "_italic_registered", None):
    _s_italic = len(_styles.CELL_XFS)
    _styles.CELL_XFS.append(
        '<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    )
    _styles._italic_registered = _s_italic

S_ITALIC = _styles._italic_registered
