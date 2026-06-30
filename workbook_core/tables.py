"""Native Excel tables (ListObjects).

The cell data stays in the worksheet, but the table itself is a separate package
artifact that needs extra wiring: a table part (xl/tables/tableN.xml), a
worksheet relationship to it, a <tableParts> child inside the worksheet, and a
[Content_Types] override. The packager (lib.package_workbook) owns that wiring;
sheet authors just declare an ExcelTable on the WorksheetSpec they return.

Use a native table for filterable/structured ranges (data dumps, deck-facing
data contracts, source lists, scenario/lookup tables). For ordinary model blocks
the lightweight styled range from primitives.build_table() is the better default.

Import direction (no cycle): ooxml <- styles <- primitives <- tables <- lib.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from workbook_core.ooxml import XML_DECL, NS_SS, NS_PR
from workbook_core.primitives import xml_attr
from workbook_core.table_style_names import NO_FORMAT_TABLE_STYLE

# The default native-table style is a NAMED no-format table style defined in
# styles.xml (NO_FORMAT_TABLE_STYLE): it points every table-style element at an
# empty differential format, so it draws no fill, border, font, stripe, header
# rule, or final border — the per-cell S_* styles stay the only visible formatting
# (header = S_HEADER_LEFT underline, body borderless, dividers only via
# total_row()), matching the styled-range build_table(). A named style is more
# robust than emitting no <tableStyleInfo> or the legacy name="None": Excel can
# inject its own banded default on open/save when a native table has no durable
# named style to preserve, so we always ship one.
#   - A built-in name (e.g. "TableStyleMedium2") opts a data dump into Excel banding.
#   - style=None emits NO <tableStyleInfo> at all — reserve it for low-level OOXML
#     cases where the absence is intentional, NOT as a way to "remove formatting"
#     (the named no-format style is the round-trip-safe way to do that).
DEFAULT_TABLE_STYLE = NO_FORMAT_TABLE_STYLE


@dataclass(frozen=True)
class ExcelTable:
    """Declarative spec for one native Excel table (ListObject).

    name:    table name (workbook-unique; safe-name rules — letters/digits/_,
             not a cell-ref shape). Becomes displayName + name on the part.
    ref:     A1-style range INCLUDING the header row, e.g. "B6:H42". The cells
             must already be written into the worksheet at that range (the table
             part is metadata only; values live in the sheet).
    headers: column header strings, in order; must match the header row in `ref`
             and be unique (Excel requires unique, non-empty column names).
    style:   table style name, or None to emit no <tableStyleInfo>. Defaults to
             workbook_core's named no-format table style (NO_FORMAT_TABLE_STYLE):
             ListObject behavior is preserved while no table-style fill/border/font
             is drawn, so the cell-level S_* styles control the look and Excel has a
             legal named style to preserve on open/save. See DEFAULT_TABLE_STYLE.
    show_row_stripes: banded-row striping (default off; only meaningful when a
             built-in `style` is set - the no-format style has no bands regardless).
    totals_row_shown: reserve a totals row (the `ref` must include it when True).
    totals:  optional {header: builtin_function} for the totals row, where
             builtin_function is e.g. "sum"/"average"/"count" (rendered as the
             column's totalsRowFunction).
    """
    name: str
    ref: str
    headers: list[str]
    style: str | None = DEFAULT_TABLE_STYLE
    show_row_stripes: bool = False
    totals_row_shown: bool = False
    totals: dict[str, str] = field(default_factory=dict)


@dataclass
class WorksheetSpec:
    """What a sheet's render() returns: the worksheet XML plus native artifacts.

    Render-local (not module-level) because table `ref`s and defined names are
    computed from the actual row counts at render time.

    xml:           the complete <worksheet> string (from primitives.worksheet()).
    tables:        native ExcelTables to wire into this sheet.
    defined_names: {name: target} added to the workbook's <definedNames>, where
                   target is a formula-style ref, e.g. "'Inputs'!$D$7". Names are
                   workbook-scoped; follow the safe-name rules (see cheat sheet
                   "Defined names").
    notes:         legacy Excel Notes (notes.ExcelNote) — the red-triangle / hover
                   cards. The packager wires the comments + VML parts; see notes.py.
                   Untyped here (list) so tables.py stays an independent sibling of
                   notes.py (the packager imports both).
    """
    xml: str
    tables: list[ExcelTable] = field(default_factory=list)
    defined_names: dict[str, str] = field(default_factory=dict)
    notes: list = field(default_factory=list)


@dataclass(frozen=True)
class SheetEntry:
    """A worksheet to register, decoupled from the one-file-per-tab module layout.

    Lets ONE source file register MULTIPLE tabs - the workbook groups its sheet
    code by data/model/audit responsibility rather than one module per tab. The
    packager (lib.package_workbook) accepts either a sheet *module* (legacy: reads
    TAB_NAME / SHEET_GROUP / render()) OR a SheetEntry, normalizing both to a
    (tab_name, group, render) triple - so the two styles coexist and a pipeline
    can migrate group by group.

    tab_name: worksheet name (load-bearing - formulas/accessors reference it by
              value; the packager rejects duplicates rather than renaming).
    group:    logical-chapter key (one of groups.SHEET_GROUPS) -> tab color +
              tab-block order; the same contiguity invariant applies as for modules.
    render:   zero-arg callable returning this sheet's WorksheetSpec.
    hidden:   when True the tab is built but marked state="hidden" in
              workbook.xml (unhide via Excel's sheet menu). Formulas on other
              sheets that reference a hidden tab keep working; at least one
              sheet in the workbook must stay visible.
    """
    tab_name: str
    group: str
    render: Callable[[], WorksheetSpec]
    hidden: bool = False


# ---------------------------------------------------------------------------
# Validation (called by the packager - the build is strict, the probe is lenient)
# ---------------------------------------------------------------------------
# Table names and defined names are load-bearing Excel identifiers: structured
# references and formulas reference them by value, so the packager validates them
# up front rather than emitting a part Excel will reject (a "repair" dialog) or one
# whose ref silently disagrees with its headers.

# [A-Za-z_] start, then letters/digits/'.'/'_': the shared safe-name shape for both
# native table names and workbook defined names (no spaces, not starting with a digit).
_SAFE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
# An A1 cell (B4, $AB$12) or an R1C1 cell - a name in either shape is forbidden.
_A1_CELL_RE = re.compile(r"^\$?[A-Za-z]{1,3}\$?[0-9]+$")
_R1C1_CELL_RE = re.compile(r"^[Rr][0-9]+[Cc][0-9]+$")
# An A1 rectangular range like "B4:E42" ($ optional); groups = (c1, r1, c2, r2).
_A1_RANGE_RE = re.compile(
    r"^\$?([A-Za-z]{1,3})\$?([0-9]+):\$?([A-Za-z]{1,3})\$?([0-9]+)$"
)


def _looks_like_cell_ref(name: str) -> bool:
    """True if `name` would be read as a cell reference (so illegal as an Excel name)."""
    if _A1_CELL_RE.match(name) or _R1C1_CELL_RE.match(name):
        return True
    return name.upper() in {"R", "C"}   # reserved single-letter names


def _col_to_num(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def validate_table_name(name: str) -> None:
    """Raise unless `name` is a legal native-table (ListObject) name."""
    if not name:
        raise ValueError("native table name is empty")
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(
            f"invalid native table name {name!r}: start with a letter or '_' and "
            f"use only letters, digits, '.', '_' (no spaces)"
        )
    if _looks_like_cell_ref(name):
        raise ValueError(
            f"native table name {name!r} looks like a cell reference; Excel forbids that"
        )


def validate_defined_name(name: str) -> None:
    """Raise unless `name` is a legal workbook defined name."""
    if not name:
        raise ValueError("defined name is empty")
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(
            f"invalid defined name {name!r}: match [A-Za-z_][A-Za-z0-9_.]* "
            f"(no spaces, not starting with a digit)"
        )
    if _looks_like_cell_ref(name):
        raise ValueError(
            f"defined name {name!r} looks like a cell reference; Excel forbids that"
        )
    if name.lower().startswith("_xlnm"):
        raise ValueError(f"defined name {name!r} uses the reserved '_xlnm' prefix")


def validate_excel_table(t: ExcelTable) -> None:
    """Raise on any malformed ExcelTable before it is wired into the package.

    Checks: legal table name; non-empty + case-insensitively-unique headers; a
    valid A1 rectangular `ref` whose column span equals len(headers); and totals
    keys that are all real header names.
    """
    validate_table_name(t.name)

    if not t.headers:
        raise ValueError(f"table {t.name!r} has no headers")
    seen: set[str] = set()
    for h in t.headers:
        if h is None or str(h).strip() == "":
            raise ValueError(f"table {t.name!r} has an empty column header")
        key = str(h).strip().lower()
        if key in seen:
            raise ValueError(
                f"table {t.name!r} has duplicate column header {h!r} "
                f"(Excel requires unique table column names)"
            )
        seen.add(key)

    m = _A1_RANGE_RE.match(t.ref)
    if not m:
        raise ValueError(
            f"table {t.name!r} ref {t.ref!r} is not a valid A1 range like 'B4:E42'"
        )
    c1, r1, c2, r2 = (_col_to_num(m.group(1)), int(m.group(2)),
                      _col_to_num(m.group(3)), int(m.group(4)))
    if c2 < c1 or r2 < r1:
        raise ValueError(
            f"table {t.name!r} ref {t.ref!r} is reversed; start cell must precede end"
        )
    span = c2 - c1 + 1
    if span != len(t.headers):
        raise ValueError(
            f"table {t.name!r} ref {t.ref!r} spans {span} column(s) but has "
            f"{len(t.headers)} header(s); the ref must cover exactly the header "
            f"columns (header row included)"
        )

    extra = [k for k in t.totals if k not in t.headers]
    if extra:
        raise ValueError(
            f"table {t.name!r} totals reference unknown column(s) {extra}; "
            f"each totals key must be a header name"
        )


def build_table_part_xml(table_id: int, t: ExcelTable) -> str:
    """Render xl/tables/table{table_id}.xml for one ExcelTable.

    table_id is the global (workbook-wide) 1-based table number, used as the part
    id and filename. The visible table name/displayName come from t.name.
    """
    n = len(t.headers)
    cols = []
    for i, h in enumerate(t.headers, start=1):
        fn = t.totals.get(h)
        extra = f' totalsRowFunction="{xml_attr(fn)}"' if fn else ""
        cols.append(f'<tableColumn id="{i}" name="{xml_attr(h)}"{extra}/>')
    cols_xml = f'<tableColumns count="{n}">{"".join(cols)}</tableColumns>'

    totals_attr = ' totalsRowShown="1"' if t.totals_row_shown else ' totalsRowShown="0"'
    # style=None emits no <tableStyleInfo> (the rare raw-OOXML case); otherwise a
    # named/built-in style reference. The default is the named no-format style.
    style_xml = (
        f'<tableStyleInfo name="{xml_attr(t.style)}" '
        f'showFirstColumn="0" showLastColumn="0" '
        f'showRowStripes="{1 if t.show_row_stripes else 0}" showColumnStripes="0"/>'
        if t.style else ""
    )
    return (
        XML_DECL
        + f'<table xmlns="{NS_SS}" id="{table_id}" name="{xml_attr(t.name)}" '
        f'displayName="{xml_attr(t.name)}" ref="{t.ref}"{totals_attr}>'
        + f'<autoFilter ref="{t.ref}"/>'
        + cols_xml + style_xml
        + "</table>"
    )


def build_sheet_rels(rels: list[tuple[str, str, str]]) -> str:
    """Render an xl/worksheets/_rels/sheetN.xml.rels part.

    rels: list of (rId, relationship_type_suffix, target). The type suffix is the
    tail of the OOXML relationship-type URI, e.g. "table".
    """
    parts = "".join(
        f'<Relationship Id="{rid}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{typ}" '
        f'Target="{target}"/>'
        for rid, typ, target in rels
    )
    return (
        XML_DECL
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + parts
        + "</Relationships>"
    )


def inject_table_parts(ws_xml: str, rids: list[str]) -> str:
    """Insert a <tableParts> child into a finished <worksheet> string.

    <tableParts> must sit late in CT_Worksheet order (after drawing, before
    extLst), so insert before <extLst> if present, else before </worksheet>.
    The packager owns the rIds (table numbering is global), so authors never
    place this element themselves.
    """
    if not rids:
        return ws_xml
    table_parts = (
        f'<tableParts count="{len(rids)}">'
        + "".join(f'<tablePart r:id="{rid}"/>' for rid in rids)
        + "</tableParts>"
    )
    if "<extLst" in ws_xml:
        return ws_xml.replace("<extLst", table_parts + "<extLst", 1)
    return ws_xml.replace("</worksheet>", table_parts + "</worksheet>", 1)
