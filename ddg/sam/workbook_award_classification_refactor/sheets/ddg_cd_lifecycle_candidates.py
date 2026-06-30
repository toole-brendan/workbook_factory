"""ddg_cd_lifecycle_candidates - DDG C-D Lifecycle Candidates: one row per (C/D tx x candidate hull).

The evidence grain behind the timing-narrowing of the family-level (grade C / D) DDG subawards.
For each C/D transaction, EVERY hull in its PIID candidate family gets a row, stage-tagged against
the purchase date - so the kept hulls (Window Match Flag TRUE) and the excluded ones (post-delivery,
no schedule data, or implausibly early - with the reason) are both visible. The narrowed set is the
TRUE rows; it is never collapsed to a single hull. Materialized by scripts/build_ddg_cd_lifecycle.py.

Read with DDG C-D Lifecycle Rollup (one row per transaction) and DDG C-D Lifecycle Coverage (the $).
This is attribution, not allocation: no per-hull dollar is assigned here (the wall, briefing §6).
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_CD_LC_CANDIDATES
from workbook_award_classification_refactor.sheets._widths import (
    W_REPORTID, W_PIID, W_CODE, W_SHORT_FLAG, W_SUPTYPE, W_DATE, W_CLASS, W_STATUS, W_TEXT_WIDE,
)

# 12 columns (the curated candidate schema). Subaward Date is a real date serial; the rest are text.
_WIDTHS = [W_REPORTID, W_PIID, W_CODE, W_SHORT_FLAG, W_SUPTYPE, W_DATE, W_STATUS, W_SHORT_FLAG,
           W_SHORT_FLAG, W_CLASS, W_STATUS, W_TEXT_WIDE]

DDG_CD_LC_CANDIDATES, cd_lc_candidates_cols = make_flat_sheet(
    tab=TAB_CD_LC_CANDIDATES, group="model",
    csv_name="ddg_cd_lifecycle_candidates", table_name="DdgCdLcCandidates",
    banner="§1 - DDG C/D timing candidates (transaction x candidate hull)",
    intro="One row per family-level (C/D) subaward x each candidate hull, stage-tagged on the "
          "purchase date. TRUE rows are the timing-narrowed set; no single hull is assigned.",
    widths=_WIDTHS,
    date_cols=["Subaward Date"],
    right_spacer=True,   # clip the long trailing Reason column
)
