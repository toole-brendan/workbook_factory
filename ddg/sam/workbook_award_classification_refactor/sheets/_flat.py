"""_flat - shared single-table sheet builder for the flat data/model tabs.

Most tabs are flat tables: a header row + N data rows. They differ only in their
columns, widths, and which columns are numeric / date / derived, so they share one
builder here (one module per tab still declares its own config and calls this). The
result carries the house style: a row-2 title banner (the tab name), a §1 section
banner, an underlined header row, collapsible data rows, sized columns, and a
native filterable Excel table.

Three kinds of column live on these sheets:
  - text (default)  -> raw string (S_DEFAULT); identifiers that merely look numeric
    (Work-type ID "01", CAGE "07482", NAICS "335312") keep their exact string form.
  - hardcoded source -> blue input font. A column named in `input_cols` is a leaf
    SOURCE value: numeric/date -> S_NUM_INPUT / S_INT_INPUT / S_DATE_INPUT; a text
    key (e.g. the Subawardee UEI identity) -> S_TEXT_INPUT (blue text, the one place
    the workbook colors a text cell - see _text_input.py).
  - derived -> a live formula. A column named in `formula_cols` carries a
    `fn(row)->"=..."` callable (resolved per row by the RowCursor) and renders
    black (S_NUM / S_INT / S_DATE) - an aggregation, not a hardcoded value.
    A formula column also named in `link_cols` instead renders GREEN (the
    cross-sheet-link styles S_LINK_INT / S_DATE_LINK): use it for roll-ups that
    surface a value living on another sheet (a count, a min/max date), as opposed
    to a genuinely new aggregate like a SUMIFS total. link_cols applies to numeric
    and date columns only - text columns always render default black.

Column TYPE is declared via int_cols / float_cols / pct_cols / date_cols (controls
coercion + number format; pct_cols carry a decimal rendered as a percent via S_PCT).
A column with no type is text. `make_flat_sheet` returns
(SheetEntry, cols): `cols(header)` gives the absolute range "'Tab'!$X$f:$X$l" of
that column's data, so a derived sheet's formulas can reference this sheet's leaf
ranges (the data_lane_vendors -> model_by_vendor pattern).
"""
from __future__ import annotations

import re

from workbook_core.primitives import col_letter, worksheet
from workbook_core.styles import (
    S_DEFAULT, S_INT, S_INT_INPUT, S_NUM, S_NUM_INPUT, S_DATE, S_DATE_INPUT,
    S_LINK_INT, S_LINK_NUM, S_DATE_LINK, S_PCT, S_PCT_INPUT, S_LINK_PCT,
)
from workbook_award_classification_refactor.sheets._text_input import S_TEXT_INPUT
from workbook_award_classification_refactor.sheets._inputfill import (
    S_NUM_INPUT_FILL, S_INT_INPUT_FILL, S_DATE_INPUT_FILL, S_TEXT_INPUT_FILL,
)
from workbook_core.tables import ExcelTable, WorksheetSpec, SheetEntry
from workbook_core.notes import ExcelNote
from workbook_core.groups import group_color
from workbook_award_classification_refactor.sheets._layout import RowCursor
from workbook_award_classification_refactor.sheets._cuts import (
    load_table, load_headers, as_int, as_float, cell, date_serial,
)
from workbook_award_classification_refactor.sheets._widths import header_styles

# type key -> (derived/black style, input/blue style, link/green style)
_STYLE_BY_TYPE = {
    "int":   (S_INT, S_INT_INPUT, S_LINK_INT),
    "float": (S_NUM, S_NUM_INPUT, S_LINK_NUM),
    "pct":   (S_PCT, S_PCT_INPUT, S_LINK_PCT),
    "date":  (S_DATE, S_DATE_INPUT, S_DATE_LINK),
}

