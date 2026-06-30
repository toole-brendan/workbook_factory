"""ddg_cd_lifecycle_rollup - DDG C-D Lifecycle Rollup: one row per family-level (C/D) transaction.

The transaction-level verdict of the timing analysis: the full PIID candidate family, the timing-
NARROWED subset (the hulls actually in build on the purchase date), how many remain, the stage(s)
they sit in and whether those agree, the narrowing-result bucket, and a Lifecycle Confidence on its
OWN axis (it never upgrades the C/D hull grade, and Assigned Hull stays blank). Every row carries the
attribution-vs-allocation scope note in the data. Materialized by scripts/build_ddg_cd_lifecycle.py;
per-candidate detail is on DDG C-D Lifecycle Candidates, the $ split by bucket on DDG C-D Lifecycle
Coverage.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_CD_LC_ROLLUP
from workbook_award_classification_refactor.sheets._widths import (
    W_REPORTID, W_PIID, W_SUPTYPE, W_TEXT_WIDE, W_RANK, W_CATEGORY, W_SHORT_FLAG, W_CLASS, W_URL,
)

# 12 columns (the curated rollup schema). Timing Candidate Count is the only numeric column.
_WIDTHS = [W_REPORTID, W_PIID, W_SUPTYPE, W_TEXT_WIDE, W_TEXT_WIDE, W_RANK, W_CATEGORY,
           W_SHORT_FLAG, W_CATEGORY, W_CLASS, W_URL, W_SHORT_FLAG]

DDG_CD_LC_ROLLUP, cd_lc_rollup_cols = make_flat_sheet(
    tab=TAB_CD_LC_ROLLUP, group="model",
    csv_name="ddg_cd_lifecycle_rollup", table_name="DdgCdLcRollup",
    banner="§1 - DDG C/D timing-narrowing rollup (one row per transaction)",
    intro="Family-level (C/D) subawards narrowed by build timing: candidate set, stage consensus, "
          "narrowing result, and a separate Lifecycle Confidence. Evidence-based narrowing, never a "
          "single-hull assignment.",
    widths=_WIDTHS,
    int_cols=["Timing Candidate Count"],
)
