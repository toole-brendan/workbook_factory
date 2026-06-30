"""Launcher for the workbook_award_classification_refactor build pipeline.

Run via:
    python build_workbook.py

Output:
    20260620_Distributed Shipbuilding Master SAM_vS.xlsx  (at the project root, projects/distributed_shipbuilding/sam/sam_awards_data/)

The shared raw-OOXML engine is the canonical ``workbook_core`` package at the
workspace root; all pipeline-specific binding lives in
``workbook_award_classification_refactor/lib.py`` and the sheet modules under
``workbook_award_classification_refactor/sheets/``.
"""
import sys

from workbook_award_classification_refactor.lib import build


if __name__ == "__main__":
    sys.exit(build())
