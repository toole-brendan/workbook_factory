"""Legacy Excel Notes (old-style cell comments) as a declarative artifact.

A Note is the yellow hover box with the little red triangle in the cell corner —
Excel's "Note", distinct from a threaded "Comment". A sheet author just declares
`ExcelNote`s on the returned `WorksheetSpec`; the packager (`lib.package_workbook`)
owns ALL of the OOXML wiring, exactly like native tables. Authors never hand-write
any of the parts below.

Notes are presentation metadata, not the audit trail: keep durable source mapping
in a real table (e.g. an Inputs source-support table) / Sources / Validation. Use a
Note only for optional hover detail on an already-summarized cell.

Import direction (no cycle): ooxml <- styles <- primitives <- {tables, notes} <- lib.

--- OOXML mechanics (maintainer reference — the packager implements this) ---------
One Note needs THREE package parts plus a worksheet element and content-types:
  * xl/comments{N}.xml             — the note text + authors (SpreadsheetML).
  * xl/drawings/vmlDrawing{N}.vml  — the note box geometry + red-triangle indicator
                                     (legacy VML; geometry is approximate, Excel
                                     normalizes it on open).
  * xl/worksheets/_rels/sheet{N}.xml.rels — relationships to BOTH parts.
  * a single <legacyDrawing r:id> on the worksheet, pointing at the VML.
  * [Content_Types].xml — one comments Override per comments part + a single `vml`
                          Default extension.
Parts are numbered by the owning sheet index (one comments + one VML per sheet),
NOT by a global counter (there is at most one of each per sheet). Inside
x:ClientData, Row/Column are ZERO-based. The packager wires notes AFTER native
tables so the injected <legacyDrawing> lands before <tableParts> (CT_Worksheet child
order is `… drawing → legacyDrawing → tableParts → extLst`), and assigns the note
relationship ids AFTER any table rels on the same sheet.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from xml.sax.saxutils import escape as xml_escape

from workbook_core.ooxml import XML_DECL, NS_SS
from workbook_core.primitives import xml_attr


@dataclass(frozen=True)
class ExcelNote:
    """One legacy Excel Note.

    ref:    single A1 cell reference on the owning sheet, e.g. "H8" (no ranges, no
            '$'). The packager rejects malformed refs and duplicates on a sheet.
    text:   hover/click note text (plain text; newlines preserved).
    author: shown in the note metadata.
    visible: False = ordinary hover note (default); True = always shown.
    width_pt / height_pt: note box size in points. Leave as None (default) to
            auto-fit the box to the text (see _fit_note_dims); pass explicit
            points only to override.
    """
    ref: str
    text: str
    author: str = "Model"
    visible: bool = False
    width_pt: float | None = None
    height_pt: float | None = None


def _fit_note_dims(text: str) -> tuple[float, float]:
    """Approximate a form-fitting note box (points) for `text` at Arial 8pt.

    Width tracks the longest line (capped, then the text wraps); height tracks the
    resulting wrapped-line count - so a one-line note gets a small box instead of
    the legacy fixed 200x100. Heuristic only (Excel re-flows on open), but it keeps
    the box close to the text instead of a fixed oversized rectangle.
    """
    CHAR_W, LINE_H, PAD_W, PAD_H, MAX_W = 4.4, 12.5, 16.0, 9.0, 220.0
    lines_in = str(text).split("\n")
    longest = max((len(ln) for ln in lines_in), default=1)
    width = min(longest * CHAR_W + PAD_W, MAX_W)
    avail = max(width - PAD_W, CHAR_W)
    n_lines = sum(max(1, math.ceil(len(ln) * CHAR_W / avail)) for ln in lines_in)
    height = n_lines * LINE_H + PAD_H
    return round(width, 1), round(height, 1)


_A1_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def _a1_to_zero(ref: str) -> tuple[int, int]:
    """A1 ref -> zero-based (row, col) for VML ClientData Row/Column."""
    m = _A1_RE.match(str(ref).upper())
    if not m:
        raise ValueError(f"unsupported note ref {ref!r}; expected a single A1 cell like H8")
    letters, row_s = m.groups()
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return int(row_s) - 1, col - 1


def validate_excel_notes(notes: list[ExcelNote], *, sheet_name: str) -> None:
    """Raise on any malformed note before it is wired into the package.

    Checks (the build is strict, mirroring validate_excel_table): a parseable single
    A1 cell `ref`, sheet-unique refs (Excel keeps one Note per cell — a duplicate
    would be repaired or picked unpredictably), and non-empty text.
    """
    seen: set[str] = set()
    for note in notes:
        ref = str(note.ref).upper()
        _a1_to_zero(ref)                     # raises on a malformed / ranged ref
        if ref in seen:
            raise ValueError(
                f"Duplicate Excel Note ref {ref!r} on sheet {sheet_name!r}; "
                f"Excel keeps one Note per cell."
            )
        seen.add(ref)
        if note.text is None or not str(note.text).strip():
            raise ValueError(
                f"Excel Note {ref!r} on sheet {sheet_name!r} has empty text."
            )


def build_comments_part_xml(notes: list[ExcelNote]) -> str:
    """Render xl/commentsN.xml for one sheet's notes."""
    authors: list[str] = []
    author_id: dict[str, int] = {}
    for n in notes:
        if n.author not in author_id:
            author_id[n.author] = len(authors)
            authors.append(n.author)
    authors_xml = "".join(f"<author>{xml_escape(a)}</author>" for a in authors)

    comments_xml = []
    for n in notes:
        comments_xml.append(
            f'<comment ref="{xml_attr(n.ref.upper())}" '
            f'authorId="{author_id[n.author]}">'
            "<text>"
            '<r><rPr><sz val="8"/><color indexed="81"/><rFont val="Arial"/>'
            '<family val="2"/></rPr>'
            f'<t xml:space="preserve">{xml_escape(n.text)}</t>'
            "</r>"
            "</text>"
            "</comment>"
        )
    return (
        XML_DECL
        + f'<comments xmlns="{NS_SS}">'
        + f"<authors>{authors_xml}</authors>"
        + f"<commentList>{''.join(comments_xml)}</commentList>"
        + "</comments>"
    )


