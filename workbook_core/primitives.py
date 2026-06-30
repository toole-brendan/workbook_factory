"""Raw OOXML SpreadsheetML primitives — the building-block layer.

Stdlib-only, no openpyxl. These are the cell/row/worksheet/table string builders
plus reference + formula helpers that sheet modules compose into a single
<worksheet> XML string. The engine (lib.py) consumes that string; styling lives
in styles.py.

Import direction (no cycle): ooxml <- styles <- primitives <- tables <- lib.
Sheet modules import from here directly:

    from workbook_core.primitives import (
        worksheet, write_row, banner_row, build_table, cref, col_letter,
        qsheet, abs_ref, sheet_ref, range_ref,
    )

Public surface:
    refs/formulas   col_letter, cref, qsheet, abs_ref, sheet_ref, range_ref
    cell/row        cell, row, filter_range, banner_row, write_row
    worksheet       worksheet  (schema-ordered optional feature slots)
    table (styled)  build_table  -> (rows_xml, next_row); a *styled range*, not a
                    native Excel table (those live in tables.py)
    xml             xml_attr  (attribute-safe escaping, incl. quotes)
    text switch     set_normalize_dashes  (em/en-dash -> hyphen on text cells)

Workbook standards enforced by worksheet() on every sheet (locked):
    showGridLines="0" · defaultRowHeight="10" · no frozen panes · no merged cells.
"""
from __future__ import annotations

from xml.sax.saxutils import escape as xml_escape

from workbook_core.ooxml import XML_DECL, NS_SS, NS_PR
# S_DEFAULT is used internally by banner_row()/write_row() for the gutter cell;
# S_BORDER_TOP + BORDER_TOP_FOR back total_row()'s continuous-divider guarantee.
from workbook_core.styles import S_DEFAULT, S_BORDER_TOP, BORDER_TOP_FOR


# ---------------------------------------------------------------------------
# Optional text normalization (pipeline-level switch)
# ---------------------------------------------------------------------------
# OFF by default. The packager flips it per build via the normalize_dashes=
# parameter of package_workbook() (destroyer opts in; submarine leaves it off so
# its em/en dashes survive). cell() reads the module-level flag.
_NORMALIZE_DASHES = False


def set_normalize_dashes(on: bool = True) -> None:
    """Enable/disable em/en-dash -> hyphen normalization on text cells.

    Set once per build by package_workbook(normalize_dashes=...). Kept here next
    to cell(), the only reader.
    """
    global _NORMALIZE_DASHES
    _NORMALIZE_DASHES = bool(on)


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def xml_attr(s: str) -> str:
    """Escape a string for use as an XML *attribute* value.

    Like xml.sax.saxutils.escape (which handles & < >) but also escapes single
    and double quotes, so it is safe inside `name="..."` attributes (e.g. sheet
    names in workbook.xml, table/defined-name identifiers).
    """
    return xml_escape(str(s), {'"': "&quot;", "'": "&apos;"})


# ---------------------------------------------------------------------------
# Cell references + formula helpers
# ---------------------------------------------------------------------------


def col_letter(n: int) -> str:
    """0-indexed column → letter. 0→A, 25→Z, 26→AA, 27→AB."""
    s = ""
    n = int(n)
    while True:
        s = chr(ord("A") + n % 26) + s
        n = n // 26 - 1
        if n < 0:
            return s


def cref(row_: int, col: int) -> str:
    """1-indexed row, 0-indexed col → 'A1'."""
    return f"{col_letter(col)}{row_}"


def qsheet(name: str) -> str:
    """Quote a sheet name for a formula: Inputs → 'Inputs'; a'b → 'a''b'.

    Always quotes (valid for any name) and doubles embedded apostrophes, matching
    the existing accessor convention (e.g. "'Control_Panel'!C15").
    """
    return "'" + str(name).replace("'", "''") + "'"


def abs_ref(row_: int, col: int) -> str:
    """1-indexed row, 0-indexed col → absolute '$A$1'."""
    return f"${col_letter(col)}${row_}"


