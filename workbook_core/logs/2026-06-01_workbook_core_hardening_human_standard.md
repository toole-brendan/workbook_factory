# Session log — workbook_core hardening + human-workbook standard

**Date:** 2026-06-01
**Scope:** `core/workbook_core/` (the xlsx build pipeline). No `deck_core` changes.
**Goal:** Apply a correctness/fail-fast hardening pass plus a "human-built workbook"
authoring standard to `workbook_core`, driven by two transcripts
(`core/transcript.txt`, `core/transcript2.txt`) with the user's explicit
scope edits folded in. This is the workbook-side counterpart to the prior
`deck_core` option-B work — but the workbook was already at the target
architecture, so this pass is hardening + doc guidance, NOT a structural refactor.

---

## 0. Operating constraints carried in from the user

Three standing constraints shaped which transcript recommendations were taken:
- **No optional lints.** Both proposed lint modes (`sheet_probe --lint`,
  `sheet_probe --human-lint`) were dropped. The probe stays a read-only inspector.
- **Tab-name verbiage = "discourage underscores," NOT "encourage spaces."** The
  guidance is phrased as *minimize underscores in visible tab names*; it never tells
  authors to prefer spaces/title-case as a rule.
- **No backward-compatibility for the style rename** (see D2): the `*_SLIDE` names
  are deleted outright, not aliased.

Dependent workbooks (`workbook_sub`, `workbook_ddg`) will need follow-up edits
(the rename + any names/refs the new validators now reject); the user owns that.

---

## 1. Engine changes (code)

### A5 — new leaf `workbook_core/ooxml.py`
Centralized `XML_DECL` + the SpreadsheetML namespace URIs (`NS_SS`, `NS_PR`,
`NS_REL`, `NS_MAP`) that were duplicated across `styles.py`, `primitives.py`, and
`sheet_probe.py`. Repointed `styles.py`, `primitives.py`, `tables.py`, `lib.py`, and
`tools/sheet_probe.py` to import the constants from `ooxml`. Import direction is now
`ooxml <- styles <- primitives <- tables <- lib` (docstrings updated). Output is
byte-identical (proven below).

### D2 — hard rename `S_TITLE_SLIDE`/`C_BG_SLIDE_TITLE` → `S_TITLE_SHEET`/`C_BG_SHEET_TITLE`
De-deck-ified the one workbook style token that carried slide vocabulary. **No
aliases** — the old names are gone everywhere in `workbook_core` (styles.py defs +
comments, primitives `banner_row` docstring, lib docstring, template, guide cheat
sheet, snippets). The style *index* is unchanged (still 8), so emitted XML is
identical; only the Python name changed. Dependent sheets that import
`S_TITLE_SLIDE` will break until updated.

### A1 — probe rolls up total-row input/link styles
`sheet_probe._style_maps()` now classifies `S_PCT_INPUT_TOTAL` as an input and
`S_LINK_NUM_TOTAL`/`S_LINK_PCT_TOTAL` as links (previously missing), so a percent
input or green link sitting in a total row is no longer under-reported in the
probe's rollups.

