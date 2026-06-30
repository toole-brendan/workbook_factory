"""Program-vendor sheet factory."""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, flat_header_letters, sm_match_row, sm_text, sm_value,
)
from workbook_award_classification_refactor.sheets._fiscal import (
    FY_HEADERS, TX_FED_FY, TX_REAL, pv_fy_formula, pv_lifetime_formula,
)
from workbook_award_classification_refactor.sheets.supplier_master import supplier_master_cols
from workbook_award_classification_refactor.sheets._cuts import load_table
from workbook_award_classification_refactor.sheets._widths import (
    W_UEI, W_NAICS, W_NAICS_DESC, W_VENDOR, W_DOMFOR, W_DOLLAR, W_COUNT,
    W_SHORT_FLAG, W_FY, W_TEXT_WIDE, W_CD,
)

_SM_ROW = "SM Match Row"
_PKEY = "Parent Key"
_PDOM = "Parent Domain $"
_PROWS = "Parent Domain Rows"
_USQ = "UEI Positive $ Squared"
_PHHI = "Parent HHI Numerator"
_PWT = "Parent Firm Weight"
_HELPERS = [_SM_ROW, _PKEY, _PDOM, _PROWS, _USQ, _PHHI, _PWT]

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
    sm_headers, sm_rows = load_table("supplier_master")
    p_at = sm_headers.index("Program")
    src = {h: sm_headers.index(h) for h in ("Subawardee UEI", "Role / Description", "Source URLs")}
    dst = {h: PV_HEADERS.index(h) for h in ("Subawardee UEI", "Role / Description", "Source URLs")}
    rows = []
    for r in sm_rows:
        if r[p_at] != program:
            continue
        row = [""] * len(PV_HEADERS)
        for h in src:
            row[dst[h]] = r[src[h]]
        rows.append(row)
    return PV_HEADERS, rows

