"""Centralized styling for the shared workbook engine.

Slim style set:

  - Arial 8pt everywhere.
  - Font color applies to NUMERIC cells only. Text labels / IDs /
    scenarios stay default black regardless of edit-state.
  - Blue (#0000FF): hardcoded numeric input.
  - Black (#000000): derived numeric value (formula result).
  - Green (#008000): standalone cross-sheet link to a numeric cell.
    Apply explicitly when writing the row - there is no auto-detection.
  - Gray italic (#808080): side-note / source-citation TEXT beside an input cell
    (S_NOTE) - the one text style that carries a color.
  - Universal number formats: numbers render with commas + 1 decimal
    (#,##0.0); percentages render italic with 1 decimal (0.0%); integer
    quantities (record counts, vendor counts - things a decimal would
    misrepresent) use the S_INT* variants (#,##0). A zero value renders
    as a dash ("-") in all of them (IB convention).
  - No text wrap, no merged cells, no gridlines. (A pale-yellow fill is used
    only by the S_PASTE_* think-cell paste-range styles - see below.)
  - Dollar units ($M, $/unit, $M/yr) live in section banners, never as cell formats.
  - Universal 10.0 row height.

Adding a new style is the same 3-step process:
  1. Append color/font/fill/border/numFmt to the relevant list.
  2. Append cellXfs entry referencing the new index.
  3. Add a `S_*` constant for the new cellXfs position.
"""
from __future__ import annotations

from xml.sax.saxutils import escape as xml_escape

from workbook_core.ooxml import XML_DECL, NS_SS
from workbook_core.table_style_names import NO_FORMAT_TABLE_STYLE


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

C_TEXT       = "000000"   # pure black - body text
C_WHITE      = "FFFFFF"
C_BLACK      = "000000"
C_INPUT_FONT = "0000FF"   # blue - hardcoded numeric inputs
C_LINK_FONT  = "008000"   # green - cross-sheet links to numeric cells
C_NOTE_FONT  = "808080"   # gray - side-note / source-citation text (italic)

# Banner backgrounds
C_BG_SHEET_TITLE  = "000000"   # sheet title - black
C_BG_SECTION      = "808080"   # section title - mid gray
C_BG_SUBSECTION   = "F2F2F2"   # sub-section - light gray

# Specialty fill (think-cell paste-range only)
C_FILL_PASTE      = "FFFACD"   # pale yellow (lemon chiffon) - paste-range marker

# Tab colors are owned by workbook_core/groups.py (one color per logical group);
# a sheet sets SHEET_GROUP and derives TAB_COLOR = group_color(SHEET_GROUP). The
# C_TAB_* role constants that used to live here were retired with that change.


# Workbook font standard: Arial 8 everywhere.
FONT_NAME = "Arial"
FONT_SIZE = "8"


# ---------------------------------------------------------------------------
# Number formats (workbook-wide universal - see top docstring)
# ---------------------------------------------------------------------------

NUM_FMTS = [
    # Three sections: positive; negative; zero. A zero value renders as a
    # dash ("-") in both formats (IB convention), not "0.0" / "0.0%".
    (164, '#,##0.0;-#,##0.0;"-"'),   # 1,234.5 ; negative -1,234.5 ; zero "-"
    (165, '0.0%;-0.0%;"-"'),         # 85.0% ; negative -85.0% ; zero "-" (italic)
    # Paste-range only: $-baked formats matching the deck charts' display units.
    # These blocks are copied straight into a think-cell chart, not read as model
    # cells, so a baked unit suffix is allowed here (and only here).
    (166, '"$"#,##0"M"'),            # paste $M (zero-decimal) -> "$2,912M"
    (167, '"$"0.0"B"'),              # paste $B (one-decimal)  -> "$4.8B"
    (168, '#,##0;-#,##0;"-"'),       # integer count 1,234 ; -1,234 ; zero "-"
    (169, 'yyyy\\-mm\\-dd'),         # ISO date 2026-06-12 (real date cells, so
                                     # MINIFS/MAXIFS aggregation works)
]


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def _font(color: str, *, bold: bool = False, italic: bool = False,
          size: str = FONT_SIZE) -> str:
    bits = [f'<sz val="{size}"/>', f'<name val="{FONT_NAME}"/>']
    if bold:
        bits.append("<b/>")
    if italic:
        bits.append("<i/>")
    bits.append(f'<color rgb="FF{color}"/>')
    return f'<font>{"".join(bits)}</font>'


