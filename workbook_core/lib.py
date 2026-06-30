"""Workbook engine — the packager that turns a list of sheet modules into an .xlsx.

Stdlib-only, no openpyxl. This module owns the package-level XML (the parts that
are not a worksheet body): [Content_Types].xml, the relationship files, workbook.xml,
styles.xml, docProps, and the zip packaging. It also wires native artifacts that
need package plumbing — Excel tables (table parts + per-sheet rels + <tableParts>)
and workbook defined names.

The worksheet bodies themselves come from sheet modules: each module exposes a
render() (or render_<stem>()) that returns a WorksheetSpec. Cell/row/worksheet
string building lives in primitives.py; styling in styles.py; table building in
tables.py.

Import direction (no cycle): ooxml <- styles <- primitives <- {tables, notes} <- lib.

A sheet module looks like:

    from workbook_core.primitives import worksheet, banner_row, write_row
    from workbook_core.styles import S_TITLE_SHEET, S_TITLE_SECTION
    from workbook_core.tables import WorksheetSpec
    from workbook_core.groups import group_color

    TAB_NAME = None          # None -> derived from the module filename (Title Case)
    SHEET_GROUP = "data"     # tab color + tab-block order (see groups.SHEET_GROUPS)
    TAB_COLOR = group_color(SHEET_GROUP)
    COLS = [...]

    def render() -> WorksheetSpec:
        return WorksheetSpec(worksheet(_build_rows(), cols=COLS, tab_color=TAB_COLOR,
                                       with_gutter=True))

The registry is a list of modules:

    from . import inputs, calcs, deckdata
    SHEETS = [inputs, calcs, deckdata]

xlsx archive layout produced by package_workbook():
  [Content_Types].xml
  _rels/.rels
  docProps/core.xml
  docProps/app.xml
  xl/workbook.xml
  xl/_rels/workbook.xml.rels
  xl/styles.xml
  xl/worksheets/sheet1.xml … sheet{N}.xml
  xl/worksheets/_rels/sheet{i}.xml.rels   (only sheets that own tables or notes)
  xl/tables/table1.xml … table{K}.xml     (only if any native tables)
  xl/comments{i}.xml                      (only sheets that own legacy Notes)
  xl/drawings/vmlDrawing{i}.vml           (only sheets that own legacy Notes)
"""
from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from workbook_core.ooxml import XML_DECL, NS_SS, NS_PR
from workbook_core.primitives import xml_attr, set_normalize_dashes
from workbook_core.tables import (
    WorksheetSpec, SheetEntry, build_table_part_xml, build_sheet_rels,
    inject_table_parts, validate_excel_table, validate_defined_name,
)
from workbook_core.notes import (
    build_comments_part_xml, build_vml_drawing_xml, inject_legacy_drawing,
    validate_excel_notes,
)
from workbook_core.groups import GROUP_ORDER


# ---------------------------------------------------------------------------
# Sheet-module resolution (module-first registry, names derived from modules)
# ---------------------------------------------------------------------------

_INVALID_SHEET_CHARS = set('[]:*?/\\')


def _module_stem(mod) -> str:
    return mod.__name__.rsplit(".", 1)[-1]


def _render_fn(mod):
    """Find a module's render callable: render() or render_<stem>()."""
    fn = getattr(mod, "render", None)
    if callable(fn):
        return fn
    stem = _module_stem(mod)
    fn = getattr(mod, f"render_{stem}", None)
    if callable(fn):
        return fn
    raise AttributeError(
        f"{mod.__name__} must expose render() or render_{stem}()"
    )


# --- Sheet-item normalization ---------------------------------------------
# A SHEETS entry is either a sheet *module* (legacy one-file-per-tab) or a
# SheetEntry (one source file registering many tabs). These helpers read the
# same surface off both, so the packager treats them uniformly and the two
# styles can coexist during a migration.

def _is_entry(item) -> bool:
    return isinstance(item, SheetEntry)


