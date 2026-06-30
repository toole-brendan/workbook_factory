"""ddg_hull_exceptions - the hull-assignment exception log (review queue).

A flat render of extracted/ddg_hull_exceptions.csv (written by scripts/tag_ddg_transactions_hulls.py):
one row per transaction whose hull evidence is a CONFLICT - an out-of-family direct hull (almost
always a REBUY citing a part's ORIGIN hull, not the ship being built) or a multi-hull row. These
carry a blank Assigned Hull and never enter the hull roll-ups; they are surfaced here so a reviewer
can adjudicate them rather than have them silently dropped. Pure materialized evidence - no formulas.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_EXCEPTIONS
from workbook_award_classification_refactor.sheets._widths import (
    W_REPORTID, W_PIID, W_VENDOR, W_CATEGORY, W_SUBNUM, W_TEXT_WIDE,
)

# Report ID | Prime PIID | Vendor | Issue | Direct Hull Text | PIID Candidate Hulls | Description
_WIDTHS = [W_REPORTID, W_PIID, W_VENDOR, W_CATEGORY, W_SUBNUM, W_TEXT_WIDE, W_TEXT_WIDE]

DDG_HULL_EXCEPTIONS, hull_exceptions_cols = make_flat_sheet(
    tab=TAB_HULL_EXCEPTIONS, group="model",
    csv_name="ddg_hull_exceptions", table_name="DdgHullExceptions",
    banner="§1 - DDG-51 hull-assignment exceptions",
    intro="Conflict / multi-hull rows (blank Assigned Hull, excluded from roll-ups) for review.",
    widths=_WIDTHS,
    display_headers={"Subaward Description (excerpt)": "Subaward Description"},
)
