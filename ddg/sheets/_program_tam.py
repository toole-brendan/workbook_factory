"""_program_tam - shared builder for the three per-program TAM tabs.

NON-sheet helper. Virginia / Columbia / DDG-51 each get their OWN self-contained TAM
tab (model group), but they share one shape: stream bases x supplier coefficient =
TAM by FY, a cumulative/average roll-up, and a folded FY2028-FY2031 outyear
projection off the FYDP. The genuine per-program differences are passed as config:

  Virginia  - BC + OBBBA streams; OBBBA enters the outlook denominator with the
              FY27 execution-spillover split.
  Columbia  - BC stream only (no OBBBA award).
  DDG-51    - BC + AP/LLTM + OBBBA streams; the BC coefficient is FY2022-vintage for
              FY2022 (FY18-22 masters) and MYP-corrected for FY23-27.

No stream toggles (streams always-on). Live OK/FAIL checks on the coefficients and
outyear band live on the Checks tab; validate_workbook.py asserts the baseline
regression externally.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet, col_letter
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER, S_NUM, S_PCT,
    S_LINK_NUM, S_LINK_PCT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from workbook_master_tam.sheets._layout import RowCursor
from workbook_master_tam.sheets.scn_budget import scn_cell, ddg_ap_base_cell
from workbook_master_tam.sheets.obbba import (
    obbba_bc_base_cell, obbba_gross_const_cell, obbba_gross_execaligned_cell,
)
from workbook_master_tam.sheets.fydp_outyears import fydp_gross_cell
from workbook_master_tam.sheets.assumptions import (
    ddg_ap_coeff_cell,
    outlook_growth_cell, outlook_ddg_hii_share_cell,
)
from workbook_master_tam.sheets._periods import FY as _FY, OY as _OY

_GROUP = "model"
_FY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_FY)}     # C..H
_OY_COL = {fy: col_letter(2 + i) for i, fy in enumerate(_OY)}     # C..F
_TOTAL_COL = col_letter(2 + len(_FY))                             # I
_C0, _CN = _FY_COL[_FY[0]], _FY_COL[_FY[-1]]                      # C, H
_C25 = _FY_COL[2025]                                              # F (FY22-25 = C:F)
_NCOLS = 1 + len(_FY) + 1                                         # label + 6 FY + Total


def build_program_tam(*, li, name, tab, intro, bc_coeff_cell, bc_coeff_fy22_cell=None,
                      obbba="none", ap=False, fydp_li=None, biw_carveout=False):
    """Build one program TAM SheetEntry. Returns (entry, accessors_dict).

    intro: italic one-line caption under the title banner (house pattern: title ->
    italic caption -> two blank rows -> §1 banner).
    obbba: "none" | "spill" (Virginia) | "const" (DDG).  ap: DDG AP/LLTM stream.
    biw_carveout: DDG only - the outyear intensity growth applies to the HII-Ingalls
    share of BC only (BIW held flat); the responsive share is Assumptions §4 ddg_hii.
    """
    fydp_li = fydp_li if fydp_li is not None else li
    has_obbba = obbba != "none"
    n_headline = 5 + (1 if has_obbba else 0) + (1 if ap else 0)
    body_base = 11 + n_headline   # title + italic caption + 2 blanks + §1 + headline + 2 blanks

    def _coeff(fy):
        if bc_coeff_fy22_cell is not None and fy == 2022:
            return bc_coeff_fy22_cell()
        return bc_coeff_cell()

    def _build_body(base):
        P: dict = {}
        c = RowCursor(base)

        # §2 TAM by fiscal year ----------------------------------------------------
        c.section("§2 - TAM by fiscal year ($M, constant FY2026)", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY] + ["FY22-27"],
                styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * (len(_FY) + 1))
        # stream bases (pure cross-sheet links to data tabs -> green S_LINK_NUM)
        P["bc_base"] = c.write(["BC base (P-5c Basic Construction)"]
                               + [f"={scn_cell(li, fy, 'basic')}" for fy in _FY]
                               + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
                               styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FY) + [S_NUM])
        if has_obbba:
            P["obbba_base"] = c.write(["OBBBA mandatory BC base"]
                                      + [f"={obbba_bc_base_cell(li, fy)}" for fy in _FY]
                                      + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
                                      styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FY) + [S_NUM])
        if ap:
            P["ap_base"] = c.write(["AP/LLTM base (P-10 Ship Construction EOQ)"]
                                   + [f"={ddg_ap_base_cell(li, fy)}" for fy in _FY]
                                   + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
                                   styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FY) + [S_NUM])
        # Applied BC coefficient localized onto the tab ONCE (per FY: DDG-51 uses its
        # FY2022 vintage for FY2022 and the MYP-corrected value FY2023+; subs are flat).
        # The stream TAMs below multiply by THIS row, so each annual TAM cell is
        # same-sheet: base x local coefficient.
        P["coeff_by_fy"] = c.write(
            ["Applied BC coefficient (from Place of Performance)"]
            + [f"={_coeff(fy)}" for fy in _FY],
            styles=[S_DEFAULT] + [S_LINK_PCT] * len(_FY))
        # stream TAMs (base x coefficient). Zero-procurement years resolve to a numeric
        # 0 (rendered "-" by the dash format), so no IF/N guard is needed.
        P["tam_bc"] = c.write(
            ["TAM - BC stream"]
            + [f'={_FY_COL[fy]}{P["bc_base"]}*{_FY_COL[fy]}${P["coeff_by_fy"]}' for fy in _FY]
            + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
            styles=[S_DEFAULT] + [S_NUM] * len(_FY) + [S_NUM])
        stream_rows = [P["tam_bc"]]
        if has_obbba:
            P["tam_obbba"] = c.write(
                ["TAM - OBBBA mandatory stream"]
                + [f'={_FY_COL[fy]}{P["obbba_base"]}*{_FY_COL[fy]}${P["coeff_by_fy"]}' for fy in _FY]
                + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
                styles=[S_DEFAULT] + [S_NUM] * len(_FY) + [S_NUM])
            stream_rows.append(P["tam_obbba"])
        if ap:
            P["tam_ap"] = c.write(
                ["TAM - AP/LLTM stream"]
                + [f'={_FY_COL[fy]}{P["ap_base"]}*{ddg_ap_coeff_cell()}' for fy in _FY]
                + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
                styles=[S_DEFAULT] + [S_NUM] * len(_FY) + [S_NUM])
            stream_rows.append(P["tam_ap"])
        P["tam"] = c.total(
            ["TAM (all streams)"]
            + [f"=SUM({_FY_COL[fy]}{stream_rows[0]}:{_FY_COL[fy]}{stream_rows[-1]})" for fy in _FY]
            + [lambda r: f"=SUM({_C0}{r}:{_CN}{r})"],
            styles=[S_BOLD] + [S_NUM] * (len(_FY) + 1), n_cols=_NCOLS)
        c.blank(2)

        # §2a Roll-up -------------------------------------------------------------
        c.subsection("§2a - Roll-up & applied coefficient", _NCOLS)
        c.blank()
        c.write(["Measure", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
        P["cum"] = c.write(["Cumulative TAM (FY22-27) $M", f"={_TOTAL_COL}{P['tam']}"],
                           styles=[S_BOLD, S_NUM])
        # Fixed FY2022-27 window: average over the period = cumulative / len(FY). Uses
        # the period count (not =AVERAGE), which is blank-safe for programs with
        # zero-procurement years (e.g. Columbia FY22/23/25).
        P["avg"] = c.write(["Average annual TAM $M/yr", f"=C{P['cum']}/{len(_FY)}"],
                           styles=[S_BOLD, S_NUM])
        if has_obbba:
            P["obbba_tam"] = c.write(["of which OBBBA mandatory TAM (cumulative) $M",
                                      f"={_TOTAL_COL}{P['tam_obbba']}"],
                                     styles=[S_DEFAULT, S_NUM])
        if ap:
            c.write(["of which AP/LLTM TAM (cumulative) $M", f"={_TOTAL_COL}{P['tam_ap']}"],
                    styles=[S_DEFAULT, S_NUM])
        P["coeff_main"] = c.write(["Applied BC supplier coefficient", f"={bc_coeff_cell()}"],
                                  styles=[S_DEFAULT, S_PCT])
        if bc_coeff_fy22_cell is not None:
            c.write(["Applied BC coefficient, FY2022 vintage", f"={bc_coeff_fy22_cell()}"],
                    styles=[S_DEFAULT, S_PCT])
        c.blank(2)

        # §3 Penetration & FY28-31 outyear outlook --------------------------------
        c.section("§3 - Penetration and outyears ($M)", _NCOLS)
        c.blank()
        c.write(["Metric"] + [f"FY{fy}" for fy in _FY], styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY))
        P["pen_num"] = c.write(["Outsourced TAM, all streams ($M)"]
                               + [f"=N({_FY_COL[fy]}{P['tam']})" for fy in _FY],
                               styles=[S_BOLD] + [S_NUM] * len(_FY))
        P["den_tse"] = c.write(["Total ship spend: P-5c Total Ship Estimate ($M)"]
                               + [f"={scn_cell(li, fy, 'total')}" for fy in _FY],
                               styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FY))
        if obbba == "spill":
            # Links to the OBBBA tab's execution-aligned gross row (FY26/FY27 spillover
            # split lives there now, not reconstructed here) - a pure link, so green.
            P["den_obbba"] = c.write(["plus OBBBA gross award ($M; FY27 via spillover)"]
                                     + [f"={obbba_gross_execaligned_cell(li, fy)}" for fy in _FY],
                                     styles=[S_DEFAULT] + [S_LINK_NUM] * len(_FY))
        elif obbba == "const":
            # N()-wrapped link is a transform, not a pure link -> black.
            P["den_obbba"] = c.write(["plus OBBBA gross award ($M)"]
                                     + [f"=N({obbba_gross_const_cell(li, fy)})" for fy in _FY],
                                     styles=[S_DEFAULT] + [S_NUM] * len(_FY))
        if has_obbba:
            P["den"] = c.total(["Total ship spend incl. OBBBA ($M)"]
                               + [f"={_FY_COL[fy]}{P['den_tse']}+N({_FY_COL[fy]}{P['den_obbba']})"
                                  for fy in _FY],
                               styles=[S_BOLD] + [S_NUM] * len(_FY), n_cols=_NCOLS - 1)
        else:
            P["den"] = c.total(["Total ship spend ($M)"]
                               + [f"=N({_FY_COL[fy]}{P['den_tse']})" for fy in _FY],
                               styles=[S_BOLD] + [S_NUM] * len(_FY), n_cols=_NCOLS - 1)
        P["pen"] = c.write(["Penetration: TAM / total ship spend"]
                           + [f'=IF({_FY_COL[fy]}{P["den"]}=0,"",{_FY_COL[fy]}{P["pen_num"]}/{_FY_COL[fy]}{P["den"]})'
                              for fy in _FY],
                           styles=[S_BOLD] + [S_PCT] * len(_FY))
        c.blank()
        # FY22-25 penetration look-back (descriptive; no longer drives the outyear).
        c.write(["Measure", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
        P["pen_2225"] = c.write(
            ["FY22-25 average penetration",
             f"=SUM({_C0}{P['pen_num']}:{_C25}{P['pen_num']})/SUM({_C0}{P['den']}:{_C25}{P['den']})"],
            styles=[S_DEFAULT, S_PCT])
        # Outyear outlook: growth applied to the BC coefficient (not blended penetration).
        # The HII outsourcing-hours growth (Assumptions §4) is phased in as a COMPOUND
        # ramp - a constant annual rate that reaches the full uplift at FY2031, the last
        # outyear: the i-th of N outyears gets factor (1+g)^(i/N), so FY2031 = (1+g)^1.
        # DDG-51 carves BIW out - only HII's responsive BC share grows, BIW held flat -
        # so its blended coefficient grows by 1 + w_hii*((1+g)^(i/N) - 1); subs ramp the
        # whole coefficient (w = 1). Growth is NOT throughput-normalized (raw hours rate).
        P["fc_bc_share"] = c.write(
            ["Forecast BC share",
             f"=SUM({_C0}{P['bc_base']}:{_C25}{P['bc_base']})/SUM({_C0}{P['den_tse']}:{_C25}{P['den_tse']})"],
            styles=[S_BOLD, S_PCT])
        P["coeff_low"] = c.write(["Outyear BC coefficient, low", f"={bc_coeff_cell()}"],
                                 styles=[S_DEFAULT, S_LINK_PCT])
        P["g_int"] = c.write(["Outyear outsourcing growth (annual target)",
                              f"={outlook_growth_cell()}"],
                             styles=[S_DEFAULT, S_LINK_PCT])
        if biw_carveout:
            P["w_resp"] = c.write(["HII share of DDG BC",
                                   f"={outlook_ddg_hii_share_cell()}"],
                                  styles=[S_DEFAULT, S_LINK_PCT])
        c.blank()
        c.write(["Outyears"] + [f"FY{fy}" for fy in _OY],
                styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_OY))
        P["oy_gross"] = c.write(["FYDP gross"]
                                + [f"={fydp_gross_cell(fydp_li, fy)}" for fy in _OY],
                                styles=[S_BOLD] + [S_LINK_NUM] * len(_OY))
        P["oy_bc"] = c.write(["Outyear BC base"]
                             + [f"={_OY_COL[fy]}{P['oy_gross']}*$C${P['fc_bc_share']}" for fy in _OY],
                             styles=[S_DEFAULT] + [S_NUM] * len(_OY))
        # High BC coefficient, ramped: compound to the full uplift at FY2031 (last outyear).
        # i-th of N outyears -> (1+g)^(i/N); DDG blends only HII's share (BIW held flat).
        _n_oy = len(_OY)
        _ramp = [f"POWER(1+$C${P['g_int']},{i + 1}/{_n_oy})" for i in range(_n_oy)]
        if biw_carveout:
            _hi_cells = [f"=$C${P['coeff_low']}*(1+$C${P['w_resp']}*({r}-1))" for r in _ramp]
        else:
            _hi_cells = [f"=$C${P['coeff_low']}*{r}" for r in _ramp]
        P["oy_coeff_hi"] = c.write(
            ["Outyear BC coefficient, high (compounded)"] + _hi_cells,
            styles=[S_DEFAULT] + [S_PCT] * _n_oy)
        P["oy_lo"] = c.write(["Outsourced BC, low"]
                             + [f"={_OY_COL[fy]}{P['oy_bc']}*$C${P['coeff_low']}" for fy in _OY],
                             styles=[S_BOLD] + [S_NUM] * len(_OY))
        P["oy_hi"] = c.write(["Outsourced BC, high"]
                             + [f"={_OY_COL[fy]}{P['oy_bc']}*{_OY_COL[fy]}{P['oy_coeff_hi']}" for fy in _OY],
                             styles=[S_BOLD] + [S_NUM] * len(_OY))
        c.blank()
        P["oy_lo_avg"] = c.write(["Outyear low average",
                                  f"=AVERAGE(C{P['oy_lo']}:F{P['oy_lo']})"],
                                 styles=[S_DEFAULT, S_NUM])
        P["oy_hi_avg"] = c.write(["Outyear high average",
                                  f"=AVERAGE(C{P['oy_hi']}:F{P['oy_hi']})"],
                                 styles=[S_DEFAULT, S_NUM])
        return c.rows, c.at(), P

    _rows, _after, P = _build_body(body_base)

    def _render() -> WorksheetSpec:
        c = RowCursor(2)
        c.title(tab, _NCOLS)                                 # row 2
        c.caption(intro)                                     # row 3
        c.blank(2)                                           # rows 4-5
        c.section("§1 - Headline TAM", _NCOLS)
        c.blank()
        c.write(["Measure", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
        c.write(["Cumulative TAM (FY22-27) $M", f"=C{P['cum']}"], styles=[S_BOLD, S_NUM])
        c.write(["Average annual TAM $M/yr", f"=C{P['avg']}"], styles=[S_BOLD, S_NUM])
        c.write(["Applied BC supplier coefficient", f"=C{P['coeff_main']}"], styles=[S_DEFAULT, S_PCT])
        if has_obbba:
            c.write(["incl. OBBBA mandatory TAM $M", f"=C{P['obbba_tam']}"], styles=[S_DEFAULT, S_NUM])
        if ap:
            c.write(["incl. AP/LLTM TAM $M", f"={_TOTAL_COL}{P['tam_ap']}"], styles=[S_DEFAULT, S_NUM])
        c.write(["Implied outyear (FY28-31) low $M/yr", f"=C{P['oy_lo_avg']}"], styles=[S_DEFAULT, S_NUM])
        c.write(["Implied outyear (FY28-31) high $M/yr", f"=C{P['oy_hi_avg']}"], styles=[S_DEFAULT, S_NUM])
        c.blank(2)
        assert c.at() == body_base, f"{tab}: headline ends at {c.at()}, expected {body_base}"
        c.feed(_rows, _after)
        ws = worksheet(c.rows, cols=[42, 12, 12, 12, 12, 12, 12, 13],
                       tab_color=group_color(_GROUP), with_gutter=True,
                       show_outline_symbols=False)
        return WorksheetSpec(ws)

    entry = SheetEntry(tab, _GROUP, _render)
    acc = dict(
        tam_cell=lambda fy: f"'{tab}'!{_FY_COL[fy]}{P['tam']}",
        cum_tam_cell=lambda: f"'{tab}'!C{P['cum']}",
        avg_annual_tam_cell=lambda: f"'{tab}'!C{P['avg']}",
        applied_coeff_cell=lambda: f"'{tab}'!C{P['coeff_main']}",
        pen_fy2225_cell=lambda: f"'{tab}'!C{P['pen_2225']}",
        outyear_low_avg_cell=lambda: f"'{tab}'!C{P['oy_lo_avg']}",
        outyear_high_avg_cell=lambda: f"'{tab}'!C{P['oy_hi_avg']}",
        # per-outyear (FY2028-31) low/high band cells, as cell refs
        outyear_low_cell=lambda fy: f"'{tab}'!{_OY_COL[fy]}{P['oy_lo']}",
        outyear_high_cell=lambda fy: f"'{tab}'!{_OY_COL[fy]}{P['oy_hi']}",
        obbba_tam_cell=(lambda: f"'{tab}'!C{P['obbba_tam']}") if has_obbba else None,
    )
    return entry, acc
