"""Fully flattened DDG-51 sheet registry.

All runtime sheets now live under ``ddg.sheets``.  A small import-compatibility
shim maps the historical source package names to this package so formula-heavy
modules copied from the DDG-sliced TAM/SAM workbooks can continue to resolve
producer modules while the filesystem is no longer split into ``tam/`` and
``sam/`` halves.
"""
from __future__ import annotations

import sys
import types

_ROOT_ALIASES = ("workbook_master_tam", "workbook_award_classification_refactor")

def _install_package_aliases() -> None:
    this = sys.modules[__name__]
    for root in _ROOT_ALIASES:
        pkg = sys.modules.get(root)
        if pkg is None:
            pkg = types.ModuleType(root)
            sys.modules[root] = pkg
        pkg.__path__ = []
        setattr(pkg, "sheets", this)
        sys.modules[f"{root}.sheets"] = this

def _alias_many(*names: str) -> None:
    for name in names:
        mod = sys.modules[f"{__name__}.{name}"]
        for root in _ROOT_ALIASES:
            sys.modules[f"{root}.sheets.{name}"] = mod

_install_package_aliases()

# Shared helpers / references first, then aliases for historical import paths.
from . import (_cuts, _tabs, _italic, _inputfill, _layout, _factor, _periods,
               _widths, _text_input, _taxonomy, _structure_classes, _hulls)
_alias_many("_cuts", "_tabs", "_italic", "_inputfill", "_layout", "_factor",
            "_periods", "_widths", "_text_input", "_taxonomy", "_structure_classes", "_hulls")
from . import _flat, deflators, _fiscal, _program_vendors
_alias_many("_flat", "deflators", "_fiscal", "_program_vendors")

# TAM producer sheets / helpers.
from . import assumptions
_alias_many("assumptions")
from . import scn_budget, place_of_performance, obbba, fydp_outyears
_alias_many("scn_budget", "place_of_performance", "obbba", "fydp_outyears")
from . import _program_tam, ddg_tam, methodology, checks
_alias_many("_program_tam", "ddg_tam", "methodology", "checks")

# SAM inputs, data leaves, dimensions, models and summaries.
from . import (taxonomy, guide_methodology, hull_mapping_methodology, lifecycle_methodology,
               naics6_archetype_map, vendor_archetype_overrides, hii_swbs_crosswalk,
               ddg_piid_hull_map, ddg_hull_master, prime_awards)
_alias_many("taxonomy", "guide_methodology", "hull_mapping_methodology", "lifecycle_methodology",
            "naics6_archetype_map", "vendor_archetype_overrides", "hii_swbs_crosswalk",
            "ddg_piid_hull_map", "ddg_hull_master", "prime_awards")
from . import ddg_subaward_transactions
_alias_many("ddg_subaward_transactions")
from . import supplier_master, supplier_year_activity, ddg_program_vendors
_alias_many("supplier_master", "supplier_year_activity", "ddg_program_vendors")
from . import (ddg_swbs_rollup, ddg_hull_spend_summary, ddg_hull_coverage, ddg_hull_swbs,
               ddg_vendor_hull, ddg_vendor_hull_swbs, ddg_hull_exceptions,
               ddg_hull_lifecycle_stage, ddg_cd_lifecycle_coverage,
               ddg_cd_lifecycle_rollup, ddg_cd_lifecycle_candidates,
               domain_concentration, where_to_play)
_alias_many("ddg_swbs_rollup", "ddg_hull_spend_summary", "ddg_hull_coverage", "ddg_hull_swbs",
            "ddg_vendor_hull", "ddg_vendor_hull_swbs", "ddg_hull_exceptions",
            "ddg_hull_lifecycle_stage", "ddg_cd_lifecycle_coverage",
            "ddg_cd_lifecycle_rollup", "ddg_cd_lifecycle_candidates",
            "domain_concentration", "where_to_play")
from . import executive_summary
_alias_many("executive_summary")

SHEETS: list = [
    # Summary / answer pages.
    executive_summary.EXECUTIVE_SUMMARY,
    domain_concentration.DOMAIN_CONCENTRATION,
    where_to_play.WHERE_TO_PLAY,

    # Guide / method.
    methodology.METHODOLOGY,
    taxonomy.TAXONOMY,
    guide_methodology.METHODOLOGY,
    hull_mapping_methodology.HULL_MAPPING_METHODOLOGY,
    lifecycle_methodology.LIFECYCLE_METHODOLOGY,

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

    # Data / source evidence.
    scn_budget.SCN_BUDGET,
    place_of_performance.PLACE_OF_PERFORMANCE,
    obbba.OBBBA,
    fydp_outyears.FYDP_OUTYEARS,
    prime_awards.PRIME_AWARDS,
    ddg_subaward_transactions.DDG_SUBAWARD_TX,

    # Validation.
    checks.CHECKS,
]
