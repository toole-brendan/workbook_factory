"""Shared OOXML constants — the leaf module of the workbook engine.

The XML declaration + the SpreadsheetML namespace URIs that every other module
needs. Centralized here so the strings are defined once and cannot drift between
styles.py, primitives.py, tables.py, lib.py, and the probe.

No dependencies (imports nothing from workbook_core). Import direction:
    ooxml <- styles <- primitives <- tables <- lib
"""
from __future__ import annotations

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

# SpreadsheetML main schema (worksheet / workbook / styles roots, default xmlns).
NS_SS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
# officeDocument relationships (the xmlns:r on workbook.xml / worksheets, and the
# worksheet/styles relationship-type URIs in xl/_rels).
NS_PR = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
# package relationships (the xmlns on every *.rels file).
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

# Parser namespace map (ElementTree): the SpreadsheetML main schema under "a".
NS_MAP = {"a": NS_SS}