def sheet_ref(sheet: str, row_: int, col: int) -> str:
    """Sheet + cell → 'Sheet Name'!$A$1 (quoted sheet, absolute cell)."""
    return f"{qsheet(sheet)}!{abs_ref(row_, col)}"


def range_ref(sheet: str, r1: int, c1: int, r2: int, c2: int) -> str:
    """Sheet + bounds → 'Sheet Name'!$A$1:$D$20 (quoted sheet, absolute range)."""
    return f"{qsheet(sheet)}!{abs_ref(r1, c1)}:{abs_ref(r2, c2)}"


# ---------------------------------------------------------------------------
# Cell + row builders
# ---------------------------------------------------------------------------


class ArrayF(str):
    """Marker for a single-cell array (CSE) formula. A formula string wrapped in
    ArrayF is emitted as <f t="array" ref="self"> so Excel evaluates it as an
    array formula (e.g. =MEDIAN(IF(cond,vals))) - the result is ONE cell, not a
    spill. Pass it through write_row exactly like a normal '=' formula string
    (it is a str subclass, so the '=' formula detection still fires)."""
    __slots__ = ()


class SpillF(str):
    """Marker for a DYNAMIC array (spill) formula. Emitted with cm="1" (pointing
    at the dynamic-array metadata record) + t="array", so Excel treats it as a
    spilling dynamic array (e.g. =SORT(UNIQUE(...)) or =MINIFS(range,key,B2#))
    that recomputes its own extent and fills the cells below/right. Write ONLY the
    anchor cell - do not emit cells in the spill range; Excel fills them on calc.
    The package must include xl/metadata.xml (lib.build_metadata_xml)."""
    __slots__ = ()


def cell(ref: str, *, style: int, value=None,
         formula: str | None = None, array: bool = False,
         spill: bool = False) -> str:
    """Single <c> element. `style` is required (keyword-only).

    - Pass `formula` (without leading '=') to write an Excel expression;
      Excel will compute and cache <v> on first open. `array=True` writes a
      single-cell array (CSE) formula; `spill=True` writes a dynamic-array
      (spill) formula (cm="1" + <f t="array">), filling cells below on calc.
    - Pass `value` for a literal int/float/str/bool.
    - Empty cells with a non-default style still emit a <c s="…"/> so
      borders / fills render.
    """
    if formula is not None:
        f = formula.lstrip("=")
        if spill:
            # Dynamic array (spill): cm="1" points at the XLDAPR (fDynamic) metadata
            # record; t="array" with an ANCHOR-ONLY ref (the libxlsxwriter pattern for
            # an extent not known at write time - Excel recomputes + re-extents on the
            # forced full calc); a cached <v>0</v> placeholder satisfies the load-time
            # validator. NO aca/ca (those are for legacy CSE formulas).
            return (f'<c r="{ref}" s="{style}" cm="1">'
                    f'<f t="array" ref="{ref}">{xml_escape(f)}</f><v>0</v></c>')
        if array:
            return (f'<c r="{ref}" s="{style}">'
                    f'<f t="array" ref="{ref}" aca="1" ca="1">{xml_escape(f)}</f></c>')
        return f'<c r="{ref}" s="{style}"><f>{xml_escape(f)}</f></c>'
    if value is None or value == "":
        if style:
            return f'<c r="{ref}" s="{style}"/>'
        return ""
    if isinstance(value, bool):
        v = 1 if value else 0
        return f'<c r="{ref}" s="{style}" t="b"><v>{v}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    text = str(value)
    if _NORMALIZE_DASHES:
        text = text.replace("—", "-").replace("–", "-")
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr"><is>'
        f'<t xml:space="preserve">{xml_escape(text)}</t></is></c>'
    )


def row(r: int, cells_xml: list[str],
        outline_level: int = 0,
        ht: float | None = None) -> str:
    """Emit one <row>.

    outline_level: when > 0, row joins a collapsible group at that depth.
      Excel infers groups from contiguous runs of equal levels; level-0
      rows (banners, subtotals) sit outside groups and stay visible when
      adjacent level-1 rows collapse.
    ht: override row height (points); paired with customHeight="1".
    """
    attrs = f' r="{r}"'
    if ht is not None:
        attrs += f' ht="{ht}" customHeight="1"'
    if outline_level:
        attrs += f' outlineLevel="{outline_level}"'
    return f'<row{attrs}>{"".join(c for c in cells_xml if c)}</row>'