def _item_label(item) -> str:
    """Identifier for error messages."""
    return f"SheetEntry({item.tab_name!r})" if _is_entry(item) else item.__name__


def _item_group(item):
    """Logical-chapter key (SheetEntry.group / module SHEET_GROUP)."""
    return item.group if _is_entry(item) else getattr(item, "SHEET_GROUP", None)


def _item_render(item):
    """Zero-arg render callable returning a WorksheetSpec."""
    if _is_entry(item):
        if not callable(item.render):
            raise AttributeError(f"{_item_label(item)} render is not callable")
        return item.render
    return _render_fn(item)


def _item_raw_name(item) -> str:
    """Pre-sanitization tab name: SheetEntry.tab_name / module TAB_NAME / stem."""
    if _is_entry(item):
        return item.tab_name
    return (getattr(item, "TAB_NAME", None)
            or _module_stem(item).replace("_", " ").title())


def _validate_sheet_name(raw, label: str) -> str:
    """Validate a worksheet name; raise rather than silently alter it.

    Sheet names are load-bearing - cross-sheet formulas and accessor functions
    reference them by value - so the name an author writes is the name that ships.
    Surrounding whitespace and apostrophes are trimmed (harmless normalization),
    but anything Excel would reject (invalid characters, an empty name, a name over
    31 chars, the reserved name "History") is a hard error: we never sanitize a bad
    character to "_" or truncate to fit behind the author's back, because that would
    leave formulas pointing at a tab that no longer has the expected name. Fix the
    TAB_NAME / SheetEntry.tab_name (or the module filename) instead.
    """
    name = str(raw).strip().strip("'")
    if not name:
        raise ValueError(f"Empty worksheet name (from {label}).")
    bad = sorted(set(name) & _INVALID_SHEET_CHARS)
    if bad:
        raise ValueError(
            f"Invalid worksheet name {name!r} (from {label}): Excel forbids "
            f"{bad} in sheet names (none of [ ] : * ? / \\). Set a clean "
            f"TAB_NAME / SheetEntry.tab_name - names are not sanitized."
        )
    if len(name) > 31:
        raise ValueError(
            f"Worksheet name {name!r} (from {label}) is {len(name)} chars; Excel's "
            f"limit is 31 - names are not truncated. Shorten the "
            f"TAB_NAME / SheetEntry.tab_name."
        )
    if name.lower() == "history":
        raise ValueError(
            f"Worksheet name {name!r} (from {label}) is reserved by Excel."
        )
    return name


def _sheet_name(item, seen: set[str]) -> str:
    """Validated, collision-checked tab name for a module or SheetEntry.

    A collision is a hard error - never a silent rename (a silent " 2" suffix would
    leave cross-sheet references pointing at the wrong tab). Set a distinct
    TAB_NAME / SheetEntry.tab_name on one of the colliding items. Comparison is
    case-insensitive, matching Excel.
    """
    name = _validate_sheet_name(_item_raw_name(item), _item_label(item))
    key = name.lower()
    if key in seen:
        raise ValueError(
            f"Duplicate worksheet name {name!r} (from {_item_label(item)}). "
            f"Excel requires unique sheet names and accessors/formulas reference "
            f"them by value; set a distinct TAB_NAME / SheetEntry.tab_name."
        )
    seen.add(key)
    return name


def _coerce_spec(rendered) -> WorksheetSpec:
    """Require render() to return a WorksheetSpec."""
    if isinstance(rendered, WorksheetSpec):
        return rendered
    raise TypeError(
        f"render() must return a WorksheetSpec, got {type(rendered).__name__!r}. "
        f"Wrap a bare worksheet string: WorksheetSpec(worksheet(...))."
    )


