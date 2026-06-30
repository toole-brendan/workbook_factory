"""obbba - the "OBBBA Mandatory" data tab (combined, Virginia + DDG-51).

OBBBA (PL 119-21, Title II) Sec. 20002 mandatory new-construction funding, loaded
from extracted/obbba.csv: Sec. 20002(16) = the second FY2026 Virginia-class submarine
($4,600M); Sec. 20002(17) = two FY2026 DDG-51 ($5,400M). Each award is FY2026 budget
authority, additive to the discretionary P-5c base. The award has no cost-category
breakout, so a BC/GFE bridge (the Assumptions BC-share knob) splits the gross into the
supplier-addressable BC base the program's TAM tab rides on its BC coefficient. The
GFE remainder stays out of TAM (standing GFE exclusion). Columbia has no OBBBA award.

Promoted accessors:
  obbba_gross_then_cell(li, fy)        then-year gross award cell
  obbba_gross_const_cell(li, fy)       constant-FY2026 gross award cell
  obbba_bc_base_cell(li, fy)           constant-FY2026 BC-addressable base (feeds the TAM tab)
  obbba_gross_execaligned_cell(li, fy) constant-FY2026 gross, FY26/FY27 spillover-split
                                       (Virginia only; the penetration denominator links here)
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_NUM_INPUT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.notes import ExcelNote
from workbook_core.groups import group_color

from ddg.sheets.kit.cuts import load_rows, as_float
from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.tabs import TAB_OBBBA
from ddg.sheets.deflators import deflator_factor_cell
from ddg.sheets.assumptions import obbba_bc_share_cell, obbba_spillover_cell
from ddg.sheets.kit.periods import FY as _FY

_GROUP = "data"
_FY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_FY)}     # C..H
_NCOLS = 1 + len(_FY)
_HDR_FY = [S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY)
# DDG-51-only slice (Virginia/Columbia OBBBA awards live in their own program folders).
# The Virginia-specific spillover branches below are li==2013-guarded, so they stay dead here.
_PROGRAMS = [(2122, "DDG-51")]


def _load():
    """{li: {'section':..., 'fy':int, 'gross':float, 'note':...}}"""
    out = {}
    for r in load_rows("obbba"):
        out[int(r["li"])] = {"section": r["section"], "fy": int(r["fy"]),
                             "gross": as_float(r["gross_then_$M"]), "note": r["scope_note"]}
    return out


def _make():
    data = _load()
    gross_then: dict = {}
    gross_const: dict = {}
    gross_exec: dict = {}
    bc_const: dict = {}
    _notes: list = []
    c = RowCursor(2)
    c.title(TAB_OBBBA, _NCOLS)
    c.caption("FY2026 mandatory awards and BC/GFE bridge")
    c.blank(2)
    c.section("§1 - Mandatory awards", _NCOLS)
    c.blank()
    c.write(["Award", "Section", "Gross $M"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER])
    for li, name in _PROGRAMS:
        d = data[li]
        r_award = c.write([f"{name} (LI {li})", d["section"], d["gross"]],
                          styles=[S_BOLD, S_DEFAULT, S_NUM_INPUT])
        _notes.append(ExcelNote(f"D{r_award}", d["note"]))   # full scope -> cell note
    c.blank(2)

    sec = 2
    for li, name in _PROGRAMS:
        d = data[li]
        share = obbba_bc_share_cell(li)
        c.section(f"§{sec} - {name} bridge ($M)", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        # then-year gross: the award $ in its budget year, 0 elsewhere
        gross_then[li] = c.write(
            [f"Sec. {d['section']} award, then-year $M"]
            + [(d["gross"] if fy == d["fy"] else 0) for fy in _FY],
            styles=[S_BOLD] + [S_NUM_INPUT] * len(_FY))
        # constant-FY2026 gross (then-year x deflator: a transform, so black)
        gross_const[li] = c.write(
            ["Gross award, constant FY2026 $M"]
            + [f"={_FY_COL[fy]}{gross_then[li]}*{deflator_factor_cell(fy)}" for fy in _FY],
            styles=[S_DEFAULT] + [S_NUM] * len(_FY))
        if li == 2013:
            # Execution-aligned gross (constant FY2026 $): the FY2026 boat's gross split
            # FY26/FY27 by the spillover knob. The Virginia TAM penetration denominator
            # links to THIS row instead of rebuilding the split inline.
            spill = obbba_spillover_cell()
            c26, gt = _FY_COL[2026], gross_then[li]
            ge_vals = ["Gross award, execution-aligned, constant FY2026 $M"]
            for fy in _FY:
                if fy == 2026:
                    ge_vals.append(f"={c26}{gt}*(1-{spill})*{deflator_factor_cell(2026)}")
                elif fy == 2027:
                    ge_vals.append(f"={c26}{gt}*{spill}*{deflator_factor_cell(2027)}")
                else:
                    ge_vals.append(0)
            gross_exec[li] = c.write(ge_vals, styles=[S_DEFAULT] + [S_NUM] * len(_FY))
        c.blank()
        c.subsection(f"§{sec}a - BC/GFE split", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        g = gross_then[li]
        if li == 2013:
            # Virginia: FY26 = gross*share*(1-spill); FY27 = FY26 gross*share*spill (FY26 boat spill).
            spill = obbba_spillover_cell()
            c26, c27 = _FY_COL[2026], _FY_COL[2027]
            bc_then_vals = ["OBBBA BC base, then-year $M"]
            for fy in _FY:
                col = _FY_COL[fy]
                if fy == 2026:
                    bc_then_vals.append(f"={c26}{g}*{share}*(1-{spill})")
                elif fy == 2027:
                    bc_then_vals.append(f"={c27}{g}*{share}+{c26}{g}*{share}*{spill}")
                else:
                    bc_then_vals.append(f"={col}{g}*{share}")
            bc_then = c.write(bc_then_vals, styles=[S_DEFAULT] + [S_NUM] * len(_FY))
            bc_const[li] = c.write(
                ["OBBBA BC base, constant FY2026 $M"]
                + [f"={_FY_COL[fy]}{bc_then}*{deflator_factor_cell(fy)}" for fy in _FY],
                styles=[S_BOLD] + [S_NUM] * len(_FY))
        else:
            # DDG: BC base = constant gross * BC share (no spillover).
            gc = gross_const[li]
            bc_const[li] = c.write(
                ["OBBBA BC base, constant FY2026 $M"]
                + [f"={_FY_COL[fy]}{gc}*{share}" for fy in _FY],
                styles=[S_BOLD] + [S_NUM] * len(_FY))
        c.write(["GFE / non-BC remainder ($M; excluded from TAM)"]
                + [f"={_FY_COL[fy]}{gross_const[li]}-{_FY_COL[fy]}{bc_const[li]}" for fy in _FY],
                styles=[S_DEFAULT] + [S_NUM] * len(_FY))
        c.blank(2)
        sec += 1

    def _chk(li, fy):
        if li not in gross_then:
            raise ValueError(f"No OBBBA award for LI {li!r} (Columbia has none)")
        if fy not in _FY_COL:
            raise ValueError(f"FY {fy!r} outside {_FY!r}")

    def obbba_gross_then_cell(li, fy):
        _chk(li, fy); return f"'{TAB_OBBBA}'!{_FY_COL[fy]}{gross_then[li]}"

    def obbba_gross_const_cell(li, fy):
        _chk(li, fy); return f"'{TAB_OBBBA}'!{_FY_COL[fy]}{gross_const[li]}"

    def obbba_bc_base_cell(li, fy):
        _chk(li, fy); return f"'{TAB_OBBBA}'!{_FY_COL[fy]}{bc_const[li]}"

    def obbba_gross_execaligned_cell(li, fy):
        if li not in gross_exec:
            raise ValueError(f"No execution-aligned gross for LI {li!r} (Virginia only)")
        if fy not in _FY_COL:
            raise ValueError(f"FY {fy!r} outside {_FY!r}")
        return f"'{TAB_OBBBA}'!{_FY_COL[fy]}{gross_exec[li]}"

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=[44, 12, 12, 12, 12, 12, 12],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False)
        return WorksheetSpec(ws, notes=_notes)

    return (SheetEntry(TAB_OBBBA, _GROUP, render),
            obbba_gross_then_cell, obbba_gross_const_cell, obbba_bc_base_cell,
            obbba_gross_execaligned_cell)


(OBBBA, obbba_gross_then_cell, obbba_gross_const_cell, obbba_bc_base_cell,
 obbba_gross_execaligned_cell) = _make()
