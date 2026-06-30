# Sheet Snippets — copy-from sheet builders (shared, both programs)

Companion to `sheet_base_template.py` + `sheet_guide.md`. The template ships the
metadata block, the title banner, and an empty `_build_rows()`. **This file is the
menu of body builders** — copy the ones a sheet needs into that module as
file-private helpers (or paste the pattern straight into `_build_rows()`).

> **You are not tied to these snippets.** They are worked examples of the house
> conventions (the gutter skeleton, the `S_*` styles, formula-driven cells,
> cross-sheet accessors) — not a required toolkit. Compose rows directly, adapt a
> snippet, or write your own helpers. The only hard rules are the style rules and
> the locked skeleton in `sheet_guide.md`.

How to use:
- These are **copy-from**, not import. Keep each sheet self-contained — imports
  stay `from workbook_core.primitives import …` / `…styles import …` /
  `…tables import …`. Copies may diverge per sheet; that's intended.
- All content starts at column B (`start_col=1`); row 1 is the auto gutter blank.
- Deeper raw-OOXML mechanics live in `workbook_core/ooxml_cheat_sheet_xlsx.md`;
  the relevant section is named at the end of each snippet.

Contents: [module skeleton](#module-skeleton) · [row cursor](#row-cursor) ·
[section block](#section-block) · [styled-range table](#styled-range-table) ·
[model hierarchy block](#model-hierarchy-block) ·
[native Excel table](#native-excel-table) · [defined names](#defined-names) ·
[native Excel note](#native-excel-note) ·
[formula & ref helpers](#formula--ref-helpers) ·
[cross-sheet link & accessors](#cross-sheet-link--accessors) ·
[FY-columns series](#fy-columns-series) ·
[SUMPRODUCT coefficient](#sumproduct-coefficient) ·
[totals row](#totals-row) · [collapsible group](#collapsible-group) ·
[QA / reconciliation row](#qa--reconciliation-row) ·
[autofilter data dump](#autofilter-data-dump) ·
[data validation](#data-validation) ·
[conditional formatting](#conditional-formatting) ·
[worksheet feature order](#worksheet-feature-order) ·
[package recipe cards](#package-recipe-cards)

---

## module skeleton

The no-preset-name shape. `TAB_NAME = None` derives the tab from the filename;
`render()` returns a `WorksheetSpec`. Register modules (not tuples) in `SHEETS`.

```python
from __future__ import annotations
from workbook_core.primitives import worksheet, banner_row, write_row, build_table
from workbook_core.styles import (
    S_DEFAULT, S_HEADER_LEFT, S_NUM, S_NUM_INPUT, S_TITLE_SHEET, S_TITLE_SECTION,
)
from workbook_core.tables import WorksheetSpec
from workbook_core.groups import group_color

TAB_NAME = None                 # -> "My Sheet" from my_sheet.py
SHEET_GROUP = "model"           # tab color + tab-block order (groups.SHEET_GROUPS)
TAB_COLOR = group_color(SHEET_GROUP)
COLS = [40, 14, 14, 14]

def _tab_name() -> str:
    return TAB_NAME or __name__.rsplit(".", 1)[-1].replace("_", " ").title()

def _build_rows() -> list[str]:
    rows = [banner_row(2, _tab_name(), n_cols=len(COLS),
                       style=S_TITLE_SHEET, with_gutter=True)]
    # ... sections ...
    return rows

def render() -> WorksheetSpec:
    return WorksheetSpec(worksheet(_build_rows(), cols=COLS, tab_color=TAB_COLOR,
                                   with_gutter=True))
```

```python
# workbook_<prog>/sheets/__init__.py
from . import control_panel, budget_normalized, pop_coefficients, tam_model
SHEETS = [control_panel, budget_normalized, pop_coefficients, tam_model]
```

---

## row cursor

Hand-numbered rows drift when you insert a section. A cursor tracks the next row
so blocks compose without off-by-one math. Copy it in if a sheet has many
sections; simple sheets can keep literal row numbers.

```python
class RowCursor:
    """Tracks the next row as you append. Start at 2 (row 1 is the gutter blank)."""
    def __init__(self, start: int = 2):
        self.r = start
        self.rows: list[str] = []

    def at(self) -> int:
        return self.r

    def banner(self, text, n_cols, *, style, **kw) -> int:
        r0 = self.r
        self.rows.append(banner_row(r0, text, n_cols=n_cols, style=style,
                                    with_gutter=True, **kw))
        self.r += 1
        return r0

    def write(self, values, *, styles, start_col: int = 1, **kw) -> int:
        r0 = self.r
        self.rows.append(write_row(r0, values, styles=styles, start_col=start_col, **kw))
        self.r += 1
        return r0

    def blank(self, n: int = 1) -> None:
        self.r += n
```

```python
def _build_rows() -> list[str]:
    c = RowCursor()
    c.banner(_tab_name(), len(COLS), style=S_TITLE_SHEET)
    c.blank()
    c.banner("§1 - Run settings", len(COLS), style=S_TITLE_SECTION)
    c.write(["Setting", "Value"], styles=S_HEADER_LEFT)
    c.write(["FY range start", 2022],
            styles=[S_DEFAULT, S_NUM_INPUT])
    return c.rows
```

---

## section block

The repeating unit, encoding the spacing rhythm (sheet_guide.md → "Row spacing
rhythm"): section banner, **1** blank, header, body, then **2** blanks before the
next section. Returns the next section's banner row.

```python
def _section(rows: list[str], r: int, title: str, header: list[str],
             body: list[list], col_styles: list[int], n_cols: int) -> int:
    rows.append(banner_row(r, title, n_cols=n_cols, style=S_TITLE_SECTION,
                           with_gutter=True))
    rows.append(write_row(r + 2, header, styles=S_HEADER_LEFT, start_col=1))  # r+1 = 1 blank
    for i, dr in enumerate(body):
        rows.append(write_row(r + 3 + i, dr, styles=col_styles, start_col=1))
    return r + 3 + len(body) + 2   # 2 blank rows before the next section banner
```
Title each section banner `§N - <short label>` and sub-sections `§Na - <short
label>` (see sheet_guide.md → "Section numbering"); the `§N` doubles as a stable ID
for cross-references in note cells (e.g. `Calcs §1 row 11`). Sections don't need
sub-sections; where a dense section needs one, insert a `banner_row(...,
style=S_TITLE_SUBSECTION)` + 1 blank before its header/content.

---

## styled-range table

The lightweight default for model blocks: a header row + styled data rows.
Returns `(rows_xml, next_row)` — extend your list and keep the cursor.

```python
table_rows, next_row = build_table(
    5,
    headers=["Scenario", "Amount $M", "Rate", "Total $M"],
    data_rows=[
        ["Base",   100, 0.12, "=C6*D6"],
        ["Upside", 125, 0.15, "=C7*D7"],
    ],
    header_style=S_HEADER_LEFT,
    col_styles=[S_DEFAULT, S_NUM_INPUT, S_PCT_INPUT, S_NUM],
    start_col=1,
)
rows.extend(table_rows)
```
Cheat sheet: "Cells and values", "Formulas and recalculation".

---

## model hierarchy block

Parent line, indented components, flush-left total — the hand-built finance look.
Indent the *label column only* with `S_LABEL_INDENT_1`; the parent line and the
`total_row()` stay flush-left. This is a styled range (native tables stay flat
records). See sheet_guide.md → "Indentation & row hierarchy".

```python
rows.append(write_row(10, ["Revenue"], styles=[S_BOLD], start_col=1))
rows.append(write_row(11, ["Newbuild", 120.0, 150.0],
                      styles=[S_LABEL_INDENT_1, S_NUM_INPUT, S_NUM_INPUT], start_col=1))
rows.append(write_row(12, ["Modernization", 80.0, 95.0],
                      styles=[S_LABEL_INDENT_1, S_NUM_INPUT, S_NUM_INPUT], start_col=1))
rows.append(total_row(13, ["Total revenue", "=SUM(C11:C12)", "=SUM(D11:D12)"],
                      styles=[S_BOLD, S_NUM, S_NUM], n_cols=3, start_col=1))
```
Indent components, not peers — a scenario table (`Base`/`Upside`/`Downside`) is
flush-left records, not a parent→child block. Indentation is independent of
`outline_level` (collapsible groups, below). Cheat sheet: "Cells and values".

---

## native Excel table

A real ListObject (filter, structured refs, table style). Write the cells with
`build_table`, then attach an `ExcelTable` whose `ref` covers the **header + body**
range. The packager writes the table part, the sheet rels, and `<tableParts>`.

```python
from workbook_core.tables import WorksheetSpec, ExcelTable

HEADERS = ["Vendor", "UEI", "Subaward $M", "Bucket"]

def render() -> WorksheetSpec:
    rows = [banner_row(2, _tab_name(), n_cols=len(COLS), style=S_TITLE_SHEET,
                       with_gutter=True)]
    table_rows, _ = build_table(
        4, headers=HEADERS, data_rows=_DATA,
        header_style=S_HEADER_LEFT, col_styles=[S_DEFAULT, S_DEFAULT, S_NUM, S_DEFAULT],
        start_col=1,
    )
    rows.extend(table_rows)
    ws = worksheet(rows, cols=COLS, tab_color=TAB_COLOR, with_gutter=True)
    last = 4 + len(_DATA)                      # header row 4 + N body rows
    return WorksheetSpec(ws, tables=[ExcelTable(
        name="tbl_subawards",                  # workbook-unique, safe name
        ref=f"B4:E{last}",                     # cols B..E, header included
        headers=HEADERS,
    )])
```
Values live in the cells; the table part is metadata only. `ExcelTable` defaults to
the workbook's named no-format table style — don't pass `style=None` just to
suppress formatting; the default named style is what stops Excel from treating the
table as style-less and injecting a banded look on open/save. Pass a built-in style
(e.g. `TableStyleMedium2`) explicitly only when you want banding. Cheat sheet:
"Tables", "Wiring a table to a sheet".

---

## defined names

Publish a stable workbook-scoped name for a load-bearing cell. Attach to the spec.

```python
from workbook_core.primitives import sheet_ref

def render() -> WorksheetSpec:
    ws = worksheet(_build_rows(), cols=COLS, tab_color=TAB_COLOR, with_gutter=True)
    return WorksheetSpec(ws, defined_names={
        "portfolio_tam": sheet_ref("TAM Model", 8, 7),   # 'TAM Model'!$H$8
    })
```
Name rules: `[A-Za-z_][A-Za-z0-9_.]*`, not a cell-ref shape, not reserved
`_xlnm.*`. Sheet-scoped names use `localSheetId` = the zero-based sheet *position*
(not `sheetId`) — see cheat sheet "Defined names" → "localSheetId trap".

---

## native Excel note

A native Excel Note — the red-triangle / yellow hover card (not a threaded
comment). Use sparingly for optional hover detail on the value/headline cell it
explains (never a label cell or a note column); keep durable provenance in a table
/ Sources / Validation (see sheet_guide.md
→ "Native Excel Notes"). Declare notes on the `WorksheetSpec`; the packager wires
the comments part, VML drawing, sheet rels, content types, and the worksheet
`<legacyDrawing>`.

```python
from workbook_core.notes import ExcelNote

def render() -> WorksheetSpec:
    ws = worksheet(_build_rows(), cols=COLS, tab_color=TAB_COLOR, with_gutter=True)
    return WorksheetSpec(ws, notes=[
        ExcelNote("H8", "Full derivation / basis text…"),
        ExcelNote("H9", "Caveat or method detail…"),
    ])
```
Combine with tables / defined names normally:
`WorksheetSpec(ws, tables=[...], defined_names={...}, notes=[...])`. Refs are single
A1 cells (no ranges, no `$`), unique per sheet; text is plain (newlines preserved);
the default is a hidden hover note (`visible=False`) authored `"Model"`. The OOXML
mechanics live in `workbook_core/notes.py` — authors never hand-write them.

---

## formula & ref helpers

Build cross-sheet references with the helpers instead of hand-formatting strings.

```python
from workbook_core.primitives import qsheet, abs_ref, sheet_ref, range_ref, col_letter, cref

qsheet("SCN Annual")             # 'SCN Annual'   (always quoted; doubles apostrophes)
abs_ref(8, 7)                    # $H$8           (1-idx row, 0-idx col)
sheet_ref("TAM Model", 8, 7)     # 'TAM Model'!$H$8
range_ref("POP Location Parse", 6, 2, 40, 2)   # 'POP Location Parse'!$C$6:$C$40
cref(6, 2)                       # C6             (relative)
col_letter(7)                    # H
```
Reminder: write source formulas with a leading `=` (`"=SUM(...)"`); the emitted
`<f>` has it stripped. Cheat sheet: "Cross-sheet formulas", "Formulas".

---

## cross-sheet link & accessors

Two halves of the contract. **Producer**: expose an accessor returning an absolute
ref to the rendered cell. **Consumer**: link with a green `S_LINK_*` style.

```python
# producer sheet (e.g. pop_coefficients.py) — keep TAB_NAME and the accessor in sync
TAB_NAME = "POP Coefficients"
_VAL = 2   # column C (0-indexed)

def bc_supplier_coeff_cell() -> str:
    """'POP Coefficients'!C6 — the BC-stream supplier coefficient."""
    return f"{qsheet(TAB_NAME)}!{col_letter(_VAL)}6"
```

```python
# consumer sheet (e.g. tam_model.py)
from workbook_<prog>.sheets.pop_coefficients import bc_supplier_coeff_cell as _bc_coeff

# pure link cell -> green S_LINK_NUM (numbers) / S_LINK_PCT (percentages)
rows.append(write_row(6, ["BC coeff", f"={_bc_coeff()}"],
                      styles=[S_DEFAULT, S_LINK_PCT], start_col=1))

# or used inside a derived formula (stays black S_NUM — it's computed, not a pure link)
b = _bc_base(2122, fy)            # accessor from budget_normalized
rows.append(write_row(7, ["BC TAM", f'=IF(N({b})=0,"",N({b})*N({_bc_coeff()}))'],
                      styles=[S_DEFAULT, S_NUM], start_col=1))
```
Use `N(...)` to coerce a linked cell that may be blank. Cheat sheet:
"Cross-sheet formulas".

---

## FY-columns series

A fiscal-year row across columns. Map FY → column once, reuse for header + data +
accessors.

```python
_FY = [2022, 2023, 2024, 2025, 2026, 2027]
_FY_COL0 = 2   # first FY column = C (0-indexed 2); gutter 0, label 1 (B)

def _fy_col(fy: int) -> str:
    return col_letter(_FY_COL0 + _FY.index(fy))

# header + a derived per-FY row. The label header reads left; the FY headers
# read centered over their numeric columns (S_HEADER_CENTER).
rows.append(write_row(5, ["Stream"] + [str(fy) for fy in _FY],
                      styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(_FY), start_col=1))
vals = ["BC stream"] + [f'=IF(N({_bc_base(2122, fy)})=0,"",'
                        f'N({_bc_base(2122, fy)})*N({_bc_coeff()}))' for fy in _FY]
rows.append(write_row(6, vals, styles=[S_DEFAULT] + [S_NUM] * len(_FY), start_col=1))
```
For mixed header alignment like this, write the header row directly with
`write_row` (a style list). `build_table()` broadcasts a single `header_style` to
every column, so it can't mix `S_HEADER_LEFT` + `S_HEADER_CENTER` in one header.

---

## SUMPRODUCT coefficient

A $-weighted ratio over a parsed corpus, so it recalculates when the corpus
weights change. The producer sheet exposes column *ranges* as accessors.

```python
# corpus sheet exposes:  corpus_range(), supplier_flag_range(), bc_flag_range()
num = f"SUMPRODUCT({_supplier_flag_range()},{_bc_flag_range()},{_corpus_range()})"
den = f"SUMPRODUCT({_bc_flag_range()},{_corpus_range()})"
rows.append(write_row(6, ["BC supplier coeff", f"=IF({den}=0,0,{num}/{den})", "SUMPRODUCT/SUMPRODUCT"],
                      styles=[S_DEFAULT, S_PCT, S_DEFAULT], start_col=1))
```

```python
# the range accessor on the corpus sheet (absolute, so it survives row inserts)
def corpus_range() -> str:
    return range_ref(TAB_NAME, _FIRST, _DOLLAR_COL, _LAST, _DOLLAR_COL)
```

---

## totals row

Use `total_row()` for any subtotal/total divider. The medium top border draws
per-cell, so a continuous rule needs every cell of the row to carry a bordered
style - `total_row()` guarantees that: it upgrades each style you pass to its
bordered variant (`S_BOLD`→`S_TOTAL`, `S_NUM`→`S_NUM_TOTAL`, `S_DEFAULT`→
`S_BORDER_TOP`, …) and pads the row out to `n_cols` with bordered blank cells, so
the line spans the full block width even past the last value. Pass the plain BASE
styles and the block's content width (the same `n_cols` you give `banner_row`).

```python
tot = ["Portfolio TAM"] + [f"=N({_fy_col(fy)}6)+N({_fy_col(fy)}7)" for fy in _FY]
rows.append(total_row(8, tot, styles=[S_BOLD] + [S_NUM] * len(_FY),
                      n_cols=1 + len(_FY), start_col=1))
```

Do **not** hand-assemble a total via `write_row` with a mix of `S_BOLD`/`S_DEFAULT`
and `*_TOTAL` styles - a bare label or spacer cell leaves a gap in the border line.

---

## collapsible group

Outline a section so a reviewer can collapse detail. The banner is the anchor
(`mark_collapsible=True` puts a neutral `x` in the gutter); body rows take
`outline_level=1`.

```python
rows.append(banner_row(4, "§1 - Run settings", n_cols=n_cols, style=S_TITLE_SECTION,
                       with_gutter=True, mark_collapsible=True))
for i, (label, value, note) in enumerate(_SETTINGS):
    rows.append(write_row(6 + i, [label, value, note],
                          styles=[S_DEFAULT, S_NUM_INPUT, S_DEFAULT],
                          start_col=1, outline_level=1))
```
Level-0 rows (banners, totals) stay visible when the group collapses. Use the gutter
`x` only for a real outline anchor — don't mark an ordinary section banner with `x`
unless its body rows are actually outlined (`outline_level=1`). Cheat sheet:
"Sparse grid rules" / outline attributes.

---

## QA / reconciliation row

One row per invariant: the two sides of an identity, a delta, an OK/FAIL flag.
All-OK is the build's green light.

```python
r = 5
lhs = f"N({_sam_broad()})"
rhs = f"N({_tam_total()})"
rows.append(write_row(
    r, ["SAM_broad <= TAM", f"={lhs}", f"={rhs}", f"=C{r}-D{r}",
        f'=IF(C{r}<=D{r}+0.5,"OK","FAIL")'],
    styles=[S_DEFAULT, S_NUM, S_NUM, S_NUM, S_BOLD], start_col=1))
```
The `+0.5` is a rounding tolerance; tighten/loosen per check.

---

## autofilter data dump

A research/source dump with filter dropdowns on the header row. Either use a
native table (above) or a plain `autoFilter`:

```python
from workbook_core.primitives import filter_range
headers = ["PIID", "Vendor", "NAICS", "$M", "Scope"]
af = filter_range(headers, _DATA, start_row=4, start_col=1)   # e.g. "B4:F128"
ws = worksheet(rows, cols=COLS, tab_color=TAB_COLOR, with_gutter=True,
               auto_filter=af)
```

---

## data validation

A dropdown / constraint. Pass complete `<dataValidation>` elements to
`worksheet(data_validations=[...])` (it wraps them in `<dataValidations>`). Inline
list:

```python
dv_inline = ('<dataValidation type="list" allowBlank="1" showInputMessage="1" '
             'showErrorMessage="1" sqref="C6">'
             '<formula1>"Base,Upside,Downside"</formula1></dataValidation>')
ws = worksheet(rows, cols=COLS, tab_color=TAB_COLOR, with_gutter=True,
               data_validations=[dv_inline])
```
Cross-sheet list sources must go through a **defined name** (most compatible), not
a raw `Sheet!Range` in `<formula1>`. Cheat sheet: "Data validation".

---

## conditional formatting

Pass complete `<conditionalFormatting>` blocks to
`worksheet(conditional_formatting=[...])`. A `cellIs` rule references a `dxfId`
(a differential format — a separate index from the `S_*` cellXfs; it must exist in
`styles.xml`'s `<dxfs>`):

```python
cf = ('<conditionalFormatting sqref="F5:F40">'
      '<cfRule type="cellIs" operator="lessThan" dxfId="1" priority="1">'
      '<formula>0</formula></cfRule></conditionalFormatting>')
ws = worksheet(rows, cols=COLS, tab_color=TAB_COLOR, with_gutter=True,
               conditional_formatting=[cf])
```
`styles.py` reserves `dxfId=0` as the empty no-format table-style dxf; append your
CF `<dxf>` to `styles.DXFS` after it and reference the new index (`dxfId="1"` for
the first real CF format). Modern (x14) data bars/icons are an `<extLst>` feature;
treat as advanced. Cheat sheet: "Conditional formatting".

---

## worksheet feature order

`worksheet()` emits children in the schema-required order; if you ever hand-build a
worksheet, keep it:

```
sheetPr → (dimension) → sheetViews → sheetFormatPr → cols → sheetData →
autoFilter → conditionalFormatting → dataValidations → hyperlinks →
drawing → tableParts → extLst
```
Wrong order is the most common cause of an Excel "repair" dialog. `tableParts` is
injected by the packager (it owns the rIds). Cheat sheet: "Required child order
inside `<worksheet>`".

---

## package recipe cards

What each artifact touches (the packager does this for you; listed so you know
what a feature costs). Cheat sheet: "Recipes: what files must I touch?".

- **Native table** → worksheet `<tableParts>` + `xl/worksheets/_rels/sheetN.xml.rels`
  + `xl/tables/tableK.xml` + a `[Content_Types]` table override. (Attach an
  `ExcelTable`; the packager wires all four.)
- **Defined name** → a `<definedName>` in `xl/workbook.xml`. (Attach to
  `WorksheetSpec.defined_names`.)
- **Native Excel Note** → `xl/comments{i}.xml` + `xl/drawings/vmlDrawing{i}.vml`
  + worksheet rels + a worksheet `<legacyDrawing r:id>` + content-types (comments
  override + a `vml` Default). Attach `ExcelNote(...)` objects to
  `WorksheetSpec.notes`; the packager wires all parts (one comments + one VML part
  per note-bearing sheet, numbered by sheet index).
- **Data validation / conditional formatting** → a slot inside the worksheet only
  (`worksheet(data_validations=…/conditional_formatting=…)`); CF rules also need a
  `<dxf>` appended to `styles.DXFS` (after the reserved `dxfId=0` no-format
  table-style dxf), referenced as `dxfId="1"`+.
- **A new style** → append font/fill/border/numFmt + a `cellXfs` entry in
  `styles.py`, then add the `S_*` constant (3-step, see `styles.py` header).
