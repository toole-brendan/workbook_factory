"""checks - the "Checks" tab (validation group): live in-workbook QA.

The ICAEW Financial Modelling Code (Error reduction, Principle #17) calls for visible
checks and a master check built into the model. This workbook already asserts fidelity
EXTERNALLY at build time (validate_workbook.py), but that script does not run when a
user opens the .xlsx and edits a knob. This tab adds LIVE checks that recalculate with
the model, so a bad input flips a cell to FAIL immediately and the master check (a
single OK / CHECK FAILED verdict, also surfaced on the Executive Summary) catches it.

These checks are deliberately STRUCTURAL/SANITY checks - bounds, band ordering,
completeness, and SAM reconciliation bridges - that flip to FAIL on a genuinely wrong
edit. They complement validate_workbook.py's external baseline-regression anchors.

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

from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.tabs import TAB_CHECKS
from ddg.sheets.kit.periods import OY as _OY
from ddg.sheets import ddg_tam as DD
from ddg.sheets import assumptions as A
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.ddg_program_vendors import ddg_pv_cols
from ddg.sheets.ddg_hull_spend_summary import hull_spend_cols
from ddg.sheets.ddg_swbs_rollup import swbs_rollup_cols
from ddg.sheets.ddg_cd_lifecycle_rollup import cd_lc_rollup_cols
from ddg.sheets.ddg_vendor_hull_lifecycle import vendor_hull_lifecycle_cols
from ddg.sheets.ddg_archetype_lifecycle import archetype_lifecycle_cols

_GROUP = "validation"
_NCOLS = 3   # content columns (gutter mode): B = Check, C = Value, D = Status
_TOL = 0.01  # $M reconciliation tolerance for live SAM bridges

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

# SAM source / roll-up ranges.
_TX_AMT = ddg_tx_cols(TX_REAL)
_TX_CONF = ddg_tx_cols("Hull Confidence")
_TX_BUILDER = ddg_tx_cols("Builder")
_PV_AMT = ddg_pv_cols("Subaward $M")
_HULL_ASSIGNED = hull_spend_cols("Assigned Subaward $M")
_SWBS_AMT = swbs_rollup_cols("Subaward $M")
_CD_ROLLUP_RID = cd_lc_rollup_cols("Subaward Report ID")
_VHL_TOTAL = vendor_hull_lifecycle_cols("Total $M")
_AL_AXIS = archetype_lifecycle_cols("Axis")
_AL_TOTAL = archetype_lifecycle_cols("Total $M")


def _make():
    c = RowCursor(2)
    c.title(TAB_CHECKS, _NCOLS)                                            # row 2
    c.caption("Input bounds, outyear ordering, SAM reconciliation, and master status")
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

    def _zero(label: str, formula: str, *, tol: float = _TOL, style=S_NUM):
        r = c.write(
            [label, formula,
             lambda rr: f'=IF(ABS(C{rr})<={tol},"OK","FAIL")'],
            styles=[S_DEFAULT, style, S_DEFAULT])
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

    # §4 SAM reconciliation ---------------------------------------------------------
    c.section("§4 - SAM reconciliation", _NCOLS)
    c.blank()
    c.write(["Check", "Delta", "Status"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER])
    _zero("Program-vendor $ reconciles to transactions",
          f"=SUM({_PV_AMT})-SUM({_TX_AMT})/1000000")
    _zero("Hull confidence ladder covers transactions",
          f'=(SUMIFS({_TX_AMT},{_TX_CONF},"A")+SUMIFS({_TX_AMT},{_TX_CONF},"B")+'
          f'SUMIFS({_TX_AMT},{_TX_CONF},"C")+SUMIFS({_TX_AMT},{_TX_CONF},"D")+'
          f'SUMIFS({_TX_AMT},{_TX_CONF},"X"))/1000000-SUM({_TX_AMT})/1000000')
    _zero("Exact-hull rollup reconciles to A/B confidence",
          f'=SUM({_HULL_ASSIGNED})-(SUMIFS({_TX_AMT},{_TX_CONF},"A")+'
          f'SUMIFS({_TX_AMT},{_TX_CONF},"B"))/1000000')
    _zero("Vendor-hull lifecycle reconciles to A/B confidence",
          f'=SUM({_VHL_TOTAL})-(SUMIFS({_TX_AMT},{_TX_CONF},"A")+'
          f'SUMIFS({_TX_AMT},{_TX_CONF},"B"))/1000000')
    _zero("Archetype lifecycle D-axis reconciles to vendor-hull lifecycle",
          f'=SUMIFS({_AL_TOTAL},{_AL_AXIS},"D")-SUM({_VHL_TOTAL})')
    _zero("Archetype lifecycle P-axis reconciles to vendor-hull lifecycle",
          f'=SUMIFS({_AL_TOTAL},{_AL_AXIS},"P")-SUM({_VHL_TOTAL})')
    _zero("SWBS rollup reconciles to HII universe",
          f'=SUM({_SWBS_AMT})-SUMIFS({_TX_AMT},{_TX_BUILDER},"HII-Ingalls")/1000000')
    _zero("C/D lifecycle rollup row count reconciles to transactions",
          f'=ROWS({_CD_ROLLUP_RID})-COUNTIFS({_TX_CONF},"C")-COUNTIFS({_TX_CONF},"D")',
          tol=0, style=S_INT)
    c.blank(2)

    # §5 Master check ---------------------------------------------------------------
    first, last = check_rows[0], check_rows[-1]
    c.section("§5 - Master check", _NCOLS)
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
