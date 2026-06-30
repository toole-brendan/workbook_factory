"""sam_calculation_map - reader-facing map of the DDG SAM calculation chain."""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.sheets._layout import RowCursor
from ddg.sheets._italic import S_ITALIC
from ddg.sheets._tabs import (
    TAB_SAM_CALC_MAP, TAB_PRIME_AWARDS, TAB_DDG_TX, TAB_SUPPLIER_MASTER,
    TAB_SUPPLIER_YEAR, TAB_DDG_PROGRAM, TAB_ARCHETYPE_AUDIT, TAB_DOMAIN_CONC,
    TAB_WHERE_TO_PLAY, TAB_HULL_COVERAGE, TAB_HULL_SPEND, TAB_VENDOR_HULL,
    TAB_SWBS_COVERAGE, TAB_SWBS_ROLLUP, TAB_HULL_SWBS, TAB_VENDOR_HULL_SWBS,
    TAB_CD_LC_COVERAGE, TAB_HULL_LIFECYCLE, TAB_CD_LC_ROLLUP,
    TAB_CD_LC_CANDIDATES, TAB_DDG_TAM, TAB_CHECKS,
)

_GROUP = "summary"
_NCOLS = 3
_COLS = [28, 50, 50]


def _row(c: RowCursor, topic: str, meaning: str, read: str) -> int:
    return c.write([topic, meaning, read], styles=[S_BOLD, S_DEFAULT, S_DEFAULT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_SAM_CALC_MAP, _NCOLS)
    c.caption("How observed DDG-51 SAM moves from prime/subaward evidence to supplier, hull, SWBS and lifecycle cuts.")
    c.blank(2)

    c.section("§1 - SAM denominator and evidence chain", _NCOLS)
    c.write(["The SAM denominator is observed reported first-tier hull-builder subawards.  It is a reporting-and-reach view, not full market penetration."], styles=[S_ITALIC])
    c.blank()
    c.write(["Step", "What it establishes", "Primary sheets"], styles=[S_HEADER_LEFT] * _NCOLS)
    for topic, meaning, read in [
        ("Prime scope", "Prime awards establish which DDG hull-builder contracts are in-scope before subawards are read.", TAB_PRIME_AWARDS),
        ("Transaction fact", "One deduplicated published subaward record is the finest-grain SAM fact; dates, dollars, SWBS, hull and lifecycle tags live here.", TAB_DDG_TX),
        ("Supplier dimension", "Each supplier is resolved once at UEI x DDG program grain: name, parent, NAICS, role and D/P archetypes.", TAB_SUPPLIER_MASTER),
        ("Annual activity", "Supplier x FY rows add first-observed / continued / reactivated status and parent-concentration helpers.", TAB_SUPPLIER_YEAR),
        ("Lifetime supplier view", "One DDG supplier row carries lifetime and FY dollars plus the resolved archetype labels used by summary cuts.", TAB_DDG_PROGRAM),
    ]:
        _row(c, topic, meaning, read)
    c.blank(2)

    c.section("§2 - The four SAM attribution layers", _NCOLS)
    c.write(["These layers answer different questions and intentionally live at different grains."], styles=[S_ITALIC])
    c.blank()
    c.write(["Layer", "Question answered", "Reader guardrail"], styles=[S_HEADER_LEFT] * _NCOLS)
    for topic, meaning, read in [
        ("Archetypes", "What capability domain and output type does the supplier represent?", "UEI x Program label.  Dollars inherit the supplier label; see Archetype Application Audit, Domain Concentration and Where to Play."),
        ("Hull identification", "Can this transaction be pinned to a specific DDG hull?", "A/B rows assign a hull; C/D stay family-level; X stays conflict / multi-hull.  Read coverage before hull spend."),
        ("SWBS application", "Which ship-system does the transaction support?", "Transaction-level and HII-Ingalls only.  GD-BIW is not SWBS-classified; U00 is unmapped HII evidence."),
        ("Lifecycle timing", "Where did the purchase fall in the build timeline?", "A/B rows are stage-tagged.  C/D rows are timing-narrowed to candidate sets; dollars are never split across hulls."),
    ]:
        _row(c, topic, meaning, read)
    c.blank(2)

    c.section("§3 - Recommended read order for SAM", _NCOLS)
    c.write(["Start with coverage pages, then drill into the detailed cut.  The coverage pages prevent over-reading partial classifications."], styles=[S_ITALIC])
    c.blank()
    c.write(["Question", "Start here", "Then drill into"], styles=[S_HEADER_LEFT] * _NCOLS)
    for question, start, drill in [
        ("How are supplier archetypes applied?", TAB_ARCHETYPE_AUDIT, f"{TAB_DOMAIN_CONC}; {TAB_WHERE_TO_PLAY}; {TAB_DDG_PROGRAM}"),
        ("Which subawards can be tied to a hull?", TAB_HULL_COVERAGE, f"{TAB_HULL_SPEND}; {TAB_VENDOR_HULL}"),
        ("Where does ship-system / SWBS evidence apply?", TAB_SWBS_COVERAGE, f"{TAB_SWBS_ROLLUP}; {TAB_HULL_SWBS}; {TAB_VENDOR_HULL_SWBS}"),
        ("Where do subawards fall in the DDG lifecycle?", TAB_CD_LC_COVERAGE, f"{TAB_HULL_LIFECYCLE}; {TAB_CD_LC_ROLLUP}; {TAB_CD_LC_CANDIDATES}"),
        ("How does observed SAM bridge to the TAM denominator?", TAB_DDG_TAM, "Executive Summary; TAM-to-SAM bridge section"),
        ("Did the workbook reconcile after edits?", TAB_CHECKS, "SAM QA rows and master check"),
    ]:
        _row(c, question, start, drill)

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


SAM_CALCULATION_MAP = SheetEntry(TAB_SAM_CALC_MAP, _GROUP, _render)