# type key -> pale-yellow FILLED input style, used only when a sheet opts in via
# input_fill=True (the curated INPUTS-group levers). Mirrors the blue input styles
# above with the FFF2CC fill added (see _inputfill.py).
_INPUT_FILL_BY_TYPE = {
    "int":   S_INT_INPUT_FILL,
    "float": S_NUM_INPUT_FILL,
    "date":  S_DATE_INPUT_FILL,
}


class Cols:
    """Column accessor for a flat sheet's DATA region, returned by make_flat_sheet.

    Back-compatible callable: ``cols(header)`` still yields the full absolute data
    range ``'Tab'!$X$first:$X$last`` (the data_lane_vendors -> model_by_vendor
    pattern). The extra methods let a consuming module reference this sheet
    positionally WITHOUT hardcoding column letters in Python (the generated Excel is
    still positional A1):
      - ``letter(h)``        -> bare column letter, e.g. ``"M"``
      - ``cell(h, row)``     -> single absolute cell, e.g. ``'Tab'!$M$5``
      - ``range(h1, h2)``    -> multi-column data block, ``'Tab'!$M$first:$AA$last``
      - ``row_span(h1, h2, r)`` -> same-sheet horizontal span on one row, ``M5:AA5``
        (relative, no tab prefix - for an in-sheet =SUM(M5:AA5))
    ``first`` / ``last`` expose the data row bounds.
    """

    __slots__ = ("_tab", "_headers", "first", "last")

    def __init__(self, tab: str, headers: list, first: int, last: int):
        self._tab = tab
        self._headers = headers
        self.first = first
        self.last = last

    def letter(self, header: str) -> str:
        return col_letter(self._headers.index(header) + 1)   # +1 for the gutter (A)

    def __call__(self, header: str) -> str:
        c = self.letter(header)
        return f"'{self._tab}'!${c}${self.first}:${c}${self.last}"

    def cell(self, header: str, row: int) -> str:
        return f"'{self._tab}'!${self.letter(header)}${row}"

    def range(self, h1: str, h2: str) -> str:
        return (f"'{self._tab}'!${self.letter(h1)}${self.first}"
                f":${self.letter(h2)}${self.last}")

    def row_span(self, h1: str, h2: str, row: int) -> str:
        return f"{self.letter(h1)}{row}:{self.letter(h2)}{row}"


def flat_header_letters(csv_name: str = None, *, headers=None, note_from=None,
                        note_from_verbatim=None, extra_cols=()) -> dict:
    """{header: column letter} for the sheet make_flat_sheet WILL build, matching its column
    math: note-source columns dropped, extra_cols appended, gutter at A (so the first data
    column is B). Lets a module reference its OWN columns by NAME at build time (same-sheet
    self-references like the SWBS match-row or a Federal-FY column), before the post-build cols
    accessor exists - so no column letter is hardcoded in Python. Pass the SAME note_from /
    note_from_verbatim / extra_cols the make_flat_sheet call uses. Column source: the explicit
    `headers` list when given (a sheet whose rows come from a `table=` source rather than a CSV),
    else <csv_name>'s header."""
    base = list(headers) if headers is not None else load_headers(csv_name)
    drop = set((note_from or {}).values()) | set((note_from_verbatim or {}).values())
    cols = [h for h in base if h not in drop] + list(extra_cols)
    return {h: col_letter(i + 1) for i, h in enumerate(cols)}   # +1 for the gutter (A)


# --- Supplier Master match-row helpers --------------------------------------------------
# The Supplier Master carries one row per (Program x UEI) with a composite "Program|UEI" key.
# A consuming row matches it ONCE (sm_match_row) and then INDEXes that row's columns, instead
# of repeating a two-criteria array search for each attribute - one MATCH + N INDEX, not N
# array MATCHes. Within the Supplier Master, the override-first archetype is resolved from two
# one-per-row match-row helpers (override_or_map) rather than a long nested INDEX/MATCH.

def sm_match_row(key_expr: str, sm_key_range: str) -> str:
    """The Supplier Master MATCH done once per consuming row, on the composite 'Program|UEI'
    key: 0 if not found (the build-time universe guard makes that impossible), else the matched
    row index."""
    return f"=IFERROR(MATCH({key_expr},{sm_key_range},0),0)"


