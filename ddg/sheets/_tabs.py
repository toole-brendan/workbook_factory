"""_tabs - canonical worksheet (tab) names for the combined DDG-51 workbook.

ONE authoritative list of tab names (the TAM front matter merged with the SAM
classification book). Tab names are load-bearing: formulas/accessors reference a
sheet by value and the packager rejects duplicate names rather than renaming, so a
rename happens in exactly one place here.

Three names collided when the two pipelines merged - TAM owns the bare
"Executive Summary", "Methodology" and "Deflators"; the SAM equivalents keep
distinct CONSTANT names (TAB_SAM_EXEC_SUMMARY / TAB_CLASSIFICATION_METHOD /
TAB_SAM_DEFLATORS) so both render without an Excel duplicate-tab error.

Tab structure (group-contiguous, canonical summary -> guide -> inputs -> model ->
data -> validation):
  [summary]    Executive Summary - SAM Executive Summary - Domain Concentration - Where to Play
  [guide]      Methodology - Taxonomy - Classification Method - Hull Mapping - Lifecycle
  [inputs]     Assumptions - Mapping(NAICS/Overrides/HII/PIID) - DDG Hull Master - Deflators (x2)
  [model]      DDG-51 TAM - Supplier Master/Year - DDG roll-ups (vendors/SWBS/hull/lifecycle)
  [data]       SCN Budget - Place of Performance - OBBBA - FYDP - Prime Awards - Subaward Tx
  [validation] Checks
"""
from __future__ import annotations

# ===== TAM front matter + model + data =====
TAB_EXEC_SUMMARY = "Executive Summary"
TAB_METHODOLOGY  = "Methodology"
TAB_ASSUMPTIONS  = "Assumptions"
TAB_VIRGINIA_TAM = "Virginia TAM"     # unused in the DDG slice (kept for reference)
TAB_COLUMBIA_TAM = "Columbia TAM"     # unused in the DDG slice (kept for reference)
TAB_DDG_TAM      = "DDG-51 TAM"
TAB_SCN_BUDGET   = "SCN Budget"
TAB_POP          = "Place of Performance"
TAB_OBBBA        = "OBBBA Mandatory"
TAB_FYDP         = "FYDP Outyears"
TAB_DEFLATORS    = "Deflators"
TAB_CHECKS       = "Checks"

# ===== SAM classification book =====
TAB_SAM_EXEC_SUMMARY  = "SAM Executive Summary"   # TAM owns "Executive Summary"
TAB_TAXONOMY          = "Taxonomy"
TAB_CLASSIFICATION_METHOD = "Classification Method"  # TAM owns "Methodology"
TAB_NAICS_MAP         = "Mapping - NAICS Defaults"
TAB_SWBS_CROSSWALK    = "Mapping - HII Code to SWBS"
TAB_DDG_PROGRAM       = "DDG Program Vendors"
TAB_VIRGINIA_PROGRAM  = "Virginia Program Vendors"   # unused in the DDG slice
TAB_COLUMBIA_PROGRAM  = "Columbia Program Vendors"   # unused in the DDG slice
TAB_SWBS_ROLLUP       = "DDG SWBS by Ship-System"
TAB_DOMAIN_CONC       = "Domain Concentration"
TAB_WHERE_TO_PLAY     = "Where to Play"
TAB_MARKET_BRIDGE     = "Market Bridge"              # unused in the DDG slice
TAB_SUBAWARD_ACTIVITY = "Subaward Activity"          # unused in the DDG slice
TAB_DDG_TX            = "DDG Subaward Transactions"
TAB_VIRGINIA_TX       = "Virginia Subaward Transactions"   # unused in the DDG slice
TAB_COLUMBIA_TX       = "Columbia Subaward Transactions"   # unused in the DDG slice
TAB_PRIME_AWARDS      = "Prime Awards"
TAB_SUPPLIER_MASTER   = "Supplier Master"
TAB_SUPPLIER_YEAR     = "Supplier-Year Activity"
TAB_ARCHETYPE_OVERRIDES = "Mapping - Vendor Overrides"
TAB_SAM_DEFLATORS     = "Deflators (SAM)"            # TAM owns "Deflators"

# --- DDG hull-linkage layer ---
TAB_PIID_HULL_MAP    = "Mapping - PIID to Hull"
TAB_HULL_MASTER      = "DDG Hull Master"
TAB_HULL_SPEND       = "DDG Hull Spend Summary"
TAB_HULL_COVERAGE    = "DDG Hull Coverage"
TAB_HULL_SWBS        = "DDG Hull x SWBS"
TAB_VENDOR_HULL      = "DDG Vendor x Hull Exposure"
TAB_VENDOR_HULL_SWBS = "DDG Vendor x Hull x SWBS"
TAB_HULL_EXCEPTIONS  = "DDG Hull Exceptions"
TAB_HULL_METHODOLOGY = "Hull Mapping Methodology"

# --- construction-lifecycle layer ---
TAB_HULL_LIFECYCLE   = "DDG Hull x Lifecycle Stage"
TAB_CD_LC_COVERAGE   = "DDG C-D Lifecycle Coverage"
TAB_CD_LC_ROLLUP     = "DDG C-D Lifecycle Rollup"
TAB_CD_LC_CANDIDATES = "DDG C-D Lifecycle Candidates"
TAB_LIFECYCLE_METHOD = "Lifecycle Methodology"

# All <= 31 chars (Excel sheet-name limit); the packager re-asserts this.
assert all(len(n) <= 31 for n in (
    TAB_EXEC_SUMMARY, TAB_METHODOLOGY, TAB_ASSUMPTIONS, TAB_DDG_TAM,
    TAB_SCN_BUDGET, TAB_POP, TAB_OBBBA, TAB_FYDP, TAB_DEFLATORS, TAB_CHECKS,
    TAB_SAM_EXEC_SUMMARY, TAB_TAXONOMY, TAB_CLASSIFICATION_METHOD, TAB_NAICS_MAP,
    TAB_SWBS_CROSSWALK, TAB_DDG_PROGRAM, TAB_SWBS_ROLLUP, TAB_DOMAIN_CONC,
    TAB_WHERE_TO_PLAY, TAB_DDG_TX, TAB_PRIME_AWARDS, TAB_SUPPLIER_MASTER,
    TAB_SUPPLIER_YEAR, TAB_ARCHETYPE_OVERRIDES, TAB_SAM_DEFLATORS,
    TAB_PIID_HULL_MAP, TAB_HULL_MASTER, TAB_HULL_SPEND, TAB_HULL_COVERAGE,
    TAB_HULL_SWBS, TAB_VENDOR_HULL, TAB_VENDOR_HULL_SWBS, TAB_HULL_EXCEPTIONS,
    TAB_HULL_METHODOLOGY, TAB_HULL_LIFECYCLE, TAB_CD_LC_COVERAGE, TAB_CD_LC_ROLLUP,
    TAB_CD_LC_CANDIDATES, TAB_LIFECYCLE_METHOD,
))