def filter_range(headers: list, data: list,
                 start_row: int = 1, start_col: int = 0) -> str:
    """Compute the autoFilter range covering a header + data block.

    Example: 12 columns + 26 data rows → "A1:L27".
    """
    end_col = col_letter(start_col + len(headers) - 1)
    end_row = start_row + len(data)
    return f"{col_letter(start_col)}{start_row}:{end_col}{end_row}"


def cf_rule(sqref: str, dxf_id: int, formula: str, priority: int = 1) -> str:
    """One <conditionalFormatting> block: apply differential format `dxf_id` to the cells
    in `sqref` where the Excel expression `formula` (leading '=' optional) is TRUE. The
    expression is evaluated relative to the top-left cell of `sqref` (use an absolute column
    + relative row, e.g. "$M7", to test each row of a column). Pair with
    worksheet(conditional_formatting=[...]) and the dxfs in styles.DXFS."""
    expr = formula[1:] if formula.startswith("=") else formula
    return (f'<conditionalFormatting sqref="{sqref}">'
            f'<cfRule type="expression" dxfId="{dxf_id}" priority="{priority}">'
            f'<formula>{xml_escape(expr)}</formula></cfRule>'
            f'</conditionalFormatting>')


def data_validation(sqref: str, *, kind: str, operator: str | None = None,
                    formula1: str | None = None, formula2: str | None = None,
                    allow_blank: bool = True, show_error: bool = True) -> str:
    """One <dataValidation> element restricting what may be typed into `sqref`.

    kind: "decimal" / "whole" / "date" / "list" / "textLength" (CT_DataValidation type).
    operator: "between" / "greaterThanOrEqual" / ... (omit for a list). formula1/formula2
    carry the bound(s); a list passes its members as formula1='"A,B,C"' (quotes included).
    Pair with worksheet(data_validations=[...]); the parent <dataValidations count="N">
    wrapper is added there. allow_blank keeps an empty cell legal (the honest default).
    """
    attrs = [f'type="{kind}"']
    if operator:
        attrs.append(f'operator="{operator}"')
    attrs.append(f'allowBlank="{1 if allow_blank else 0}"')
    if show_error:
        attrs.append('showErrorMessage="1"')
    attrs.append(f'sqref="{sqref}"')
    inner = ""
    if formula1 is not None:
        inner += f'<formula1>{xml_escape(formula1)}</formula1>'
    if formula2 is not None:
        inner += f'<formula2>{xml_escape(formula2)}</formula2>'
    head = " ".join(attrs)
    return f'<dataValidation {head}>{inner}</dataValidation>' if inner else \
           f'<dataValidation {head}/>'


def banner_row(r: int, text: str, n_cols: int,
               *, style: int,
               with_gutter: bool = False,
               mark_collapsible: bool = False,
               outline_level: int = 0,
               text_col: int = 1) -> str:
    """Render a full-width banner row. `style` is required (keyword-only).

    Legacy (with_gutter=False): `text` is placed in column A with `style`;
    columns B..n_cols-1 emit empty cells with the same style so the fill
    spans the row.

    Gutter mode (with_gutter=True): column A (gutter) stays free of the
    banner fill - it uses S_DEFAULT, so no banner background leaks into
    the gutter. When mark_collapsible=True, a neutral-style lowercase 'x'
    is placed in column A. Banner text moves to column B; the banner fill
    spans columns B..n_cols.

    outline_level: a banner can itself sit inside a deeper group and act as
    the summary row for the rows below it (e.g. a §-section banner at level 1
    summarising level-2 detail). Default 0 keeps banners outside any group.

    text_col (gutter mode): the content column the label is written into; the
    banner fill always spans columns 1..n_cols. Default 1 (the first content
    column, B). Pass the first VISIBLE content column when leading columns are
    hidden, so the label is not lost behind a zero-width hidden column.

    Use S_TITLE_SHEET / S_TITLE_SECTION / S_TITLE_SUBSECTION as `style`.
    """
    if with_gutter:
        parts = []
        if mark_collapsible:
            parts.append(cell(cref(r, 0), value="x", style=S_DEFAULT))
        for i in range(1, n_cols + 1):
            parts.append(cell(cref(r, i), value=(text if i == text_col else None),
                              style=style))
    else:
        parts = [cell(cref(r, 0), value=text, style=style)]
        for i in range(1, n_cols):
            parts.append(cell(cref(r, i), value=None, style=style))
    return row(r, parts, outline_level=outline_level)