def sm_text(match_cell: str, ret_range: str, empty: str = "-") -> str:
    """A dimension column resolved from the SM match-row: `empty` if unmatched OR the SM cell
    is blank (so INDEX-of-blank never renders as 0), else the Supplier Master value."""
    idx = f"INDEX({ret_range},{match_cell})"
    return f'=IF({match_cell}=0,"{empty}",IF({idx}="","{empty}",{idx}))'


def sm_value(match_cell: str, ret_range: str, default: str) -> str:
    """A resolved code/label from the SM match-row (the SM column always carries a value, e.g.
    the resolved D0 / P0), so no blank guard - just `default` when unmatched."""
    return f'=IF({match_cell}=0,"{default}",INDEX({ret_range},{match_cell}))'


def override_or_map(ov_match: str, ov_ret: str, naics_match: str, naics_ret: str,
                    default: str) -> str:
    """Override-first resolved archetype CODE (Supplier Master), AXIS-SPECIFIC: use the
    (UEI x Program) override only when it matched AND this axis's override cell is non-blank
    (an override row may set D but leave P blank - INDEX of a blank cell is numeric 0, not a
    valid P code), else the NAICS-6 map if matched, else `default` (D0 / P0). The MATCHes are
    hoisted to one per-row helper column each, so this stays a short IF/INDEX.

    AND does not short-circuit, so the override INDEX is evaluated even when ov_match=0; guard its
    index with MAX(.,1) so it never becomes INDEX(range,0) - which returns the whole column and,
    in a scalar context on a row OUTSIDE the override range, fails by implicit intersection
    (#VALUE!) on recalc. The guarded value is irrelevant there since AND's first arg is already
    FALSE; the THEN branch keeps the bare ov_match (only reached when ov_match>0)."""
    cond_idx = f"INDEX({ov_ret},MAX({ov_match},1))"
    ov_idx = f"INDEX({ov_ret},{ov_match})"
    return (f'=IF(AND({ov_match}>0,{cond_idx}<>""),{ov_idx},'
            f'IF({naics_match}>0,INDEX({naics_ret},{naics_match}),"{default}"))')


def override_or_map_basis(ov_match: str, ov_ret: str, naics_match: str) -> str:
    """The basis-tier label paired with override_or_map, AXIS-SPECIFIC (takes this axis's
    override range so the override-cell-blank case falls through to the map): 'Research
    override' / 'NAICS-6 map' / 'Unresolved'. Same MAX(.,1) index guard as override_or_map so the
    non-short-circuiting AND never evaluates INDEX(range,0) on an out-of-range row (#VALUE!)."""
    cond_idx = f"INDEX({ov_ret},MAX({ov_match},1))"
    return (f'=IF(AND({ov_match}>0,{cond_idx}<>""),"Research override",'
            f'IF({naics_match}>0,"NAICS-6 map","Unresolved"))')


def swbs_match_row(builder_cell: str, code_cell: str, code_key: str,
                   eligible: str = "HII-Ingalls") -> str:
    """The crosswalk MATCH done ONCE per transaction: 0 for a non-HII-Ingalls (out-of-
    scope) row or an HII row whose code is absent from the crosswalk, else the matched
    row index. The three SWBS outputs then INDEX on this helper instead of each
    repeating the same MATCH (3x -> 1x over the ~6.4k DDG transactions)."""
    return (f'=IF({builder_cell}<>"{eligible}",0,'
            f'IFERROR(MATCH({code_cell},{code_key},0),0))')


