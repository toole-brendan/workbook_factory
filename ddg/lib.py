"""DDG-51 workbook package bindings and consolidated data locations.

This module is the new program-level home for the merged DDG workbook.  The
historical TAM/SAM packages remain as implementation compatibility layers, but
all workbook-ready CSV inputs resolve through the DDG-scoped data tree below.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parent

OUT = PROJECT_DIR / "20260630_Distributed Shipbuilding DDG51_v1.1.xlsx"
TITLE = "Distributed Shipbuilding - DDG-51 TAM + SAM"
CREATOR = "workbook_factory ddg/build_workbook.py"
APP_NAME = "workbook_factory"

DATA_DIR = PROJECT_DIR / "data"
WORKBOOK_INPUTS = DATA_DIR / "workbook_inputs"

TAM_BUDGET_DATA = WORKBOOK_INPUTS / "tam_budget"
SAM_AWARDS_DATA = WORKBOOK_INPUTS / "sam_awards"
SAM_SCOPE_DATA = SAM_AWARDS_DATA / "scope"
SAM_TX_DATA = SAM_AWARDS_DATA / "transactions"
SAM_SUPPLIER_DATA = SAM_AWARDS_DATA / "supplier"
SAM_CLASSIFICATION_DATA = SAM_AWARDS_DATA / "classification"
SAM_SWBS_DATA = SAM_AWARDS_DATA / "swbs"
SAM_HULL_DATA = SAM_AWARDS_DATA / "hull"
SAM_LIFECYCLE_DATA = SAM_AWARDS_DATA / "lifecycle"
SAM_REFERENCE_DATA = SAM_AWARDS_DATA / "reference"
AUDIT_DATA = DATA_DIR / "audit"
RESEARCH_WORKLIST_DATA = DATA_DIR / "research_worklists"

# Legacy stem -> consolidated workbook-input CSV.  The sheet modules still use
# the stems inherited from the source workbooks; keeping the alias here lets the
# data tree carry DDG-specific, explicit names without touching every formula module.
TAM_CSV_ALIASES = {
    "scn_budget": TAM_BUDGET_DATA / "ddg_scn_budget.csv",
    "ap_lltm": TAM_BUDGET_DATA / "ddg_ap_lltm.csv",
    "place_of_performance": TAM_BUDGET_DATA / "ddg_place_of_performance.csv",
    "obbba": TAM_BUDGET_DATA / "ddg_obbba.csv",
    "fydp_outyears": TAM_BUDGET_DATA / "ddg_fydp_outyears.csv",
    "deflators": TAM_BUDGET_DATA / "ref_tam_procurement_deflators_fy2026.csv",
}

SAM_CSV_ALIASES = {
    "prime_awards": SAM_SCOPE_DATA / "ddg_prime_awards.csv",
    "ddg_subaward_transactions": SAM_TX_DATA / "ddg_subaward_transactions.csv",
    "supplier_master": SAM_SUPPLIER_DATA / "ddg_supplier_master.csv",
    "supplier_year_activity": SAM_SUPPLIER_DATA / "ddg_supplier_year_activity.csv",
    "vendor_archetype_overrides": SAM_CLASSIFICATION_DATA / "ddg_vendor_archetype_overrides.csv",
    "naics6_archetype_map": SAM_CLASSIFICATION_DATA / "ddg_naics6_archetype_map.csv",
    "hii_swbs_crosswalk": SAM_SWBS_DATA / "ddg_hii_swbs_crosswalk.csv",
    "ddg_swbs_by_subsystem": SAM_SWBS_DATA / "ddg_swbs_by_subsystem.csv",
    "ddg_piid_hull_map": SAM_HULL_DATA / "ddg_piid_hull_map.csv",
    "ddg_hull_master": SAM_HULL_DATA / "ddg_hull_master.csv",
    "ddg_hull_exceptions": SAM_HULL_DATA / "ddg_hull_exceptions.csv",
    "ddg_vendor_hull_exposure": SAM_HULL_DATA / "ddg_vendor_hull_exposure.csv",
    "ddg_vendor_hull_swbs": SAM_HULL_DATA / "ddg_vendor_hull_swbs.csv",
    "ddg_cd_lifecycle_rollup": SAM_LIFECYCLE_DATA / "ddg_cd_lifecycle_rollup.csv",
    "ddg_cd_lifecycle_candidates": SAM_LIFECYCLE_DATA / "ddg_cd_lifecycle_candidates.csv",
    "deflators": SAM_REFERENCE_DATA / "ref_sam_procurement_deflators_fy2026.csv",
    "duplicate_audit": AUDIT_DATA / "duplicate_audit.csv",
    "duplicate_candidates": AUDIT_DATA / "duplicate_candidates.csv",
    # Kept for the current universe guard / research-prep lineage.  The rendered
    # DDG Program Vendors sheet now sources rows from Supplier Master.
    "ddg_program_vendors": RESEARCH_WORKLIST_DATA / "ddg_program_vendors.csv",
}

def resolve_tam_csv(stem: str) -> Path:
    try:
        return TAM_CSV_ALIASES[stem]
    except KeyError as exc:
        raise FileNotFoundError(
            f"unknown TAM CSV stem {stem!r}; add it to ddg.lib.TAM_CSV_ALIASES"
        ) from exc

def resolve_sam_csv(stem: str) -> Path:
    try:
        return SAM_CSV_ALIASES[stem]
    except KeyError as exc:
        raise FileNotFoundError(
            f"unknown SAM CSV stem {stem!r}; add it to ddg.lib.SAM_CSV_ALIASES"
        ) from exc
