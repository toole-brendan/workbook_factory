"""_program_vendors - the one factory behind the three program-vendor sheets.

The DDG-51 / Virginia / Columbia program-vendor sheets are identical except their program
label, transaction fact sheet, and tab / CSV identity. `make_program_vendor_sheet()` holds
all the shared wiring so each program module is a short config (the only differences are
program / tab / tx_cols / csv_name / table_name / banner / intro).

Each sheet now depends on just TWO upstream sheets:
  - its program's Subaward Transactions leaf - the per-FY $M split and lifetime Subaward $M are
    a single SUMIFS over the transaction sheet's constant-FY2026$ column keyed on UEI + Federal
    FY (deflation lives at the transaction grain, see _fiscal); records / first / last are
    COUNTIFS / MINIFS / MAXIFS; Domestic-or-Foreign a foreign-majority IF over Country Code.
  - the Supplier Master - one hidden "SM Match Row" helper matches the row's "Program|UEI" key
    ONCE; the vendor name / NAICS-6 / parent and the resolved archetype (D / P + bases) then
    INDEX that row. One MATCH + N INDEX, instead of a two-criteria array search per attribute
    and a long override-then-map per archetype cell.
These sheets sit in the `model` group, mirroring award_analysis's model_by_vendor.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, flat_header_letters, sm_match_row, sm_text, sm_value,
)
from workbook_award_classification_refactor.sheets._fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula,
)
from workbook_award_classification_refactor.sheets.supplier_master import (
    supplier_master_cols,
)
from workbook_award_classification_refactor.sheets._cuts import load_table
from workbook_award_classification_refactor.sheets._widths import (
    W_UEI, W_NAICS, W_NAICS_DESC, W_VENDOR, W_DOMFOR, W_DOLLAR, W_COUNT,
    W_SHORT_FLAG, W_FY, W_TEXT_WIDE, W_CD,
)

_SM_ROW = "SM Match Row"
# Concentration helpers (sheet-only, hidden). The parent helpers collapse each UEI to its
# standardized ultimate parent and pre-aggregate that parent's positive FY2026$ within the
# row's domain. The three row-level numerator/weight helpers deliberately move array arithmetic
# out of the summary sheets: Domain Concentration can aggregate them with
# SUMIFS, avoiding cross-sheet SUMPRODUCT expressions (especially 1/range) that surface #VALUE!
# when any upstream cell is nonnumeric or temporarily unresolved during recalc.
_PKEY = "Parent Key"
_PDOM = "Parent Domain $"
_PROWS = "Parent Domain Rows"
_USQ = "UEI Positive $ Squared"
_PHHI = "Parent HHI Numerator"
_PWT = "Parent Firm Weight"
_HELPERS = [_SM_ROW, _PKEY, _PDOM, _PROWS, _USQ, _PHHI, _PWT]

# The program-vendor sheet's canonical column layout (it used to be the header of the
# <program>_program_vendors.csv). The sheet's ROWS now come from the Supplier Master dimension
# (see _program_vendor_table) instead of that CSV; only Subawardee UEI + Role / Description +
# Source URLs are static leaf values, every other column is a live formula defined in
# make_program_vendor_sheet. (<program>_program_vendors.csv survives only for the research-prep
# worklists - it is no longer a workbook input, so no second Program x UEI universe can drift.)
PV_HEADERS = [
    "Subawardee UEI", "Subawardee NAICS-6 (Primary)", "Subawardee NAICS-6 Description",
    "Parent UEI", "Parent Vendor Name", "Subawardee Vendor Name",
    "Predominant Place of Performance (by records)", "Subaward $M",
    "Published Subaward Records", "First Subaward", "Last Subaward",
    *FY_HEADERS,
    "Capability Domain Archetype (D)", "Capability Domain Archetype Basis",
    "Primary Output Archetype (P)", "Primary Output Archetype Basis",
    "Role / Description", "Source URLs",
]


def _program_vendor_table(program: str):
    """The program-vendor sheet's (headers, rows), sourced from the Supplier Master dimension
    filtered on `program`. Each row carries only the static leaf values - the subawardee UEI plus
    its Role / Description + Source URLs (relocated into the Supplier Master) - in the PV_HEADERS
    layout; every other column is a live formula filled by make_program_vendor_sheet, so its
    placeholder here is blank. Supplier Master is already dollar-desc per program, so filtering
    preserves that row order."""
    sm_headers, sm_rows = load_table("supplier_master")
    p_at = sm_headers.index("Program")
    src = {h: sm_headers.index(h)
           for h in ("Subawardee UEI", "Role / Description", "Source URLs")}
    dst = {h: PV_HEADERS.index(h)
           for h in ("Subawardee UEI", "Role / Description", "Source URLs")}
    rows = []
    for r in sm_rows:
        if r[p_at] != program:
            continue
        row = [""] * len(PV_HEADERS)
        for h in src:
            row[dst[h]] = r[src[h]]
        rows.append(row)
    return PV_HEADERS, rows

# Subawardee UEI | NAICS-6 | NAICS-6 desc | Parent UEI | Parent name | Subawardee name |
# Dom/For | $M | Records | First | Last | ≤FY12..FY26 $M (15) | D | D basis | P | P basis |
# Role | SM Match Row | Parent Key | Parent Domain $ | Parent Domain Rows |
# UEI Positive $ Squared | Parent HHI Numerator | Parent Firm Weight (all hidden).
_WIDTHS = [W_UEI, W_NAICS, W_NAICS_DESC, W_UEI, W_VENDOR, W_VENDOR, W_DOMFOR,
           W_DOLLAR, W_COUNT, W_SHORT_FLAG, W_SHORT_FLAG,
           *([W_FY] * 15),
           W_SHORT_FLAG, W_DOMFOR, W_SHORT_FLAG, W_DOMFOR,
           W_TEXT_WIDE,
           W_CD, W_UEI, W_DOLLAR, W_CD, W_DOLLAR, W_DOLLAR, W_DOLLAR]

# Supplier Master source ranges (each attribute resolved once per UEI x program over there).
_SM_KEY = supplier_master_cols("Key")
_SM_NAME = supplier_master_cols("Subawardee Vendor Name")
_SM_NAICS = supplier_master_cols("Primary NAICS-6")
_SM_DESC = supplier_master_cols("NAICS-6 Description")
_SM_PUEI = supplier_master_cols("Parent UEI")
_SM_PNAME = supplier_master_cols("Parent Vendor Name")
_SM_D = supplier_master_cols("Capability Domain (D)")
_SM_DB = supplier_master_cols("Capability Domain Basis")
_SM_P = supplier_master_cols("Primary Output (P)")
_SM_PB = supplier_master_cols("Primary Output Basis")

_NOTE_FROM = {"Role / Description": "Source URLs"}


def make_program_vendor_sheet(*, program: str, tab: str, tx_cols, csv_name: str,
                              table_name: str, banner: str, intro: str):
    """Build one program-vendor sheet. `program` is the (UEI x Program) label that forms the
    Supplier Master key; `tx_cols` is the program's transaction-sheet accessor."""
    uei = tx_cols("Subawardee UEI")
    date = tx_cols("Subaward Date")
    cc = tx_cols("Country Code")
    real = tx_cols(TX_REAL)           # constant-FY2026$ amount, at transaction grain
    fedfy = tx_cols(TX_FED_FY)        # federal FY, at transaction grain

    # Rows come from the Supplier Master dimension filtered on this program (the program-vendor
    # CSV is no longer a workbook input - it survives only for the research-prep worklists).
    pv_headers, pv_rows = _program_vendor_table(program)

    # This sheet's own column letters (gutter at A; note source col dropped; helpers appended).
    L = flat_header_letters(headers=pv_headers, note_from=_NOTE_FROM, extra_cols=_HELPERS)
    smrow_col = L[_SM_ROW]

    def smrow(r):
        return f"${smrow_col}{r}"

    # Same-sheet data-row span (intro layout: title 2, intro 3, blanks 4-5, banner 6, blank 7,
    # header 8 -> data starts at 9). Asserted against the post-build cols accessor below, so a
    # layout change fails loudly rather than mis-keying the parent-grain helpers.
    _first = 9
    _last = 8 + len(pv_rows)

    def _rng(header: str) -> str:
        """Absolute same-sheet range for one of THIS sheet's columns (no tab prefix needed)."""
        c = L[header]
        return f"${c}${_first}:${c}${_last}"

    _PUEI = f"${L['Parent UEI']}"          # resolved parent UEI cell (per row)
    _UEI = f"${L['Subawardee UEI']}"       # the row's own UEI (column B), parent fallback
    _PKC = f"${L[_PKEY]}"                  # this row's Parent Key cell
    _DC = f"${L['Capability Domain Archetype (D)']}"   # this row's resolved D cell
    _MC = f"${L['Subaward $M']}"              # this row's net FY2026$ total
    _PDC = f"${L[_PDOM]}"                     # this row's parent-domain positive total
    _PRC = f"${L[_PROWS]}"                    # positive rows in this parent x domain
    _M_RNG = _rng("Subaward $M")
    _PK_RNG = _rng(_PKEY)
    _D_RNG = _rng("Capability Domain Archetype (D)")

    formulas = {
        # Parent Key = standardized ultimate parent UEI, falling back to the UEI itself when
        # Supplier Master carries no parent ("-"), so standalone firms stay distinct.
        _PKEY: lambda r: f'=IF({_PUEI}{r}="-",{_UEI}{r},{_PUEI}{r})',
        # Parent Domain $ = this parent's POSITIVE FY2026$ total within this row's domain.
        _PDOM: lambda r: (f'=SUMIFS({_M_RNG},{_PK_RNG},{_PKC}{r},'
                          f'{_D_RNG},{_DC}{r},{_M_RNG},">0")'),
        # Parent Domain Rows = positive rows sharing this parent + domain (>=1 guard so the
        # distinct-parent count 1/COUNT never divides by zero on the Domain Concentration sheet).
        _PROWS: lambda r: (f'=MAX(1,COUNTIFS({_PK_RNG},{_PKC}{r},'
                           f'{_D_RNG},{_DC}{r},{_M_RNG},">0"))'),
        # Row-level concentration numerators / weights. These are zero for nonpositive rows,
        # matching the positive-spend concentration denominator used on the summary sheets.
        _USQ: lambda r: f'=IF({_MC}{r}>0,{_MC}{r}^2,0)',
        _PHHI: lambda r: f'=IF({_MC}{r}>0,{_MC}{r}*{_PDC}{r},0)',
        _PWT: lambda r: f'=IF({_MC}{r}>0,1/{_PRC}{r},0)',
        _SM_ROW: lambda r: sm_match_row(f'"{program}|"&$B{r}', _SM_KEY),
        "Subaward $M":      pv_lifetime_formula(real, uei),
        "Published Subaward Records": lambda r: f"=COUNTIFS({uei},$B{r})",
        "First Subaward":   lambda r: f"=_xlfn.MINIFS({date},{uei},$B{r})",
        "Last Subaward":    lambda r: f"=_xlfn.MAXIFS({date},{uei},$B{r})",
        "Predominant Place of Performance (by records)": lambda r: (
            f'=IF(COUNTIFS({uei},$B{r},{cc},"<>USA",{cc},"<>")'
            f'>COUNTIFS({uei},$B{r},{cc},"USA"),"Foreign","Domestic")'),
        "Subawardee Vendor Name":         lambda r: sm_text(smrow(r), _SM_NAME),
        "Subawardee NAICS-6 (Primary)":   lambda r: sm_text(smrow(r), _SM_NAICS),
        "Subawardee NAICS-6 Description": lambda r: sm_text(smrow(r), _SM_DESC),
        "Parent UEI":                     lambda r: sm_text(smrow(r), _SM_PUEI),
        "Parent Vendor Name":             lambda r: sm_text(smrow(r), _SM_PNAME),
        "Capability Domain Archetype (D)":     lambda r: sm_value(smrow(r), _SM_D, "D0"),
        "Capability Domain Archetype Basis":   lambda r: sm_value(smrow(r), _SM_DB, "Unresolved"),
        "Primary Output Archetype (P)":        lambda r: sm_value(smrow(r), _SM_P, "P0"),
        "Primary Output Archetype Basis":      lambda r: sm_value(smrow(r), _SM_PB, "Unresolved"),
    }
    # Constant-FY2026$ per-FY split: one SUMIFS over the tx FY2026$ column per FY bin.
    for h in FY_HEADERS:
        formulas[h] = pv_fy_formula(real, uei, fedfy, h)

    entry, cols = make_flat_sheet(
        tab=tab, group="model", csv_name=csv_name, table_name=table_name,
        table=(pv_headers, pv_rows),
        banner=banner, intro=intro, widths=_WIDTHS,
        int_cols=["Published Subaward Records", _SM_ROW, _PROWS],
        float_cols=["Subaward $M", *FY_HEADERS, _PDOM, _USQ, _PHHI, _PWT],
        date_cols=["First Subaward", "Last Subaward"], formula_cols=formulas,
        input_cols=["Subawardee UEI"],
        # COUNTIFS/MINIFS/MAXIFS surface values living on the tx sheet -> green links;
        # $M (a new SUMIFS aggregate) and the place-of-performance classifier stay black.
        link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
        note_from=_NOTE_FROM, right_spacer=True, extra_cols=_HELPERS,
        # the SM match index + concentration helpers are formula plumbing, not reader content.
        hidden_headers=_HELPERS,
        # shorten the wide headers for the reader; the canonical names still drive every
        # formula / cols accessor (cross-sheet refs are unaffected).
        display_headers={
            "Published Subaward Records": "Records",
            "Predominant Place of Performance (by records)": "Primary location",
            "Capability Domain Archetype (D)": "Domain (D)",
            "Capability Domain Archetype Basis": "Domain basis",
            "Primary Output Archetype (P)": "Output (P)",
            "Primary Output Archetype Basis": "Output basis",
        })

    # Guards: the helper letters + the data-row span the parent helpers were built on must be
    # exactly what make_flat_sheet rendered (else the same-sheet SUMIFS/COUNTIFS ranges drift).
    assert f"!${smrow_col}$" in cols(_SM_ROW), (smrow_col, cols(_SM_ROW))
    assert (cols.first, cols.last) == (_first, _last), (cols.first, cols.last, _first, _last)
    return entry, cols
