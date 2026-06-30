"""Sheet registry - the one tab order + grouping for the combined DDG-51 workbook.

ONE module per rendered sheet (one file = one tab), one flat package (the former
``tam/`` and ``sam/`` split is gone). Each module exposes a single
``tables.SheetEntry`` declaring its group (see ``workbook_core.groups``); the
packager keeps each group contiguous and in the canonical
``summary -> guide -> inputs -> model -> data -> validation`` order and rejects
duplicate tab names.

Two import orders live here on purpose:
  - the ``from . import (...)`` block imports producers before consumers, so a
    promoted accessor (``ddg_tam.tam_cell``, ``ddg_program_vendors.ddg_pv_cols``)
    exists by the time a summary/model tab references it. Python's import graph
    already enforces this; listing the TAM block then the SAM block (each in its
    own working order) keeps it explicit.
  - ``SHEETS`` lists the tabs in DISPLAY order (summary first), which differs from
    import order - the reader meets the answer pages before the data spine.

Shared NON-sheet helpers (imported by the sheet modules; NOT registered):
  _tabs (names) - _data (CSV manifest) - _tam_*/_sam_* leaves (layout, widths,
  cuts, fills, fiscal, flat, taxonomy, integrity, ...).
"""
from __future__ import annotations

from . import (
    # --- TAM block (front matter + model + data spine) ---
    executive_summary,
    methodology,
    assumptions,
    ddg_tam,
    scn_budget,
    place_of_performance,
    obbba,
    fydp_outyears,
    tam_deflators,
    checks,
    # --- SAM block (answer pages + classification model + evidence) ---
    domain_concentration,
    where_to_play,
    taxonomy,
    classification_method,
    hull_mapping_methodology,
    lifecycle_methodology,
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
    naics6_archetype_map,
    vendor_archetype_overrides,
    hii_swbs_crosswalk,
    ddg_piid_hull_map,
    ddg_hull_master,
    sam_deflators,
    prime_awards,
    ddg_subaward_transactions,
)


SHEETS: list = [
    # --- Summary (the answer pages) ---
    executive_summary.EXECUTIVE_SUMMARY,            # merged TAM + SAM front door
    domain_concentration.DOMAIN_CONCENTRATION,
    where_to_play.WHERE_TO_PLAY,
    # --- Guide (scope & method) ---
    methodology.METHODOLOGY,                         # TAM ("Methodology")
    taxonomy.TAXONOMY,
    classification_method.METHODOLOGY,               # SAM ("Classification Method")
    hull_mapping_methodology.HULL_MAPPING_METHODOLOGY,
    lifecycle_methodology.LIFECYCLE_METHODOLOGY,
    # --- Inputs (editable levers + curated mappings + deflators) ---
    assumptions.ASSUMPTIONS,
    naics6_archetype_map.NAICS_ARCHETYPE_MAP,
    vendor_archetype_overrides.VENDOR_ARCHETYPE_OVERRIDES,
    hii_swbs_crosswalk.HII_SWBS_CROSSWALK,
    ddg_piid_hull_map.DDG_PIID_HULL_MAP,
    ddg_hull_master.DDG_HULL_MASTER,
    tam_deflators.DEFLATORS,
    sam_deflators.DEFLATORS,
    # --- Model (TAM engine + Supplier dimension + DDG roll-ups) ---
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
    # --- Data (source evidence) ---
    scn_budget.SCN_BUDGET,
    place_of_performance.PLACE_OF_PERFORMANCE,
    obbba.OBBBA,
    fydp_outyears.FYDP_OUTYEARS,
    prime_awards.PRIME_AWARDS,
    ddg_subaward_transactions.DDG_SUBAWARD_TX,
    # --- Validation ---
    checks.CHECKS,
]
