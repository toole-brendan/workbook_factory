# Session log — workbook_core named no-format table style

**Date:** 2026-06-01 (follow-up to `2026-06-01_workbook_core_hardening_human_standard.md`
and `2026-06-01_workbook_core_indentation_styling.md`)
**Scope:** `core/workbook_core/` (the xlsx build pipeline). No `deck_core` changes.
**Goal:** Replace the native-table `style="None"` strategy with a **named custom
no-format table style** shipped in `styles.xml`, referenced by every `ExcelTable`
by default. Driven by a proposal modeled on the SRT pipeline; adapted to current
core conventions (generic name, hardened `ooxml.py` import direction).

---

## 0. Why — the lesson

The prior hardening pass set native tables to `tableStyleInfo name="None"` (no
built-in overlay) and **deliberately left** `styles.xml`'s `defaultTableStyle` at
`TableStyleMedium2` with an empty `<dxfs count="0"/>` / `<tableStyles count="0">`.
That is close but not round-trip-safe: when a native table has **no durable named
style** to preserve, Excel can inject its own striped/banded default on open/save.
The stronger pattern: define one **named no-format table style** in `styles.xml`
(all table-style element slots pointed at a single empty `<dxf/>`), make it the
workbook default, and have every `ExcelTable` reference it. Same initial look as the
old `name="None"` (cell-level `S_*` styles remain the only visible formatting), but
Excel now has a legal named style to keep. **This supersedes the hardening log's
"defaultTableStyle left as TableStyleMedium2" decision.**

`style=None` (Python `None`) is retained but re-scoped: it now emits **no
`<tableStyleInfo>` at all** — reserved for low-level OOXML cases where the absence
is intentional, NOT as a way to "remove formatting" (the named style does that).

**Adapted from the proposal (did NOT copy the SRT files wholesale):** generic core
name `WorkbookCore_NoFormatTable` (not `SRT_NoFormatTable`); kept the hardened
import direction (`tables.py` imports XML constants from `ooxml.py`, not
`primitives`); kept `S_TITLE_SHEET` (the SRT files still use the old
`S_TITLE_SLIDE`); took only the table-style *pattern*, not the SRT palette.

---

## 1. Engine changes (code)

### New leaf module `workbook_core/table_style_names.py`
A no-import constants leaf (alongside `ooxml.py`) holding
`NO_FORMAT_TABLE_STYLE = "WorkbookCore_NoFormatTable"`, so `styles.py` (defines the
style) and `tables.py` (references it) share the literal without an import cycle.
Listed in the `__init__.py` layout map.

### `styles.py` — define the no-format style catalog
- Imports `NO_FORMAT_TABLE_STYLE`.
- New "Native-table style catalog" section: `DXFS = ["<dxf/>"]` (one empty
  differential format at **dxfId=0, reserved**) + `_TABLE_STYLE_ELEMENTS` (the 13
  table-style element types) + `_build_no_format_table_styles_xml()` which renders a
  single `<tableStyle name="WorkbookCore_NoFormatTable" pivot="0" table="1"
  count="13">` with every element pointed at `dxfId="0"`, inside `<tableStyles
  count="1" defaultTableStyle="WorkbookCore_NoFormatTable" …>`.
- `build_styles_xml()` now emits `<dxfs count="1"><dxf/></dxfs>` and the catalog
  (was `<dxfs count="0"/>` + `<tableStyles count="0" defaultTableStyle=
  "TableStyleMedium2">`). Schema order (`… cellStyles, dxfs, tableStyles`) unchanged.

### `tables.py` — default to the named style; re-scope `None`
- Imports `NO_FORMAT_TABLE_STYLE`; `DEFAULT_TABLE_STYLE = NO_FORMAT_TABLE_STYLE`
  (was the literal `"None"`), with a comment explaining round-trip robustness +
  the built-in / `None` escape hatches.
- `ExcelTable.style` typed `str | None` (was `str`); docstring updated.
- `build_table_part_xml()` emits `<tableStyleInfo …/>` only `if t.style`; `None`
  emits nothing. `show_row_stripes` default stays `False`.

### `lib.py` — one comment, no structural change
Added a note at the `styles.xml` write site: a native table depends on BOTH its
table part and `styles.xml` (which carries the referenced no-format style). All the
hardening (fail-fast names, validators, `ooxml.py`, `S_TITLE_SHEET`) is untouched.
No build-time "must use NO_FORMAT" assertion (it would wrongly reject legitimate
built-in / `None` styles).

