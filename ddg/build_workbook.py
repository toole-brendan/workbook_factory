"""build_workbook.py - build the combined DDG-51 TAM + SAM workbook.

One flat ``sheets`` package, the canonical ``workbook_core`` group order (no
sam_* retagging - the muted palette is the engine default), and the SAM universe
guards run before packaging exactly as the standalone SAM build did.

Run:    python build_workbook.py
Output: 20260630 Distributed Shipbuilding DDG51 v1.1.xlsx  (in this folder)
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent      # workbook_factory/ddg/  -> top-level `lib`, `sheets`
_ROOT = _HERE.parent                          # workbook_factory/      -> `workbook_core`
for _p in (_HERE, _ROOT):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# Dash normalization must be ON *before* importing the sheet modules: the flat SAM
# sheets build their cell XML eagerly at import, so the switch has to be set before
# the registry import below, not just at package time.
from workbook_core.primitives import set_normalize_dashes

set_normalize_dashes(True)

from workbook_core.lib import package_workbook
from lib import OUT, TITLE, CREATOR, APP_NAME
from sheets import SHEETS
from sheets import _sam_integrity as ig


def _run_guards() -> None:
    """Re-run the SAM build-stopping universe guards (DDG-scoped) before packaging,
    mirroring the standalone SAM lib.build()."""
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
    return package_workbook(OUT, SHEETS, title=TITLE, creator=CREATOR,
                            app_name=APP_NAME, normalize_dashes=True)


if __name__ == "__main__":
    sys.exit(build())
