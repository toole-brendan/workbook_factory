"""Shared build infrastructure for the DDG sheet modules (no tabs of its own).

CSV loading (cuts), the row-cursor / generic flat-sheet builder (layout, flat),
per-build style registration (styles), fiscal-window + reference constants
(fiscal, periods, tabs, widths, taxonomy, structure_classes), hull-formula
helpers (hulls), the program-vendor/TAM sheet factories (program_vendors,
program_tam), and the build-stopping integrity guards (integrity).
"""
from __future__ import annotations
