"""ddg_hull_master - one row per DDG-51 hull (the hull dimension).

The hull reference dimension: builder, prime PIID, contract block / MYP, Flight, and award FY for
each in-scope hull, with a confidence grade and the supporting public source folded into a hover
Note. It supplies the row spine + builder label for the hull roll-ups (DDG Hull Spend Summary,
DDG Hull x SWBS) the way the Supplier Master supplies the program-vendor sheets.

Construction milestone chain - MYP Base Award / Start Fabrication (first steel) / Keel Laid / Launch /
Delivery / Commissioned, with a per-hull Schedule Confidence (Actual / Projected / Estimated). The
earliest Keel Laid (falling back to Start Fabrication where a keel is not yet curated) / latest Delivery
over a PIID's hulls feed the construction envelope on Mapping - PIID to Hull (which the DDG Procurement
Timing phase reads, keel-basis); each hull's own milestones bound the five build-stage bands on DDG 125
& 128 Full-Span. Start Fabrication is the published first-steel date (SAR / NAVSEA SNA deck), distinct
from Keel Laid (keel authentication); later milestones are blank for hulls not yet there. Built by hand
(HII supplier PDFs, SAR / MSAR, NAVSEA, USNI, NVR, shipyard releases); NOT regenerated. Award FY is
approximate for the MYP hulls (the row Confidence grades the hull->builder identity).

Promoted accessor: hull_master_cols(header) -> "'DDG Hull Master'!$X$first:$X$last".
"""
from __future__ import annotations

from ddg.sheets.kit.flat import make_flat_sheet
from ddg.sheets.kit.tabs import TAB_HULL_MASTER
from ddg.sheets.kit.widths import (
    W_SHORT_FLAG, W_SUPTYPE, W_PIID, W_STATUS, W_CLASS, W_FY, W_DATE,
)

# Hull | Builder | Prime PIID | Block / MYP | Flight | Award FY | Confidence | MYP Base Award |
#   Start Fabrication | Keel Laid | Launch | Delivery | Commissioned | Schedule Confidence
# (Source URL -> hover Note on Hull; Milestone Source URL -> hover Note on Schedule Confidence.)
_WIDTHS = [W_SHORT_FLAG, W_SUPTYPE, W_PIID, W_STATUS, W_CLASS, W_FY, W_CLASS,
           W_DATE, W_DATE, W_DATE, W_DATE, W_DATE, W_DATE, W_SHORT_FLAG]

DDG_HULL_MASTER, hull_master_cols = make_flat_sheet(
    tab=TAB_HULL_MASTER, group="inputs",
    csv_name="ddg_hull_master", table_name="DdgHullMaster",
    banner="§1 - DDG-51 hull master",
    intro="One row per hull: builder, prime contract, block / MYP, Flight, award FY (approximate), "
          "and the curated construction milestone chain (MYP Base Award / Start Fabrication / Keel "
          "Laid / Launch / Delivery / Commissioned).",
    widths=_WIDTHS,
    int_cols=["Award FY"],
    input_cols=["Hull"], input_fill=True,
    # each public source folds into a hover Note: identity on Hull, milestones on Schedule Confidence.
    note_from={"Hull": "Source URL", "Schedule Confidence": "Milestone Source URL"},
    display_headers={"Contract Block / MYP": "Block / MYP"},
)
