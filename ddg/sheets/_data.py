"""_data - the build's data manifest: logical stem -> concrete file under data/.

Sheet code references a CSV by a terse LOGICAL stem (``supplier_master``,
``scn_budget``, ``deflators``). The physical file carries a DDG-specific or
reference NAME in a category folder (``ddg_supplier_master.csv`` under
``sam_awards/supplier/``). This module is the single bridge between the two, so:

  - the repository shows DDG-specificity in every path + file stem, while
  - the sheet modules stay terse and source-agnostic, and
  - a future Virginia/Columbia extraction cannot silently reuse a DDG file - it
    would have to add its own manifest rows.

Resolution is SIDE-AWARE (``tam`` vs ``sam``) because the two pipelines each have a
``deflators`` stem pointing at a different reference table. ``_tam_cuts`` calls
``tam(stem)``; ``_sam_cuts`` (and ``_sam_integrity``) call ``sam(stem)``.

Every stem here is read from disk by a sheet's ``make_flat_sheet(csv_name=...)``
(when no in-memory ``table=`` is given), a TAM ``_tam_cuts.load_rows`` call, or a
``_sam_integrity`` guard. Stems consumed only in-memory (e.g. ``ddg_program_vendors``,
the hull roll-ups, ``where_to_play``) are intentionally absent.
"""
from __future__ import annotations

from pathlib import Path

from lib import DATA_DIR

_INPUTS = "workbook_inputs"

# logical stem -> path relative to DATA_DIR.  (consumer modules noted for governance)
_TAM = {
    "scn_budget":            f"{_INPUTS}/tam_budget/ddg_scn_budget.csv",            # scn_budget
    "ap_lltm":               f"{_INPUTS}/tam_budget/ddg_ap_lltm.csv",               # scn_budget
    "place_of_performance":  f"{_INPUTS}/tam_budget/ddg_place_of_performance.csv",  # place_of_performance
    "obbba":                 f"{_INPUTS}/tam_budget/ddg_obbba.csv",                 # obbba
    "fydp_outyears":         f"{_INPUTS}/tam_budget/ddg_fydp_outyears.csv",         # fydp_outyears
    "deflators":             f"{_INPUTS}/tam_budget/ref_tam_procurement_deflators_fy2026.csv",  # tam_deflators
}
_SAM = {
    # scope
    "prime_awards":               f"{_INPUTS}/sam_awards/scope/ddg_prime_awards.csv",          # prime_awards, _sam_integrity
    "prime_contract_scope":       f"{_INPUTS}/sam_awards/scope/ddg_prime_contract_scope.csv",  # _sam_integrity (guard manifest)
    # transactions
    "ddg_subaward_transactions":  f"{_INPUTS}/sam_awards/transactions/ddg_subaward_transactions.csv",  # ddg_subaward_transactions + guards
    # supplier
    "supplier_master":            f"{_INPUTS}/sam_awards/supplier/ddg_supplier_master.csv",        # supplier_master + guards
    "supplier_year_activity":     f"{_INPUTS}/sam_awards/supplier/ddg_supplier_year_activity.csv", # supplier_year_activity + guard
    # classification
    "naics6_archetype_map":       f"{_INPUTS}/sam_awards/classification/ddg_naics6_archetype_map.csv",       # naics6_archetype_map + guards
    "vendor_archetype_overrides": f"{_INPUTS}/sam_awards/classification/ddg_vendor_archetype_overrides.csv", # vendor_archetype_overrides + guard
    # swbs
    "hii_swbs_crosswalk":         f"{_INPUTS}/sam_awards/swbs/ddg_hii_swbs_crosswalk.csv",  # hii_swbs_crosswalk
    "ddg_swbs_by_subsystem":      f"{_INPUTS}/sam_awards/swbs/ddg_swbs_by_subsystem.csv",   # ddg_swbs_rollup
    # hull
    "ddg_piid_hull_map":          f"{_INPUTS}/sam_awards/hull/ddg_piid_hull_map.csv",        # ddg_piid_hull_map + guards
    "ddg_hull_master":            f"{_INPUTS}/sam_awards/hull/ddg_hull_master.csv",          # ddg_hull_master + guards
    "ddg_hull_exceptions":        f"{_INPUTS}/sam_awards/hull/ddg_hull_exceptions.csv",      # ddg_hull_exceptions
    "ddg_vendor_hull_exposure":   f"{_INPUTS}/sam_awards/hull/ddg_vendor_hull_exposure.csv", # ddg_vendor_hull
    "ddg_vendor_hull_swbs":       f"{_INPUTS}/sam_awards/hull/ddg_vendor_hull_swbs.csv",      # ddg_vendor_hull_swbs
    # lifecycle
    "ddg_cd_lifecycle_rollup":     f"{_INPUTS}/sam_awards/lifecycle/ddg_cd_lifecycle_rollup.csv",     # ddg_cd_lifecycle_rollup + guard
    "ddg_cd_lifecycle_candidates": f"{_INPUTS}/sam_awards/lifecycle/ddg_cd_lifecycle_candidates.csv", # ddg_cd_lifecycle_candidates + guard
    # reference
    "deflators":                  f"{_INPUTS}/sam_awards/reference/ref_sam_procurement_deflators_fy2026.csv",  # sam_deflators
    # audit / guard inputs (not rendered sheets)
    "duplicate_audit":            "audit/duplicate_audit.csv",       # _sam_integrity
    "duplicate_candidates":       "audit/duplicate_candidates.csv",  # _sam_integrity
}


def _resolve(table: dict, stem: str) -> Path:
    try:
        rel = table[stem]
    except KeyError:
        raise KeyError(
            f"unknown data stem {stem!r}; add it to sheets/_data.py "
            f"(known: {sorted(table)})") from None
    return DATA_DIR / rel


def tam(stem: str) -> Path:
    """Path to the TAM-side CSV for a logical stem."""
    return _resolve(_TAM, stem)


def sam(stem: str) -> Path:
    """Path to the SAM-side CSV for a logical stem."""
    return _resolve(_SAM, stem)
