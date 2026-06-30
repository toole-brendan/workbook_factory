"""workbook_core — shared raw-OOXML SpreadsheetML engine + authoring kit.

Stdlib-only. The single source of truth for the workbook engine used by the
per-program pipelines (workbook_ddg, workbook_submarines, …). Layout:

  lib.py          the packager: package_workbook() + package-level XML builders
                  (content-types, rels, workbook.xml, docProps) + native-table /
                  defined-name wiring + the CSV loader.
  primitives.py   cell/row/worksheet/banner_row/write_row/build_table builders +
                  reference/formula helpers (col_letter, cref, qsheet, abs_ref,
                  sheet_ref, range_ref) + the dash-normalization switch.
  tables.py       native Excel tables (ExcelTable) + the WorksheetSpec a sheet's
                  render() returns + the table/defined-name validators.
  notes.py        legacy Excel Notes (ExcelNote) attached to WorksheetSpec.notes +
                  the comments/VML builders + the note validator; a sibling of
                  tables.py (the packager wires both).
  styles.py       the style palette: S_* cell styles, C_* colors, build_styles_xml.
  ooxml.py        shared OOXML constants (XML_DECL, namespace URIs, NS_MAP) — the
                  leaf module; everything else imports these from here.
  table_style_names.py  canonical native-table style names (the named no-format
                  table style); a leaf shared by styles.py + tables.py.

Authoring kit (for hand-building sheet modules):
  sheet_base_template.py    copy-to-start skeleton for one sheet.
  sheet_guide.md            the workbook style + structure rules.
  sheet_snippets.md         copy-from section/row/table builders.
  sheet_probe.py            read-only worksheet/workbook inspector.

Raw SpreadsheetML reference (cheat sheet, schema, SDK docs) lives under
infra/ooxml_reference/.

A sheet module exposes render() (or render_<stem>()) -> WorksheetSpec and sets
TAB_NAME / SHEET_GROUP / TAB_COLOR / COLS (the group drives tab color + order; see
groups.py). The per-program lib.py binds the output
path, the extracted-data dir, and the docProps identity, lists its sheet modules,
and calls package_workbook().
"""
