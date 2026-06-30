"""ddg_piid_hull_map - the prime PIID -> candidate hull family crosswalk (curated lever).

One row per in-scope DDG-51 prime PIID, giving the hull family that PIID builds (Layer A of the
hull attribution). This is the SINGLE source of truth for the PIID->hull mapping: the hull tagger
(scripts/tag_ddg_transactions_hulls.py) READS this CSV to resolve each subaward's candidate family
and to detect out-of-family direct-hull conflicts, and the workbook renders it here. A single-ship
PIID assigns every one of its rows to its one hull (grade A); a multi-hull family PIID assigns only
a single in-family direct-text hull (grade B), everything else staying family-level or flagged.

Built by hand from HII Ingalls supplier-procurement PDFs (titled by hull range + prime contract),
the DDG-51 SAR / MSAR, and USNI. Edit this CSV by hand; it is NOT regenerated.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_PIID_HULL_MAP
from workbook_award_classification_refactor.sheets._widths import (
    W_PIID, W_SUPTYPE, W_TEXT_WIDE, W_CLASS, W_TEXT,
)

# Prime PIID | Builder | Candidate Hulls | Exact or Family | Source | Notes
_WIDTHS = [W_PIID, W_SUPTYPE, W_TEXT_WIDE, W_CLASS, W_TEXT_WIDE, W_TEXT]

DDG_PIID_HULL_MAP, piid_hull_map_cols = make_flat_sheet(
    tab=TAB_PIID_HULL_MAP, group="inputs",
    csv_name="ddg_piid_hull_map", table_name="DdgPiidHullMap",
    banner="§1 - DDG-51 prime PIID to candidate hull family",
    intro="Layer A of hull attribution: each in-scope DDG prime PIID and the hull(s) it builds.",
    widths=_WIDTHS,
    # editable levers: the lookup key (PIID) + the assigned hull family, on a pale-yellow fill.
    input_cols=["Prime PIID", "Candidate Hulls"],
    input_fill=True,
    display_headers={"Exact or Family": "Scope"},
)
