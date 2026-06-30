"""hull_mapping_methodology - the "Hull Mapping Methodology" tab (guide group).

The compact method a reader needs to interpret the hull columns and roll-ups: the two-layer
attribution (PIID family + direct text), the confidence grades, the assignment rule (including the
conflict rule that keeps REBUY origin-hull references out of the roll-ups), the columns added to the
DDG Subaward Transactions sheet, the curated inputs, and the known limitations.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._italic import S_ITALIC
from workbook_award_classification_refactor.sheets._tabs import (
    TAB_HULL_METHODOLOGY, TAB_PIID_HULL_MAP, TAB_HULL_MASTER, TAB_DDG_TX,
    TAB_HULL_SPEND, TAB_HULL_COVERAGE, TAB_HULL_SWBS, TAB_VENDOR_HULL,
    TAB_VENDOR_HULL_SWBS, TAB_HULL_EXCEPTIONS, TAB_LIFECYCLE_METHOD,
)

_GROUP = "guide"
_NCOLS = 2
_COLS = [34, 84]


def _kv(c: RowCursor, topic: str, detail: str) -> int:
    return c.write([topic, detail], styles=[S_BOLD, S_DEFAULT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_HULL_METHODOLOGY, _NCOLS)
    c.caption("How each DDG-51 subaward is linked to a hull, and how confident that link is.")
    c.blank(2)

    # §1 Two-layer approach
    c.section("§1 - Two-layer attribution", _NCOLS)
    c.write(["Hull mapping is feasible but only partially exact; it is confidence-scored, never a "
             "forced one-row-one-hull assignment."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Layer A - PIID family", "Every subaward's Prime PIID resolves to the hull family that "
                                    "contract builds (the curated PIID-to-Hull map). Narrows the "
                                    "hull set; rarely names the exact hull on its own.")
    _kv(c, "Layer B - direct text", "DDG NNN hulls are scanned out of the Subaward Number / "
                                    "Description (the strongest evidence) and, separately, the "
                                    "prime Description of Requirement (weaker).")
    c.blank(2)

    # §2 Confidence grades
    c.section("§2 - Confidence grades", _NCOLS)
    c.write(["The grade on each transaction (Hull Confidence). Only A and B populate Assigned Hull "
             "and roll up to a hull."], styles=[S_ITALIC])
    c.blank()
    c.write(["Grade", "Meaning"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for g, m in [
        ("A", "Official exact - a single-ship PIID assigns every row to its one hull."),
        ("B", "Direct subaward text names one hull, and that hull is in the PIID family."),
        ("C", "A hull appears only in the prime requirement text - kept family-level, not exact."),
        ("D", "No hull text; the PIID family is the only evidence."),
        ("X", "Conflict (a direct hull outside the PIID family) or a multi-hull row - not assigned."),
    ]:
        c.write([g, m], styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    # §3 Assignment rule
    c.section("§3 - Assignment rule", _NCOLS)
    c.write(["When Assigned Hull is populated, and why conflicts are held out."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Exact where possible", "Assign a hull only for one clear in-family direct hull (B) or a "
                                   "single-ship PIID (A). Family-level where necessary; unassigned "
                                   "otherwise. Never force a hull.")
    _kv(c, "Conflict rule", "A direct hull outside its PIID family is a conflict (X), left "
                            "unassigned. These are almost all REBUY orders that cite a part's "
                            "ORIGIN hull (e.g. a part first bought for DDG 119, re-bought under the "
                            "DDG 128-and-follow MYP) - not the ship being built.")
    _kv(c, "Multi-hull stays multi", "A row naming several hulls is not split or forced to one; it "
                                     "is held out of the exact-hull roll-ups (X).")
    c.blank(2)

    # §4 Columns
    c.section("§4 - Columns on the transactions sheet", _NCOLS)
    c.write([f"Added to '{TAB_DDG_TX}'. The regex hull evidence is generated on rebuild; the "
             "classification is a LIVE formula off the PIID-to-Hull map, so editing that map updates "
             "the transaction sheet and every roll-up."], styles=[S_ITALIC])
    c.blank()
    for col, use in [
        ("Direct Hull Text / Count", "hulls in the subaward number / description (generated)"),
        ("Prime Requirement Hull Text / Count", "hulls in the prime requirement description (generated)"),
        ("PIID Candidate Hulls", "the hull family from the Prime PIID (live formula off the map)"),
        ("Assigned Hull", "the single hull assigned, grades A / B only, else blank (live)"),
        ("Hull Assignment Scope", "Exact hull / PIID family / Multi-hull / Conflict / Unassigned (live)"),
        ("Hull Assignment Basis", "which evidence drove the assignment (live)"),
        ("Hull Confidence", "the A / B / C / D / X grade above (live)"),
    ]:
        c.write([col, use], styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    # §5 Inputs & outputs
    c.section("§5 - Inputs and roll-ups", _NCOLS)
    c.write(["The curated sources this layer reads, and the views built on it."], styles=[S_ITALIC])
    c.blank()
    c.write(["Sheet", "Role"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for src, use in [
        (TAB_PIID_HULL_MAP, "curated PIID-to-hull family; the single source of truth for hull data"),
        (TAB_HULL_MASTER, "one row per hull: builder, PIID, block / MYP, Flight, award FY"),
        (TAB_HULL_SPEND, "assigned subaward $ per hull"),
        (TAB_HULL_COVERAGE, "exact vs inferred vs conflict $ across the whole DDG universe"),
        (TAB_HULL_SWBS, "HII hulls x SWBS ship-system"),
        (TAB_VENDOR_HULL, "vendor x assigned hull exposure"),
        (TAB_VENDOR_HULL_SWBS, "vendor x assigned hull x SWBS subsystem (HII)"),
        (TAB_HULL_EXCEPTIONS, "the conflict / multi-hull review queue"),
    ]:
        c.write([src, use], styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    # §6 Limitations
    c.section("§6 - Limitations", _NCOLS)
    c.write(["What the source data cannot prove."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Family-level dominates", "Most DDG subaward $ is attributable only to a PIID hull family "
                                     "(C / D), not an exact hull - see Hull Coverage.")
    _kv(c, "Multi-hull material", "A multi-hull buy, class-standard equipment, spares, or repair "
                                  "parts may legitimately span hulls; it is not forced onto one.")
    _kv(c, "Lifecycle layer", f"Purchase timing vs each hull's build schedule now stage-tags every "
                              f"exact-hull subaward and narrows the family-level (C/D) candidates - "
                              f"see '{TAB_LIFECYCLE_METHOD}'.")
    _kv(c, "No physical module", "Subaward text supports hull / SWBS / vendor / timing, not the HII "
                                 "physical module / grand block / structural unit.")

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


HULL_MAPPING_METHODOLOGY = SheetEntry(TAB_HULL_METHODOLOGY, _GROUP, _render)
