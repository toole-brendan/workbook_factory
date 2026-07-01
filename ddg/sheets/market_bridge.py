"""market_bridge - TAM-to-observed-SAM bridge and denominator ladder."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER,
    S_NUM, S_PCT, S_LINK_NUM,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.styles import S_ITALIC
from ddg.sheets.kit.tabs import TAB_MARKET_BRIDGE
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets import ddg_tam as TAM
from ddg.sheets.ddg_program_vendors import ddg_pv_cols
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols

_GROUP = "summary"
_NCOLS = 6
_BRIDGE_FY = (2022, 2023, 2024, 2025)

_TX_REAL = ddg_tx_cols(TX_REAL)
_TX_CONF = ddg_tx_cols("Hull Confidence")
_TX_BUILDER = ddg_tx_cols("Builder")
_TX_SWBS = ddg_tx_cols("SWBS")

_PV_AMT = ddg_pv_cols("Subaward $M")
_PV_D = ddg_pv_cols("Capability Domain Archetype (D)")
_PV_P = ddg_pv_cols("Primary Output Archetype (P)")


def _sam_fy_total(fy: int) -> str:
    return f"=SUM({ddg_pv_cols(f'FY{str(fy)[-2:]} $M')})"


def _conf_raw(*grades: str) -> str:
    return "+".join(f'SUMIFS({_TX_REAL},{_TX_CONF},"{g}")' for g in grades)


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_MARKET_BRIDGE, _NCOLS)
    c.caption("TAM vs observed first-tier SAM, plus the denominator ladder for downstream cuts.")
    c.blank(2)

    c.section("§1 - TAM vs observed SAM", _NCOLS)
    c.blank()
    c.write(["FY", "TAM $M", "Observed SAM $M", "Observed SAM / TAM", "Use", "Caveat"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * 3 + [S_HEADER_LEFT, S_HEADER_LEFT])
    for fy in _BRIDGE_FY:
        c.write([fy, f"={TAM.tam_cell(fy)}", _sam_fy_total(fy),
                 lambda r: f'=IFERROR(D{r}/C{r},"")',
                 "Bridge top-down opportunity to reported supplier evidence",
                 "Reporting / reach bridge, not market penetration"],
                styles=[S_DEFAULT, S_LINK_NUM, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.blank()
    c.write(["Observed SAM uses reported first-tier subawards as evidence of supplier structure "
             "and timing; it is not the full outsourced-market total."], styles=[S_ITALIC])
    c.blank(2)

    total_raw = f"SUM({_TX_REAL})"
    hii_raw = f'SUMIFS({_TX_REAL},{_TX_BUILDER},"HII-Ingalls")'
    swbs_mapped_raw = f'({hii_raw}-SUMIFS({_TX_REAL},{_TX_BUILDER},"HII-Ingalls",{_TX_SWBS},"U00*"))'
    ab_raw = f"({_conf_raw('A', 'B')})"
    cd_raw = f"({_conf_raw('C', 'D')})"
    x_raw = f"({_conf_raw('X')})"
    dp_classified = f'SUMIFS({_PV_AMT},{_PV_D},"<>D0",{_PV_P},"<>P0")'

    c.section("§2 - Observed-SAM denominator ladder", _NCOLS)
    c.blank()
    c.write(["Layer", "Coverage basis", "$M", "Share", "Supports", "Boundary"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER,
                    S_HEADER_CENTER, S_HEADER_LEFT, S_HEADER_LEFT])
    c.write(["Observed SAM", "All DDG subaward transactions", f"={total_raw}/1000000", "=1",
             "Supplier ecosystem evidence", "Not the full outsourced-market total"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["D/P classified", "UEI x Program supplier labels", f"={dp_classified}",
             f'=IFERROR({dp_classified}/SUM({_PV_AMT}),"")',
             "Where-to-play by capability / output", "Depends on supplier classification quality"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["HII SWBS universe", "Builder = HII-Ingalls", f"={hii_raw}/1000000",
             f'=IFERROR({hii_raw}/{total_raw},"")',
             "Ship-system application", "GD-BIW rows carry no SWBS classification"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["SWBS mapped", "HII rows outside U00", f"={swbs_mapped_raw}/1000000",
             f'=IFERROR({swbs_mapped_raw}/{hii_raw},"")',
             "Mapped HII ship-system mix", "U00 remains no SWBS evidence"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["Exact hull", "Hull confidence A/B", f"={ab_raw}/1000000",
             f'=IFERROR({ab_raw}/{total_raw},"")',
             "Hull and hull-stage rollups", "C/D family-level dollars are not allocated"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["Family-level hull", "Hull confidence C/D", f"={cd_raw}/1000000",
             f'=IFERROR({cd_raw}/{total_raw},"")',
             "Candidate-family views; procurement-timing phase", "No single-hull dollar assignment"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.write(["Conflict / review", "Hull confidence X", f"={x_raw}/1000000",
             f'=IFERROR({x_raw}/{total_raw},"")',
             "Research queue", "Conflict / multi-hull / unassigned evidence"],
            styles=[S_DEFAULT, S_DEFAULT, S_LINK_NUM, S_PCT, S_DEFAULT, S_DEFAULT])
    c.blank(2)

    c.section("§3 - Cut discipline", _NCOLS)
    c.blank()
    c.write(["Cut", "Good for", "Do not use for"], styles=[S_HEADER_LEFT] * 3)
    for cut, good, boundary in [
        ("TAM", "Total outsourced opportunity by FY", "Supplier concentration or ship-system mix"),
        ("Observed SAM", "Reported supplier structure, continuity and concentration", "Full outsourced-market penetration"),
        ("D/P archetypes", "Entity-level capability and output-market screens", "Transaction-level ship-system assignment"),
        ("SWBS", "HII ship-system application", "GD-BIW ship-system mix without a separate assumption"),
        ("Exact hull A/B", "Hull x supplier rollups; per-hull build-stage drill-down", "Whole-market hull allocation"),
        ("Family-level C/D", "Candidate-family membership and procurement-timing phase", "Per-hull dollar split"),
    ]:
        c.write([cut, good, boundary], styles=[S_DEFAULT, S_DEFAULT, S_DEFAULT])

    ws = worksheet(c.rows, cols=[24, 34, 14, 12, 36, 42],
                   tab_color=group_color(_GROUP), with_gutter=True,
                   show_outline_symbols=False)
    return WorksheetSpec(ws)


MARKET_BRIDGE = SheetEntry(TAB_MARKET_BRIDGE, _GROUP, _render)