FONTS = [
    _font(C_TEXT),                                  # 0  black default
    _font(C_TEXT, bold=True),                       # 1  black bold
    _font(C_WHITE, bold=True),                      # 2  white bold (banner)
    _font(C_INPUT_FONT),                            # 3  blue input
    _font(C_LINK_FONT),                             # 4  green link
    _font(C_TEXT, italic=True),                     # 5  black italic (percent)
    _font(C_INPUT_FONT, italic=True),               # 6  blue italic (input percent)
    _font(C_LINK_FONT, italic=True),                # 7  green italic (link percent)
    _font(C_TEXT, bold=True, italic=True),          # 8  black bold italic (total percent)
    _font(C_NOTE_FONT, italic=True),                # 9  gray italic (side-note)
]


# ---------------------------------------------------------------------------
# Fills
# ---------------------------------------------------------------------------

FILLS = [
    '<fill><patternFill patternType="none"/></fill>',                                                          # 0  no fill
    '<fill><patternFill patternType="gray125"/></fill>',                                                       # 1  Excel default (required)
    f'<fill><patternFill patternType="solid"><fgColor rgb="FF{C_BG_SHEET_TITLE}"/></patternFill></fill>',      # 2  sheet title (black)
    f'<fill><patternFill patternType="solid"><fgColor rgb="FF{C_BG_SECTION}"/></patternFill></fill>',          # 3  section title (mid gray)
    f'<fill><patternFill patternType="solid"><fgColor rgb="FF{C_BG_SUBSECTION}"/></patternFill></fill>',       # 4  sub-section (light gray)
    f'<fill><patternFill patternType="solid"><fgColor rgb="FF{C_FILL_PASTE}"/></patternFill></fill>',          # 5  paste pale yellow (think-cell paste-range)
]


# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------

# Thin black side element (used by the paste-range perimeter borders below).
def _thin(side: str) -> str:
    return f'<{side} style="thin"><color rgb="FF{C_BLACK}"/></{side}>'


BORDERS = [
    "<border><left/><right/><top/><bottom/></border>",                              # 0  no border
    (                                                                                # 1  bottom thin black - column header underline
        "<border>"
        '<left/><right/><top/>'
        f'<bottom style="thin"><color rgb="FF{C_BLACK}"/></bottom>'
        "</border>"
    ),
    (                                                                                # 2  top medium black - total / subtotal divider
        "<border>"
        '<left/><right/>'
        f'<top style="medium"><color rgb="FF{C_BLACK}"/></top>'
        '<bottom/>'
        "</border>"
    ),
    # ----- think-cell paste-range perimeter borders (thin black) -----
    # Each marks which corner/edge of the paste rectangle a cell sits on. The
    # bottom edge ("B") reuses border 1 (bottom-thin); the interior reuses 0 (none).
    f'<border>{_thin("left")}<right/>{_thin("top")}<bottom/></border>',   # 3  TL (top+left)
    f'<border><left/><right/>{_thin("top")}<bottom/></border>',           # 4  T  (top)
    f'<border><left/>{_thin("right")}{_thin("top")}<bottom/></border>',   # 5  TR (top+right)
    f'<border>{_thin("left")}<right/><top/>{_thin("bottom")}</border>',   # 6  BL (bottom+left)
    f'<border><left/>{_thin("right")}<top/>{_thin("bottom")}</border>',   # 7  BR (bottom+right)
    f'<border>{_thin("left")}<right/><top/><bottom/></border>',           # 8  L  (left)
    f'<border><left/>{_thin("right")}<top/><bottom/></border>',           # 9  R  (right)
]


# ---------------------------------------------------------------------------
# Cell formats (cellXfs) - index = its S_* constant value below.
# All alignment blocks use NO wrap (workbook standard: no wrapped text).
# ---------------------------------------------------------------------------

