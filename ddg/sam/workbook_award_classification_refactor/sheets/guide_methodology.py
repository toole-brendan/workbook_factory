"""guide_methodology - the "Methodology" tab (guide group; one module = one sheet).

Scope, the classification axes, the assignment rule, the inputs, and the activity /
continuity definitions - the compact method a reader needs to interpret the figures.
Full code definitions live on the Taxonomy tab (the shared ``_taxonomy`` leaf); this
sheet only summarizes them, and defines the annual activity / continuity measures the
Where to Play and Supplier-Year Activity sheets report.
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
from workbook_award_classification_refactor.sheets._tabs import (
    TAB_METHODOLOGY, TAB_SUPPLIER_MASTER, TAB_NAICS_MAP,
    TAB_ARCHETYPE_OVERRIDES, TAB_PRIME_AWARDS, TAB_SWBS_CROSSWALK,
)
from workbook_award_classification_refactor.sheets._structure_classes import (
    STRUCTURE_RULES,
)

_GROUP = "guide"
_NCOLS = 2
_COLS = [34, 84]


def _kv(c: RowCursor, topic: str, detail: str) -> int:
    return c.write([topic, detail], styles=[S_BOLD, S_DEFAULT])


def _render_methodology() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_METHODOLOGY, _NCOLS)
    c.caption("Scope, classification axes, assignment rule, and inputs.")
    c.blank(2)

    # §1 Scope
    c.section("§1 - Scope", _NCOLS)
    c.write(["What's counted, at what grain, and what's deliberately excluded."],
            styles=[S_ITALIC])
    c.blank()
    _kv(c, "Unit", "The supplier operating entity (UEI), classified per program - not the "
                   "corporate parent or the subaward transaction.")
    _kv(c, "Grain", "UEI x Program: each supplier UEI is classified for the DDG-51 program.")
    _kv(c, "Included", "Hull-builder new-construction contracts, including shipbuilder-procured "
                       "non-nuclear long-lead / EOQ material.")
    _kv(c, "Excluded", "GFE / component-prime advance procurement (GE propulsion, Aegis, etc.); "
                       "and design, lead-yard, ship-alteration, and planning-yard work.")
    _kv(c, "Long-lead", "DDG long-lead is predominantly GFE, so the DDG base captures relatively "
                        "little AP / LLTM / EOQ.")
    _kv(c, "Dollars", "Subaward $ inherit the entity's labels (joined on UEI x program); NAICS "
                      "is a self-reported entity attribute, so transactions carry none of their own.")
    c.blank(2)

    # §2 Classification axes
    c.section("§2 - Classification axes", _NCOLS)
    c.write(["Two independent entity axes (one label each, with a forced catch-all) plus a "
             "transaction-level companion. Full code legend: Taxonomy tab."],
            styles=[S_ITALIC])
    c.blank()
    _kv(c, "Capability Domain (D)", "The technical ship area the entity is competent in. "
                                    "D1-D11, D0. Published.")
    _kv(c, "Primary Output (P)", "The physical form / integration level of what is delivered. "
                                 "P1-P6, P0. Published.")
    _kv(c, "Ship-System Application (SWBS)", "Which ship system a subaward supports; "
                                             "transaction-level, HII-DDG only. 100-900, X00 / L00 / U00.")
    c.blank(2)

    # §3 Assignment
    c.section("§3 - Assignment", _NCOLS)
    c.write(["How each supplier's label is chosen when sources disagree."],
            styles=[S_ITALIC])
    c.blank()
    _kv(c, "Precedence", "The curated vendor registry (hand-verified) overrides the NAICS-6 entity "
                         "default; unresolved only when neither resolves.")
    _kv(c, "Rule", "Per UEI x Program, take the most representative recurring output across the "
                   "vendor's contractual boundary, not the most sophisticated item in its portfolio. "
                   "Take the highest integration level only when items ship as one configured system.")
    _kv(c, "Output evidence", "Positive evidence only - an integration-suggestive NAICS never "
                              "auto-assigns a high-integration output.")
    c.blank(2)

    # §4 Inputs
    c.section("§4 - Inputs", _NCOLS)
    c.write(["The sheets this classification reads from."], styles=[S_ITALIC])
    c.blank()
    c.write(["Input", "Use"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for src, use in [
        (TAB_SUPPLIER_MASTER, "supplier dimension: one row per UEI x program, with primary NAICS-6"),
        (TAB_NAICS_MAP, "NAICS-6 to D / P default archetype crosswalk (the long-tail mapping)"),
        (TAB_ARCHETYPE_OVERRIDES, "hand-researched (Program, UEI) overrides of the default"),
        ("Subaward Transactions", "the subaward-dollar fact spine (DDG-51)"),
        (TAB_PRIME_AWARDS, "in-scope prime contracts (USAspending place-of-performance + obligations)"),
        (TAB_SWBS_CROSSWALK, "HII work-item code to observed SWBS group (HII-DDG only)"),
    ]:
        c.write([src, use], styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    # §5 Activity & continuity definitions
    c.section("§5 - Activity and continuity definitions", _NCOLS)
    c.write(["Exact definitions for the annual measures on Where to Play and Supplier-Year "
             "Activity. A supplier-year is one supplier (UEI) on one program in one federal "
             "fiscal year."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Active (in a FY)", "A supplier with positive spend on the program that fiscal year. "
                               "Positive Supplier $ is the larger of net spend and zero, so "
                               "deobligation-only years do not count as active.")
    _kv(c, "First observed", "Active this fiscal year with no positive spend on the program in any "
                             "earlier year - a genuinely new supplier (the start of the window can "
                             "censor this, so it is a lower bound).")
    _kv(c, "Continued", "Active this fiscal year and active the immediately preceding fiscal year.")
    _kv(c, "Reactivated", "Active this fiscal year and in some earlier year, but not the immediately "
                          "preceding one - a returning supplier.")
    _kv(c, "Incumbent vendor share", "Of this year's active suppliers, the share active the prior "
                                     "year too (a supplier-count ratio).")
    _kv(c, "Incumbent $ share", "Of this year's positive spend, the share paid to suppliers active "
                                "the prior year too (a dollar ratio).")
    _kv(c, "Retention", "Of last year's active suppliers, the share still active this year.")
    _kv(c, "Parent concentration", "Concentration after each operating UEI is collapsed to its "
                                   "standardized ultimate parent: Parent Top-1 (largest parent's "
                                   "share of positive spend), Parent HHI (sum of squared parent "
                                   "shares) and Parent Eff Firms (one over Parent HHI).")
    _kv(c, "Structure class", "Annual screen based on active-supplier count, Parent HHI, and "
                              "incumbent-dollar share - a neutral MECE label, not a market test.")
    c.blank()
    c.write(["Class", "Rule"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for label, rule in STRUCTURE_RULES:
        c.write([label, rule], styles=[S_DEFAULT, S_DEFAULT])

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


METHODOLOGY = SheetEntry(TAB_METHODOLOGY, _GROUP, _render_methodology)