def write_row(r: int, values: list, *, styles, start_col: int = 0,
              outline_level: int = 0,
              ht: float | None = None,
              mark_collapsible: bool = False) -> str:
    """Write one row of mixed values starting at start_col.

    Values starting with '=' (followed by a letter/digit/paren/quote) are
    treated as formulas. `styles` is required (keyword-only); pass either
    a single int (broadcast to every value) or a list whose length
    equals values. None values emit a styled empty cell so borders are
    preserved when styles are non-default.

    Pass the style explicitly for every cell - there is no auto-swap
    for cross-sheet refs. Use S_LINK_NUM (numbers) or S_LINK_PCT
    (percentages) explicitly when writing a pure =Sheet!Cell numeric
    reference.

    outline_level / ht forwarded to row(); see row()'s docstring.
    mark_collapsible=True places a neutral-style 'x' in column A
    (the gutter), marking this row as a collapse anchor.
    """
    if isinstance(styles, int):
        styles_list = [styles] * len(values)
    else:
        styles_list = list(styles)
        if len(styles_list) != len(values):
            raise ValueError(
                f"styles list length {len(styles_list)} != values "
                f"length {len(values)} - every value must have an "
                f"explicit style (no S_DEFAULT padding)"
            )

    cells = []
    if mark_collapsible:
        cells.append(cell(cref(r, 0), value="x", style=S_DEFAULT))
    for i, (v, s) in enumerate(zip(values, styles_list)):
        ref = cref(r, start_col + i)
        # Treat as formula only if it starts with '=' followed by a letter,
        # digit, '(', '-', '+', quote, '$' (absolute ref), '_' (e.g. the
        # _xlfn.* future-function prefix), or '{' (array constant) - not
        # a space or descriptive text.
        if (isinstance(v, str) and len(v) > 1 and v[0] == "="
                and (v[1].isalpha() or v[1].isdigit() or v[1] in "('-+\"$_{")):
            formula_body = v[1:]
            cells.append(cell(ref, formula=formula_body, style=s,
                              array=isinstance(v, ArrayF),
                              spill=isinstance(v, SpillF)))
        else:
            cells.append(cell(ref, value=v, style=s))
    return row(r, cells, outline_level=outline_level, ht=ht)


def total_row(r: int, values: list, *, styles, n_cols: int,
              start_col: int = 1,
              outline_level: int = 0,
              ht: float | None = None) -> str:
    """Write a total/subtotal divider row with a CONTINUOUS top border.

    The total divider is a top medium border baked per-cell into the style, so
    the line is unbroken only if every cell across the row carries a bordered
    style. This helper guarantees that: it (1) upgrades each given style to its
    top-bordered variant via styles.BORDER_TOP_FOR (S_BOLD->S_TOTAL,
    S_NUM->S_NUM_TOTAL, S_DEFAULT->S_BORDER_TOP, ...; already-bordered styles map
    to themselves), and (2) pads the row out to `n_cols` content columns with
    bordered empty cells, so the line spans the full block width even past the
    last value.

    Pass the plain BASE styles for each value (e.g. S_BOLD for the label, S_NUM
    for figures) and the block's content width as `n_cols` - the same width you
    pass to banner_row(). `values` may be shorter than n_cols (the tail is padded
    with blank bordered cells). Values beginning with '=' are treated as formulas
    (delegated to write_row). The gutter (column A) is left unbordered, matching
    the banners.
    """
    if isinstance(styles, int):
        styles = [styles] * len(values)
    else:
        styles = list(styles)
        if len(styles) != len(values):
            raise ValueError(
                f"styles length {len(styles)} != values length {len(values)}"
            )
    if len(values) > n_cols:
        raise ValueError(
            f"total_row got {len(values)} values but n_cols={n_cols}"
        )
    upgraded = []
    for s in styles:
        if s not in BORDER_TOP_FOR:
            raise ValueError(
                f"total_row: no bordered total variant for style index {s} - "
                f"add one to styles.BORDER_TOP_FOR"
            )
        upgraded.append(BORDER_TOP_FOR[s])
    pad = n_cols - len(values)
    vals = list(values) + [None] * pad
    sty = upgraded + [S_BORDER_TOP] * pad
    return write_row(r, vals, styles=sty, start_col=start_col,
                     outline_level=outline_level, ht=ht)