def _assert_group_blocks(sheet_modules) -> None:
    """Enforce the tab-group invariant: every sheet declares a SHEET_GROUP, each
    group forms ONE contiguous run, and the runs follow groups.SHEET_GROUPS order.

    This makes "same group -> same color -> together in tab order" structural: a
    misplaced or mis-tagged tab fails the build instead of silently scattering a
    color. (Color itself derives from the group via groups.group_color(), so it
    can't drift from the group.)
    """
    seq = [(_item_label(m), _item_group(m)) for m in sheet_modules]
    missing = [label for label, g in seq if g is None]
    if missing:
        raise ValueError(f"sheet items missing SHEET_GROUP/group: {missing}")
    unknown = sorted({g for _n, g in seq if g not in GROUP_ORDER})
    if unknown:
        raise ValueError(f"unknown SHEET_GROUP(s): {unknown}")
    # Contiguity: collapse to the run of group keys; no key may reappear.
    runs: list[str] = []
    for _name, g in seq:
        if not runs or runs[-1] != g:
            if g in runs:
                raise ValueError(
                    f"SHEET_GROUP {g!r} is split across the tab order - all tabs of "
                    f"a group must be contiguous"
                )
            runs.append(g)
    # Canonical order: the runs appear in groups.SHEET_GROUPS order.
    order = [GROUP_ORDER[g] for g in runs]
    if order != sorted(order):
        raise ValueError(
            f"tab-group blocks out of canonical order: {runs} (expected the order "
            f"in groups.SHEET_GROUPS)"
        )


# ---------------------------------------------------------------------------
# Package-level XML
# ---------------------------------------------------------------------------


def build_content_types(n_sheets: int, n_tables: int = 0,
                        comment_part_nums: list[int] | None = None,
                        has_vml: bool = False) -> str:
    comment_part_nums = comment_part_nums or []
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'spreadsheetml.worksheet+xml"/>'
        for i in range(1, n_sheets + 1)
    )
    table_overrides = "".join(
        f'<Override PartName="/xl/tables/table{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'spreadsheetml.table+xml"/>'
        for i in range(1, n_tables + 1)
    )
    # Legacy Notes: a per-part comments Override, plus ONE `vml` extension Default
    # (the VML drawing parts share the .vml extension, so a Default — not per-part
    # Overrides — is the correct content-type registration).
    comments_overrides = "".join(
        f'<Override PartName="/xl/comments{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'spreadsheetml.comments+xml"/>'
        for i in comment_part_nums
    )
    vml_default = (
        '<Default Extension="vml" '
        'ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing"/>'
        if has_vml else ""
    )
    return (
        XML_DECL
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + vml_default
        + '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/xl/metadata.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        + sheet_overrides
        + table_overrides
        + comments_overrides
        + "</Types>"
    )


def build_root_rels() -> str:
    return (
        XML_DECL
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def build_defined_names_xml(defined_names: dict[str, str]) -> str:
    """Render a <definedNames> block from {name: target-ref}.

    Names are workbook-scoped. Each must follow Excel's name rules
    ([A-Za-z_][A-Za-z0-9_.]*, not a cell-ref shape, not a reserved _xlnm name);
    the target is a formula-style reference such as "'Inputs'!$D$7".
    """
    if not defined_names:
        return ""
    items = "".join(
        f'<definedName name="{xml_attr(nm)}">{xml_escape(target)}</definedName>'
        for nm, target in defined_names.items()
    )
    return f"<definedNames>{items}</definedNames>"


def build_workbook_xml(sheet_names: list[str], defined_names_xml: str = "",
                       hidden: list[bool] | None = None) -> str:
    """hidden: optional per-sheet visibility flags parallel to sheet_names;
    a True entry emits state="hidden" on that <sheet>."""
    hidden = hidden or [False] * len(sheet_names)
    sheets_xml = "".join(
        f'<sheet name="{xml_attr(name)}" sheetId="{i}"'
        + (' state="hidden"' if hide else "")
        + f' r:id="rId{i}"/>'
        for i, (name, hide) in enumerate(zip(sheet_names, hidden), start=1)
    )
    return (
        XML_DECL
        + f'<workbook xmlns="{NS_SS}" xmlns:r="{NS_PR}">'
        + '<workbookPr defaultThemeVersion="166925"/>'
        + '<bookViews><workbookView xWindow="0" yWindow="0" '
        'windowWidth="28800" windowHeight="16800"/></bookViews>'
        + f"<sheets>{sheets_xml}</sheets>"
        + defined_names_xml
        + '<calcPr calcId="191029" fullCalcOnLoad="1" forceFullCalc="1"/>'
        + "</workbook>"
    )


def build_workbook_rels(n_sheets: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, n_sheets + 1)
    )
    styles_rel = (
        f'<Relationship Id="rId{n_sheets + 1}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        f'Target="styles.xml"/>'
    )
    metadata_rel = (
        f'<Relationship Id="rId{n_sheets + 2}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata" '
        f'Target="metadata.xml"/>'
    )
    return (
        XML_DECL
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + rels + styles_rel + metadata_rel
        + "</Relationships>"
    )