CELL_XFS = [
    # 0  S_DEFAULT - black default, no fill, no border, no number format
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>',
    # 1  S_BOLD - black bold
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>',
    # 2  S_HEADER_LEFT - column header: bold black, bottom underline, left-aligned
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" '
    'applyFont="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # 3  S_TOTAL - bold black, medium top border (subtotal / total divider)
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="2" xfId="0" '
    'applyFont="1" applyBorder="1"/>',
    # 4  S_NUM - black number (1,234.5)
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>',
    # 5  S_NUM_INPUT - blue number (hardcoded)
    '<xf numFmtId="164" fontId="3" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 6  S_PCT - black italic percent (85.0%)
    '<xf numFmtId="165" fontId="5" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 7  S_PCT_INPUT - blue italic percent (hardcoded)
    '<xf numFmtId="165" fontId="6" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 8  S_TITLE_SHEET - banner: black bg, white bold, left-aligned
    '<xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" '
    'applyFont="1" applyFill="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # 9  S_TITLE_SECTION - banner: mid gray bg, white bold, left-aligned
    '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" '
    'applyFont="1" applyFill="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # 10 S_TITLE_SUBSECTION - banner: light gray bg, black bold, left-aligned
    '<xf numFmtId="0" fontId="1" fillId="4" borderId="0" xfId="0" '
    'applyFont="1" applyFill="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # ----- Green-font link variants (apply explicitly to numeric cross-sheet refs) -----
    # 11 S_LINK_NUM - green number
    '<xf numFmtId="164" fontId="4" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 12 S_LINK_PCT - green italic percent
    '<xf numFmtId="165" fontId="7" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # ----- Bordered total-row variants (top medium border + number format) -----
    # Apply across every cell of a total row so the border runs continuous.
    # 13 S_NUM_TOTAL - bold number + top border
    '<xf numFmtId="164" fontId="1" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 14 S_PCT_TOTAL - bold italic percent + top border
    '<xf numFmtId="165" fontId="8" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 15 S_NUM_INPUT_TOTAL - blue number + top border (hardcoded values in total rows)
    '<xf numFmtId="164" fontId="3" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Filler / remaining bordered total-row variants -----
    # The top medium border draws per-cell, so every cell of a total row needs a
    # bordered style or the divider line breaks. These complete the set so any
    # cell type (incl. an empty spacer) can carry the line; total_row() upgrades
    # base styles to these automatically.
    # 16 S_BORDER_TOP - plain cell, top border only (empty spacer cells in a total row)
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="2" xfId="0" applyBorder="1"/>',
    # 17 S_PCT_INPUT_TOTAL - blue italic percent + top border
    '<xf numFmtId="165" fontId="6" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 18 S_LINK_NUM_TOTAL - green number + top border
    '<xf numFmtId="164" fontId="4" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 19 S_LINK_PCT_TOTAL - green italic percent + top border
    '<xf numFmtId="165" fontId="7" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Indented labels + alternate header alignment -----
    # Indented labels are plain black labels (like S_DEFAULT) nudged right one/two
    # indent steps, for a parent->child styled-range model block (the components
    # under a line item). This is *visual* indentation only - it is independent of
    # row outlineLevel (the collapsible-group feature). No total variants: an
    # indented subtotal is rare and the convention keeps totals flush-left
    # (S_BOLD/S_TOTAL), so total_row() intentionally has no mapping for these.
    # 20 S_LABEL_INDENT_1 - black label, indent 1 (a direct component row)
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center" indent="1"/></xf>',
    # 21 S_LABEL_INDENT_2 - black label, indent 2 (a rare nested component)
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center" indent="2"/></xf>',
    # 22 S_HEADER_CENTER - column header: bold black, bottom underline, centered
    # (FY / numeric column headers; text-label headers stay S_HEADER_LEFT)
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" '
    'applyFont="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
    # ----- think-cell paste-range markers (ChartData / z_ChartData) -----
    # Pale-yellow fill (5) + thin-black perimeter, so each chart block reads as a
    # clean copy-paste rectangle. The position suffix (_TL/_T/_TR/_BL/_B/_BR/_L/_R/
    # _INT) selects the perimeter border; the unit suffix (_M $M / _B $B / _P %)
    # selects the number format. Values are black-on-yellow (NOT the green link
    # font) - these cells are pasted into a deck chart, not read as model cells.
    # Headers (text, bold, centered):
    # 23 S_PASTE_HEADER_TL - top-left corner
    '<xf numFmtId="0" fontId="1" fillId="5" borderId="3" xfId="0" '
    'applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
    # 24 S_PASTE_HEADER_T - top edge
    '<xf numFmtId="0" fontId="1" fillId="5" borderId="4" xfId="0" '
    'applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
    # 25 S_PASTE_HEADER_TR - top-right corner
    '<xf numFmtId="0" fontId="1" fillId="5" borderId="5" xfId="0" '
    'applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
    # Row labels (text, plain, left) - the first column of a matrix block:
    # 26 S_PASTE_LABEL_L - left edge (matrix middle rows)
    '<xf numFmtId="0" fontId="0" fillId="5" borderId="8" xfId="0" '
    'applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # 27 S_PASTE_LABEL_BL - bottom-left corner (last matrix row)
    '<xf numFmtId="0" fontId="0" fillId="5" borderId="6" xfId="0" '
    'applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # Value cells, $M (numFmt 166):
    # 28 S_PASTE_VAL_BL_M
    '<xf numFmtId="166" fontId="0" fillId="5" borderId="6" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 29 S_PASTE_VAL_B_M
    '<xf numFmtId="166" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 30 S_PASTE_VAL_BR_M
    '<xf numFmtId="166" fontId="0" fillId="5" borderId="7" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 31 S_PASTE_VAL_R_M
    '<xf numFmtId="166" fontId="0" fillId="5" borderId="9" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 32 S_PASTE_VAL_INT_M
    '<xf numFmtId="166" fontId="0" fillId="5" borderId="0" xfId="0" applyNumberFormat="1" applyFill="1"/>',
    # Value cells, $B (numFmt 167):
    # 33 S_PASTE_VAL_BL_B
    '<xf numFmtId="167" fontId="0" fillId="5" borderId="6" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 34 S_PASTE_VAL_B_B
    '<xf numFmtId="167" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 35 S_PASTE_VAL_BR_B
    '<xf numFmtId="167" fontId="0" fillId="5" borderId="7" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 36 S_PASTE_VAL_R_B
    '<xf numFmtId="167" fontId="0" fillId="5" borderId="9" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 37 S_PASTE_VAL_INT_B
    '<xf numFmtId="167" fontId="0" fillId="5" borderId="0" xfId="0" applyNumberFormat="1" applyFill="1"/>',
    # Value cells, percent (numFmt 165; black non-italic on yellow):
    # 38 S_PASTE_VAL_BL_P
    '<xf numFmtId="165" fontId="0" fillId="5" borderId="6" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 39 S_PASTE_VAL_B_P
    '<xf numFmtId="165" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 40 S_PASTE_VAL_BR_P
    '<xf numFmtId="165" fontId="0" fillId="5" borderId="7" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 41 S_PASTE_VAL_R_P
    '<xf numFmtId="165" fontId="0" fillId="5" borderId="9" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>',
    # 42 S_PASTE_VAL_INT_P
    '<xf numFmtId="165" fontId="0" fillId="5" borderId="0" xfId="0" applyNumberFormat="1" applyFill="1"/>',
    # 43 S_NOTE - gray italic side-note text (source / citation beside an input cell)
    '<xf numFmtId="0" fontId="9" fillId="0" borderId="0" xfId="0" '
    'applyFont="1" applyAlignment="1">'
    '<alignment horizontal="left" vertical="center"/></xf>',
    # ----- Integer-count variants (numFmt 168: #,##0, zero as dash) -----
    # For quantities where a decimal would misrepresent the value (record
    # counts, vendor counts, PIID footprints). Same color roles as S_NUM*.
    # 44 S_INT - black integer (derived/formula count)
    '<xf numFmtId="168" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>',
    # 45 S_INT_INPUT - blue integer (hardcoded count)
    '<xf numFmtId="168" fontId="3" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 46 S_LINK_INT - green integer (cross-sheet link to a count cell)
    '<xf numFmtId="168" fontId="4" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 47 S_INT_TOTAL - bold integer + top border
    '<xf numFmtId="168" fontId="1" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 48 S_INT_INPUT_TOTAL - blue integer + top border
    '<xf numFmtId="168" fontId="3" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 49 S_LINK_INT_TOTAL - green integer + top border
    '<xf numFmtId="168" fontId="4" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Date variants (numFmt 169: yyyy-mm-dd, real date serials) -----
    # 50 S_DATE_INPUT - blue date (hardcoded date serial)
    '<xf numFmtId="169" fontId="3" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 51 S_DATE_INPUT_TOTAL - blue date + top border
    '<xf numFmtId="169" fontId="3" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 52 S_DATE_LINK - green date (cross-sheet link to a date cell)
    '<xf numFmtId="169" fontId="4" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1" applyFont="1"/>',
    # 53 S_DATE_LINK_TOTAL - green date + top border
    '<xf numFmtId="169" fontId="4" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Derived date variants (numFmt 169; black font - a formula result,
    # not a cross-sheet link). Use for MAXIFS/last-award + computed next-date
    # cells; the green S_DATE_LINK stays for pure cross-sheet date refs only.
    # 54 S_DATE - black date (derived/formula date)
    '<xf numFmtId="169" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>',
    # 55 S_DATE_TOTAL - bold date + top border
    '<xf numFmtId="169" fontId="1" fillId="0" borderId="2" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Vertical-fence percent variants (matrix block left/right edges) -----
    # Black italic percent (like S_PCT) plus one thin vertical border, used to fence
    # each program block in the exec-summary mix matrices: a left border on the block's
    # first FY column, a right border on its last. borderId 8 = left, 9 = right.
    # 56 S_PCT_LEFT - black italic percent + left border
    '<xf numFmtId="165" fontId="5" fillId="0" borderId="8" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # 57 S_PCT_RIGHT - black italic percent + right border
    '<xf numFmtId="165" fontId="5" fillId="0" borderId="9" xfId="0" '
    'applyNumberFormat="1" applyFont="1" applyBorder="1"/>',
    # ----- Centered column headers carrying a vertical block fence -----
    # Like S_HEADER_CENTER (bold, centered, bottom underline) but with one vertical
    # border so a matrix block's left/right fence runs up into the FY header row.
    # borderId 6 = bottom+left, 7 = bottom+right (reused from the paste-range set).
    # 58 S_HEADER_CENTER_LEFT - centered header + bottom underline + left fence
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="6" xfId="0" '
    'applyFont="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
    # 59 S_HEADER_CENTER_RIGHT - centered header + bottom underline + right fence
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="7" xfId="0" '
    'applyFont="1" applyBorder="1" applyAlignment="1">'
    '<alignment horizontal="center" vertical="center"/></xf>',
]


