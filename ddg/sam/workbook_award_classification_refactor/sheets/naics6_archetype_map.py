"""naics6_archetype_map - the NAICS-6 -> archetype crosswalk (leaf reference).

One row per observed subawardee NAICS-6 industry code, giving the DEFAULT archetype -
Capability Domain (D) and Primary Output (P) - used to tag a program-vendor row when that
UEI has no hand-researched override. The per-axis rationale and any caveat fold into hover
Notes on the D / P / Mapping Status cells. Built from extracted/naics6_archetype_map.csv.

Promoted accessor (imported by the program-vendor sheets, Phase 2):
  naics_map_cols(header) -> "'Mapping - NAICS Defaults'!$X$first:$X$last".
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_NAICS_MAP
from workbook_award_classification_refactor.sheets._widths import (
    W_NAICS, W_NAICS_DESC, W_SHORT_FLAG,
)

# NAICS-6 | Title | D | P | Mapping Status
_WIDTHS = [W_NAICS, W_NAICS_DESC, W_SHORT_FLAG, W_SHORT_FLAG, W_SHORT_FLAG]

NAICS_ARCHETYPE_MAP, naics_map_cols = make_flat_sheet(
    tab=TAB_NAICS_MAP, group="inputs",
    csv_name="naics6_archetype_map", table_name="Naics6ArchetypeMap",
    banner="§1 - NAICS-6 to archetype crosswalk",
    intro="Default domain and output by observed NAICS-6.",
    widths=_WIDTHS,
    # editable levers: the lookup key + the two classification codes, on a pale-yellow fill.
    input_cols=["NAICS-6", "Capability Domain (D)", "Primary Output (P)"],
    input_fill=True,
    # per-axis rationale + caveat fold into hover Notes (dropped from the visible table).
    note_from_verbatim={
        "Capability Domain (D)": "D Rationale",
        "Primary Output (P)": "P Rationale",
        "Mapping Status": "Notes / Caveats",
    },
    display_headers={
        "Capability Domain (D)": "Domain (D)",
        "Primary Output (P)": "Output (P)",
        "Mapping Status": "Status",
    },
)