def build_metadata_xml() -> str:
    """The dynamic-array (spill) metadata part. A worksheet cell whose formula
    spills carries cm="1", pointing at the single cellMetadata record below,
    whose XLDAPR future-metadata flags it fDynamic="1" - that is what tells Excel
    to treat the formula as a DYNAMIC array (spills + recomputes its own extent)
    rather than a legacy CSE array (confined to its ref). Always emitted; harmless
    when no cell references it."""
    return (
        XML_DECL
        + '<metadata xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:xlrd="http://schemas.microsoft.com/office/spreadsheetml/2017/richdata" '
        'xmlns:xda="http://schemas.microsoft.com/office/spreadsheetml/2017/dynamicarray">'
        '<metadataTypes count="1">'
        '<metadataType name="XLDAPR" minSupportedVersion="120000" copy="1" '
        'pasteAll="1" pasteValues="1" merge="1" splitFirst="1" rowColShift="1" '
        'clearFormats="1" clearComments="1" assign="1" coerce="1" cellMeta="1"/>'
        '</metadataTypes>'
        '<futureMetadata name="XLDAPR" count="1"><bk><extLst>'
        '<ext uri="{bdbb8cdc-fa1e-496e-a857-3c3f30c029c3}">'
        '<xda:dynamicArrayProperties fDynamic="1" fCollapsed="0"/>'
        '</ext></extLst></bk></futureMetadata>'
        '<cellMetadata count="1"><bk><rc t="1" v="0"/></bk></cellMetadata>'
        '</metadata>'
    )


