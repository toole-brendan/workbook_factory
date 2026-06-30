"""Build the fully flattened DDG-51 workbook."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_root = str(_ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)

from workbook_core.primitives import set_normalize_dashes

# Some flat sheets build XML at import time, so normalize before importing registry modules.
set_normalize_dashes(True)

import workbook_core.groups as _groups
from workbook_core.lib import package_workbook

from ddg.lib import OUT, TITLE, CREATOR, APP_NAME
from ddg.sheets import SHEETS
from ddg.sheets.kit import integrity as ig

_MERGED_ORDER = ["summary", "guide", "inputs", "model", "data", "validation"]

def _apply_group_order() -> None:
    _groups.GROUP_ORDER.clear()
    _groups.GROUP_ORDER.update({k: i for i, k in enumerate(_MERGED_ORDER)})

def _run_guards() -> None:
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
    return package_workbook(OUT, SHEETS, title=TITLE, creator=CREATOR,
                            app_name=APP_NAME, normalize_dashes=True)

if __name__ == "__main__":
    raise SystemExit(build())
