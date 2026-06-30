"""_tabs - canonical worksheet (tab) names, in one place.

Local non-sheet helper (like _layout / _cuts / _widths). Tab names are
load-bearing: the packager rejects duplicates rather than renaming, and a native
table sits on a named sheet. Centralizing the names here means a rename happens in
exactly one place.

Tab structure (group-contiguous, canonical guide -> model -> data order):
  [guide] Taxonomy · Methodology
  [model] DDG Program Vendors · Virginia Program Vendors · Columbia Program Vendors
  [data]  DDG/Virginia/Columbia Subaward Transactions (the fact spine; each row
          carries its own domestic/foreign flag + country) ·
          Subawardee UEI Index · Subawardee Parents
"""
from __future__ import annotations

TAB_EXEC_SUMMARY     = "SAM Executive Summary"   # renamed in the combined book (TAM owns "Executive Summary")
TAB_TAXONOMY         = "Taxonomy"
TAB_METHODOLOGY      = "Classification Method"    # renamed in the combined book (TAM owns "Methodology")
TAB_NAICS_MAP        = "Mapping - NAICS Defaults"
TAB_SWBS_CROSSWALK   = "Mapping - HII Code to SWBS"
TAB_DDG_PROGRAM      = "DDG Program Vendors"
TAB_VIRGINIA_PROGRAM = "Virginia Program Vendors"
TAB_COLUMBIA_PROGRAM = "Columbia Program Vendors"
# per-subsystem SWBS roll-up (HII-Ingalls DDG-51 only carries SWBS)
TAB_SWBS_ROLLUP      = "DDG SWBS by Ship-System"
# lifetime capability-domain structure ("observed structure") — size x concentration, live
TAB_DOMAIN_CONC      = "Domain Concentration"
# annual Program x Archetype x FY "where to play" scorecard (over Supplier-Year Activity)
TAB_WHERE_TO_PLAY    = "Where to Play"
# observed reported subawards -> illustrative cumulative co-build scenario (HII co-build add-on)
TAB_MARKET_BRIDGE    = "Market Bridge"
# observed subaward reporting activity per (UEI x prime PIID): reports, action span, $
TAB_SUBAWARD_ACTIVITY = "Subaward Activity"
# raw transaction fact sheets (one row per subaward report id)
TAB_DDG_TX           = "DDG Subaward Transactions"
TAB_VIRGINIA_TX      = "Virginia Subaward Transactions"
TAB_COLUMBIA_TX      = "Columbia Subaward Transactions"
# in-scope prime contracts (USAspending award detail: authoritative prime PoP + obligations)
TAB_PRIME_AWARDS     = "Prime Awards"
# supplier dimension + classification (one row per UEI x program; merges the former
# Subawardee UEI Index + Subawardee Parents into one source)
TAB_SUPPLIER_MASTER  = "Supplier Master"
# annual supplier activity model (one row per Program x UEI x Federal FY; status + concentration)
TAB_SUPPLIER_YEAR    = "Supplier-Year Activity"
# archetype crosswalk (NAICS-6 default) + the hand-researched (Program, UEI) overrides
TAB_ARCHETYPE_OVERRIDES = "Mapping - Vendor Overrides"
# back-of-book price-deflator helper (Green Book Procurement TOA -> constant FY2026$ factor)
TAB_DEFLATORS        = "Deflators (SAM)"   # renamed in the combined book (TAM owns "Deflators")

# --- DDG hull-linkage layer ---
# curated reference inputs (the single source of truth for hull data)
TAB_PIID_HULL_MAP    = "Mapping - PIID to Hull"   # Prime PIID -> candidate hull family
TAB_HULL_MASTER      = "DDG Hull Master"          # one row per hull (builder / PIID / block / flight)
# derived hull roll-ups (live SUMIFS over the DDG tx leaf, keyed on Assigned Hull / Confidence)
TAB_HULL_SPEND       = "DDG Hull Spend Summary"   # one row per hull: assigned subaward $
TAB_HULL_COVERAGE    = "DDG Hull Coverage"        # exact vs inferred vs unassigned vs conflict $
TAB_HULL_SWBS        = "DDG Hull x SWBS"          # HII hulls x SWBS major group
TAB_VENDOR_HULL      = "DDG Vendor x Hull Exposure"  # vendor x assigned hull (long-format)
TAB_VENDOR_HULL_SWBS = "DDG Vendor x Hull x SWBS"  # vendor x assigned hull x ship-system (HII)
TAB_HULL_EXCEPTIONS  = "DDG Hull Exceptions"      # conflict / multi-hull / out-of-family log
TAB_HULL_METHODOLOGY = "Hull Mapping Methodology"  # the two-layer method + confidence grades

# --- construction-lifecycle layer (timing: when each subaward was made vs each hull's build) ---
TAB_HULL_LIFECYCLE   = "DDG Hull x Lifecycle Stage"   # exact A/B $ by hull x build stage
TAB_CD_LC_COVERAGE   = "DDG C-D Lifecycle Coverage"   # family-level $ by timing-narrowing result
TAB_CD_LC_ROLLUP     = "DDG C-D Lifecycle Rollup"     # one row per C/D tx: narrowed candidate set
TAB_CD_LC_CANDIDATES = "DDG C-D Lifecycle Candidates"  # one row per C/D tx x candidate hull
TAB_LIFECYCLE_METHOD = "Lifecycle Methodology"        # stages, windows, dual confidence, the wall

# All <= 31 chars (Excel sheet-name limit); the packager re-asserts this.
assert all(len(n) <= 31 for n in (
    TAB_EXEC_SUMMARY,
    TAB_TAXONOMY, TAB_METHODOLOGY, TAB_NAICS_MAP, TAB_SWBS_CROSSWALK,
    TAB_DDG_PROGRAM, TAB_VIRGINIA_PROGRAM, TAB_COLUMBIA_PROGRAM, TAB_SWBS_ROLLUP,
    TAB_DOMAIN_CONC, TAB_WHERE_TO_PLAY, TAB_MARKET_BRIDGE,
    TAB_DDG_TX, TAB_VIRGINIA_TX, TAB_COLUMBIA_TX,
    TAB_SUPPLIER_MASTER, TAB_SUPPLIER_YEAR, TAB_ARCHETYPE_OVERRIDES, TAB_DEFLATORS,
    TAB_SUBAWARD_ACTIVITY, TAB_PRIME_AWARDS,
    TAB_PIID_HULL_MAP, TAB_HULL_MASTER, TAB_HULL_SPEND, TAB_HULL_COVERAGE,
    TAB_HULL_SWBS, TAB_VENDOR_HULL, TAB_VENDOR_HULL_SWBS, TAB_HULL_EXCEPTIONS,
    TAB_HULL_METHODOLOGY,
    TAB_HULL_LIFECYCLE, TAB_CD_LC_COVERAGE, TAB_CD_LC_ROLLUP, TAB_CD_LC_CANDIDATES,
    TAB_LIFECYCLE_METHOD,
))