def swbs_from_row(builder_cell: str, match_cell: str, ret_range: str,
                  eligible: str = "HII-Ingalls", na: str = "", unmapped: str = "U00") -> str:
    """An SWBS output column (subsystem / display / basis) resolved from the shared match-row
    helper (swbs_match_row): `na` for a non-HII-Ingalls row, `unmapped` for an HII row whose
    code did not match (match=0), else INDEX the crosswalk return column at the matched row -
    the Builder-gated lookup, but driven off the one-per-row match so there is no second MATCH."""
    idx = f"INDEX({ret_range},{match_cell})"
    return (f'=IF({builder_cell}<>"{eligible}","{na}",'
            f'IF({match_cell}=0,"{unmapped}",{idx}))')


_NOTE_SPLIT = re.compile(r"[\s|;]+")


def _note_text(raw: str) -> str:
    """Normalize a Source-URLs cell into one URL per line for a hover Note.

    The CSV mixes separators (newline, ' | ', '; '), so split on any whitespace /
    pipe / semicolon run, keep the http(s) tokens, and strip trailing punctuation.
    When a cell carries no URL but does hold text (e.g. a 'No reliable public source
    located' annotation), fall back to that text verbatim so the value is not lost
    when the Source-URLs column is dropped. Returns "" only for an empty cell."""
    s = str(raw or "").strip()
    urls = [t.rstrip(".,);") for t in _NOTE_SPLIT.split(s) if t.startswith("http")]
    if urls:
        return "\n".join(urls)
    return " ".join(s.split())


def _note_verbatim(raw: str) -> str:
    """Note text used as-is (internal newlines preserved, ends trimmed) — for a
    pre-composed note like the archetype Basis evidence (reasoning + sources already
    laid out by build_program_vendors). Returns "" for an empty cell."""
    return str(raw or "").strip()


