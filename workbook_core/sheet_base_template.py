"""<Sheet Name> - ONE-SENTENCE INTENT: the question this sheet answers.

Style + structure rules: workbook_core/sheet_guide.md. Copy-from builders
(section block, input table, cross-sheet link, FY series, native table, defined
names, QA row): workbook_core/sheet_snippets.md - worked references you may draw
on, not a required toolkit. Raw SpreadsheetML mechanics:
infra/ooxml_reference/ooxml_cheat_sheet_xlsx.md. Emitted-cell truth: workbook_<prog>/reports/
sheet_probe/<name>. To use: copy to workbook_<project>/sheets/<name>.py, set the
metadata + INTENT/LAYOUT, build _build_rows(), then add the module to
sheets/__init__.py SHEETS (in tab order). DDG uses this one-module-per-tab style.

Consolidated alternative (see workbook_submarines): several sheets may instead live in one
group file (e.g. tam_sheets.py) and be registered as tables.SheetEntry(tab_name,
group, render) objects in SHEETS rather than as modules - package_workbook accepts
both, and one file may emit several tabs (each section built at a runtime base row).

Self-contained: imports come straight from workbook_core (primitives / styles /
tables). The per-program lib.py binds the output path, the extracted-data dir,
the docProps identity, and the dash setting; this module only renders rows.

Human-output rule: INTENT and LAYOUT are source-only authoring notes - do NOT emit
them into the worksheet. Visible worksheet text should read like a human-built Excel
model: short tab name, short title banner, compact section labels, no README/Guide/
Instructions tab unless explicitly requested. See sheet_guide.md "Human workbook
standard".

INTENT
    [What is this sheet for? One short paragraph naming the question the sheet
    answers and what downstream consumers read from it - by purpose (an inputs
    surface, a calc, a deck-facing contract, a checks tab, a sources list). Be
    specific about which cells other sheets link to.]

LAYOUT
    [Top-to-bottom section map; name each section, its row range, and what it
    holds. Lock it here so the structure is reviewable without reading the body.
    e.g.
        row 2      : title banner
        row 4-12   : section banner + 8-row inputs table
        row 14-20  : section banner + derived block]
"""
from __future__ import annotations

from workbook_core.primitives import (
    worksheet, banner_row, write_row, build_table, col_letter, cref,
    sheet_ref, qsheet,
)
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_TOTAL,
    S_NUM, S_NUM_INPUT, S_NUM_TOTAL,
    S_PCT, S_PCT_INPUT, S_PCT_TOTAL,
    S_LINK_NUM, S_LINK_PCT,
    S_LABEL_INDENT_1, S_LABEL_INDENT_2, S_HEADER_CENTER,
    S_TITLE_SHEET, S_TITLE_SECTION, S_TITLE_SUBSECTION,
)
from workbook_core.tables import WorksheetSpec
from workbook_core.groups import group_color

# ── Sheet metadata (the packager reads TAB_NAME + SHEET_GROUP; the rest is local) ──
TAB_NAME = None                 # None -> tab name derived from this filename (Title Case)
SHEET_GROUP = "data"            # logical chapter -> tab color + tab-block order;
TAB_COLOR = group_color(SHEET_GROUP)   #   one of groups.SHEET_GROUPS (see sheet_guide.md)
COLS = [44, 14, 14, 14, 14, 12, 30]   # content widths, col B onward (gutter is auto)
WITH_GUTTER = True              # column A gutter + auto-blank row 1 (workbook standard)


def _tab_name() -> str:
    """Display name for the title banner: TAB_NAME, else the filename in Title Case.

    Matches how the packager derives the worksheet name, so the row-2 banner and
    the actual tab stay in sync without hand-editing a literal.
    """
    return TAB_NAME or __name__.rsplit(".", 1)[-1].replace("_", " ").title()


# ════════════════════════════════════════════════════════════════════════════
# BUILD YOUR SHEET BODY HERE
# ════════════════════════════════════════════════════════════════════════════
# Compose rows top-to-bottom into the list. Row 1 is the auto-injected gutter
# blank (do not emit it); start content at row 2. Content begins at column B
# (start_col=1) - column A is the gutter. Every style argument is required; pick
# styles by cell purpose from the S_* cheat sheet in sheet_guide.md.
#
# Paste section / table / cross-sheet / FY / native-table / QA builders from
# sheet_snippets.md as needed. If this sheet exposes load-bearing cells to other
# sheets, add accessor functions at the bottom (see snippets -> cross-sheet link).
def _build_rows() -> list[str]:
    rows: list[str] = []

    # Title banner (row 2) - derives from TAB_NAME / filename; do not hard-code.
    # Keep it short: it should read like the tab label, not a sentence.
    rows.append(banner_row(2, _tab_name(), n_cols=len(COLS),
                           style=S_TITLE_SHEET, with_gutter=WITH_GUTTER))

    # Section blocks go here: banner_row(S_TITLE_SECTION) + write_row/build_table.
    # Title section banners "§N - <short label>" (sub-sections "§Na - ..."); see
    # sheet_guide.md "Section numbering". Spacing: see "Row spacing rhythm".

    return rows


def render() -> WorksheetSpec:
    """Render this sheet. Wrap the worksheet XML in a WorksheetSpec.

    Add native tables / defined names to the spec when the sheet needs them:
        return WorksheetSpec(ws, tables=[...], defined_names={...})
    See sheet_snippets.md -> native Excel table / defined names.

    Native tables default to the core named no-format table style; attach an
    ExcelTable only for flat, filterable data / source / lookup / output-contract
    ranges, not for model or row-hierarchy blocks (use build_table for those).
    """
    ws = worksheet(
        _build_rows(),
        cols=COLS,
        tab_color=TAB_COLOR,
        with_gutter=WITH_GUTTER,
    )
    return WorksheetSpec(ws)
