"""workbook_master_tam (master_v2) - Distributed Shipbuilding Master TAM, lean rebuild.

One TAM-only workbook spanning all three programs treated INDIVIDUALLY - Virginia,
Columbia, and DDG-51 - plus the data spine each program's live formulas draw on.
The outsourcing-ceiling layer is deliberately tabled (not built here).

Flat layout (chosen 2026-06-21, mirroring the SAM award_classification refactor):
one file = one tab under sheets/, every NON-sheet helper is _-prefixed and exists
once (_layout / _tabs / _widths / _cuts). Data is combined BY TYPE - one SCN
Budget / Place of Performance / OBBBA / FYDP / Deflators sheet, each covering all
three programs - rather than per-program copies.

The shared raw-OOXML engine is the canonical ``workbook_core`` package at the
workspace root; sheet modules import ``workbook_core.*`` directly.

Two dirs are put on sys.path so both packages import regardless of entry point:
  - the build dir (this package's parent, ``workbook_factory/ddg/tam/``) so
    ``workbook_master_tam`` resolves;
  - the factory root (three levels up, ``workbook_factory/``) so the copied
    ``workbook_core`` resolves.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = str(_HERE.parents[1])   # workbook_factory/ddg/tam/
_CORE_DIR = str(_HERE.parents[3])       # workbook_factory/ (holds the copied workbook_core)

for _p in (_PROJECT_ROOT, _CORE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