def make_flat_sheet(*, tab: str, group: str, csv_name: str, table_name: str,
                    banner: str, widths: list, intro=None, int_cols=(),
                    float_cols=(), pct_cols=(), date_cols=(), input_cols=(),
                    input_fill=False, formula_cols=None, link_cols=(), note_from=None,
                    note_from_verbatim=None, right_spacer=False, extra_cols=(),
                    hidden_headers=(), display_headers=None, table=None):
    """Build a single-table sheet from extracted/<csv_name>.csv.

    Returns (SheetEntry, cols) where cols(header) -> "'Tab'!$Col$first:$Col$last".

    input_fill: when True, the input_cols cells render on a pale-yellow fill (the
    filled clones in _inputfill.py) instead of blue font alone - the "mark your
    inputs" treatment, reserved for the curated INPUTS-group LEVER sheets (NAICS map,
    overrides, crosswalk, deflators). Leave it OFF for the data-group source spines
    and model-group identity keys: their input_cols are evidence leaves, not editable
    levers, and filling thousands of rows would defeat the highlight.

    extra_cols: optional list of column HEADERS appended after the CSV columns. They
    live only in the rendered sheet (no CSV cell), so each MUST carry a formula in
    formula_cols (and declare its type via int_cols/float_cols/date_cols). Use it to
    push a derived measure or a match-row helper to the fact grain WITHOUT
    regenerating the extracted CSV. `widths` must include these columns.

    intro: optional italic one-line orientation caption written immediately under
    the row-2 title banner (the Taxonomy-tab house pattern: title banner -> italic
    caption -> two blank rows -> §1 section banner). When omitted the sheet keeps
    the bare title-banner -> one-blank -> banner spacing.

    note_from: optional {anchor_header: source_header} map. Each source column is
    DROPPED from the visible table and its per-row value is normalized (one URL per
    line) into a native Excel Note anchored on the anchor column's cell — used to
    fold a Source-URLs column into hover notes on the prose it supports. Rows whose
    source cell is empty get no note. `widths` must match the columns that REMAIN
    after the source columns are dropped.

    note_from_verbatim: same contract as note_from, but the note text is used
    as-is (newlines preserved, no URL extraction) — for pre-composed evidence notes
    like the archetype Basis reasoning + sources. Source columns named here are also
    dropped; an anchor must not appear in both maps (one Note per cell).

    right_spacer: when True, write a single-space cell in the column immediately
    right of the table on every DATA row (no header, no banner extension, not part
    of the table). It is a fake spacer column whose only job is to clip a long final
    text column (e.g. Role / Description) so its overflow stops instead of running
    on across the empty grid.

    hidden_headers: optional set of column HEADERS to hide from the reader. The
    column stays in the grid (its width slot is emitted with hidden="1") so any
    A1 formula that references it keeps working - used to tuck a formula-helper
    column (a match-row index, a join key) out of sight without breaking the
    lookups built on it.

    display_headers: optional {canonical_header: shown_label} map. The header CELL
    and the native-table column name render the shorter label, while the internal
    `headers` list (formula lookups, the cols accessor, note anchors, CSV identity)
    keeps the canonical name - so a visible header can be shortened without
    re-pointing any formula. Aliased labels must stay unique within the sheet.
    """
    note_from = dict(note_from or {})
    note_from_verbatim = dict(note_from_verbatim or {})
    # (anchor header, source header, mode): URL-normalized vs verbatim note text.
    note_specs = ([(a, s, "url") for a, s in note_from.items()]
                  + [(a, s, "verbatim") for a, s in note_from_verbatim.items()])
    # Row source: an explicit (headers, rows) `table` when given - a sheet whose rows are built
    # in-memory (e.g. the program-vendor sheets, filtered from the Supplier Master dimension)
    # rather than read from extracted/<csv_name>.csv - else load that CSV.
    headers, rows = table if table is not None else load_table(csv_name)
    # Columns consumed into Notes are dropped from the visible table; capture their
    # original positions first so each row's source value can be read after the drop.
    for anchor, src, _mode in note_specs:
        if anchor not in headers:
            raise ValueError(f"{csv_name}: note anchor column {anchor!r} not found")
        if src not in headers:
            raise ValueError(f"{csv_name}: note source column {src!r} not found")
    drop = {src for _a, src, _m in note_specs}
    src_orig = {src: headers.index(src) for src in drop}
    keep = [j for j, h in enumerate(headers) if h not in drop]
    headers = [headers[j] for j in keep]
    n_csv = len(headers)                    # columns sourced from the CSV (after drop)
    headers = headers + list(extra_cols)    # sheet-only computed columns appended after
    ncols = len(headers)
    if len(widths) != ncols:
        raise ValueError(
            f"{csv_name}: {len(widths)} widths != {ncols} columns ({headers})")
    int_cols, float_cols, date_cols = set(int_cols), set(float_cols), set(date_cols)
    pct_cols = set(pct_cols)
    input_cols = set(input_cols)
    link_cols = set(link_cols)
    hidden_headers = set(hidden_headers)
    display_headers = dict(display_headers or {})
    bad_hidden = hidden_headers - set(headers)
    if bad_hidden:
        raise ValueError(f"{csv_name}: hidden_headers not in columns: {sorted(bad_hidden)}")
    bad_display = set(display_headers) - set(headers)
    if bad_display:
        raise ValueError(f"{csv_name}: display_headers not in columns: {sorted(bad_display)}")
    formula_cols = dict(formula_cols or {})
    missing_fx = [h for h in extra_cols if h not in formula_cols]
    if missing_fx:
        raise ValueError(f"{csv_name}: extra_cols without a formula: {missing_fx}")
    numeric = int_cols | float_cols | pct_cols | date_cols   # centered headers

    def _type(h: str):
        if h in int_cols:
            return "int"
        if h in float_cols:
            return "float"
        if h in pct_cols:
            return "pct"
        if h in date_cols:
            return "date"
        return None

    def _style(h: str) -> int:
        t = _type(h)
        if t is None:
            # text: blue (or pale-yellow filled, when input_fill) for a hardcoded
            # source key (input_cols), else black
            if h in input_cols:
                return S_TEXT_INPUT_FILL if input_fill else S_TEXT_INPUT
            return S_DEFAULT
        derived, inp, link = _STYLE_BY_TYPE[t]
        if h in link_cols:
            return link             # cross-sheet link surfaced green (override)
        if h in formula_cols:
            return derived          # live aggregation -> black
        if h in input_cols:
            # hardcoded source -> blue, or pale-yellow filled when the sheet opts in
            # (.get: no pale-yellow pct fill exists, so a pct input falls back to blue)
            return _INPUT_FILL_BY_TYPE.get(t, inp) if input_fill else inp
        return derived             # typed leaf without an input flag -> black

    col_styles = [_style(h) for h in headers]

    def convert(j: int, raw: str):
        h = headers[j]
        if h in formula_cols:
            return formula_cols[h]   # callable; RowCursor.write resolves per row
        t = _type(h)
        if t == "int":
            return as_int(raw)
        if t in ("float", "pct"):       # a percent is stored as a decimal, formatted by S_PCT
            return as_float(raw)
        if t == "date":
            return date_serial(raw)
        return cell(raw)

    # anchor header -> its spreadsheet column letter (gutter at A, so +1)
    anchor_letter = {a: col_letter(headers.index(a) + 1)
                     for a, _s, _m in note_specs}
    notes: list[ExcelNote] = []

    # When leading columns are hidden (e.g. a hidden join Key in column B), the banner
    # and caption text must move to the first VISIBLE content column or they vanish
    # behind the zero-width hidden column. Content columns are 1-based here (gutter
    # A = 0, first content column B = 1); the first visible one is the first non-hidden
    # header. With no hidden lead this is 1, so every other sheet is unchanged.
    first_visible_col = next((i + 1 for i, h in enumerate(headers)
                              if h not in hidden_headers), 1)

    c = RowCursor(2)
    c.title(tab, ncols, text_col=first_visible_col)
    if intro:
        c.caption(intro, start_col=first_visible_col)
        c.blank(2)
    else:
        c.blank()
    c.section(banner, ncols, text_col=first_visible_col)
    c.blank()
    # Fake spacer column (one cell right of the table) appended to data rows only -
    # no header cell, so the banner/header still span B..last and the table_ref does
    # not include it.
    spacer_vals = [" "] if right_spacer else []
    spacer_sty = [S_DEFAULT] if right_spacer else []

    # Visible header labels: display alias where given, canonical name otherwise.
    # `headers` (canonical) still drives every formula lookup / cols accessor;
    # only the rendered cell + the native-table column name use the alias.
    display = [display_headers.get(h, h) for h in headers]
    hdr = c.write(display, styles=header_styles(headers, center_headers=numeric))
    for row in rows:
        # CSV columns read their cell; extra (sheet-only) columns get "" and resolve to
        # their formula in convert(). `j < n_csv` short-circuits before indexing keep[].
        vals = [convert(j, row[keep[j]] if (j < n_csv and keep[j] < len(row)) else "")
                for j in range(ncols)]
        rownum = c.write(vals + spacer_vals, styles=col_styles + spacer_sty)
        for anchor, src, mode in note_specs:
            j = src_orig[src]
            raw = row[j] if j < len(row) else ""
            text = _note_verbatim(raw) if mode == "verbatim" else _note_text(raw)
            if text:
                notes.append(
                    ExcelNote(ref=f"{anchor_letter[anchor]}{rownum}", text=text))
    first, last = hdr + 1, hdr + len(rows)
    table_ref = f"B{hdr}:{col_letter(ncols)}{last}"

    cols = Cols(tab, headers, first, last)

    # Hidden formula-helper columns: keep their width slot but mark hidden so the
    # reader never sees them while the A1 refs built on them stay valid.
    cols_spec = [({"width": w, "hidden": True} if headers[i] in hidden_headers else w)
                 for i, w in enumerate(widths)]

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=cols_spec, tab_color=group_color(group),
                       with_gutter=True, show_outline_symbols=False)
        return WorksheetSpec(ws, tables=[
            ExcelTable(name=table_name, ref=table_ref, headers=display)],
            notes=notes)

    return SheetEntry(tab, group, render), cols
