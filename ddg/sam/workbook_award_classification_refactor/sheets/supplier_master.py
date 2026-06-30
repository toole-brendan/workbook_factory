"""supplier_master - the single per-(UEI x program) supplier dimension + classification sheet.

Merges the two former dimension sheets (Subawardee UEI Index + Subawardee Parents) into ONE
source at the Program x UEI grain, so the program-vendor sheets resolve every supplier
attribute with a single match-row into here (one MATCH + N INDEX) instead of repeating a
two-criteria array search per attribute. Independent refreshes of two parallel sheets were the
cause of the dimension-universe drift; with one source - guaranteed by the build-time universe
guard (_integrity) to cover exactly the program-vendor / transaction universe - that can't recur.

Columns: a composite "Program|UEI" Key (the match target), Program, UEI, vendor name, NAICS-6
+ description, the dollar-modal standardized Parent UEI + name (and the raw Parent UEI(s) set),
the Role / Description + Source URLs prose (relocated here so the program-vendor sheets read it
from this one dimension), then the RESOLVED archetype - Capability Domain (D) / Primary Output
(P) + their bases - computed
LIVE here (override-first over the Mapping - Vendor Overrides sheet, then the Mapping - NAICS
Defaults sheet, else D0/P0) from two one-per-row match-row helpers, so editing an override or the
crosswalk updates them. Built from extracted/supplier_master.csv (scripts/build_supplier_master.py).

Promoted accessor (imported by the program-vendor factory): `supplier_master_cols`.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, flat_header_letters,
    override_or_map, override_or_map_basis,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_SUPPLIER_MASTER
from workbook_award_classification_refactor.sheets.naics6_archetype_map import naics_map_cols
from workbook_award_classification_refactor.sheets.vendor_archetype_overrides import overrides_cols
from workbook_award_classification_refactor.sheets._widths import (
    W_VENDOR, W_PROGRAM, W_UEI, W_NAICS, W_NAICS_DESC, W_CD, W_SHORT_FLAG, W_DOMFOR,
    W_TEXT_WIDE,
)

# Key | Program | UEI | Vendor Name | NAICS-6 | NAICS-6 desc | Parent UEI | Parent name |
# Parent UEI(s) | Role / Description | Override Match Row | NAICS Map Match Row | D | D Basis |
# P | P Basis   (Source URLs folds into a hover Note on Role / Description)
_CSV_WIDTHS = [W_VENDOR, W_PROGRAM, W_UEI, W_VENDOR, W_NAICS, W_NAICS_DESC,
               W_UEI, W_VENDOR, W_VENDOR, W_TEXT_WIDE]
_EXTRA = ["Override Match Row", "NAICS Map Match Row",
          "Capability Domain (D)", "Capability Domain Basis",
          "Primary Output (P)", "Primary Output Basis"]
_EXTRA_WIDTHS = [W_CD, W_CD, W_SHORT_FLAG, W_DOMFOR, W_SHORT_FLAG, W_DOMFOR]
_WIDTHS = _CSV_WIDTHS + _EXTRA_WIDTHS

# Source URLs folds into a hover Note on Role / Description (dropped from the visible table).
_NOTE_FROM = {"Role / Description": "Source URLs"}
_L = flat_header_letters("supplier_master", note_from=_NOTE_FROM, extra_cols=_EXTRA)

# override + crosswalk source ranges for the resolved archetype
_OV_KEY = overrides_cols("Key")
_OV_D = overrides_cols("Capability Domain (D)")
_OV_P = overrides_cols("Primary Output (P)")
_MAP_NAICS = naics_map_cols("NAICS-6")
_MAP_D = naics_map_cols("Capability Domain (D)")
_MAP_P = naics_map_cols("Primary Output (P)")


def _key(r):    return f"${_L['Key']}{r}"
def _naics(r):  return f"${_L['Primary NAICS-6']}{r}"
def _ovm(r):    return f"${_L['Override Match Row']}{r}"
def _nm(r):     return f"${_L['NAICS Map Match Row']}{r}"


_FORMULAS = {
    # one MATCH per row into each source; the D/P/basis cells then just INDEX these.
    "Override Match Row":  lambda r: f"=IFERROR(MATCH({_key(r)},{_OV_KEY},0),0)",
    "NAICS Map Match Row": lambda r: f"=IFERROR(MATCH({_naics(r)},{_MAP_NAICS},0),0)",
    "Capability Domain (D)":    lambda r: override_or_map(_ovm(r), _OV_D, _nm(r), _MAP_D, "D0"),
    "Capability Domain Basis":  lambda r: override_or_map_basis(_ovm(r), _OV_D, _nm(r)),
    "Primary Output (P)":       lambda r: override_or_map(_ovm(r), _OV_P, _nm(r), _MAP_P, "P0"),
    "Primary Output Basis":     lambda r: override_or_map_basis(_ovm(r), _OV_P, _nm(r)),
}

SUPPLIER_MASTER, supplier_master_cols = make_flat_sheet(
    tab=TAB_SUPPLIER_MASTER, group="model",
    csv_name="supplier_master", table_name="SupplierMaster",
    banner="§1 - Supplier master",
    intro="One row per program and supplier UEI; standardized identity, parent, role, domain and output.",
    widths=_WIDTHS,
    int_cols=["Override Match Row", "NAICS Map Match Row"],
    input_cols=["Key", "Subawardee UEI", "Parent UEI"],
    formula_cols=_FORMULAS, extra_cols=_EXTRA, note_from=_NOTE_FROM,
    # internal join key + the per-row override / NAICS-map match indices are formula
    # plumbing (Program + UEI are shown separately); hide them from the reader.
    hidden_headers=["Key", "Override Match Row", "NAICS Map Match Row"],
)

# Guard: the resolution helpers reference this sheet's own Key / NAICS-6 / match-row columns;
# assert the by-name letters match the sheet make_flat_sheet built.
assert all(f"!${_L[h]}$" in supplier_master_cols(h) for h in (
    "Key", "Primary NAICS-6", "Override Match Row", "NAICS Map Match Row")), {
    h: (_L[h], supplier_master_cols(h)) for h in (
        "Key", "Primary NAICS-6", "Override Match Row", "NAICS Map Match Row")}
