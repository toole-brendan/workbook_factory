"""workbook_award_classification_refactor - Award Classification Refactor workbook build pipeline.

The reference / classification workbook over the new-construction subaward vendor
base: an entity-level classification taxonomy (capability domain / operating role /
primary output), a first-pass classification roster, a wide vendor-context profile,
and per-program (DDG-51 / Virginia / Columbia) top-vendor work-description cuts.

This pipeline reconstructs the hand-built
``projects/distributed_shipbuilding/sam/sam_awards_data/20260620_Distributed Shipbuilding Master SAM_vS.xlsx`` through the shared
raw-OOXML engine so it carries the house style (title/section banners, header
underlines, tab colors by group, sized columns, native filterable tables, Arial 8 /
gutter layout). The cell content is extracted verbatim into ``extracted/*.csv`` by
``extract_classification_cuts.py``; the sheet modules style and render it.

Thin per-pipeline package: binds the output path, the extracted-data dir, and the
docProps identity (lib.py), and registers the sheet modules (sheets/). The shared
raw-OOXML engine is the canonical ``workbook_core`` package at the workspace root;
the sheet modules import ``workbook_core.*`` directly. There is no vendored copy of
workbook_core inside this pipeline -- it imports the single source of truth at
``<workspace root>/workbook_core``.

This module makes both packages importable regardless of entry point by putting two
dirs on sys.path:
  - the build dir (this package's parent, ``workbook_factory/ddg/sam/``) so
    ``workbook_award_classification_refactor`` resolves;
  - the factory root (three levels up, ``workbook_factory/``) so the copied
    ``workbook_core`` resolves.
When the build is launched via ``build_workbook.py`` the build dir is already
sys.path[0]; the factory root is prepended here so the ``workbook_core`` import
resolves.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = str(_HERE.parents[1])   # workbook_factory/ddg/sam/
_CORE_DIR = str(_HERE.parents[3])       # workbook_factory/ (holds the copied workbook_core)

for _p in (_PROJECT_ROOT, _CORE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
