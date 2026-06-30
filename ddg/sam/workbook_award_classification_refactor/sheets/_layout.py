"""_layout - a local row cursor for the consolidated sheet modules.

Adapted (copy-from, per the workbook_core "snippets stay copy-from" principle) from
the RowCursor snippet in workbook_core/sheet_snippets.md. It lives inside
workbook_award_analysis so the shared engine stays untouched; it just composes the
workbook_core primitives (banner_row / write_row / total_row).

A cursor tracks the next row as you append, so blocks compose without off-by-one
math and the 1/1/2 spacing rhythm (sheet_guide.md "Row spacing rhythm") reads as
`c.blank()` / `c.blank(2)`. Every emitting method RETURNS the row it wrote, so a
producer captures load-bearing positions straight from the writing call:

    c = RowCursor(4)
    pos["coeff"] = c.write(["BC coeff", f"={x}"], styles=[S_DEFAULT, S_LINK_PCT])
    ...
    def bc_coeff_cell(): return f"'{TAB}'!C{pos['coeff']}"

This keeps the safety invariant "the accessor row derives from the same value used
to write the row" structural - there is no second literal to drift.

Self-referential formulas (a cell whose formula names its own row, e.g.
`=C{r}+D{r}` or `=1-SUM(E47:E53)`) are written by passing a CALLABLE in the values
list; the cursor calls it with the row it just assigned:

    c.write([name, f"={obs}", 0, lambda r: f"=C{r}+D{r}"], styles=[...])

Content lives in columns B+ (gutter mode); start_col defaults to 1 and banners use
with_gutter=True, matching every consolidated sheet.
"""
from __future__ import annotations

from workbook_core.primitives import banner_row, write_row, total_row
from workbook_core.primitives import row as _blank_row
from workbook_core.styles import (S_TITLE_SHEET, S_TITLE_SECTION,
                                  S_TITLE_SUBSECTION)

from ._italic import S_ITALIC


def _resolve(values: list, r: int) -> list:
    """Replace any callable in `values` with its result called on the row `r`."""
    return [v(r) if callable(v) else v for v in values]


