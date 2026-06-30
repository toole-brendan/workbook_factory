"""Canonical names for workbook_core native-table styles — a leaf module.

Holds the table-style name shared by styles.py (which defines the style in
styles.xml) and tables.py (which references it on every ExcelTable), so the two
can agree on the literal without an import cycle.

A *named* no-format table style is used instead of omitting <tableStyleInfo> (or
the legacy name="None") because Excel can inject its own default striped/banded
table formatting when a style-less native table is opened and re-saved. Shipping a
durable named style gives Excel something legal to preserve, while the cell-level
S_* styles stay the only visible formatting.

No dependencies (imports nothing from workbook_core); a leaf alongside ooxml.py.
"""
from __future__ import annotations

# Generic core name (not a per-program name). The style itself is built in
# styles.py (_build_no_format_table_styles_xml) and set as the workbook default.
NO_FORMAT_TABLE_STYLE = "WorkbookCore_NoFormatTable"