def build_core_props(title: str, creator: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        XML_DECL
        + '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{xml_escape(title)}</dc:title>'
        f'<dc:creator>{xml_escape(creator)}</dc:creator>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def build_app_props(n_sheets: int, sheet_names: list[str], app_name: str) -> str:
    titles = "".join(f"<vt:lpstr>{xml_escape(n)}</vt:lpstr>" for n in sheet_names)
    return (
        XML_DECL
        + '<Properties '
        'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        f'<Application>{xml_escape(app_name)}</Application>'
        '<HeadingPairs><vt:vector size="2" baseType="variant">'
        '<vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>'
        f'<vt:variant><vt:i4>{n_sheets}</vt:i4></vt:variant>'
        '</vt:vector></HeadingPairs>'
        f'<TitlesOfParts><vt:vector size="{n_sheets}" baseType="lpstr">{titles}</vt:vector></TitlesOfParts>'
        "</Properties>"
    )


# ---------------------------------------------------------------------------
# CSV loader
# ---------------------------------------------------------------------------


def load_extracted_csv(name: str, extracted_dir) -> tuple[list[str], list[list]]:
    """Load <extracted_dir>/<name>.csv. Returns (headers, rows).

    Numeric cells are coerced to int or float; empty cells become None.
    Cells starting with '=' are passed through as Excel formulas.

    `extracted_dir` is supplied by the calling pipeline's lib.py (its own
    EXTRACTED path), so the engine stays pipeline-agnostic.
    """
    import csv
    path = Path(extracted_dir) / f"{name}.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rdr = csv.reader(fh)
        rows = list(rdr)
    if not rows:
        return [], []
    headers = rows[0]
    data = []
    for r in rows[1:]:
        coerced = []
        for v in r:
            v = v.strip()
            if v == "":
                coerced.append(None)
                continue
            if v.startswith("="):
                coerced.append(v)
                continue
            try:
                if "." in v or "e" in v.lower():
                    coerced.append(float(v))
                else:
                    coerced.append(int(v))
            except ValueError:
                coerced.append(v)
        data.append(coerced)
    return headers, data


# ---------------------------------------------------------------------------
# Build entry point
# ---------------------------------------------------------------------------


def package_workbook(out_path, sheet_modules, *, title: str, creator: str,
                     app_name: str, normalize_dashes: bool = False) -> int:
    """Render every sheet module and package into the output xlsx.

    sheet_modules: the pipeline's SHEETS list. Each item is either a sheet
      *module* (exposes render()/render_<stem>() returning a WorksheetSpec; may
      set TAB_NAME, else the tab name is the filename stem in Title Case) OR a
      tables.SheetEntry (tab_name + group + render callable), letting one source
      file register many tabs. Both are normalized to (tab_name, group, render).
      render() MUST return a WorksheetSpec - a bare worksheet string is rejected
      here; wrap it as WorksheetSpec(worksheet(...)). (The probe is lenient and
      wraps bare strings for inspection, but the build is strict.)
    normalize_dashes: when True, em/en dashes in text cells render as hyphens
      (set once for the whole build; default off).
    out_path / title / creator / app_name: per-pipeline bindings.

    Raises ValueError on a duplicate worksheet name, native-table name, or
    defined name - all must be unique, and collisions are load-bearing (formulas
    reference them by value), so they are never silently renamed.
    """
    set_normalize_dashes(normalize_dashes)
    _assert_group_blocks(sheet_modules)

    out_path = Path(out_path)
    n = len(sheet_modules)

    # Render every sheet, deriving its tab name from the module.
    seen: set[str] = set()
    rendered: list[tuple[str, WorksheetSpec]] = []
    hidden_flags: list[bool] = []
    for item in sheet_modules:
        spec = _coerce_spec(_item_render(item)())
        name = _sheet_name(item, seen)
        rendered.append((name, spec))
        hidden_flags.append(bool(getattr(item, "hidden", False)))
    sheet_names = [name for name, _ in rendered]
    if all(hidden_flags):
        raise ValueError("All sheets are hidden; Excel requires at least one "
                         "visible worksheet.")

    # Wire native tables: global table numbering, per-sheet rels + <tableParts>.
    global_table_num = 0
    seen_table_names: set[str] = set()    # workbook-unique table names (Excel rule)
    seen_defined: set[str] = set()        # workbook-unique defined names
    table_parts: dict[str, str] = {}      # xl/tables/tableK.xml -> xml
    comments_parts: dict[str, str] = {}   # xl/commentsN.xml -> xml (legacy notes)
    vml_parts: dict[str, str] = {}        # xl/drawings/vmlDrawingN.vml -> xml
    comment_part_nums: list[int] = []     # sheet indices that carry a comments part
    sheet_rels: dict[int, str] = {}       # sheet index -> rels xml
    sheet_bodies: list[str] = []
    defined_names: dict[str, str] = {}
    for idx, (name, spec) in enumerate(rendered, start=1):
        ws_xml = spec.xml
        rids: list[str] = []
        rels: list[tuple[str, str, str]] = []
        for t in spec.tables:
            validate_excel_table(t)
            tkey = t.name.lower()
            if tkey in seen_table_names:
                raise ValueError(
                    f"Duplicate table name {t.name!r} (sheet {name!r}). "
                    f"Excel requires workbook-unique table names."
                )
            seen_table_names.add(tkey)
            global_table_num += 1
            rid = f"rId{len(rels) + 1}"        # rels accumulate; notes continue after
            table_parts[f"xl/tables/table{global_table_num}.xml"] = (
                build_table_part_xml(global_table_num, t)
            )
            rels.append((rid, "table", f"../tables/table{global_table_num}.xml"))
            rids.append(rid)
        if rids:
            ws_xml = inject_table_parts(ws_xml, rids)
        # Legacy Excel Notes are wired like native tables: the author declares them
        # on the WorksheetSpec; the packager owns the comments part, VML drawing
        # part, sheet rels, content-types, and the worksheet <legacyDrawing>. Wired
        # AFTER tables so the injected <legacyDrawing> lands before <tableParts>
        # (CT_Worksheet child order), and the note rel ids continue after table rels.
        # Comments/VML parts are numbered by sheet index (<=1 of each per sheet).
        if spec.notes:
            validate_excel_notes(spec.notes, sheet_name=name)
            comments_parts[f"xl/comments{idx}.xml"] = build_comments_part_xml(spec.notes)
            vml_parts[f"xl/drawings/vmlDrawing{idx}.vml"] = (
                build_vml_drawing_xml(spec.notes, idmap=idx)
            )
            comment_part_nums.append(idx)
            comment_rid = f"rId{len(rels) + 1}"
            vml_rid = f"rId{len(rels) + 2}"
            rels.append((comment_rid, "comments", f"../comments{idx}.xml"))
            rels.append((vml_rid, "vmlDrawing", f"../drawings/vmlDrawing{idx}.vml"))
            ws_xml = inject_legacy_drawing(ws_xml, vml_rid)
        if rels:
            sheet_rels[idx] = build_sheet_rels(rels)
        sheet_bodies.append(ws_xml)
        for dn_name, dn_target in spec.defined_names.items():
            validate_defined_name(dn_name)
            if dn_name.lower() in seen_defined:
                raise ValueError(
                    f"Duplicate defined name {dn_name!r} (sheet {name!r}). "
                    f"Defined names must be workbook-unique."
                )
            seen_defined.add(dn_name.lower())
            defined_names[dn_name] = dn_target

    defined_names_xml = build_defined_names_xml(defined_names)

    print(f"Building {out_path.name} with {n} sheets …")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
                    build_content_types(n, global_table_num,
                                        comment_part_nums=comment_part_nums,
                                        has_vml=bool(vml_parts)))
        zf.writestr("_rels/.rels", build_root_rels())
        zf.writestr("docProps/core.xml", build_core_props(title, creator))
        zf.writestr("docProps/app.xml", build_app_props(n, sheet_names, app_name))
        zf.writestr("xl/workbook.xml",
                    build_workbook_xml(sheet_names, defined_names_xml,
                                       hidden=hidden_flags))
        zf.writestr("xl/_rels/workbook.xml.rels", build_workbook_rels(n))
        zf.writestr("xl/metadata.xml", build_metadata_xml())
        # build_styles_xml is imported lazily so the engine has no hard
        # dependency-direction issue if a pipeline overrides styles. styles.xml also
        # carries the named no-format table style every native table references by
        # default, so a native table depends on BOTH its table part and this part.
        from workbook_core.styles import build_styles_xml
        zf.writestr("xl/styles.xml", build_styles_xml())
        for i, (name, body) in enumerate(zip(sheet_names, sheet_bodies), start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", body)
            if i in sheet_rels:
                zf.writestr(f"xl/worksheets/_rels/sheet{i}.xml.rels", sheet_rels[i])
            print(f"  sheet {i}: {name:<20s}  {len(body):>7,} bytes")
        for path, xml in table_parts.items():
            zf.writestr(path, xml)
        for path, xml in comments_parts.items():
            zf.writestr(path, xml)
        for path, xml in vml_parts.items():
            zf.writestr(path, xml)

    print(f"Wrote {out_path}")
    print(f"  size: {out_path.stat().st_size:,} bytes")
    if global_table_num:
        print(f"  native tables: {global_table_num}")
    if comment_part_nums:
        print(f"  note parts: {len(comment_part_nums)}")
    return 0