# ---------------------------------------------------------------------------
# S_* constants - keep indices in sync with CELL_XFS positions above.
# ---------------------------------------------------------------------------

S_DEFAULT          = 0
S_BOLD             = 1
S_HEADER_LEFT      = 2
S_TOTAL            = 3
S_NUM              = 4
S_NUM_INPUT        = 5
S_PCT              = 6
S_PCT_INPUT        = 7
S_TITLE_SHEET      = 8
S_TITLE_SECTION    = 9
S_TITLE_SUBSECTION = 10
S_LINK_NUM         = 11
S_LINK_PCT         = 12
S_NUM_TOTAL        = 13
S_PCT_TOTAL        = 14
S_NUM_INPUT_TOTAL  = 15
S_BORDER_TOP       = 16
S_PCT_INPUT_TOTAL  = 17
S_LINK_NUM_TOTAL   = 18
S_LINK_PCT_TOTAL   = 19
S_LABEL_INDENT_1   = 20
S_LABEL_INDENT_2   = 21
S_HEADER_CENTER    = 22

# think-cell paste-range markers (z_ChartData). Position suffix selects the
# perimeter border; unit suffix selects the number format (_M $M / _B $B / _P %).
S_PASTE_HEADER_TL  = 23
S_PASTE_HEADER_T   = 24
S_PASTE_HEADER_TR  = 25
S_PASTE_LABEL_L    = 26
S_PASTE_LABEL_BL   = 27
S_PASTE_VAL_BL_M   = 28
S_PASTE_VAL_B_M    = 29
S_PASTE_VAL_BR_M   = 30
S_PASTE_VAL_R_M    = 31
S_PASTE_VAL_INT_M  = 32
S_PASTE_VAL_BL_B   = 33
S_PASTE_VAL_B_B    = 34
S_PASTE_VAL_BR_B   = 35
S_PASTE_VAL_R_B    = 36
S_PASTE_VAL_INT_B  = 37
S_PASTE_VAL_BL_P   = 38
S_PASTE_VAL_B_P    = 39
S_PASTE_VAL_BR_P   = 40
S_PASTE_VAL_R_P    = 41
S_PASTE_VAL_INT_P  = 42

