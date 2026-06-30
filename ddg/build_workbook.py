"""Build the consolidated DDG-51 workbook.

The source workbooks started as separate TAM and SAM pipelines.  This entrypoint
makes DDG the runtime unit: one sheet registry, one merged Executive Summary, and
one consolidated DDG-scoped data tree.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# Repository root is needed for ``import ddg`` / ``import workbook_core``.  The
# historical implementation packages remain on sys.path while their modules are
# folded into the consolidated DDG registry.
for _p in (_ROOT, _HERE / "tam", _HERE / "sam"):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

from workbook_core.primitives import set_normalize_dashes

# Several flat SAM sheets build their XML at import time, so dash normalization
# must be enabled before importing the registry.
set_normalize_dashes(True)

import workbook_core.groups as _groups
from workbook_core.lib import package_workbook

from ddg.lib import OUT, TITLE, CREATOR, APP_NAME
from ddg.sheets import SHEETS
from ddg.sheets import _sam_integrity as ig

_MERGED_ORDER = [
    "summary",
    "guide",
    "inputs",
    "model",
    "data",
    "validation",
    "outputs",
    "sources",
    "chartdata",
]

def _apply_group_order() -> None:
    """Restore the merged DDG workbook order after legacy package imports.

    The old SAM build mutates ``GROUP_ORDER`` into its standalone reader order.
    The merged DDG registry uses the shared workbook order instead.
    """
    _groups.GROUP_ORDER.clear()
    _groups.GROUP_ORDER.update({k: i for i, k in enumerate(_MERGED_ORDER)})

def _run_guards() -> None:
    """Run the DDG-scoped SAM integrity guards against the consolidated CSV tree."""
    ig.assert_piids_in_manifest()
    ig.assert_universes_aligned()
    ig.assert_duplicate_audit_recorded()
    ig.assert_archetype_codes_valid()
    ig.assert_naics_rationale_aligned()
    ig.assert_transaction_dates_covered_by_fiscal_axis()
    ig.assert_prime_awards_cover_transaction_piids()
    ig.assert_supplier_year_activity_spine()
    ig.assert_hull_piids_mapped()
    ig.assert_hull_map_master_consistent()
    ig.assert_hull_milestones_monotonic()
    ig.assert_lifecycle_columns_consistent()

def build() -> int:
    _run_guards()
    _apply_group_order()
    return package_workbook(
        OUT,
        SHEETS,
        title=TITLE,
        creator=CREATOR,
        app_name=APP_NAME,
        normalize_dashes=True,
    )

if __name__ == "__main__":
    raise SystemExit(build())
