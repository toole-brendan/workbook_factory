# Session log — workbook_core indentation / row-hierarchy styling

**Date:** 2026-06-01 (follow-up to `2026-06-01_workbook_core_hardening_human_standard.md`)
**Scope:** `core/workbook_core/` (the xlsx build pipeline). No `deck_core` changes.
**Goal:** Add label-indentation / row-hierarchy authoring guidance + the minimal
style tokens to express it. Driven by a proposal from another AI agent that was
written against **stale** copies of the pipeline files; this session first
*verified* that proposal against the current files, corrected it, then implemented
a trimmed version.

---

## 0. Framing — evaluating the stale-file proposal

The user supplied an external proposal to add indentation guidance and asked to
confirm its "edit here" recommendations still make sense against the current code.

**What it got right (verified against current files):** every factual claim held —
`S_HEADER_LEFT` + all three banner styles are explicitly left-aligned; ordinary
label/numeric styles carry no `<alignment>` (Excel defaults); the guide has no
indent styles in its cheat sheet; merges/wrap/gridlines are banned; the FY snippet
broadcasts one `S_HEADER_LEFT` over the whole header row. Its self-restraint
("don't mint `S_PARENT_ROW`/`S_CHILD_ROW` role language; keep tokens Excel-native")
matches this project's recorded lesson ("capture the principle, don't mint a
construct per pattern").

**What was corrected before implementing:**
- **Vocabulary collision.** The proposal documented hierarchy as "Level 0/1/2",
  but "level" is already taken by `outlineLevel` (the collapsible-group feature,
  `primitives.row()` / the collapsible-group snippet). Visual indent (`indent=`)
  and collapsible outline level are orthogonal. The guidance was written as
  "indent 1 / indent 2" with an explicit note that it is independent of
  `outline_level`.
- **Over-build (YAGNI).** It proposed indent-*total* variants
  (`S_LABEL_INDENT_*_TOTAL`) + `BORDER_TOP_FOR` mappings and an `S_HEADER_RIGHT`.
  But the convention keeps totals flush-left (`S_BOLD`/`S_TOTAL`), so the total
  variants would ship unused, and there's an unresolved design question (is an
  indented subtotal bold?). All three deferred per the user's "trimmed" choice.
- **Missing `applyAlignment="1"`** on the proposed `<xf>` (the alignment wouldn't
  apply); added.

**What it missed (because of stale files):**
- the snippets **Contents TOC** (hand-maintained; a prior session added an entry
  specifically because agents over-index on TOCs) — updated;
- the guide's **style cheat sheet** table — the new styles added there;
- `build_table()` **can't do per-column header styles** (single `header_style`
  int, broadcast) — documented a caveat so centered FY headers go via `write_row`;
- the **`styles.xml` byte/sha baseline** the hardening log pinned — intentionally
  re-baselined here;
- **no probe change needed** — the probe resolves `S_*` names dynamically, so the
  new styles display automatically and aren't misclassified (verified).

---

## 1. Engine change (code) — three styles (the "trimmed" set)

`styles.py`: appended three `cellXfs` entries (indices 20–22) + their `S_*`
constants. No new fonts/fills/borders were needed (they reuse fontId 0/1 and
borderId 0/1).
- **`S_LABEL_INDENT_1`** (20) — plain black label, `indent="1"` (a direct
  component row under a line item).
- **`S_LABEL_INDENT_2`** (21) — same, `indent="2"` (a rare nested component).
- **`S_HEADER_CENTER`** (22) — bold black, bottom underline, **centered** (FY /
  numeric column headers; text-label headers stay `S_HEADER_LEFT`).

All three set `applyAlignment="1"`. **No total variants and no `BORDER_TOP_FOR`
entries** — by design: an indented subtotal is rare and totals stay flush-left, so
`total_row()` correctly *raises* if handed an indent style (verified) rather than
emitting a broken divider.

---

## 2. Docs / template