### A2 — fail-fast worksheet names (`lib.py`)
Replaced `_clean_sheet_name()` (silent sanitize + 31-char truncate) with
`_validate_sheet_name()`: trims surrounding whitespace/apostrophes (harmless), then
**raises** on invalid chars (`[ ] : * ? / \`), empty names, names over 31 chars, or
the reserved name "History". Sheet names are load-bearing (formulas/accessors
reference them by value), so a silently-altered name could drift from what a formula
expects — now it's a hard build error.

### A3 — validators for tables + defined names (`tables.py`, wired in `lib.py`)
New `validate_table_name`, `validate_defined_name`, `validate_excel_table` in
`tables.py`; `package_workbook()` calls `validate_excel_table(t)` per table and
`validate_defined_name(dn)` per defined name. Checks: safe-name shape
(`[A-Za-z_][A-Za-z0-9_.]*`, not a cell-ref shape, no reserved `_xlnm`); non-empty +
case-insensitively-unique headers; a valid A1 rectangular `ref` whose column span
equals `len(headers)`; and `totals` keys all being real header names. Build is
strict; the probe stays lenient.

### A4 — `build_table()` rejects over-wide rows (`primitives.py`)
A data row with more values than headers used to be silently sliced (dropping the
extras). It now raises. Short rows still pad with `None` as before.

### G (code) — native tables default to no built-in style (`tables.py`)
`DEFAULT_TABLE_STYLE` changed `"TableStyleMedium2"` → `"None"` and
`ExcelTable.show_row_stripes` default `True` → `False`. With no built-in ListObject
style overlay, the per-cell `S_*` styles alone control the look — header =
`S_HEADER_LEFT` bottom underline only (no top border), body borderless, no final
bottom rule. This is the user's "(a)" choice (vs. documenting a fallback). Built-in
Excel table styles draw their own header/edge borders that cell styles can't
override; `"None"` removes that overlay and is fully determined by emitted XML.
**Deliberately left:** `styles.xml`'s `defaultTableStyle="TableStyleMedium2"` — that
is the Excel-native fallback for interactively-created tables and is moot for ours
(every `ExcelTable` now emits `tableStyleInfo name="None"`), so it stays and
`build_styles_xml()` is byte-identical.

---

## 2. Docs / template / vocabulary

### B1 — "Human workbook standard" (`sheet_guide.md`)
New section (after "Building a sheet"): the workbook should look hand-built, not
generated. Bans Guide/README/Instructions tabs, explanatory cell prose
("This workbook…", "Generated by…"), long narrative banners, and visible "role"
labels in cells; INTENT/LAYOUT stay source-only; visible text is compact (title =
tab name, sections = short noun phrases, no trailing periods).

### C1 — "Tab names" (`sheet_guide.md`)
New section: **minimize underscores in visible tab names** (the rule is about
underscores, not a spaces mandate). Underscores remain correct for module names,
accessors, native table names, and defined names. `TAB_NAME=None` derivation drops
filename underscores; set `TAB_NAME` only for punctuation/acronyms.

### D3 — "role" → "purpose"
Folded into B1 (no visible role labels) and the template (`by role` → `by purpose`
in the INTENT prompt). Tokens stay internal cell-purpose tokens; no visible role
surface.

### E — "Row spacing rhythm" (`sheet_guide.md` + `sheet_snippets.md`)
Documented the compact rhythm: 1 blank after a section/sub-section banner; **2**
blanks between the last content row of a section and the next section banner;
sub-sections optional; no decorative spacers. Updated the `_section` snippet to
return `+2` (was `+1`) so the helper *encodes* the rhythm instead of demonstrating
the old single-blank trailing pattern.

### F — "Column widths" (`sheet_guide.md`)
New section with sizing taste rules (label ~36–44, numeric/FY ~12–14, status
~10–14, note ~24–32 sparingly; no wrap; shorten/split rather than widen).

### G (docs) — "Native table visual discipline" (`sheet_guide.md`)
Documents the `style="None"` default + border discipline + the styled-range +
`autoFilter` fallback when full visual control matters more than ListObject
semantics.

### D1 — `groups.py` `guide` group softened
Docstring now states groups are ordering/color metadata, not a checklist; no group
is required; don't add a guide/readme tab just because the group exists. The `guide`
chapter line reworded to "optional/rare." Mirrored in the guide's Groups table.

### H — gutter `x` clarification (`sheet_snippets.md`)
One sentence: use the gutter `x` only for a real outline anchor; don't mark an
ordinary banner with `x` unless its body rows are actually outlined.

### N — section numbering (§) convention (`sheet_guide.md` + snippets + template)
Ported the clean section-numbering convention from the `workbook_n81` workbook
(`N81 meeting/workbook_n81/`): section banners are titled **`§N - Title`** (section
sign + sequential integer per sheet + short noun phrase), and sub-section banners
**`§Na - Title`** (parent number + lowercase letter, e.g. `§6a`, `§6b`). The `§N`
label doubles as a stable, scannable ID reused as a cross-reference in note cells
and across sheets (`Calcs §1 row 11`, `O&S §3 vs §4`, `MSAR Dec 2023 §4`) — point at
a block without quoting a row number that moves. Added a "Section numbering"
subsection under "The sheet skeleton", reconciled the Human-standard section-banner
bullet to the `§N - …` form, and modelled it in the `_section` / RowCursor /
collapsible snippets and the template's section comment. **Encoding chosen (per the
user): docs + snippet convention only — authors write the literal `§N - …` label,
no new helper or primitive** (matches how `workbook_n81` did it and the
"don't mint a construct" lesson). Zero engine change: `§` (U+00A7) passes through
`cell()`'s inline-string path (verified emitted as UTF-8 `c2 a7`), and the ` - `
uses a plain hyphen so the dash-normalization switch never touches it.

### C2 — underscore example cleanup
Fixed underscore tab-name examples in the guide + snippets (`'Control_Panel'` →
`'Control Panel'`, `'TAM_Model'` → `'TAM Model'`, `range_ref("POP_Location_Parse"…)`
→ `"POP Location Parse"`, producer `TAB_NAME = "POP_Coefficients"` → `"POP
Coefficients"`). Defined-name / table-name identifiers (`portfolio_tam`,
`tbl_subawards`) keep their underscores. (These are docs/examples only — no real tab
was renamed; that's the dependent-workbook follow-up.)

### B2 — template (`sheet_base_template.py`)
Added a "Human-output rule" to the docstring (INTENT/LAYOUT are source-only; visible
text reads human-built) and a "keep it short — reads like the tab label, not a
sentence" comment on the title banner. `__init__.py` layout map gained an `ooxml.py`
line and noted the new validators.

---

## 3. Verification

Behavior-preserving anchors held across the whole pass:
- `build_styles_xml()` → **4161 bytes, sha1 3b201ffbe9ef5efd5fd0d04b5993ecc63b6d8bd3**
  (unchanged — D2 rename + ooxml repoint don't touch styles.xml output; the
  `defaultTableStyle` default was deliberately not changed).
- `sheet_base_template.render().xml` → **1104 bytes, sha1
  07ed92b43619c92acc00c56140d74b8cb5eaee20** (unchanged — template edits are
  docstring/comments + a same-valued token rename).

Intended changes asserted directly:
- native `tableStyleInfo` now `name="None" showRowStripes="0"` (was
  `TableStyleMedium2`/stripes-on) — confirmed in a built `.xlsx`.
- A1: a `S_PCT_INPUT_TOTAL` cell rolls into `hardcoded_inputs`, a
  `S_LINK_NUM_TOTAL` cell into `green_links`.
- A2: invalid char / >31 chars / empty / "History" all raise; a valid quoted name
  passes after strip.
- A3: bad table name (space, cell-ref shape), duplicate headers, ref/header span
  mismatch, unknown totals key, and bad defined names (space, cell-ref shape,
  `_xlnm`) all raise; valid ones pass.
- A4: an over-wide data row raises; a short row still pads.
- End-to-end `package_workbook()` (native table + defined name + `normalize_dashes`)
  builds; all 10 emitted parts parse as well-formed XML.

**Environment:** `python` (3.14.4) on PATH; read-only checks + temp-file builds, no
mutations to real workbooks.

---

## 4. Deliberately NOT done
- **No optional lints** (`sheet_probe --lint`, `--human-lint`) — per the user.
- **No structural refactor** — the workbook architecture was already the target;
  this pass only hardens it and adds guidance.
- **`styles.xml` `defaultTableStyle`** left as `TableStyleMedium2` (Excel-native
  fallback, moot for our explicitly-styled tables).
- **Snippets stay copy-from**, not promoted to importable helpers (the intended
  divergence, same as the deck).

---

## 5. Files changed this session
- **Added:** `core/workbook_core/ooxml.py`
- **Edited (code):** `styles.py` (rename + ooxml import), `primitives.py`
  (ooxml import, A4, docstring), `tables.py` (ooxml import, G default + validators),
  `lib.py` (ooxml import, A2, A3 wiring, docstring), `tools/sheet_probe.py`
  (ooxml import, A1), `groups.py` (D1), `__init__.py` (layout map)
- **Edited (docs/template):** `sheet_guide.md` (B1/C1/D3/E/F/G-docs/D1/C2/N),
  `sheet_snippets.md` (E/H/C2/N + rename), `sheet_base_template.py` (B2/N + rename)
- **This log:** `core/logs/2026-06-01_workbook_core_hardening_human_standard.md`

---

## 6. Follow-ups (for the user, not done here)
- **Dependent workbooks** (`workbook_sub`, `workbook_ddg`): update imports of the
  removed `S_TITLE_SLIDE`/`C_BG_SLIDE_TITLE`; rerun builds and fix anything the new
  worksheet-name / table / defined-name validators now reject; rename underscore
  visible tabs to match the new guidance (and update the cross-sheet refs that point
  at them); re-space sections to the new 2-blank/1-blank rhythm; prefix section
  banners with `§N - …` (sub-sections `§Na - …`) labels; drop any guide/readme tabs.
