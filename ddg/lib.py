"""DDG-51 workbook package bindings and consolidated data locations."""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parent

OUT = PROJECT_DIR / "20260630_Distributed Shipbuilding DDG51_vS.xlsx"
TITLE = "Distributed Shipbuilding - DDG-51 TAM + SAM"
CREATOR = "workbook_factory ddg/build_workbook.py"
APP_NAME = "workbook_factory"

# Reader-facing SAM transaction window: enough lookback to capture early Flight III
# award / AP-LLTM / construction activity. The in-progress FY is INCLUDED but partial
# (FSRS subaward reporting lags several months); per-FY exhibits flag it.
SAM_TX_FY_START = 2013
SAM_TX_FY_END = 2026
SAM_LAST_COMPLETE_FY = 2025           # last fully-reported federal FY
SAM_REPORTED_THROUGH = "May 2026"     # latest subaward date in the pull (update per re-pull)
SAM_TX_WINDOW_LABEL = f"FY{SAM_TX_FY_START}-FY{SAM_TX_FY_END}"
SAM_PARTIAL_NOTE = (f"FY{SAM_TX_FY_END} is partial - subawards reported through "
                    f"{SAM_REPORTED_THROUGH}; FSRS reporting lags several months")
SAM_TX_WINDOW_LABEL_FULL = f"{SAM_TX_WINDOW_LABEL} ({SAM_PARTIAL_NOTE})"

# Bridge axis: TAM budget years (start FY2022) ∩ SAM years. Per-FY, never pooled;
# the two universes share an axis ONLY on the bridge exhibits.
BRIDGE_FYS = tuple(range(2022, SAM_TX_FY_END + 1))

# Pool window for supplier-STRUCTURE metrics (concentration / incumbency / where-to-play):
# trailing N complete FYs. Single-year supplier shares are lumpy (one grand block or EOQ
# buy swings a year), so structure metrics pool by design - but over a NAMED, derived
# window that rolls forward when the next FY completes, not a frozen literal.
POOL_N = 4
POOL_FYS = tuple(range(SAM_LAST_COMPLETE_FY - POOL_N + 1, SAM_LAST_COMPLETE_FY + 1))
POOL_LABEL = f"FY{POOL_FYS[0]}-FY{POOL_FYS[-1]} (trailing {POOL_N} complete FYs)"

DATA_DIR = PROJECT_DIR / "data"
WORKBOOK_INPUTS = DATA_DIR / "workbook_inputs"
REFERENCE_DATA = WORKBOOK_INPUTS / "reference"

TAM_BUDGET_DATA = WORKBOOK_INPUTS / "tam_budget"
SAM_AWARDS_DATA = WORKBOOK_INPUTS / "sam_awards"
SAM_SCOPE_DATA = SAM_AWARDS_DATA / "scope"
SAM_TX_DATA = SAM_AWARDS_DATA / "transactions"
SAM_SUPPLIER_DATA = SAM_AWARDS_DATA / "supplier"
SAM_CLASSIFICATION_DATA = SAM_AWARDS_DATA / "classification"
SAM_SWBS_DATA = SAM_AWARDS_DATA / "swbs"
SAM_HULL_DATA = SAM_AWARDS_DATA / "hull"
SAM_LIFECYCLE_DATA = SAM_AWARDS_DATA / "lifecycle"
AUDIT_DATA = DATA_DIR / "audit"
RESEARCH_WORKLIST_DATA = DATA_DIR / "research_worklists"

CSV_ALIASES = {
    # Shared references.
    "deflators": REFERENCE_DATA / "ref_procurement_deflators_fy2026.csv",

    # TAM budget / opportunity inputs.
    "scn_budget": TAM_BUDGET_DATA / "ddg_scn_budget.csv",
    "ap_lltm": TAM_BUDGET_DATA / "ddg_ap_lltm.csv",
    "place_of_performance": TAM_BUDGET_DATA / "ddg_place_of_performance.csv",
    "obbba": TAM_BUDGET_DATA / "ddg_obbba.csv",
    "fydp_outyears": TAM_BUDGET_DATA / "ddg_fydp_outyears.csv",

    # SAM award / supplier inputs.
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
    "ddg_grand_block_subawards": SAM_HULL_DATA / "ddg_grand_block_subawards.csv",
    "ddg_hull_exceptions": SAM_HULL_DATA / "ddg_hull_exceptions.csv",
    "ddg_vendor_hull_exposure": SAM_HULL_DATA / "ddg_vendor_hull_exposure.csv",
    "ddg_vendor_hull_swbs": SAM_HULL_DATA / "ddg_vendor_hull_swbs.csv",
    "ddg_procurement_timing": SAM_LIFECYCLE_DATA / "ddg_procurement_timing.csv",

    # Guard / worklist inputs.
    "duplicate_audit": AUDIT_DATA / "duplicate_audit.csv",
    "duplicate_candidates": AUDIT_DATA / "duplicate_candidates.csv",
    "ddg_program_vendors": RESEARCH_WORKLIST_DATA / "ddg_program_vendors.csv",
}

def resolve_csv(stem: str) -> Path:
    try:
        return CSV_ALIASES[stem]
    except KeyError as exc:
        raise FileNotFoundError(
            f"unknown DDG CSV stem {stem!r}; add it to ddg.lib.CSV_ALIASES"
        ) from exc

# Backward-compatible names used by the historical source modules that now live in ddg.sheets.
def resolve_tam_csv(stem: str) -> Path: return resolve_csv(stem)
def resolve_sam_csv(stem: str) -> Path: return resolve_csv(stem)
