"""Compatibility launcher for the consolidated DDG-51 workbook build.

``build_workbook.py`` is now the primary entrypoint.  This file remains so older
docs / shell history that call ``python build_ddg.py`` still build the same book.
"""
from __future__ import annotations

import sys

from build_workbook import build

if __name__ == "__main__":
    sys.exit(build())
