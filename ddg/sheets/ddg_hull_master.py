"""ddg_hull_master - one row per DDG-51 hull (the hull dimension).

The hull reference dimension: builder, prime PIID, contract block / MYP, Flight, and award FY for
each in-scope hull, with a confidence grade and the supporting public source folded into a hover
Note. It supplies the row spine + builder label for the hull roll-ups (DDG Hull Spend Summary,
DDG Hull x SWBS) the way the Supplier Master supplies the program-vendor sheets.

Construction milestone dates - Start Fabrication / Launch / Delivery, with a per-hull Schedule
Confidence (Actual / Projected / Estimated) - drive the lifecycle layer (DDG Hull x Lifecycle Stage,
DDG C-D Lifecycle Candidates / Rollup / Coverage; the engine is scripts/_lifecycle.py). Start
Fabrication is the published fabrication-start, else keel-laying as the proxy; Launch is blank for
hulls not yet launched (their in-build spend reads as Construction). Built by hand (HII supplier PDFs,
SAR / MSAR, USNI, NVR, shipyard releases); NOT regenerated. Award FY is approximate for the MYP hulls
(the row Confidence grades the hull->builder identity, not the exact procurement year).

Promoted accessor: hull_master_cols(header) -> "'DDG Hull Master'!$X$first:$X$last".
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_MASTER
from workbook_award_classification_refactor.sheets._widths import (
    W_SHORT_FLAG, W_SUPTYPE, W_PIID, W_STATUS, W_CLASS, W_FY, W_DATE,
)

# Hull | Builder | Prime PIID | Block / MYP | Flight | Award FY | Confidence |
#   Start Fabrication | Launch | Delivery | Schedule Confidence
# (Source URL -> hover Note on Hull; Milestone Source URL -> hover Note on Schedule Confidence.)
_WIDTHS = [W_SHORT_FLAG, W_SUPTYPE, W_PIID, W_STATUS, W_CLASS, W_FY, W_CLASS,
           W_DATE, W_DATE, W_DATE, W_SHORT_FLAG]

DDG_HULL_MASTER, hull_master_cols = make_flat_sheet(
    tab=TAB_HULL_MASTER, group="inputs",
    csv_name="ddg_hull_master", table_name="DdgHullMaster",
    banner="§1 - DDG-51 hull master",
    intro="One row per hull: builder, prime contract, block / MYP, Flight, award FY (approximate), "
          "and the curated construction milestones (Start Fabrication / Launch / Delivery).",
    widths=_WIDTHS,
    int_cols=["Award FY"],
    input_cols=["Hull"], input_fill=True,
    # each public source folds into a hover Note: identity on Hull, milestones on Schedule Confidence.
    note_from={"Hull": "Source URL", "Schedule Confidence": "Milestone Source URL"},
    display_headers={"Contract Block / MYP": "Block / MYP"},
)
