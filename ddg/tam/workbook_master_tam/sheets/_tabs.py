"""_tabs - canonical worksheet (tab) names, in one place.

Local non-sheet helper (like _layout / _cuts / _widths). Tab names are
load-bearing: formulas/accessors reference a sheet by value and the packager
rejects duplicates rather than renaming. Centralizing the names here means a
rename happens in exactly one place.

Tab structure (group-contiguous, canonical summary -> guide -> inputs -> model
-> data -> validation order):
  [summary]    Executive Summary
  [guide]      Methodology
  [inputs]     Assumptions
  [model]      Virginia TAM · Columbia TAM · DDG-51 TAM   (programs treated individually)
  [data]       SCN Budget · Place of Performance · OBBBA Mandatory · FYDP Outyears · Deflators
  [validation] Checks   (live in-workbook QA; sorts last)
"""
from __future__ import annotations

TAB_EXEC_SUMMARY = "Executive Summary"
TAB_METHODOLOGY  = "Methodology"
TAB_ASSUMPTIONS  = "Assumptions"
# model - one tab per program
TAB_VIRGINIA_TAM = "Virginia TAM"
TAB_COLUMBIA_TAM = "Columbia TAM"
TAB_DDG_TAM      = "DDG-51 TAM"
# data - combined by type (all three programs in each)
TAB_SCN_BUDGET   = "SCN Budget"
TAB_POP          = "Place of Performance"
TAB_OBBBA        = "OBBBA Mandatory"
TAB_FYDP         = "FYDP Outyears"
TAB_DEFLATORS    = "Deflators"
# validation - live in-workbook checks + master check
TAB_CHECKS       = "Checks"

# All <= 31 chars (Excel sheet-name limit); the packager re-asserts this.
assert all(len(n) <= 31 for n in (
    TAB_EXEC_SUMMARY, TAB_METHODOLOGY, TAB_ASSUMPTIONS,
    TAB_VIRGINIA_TAM, TAB_COLUMBIA_TAM, TAB_DDG_TAM,
    TAB_SCN_BUDGET, TAB_POP, TAB_OBBBA, TAB_FYDP, TAB_DEFLATORS,
    TAB_CHECKS,
))
