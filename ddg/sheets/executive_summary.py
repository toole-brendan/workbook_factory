"""executive_summary - the master TAM answer page (summary group).

The one cross-program page: programs down the side, fiscal years across the top.
Nothing is hardcoded - every cell links into the three per-program TAM tabs; the
Total row sums the three programs within each fiscal year. Outsourced new-construction
TAM is the supplier-addressable share of Basic Construction (BC base x place-of-
performance coefficient), plus the OBBBA mandatory overlay. §2 shows it by fiscal year
FY2022-2027 (no cumulative roll-up; FY2026-27 are budget-request estimates, E). §3
carries the FY2028-31 outyear projection as an explicit low/high band (no single central
case): low = status-quo BC coefficient, high = the coefficient compound-ramped to the
full HII outsourcing-hours uplift by FY2031 (Assumptions §4; DDG-51 HII-Ingalls 55% share).
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_LINK_NUM, S_LINK_PCT,
    S_NUM,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from sheets._tam_layout import RowCursor
from sheets._tam_italic import S_ITALIC
from sheets._tabs import TAB_EXEC_SUMMARY
from sheets import _tam_periods as _periods
from sheets import ddg_tam as DD

_GROUP = "summary"
# §2 firm per-year grid (transposed: programs down, fiscal years across; no
# cumulative roll-up) for FY2022-2027: FY2022-25 firm, FY2026-27 budget request
# (E; FY26 incl. OBBBA). §3 carries the FY2028-31 outyear projection as an explicit
# low/high band (no single central case): low = status-quo BC coefficient, high =
# the coefficient compound-ramped to the full outsourcing-hours uplift by FY2031.
_FIRM_FY = _periods.FY               # FY2022-2027 in the firm/budget grid
_OY = _periods.OY                    # FY2028-2031 FYDP outyear band
_LAST_FIRM_FY = 2025                 # <= this: firm; > this: "E" suffix
_PROGRAMS = [("DDG-51", DD)]
_NCOLS_2 = 1 + len(_FIRM_FY) + 1     # program label + 6 FY columns + BC coeff column
_NCOLS_3 = 1 + len(_OY)              # program label + 4 outyear columns


def _fy_label(fy: int) -> str:
    return f"FY{fy}" + ("E" if fy > _LAST_FIRM_FY else "")


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_EXEC_SUMMARY, _NCOLS_2)                                # row 2
    c.caption("DDG-51 outsourced TAM, FY2022-31, constant FY2026 $M")  # row 3
    c.blank(2)

    # §1 Scope
    c.section("§1 - Scope", _NCOLS_2)
    c.blank()
    c.write(["Question", "DDG-51 outsourced new-construction TAM"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.write(["Definition", "BC base x supplier coefficient, plus applicable overlays"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.write(["Program", "DDG-51 (Arleigh Burke, LI 2122)"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.write(["Window", "FY2022-31, constant FY2026 $M"],
            styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    # §2 Outsourced TAM by fiscal year, firm/budget years (transposed: programs down)
    c.section("§2 - FY2022-27 outsourced TAM ($M)", _NCOLS_2)
    c.blank()
    c.write(["Program"] + [_fy_label(fy) for fy in _FIRM_FY] + ["BC coeff"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * (len(_FIRM_FY) + 1))
    prog_rows = []
    for nm, mod in _PROGRAMS:
        vals = ([nm] + [f"={mod.tam_cell(fy)}" for fy in _FIRM_FY]
                + [f"={mod.applied_coeff_cell()}"])
        styles = [S_DEFAULT] + [S_LINK_NUM] * len(_FIRM_FY) + [S_LINK_PCT]
        prog_rows.append(c.write(vals, styles=styles))
    r0, r1 = prog_rows[0], prog_rows[-1]
    total_vals = (["Total"]
                  + [f"=SUM({col_letter(2 + i)}{r0}:{col_letter(2 + i)}{r1})"
                     for i in range(len(_FIRM_FY))]
                  + [None])
    c.total(total_vals, styles=[S_BOLD] + [S_NUM] * len(_FIRM_FY) + [S_DEFAULT],
            n_cols=_NCOLS_2)
    c.write(["E = estimate: FY2026-27 budget request (FY2026 incl. OBBBA)."],
            styles=[S_ITALIC])
    c.blank(2)

    # §3 FY2028-31 outyear outlook band: low (status-quo coeff) and high (compound-ramped)
    c.section("§3 - FY2028-31 outlook ($M)", _NCOLS_3)
    c.blank()
    c.write(["Outyear ($M)"] + [_fy_label(fy) for fy in _OY],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_OY))
    cl = [col_letter(2 + i) for i in range(len(_OY))]
    lo_rows = [c.write([f"{nm} low"] + [f"={mod.outyear_low_cell(fy)}" for fy in _OY],
                       styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
               for nm, mod in _PROGRAMS]
    c.total(["Total low"] + [f"=SUM({cl[i]}{lo_rows[0]}:{cl[i]}{lo_rows[-1]})"
                             for i in range(len(_OY))],
            styles=[S_BOLD] + [S_NUM] * len(_OY), n_cols=_NCOLS_3)
    hi_rows = [c.write([f"{nm} high"] + [f"={mod.outyear_high_cell(fy)}" for fy in _OY],
                       styles=[S_DEFAULT] + [S_LINK_NUM] * len(_OY))
               for nm, mod in _PROGRAMS]
    c.total(["Total high"] + [f"=SUM({cl[i]}{hi_rows[0]}:{cl[i]}{hi_rows[-1]})"
                              for i in range(len(_OY))],
            styles=[S_BOLD] + [S_NUM] * len(_OY), n_cols=_NCOLS_3)
    c.write(["Low holds coefficients flat; high compound-ramps Assumptions §4 growth to FY2031."],
            styles=[S_ITALIC])

    ws = worksheet(c.rows, cols=[22] + [11] * len(_FIRM_FY) + [11],
                   tab_color=group_color(_GROUP), with_gutter=True,
                   show_outline_symbols=False)
    return WorksheetSpec(ws)


EXECUTIVE_SUMMARY = SheetEntry(TAB_EXEC_SUMMARY, _GROUP, _render)
