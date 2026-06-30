"""ddg_program_vendors - the DDG-51 program-vendor sheet (a thin config over the factory).

One row per distinct subawardee UEI on the DDG-51 program across all corpus years,
entity-grain (NOT parent-collapsed); see _program_vendors for the shared column rationale,
the live-formula design, and the (UEI x Program) dimension / archetype wiring. This module
just binds the DDG-specific program label, transaction leaf, tab, CSV and intro. `model` group.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._program_vendors import (
    make_program_vendor_sheet,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_DDG_PROGRAM
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)

DDG_PROGRAM_VENDORS, ddg_pv_cols = make_program_vendor_sheet(
    program="DDG", tab=TAB_DDG_PROGRAM, tx_cols=ddg_tx_cols,
    csv_name="ddg_program_vendors", table_name="DdgProgramVendors",
    banner="§1 - DDG-51 subaward recipients",
    intro="Entity-level DDG-51 suppliers; reported hull-builder first-tier subawards in "
          "constant FY2026$.",
)