# Gray italic side-note text (source / citation annotations beside input cells).
S_NOTE             = 43

# Integer-count variants (record/vendor counts - no decimal).
S_INT              = 44
S_INT_INPUT        = 45
S_LINK_INT         = 46
S_INT_TOTAL        = 47
S_INT_INPUT_TOTAL  = 48
S_LINK_INT_TOTAL   = 49
S_DATE_INPUT       = 50
S_DATE_INPUT_TOTAL = 51
S_DATE_LINK        = 52
S_DATE_LINK_TOTAL  = 53
S_DATE             = 54   # black derived date (formula result)
S_DATE_TOTAL       = 55

# Vertical-fence percent variants (matrix block left/right edges).
S_PCT_LEFT         = 56
S_PCT_RIGHT        = 57
# Centered headers carrying a vertical block fence (left/right edge of a matrix block).
S_HEADER_CENTER_LEFT  = 58
S_HEADER_CENTER_RIGHT = 59


# Base style -> its top-bordered total-row variant. total_row() (primitives.py)
# upgrades every cell of a total row through this map so the divider border runs
# continuously across the whole row (a bare S_BOLD label or S_DEFAULT spacer would
# otherwise leave a gap). Already-bordered styles map to themselves.
BORDER_TOP_FOR = {
    S_DEFAULT:          S_BORDER_TOP,
    S_BOLD:             S_TOTAL,
    S_HEADER_LEFT:      S_TOTAL,
    S_NUM:              S_NUM_TOTAL,
    S_NUM_INPUT:        S_NUM_INPUT_TOTAL,
    S_PCT:              S_PCT_TOTAL,
    S_PCT_INPUT:        S_PCT_INPUT_TOTAL,
    S_LINK_NUM:         S_LINK_NUM_TOTAL,
    S_LINK_PCT:         S_LINK_PCT_TOTAL,
    S_INT:              S_INT_TOTAL,
    S_INT_INPUT:        S_INT_INPUT_TOTAL,
    S_LINK_INT:         S_LINK_INT_TOTAL,
    S_DATE_INPUT:       S_DATE_INPUT_TOTAL,
    S_DATE_LINK:        S_DATE_LINK_TOTAL,
    S_DATE:             S_DATE_TOTAL,
    # already-bordered -> identity (idempotent)
    S_TOTAL:            S_TOTAL,
    S_NUM_TOTAL:        S_NUM_TOTAL,
    S_PCT_TOTAL:        S_PCT_TOTAL,
    S_NUM_INPUT_TOTAL:  S_NUM_INPUT_TOTAL,
    S_BORDER_TOP:       S_BORDER_TOP,
    S_PCT_INPUT_TOTAL:  S_PCT_INPUT_TOTAL,
    S_LINK_NUM_TOTAL:   S_LINK_NUM_TOTAL,
    S_LINK_PCT_TOTAL:   S_LINK_PCT_TOTAL,
    S_INT_TOTAL:        S_INT_TOTAL,
    S_INT_INPUT_TOTAL:  S_INT_INPUT_TOTAL,
    S_LINK_INT_TOTAL:   S_LINK_INT_TOTAL,
    S_DATE_INPUT_TOTAL: S_DATE_INPUT_TOTAL,
    S_DATE_LINK_TOTAL:  S_DATE_LINK_TOTAL,
    S_DATE_TOTAL:       S_DATE_TOTAL,
}


