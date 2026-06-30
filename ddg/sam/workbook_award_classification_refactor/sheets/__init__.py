"""Sheet registry - the tab order and grouping for the workbook.

ONE module per rendered sheet (one file = one tab). Tab order = the order of SHEETS
below. Each module exposes a single tables.SheetEntry and declares its group (see
workbook_core.groups); the blocks below keep each group contiguous and in
groups.SHEET_GROUPS canonical order. package_workbook() asserts that at build time.

Reader-first layers (answer -> scope/method -> model/calculations -> mappings/deflators ->
evidence):
  - summary : the reader-facing answer pages - Executive Summary, the Domain
              Concentration "where to play" cut, and the Market Bridge estimate.
  - guide   : scope & method - Taxonomy and Methodology.
  - model   : the Supplier Master dimension (override-first D / P resolved live) plus the
              derived cuts - the three program-vendor roll-ups (live SUMIFS / COUNTIFS /
              MINIFS / MAXIFS over the transaction leaves + a single Supplier Master
              match-row) and the per-subsystem SWBS roll-up.
  - inputs  : the editable classification levers + curated mappings - the NAICS-6 archetype
              defaults, the hand-researched (Program, UEI) overrides, the HII code -> SWBS
              crosswalk, and the deflators (hand-maintained values that drive formulas).
  - data    : the source evidence - the prime awards and the three raw subaward-transaction
              fact spines.

Shared NON-sheet helpers (imported by the sheet modules; NOT registered here):
  - _layout / _tabs / _widths / _cuts / _flat / _fiscal / _program_vendors / _taxonomy
  - _integrity : the build-stopping (Program x UEI) universe guard (called from lib.build)
"""
from __future__ import annotations

from . import (
    # summary (reader-facing answer pages)
    executive_summary,
    domain_concentration,
    where_to_play,
    # guide (scope & method)
    taxonomy,
    guide_methodology,
    hull_mapping_methodology,
    lifecycle_methodology,
    # model (Supplier Master dimension + derived program-vendor roll-ups + per-subsystem SWBS roll-up
    #        + the DDG hull-linkage roll-ups + the construction-lifecycle roll-ups)
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
    # inputs (editable classification levers + curated mappings + deflators)
    naics6_archetype_map,
    vendor_archetype_overrides,
    hii_swbs_crosswalk,
    ddg_piid_hull_map,
    ddg_hull_master,
    deflators,
    # data (source evidence: prime awards + the DDG raw subaward-transaction spine)
    prime_awards,
    ddg_subaward_transactions,
)


SHEETS: list = [
    # --- Summary (the answer pages) ---
    executive_summary.EXECUTIVE_SUMMARY,
    domain_concentration.DOMAIN_CONCENTRATION,
    where_to_play.WHERE_TO_PLAY,
    # --- Guide (scope & method) ---
    taxonomy.TAXONOMY,
    guide_methodology.METHODOLOGY,
    hull_mapping_methodology.HULL_MAPPING_METHODOLOGY,
    lifecycle_methodology.LIFECYCLE_METHODOLOGY,
    # --- Model / calculations (Supplier Master dimension + program-vendor roll-ups + SWBS roll-up
    #     + the DDG hull-linkage roll-ups + the construction-lifecycle roll-ups) ---
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
    # --- Inputs / mappings (editable classification levers + curated mappings + deflators) ---
    naics6_archetype_map.NAICS_ARCHETYPE_MAP,
    vendor_archetype_overrides.VENDOR_ARCHETYPE_OVERRIDES,
    hii_swbs_crosswalk.HII_SWBS_CROSSWALK,
    ddg_piid_hull_map.DDG_PIID_HULL_MAP,
    ddg_hull_master.DDG_HULL_MASTER,
    deflators.DEFLATORS,
    # --- Data (source evidence: prime awards + the DDG raw subaward-transaction spine) ---
    prime_awards.PRIME_AWARDS,
    ddg_subaward_transactions.DDG_SUBAWARD_TX,
]
