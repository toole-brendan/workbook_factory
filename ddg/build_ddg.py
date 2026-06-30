"""build_ddg.py - build the combined DDG-51 TAM + SAM workbook.

Imports the DDG-sliced TAM and SAM sheet registries from the two sub-packages
(``tam/workbook_master_tam`` and ``sam/workbook_award_classification_refactor``),
re-tags the SAM tabs into their own group block so the workbook reads
``[TAM block] -> [SAM block]`` rather than interleaving by shared group, and
packages both into one .xlsx through the shared ``workbook_core`` engine.

The three tab-name collisions (Executive Summary / Methodology / Deflators) are
resolved on the SAM side at sam/.../sheets/_tabs.py (so every SAM formula follows),
not here - the packager rejects duplicate tab names rather than renaming.

Run:    python build_ddg.py
Output: 20260630_Distributed Shipbuilding DDG51_v1.0.xlsx   (in this folder)
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# The two sub-package dirs (so workbook_master_tam / workbook_award_classification_refactor
# resolve) + the factory root (so the copied workbook_core resolves).
for _p in (_HERE / "tam", _HERE / "sam", _HERE.parent):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

# Dash normalization must be ON *before* importing the sheet modules: the flat sheets
# build their cell XML eagerly at import (see the SAM pipeline's lib.build note), so the
# switch has to be set before the registry imports below, not just at package time.
from workbook_core.primitives import set_normalize_dashes

set_normalize_dashes(True)

import workbook_core.groups as _groups
from workbook_core.tables import SheetEntry
from workbook_core.lib import package_workbook

# DDG-sliced registries. Importing these also runs each pipeline's lib.py palette setup
# (both set the same muted scheme, which is now also the workbook_core default).
from workbook_master_tam.sheets import SHEETS as _TAM_SHEETS
from workbook_award_classification_refactor.sheets import SHEETS as _SAM_SHEETS

OUT = _HERE / "20260630_Distributed Shipbuilding DDG51_v1.0.xlsx"
_TITLE = "Distributed Shipbuilding - DDG-51 TAM + SAM (combined)"
_CREATOR = "workbook_factory ddg/build_ddg.py"
_APP = "workbook_factory"

# The SAM block is re-tagged into its own group keys so the two pipelines form two
# contiguous tab blocks (TAM first, then SAM). Color is unaffected: each sheet baked its
# tab color from its ORIGINAL group at import, so a sam_* tab keeps its chapter's color.
_SAM_GROUP_MAP = {
    "summary": "sam_summary", "guide": "sam_guide", "model": "sam_model",
    "inputs": "sam_inputs", "data": "sam_data",
}

# Combined tab-block order: the TAM chapters, then the SAM chapters.
_COMBINED_ORDER = [
    "summary", "guide", "inputs", "model", "data", "validation",
    "sam_summary", "sam_guide", "sam_model", "sam_inputs", "sam_data",
]


def _retag_sam(entry: SheetEntry) -> SheetEntry:
    """Rebuild a SAM SheetEntry under its sam_* group (tab_name / render unchanged)."""
    return SheetEntry(entry.tab_name, _SAM_GROUP_MAP.get(entry.group, entry.group),
                      entry.render, entry.hidden)


def _apply_group_order() -> None:
    """Install the combined group order + colors LAST.

    workbook_core.lib imported GROUP_ORDER by reference and each sub-pipeline's lib.py
    mutates these dicts at import (the SAM lib even clears GROUP_ORDER), so we mutate the
    SAME dict objects in place here, after both registries are imported.
    """
    _groups.GROUP_ORDER.clear()
    _groups.GROUP_ORDER.update({k: i for i, k in enumerate(_COMBINED_ORDER)})
    for sam_k, base_k in (("sam_summary", "summary"), ("sam_guide", "guide"),
                          ("sam_model", "model"), ("sam_inputs", "inputs"),
                          ("sam_data", "data")):
        _groups._COLOR[sam_k] = _groups._COLOR[base_k]


def _run_sam_guards() -> None:
    """Re-run the SAM build-stopping universe guards (now DDG-scoped) before packaging,
    mirroring the standalone SAM lib.build() so the combined build is just as strict."""
    from workbook_award_classification_refactor.sheets import _integrity as ig

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
    _run_sam_guards()
    _apply_group_order()
    sheets = list(_TAM_SHEETS) + [_retag_sam(e) for e in _SAM_SHEETS]
    return package_workbook(OUT, sheets, title=_TITLE, creator=_CREATOR,
                            app_name=_APP, normalize_dashes=True)


if __name__ == "__main__":
    sys.exit(build())