# ---------------------------------------------------------------------------
# Worksheet wrapper
# ---------------------------------------------------------------------------


def worksheet(rows_xml: list[str],
              cols: list | None = None,
              tab_color: str | None = None,
              auto_filter: str | None = None,
              with_gutter: bool = False,
              *,
              show_outline_symbols: bool = False,
              conditional_formatting: list[str] | None = None,
              data_validations: list[str] | None = None,
              ext_lst: str | None = None,
              **_ignored) -> str:
    """Wrap row XML strings into a complete <worksheet>.

    cols: list of column specs (Excel character units). Each entry is a bare
        width number, None (column skipped), or a {"width": w, "hidden": bool}
        mapping - hidden columns stay in the grid (A1 refs/formula helpers keep
        working) but are not shown to the reader.
    tab_color: 6-char hex (no leading '#'). Use groups.group_color(SHEET_GROUP).
    auto_filter: range like "A1:L27" - Excel adds filter dropdowns on row 1.
    with_gutter: prepend a 1.5-char-wide gutter column at column A and inject
        an empty row 1. Sheet modules using with_gutter must place content
        starting at column B (start_col=1) and row 2.
    show_outline_symbols: gutter mode hides Excel's native outline +/- controls
        by default (showOutlineSymbols="0") so the cosmetic gutter 'x' is the
        only collapse cue. Set True to surface the real interactive controls
        (the rows must carry a deliberate outlineLevel hierarchy). Opt-in per
        sheet; no effect when with_gutter is False.

    Optional feature slots (emitted in the schema-required order; default off):
      conditional_formatting: list of complete <conditionalFormatting …> blocks.
      data_validations:       list of <dataValidation …> elements (wrapped in a
                              <dataValidations count="N"> parent here).
      ext_lst:                a single <extLst>…</extLst> string (must be last).
    Native Excel <tableParts> are NOT a slot here - the packager injects them
    (it owns the per-sheet relationship ids); see tables.inject_table_parts.

    Workbook standards applied to every sheet (locked):
      - showGridLines="0"        no gridlines
      - defaultRowHeight="10"    universal 10.0 row height
      - no frozen panes          (freeze_row kwarg accepted but ignored)
      - no merged cells          (merges kwarg accepted but ignored)
    """
    cols_xml = ""
    final_cols = list(cols) if cols else []
    if with_gutter:
        # OOXML width 2.2109375 ≈ 1.5 character UI display at Calibri 11 MDW=7.
        final_cols = [2.2109375] + final_cols
    if final_cols:
        defs = []
        for i, spec in enumerate(final_cols, start=1):
            # A column spec is either a bare width (number / None) or a structured
            # {"width": w, "hidden": bool} mapping - the latter lets a sheet keep a
            # formula-helper column in the grid (so A1 refs stay valid) while hiding
            # it from the reader. None still skips the column entirely.
            if isinstance(spec, dict):
                w, hidden = spec.get("width"), bool(spec.get("hidden"))
            else:
                w, hidden = spec, False
            if w is None:
                continue
            hidden_attr = ' hidden="1"' if hidden else ''
            defs.append(
                f'<col min="{i}" max="{i}" width="{w}" customWidth="1"{hidden_attr}/>')
        if defs:
            cols_xml = f'<cols>{"".join(defs)}</cols>'

    # sheetPr child order: tabColor before outlinePr (CT_SheetPr schema).
    sheetpr_inner = ""
    if tab_color:
        sheetpr_inner += f'<tabColor rgb="FF{tab_color}"/>'
    if with_gutter:
        sheetpr_inner += '<outlinePr summaryBelow="0"/>'
    tab_xml = f'<sheetPr>{sheetpr_inner}</sheetPr>' if sheetpr_inner else ""

    view_attrs = 'showGridLines="0" workbookViewId="0"'
    if with_gutter:
        view_attrs += f' showOutlineSymbols="{1 if show_outline_symbols else 0}"'
    views_xml = f'<sheetViews><sheetView {view_attrs}/></sheetViews>'
    fmt_xml = '<sheetFormatPr defaultRowHeight="10" customHeight="1"/>'

    filter_xml = f'<autoFilter ref="{auto_filter}"/>' if auto_filter else ""

    # Optional feature slots, in CT_Worksheet child order:
    # sheetData -> autoFilter -> conditionalFormatting -> dataValidations -> extLst.
    cf_xml = "".join(conditional_formatting or [])
    if data_validations:
        dv_xml = (f'<dataValidations count="{len(data_validations)}">'
                  + "".join(data_validations) + "</dataValidations>")
    else:
        dv_xml = ""
    ext_xml = ext_lst or ""

    # Gutter row 1: empty row at default 10pt so all subsequent row numbers
    # shift down by 1. Sheet modules using with_gutter must not emit row 1.
    sheet_data_parts = []
    if with_gutter:
        sheet_data_parts.append('<row r="1"/>')
    sheet_data_parts.append("".join(rows_xml))

    return (
        XML_DECL
        + f'<worksheet xmlns="{NS_SS}" xmlns:r="{NS_PR}">'
        + tab_xml + views_xml + fmt_xml + cols_xml
        + f"<sheetData>{''.join(sheet_data_parts)}</sheetData>"
        + filter_xml + cf_xml + dv_xml + ext_xml
        + "</worksheet>"
    )