- **`sheet_guide.md`** — new **"Indentation & row hierarchy"** subsection under
  Style rules (indent only for true parent→child in a styled-range block; parents
  /inputs/totals stay flush-left; indent components not peers; never in native
  tables/source lists/output contracts/lookup tables; never via leading spaces;
  *visual* indent is independent of `outline_level`). Added two rows to the **style
  cheat sheet** (`S_LABEL_INDENT_1`/`_2`, `S_HEADER_CENTER`) and split the header
  cheat-sheet line into text (`S_HEADER_LEFT`) vs numeric/FY (`S_HEADER_CENTER`).
- **`sheet_snippets.md`** — new **"model hierarchy block"** snippet (parent /
  indented components / flush-left `total_row`, with a concrete row-tie-out
  example) + a **Contents TOC** entry; updated the **FY-columns** snippet to
  `[S_HEADER_LEFT] + [S_HEADER_CENTER]*len(_FY)` and added the `build_table`
  single-header-style caveat.
- **`sheet_base_template.py`** — added `S_LABEL_INDENT_1`, `S_LABEL_INDENT_2`,
  `S_HEADER_CENTER` to the template's import menu so they're discoverable from a
  fresh sheet.

---

## 3. Verification

- **`build_styles_xml()` re-baselined (intentional):** was **4161 bytes / sha1
  3b201ffbe9ef5efd5fd0d04b5993ecc63b6d8bd3**, now **4614 bytes / sha1
  5110441d452b7aad6e487f2df236b519639384d5**. Well-formed XML; 23 `cellXfs` ↔ 23
  `S_*` constants, all unique + in range.
- The three new `<xf>` carry exactly `indent=1` / `indent=2` / `horizontal=center`
  with `applyAlignment="1"`.
- **`sheet_base_template.render()` unchanged:** still **1104 bytes / sha1
  07ed92b43619c92acc00c56140d74b8cb5eaee20** (the import-menu edit adds names, not
  output).
- End-to-end: a worksheet built from the documented model-hierarchy + centered-FY
  patterns parses well-formed; the probe resolves `S_HEADER_CENTER` /
  `S_LABEL_INDENT_1` by name and does **not** misclassify indent labels as
  inputs/links/titles; `total_row()` rejects an indent style with a clear error.

**Environment:** `python` (3.14.4) on PATH; read-only checks + in-memory builds, no
mutations to real workbooks.

---

## 4. Deliberately NOT done (deferred, per the "trimmed" scope)
- `S_LABEL_INDENT_1_TOTAL` / `S_LABEL_INDENT_2_TOTAL` + their `BORDER_TOP_FOR`
  mappings — add only when a real sheet needs an indented subtotal (trivial 3-step
  add; resolve the "bold indented subtotal?" question then).
- `S_HEADER_RIGHT` — add if right-aligned numeric headers are ever preferred over
  centered.
- No probe change (none needed); no lints (per the standing no-optional-lints rule).

---

## 5. Files changed this session
- **Edited (code):** `styles.py` (3 cellXfs + 3 `S_*` constants).
- **Edited (docs/template):** `sheet_guide.md` (Indentation subsection + cheat
  sheet), `sheet_snippets.md` (model-hierarchy snippet + TOC + FY update + caveat),
  `sheet_base_template.py` (import menu).
- **This log:** `core/logs/2026-06-01_workbook_core_indentation_styling.md`

---

## 6. Follow-ups (for the user / dependent workbooks)
- The dependent-workbook follow-ups from the prior hardening log still stand
  (`workbook_sub` / `workbook_ddg`: the `S_TITLE_SLIDE`→`S_TITLE_SHEET` rename,
  validator fixes, tab renames, §N banners, spacing). Indentation is purely
  additive — existing sheets keep working unchanged; adopt `S_LABEL_INDENT_1` /
  `S_HEADER_CENTER` where a model block reads better with hierarchy.
