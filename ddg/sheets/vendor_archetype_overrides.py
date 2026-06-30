"""vendor_archetype_overrides - the hand-researched archetype overrides (leaf input).

One row per researched subawardee UEI x program: the hand-assigned Capability Domain (D)
and Primary Output (P) that take precedence over the NAICS-6 crosswalk default on the
program-vendor sheets. The per-axis research evidence (reasoning + source URLs) folds
into hover Notes on the D / P cells. R is not researched per vendor (it is the internal
axis, defaulted from the crosswalk), so it is not carried here. Built from
extracted/vendor_archetype_overrides.csv (scripts/build_archetype_overrides.py).

Promoted accessor (imported by the program-vendor sheets, Phase 2):
  overrides_cols(header) -> "'Mapping - Vendor Overrides'!$X$first:$X$last".
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, flat_header_letters,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_ARCHETYPE_OVERRIDES
from workbook_award_classification_refactor.sheets._widths import (
    W_PROGRAM, W_UEI, W_SHORT_FLAG, W_VENDOR,
)

# Program | Subawardee UEI | Capability Domain (D) | Primary Output (P) | Key (Program|UEI)
_WIDTHS = [W_PROGRAM, W_UEI, W_SHORT_FLAG, W_SHORT_FLAG, W_VENDOR]

_NOTE_VERBATIM = {
    "Capability Domain (D)": "Capability Domain Note",
    "Primary Output (P)": "Primary Output Note",
}
# Composite "Program|UEI" join key (computed) so the Supplier Master can resolve its override
# with a single MATCH instead of a two-criteria array search; letters resolved by name.
_EXTRA = ["Key"]
_L = flat_header_letters("vendor_archetype_overrides",
                         note_from_verbatim=_NOTE_VERBATIM, extra_cols=_EXTRA)
_KEY_FORMULA = {
    "Key": lambda r: f'=${_L["Program"]}{r}&"|"&${_L["Subawardee UEI"]}{r}',
}

VENDOR_ARCHETYPE_OVERRIDES, overrides_cols = make_flat_sheet(
    tab=TAB_ARCHETYPE_OVERRIDES, group="inputs",
    csv_name="vendor_archetype_overrides", table_name="VendorArchetypeOverrides",
    banner="§1 - Hand-researched archetype overrides",
    intro="Researched domain and output overrides by program and supplier UEI.",
    widths=_WIDTHS,
    # editable levers: the UEI key + the two override codes, on a pale-yellow fill.
    input_cols=["Subawardee UEI", "Capability Domain (D)", "Primary Output (P)"],
    input_fill=True,
    formula_cols=_KEY_FORMULA, extra_cols=_EXTRA,
    # the composite "Program|UEI" join key is formula plumbing (Program + UEI are shown
    # separately); keep it in the grid for the Supplier Master MATCH but hide it.
    hidden_headers=_EXTRA,
    # per-axis research evidence folds into hover Notes (dropped from the visible table).
    note_from_verbatim=_NOTE_VERBATIM,
    display_headers={
        "Subawardee UEI": "Supplier UEI",
        "Capability Domain (D)": "Domain (D)",
        "Primary Output (P)": "Output (P)",
    },
)
