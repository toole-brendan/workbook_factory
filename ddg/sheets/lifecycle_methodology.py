"""lifecycle_methodology - the "Lifecycle Methodology" tab (guide group).

How purchase TIMING is used: to stage-tag each subaward (which build phase it supported) and, for
the family-level C/D rows, to NARROW the candidate hull set to the ships in build at that date. The
sibling of Hull Mapping Methodology - that one answers WHICH HULL, this one answers WHICH STAGE and
HOW FAR timing narrows. It states the four stages and their windows, the two confidence axes, and -
the load-bearing discipline - the wall between evidence-based narrowing and modeled allocation.
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import S_DEFAULT, S_BOLD, S_HEADER_LEFT
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._italic import S_ITALIC
from workbook_award_classification_refactor.sheets._tabs import (
    TAB_LIFECYCLE_METHOD, TAB_HULL_MASTER, TAB_DDG_TX, TAB_HULL_LIFECYCLE,
    TAB_CD_LC_COVERAGE, TAB_CD_LC_ROLLUP, TAB_CD_LC_CANDIDATES, TAB_HULL_METHODOLOGY,
)

_GROUP = "guide"
_NCOLS = 2
_COLS = [34, 84]


def _kv(c: RowCursor, topic: str, detail: str) -> int:
    return c.write([topic, detail], styles=[S_BOLD, S_DEFAULT])


def _render() -> WorksheetSpec:
    c = RowCursor(2)
    c.title(TAB_LIFECYCLE_METHOD, _NCOLS)
    c.caption("Using when each subaward was made, vs when each ship was built, to stage-tag it and "
              "narrow the family-level candidates - without ever forcing one hull or splitting a dollar.")
    c.blank(2)

    # §1 Two axes
    c.section("§1 - What timing adds", _NCOLS)
    c.write([f"Built on the milestone dates curated on '{TAB_HULL_MASTER}'. The hull identity itself "
             f"is the separate A/B/C/D/X layer - see '{TAB_HULL_METHODOLOGY}'."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Stage tagging (A/B + C/D)", "Compare the purchase date to the hull's build schedule to "
                                        "label which construction STAGE it supported.")
    _kv(c, "Narrowing (C/D only)", "For a family-level row, keep only the hulls actually in build at "
                                   "the purchase date - shrinking 5-7 candidates toward 1-3. The set "
                                   "is narrowed, never collapsed to one hull.")
    c.blank(2)

    # §2 Stages + windows
    c.section("§2 - The four construction stages", _NCOLS)
    c.write(["Windows from Start Fabrication / Launch / Delivery. Launch is unknown for hulls not yet "
             "launched, so their in-build spend reads as Construction (no Outfit split yet)."],
            styles=[S_ITALIC])
    c.blank()
    c.write(["Stage", "Window (vs the hull's schedule)"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for s, w in [
        ("Long-lead", "Before start of fabrication - advance / long-lead material."),
        ("Construction", "Start of fabrication to launch (or to delivery if not yet launched)."),
        ("Outfit / test", "Launch to delivery - post-launch outfitting, test, activation."),
        ("Post-delivery", "After delivery to the Navy - outside the core build (not a timing match)."),
    ]:
        c.write([s, w], styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    # §3 Two confidence axes
    c.section("§3 - Two confidence axes (separate from hull confidence)", _NCOLS)
    c.write(["Lifecycle confidence is its OWN grade; it never upgrades the A/B/C/D/X hull grade, and "
             "a C/D row's Assigned Hull stays blank."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Date Source Confidence", "Actual (delivered / launched, published) / Projected (future "
                                     "schedule) / Estimated. A projected window caps the lifecycle "
                                     "confidence below.")
    _kv(c, "Lifecycle Confidence", "High = one hull, in active construction, on actual dates. "
                                   "Medium = 2-3 hulls, or one on long-lead / projected dates. "
                                   "Low = 4+ hulls (little narrowing). Flagged = no window match / no "
                                   "schedule data.")
    c.blank(2)

    # §4 Narrowing results
    c.section("§4 - Narrowing results (C/D)", _NCOLS)
    c.write([f"The per-transaction verdict on '{TAB_CD_LC_ROLLUP}'; the $ split is on "
             f"'{TAB_CD_LC_COVERAGE}'."], styles=[S_ITALIC])
    c.blank()
    for r, m in [
        ("Single candidate", "Timing narrows the family to one hull (not an assignment - a candidate)."),
        ("2-3 candidates", "Narrowed to 2-3 hulls in build at the time."),
        ("Still family-level", "4+ hulls still plausible - the common case; timing barely narrows."),
        ("Exception (no window match)", "Date outside every candidate hull's window (spares / repair / "
                                        "class-wide / mis-dated) - surfaced for review."),
        ("No schedule data", "No hull in the family carries milestone dates yet."),
    ]:
        c.write([r, m], styles=[S_BOLD, S_DEFAULT])
    c.blank(2)

    # §5 The wall
    c.section("§5 - Attribution vs allocation (the wall)", _NCOLS)
    c.write(["The load-bearing discipline - why these sheets carry no per-hull dollar."],
            styles=[S_ITALIC])
    c.blank()
    _kv(c, "Narrowing is attribution", "Keeping only the hulls physically in build is evidence - the "
                                       "defensible win. Each rollup row says so: 'Evidence-based "
                                       "narrowing, not modeled allocation'.")
    _kv(c, "Splitting $ is allocation", "Dividing a family dollar across candidate hulls by a formula "
                                        "is a modeling assumption, not evidence. It is NOT done here; "
                                        "if ever needed it must live in a separate, labelled modeled view.")
    c.blank(2)

    # §6 Sheets
    c.section("§6 - Where the lifecycle layer lives", _NCOLS)
    c.write(["The views built on the timing analysis."], styles=[S_ITALIC])
    c.blank()
    c.write(["Sheet", "Role"], styles=[S_HEADER_LEFT, S_HEADER_LEFT])
    for src, use in [
        (TAB_HULL_MASTER, "the curated Start Fabrication / Launch / Delivery + Schedule Confidence"),
        (TAB_DDG_TX, "per-row Lifecycle Stage (A/B) and Narrowing Result / Lifecycle Confidence (C/D)"),
        (TAB_HULL_LIFECYCLE, "exact (A/B) subaward $ split by build stage, per hull"),
        (TAB_CD_LC_COVERAGE, "family-level (C/D) $ by narrowing result and by lifecycle confidence"),
        (TAB_CD_LC_ROLLUP, "one row per C/D transaction: the narrowed candidate set + verdict"),
        (TAB_CD_LC_CANDIDATES, "one row per C/D transaction x candidate hull (kept and excluded)"),
    ]:
        c.write([src, use], styles=[S_DEFAULT, S_DEFAULT])
    c.blank(2)

    # §7 Limitations
    c.section("§7 - Limitations", _NCOLS)
    c.write(["What timing can and cannot do."], styles=[S_ITALIC])
    c.blank()
    _kv(c, "Long-lead is the confounder", "Material for a later ship is often bought while an earlier "
                                          "ship is in build, so timing narrows but never PROVES the "
                                          "hull - long-lead hulls are kept as candidates at low confidence.")
    _kv(c, "Most $ stays family-level", "Long, overlapping construction windows (and missing launch "
                                        "dates for newer hulls) leave most C/D $ at 4+ candidates.")
    _kv(c, "Projected dates", "Newer hulls depend on projected milestones, which cap lifecycle "
                              "confidence until real dates are published.")

    ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                   with_gutter=True, show_outline_symbols=False)
    return WorksheetSpec(ws)


LIFECYCLE_METHODOLOGY = SheetEntry(TAB_LIFECYCLE_METHOD, _GROUP, _render)
