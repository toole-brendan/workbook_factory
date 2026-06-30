"""ddg pipeline bindings - the single home for this workbook's paths + identity.

The OOXML engine lives in the shared ``workbook_core`` package at the factory root.
This module is intentionally thin: it binds the output path, the data root, and the
docProps identity. The sheet modules import ``workbook_core.*`` directly for the
engine and ``sheets._data`` (which reads ``DATA_DIR`` from here) for their CSV inputs.

Data layout (see data/README.md): every build input lives under ``data/`` with a
DDG-specific or reference name; ``sheets._data`` maps each module's terse logical
stem to its concrete path, so the repository itself shows that this is a DDG-scoped
workbook without needing the source-extraction context.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent        # workbook_factory/ddg/
DATA_DIR = PROJECT_DIR / "data"                       # all build + guard CSV inputs

OUT = PROJECT_DIR / "20260630_Distributed Shipbuilding DDG51_v1.1.xlsx"

TITLE = "Distributed Shipbuilding - DDG-51 TAM + SAM"
CREATOR = "workbook_factory ddg/build_workbook.py"
APP_NAME = "workbook_factory"