---

## 2. Docs / template

- **`sheet_guide.md`** — "Native table visual discipline" rewritten: default is the
  **named** no-format style (not `style="None"`); a flat-record / ListObject
  contract, not decoration; explicit "use native tables for flat
  data/source/lookup/output-contract ranges, use `build_table()` for model /
  hierarchy / bridge / P&L / roll-forward blocks"; `style=None` is not a
  formatting-removal tool; built-in styles only for deliberate banding.
- **`sheet_snippets.md`** — native-table snippet gained a note (default named style;
  don't use `style=None` to suppress formatting). **dxfId reservation fix:** the
  conditional-formatting snippet now uses `dxfId="1"` (was `"0"`, which is now the
  reserved no-format dxf) and its note + the package recipe card explain that CF
  `<dxf>`s append to `styles.DXFS` after `dxfId=0`.
- **`sheet_base_template.py`** — `render()` docstring note: native tables default to
  the core no-format style; attach `ExcelTable` only for flat filterable ranges.
- **`ooxml_cheat_sheet_xlsx.md`** — left unchanged on purpose: its `<dxfs count="0">`
  / `defaultTableStyle="TableStyleMedium2"` lines are a *generic* vanilla-Excel
  `styles.xml` skeleton and a generic "dxfId=0 = first dxf" fact, not claims about
  what workbook_core emits.

---

## 3. Verification

- **`build_styles_xml()` re-baselined (intentional):** was **4614 bytes / sha1
  5110441d452b7aad6e487f2df236b519639384d5** (post-indentation), now **5436 bytes /
  sha1 81c1d20ad1476cb32066e08b0b30af2394b597e5**. Well-formed; `<dxfs count="1">`
  with one `<dxf/>`; `<tableStyles count="1" default=WorkbookCore_NoFormatTable>`
  with a 13-element `<tableStyle>` (count attr = actual = 13, every element
  `dxfId="0"`).
- Default `ExcelTable` emits `<tableStyleInfo name="WorkbookCore_NoFormatTable" …>`;
  `style=None` emits **no** `<tableStyleInfo>`. Both table parts well-formed;
  `validate_excel_table` accepts both.
- **End-to-end** `package_workbook()` with a native table builds a 10-part `.xlsx`;
  `xl/tables/table1.xml` references the named style, `xl/styles.xml` carries the
  `<tableStyle>` definition, and every emitted part parses as well-formed XML.
- **`sheet_probe`** reports `style: WorkbookCore_NoFormatTable` (module mode) with no
  code change (it reads `t.style` / the part's `tableStyleInfo` name).

**Environment:** `python` (3.14.4) on PATH; read-only checks + a temp-file build
(removed after), no mutations to real workbooks.

---

## 4. Deliberately NOT done
- No `lib.py` structural change and no build-time table-style assertion.
- `ooxml_cheat_sheet_xlsx.md` left as a generic OOXML reference (see §2).
- Did not copy the SRT files wholesale (see §0).

---

## 5. Files changed this session
- **Added:** `core/workbook_core/table_style_names.py`
- **Edited (code):** `styles.py` (import + catalog + `build_styles_xml`),
  `tables.py` (import + default + `style: str|None` + conditional emission +
  docstrings), `lib.py` (one comment), `__init__.py` (layout map)
- **Edited (docs/template):** `sheet_guide.md` (Native table visual discipline),
  `sheet_snippets.md` (native-table note + CF dxfId fix + recipe card),
  `sheet_base_template.py` (render docstring)
- **This log:** `core/logs/2026-06-01_workbook_core_named_table_style.md`

---

## 6. Follow-ups (for the user / dependent workbooks)
- `workbook_sub` / `workbook_ddg`: rebuild; any existing `ExcelTable(style="None")`
  now means **no `<tableStyleInfo>`** (different from the old `name="None"`). Drop
  the explicit `style=` to take the new named default, or set it intentionally.
- Any sheet that already attaches a real CF `<dxf>` must use `dxfId="1"`+ now that
  `dxfId=0` is reserved.
- The prior dependent-workbook follow-ups still stand (the `S_TITLE_SHEET` rename,
  validator fixes, tab renames, §N banners, spacing; indentation styles are
  additive).