def build_vml_drawing_xml(notes: list[ExcelNote], *, idmap: int) -> str:
    """Render xl/drawings/vmlDrawingN.vml: the note boxes + red-triangle anchors.

    Row/Column inside x:ClientData are zero-based. The x:Anchor box geometry is
    approximate (col/row + offsets); Excel normalizes it on open.
    """
    shapes = []
    for i, n in enumerate(notes, start=1025):
        row0, col0 = _a1_to_zero(n.ref)
        # Box size: auto-fit to the text unless explicit points were given.
        w_pt, h_pt = (
            _fit_note_dims(n.text)
            if (n.width_pt is None or n.height_pt is None)
            else (n.width_pt, n.height_pt)
        )
        # Anchor span (cells) approximated from the fitted points so it tracks the
        # CSS box rather than a fixed 3-col x 6-row rectangle; ~48pt/column and the
        # 10pt default row height. SizeWithCells is intentionally omitted ("move but
        # don't size") so the note keeps this fitted size instead of ballooning to
        # the underlying cell range.
        col_span = max(1, round(w_pt / 48.0))
        row_span = max(1, round(h_pt / 10.0))
        anchor = (f"{col0 + 1}, 15, {row0}, 2, "
                  f"{col0 + 1 + col_span}, 15, {row0 + row_span}, 4")
        visibility = "visible" if n.visible else "hidden"
        visible_xml = "<x:Visible/>" if n.visible else ""
        shapes.append(
            f'<v:shape id="_x0000_s{i}" type="#_x0000_t202" '
            f'style="position:absolute;margin-left:120pt;margin-top:1.5pt;'
            f'width:{w_pt}pt;height:{h_pt}pt;'
            f'z-index:{i - 1024};visibility:{visibility}" '
            'fillcolor="#ffffe1" o:insetmode="auto">'
            '<v:fill color2="#ffffe1"/>'
            '<v:shadow on="t" color="black" obscured="t"/>'
            '<v:path o:connecttype="none"/>'
            '<v:textbox style="mso-direction-alt:auto"><div style="text-align:left"/></v:textbox>'
            '<x:ClientData ObjectType="Note">'
            "<x:MoveWithCells/>"
            f"<x:Anchor>{anchor}</x:Anchor>"
            "<x:AutoFill>False</x:AutoFill>"
            f"{visible_xml}"
            f"<x:Row>{row0}</x:Row><x:Column>{col0}</x:Column>"
            "</x:ClientData>"
            "</v:shape>"
        )
    return (
        XML_DECL
        + '<xml xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:x="urn:schemas-microsoft-com:office:excel">'
        '<o:shapelayout v:ext="edit">'
        f'<o:idmap v:ext="edit" data="{idmap}"/>'
        "</o:shapelayout>"
        '<v:shapetype id="_x0000_t202" coordsize="21600,21600" o:spt="202" '
        'path="m,l,21600r21600,l21600,xe">'
        '<v:stroke joinstyle="miter"/>'
        '<v:path gradientshapeok="t" o:connecttype="rect"/>'
        "</v:shapetype>"
        + "".join(shapes)
        + "</xml>"
    )


def inject_legacy_drawing(ws_xml: str, rid: str) -> str:
    """Insert a worksheet-level <legacyDrawing r:id="..."/>.

    CT_Worksheet order puts legacyDrawing before tableParts and extLst, so insert
    before <tableParts if present, else before <extLst, else before </worksheet>.
    """
    legacy = f'<legacyDrawing r:id="{xml_attr(rid)}"/>'
    if "<tableParts" in ws_xml:
        return ws_xml.replace("<tableParts", legacy + "<tableParts", 1)
    if "<extLst" in ws_xml:
        return ws_xml.replace("<extLst", legacy + "<extLst", 1)
    return ws_xml.replace("</worksheet>", legacy + "</worksheet>", 1)
