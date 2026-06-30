"""Merged DDG-51 sheet registry.

This registry is the display order for the consolidated DDG workbook.  The sheet
implementation still reuses the already-DDG-sliced TAM/SAM modules, but the
workbook is now composed as one DDG program rather than two visible halves.
"""
from __future__ import annotations

# Historical TAM implementation modules.
from workbook_master_tam.sheets import (
    methodology as tam_methodology,
    assumptions,
    ddg_tam,
    scn_budget,
    place_of_performance,
    obbba,
    fydp_outyears,
    deflators as tam_deflators,
    checks,
)

# Historical SAM implementation modules.
from workbook_award_classification_refactor.sheets import (
    taxonomy,
    guide_methodology as classification_method,
    hull_mapping_methodology,
    lifecycle_methodology,
    naics6_archetype_map,
    vendor_archetype_overrides,
    hii_swbs_crosswalk,
    ddg_piid_hull_map,
    ddg_hull_master,
    deflators as sam_deflators,
    supplier_master,
    supplier_year_activity,
    ddg_program_vendors,
    ddg_swbs_rollup,
    ddg_hull_spend_summary,
    ddg_hull_coverage,
    ddg_hull_swbs,
    ddg_vendor_hull,
    ddg_vendor_hull_swbs,
    ddg_hull_exceptions,
    ddg_hull_lifecycle_stage,
    ddg_cd_lifecycle_coverage,
    ddg_cd_lifecycle_rollup,
    ddg_cd_lifecycle_candidates,
    domain_concentration,
    where_to_play,
    prime_awards,
    ddg_subaward_transactions,
)

from . import executive_summary

SHEETS: list = [
    # --- Summary / answer pages ---
    executive_summary.EXECUTIVE_SUMMARY,
    domain_concentration.DOMAIN_CONCENTRATION,
    where_to_play.WHERE_TO_PLAY,

    # --- Guide / method ---
    tam_methodology.METHODOLOGY,
    taxonomy.TAXONOMY,
    classification_method.METHODOLOGY,
    hull_mapping_methodology.HULL_MAPPING_METHODOLOGY,
    lifecycle_methodology.LIFECYCLE_METHODOLOGY,

    # --- Inputs / editable levers ---
    assumptions.ASSUMPTIONS,
    naics6_archetype_map.NAICS_ARCHETYPE_MAP,
    vendor_archetype_overrides.VENDOR_ARCHETYPE_OVERRIDES,
    hii_swbs_crosswalk.HII_SWBS_CROSSWALK,
    ddg_piid_hull_map.DDG_PIID_HULL_MAP,
    ddg_hull_master.DDG_HULL_MASTER,
    sam_deflators.DEFLATORS,

    # --- Model / calculations ---
    ddg_tam.DDG_TAM,
    supplier_master.SUPPLIER_MASTER,
    supplier_year_activity.SUPPLIER_YEAR_ACTIVITY,
    ddg_program_vendors.DDG_PROGRAM_VENDORS,
    ddg_swbs_rollup.DDG_SWBS_ROLLUP,
    ddg_hull_spend_summary.DDG_HULL_SPEND,
    ddg_hull_coverage.DDG_HULL_COVERAGE,
    ddg_hull_swbs.DDG_HULL_SWBS,
    ddg_vendor_hull.DDG_VENDOR_HULL,
    ddg_vendor_hull_swbs.DDG_VENDOR_HULL_SWBS,
    ddg_hull_exceptions.DDG_HULL_EXCEPTIONS,
    ddg_hull_lifecycle_stage.DDG_HULL_LIFECYCLE,
    ddg_cd_lifecycle_coverage.DDG_CD_LC_COVERAGE,
    ddg_cd_lifecycle_rollup.DDG_CD_LC_ROLLUP,
    ddg_cd_lifecycle_candidates.DDG_CD_LC_CANDIDATES,

    # --- Data / source evidence ---
    scn_budget.SCN_BUDGET,
    place_of_performance.PLACE_OF_PERFORMANCE,
    obbba.OBBBA,
    fydp_outyears.FYDP_OUTYEARS,
    tam_deflators.DEFLATORS,
    prime_awards.PRIME_AWARDS,
    ddg_subaward_transactions.DDG_SUBAWARD_TX,

    # --- Validation ---
    checks.CHECKS,
]