# ---------------------------------------------------------------------------
# Table builder (styled range — NOT a native Excel table; see tables.py)
# ---------------------------------------------------------------------------


def build_table(start_row: int,
                headers: list[str],
                data_rows: list[list],
                *,
                header_style: int,
                col_styles,
                start_col: int = 0,
                outline_level: int = 0,
                mark_header_collapsible: bool = False) -> tuple[list[str], int]:
    """Header row + data rows starting at (start_row, start_col).

    This emits a *styled range* (header + body rows with cell styles); it is the
    lightweight default for model blocks. For a native Excel table (ListObject:
    structured refs, filter persistence, table style) return an ExcelTable on the
    WorksheetSpec instead - see tables.py.

    `header_style` and `col_styles` are required (keyword-only).
    `col_styles` is either a single int (broadcast to every column) or
    a list whose length equals headers.

    outline_level: applied to data rows only - the header row stays at
    level 0 so column headers remain visible when a section collapses.
    mark_header_collapsible: places an 'x' in the gutter (column A) on
    the header row, marking it as a collapse anchor for the data rows.

    Returns (list_of_row_xml, next_row_after_table).
    """
    out = [write_row(start_row, headers, styles=header_style,
                     start_col=start_col,
                     mark_collapsible=mark_header_collapsible)]
    if isinstance(col_styles, int):
        col_styles = [col_styles] * len(headers)
    elif len(col_styles) != len(headers):
        raise ValueError(
            f"col_styles length {len(col_styles)} != headers length "
            f"{len(headers)} - every column must have an explicit style"
        )

    for i, dr in enumerate(data_rows):
        if len(dr) > len(headers):
            raise ValueError(
                f"data row {i} has {len(dr)} values but table has "
                f"{len(headers)} headers - extra values would be silently "
                f"dropped; trim the row or add a header column"
            )
        padded = list(dr) + [None] * (len(headers) - len(dr))
        out.append(
            write_row(start_row + 1 + i,
                      padded,
                      styles=col_styles,
                      start_col=start_col,
                      outline_level=outline_level)
        )
    return out, start_row + 1 + len(data_rows)