# ---------------------------------------------------------------------------
# Native-table style catalog: one named no-format table style
# ---------------------------------------------------------------------------
# Every ExcelTable references this style by default (tables.DEFAULT_TABLE_STYLE =
# NO_FORMAT_TABLE_STYLE). It points all of its table-style element slots at a single
# EMPTY differential format (dxfId=0), so it contributes no fill / border / font /
# stripe — the cell-level S_* styles remain the only visible formatting — while
# still being a durable named style Excel preserves on open/save (a style-less
# table can get a banded default re-injected; see table_style_names.py).

# dxfId=0: intentionally empty (no font/fill/border/numFmt). RESERVED for the
# no-format table style — any conditional-formatting dxf appends AFTER it (dxfId=1, 2, …).
def _dxf_bgfill(rgb: str) -> str:
    """A differential format that sets only a solid background fill — for conditional-
    formatting highlights. bgColor is the fill Excel paints on a matching cell."""
    return f'<dxf><fill><patternFill><bgColor rgb="{rgb}"/></patternFill></fill></dxf>'


DXFS = [
    "<dxf/>",                       # dxfId=0 - reserved empty (no-format table style)
    _dxf_bgfill("FFF4CCCC"),        # dxfId=1 DXF_ANOMALY  - light red
    _dxf_bgfill("FFFFF2CC"),        # dxfId=2 DXF_IMMINENT - light amber
    _dxf_bgfill("FFFCE4D6"),        # dxfId=3 DXF_COVERAGE - light orange
    _dxf_bgfill("FFE2EFDA"),        # dxfId=4 DXF_INMARKET - light green
]
# Symbolic dxfId handles for sheet-module conditional formatting (see primitives.cf_rule).
DXF_ANOMALY, DXF_IMMINENT, DXF_COVERAGE, DXF_INMARKET = 1, 2, 3, 4

