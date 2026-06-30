"""checks - the "Checks" tab (validation group): live in-workbook QA.

The ICAEW Financial Modelling Code (Error reduction, Principle #17) calls for visible
checks and a master check built into the model. This workbook already asserts fidelity
EXTERNALLY at build time (validate_workbook.py), but that script does not run when a
user opens the .xlsx and edits a knob. This tab adds LIVE checks that recalculate with
the model, so a bad input flips a cell to FAIL immediately and the master check (a
single OK / CHECK FAILED verdict, also surfaced on the Executive Summary) catches it.

These checks are deliberately STRUCTURAL/SANITY checks - bounds, band ordering,
completeness - that flip to FAIL on a genuinely wrong edit. They complement, rather
than duplicate, validate_workbook.py's external baseline-regression anchors (those
re-check captured magic numbers against an independent LibreOffice recalc, which is
the right place for a regression guard and would only hardcode magic numbers in-sheet).

Each check row is [label, live value, =IF(condition,"OK","FAIL")]; the status cells
form column D, so the master check is =IF(COUNTIF(<status range>,"FAIL")=0, ...).
Conditional formatting red-fills any FAIL / CHECK FAILED cell.

Promoted accessor:
  master_check_cell()  -> the master OK / CHECK FAILED status cell (Executive Summary links it)
"""
from __future__ import annotations

import workbook_core.styles as _styles
from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_INT,
    S_LINK_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from sheets._tam_layout import RowCursor
from sheets._tabs import TAB_CHECKS
from sheets._tam_periods import OY as _OY
from sheets import ddg_tam as DD
from sheets import assumptions as A

_GROUP = "validation"
_NCOLS = 3   # content columns (gutter mode): B = Check, C = Value, D = Status

# Per-build red-fill differential format for FAIL cells (the per-build append trick;
# DXFS[0] is reserved for the no-format table style, so this appends at dxfId >= 1).
# Excel's standard "light red fill, dark red text"; CF dxf fills use bgColor.
if not getattr(_styles, "_check_fail_dxf", None):
    _styles._check_fail_dxf = len(_styles.DXFS)
    _styles.DXFS.append(
        '<dxf><font><color rgb="FF9C0006"/></font>'
        '<fill><patternFill><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf>'
    )
_FAIL_DXF = _styles._check_fail_dxf


def _make():
    c = RowCursor(2)
    c.title(TAB_CHECKS, _NCOLS)                                            # row 2
    c.caption("Input bounds, outyear ordering, and completeness")          # row 3
    c.blank(2)

    check_rows: list[int] = []

    def _bounds(label, ref, *, lo, hi, lo_strict):
        op = ">" if lo_strict else ">="
        r = c.write(
            [label, f"={ref}",
             lambda rr: f'=IF(AND(C{rr}{op}{lo},C{rr}<={hi}),"OK","FAIL")'],
            styles=[S_DEFAULT, S_LINK_PCT, S_DEFAULT])
        check_rows.append(r)
        return r

    def _band(label, mod):
        diffs = ",".join(f"{mod.outyear_high_cell(fy)}-{mod.outyear_low_cell(fy)}"
                         for fy in _OY)
        r = c.write(
            [label, f"=MIN({diffs})",
             lambda rr: f'=IF(C{rr}>=-0.001,"OK","FAIL")'],
            styles=[S_DEFAULT, S_NUM, S_DEFAULT])
        check_rows.append(r)
        return r

    # §1 Share bounds ---------------------------------------------------------------
    c.section("§1 - Share bounds", _NCOLS)
    c.blank()
    c.write(["Check", "Value", "Status"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER])
    _bounds("DDG-51 applied BC coefficient", DD.applied_coeff_cell(),
            lo=0, hi=1, lo_strict=True)
    _bounds("DDG-51 OBBBA modeled BC share", A.obbba_bc_share_cell(2122),
            lo=0, hi=1, lo_strict=False)
    _bounds("DDG-51 AP/LLTM supplier coefficient", A.ddg_ap_coeff_cell(),
            lo=0, hi=1, lo_strict=False)
    c.blank(2)

    # §2 Outyear band ---------------------------------------------------------------
    c.section("§2 - Outyear band", _NCOLS)
    c.blank()
    c.write(["Check", "Min margin $M", "Status"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER])
    _band("DDG-51 outyear high >= low", DD)
    c.blank(2)

    # §3 Completeness ---------------------------------------------------------------
    c.section("§3 - Completeness", _NCOLS)
    c.blank()
    c.write(["Check", "Count", "Status"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER])
    knobs = [A.ddg_ap_coeff_cell(), A.obbba_spillover_cell(),
             A.outlook_growth_cell(), A.outlook_ddg_hii_share_cell(),
             A.obbba_bc_share_cell(2122)]
    r_knobs = c.write(
        ["Key behavioral knobs present & numeric", f"=COUNT({','.join(knobs)})",
         lambda rr: f'=IF(C{rr}={len(knobs)},"OK","FAIL")'],
        styles=[S_DEFAULT, S_INT, S_DEFAULT])
    check_rows.append(r_knobs)
    c.blank(2)

    # §4 Master check ---------------------------------------------------------------
    first, last = check_rows[0], check_rows[-1]
    c.section("§4 - Master check", _NCOLS)
    c.blank()
    mrow = c.write(
        ["All checks",
         f'=COUNTIF(D{first}:D{last},"FAIL")',
         lambda rr: f'=IF(C{rr}=0,"OK","CHECK FAILED")'],
        styles=[S_BOLD, S_INT, S_BOLD])

    # Conditional formatting: red-fill any FAIL / CHECK FAILED status cell.
    _cf = (
        f'<conditionalFormatting sqref="D{first}:D{last} D{mrow}">'
        f'<cfRule type="cellIs" dxfId="{_FAIL_DXF}" priority="1" operator="equal">'
        f'<formula>"FAIL"</formula></cfRule>'
        f'<cfRule type="cellIs" dxfId="{_FAIL_DXF}" priority="2" operator="equal">'
        f'<formula>"CHECK FAILED"</formula></cfRule>'
        f'</conditionalFormatting>'
    )

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=[52, 14, 16],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False,
                       conditional_formatting=[_cf])
        return WorksheetSpec(ws)

    def master_check_cell() -> str:
        return f"'{TAB_CHECKS}'!D{mrow}"

    return SheetEntry(TAB_CHECKS, _GROUP, render), master_check_cell


(CHECKS, master_check_cell) = _make()
