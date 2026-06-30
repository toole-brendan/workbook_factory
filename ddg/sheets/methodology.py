"""methodology - the "Methodology" tab (guide group).

The framing, formula, scope, key definitions, per-program coefficient basis, and the
source list - one tab merging what the original per-program workbooks split across
Methodology + Source Index + References.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from sheets._tam_layout import RowCursor
from sheets._tabs import TAB_METHODOLOGY

_GROUP = "guide"
_NCOLS = 2


def _kv(c, topic, detail):
    c.write([topic, detail], styles=[S_BOLD, S_DEFAULT])


def _p(c, text):
    c.write([text], styles=[S_DEFAULT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_METHODOLOGY, _NCOLS)
    c.caption("TAM definition, formula, scope, coefficient basis, and sources")
    c.blank(2)

    # §1 Scope
    c.section("§1 - Scope", _NCOLS)
    c.blank()
    _kv(c, "Question", "Supplier-addressable TAM for DDG-51 (Arleigh Burke) new construction.")
    _kv(c, "Market", "New-construction work outsourced away from the prime/co-prime yards.")
    _kv(c, "Basis", "Built from SCN budget + DoD award place-of-performance, not sparse subawards.")
    c.blank(2)

    # §2 Formula
    c.section("§2 - Formula", _NCOLS)
    c.blank()
    _p(c, "TAM = BC base x BC coeff + OBBBA BC base x BC coeff + AP/LLTM base x AP coeff")
    _kv(c, "BC base", "P-5c Basic Construction $/program/FY (SCN Budget), constant FY2026 $; GFE excluded.")
    _kv(c, "BC coefficient", "Award $-share landing away from the prime/co-prime yards (Place of Performance).")
    _kv(c, "OBBBA BC base", "BC slice of the OBBBA mandatory award (gross x BC share).")
    _kv(c, "AP/LLTM", "DDG only: P-10 Ship Construction EOQ x AP coeff (subs hold LLTM inside BC).")
    c.blank(2)

    # §3 Coefficients
    c.section("§3 - Coefficients", _NCOLS)
    c.blank()
    _kv(c, "DDG-51 (~25.3%)", "MYP-corrected FY23-27 masters + disclosed corpus; FY2022 uses FY18-22 vintage (~22%).")
    c.blank(2)

    # §4 Sources
    c.section("§4 - Sources", _NCOLS)
    c.blank()
    c.write(["Source", "Use"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for src, use in [
        ("PB2027 SCN P-5c", "BC base + cost-category breakdown (SCN Budget)"),
        ("PB2027 SCN P-40", "FY2025-31 FYDP outyears (FYDP Outyears)"),
        ("PB2027 SCN P-10", "DDG Ship Construction EOQ (AP/LLTM base)"),
        ("DoD award announcements", "place-of-performance corpus + construction masters"),
        ("DDG MYP awards", "DDG applied BC coefficient (MYP-corrected)"),
        ("OBBBA Sec. 20002", "mandatory new-construction overlay (OBBBA Mandatory)"),
        ("Green Book Table 5-4", "constant-FY2026 deflators (Deflators)"),
    ]:
        c.write([src, use], styles=[S_DEFAULT, S_DEFAULT])

    ws = worksheet(c.rows, cols=[34, 80],
                   tab_color=group_color(_GROUP), with_gutter=True,
                   show_outline_symbols=False)
    return WorksheetSpec(ws)


METHODOLOGY = SheetEntry(TAB_METHODOLOGY, _GROUP, _render)
