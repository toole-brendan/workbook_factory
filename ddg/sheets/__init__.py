"""Fully flattened DDG-51 sheet registry.

All runtime sheets live under ``ddg.sheets``; shared build infrastructure (CSV
loading, the row cursor, style registration, fiscal/reference constants, the
program-vendor/TAM factories, integrity guards) lives one level down in
``ddg.sheets.kit`` and is not a tab itself. Every module below imports its own
dependencies by real path, so this file just needs to import each TAB module
(for its side-effecting sheet build + to bind it into SHEETS) - Python resolves
the kit/ dependency graph on demand, no import-order bookkeeping required.
"""
from __future__ import annotations

# TAM producer sheets.
from . import assumptions
from . import scn_budget, place_of_performance, obbba, fydp_outyears
from . import deflators, ddg_tam, methodology

# SAM reference / source sheets. Guide modules are import-compatible but not visible tabs.
from . import (taxonomy, guide_methodology, hull_mapping_methodology,
               naics6_archetype_map, vendor_archetype_overrides, hii_swbs_crosswalk,
               ddg_piid_hull_map, ddg_hull_master, prime_awards)
from . import ddg_subaward_transactions
from . import supplier_master, supplier_year_activity, ddg_program_vendors
from . import (archetype_application_audit, ddg_swbs_rollup, swbs_coverage,
               ddg_hull_spend_summary, ddg_hull_coverage, ddg_hull_swbs,
               ddg_vendor_hull, ddg_vendor_hull_swbs, ddg_hull_exceptions,
               ddg_procurement_timing, ddg_full_span_drilldown,
               market_bridge, domain_concentration, where_to_play)
from . import executive_summary
from . import checks

SHEETS: list = [
    # Summary / answer pages.
    executive_summary.EXECUTIVE_SUMMARY,
    market_bridge.MARKET_BRIDGE,
    where_to_play.WHERE_TO_PLAY,
    domain_concentration.DOMAIN_CONCENTRATION,

    # Inputs / references.
    assumptions.ASSUMPTIONS,
    deflators.DEFLATORS,
    naics6_archetype_map.NAICS_ARCHETYPE_MAP,
    vendor_archetype_overrides.VENDOR_ARCHETYPE_OVERRIDES,
    hii_swbs_crosswalk.HII_SWBS_CROSSWALK,
    ddg_piid_hull_map.DDG_PIID_HULL_MAP,
    ddg_hull_master.DDG_HULL_MASTER,

    # Model / calculations.
    ddg_tam.DDG_TAM,
    supplier_master.SUPPLIER_MASTER,
    supplier_year_activity.SUPPLIER_YEAR_ACTIVITY,
    ddg_program_vendors.DDG_PROGRAM_VENDORS,
    archetype_application_audit.ARCHETYPE_APPLICATION_AUDIT,
    ddg_swbs_rollup.DDG_SWBS_ROLLUP,
    swbs_coverage.SWBS_COVERAGE,
    ddg_hull_coverage.DDG_HULL_COVERAGE,
    ddg_hull_spend_summary.DDG_HULL_SPEND,
    ddg_hull_swbs.DDG_HULL_SWBS,
    ddg_vendor_hull.DDG_VENDOR_HULL,
    ddg_vendor_hull_swbs.DDG_VENDOR_HULL_SWBS,
    ddg_hull_exceptions.DDG_HULL_EXCEPTIONS,
    ddg_procurement_timing.DDG_PROC_TIMING,
    ddg_full_span_drilldown.DDG_FULL_SPAN,

    # Data / source evidence.
    prime_awards.PRIME_AWARDS,
    ddg_subaward_transactions.DDG_SUBAWARD_TX,
    scn_budget.SCN_BUDGET,
    place_of_performance.PLACE_OF_PERFORMANCE,
    obbba.OBBBA,
    fydp_outyears.FYDP_OUTYEARS,

    # Validation.
    checks.CHECKS,
]
