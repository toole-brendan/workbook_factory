"""taxonomy - the "Taxonomy" tab: the entity-level classification legend.

A reference / legend sheet (guide group): the code tables for the two entity
axes - Capability Domain and Primary Output - plus the transaction-level
Ship-System Application (SWBS) legend. Each axis is a section banner + a
short intro + a [code, term, definition] table.

This sheet is PURELY the legend (what each code means). How codes are assigned and
disambiguated - the assignment rule, the Domain tie-breaks, the Output boundary
tests - lives on the Methodology tab. The vocabulary lives in the ``_taxonomy`` leaf so this renderer
and ``guide_methodology`` share one source of truth; this module only lays it out.
Like Sources in the analysis workbook, the tab carries no native table.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._italic import S_ITALIC
from workbook_award_classification_refactor.sheets._tabs import TAB_TAXONOMY
from workbook_award_classification_refactor.sheets._taxonomy import (
    GRAIN_INTRO,
    DOMAIN_INTRO, DOMAINS,
    OUTPUT_INTRO, OUTPUTS,
    SWBS_INTRO, SWBS_GROUPS, SWBS_HIERARCHY_NOTE,
)

_GROUP = "guide"
_NCOLS = 3
#       B code | C term | D definition
_COLS = [8, 34, 58]


def _legend(c: RowCursor, title: str, intro: str, term_header: str,
            rows: list) -> None:
    """A §-section legend: banner + italic intro (immediately below) + a
    [Code, term, Definition] table."""
    c.section(title, _NCOLS)
    c.write([intro], styles=[S_ITALIC])
    c.blank()
    c.write(["Code", term_header, "Definition"], styles=S_HEADER_LEFT)
    for code, name, defn in rows:
        c.write([code, name, defn], styles=[S_BOLD, S_DEFAULT, S_DEFAULT])


def _make_taxonomy():
    def render() -> WorksheetSpec:
        c = RowCursor(2)
        c.title(TAB_TAXONOMY, _NCOLS)                                # row 2
        c.caption(GRAIN_INTRO)                                       # row 3 (italic)
        c.blank(2)                                                   # rows 4-5

        _legend(c, "§1 - Capability Domain Archetypes",  # banner -> row 6
                DOMAIN_INTRO, "Capability Domain", DOMAINS)
        c.blank(2)
        _legend(c, "§2 - Primary Output Archetypes",
                OUTPUT_INTRO, "Primary Output", OUTPUTS)
        c.blank(2)

        # §3 - Ship-System Application (SWBS): transaction-level, HII-DDG only
        c.section("§3 - Ship-System Application (SWBS)", _NCOLS)
        c.write([SWBS_INTRO], styles=[S_ITALIC])
        c.blank()
        c.write(["Code", "Ship-System Application", "Example subsystems / drill-down"],
                styles=S_HEADER_LEFT)
        for code, name, examples in SWBS_GROUPS:
            c.write([code, name, examples], styles=[S_BOLD, S_DEFAULT, S_DEFAULT])
        c.write([SWBS_HIERARCHY_NOTE], styles=[S_DEFAULT])

        ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                       with_gutter=True, show_outline_symbols=False)
        return WorksheetSpec(ws)

    return SheetEntry(TAB_TAXONOMY, _GROUP, render)


TAXONOMY = _make_taxonomy()