_WIDTHS = [W_UEI, W_NAICS, W_NAICS_DESC, W_UEI, W_VENDOR, W_VENDOR, W_DOMFOR,
           W_DOLLAR, W_COUNT, W_SHORT_FLAG, W_SHORT_FLAG,
           *([W_FY] * len(FY_HEADERS)),
           W_SHORT_FLAG, W_DOMFOR, W_SHORT_FLAG, W_DOMFOR,
           W_TEXT_WIDE, W_CD, W_UEI, W_DOLLAR, W_CD, W_DOLLAR, W_DOLLAR, W_DOLLAR]

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
    uei = tx_cols("Subawardee UEI")
    date = tx_cols("Subaward Date")
    cc = tx_cols("Country Code")
    real = tx_cols(TX_REAL)
    fedfy = tx_cols(TX_FED_FY)
    pv_headers, pv_rows = _program_vendor_table(program)

    L = flat_header_letters(headers=pv_headers, note_from=_NOTE_FROM, extra_cols=_HELPERS)
    smrow_col = L[_SM_ROW]
    _first = 9
    _last = 8 + len(pv_rows)

    def smrow(r):
        return f"${smrow_col}{r}"

    def _rng(header: str) -> str:
        c = L[header]
        return f"${c}${_first}:${c}${_last}"

    _PUEI = f"${L['Parent UEI']}"
    _UEI = f"${L['Subawardee UEI']}"
    _PKC = f"${L[_PKEY]}"
    _DC = f"${L['Capability Domain Archetype (D)']}"
    _MC = f"${L['Subaward $M']}"
    _PDC = f"${L[_PDOM]}"
    _PRC = f"${L[_PROWS]}"
    _M_RNG = _rng("Subaward $M")
    _PK_RNG = _rng(_PKEY)
    _D_RNG = _rng("Capability Domain Archetype (D)")

    formulas = {
        _PKEY: lambda r: f'=IF({_PUEI}{r}="-",{_UEI}{r},{_PUEI}{r})',
        _PDOM: lambda r: f'=SUMIFS({_M_RNG},{_PK_RNG},{_PKC}{r},{_D_RNG},{_DC}{r},{_M_RNG},">0")',
        _PROWS: lambda r: f'=MAX(1,COUNTIFS({_PK_RNG},{_PKC}{r},{_D_RNG},{_DC}{r},{_M_RNG},">0"))',
        _USQ: lambda r: f'=IF({_MC}{r}>0,{_MC}{r}^2,0)',
        _PHHI: lambda r: f'=IF({_MC}{r}>0,{_MC}{r}*{_PDC}{r},0)',
        _PWT: lambda r: f'=IF({_MC}{r}>0,1/{_PRC}{r},0)',
        _SM_ROW: lambda r: sm_match_row(f'"{program}|"&$B{r}', _SM_KEY),
        "Subaward $M": pv_lifetime_formula(real, uei),
        "Published Subaward Records": lambda r: f"=COUNTIFS({uei},$B{r})",
        "First Subaward": lambda r: f"=_xlfn.MINIFS({date},{uei},$B{r})",
        "Last Subaward": lambda r: f"=_xlfn.MAXIFS({date},{uei},$B{r})",
        "Predominant Place of Performance (by records)": lambda r: (
            f'=IF(COUNTIFS({uei},$B{r},{cc},"<>USA",{cc},"<>")'
            f'>COUNTIFS({uei},$B{r},{cc},"USA"),"Foreign","Domestic")'),
        "Subawardee Vendor Name": lambda r: sm_text(smrow(r), _SM_NAME),
        "Subawardee NAICS-6 (Primary)": lambda r: sm_text(smrow(r), _SM_NAICS),
        "Subawardee NAICS-6 Description": lambda r: sm_text(smrow(r), _SM_DESC),
        "Parent UEI": lambda r: sm_text(smrow(r), _SM_PUEI),
        "Parent Vendor Name": lambda r: sm_text(smrow(r), _SM_PNAME),
        "Capability Domain Archetype (D)": lambda r: sm_value(smrow(r), _SM_D, "D0"),
        "Capability Domain Archetype Basis": lambda r: sm_value(smrow(r), _SM_DB, "Unresolved"),
        "Primary Output Archetype (P)": lambda r: sm_value(smrow(r), _SM_P, "P0"),
        "Primary Output Archetype Basis": lambda r: sm_value(smrow(r), _SM_PB, "Unresolved"),
    }
    for h in FY_HEADERS:
        formulas[h] = pv_fy_formula(real, uei, fedfy, h)

    entry, cols = make_flat_sheet(
        tab=tab, group="model", csv_name=csv_name, table_name=table_name,
        table=(pv_headers, pv_rows), banner=banner, intro=intro, widths=_WIDTHS,
        int_cols=["Published Subaward Records", _SM_ROW, _PROWS],
        float_cols=["Subaward $M", *FY_HEADERS, _PDOM, _USQ, _PHHI, _PWT],
        date_cols=["First Subaward", "Last Subaward"], formula_cols=formulas,
        input_cols=["Subawardee UEI"],
        link_cols=["Published Subaward Records", "First Subaward", "Last Subaward"],
        note_from=_NOTE_FROM, right_spacer=True, extra_cols=_HELPERS,
        hidden_headers=_HELPERS,
        display_headers={
            "Published Subaward Records": "Records",
            "Predominant Place of Performance (by records)": "Primary location",
            "Capability Domain Archetype (D)": "Domain (D)",
            "Capability Domain Archetype Basis": "Domain basis",
            "Primary Output Archetype (P)": "Output (P)",
            "Primary Output Archetype Basis": "Output basis",
        })
    assert f"!${smrow_col}$" in cols(_SM_ROW), (smrow_col, cols(_SM_ROW))
    assert (cols.first, cols.last) == (_first, _last), (cols.first, cols.last, _first, _last)
    return entry, cols