# The table-style element slots, all pointed at the empty dxfId=0. Stripe slots
# carry size="1" (matches what Excel emits); moot here since the dxf is empty and
# showRowStripes is off on every table.
_TABLE_STYLE_ELEMENTS = [
    ("wholeTable", None),
    ("headerRow", None),
    ("totalRow", None),
    ("firstColumn", None),
    ("lastColumn", None),
    ("firstHeaderCell", None),
    ("lastHeaderCell", None),
    ("firstTotalCell", None),
    ("lastTotalCell", None),
    ("firstRowStripe", 1),
    ("secondRowStripe", 1),
    ("firstColumnStripe", 1),
    ("secondColumnStripe", 1),
]


def _build_no_format_table_styles_xml() -> str:
    """Render the <tableStyles> block: the named no-format style, set as default."""
    elems = []
    for typ, size in _TABLE_STYLE_ELEMENTS:
        size_attr = f' size="{size}"' if size is not None else ""
        elems.append(f'<tableStyleElement type="{typ}" dxfId="0"{size_attr}/>')
    return (
        f'<tableStyles count="1" '
        f'defaultTableStyle="{NO_FORMAT_TABLE_STYLE}" '
        f'defaultPivotStyle="PivotStyleLight16">'
        f'<tableStyle name="{NO_FORMAT_TABLE_STYLE}" pivot="0" table="1" '
        f'count="{len(elems)}">'
        + "".join(elems)
        + "</tableStyle>"
        + "</tableStyles>"
    )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def build_styles_xml() -> str:
    """Render xl/styles.xml from the palette + format / font / fill / border
    lists + cellXfs above. Called once per build.
    """
    def attr(s: str) -> str:
        return xml_escape(s, {'"': "&quot;", "'": "&apos;"})

    nf_xml = "".join(
        f'<numFmt numFmtId="{i}" formatCode="{attr(c)}"/>'
        for i, c in NUM_FMTS
    )
    fonts_xml = f'<fonts count="{len(FONTS)}">{"".join(FONTS)}</fonts>'
    fills_xml = f'<fills count="{len(FILLS)}">{"".join(FILLS)}</fills>'
    borders_xml = f'<borders count="{len(BORDERS)}">{"".join(BORDERS)}</borders>'
    cell_style_xfs = (
        '<cellStyleXfs count="1">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
        "</cellStyleXfs>"
    )
    cell_xfs_xml = (
        f'<cellXfs count="{len(CELL_XFS)}">{"".join(CELL_XFS)}</cellXfs>'
    )
    # Minimal cellStyles block - reduces repair-dialog risk in stricter
    # OOXML consumers (LibreOffice, some Excel versions). References the
    # zeroth cellStyleXfs entry as the Normal style.
    cell_styles_xml = (
        '<cellStyles count="1">'
        '<cellStyle name="Normal" xfId="0" builtinId="0"/>'
        '</cellStyles>'
    )
    # dxfs: dxfId=0 is the empty differential format the no-format table style
    # points at (see "Native-table style catalog" above). It is RESERVED — any
    # future conditional-formatting dxf appends AFTER it (dxfId=1, 2, …).
    # tableStyles: the named no-format table style, set as the workbook default so
    # every native table (and any table a user later creates) keeps a legal named
    # style instead of letting Excel inject a banded default on open/save.
    # Schema order inside <styleSheet>: ... cellStyles, dxfs, tableStyles.
    dxfs_xml = f'<dxfs count="{len(DXFS)}">{"".join(DXFS)}</dxfs>'
    table_styles_xml = _build_no_format_table_styles_xml()

    return (
        XML_DECL
        + f'<styleSheet xmlns="{NS_SS}">'
        + f'<numFmts count="{len(NUM_FMTS)}">{nf_xml}</numFmts>'
        + fonts_xml + fills_xml + borders_xml
        + cell_style_xfs + cell_xfs_xml + cell_styles_xml
        + dxfs_xml + table_styles_xml
        + "</styleSheet>"
    )
