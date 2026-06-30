"""scn_budget - the "SCN Budget" data tab (combined, all three programs).

The P-5c per-FY cost-category breakdown for Virginia (LI 2013), Columbia (LI 1045)
and DDG-51 (LI 2122), loaded from extracted/scn_budget.csv (then-year $M). Each
program block carries: the then-year categories, derived BC/GFE ratios, and a
constant-FY2026 block (then-year x Green Book deflator). Basic Construction is the
value every program's TAM tab consumes as its BC stream base.

Promoted accessors:
  scn_cell(li, fy, metric) -> 'SCN Budget'!...  Dollar metrics resolve to the
    constant-FY2026 rows; ratio metrics (bc_pct, gfe_pct) resolve to the then-year
    ratio rows (a same-FY ratio is deflator-invariant).
  ddg_ap_base_cell(li, fy)  DDG-51 AP/LLTM (P-10 EOQ) constant-FY2026 base (§5).
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_NUM_INPUT, S_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.cuts import load_rows, as_float
from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.tabs import TAB_SCN_BUDGET
from ddg.sheets.deflators import deflator_factor_cell
from ddg.sheets.kit.styles import S_FACTOR
from ddg.sheets.kit.periods import FY as _FY

_GROUP = "data"
_FY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_FY)}     # C..H
_C0, _CN = _FY_COL[_FY[0]], _FY_COL[_FY[-1]]                      # C, H
_NCOLS = 1 + len(_FY) + 1
_HDR = [S_HEADER_LEFT] + [S_HEADER_CENTER] * (len(_FY) + 1)
_HDR_FY = [S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY)

# title(2)+italic(3)+2 blanks+§1 banner(6)+blank+header(8)+1 program row(9)+
# portfolio(10)+local deflator factor row(11)+2 blanks -> detail at 14.
# (DDG-51-only slice: §1 carries one program row instead of three.)
_FACTOR_ROW = 11     # one local "Constant-FY2026 factor" row; the §Nb const blocks
                     # multiply by THIS row (6 cells) instead of cross-sheet refs.
_DETAIL_BASE = 14

_LABEL = {
    "total": "Total Ship Estimate", "plans": "Plans Costs",
    "propulsion": "Propulsion Equipment", "electronics": "Electronics",
    "hme": "Hull, Mechanical, Electrical (HM&E)", "ordnance": "Ordnance",
    "other_cost": "Other Cost", "technology_insertion": "Technology Insertion",
    "gfe": "GFE Sum", "change_orders": "Change Orders",
    "basic": "Basic Construction (TAM base)",
}
_SUB_METRICS = ["total", "plans", "propulsion", "electronics", "hme", "ordnance",
                "other_cost", "technology_insertion", "gfe", "change_orders", "basic"]
_DDG_METRICS = ["total", "plans", "electronics", "ordnance", "hme", "other_cost",
                "gfe", "change_orders", "basic"]
_RATIO_METRICS = {"bc_pct", "gfe_pct"}
_PROGRAMS = [(2122, "DDG-51", _DDG_METRICS)]


def _load():
    out: dict[int, dict[int, dict]] = {}
    for r in load_rows("scn_budget"):
        li, fy = int(r["li"]), int(r["fy"])
        out.setdefault(li, {})[fy] = {m: as_float(r.get(m)) for m in _SUB_METRICS}
    return out


def _build_detail(base: int):
    data = _load()
    then: dict = {}
    const: dict = {}
    ratio: dict = {}
    c = RowCursor(base)
    sec = 2
    for li, name, metrics in _PROGRAMS:
        then[li], const[li], ratio[li] = {}, {}, {}
        c.section(f"§{sec} - {name} P-5c", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        for m in metrics:
            vals = [_LABEL[m]] + [(data.get(li, {}).get(fy, {}) or {}).get(m) for fy in _FY]
            then[li][m] = c.write(vals, styles=[S_BOLD] + [S_NUM_INPUT] * len(_FY))
        c.blank()
        c.subsection(f"§{sec}a - Ratios", _NCOLS)
        c.blank()
        c.write(["Ratio"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        rt = then[li]["total"]
        for label, num_m, key in [("BC % of Total", "basic", "bc_pct"),
                                  ("GFE % of Total", "gfe", "gfe_pct")]:
            nr = then[li][num_m]
            vals = [label] + [f'=IF({_FY_COL[fy]}{rt}=0,"",{_FY_COL[fy]}{nr}/{_FY_COL[fy]}{rt})'
                              for fy in _FY]
            ratio[li][key] = c.write(vals, styles=[S_BOLD] + [S_PCT] * len(_FY))
        c.blank()
        c.subsection(f"§{sec}b - Constant FY2026 $M", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
        for m in metrics:
            vals = [_LABEL[m]] + [f"={_FY_COL[fy]}{then[li][m]}*{_FY_COL[fy]}${_FACTOR_ROW}"
                                  for fy in _FY]
            const[li][m] = c.write(vals, styles=[S_BOLD] + [S_NUM] * len(_FY))
        c.blank(2)
        sec += 1

    # §5 - DDG-51 AP/LLTM (P-10): source data folded onto the data tab (was hardcoded
    # on Assumptions). Constant-$ EOQ = then-year x the local deflator factor row; this
    # row is the DDG TAM tab's AP/LLTM base. Only the AP coefficient stays on Assumptions.
    ap = {int(r["fy"]): r for r in load_rows("ap_lltm")}
    c.section(f"§{sec} - DDG-51 AP/LLTM (P-10 EOQ)", _NCOLS)
    c.blank()
    c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=_HDR_FY)
    c.write(["CY AP gross, then-year $ (P-1; memo)"]
            + [as_float((ap.get(fy) or {}).get("cy_gross_then_$M")) for fy in _FY],
            styles=[S_DEFAULT] + [S_NUM_INPUT] * len(_FY))
    ap_eoq = c.write(["Ship Construction EOQ, then-year $ (P-10)"]
                     + [as_float((ap.get(fy) or {}).get("eoq_then_$M")) for fy in _FY],
                     styles=[S_BOLD] + [S_NUM_INPUT] * len(_FY))
    ap_const_row = c.write(["Ship Construction EOQ, constant FY2026 $M"]
                           + [f"={_FY_COL[fy]}{ap_eoq}*{_FY_COL[fy]}${_FACTOR_ROW}" for fy in _FY],
                           styles=[S_BOLD] + [S_NUM] * len(_FY))
    c.blank(2)
    return c.rows, c.at(), then, const, ratio, ap_const_row


_ROWS, _AFTER, _then, _const, _ratio, _AP_CONST_ROW = _build_detail(_DETAIL_BASE)


def scn_cell(li: int, fy: int, metric: str) -> str:
    if li not in _then:
        raise ValueError(f"Unknown LI {li!r}")
    if fy not in _FY_COL:
        raise ValueError(f"FY {fy!r} outside {_FY!r}")
    if metric in _RATIO_METRICS:
        return f"'{TAB_SCN_BUDGET}'!{_FY_COL[fy]}{_ratio[li][metric]}"
    if metric not in _const[li]:
        raise ValueError(f"Unknown metric {metric!r} for LI {li}")
    return f"'{TAB_SCN_BUDGET}'!{_FY_COL[fy]}{_const[li][metric]}"


def ddg_ap_base_cell(li: int, fy: int) -> str:
    """DDG-51 AP/LLTM (P-10 Ship Construction EOQ) constant-FY2026 base -> the DDG TAM
    tab's AP stream. DDG-only; the AP supplier coefficient is a separate Assumptions knob."""
    if li != 2122:
        raise ValueError(f"AP/LLTM stream is DDG-only; got LI {li!r}")
    if fy not in _FY_COL:
        raise ValueError(f"FY {fy!r} outside {_FY!r}")
    return f"'{TAB_SCN_BUDGET}'!{_FY_COL[fy]}{_AP_CONST_ROW}"


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_SCN_BUDGET, _NCOLS)
    c.caption("PB2027 P-5c cost categories and constant-dollar BC bases")
    c.blank(2)
    c.section("§1 - Basic Construction by program", _NCOLS)
    c.blank()
    c.write(["Measure"] + [f"FY{fy}" for fy in _FY] + ["Total"], styles=_HDR)
    for li, name, _m in _PROGRAMS:
        vals = ([f"{name} Basic Construction"]
                + [f"={scn_cell(li, fy, 'basic')}" for fy in _FY]
                + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"])
        c.write(vals, styles=[S_BOLD] + [S_NUM] * len(_FY) + [S_NUM])
    port = (["Portfolio Basic Construction"]
            + ["=" + "+".join(f"N({scn_cell(li, fy, 'basic')})" for li, _n, _m in _PROGRAMS)
               for fy in _FY]
            + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"])
    c.total(port, styles=[S_BOLD] + [S_NUM] * len(_FY) + [S_NUM], n_cols=_NCOLS)
    # Local deflator driver: link each FY's factor from Deflators ONCE; the per-program
    # constant-FY2026 blocks below multiply by this row, not 186 cross-sheet refs.
    fac_r = c.write(["Constant-FY2026 factor (then-year x this; from Deflators)"]
                    + [f"={deflator_factor_cell(fy)}" for fy in _FY],
                    styles=[S_BOLD] + [S_FACTOR] * len(_FY))
    assert fac_r == _FACTOR_ROW, f"factor row at {fac_r}, expected {_FACTOR_ROW}"
    c.blank(2)

    assert c.at() == _DETAIL_BASE, f"headline ends at {c.at()}, expected {_DETAIL_BASE}"
    c.feed(_ROWS, _AFTER)
    ws = worksheet(c.rows, cols=[40, 12, 12, 12, 12, 12, 12, 13],
                   tab_color=group_color(_GROUP), with_gutter=True,
                   show_outline_symbols=False)
    return WorksheetSpec(ws)


SCN_BUDGET = SheetEntry(TAB_SCN_BUDGET, _GROUP, _render)
