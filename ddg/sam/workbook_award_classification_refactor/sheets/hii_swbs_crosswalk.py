"""hii_swbs_crosswalk - the HII work-item code -> SWBS crosswalk (leaf reference).

One row per HII-Ingalls work-item code, giving the ship-system application (SWBS) used to
tag a DDG-51 subaward transaction by its code. The SWBS analogue of the NAICS-6 Archetype
Map: the DDG Subaward SWBS sheet resolves its SWBS / SWBS basis cells by a single-key
INDEX/MATCH on the code into this table. Two provenance tiers carried in SWBS basis:
X (observed - deterministic modal SWBS in the HII code dictionary) and C (curated -
inference from component text / codebook for high-dollar codes the dictionary left blank).
The component-text / curation rationale folds into a hover Note on the SWBS cell. Built
from extracted/hii_swbs_crosswalk.csv (scripts/build_swbs_crosswalk.py).

Promoted accessor (imported by ddg_subaward_swbs):
  swbs_xwalk_cols(header) -> "'Mapping - HII Code to SWBS'!$X$first:$X$last".
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_SWBS_CROSSWALK
from workbook_award_classification_refactor.sheets._widths import (
    W_TEXT_WIDE,
)

# HII Work-Item Code | SWBS Subsystem | SWBS (display) | SWBS basis   (Evidence -> Note)
_WIDTHS = [12, 14, W_TEXT_WIDE, 18]

HII_SWBS_CROSSWALK, swbs_xwalk_cols = make_flat_sheet(
    tab=TAB_SWBS_CROSSWALK, group="inputs",
    csv_name="hii_swbs_crosswalk", table_name="HiiSwbsCrosswalk",
    banner="§1 - HII work-item code to SWBS crosswalk",
    intro="HII work-item code to SWBS subsystem.",
    widths=_WIDTHS,
    # editable levers: the lookup key + the assigned subsystem code, on a pale-yellow fill.
    input_cols=["HII Work-Item Code", "SWBS Subsystem"],
    input_fill=True,
    # component-text / curation rationale folds into a hover Note on the SWBS cell.
    note_from_verbatim={"SWBS": "Evidence"},
    display_headers={
        "HII Work-Item Code": "HII Code",
        "SWBS Subsystem": "Subsystem",
        "SWBS basis": "Basis",
    },
)
