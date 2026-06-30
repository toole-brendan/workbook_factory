"""assumptions - the "Assumptions" tab (inputs group; the single edit surface).

The one place a model user changes BEHAVIORAL assumptions (raw extracted data lives on
the data tabs; the place-of-performance construction masters and coefficients live on
the Place of Performance tab). No stream toggles: streams are always-on. Editable knob
cells carry a pale-yellow input fill (S_PCT_INPUT_FILL); live checks on those knobs live
on the Checks tab (validation group), complementing the external validate_workbook.py.

Sections:
  §2 DDG AP/LLTM supplier coefficient (the P-10 EOQ source dollars live on SCN Budget).
  §3 OBBBA BC shares (per-program BC share of the gross award + spillover).
  §4 Outyear outsourcing growth (raw HII outsourcing-hours target; the program TAM
     tabs compound-ramp it onto the outyear BC coefficient - no throughput normalization).
(The FY window and units are fixed model facts; they live in the caption and Methodology.)

Promoted accessors (cell refs into 'Assumptions'!):
  ddg_ap_coeff_cell,
  obbba_bc_share_cell(li), obbba_spillover_cell,
  outlook_growth_cell, outlook_ddg_hii_share_cell
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_PCT,
    S_LINK_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.notes import ExcelNote
from workbook_core.groups import group_color

from ddg.sheets.kit.layout import RowCursor
# Input cells get a pale-yellow fill (not just blue font) per the ICAEW code; the
# filled style variants are registered per-build in _inputfill (no engine edit).
from ddg.sheets.kit.styles import S_PCT_INPUT_FILL
from ddg.sheets.kit.tabs import TAB_ASSUMPTIONS
from ddg.sheets.kit.periods import FY as _FY

_GROUP = "inputs"
_NCOLS = 7
_FY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_FY)}     # C..H
_HDR_FY = [S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY)


def _make():
    P: dict = {}
    c = RowCursor(2)
    c.title(TAB_ASSUMPTIONS, _NCOLS)
    c.caption("Editable supplier-share, OBBBA, and outyear assumptions")
    c.blank(2)

    # §2 DDG AP/LLTM coefficient (the P-10 EOQ source dollars live on the SCN Budget tab)
    c.section("§2 - DDG AP/LLTM supplier coefficient", _NCOLS)
    c.blank()
    c.write(["Knob", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
    P["ap_coeff"] = c.write(["DDG AP/LLTM supplier coefficient", 1.00],
                            styles=[S_DEFAULT, S_PCT_INPUT_FILL])
    c.blank(2)

    # §3 OBBBA BC shares
    c.section("§3 - OBBBA BC shares", _NCOLS)
    c.blank()
    c.write(["Control", "Observed", "Adjustment", "Modeled"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    r_ddg = c.write(["DDG-51 OBBBA BC share (Sec. 20002(17))", 0.628, 0, lambda r: f"=C{r}+D{r}"],
                    styles=[S_DEFAULT, S_PCT_INPUT_FILL, S_PCT_INPUT_FILL, S_PCT])
    P["obbba_share"] = {2122: ("E", r_ddg)}
    c.blank()
    P["spillover"] = c.write(["FY2027 execution spillover", 0],
                             styles=[S_DEFAULT, S_PCT_INPUT_FILL])
    c.blank(2)

    # §4 Outyear outsourcing growth (raw HII hours-growth target; the program TAM tabs
    # compound-ramp it onto the outyear BC coefficient - NO throughput normalization).
    c.section("§4 - Outyear outsourcing growth", _NCOLS)
    c.blank()
    c.write(["Knob", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
    P["g_hours"] = c.write(["HII outsourcing-hours growth (annual)", 0.30],
                           styles=[S_DEFAULT, S_PCT_INPUT_FILL])
    P["ddg_hii"] = c.write(["DDG-51 HII share of BC", 0.55],
                           styles=[S_DEFAULT, S_PCT_INPUT_FILL])

    _notes = [
        ExcelNote(f"C{P['ap_coeff']}",
                  "P-10 Ship Construction EOQ only; excludes adds and terminal GFE."),
        ExcelNote(f"C{P['g_hours']}",
                  "HII FY2026 target: outsourcing hours +30% y/y. Phased onto the outyear "
                  "BC coefficient as a compound ramp reaching the full +30% at FY2031 "
                  "(no throughput normalization)."),
        ExcelNote(f"C{P['ddg_hii']}",
                  "Growth applies to HII's 55% DDG BC share; BIW held flat."),
    ]

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=[40, 18, 13, 12, 12, 13, 12],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False)
        return WorksheetSpec(ws, notes=_notes)

    def ddg_ap_coeff_cell() -> str:
        return f"'{TAB_ASSUMPTIONS}'!C{P['ap_coeff']}"

    def obbba_bc_share_cell(li: int) -> str:
        if li not in P["obbba_share"]:
            raise ValueError(f"No OBBBA BC share for LI {li!r}")
        col, row = P["obbba_share"][li]
        return f"'{TAB_ASSUMPTIONS}'!{col}{row}"

    def obbba_spillover_cell() -> str:
        return f"'{TAB_ASSUMPTIONS}'!C{P['spillover']}"

    def outlook_growth_cell() -> str:
        return f"'{TAB_ASSUMPTIONS}'!C{P['g_hours']}"

    def outlook_ddg_hii_share_cell() -> str:
        return f"'{TAB_ASSUMPTIONS}'!C{P['ddg_hii']}"

    return (SheetEntry(TAB_ASSUMPTIONS, _GROUP, render),
            dict(ddg_ap_coeff_cell=ddg_ap_coeff_cell,
                 obbba_bc_share_cell=obbba_bc_share_cell, obbba_spillover_cell=obbba_spillover_cell,
                 outlook_growth_cell=outlook_growth_cell,
                 outlook_ddg_hii_share_cell=outlook_ddg_hii_share_cell))


(ASSUMPTIONS, _A) = _make()
ddg_ap_coeff_cell = _A["ddg_ap_coeff_cell"]
obbba_bc_share_cell = _A["obbba_bc_share_cell"]
obbba_spillover_cell = _A["obbba_spillover_cell"]
outlook_growth_cell = _A["outlook_growth_cell"]
outlook_ddg_hii_share_cell = _A["outlook_ddg_hii_share_cell"]
