"""archetype_application_audit - visible audit of D/P archetype application."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_INT, S_PCT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.styles import S_ITALIC
from ddg.sheets.kit.tabs import TAB_ARCHETYPE_AUDIT
from ddg.sheets.kit.taxonomy import DOMAINS, OUTPUTS
from ddg.sheets.ddg_program_vendors import ddg_pv_cols

_GROUP = "model"
_NCOLS = 6
_COLS = [14, 22, 42, 12, 14, 12]

_D_CODE = ddg_pv_cols("Capability Domain Archetype (D)")
_D_BASIS = ddg_pv_cols("Capability Domain Archetype Basis")
_P_CODE = ddg_pv_cols("Primary Output Archetype (P)")
_P_BASIS = ddg_pv_cols("Primary Output Archetype Basis")
_AMT = ddg_pv_cols("Subaward $M")
_TOTAL = f"SUM({_AMT})"

_BASIS_ROWS = [
    ("Research override", "Curated vendor override supplied this axis's label."),
    ("NAICS-6 map", "No axis-specific override; supplier primary NAICS mapped to the label."),
    ("Unresolved", "No usable override or NAICS default; catch-all D0 / P0 remains."),
]


def _write_basis(c: RowCursor, axis: str, basis_range: str) -> None:
    for basis, note in _BASIS_ROWS:
        c.write([axis, basis, note,
                 f'=COUNTIFS({basis_range},"{basis}")',
                 f'=SUMIFS({_AMT},{basis_range},"{basis}")',
                 lambda rr: f'=IFERROR(F{rr}/{_TOTAL},"")'],
                styles=[S_DEFAULT, S_DEFAULT, S_DEFAULT, S_INT, S_NUM, S_PCT])


def _write_code_rows(c: RowCursor, axis_label: str, code_range: str, taxonomy) -> None:
    for code, name, _definition in taxonomy:
        c.write([axis_label, code, name,
                 f'=COUNTIFS({code_range},"{code}")',
                 f'=SUMIFS({_AMT},{code_range},"{code}")',
                 lambda rr: f'=IFERROR(F{rr}/{_TOTAL},"")'],
                styles=[S_DEFAULT, S_BOLD, S_DEFAULT, S_INT, S_NUM, S_PCT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_ARCHETYPE_AUDIT, _NCOLS)
    c.caption("How supplier-level D/P archetypes are applied to DDG observed SAM dollars.")
    c.blank(2)

    c.section("§1 - Resolution basis", _NCOLS)
    c.write(["Dollars inherit the supplier UEI x Program label from DDG Program Vendors.  Basis shows whether that label came from research override, NAICS default, or unresolved catch-all."], styles=[S_ITALIC])
    c.blank()
    c.write(["Axis", "Basis", "Meaning", "UEIs", "Subaward $M", "% of DDG $"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    _write_basis(c, "Capability Domain (D)", _D_BASIS)
    _write_basis(c, "Primary Output (P)", _P_BASIS)
    c.blank(2)

    c.section("§2 - Capability Domain (D) distribution", _NCOLS)
    c.blank()
    c.write(["Axis", "Code", "Archetype", "UEIs", "Subaward $M", "% of DDG $"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    _write_code_rows(c, "D", _D_CODE, DOMAINS)
    c.blank(2)

    c.section("§3 - Primary Output (P) distribution", _NCOLS)
    c.blank()
    c.write(["Axis", "Code", "Archetype", "UEIs", "Subaward $M", "% of DDG $"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    _write_code_rows(c, "P", _P_CODE, OUTPUTS)

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


ARCHETYPE_APPLICATION_AUDIT = SheetEntry(TAB_ARCHETYPE_AUDIT, _GROUP, _render)