class RowCursor:
    """Tracks the next row as you append. Start at 2 (row 1 is the gutter blank).

    Named anchors: pass ``mark="name"`` to any emit method to record the row it
    wrote into ``self.marks``; read it back with ``marked("name")``. A producer
    that exposes positions to another sheet (e.g. domain_concentration's
    ``domain_conc_range`` accessor) tags the load-bearing rows AS IT WRITES THEM
    and the accessor reads the captured value - so the cross-sheet range derives
    from the same row the cursor actually emitted, with no parallel hand-counted
    layout constant that can drift (the Cols invariant, for hand-built sheets).

    Outline hierarchy (whole-sheet collapse). The cursor also maintains a running
    "detail level" so a sheet builds a deliberate nested outline without each call
    passing outline_level by hand:

        title(0)      -> caption / section-banners / spacer blanks at level 1
        section(1)    -> its header / data / total / subsection-banners at level 2
        subsection(2) -> its detail at level 3

    Calling title/section/subsection emits the banner at its own level and then
    bumps the running detail level for the rows that follow; write/total/blank
    default to that level. With showOutlineSymbols on, Excel renders one '+'/'-'
    control per group: the row-2 title folds the whole sheet, each section folds
    its body, each subsection folds its detail.
    """

    def __init__(self, start: int = 2):
        self.r = start
        self.rows: list[str] = []
        self.marks: dict[str, int] = {}
        self._detail = 0  # running outline level for write/total/blank

    def at(self) -> int:
        """The row the next emit will use."""
        return self.r

    def marked(self, name: str) -> int:
        """The row recorded under `name` by a prior emit's mark= (KeyError if absent)."""
        return self.marks[name]

    def banner(self, text: str, n_cols: int, *, style: int,
               mark: str | None = None, **kw) -> int:
        """Emit a full-width banner (gutter mode). Returns its row."""
        r0 = self.r
        self.rows.append(banner_row(r0, text, n_cols=n_cols, style=style,
                                    with_gutter=True, **kw))
        if mark is not None:
            self.marks[mark] = r0
        self.r += 1
        return r0

    def title(self, text: str, n_cols: int, *, text_col: int = 1) -> int:
        """Row-2 sheet title (outline level 0); detail below becomes level 1.

        text_col places the banner label in a specific content column (default the
        first, B); pass the first VISIBLE column when leading columns are hidden."""
        r0 = self.banner(text, n_cols, style=S_TITLE_SHEET,
                         mark_collapsible=True, outline_level=0, text_col=text_col)
        self._detail = 1
        return r0

    def caption(self, text: str, *, style: int = S_ITALIC, start_col: int = 1) -> int:
        """Row-3 italic caption, at the current detail level (1 under a title).

        start_col places the caption text in a specific content column (default the
        first, B); pass the first VISIBLE column when leading columns are hidden."""
        return self.write([text], styles=[style], start_col=start_col)

    def section(self, text: str, n_cols: int, *, text_col: int = 1) -> int:
        """Section banner (outline level 1); its body becomes level 2.

        text_col: see title() - the content column the banner label is written into."""
        r0 = self.banner(text, n_cols, style=S_TITLE_SECTION,
                         mark_collapsible=True, outline_level=1, text_col=text_col)
        self._detail = 2
        return r0

    def subsection(self, text: str, n_cols: int) -> int:
        """Subsection banner (outline level 2); its detail becomes level 3."""
        r0 = self.banner(text, n_cols, style=S_TITLE_SUBSECTION,
                         mark_collapsible=True, outline_level=2)
        self._detail = 3
        return r0

    def write(self, values: list, *, styles, start_col: int = 1,
              mark: str | None = None, **kw) -> int:
        """Emit one content row. Callable values are resolved against the row.

        Returns the row written. `mark` records that row under the given name.
        The row's outline level defaults to the cursor's running detail level
        (set by the most recent title/section/subsection); pass outline_level=
        to override.
        """
        r0 = self.r
        kw.setdefault("outline_level", self._detail)
        self.rows.append(write_row(r0, _resolve(values, r0), styles=styles,
                                   start_col=start_col, **kw))
        if mark is not None:
            self.marks[mark] = r0
        self.r += 1
        return r0

    def total(self, values: list, *, styles, n_cols: int, start_col: int = 1,
              mark: str | None = None, **kw) -> int:
        """Emit a total/subtotal divider via total_row(). Pass BASE styles.

        Callable values are resolved against the row. Returns the row written;
        `mark` records that row under the given name. Outline level defaults to
        the cursor's running detail level (override with outline_level=).
        """
        r0 = self.r
        kw.setdefault("outline_level", self._detail)
        self.rows.append(total_row(r0, _resolve(values, r0), styles=styles,
                                   n_cols=n_cols, start_col=start_col, **kw))
        if mark is not None:
            self.marks[mark] = r0
        self.r += 1
        return r0

    def feed(self, rows_xml: list[str], next_row: int) -> None:
        """Splice in pre-built rows (e.g. build_table output) and jump to next_row.

        Use when a helper returns (rows_xml, next_row); the cursor adopts the rows
        and continues from next_row so later positions stay consistent.
        """
        self.rows.extend(r for r in rows_xml if r)
        self.r = next_row

    def blank(self, n: int = 1, *, outline_level: int | None = None) -> None:
        """Advance past n blank rows.

        Inside an outlined sheet (detail level > 0) the blank rows are EMITTED
        as empty `<row outlineLevel=.../>` so they don't interrupt the group's
        contiguous run (an absent row is an implicit level-0 row, which would
        split the outline). At level 0 nothing is emitted, exactly as before.
        """
        lvl = self._detail if outline_level is None else outline_level
        for _ in range(n):
            if lvl:
                self.rows.append(_blank_row(self.r, [], outline_level=lvl))
            self.r += 1
