"""sheet_probe - read-only inspector for workbook_core sheets and built .xlsx files.

Reports what the emitted OOXML actually says: tab color, gridlines, column widths,
rows (with outline level / height), every cell (ref, style resolved to its S_*
name, value, formula), plus derived rollups - banner rows, hardcoded inputs,
green-link cells, placeholder cells, formulas grouped by the sheet they reference,
declared native tables, and defined names. It never builds, repairs, or judges.

Two modes:
  module : import a sheet module, run render()/render_<stem>() -> WorksheetSpec,
           inspect the worksheet XML (and the spec's tables + defined_names).
  file   : open a built .xlsx and inspect xl/worksheets/sheet{N}.xml, plus the
           native tables (sheet rels -> xl/tables/*) and the workbook defined
           names that target each sheet.

Output (replaces, never stacks):
  <out_dir>/<name>.md
  <out_dir>/<name>.json

CLI:
  sheet_probe <target> [--sheet N|NAME] [--json] [--all] [--out-dir DIR]

  target: a dotted module path (workbook_ddg.sheets.inputs), a .py file, or a
          .xlsx file. --all probes every module in the program's SHEETS (module
          mode) or every worksheet in the file (file mode).
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import posixpath
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# Make the shared engine importable when run as a direct script: parents[1] of
# …/workbook_core/sheet_probe.py is the workspace root (which holds workbook_core).
_CORE_ROOT = str(Path(__file__).resolve().parents[1])
if _CORE_ROOT not in sys.path:
    sys.path.insert(0, _CORE_ROOT)

from workbook_core.ooxml import NS_SS as _SS, NS_PR as _PR, NS_MAP as _NS  # noqa: E402


def _q(tag: str) -> str:
    return f"{{{_SS}}}{tag}"


# ---------------------------------------------------------------------------
# Style index -> S_* name (and role sets), read live from workbook_core.styles
# ---------------------------------------------------------------------------


def _style_maps():
    import workbook_core.styles as st
    idx_to_name = {
        v: k for k, v in vars(st).items()
        if k.startswith("S_") and isinstance(v, int)
    }
    inputs = {getattr(st, n) for n in
              ("S_NUM_INPUT", "S_PCT_INPUT",
               "S_NUM_INPUT_TOTAL", "S_PCT_INPUT_TOTAL") if hasattr(st, n)}
    links = {getattr(st, n) for n in
             ("S_LINK_NUM", "S_LINK_PCT",
              "S_LINK_NUM_TOTAL", "S_LINK_PCT_TOTAL") if hasattr(st, n)}
    titles = {getattr(st, n) for n in
              ("S_TITLE_SHEET", "S_TITLE_SECTION", "S_TITLE_SUBSECTION")
              if hasattr(st, n)}
    return idx_to_name, inputs, links, titles


# ---------------------------------------------------------------------------
# Signature-based style resolution (file mode): match a cellXf by what it IS
# (numFmt + font + fill + border + alignment), not by its numeric index.
# ---------------------------------------------------------------------------
# Excel compacts and re-orders the style table when it opens + re-saves a workbook, so a
# cell's s="5" in a round-tripped file may no longer be the engine's S_NUM_INPUT. Resolving
# each cellXf to a SIGNATURE - the resolved definitions of the font / fill / border / numFmt
# it references, which are index-independent - lets file mode label styles by identity.


def _norm_elem(el) -> str:
    """Canonical, attribute-order-independent string for an XML element + its children."""
    tag = el.tag.split("}")[-1]
    attrs = ",".join(f"{k}={v}" for k, v in sorted(el.attrib.items()))
    kids = "".join(sorted(_norm_elem(c) for c in el))
    return f"<{tag} {attrs}>{kids}</{tag}>"


def _cellxf_signatures(styles_xml: str) -> list[tuple]:
    """One signature per cellXf (in document order). Each resolves the xf's numFmtId / fontId
    / fillId / borderId to the actual definition, so the signature survives a re-index."""
    root = ET.fromstring(styles_xml)

    def _kids(tag):
        parent = root.find(f"a:{tag}", _NS)
        return list(parent) if parent is not None else []

    numfmts = {}
    nf_parent = root.find("a:numFmts", _NS)
    if nf_parent is not None:
        for nf in nf_parent.findall("a:numFmt", _NS):
            numfmts[nf.get("numFmtId")] = nf.get("formatCode")
    fonts = [_norm_elem(e) for e in _kids("fonts")]
    fills = [_norm_elem(e) for e in _kids("fills")]
    borders = [_norm_elem(e) for e in _kids("borders")]

    def _at(seq, i, kind):
        return seq[i] if 0 <= i < len(seq) else f"#{kind}{i}"

    sigs = []
    cellxfs = root.find("a:cellXfs", _NS)
    for xf in (cellxfs.findall("a:xf", _NS) if cellxfs is not None else []):
        nfid = xf.get("numFmtId", "0")
        align = xf.find("a:alignment", _NS)
        sigs.append((
            numfmts.get(nfid, nfid),                                  # numfmt code or builtin id
            _at(fonts, int(xf.get("fontId", "0")), "font"),
            _at(fills, int(xf.get("fillId", "0")), "fill"),
            _at(borders, int(xf.get("borderId", "0")), "border"),
            _norm_elem(align) if align is not None else "",
        ))
    return sigs


def _canonical_sig_to_name() -> dict:
    """signature -> S_* name, computed from the engine's own freshly-rendered styles.xml."""
    from workbook_core.styles import build_styles_xml
    idx_to_name, *_ = _style_maps()
    out = {}
    for idx, sig in enumerate(_cellxf_signatures(build_styles_xml())):
        out.setdefault(sig, idx_to_name.get(idx, f"#{idx}"))
    return out


def _file_style_maps(file_styles_xml: str):
    """(idx_to_name, inputs, links, titles) keyed by the FILE's cellXf indices, resolved by
    signature against the canonical engine styles - so a round-tripped workbook is labelled
    correctly even after Excel renumbered its style table."""
    idx_to_name_c, inputs_c, links_c, titles_c = _style_maps()
    name_inputs = {idx_to_name_c.get(i) for i in inputs_c}
    name_links = {idx_to_name_c.get(i) for i in links_c}
    name_titles = {idx_to_name_c.get(i) for i in titles_c}
    sig_to_name = _canonical_sig_to_name()
    idx_to_name, inputs, links, titles = {}, set(), set(), set()
    for idx, sig in enumerate(_cellxf_signatures(file_styles_xml)):
        name = sig_to_name.get(sig, f"#{idx}")
        idx_to_name[idx] = name
        if name in name_inputs:
            inputs.add(idx)
        if name in name_links:
            links.add(idx)
        if name in name_titles:
            titles.add(idx)
    return idx_to_name, inputs, links, titles


# ---------------------------------------------------------------------------
# Worksheet XML -> structured inventory
# ---------------------------------------------------------------------------


def _cell_text(c: ET.Element) -> str | None:
    """Extract a cell's displayed text (inlineStr <is><t>, or <v>)."""
    is_el = c.find("a:is", _NS)
    if is_el is not None:
        t = is_el.find("a:t", _NS)
        return t.text if t is not None else ""
    v = c.find("a:v", _NS)
    return v.text if v is not None else None


def _placeholderish(text: str | None) -> bool:
    if not text:
        return False
    u = text.upper()
    return "TBD" in u or "PENDING" in u or u.startswith("PEND-")


def _referenced_sheets(formula: str) -> list[str]:
    """Pull sheet names a formula references: 'Sheet Name'!… or Bareword!…."""
    out: list[str] = []
    i = 0
    n = len(formula)
    while i < n:
        ch = formula[i]
        if ch == "'":
            j = formula.find("'", i + 1)
            # handle doubled '' inside quoted name
            while j != -1 and j + 1 < n and formula[j + 1] == "'":
                j = formula.find("'", j + 2)
            if j != -1 and j + 1 < n and formula[j + 1] == "!":
                out.append(formula[i + 1:j].replace("''", "'"))
                i = j + 2
                continue
            i = (j + 1) if j != -1 else n
        elif ch == "!" :
            # bareword sheet ref: scan back for the identifier
            k = i - 1
            while k >= 0 and (formula[k].isalnum() or formula[k] in "_."):
                k -= 1
            word = formula[k + 1:i]
            if word and not word[0].isdigit():
                out.append(word)
            i += 1
        else:
            i += 1
    # de-dup, preserve order
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def inspect_worksheet_xml(xml: str, style_maps=None) -> dict:
    """Parse one <worksheet> string into a structured inventory dict.

    style_maps: optional (idx_to_name, input_styles, link_styles, title_styles). File mode
    passes maps resolved from the FILE's own styles.xml by signature, so a workbook Excel
    opened + re-saved (which renumbers the style table) is still labelled by what each style
    IS. Module mode omits it and uses the live workbook_core.styles indices.
    """
    if style_maps is None:
        idx_to_name, input_styles, link_styles, title_styles = _style_maps()
    else:
        idx_to_name, input_styles, link_styles, title_styles = style_maps
    root = ET.fromstring(xml)

    tab_color = None
    sheetpr = root.find("a:sheetPr", _NS)
    if sheetpr is not None:
        tc = sheetpr.find("a:tabColor", _NS)
        if tc is not None:
            tab_color = tc.get("rgb")

    gridlines = None
    sv = root.find("a:sheetViews/a:sheetView", _NS)
    if sv is not None:
        gridlines = sv.get("showGridLines")

    cols = []
    cols_el = root.find("a:cols", _NS)
    if cols_el is not None:
        for c in cols_el.findall("a:col", _NS):
            cols.append({"min": c.get("min"), "max": c.get("max"),
                         "width": c.get("width")})

    rows_out = []
    cells_out = []
    banners = []
    inputs = []
    links = []
    placeholders = []
    formula_refs: dict[str, list[str]] = {}
    n_formulas = 0

    sheet_data = root.find("a:sheetData", _NS)
    for row in (sheet_data.findall("a:row", _NS) if sheet_data is not None else []):
        r = row.get("r")
        rinfo = {"r": r}
        if row.get("outlineLevel"):
            rinfo["outlineLevel"] = row.get("outlineLevel")
        if row.get("ht"):
            rinfo["ht"] = row.get("ht")
        rcells = row.findall("a:c", _NS)
        rinfo["n_cells"] = len(rcells)
        rows_out.append(rinfo)
        for c in rcells:
            ref = c.get("r")
            s = c.get("s")
            sidx = int(s) if s is not None else 0
            sname = idx_to_name.get(sidx, f"#{sidx}")
            f = c.find("a:f", _NS)
            formula = f.text if f is not None else None
            text = _cell_text(c)
            entry = {"ref": ref, "style": sname}
            if formula is not None:
                entry["formula"] = formula
            elif text is not None:
                entry["value"] = text
            cells_out.append(entry)

            if sidx in title_styles and text:
                banners.append({"ref": ref, "style": sname, "text": text})
            if sidx in input_styles:
                inputs.append({"ref": ref, "style": sname, "value": text})
            if sidx in link_styles:
                links.append({"ref": ref, "style": sname, "formula": formula})
            if formula is not None:
                n_formulas += 1
                for sh in _referenced_sheets(formula):
                    formula_refs.setdefault(sh, []).append(ref)
            if _placeholderish(text):
                placeholders.append({"ref": ref, "value": text})

    return {
        "tab_color": tab_color,
        "gridlines_shown": gridlines,
        "n_cols": len(cols),
        "cols": cols,
        "n_rows": len(rows_out),
        "rows": rows_out,
        "n_cells": len(cells_out),
        "cells": cells_out,
        "banners": banners,
        "hardcoded_inputs": inputs,
        "green_links": links,
        "placeholders": placeholders,
        "n_formulas": n_formulas,
        "formula_refs_by_sheet": {k: v for k, v in sorted(formula_refs.items())},
    }


# ---------------------------------------------------------------------------
# Source resolution (module mode / file mode)
# ---------------------------------------------------------------------------


def _load_module(target: str):
    """Import a sheet module from a dotted path or a .py file path."""
    if target.endswith(".py") or "/" in target:
        path = Path(target).resolve()
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return importlib.import_module(target)


def _render_spec(mod):
    """Call render()/render_<stem>() and return a WorksheetSpec.

    Probe-only leniency: a bare worksheet string is wrapped so a sheet can be
    inspected mid-development. The build (package_workbook) is stricter and
    requires a WorksheetSpec - a note is printed so that gap stays visible.
    """
    from workbook_core.tables import WorksheetSpec
    label = getattr(mod, "__name__", None) or repr(mod)
    fn = getattr(mod, "render", None)
    if not callable(fn):
        stem = label.rsplit(".", 1)[-1]
        fn = getattr(mod, f"render_{stem}", None)
    if not callable(fn):
        raise AttributeError(f"{label}: no render()/render_<stem>()")
    out = fn()
    if isinstance(out, WorksheetSpec):
        return out
    if isinstance(out, str):
        print(f"  note: {label}.render() returned a bare string; the build "
              f"requires WorksheetSpec(worksheet(...)). Wrapping for inspection.")
        return WorksheetSpec(out)
    raise TypeError(f"{label}.render() returned {type(out).__name__}")


def probe_module(mod, *, name: str | None = None) -> dict:
    from workbook_core.tables import SheetEntry
    spec = _render_spec(mod)
    if isinstance(mod, SheetEntry):
        rep = {"source": "entry", "name": name or mod.tab_name,
               "tab_name": mod.tab_name, "sheet_group": mod.group}
    else:
        rep = {"source": "module", "name": name or mod.__name__.rsplit(".", 1)[-1],
               "tab_name": getattr(mod, "TAB_NAME", None),
               "sheet_group": getattr(mod, "SHEET_GROUP", None)}
    rep.update(inspect_worksheet_xml(spec.xml))
    rep["tables"] = [
        {"name": t.name, "ref": t.ref, "headers": list(t.headers),
         "style": t.style, "totals_row_shown": t.totals_row_shown}
        for t in spec.tables
    ]
    rep["defined_names"] = dict(spec.defined_names)
    # Module mode reports declared legacy Notes (file mode does not yet read the
    # comments parts back — a deferred fast-follow).
    rep["notes"] = [
        {"ref": nt.ref, "author": nt.author, "text": str(nt.text)}
        for nt in getattr(spec, "notes", [])
    ]
    return rep


def _xlsx_sheet_names(zf: zipfile.ZipFile) -> list[str]:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    return [s.get("name") for s in wb.iter(_q("sheet"))]


def _xlsx_defined_names(zf: zipfile.ZipFile) -> list[dict]:
    """All workbook defined names: {name, localSheetId, target}."""
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    dn = wb.find("a:definedNames", _NS)
    if dn is None:
        return []
    return [{"name": d.get("name"), "localSheetId": d.get("localSheetId"),
             "target": (d.text or "")}
            for d in dn.findall("a:definedName", _NS)]


def _xlsx_sheet_tables(zf: zipfile.ZipFile, sheet_idx: int) -> list[dict]:
    """Native tables on sheet N: <tableParts> -> sheet rels -> table parts."""
    ws = ET.fromstring(zf.read(f"xl/worksheets/sheet{sheet_idx}.xml"))
    tparts = ws.find("a:tableParts", _NS)
    if tparts is None:
        return []
    rid_target: dict[str, str] = {}
    try:
        rels = ET.fromstring(zf.read(f"xl/worksheets/_rels/sheet{sheet_idx}.xml.rels"))
        for rel in rels:                      # <Relationship Id=.. Target=..>
            rid_target[rel.get("Id")] = rel.get("Target")
    except KeyError:
        pass
    out = []
    rid_attr = f"{{{_PR}}}id"
    for tp in tparts.findall("a:tablePart", _NS):
        target = rid_target.get(tp.get(rid_attr))
        if not target:
            continue
        part = posixpath.normpath(posixpath.join("xl/worksheets", target))
        try:
            t = ET.fromstring(zf.read(part))
        except KeyError:
            continue
        tsi = t.find("a:tableStyleInfo", _NS)
        out.append({"name": t.get("name"), "displayName": t.get("displayName"),
                    "ref": t.get("ref"),
                    "headers": [c.get("name") for c in t.iter(_q("tableColumn"))],
                    "style": tsi.get("name") if tsi is not None else None})
    return out


def probe_file(xlsx: Path, *, sheet: str | None = None) -> list[dict]:
    """Inspect one or all worksheets in a built .xlsx."""
    reps = []
    with zipfile.ZipFile(xlsx) as zf:
        names = _xlsx_sheet_names(zf)
        targets = list(enumerate(names, start=1))
        if sheet is not None:
            if sheet.isdigit():
                idx = int(sheet)
                targets = [(idx, names[idx - 1])]
            else:
                idx = names.index(sheet) + 1
                targets = [(idx, sheet)]
        all_dn = _xlsx_defined_names(zf)
        # Resolve this file's style table by signature once, so cells are labelled by what
        # each style IS even if Excel re-saved + renumbered the table.
        try:
            style_maps = _file_style_maps(zf.read("xl/styles.xml").decode("utf-8"))
        except KeyError:
            style_maps = None
        for i, nm in targets:
            xml = zf.read(f"xl/worksheets/sheet{i}.xml").decode("utf-8")
            rep = {"source": "file", "name": nm, "tab_name": nm,
                   "sheet_index": i}
            rep.update(inspect_worksheet_xml(xml, style_maps))
            rep["tables"] = _xlsx_sheet_tables(zf, i)
            # Defined names whose target references this sheet, or are scoped to
            # it (localSheetId is the zero-based sheet position).
            dn_for_sheet = {}
            for d in all_dn:
                in_target = nm in _referenced_sheets(d["target"])
                scoped = (d["localSheetId"] is not None
                          and d["localSheetId"].isdigit()
                          and int(d["localSheetId"]) == i - 1)
                if in_target or scoped:
                    dn_for_sheet[d["name"]] = d["target"]
            rep["defined_names"] = dn_for_sheet
            reps.append(rep)
    return reps


# ---------------------------------------------------------------------------
# Rendering the report
# ---------------------------------------------------------------------------


def _md(rep: dict) -> str:
    L = [f"# sheet_probe: {rep['name']}", ""]
    L.append(f"- source: `{rep['source']}`")
    if rep.get("tab_name") is not None:
        L.append(f"- tab name: `{rep['tab_name']}`")
    if rep.get("sheet_role"):
        L.append(f"- role: `{rep['sheet_role']}`")
    L.append(f"- tab color: `{rep.get('tab_color')}`")
    L.append(f"- gridlines shown: `{rep.get('gridlines_shown')}`")
    L.append(f"- columns: {rep.get('n_cols')} · rows: {rep.get('n_rows')} · "
             f"cells: {rep.get('n_cells')} · formulas: {rep.get('n_formulas')}")
    L.append("")

    if rep.get("banners"):
        L.append("## Banners")
        for b in rep["banners"]:
            L.append(f"- `{b['ref']}` {b['style']} — {b['text']}")
        L.append("")

    if rep.get("tables"):
        L.append("## Native tables")
        for t in rep["tables"]:
            L.append(f"- `{t['name']}` ref `{t['ref']}` "
                     f"[{', '.join(t['headers'])}] style {t['style']}")
        L.append("")

    if rep.get("defined_names"):
        L.append("## Defined names")
        for k, v in rep["defined_names"].items():
            L.append(f"- `{k}` → `{v}`")
        L.append("")

    if rep.get("notes"):
        L.append(f"## Notes ({len(rep['notes'])})")
        for nt in rep["notes"]:
            txt = str(nt["text"]).replace("\n", " ")
            if len(txt) > 100:
                txt = txt[:100] + "…"
            L.append(f"- `{nt['ref']}` ({nt['author']}) — {txt}")
        L.append("")

    if rep.get("formula_refs_by_sheet"):
        L.append("## Formula dependencies (referenced sheet → cells)")
        for sh, refs in rep["formula_refs_by_sheet"].items():
            shown = ", ".join(refs[:12]) + (" …" if len(refs) > 12 else "")
            L.append(f"- **{sh}** ({len(refs)}): {shown}")
        L.append("")

    if rep.get("hardcoded_inputs"):
        L.append(f"## Hardcoded inputs ({len(rep['hardcoded_inputs'])})")
        for c in rep["hardcoded_inputs"][:40]:
            L.append(f"- `{c['ref']}` {c['style']} = {c['value']}")
        L.append("")

    if rep.get("green_links"):
        L.append(f"## Cross-sheet links ({len(rep['green_links'])})")
        for c in rep["green_links"][:40]:
            L.append(f"- `{c['ref']}` {c['style']} = {c.get('formula')}")
        L.append("")

    if rep.get("placeholders"):
        L.append(f"## Placeholders ({len(rep['placeholders'])})")
        for c in rep["placeholders"]:
            L.append(f"- `{c['ref']}` — {c['value']}")
        L.append("")

    L.append("## Cells")
    for c in rep.get("cells", []):
        body = c.get("formula")
        body = f"={body}" if body is not None else c.get("value", "")
        L.append(f"- `{c['ref']}` {c['style']}: {body}")
    L.append("")
    return "\n".join(L)


def _safe_report_name(name: str) -> str:
    """Slugify a sheet name into a filesystem-safe report stem."""
    s = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))
    s = "_".join(filter(None, s.split("_")))
    return s[:80] or "sheet"


def _report_stem(rep: dict) -> str:
    """Report filename stem: slugified name, prefixed with the sheet index in
    file mode so order is preserved and slug collisions are disambiguated."""
    slug = _safe_report_name(rep["name"])
    idx = rep.get("sheet_index")
    return f"{idx:02d}_{slug}" if isinstance(idx, int) else slug


def _write(rep: dict, out_dir: Path, *, json_only: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _report_stem(rep)   # the real sheet name stays inside the report
    (out_dir / f"{stem}.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    if not json_only:
        (out_dir / f"{stem}.md").write_text(_md(rep), encoding="utf-8")
    kinds = "json" if json_only else "md+json"
    print(f"  wrote {out_dir / stem}.{{{kinds}}}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None, *, default_package: str = "workbook_ddg",
         default_out_dir: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description="Inspect a workbook sheet or .xlsx.")
    ap.add_argument("target", nargs="?",
                    help="dotted module path, .py file, or .xlsx file")
    ap.add_argument("--sheet", help="file mode: sheet index (1-based) or name")
    ap.add_argument("--all", action="store_true",
                    help="probe every sheet (SHEETS registry, or all in the file)")
    ap.add_argument("--json", action="store_true", help="write JSON only")
    ap.add_argument("--out-dir", help="override output directory")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir) if args.out_dir else (
        default_out_dir or Path.cwd() / "reports" / "sheet_probe")

    if not args.target and not args.all:
        ap.error("give a target, or --all")

    # file mode
    if args.target and args.target.endswith(".xlsx"):
        reps = probe_file(Path(args.target),
                          sheet=None if args.all else args.sheet)
        for rep in reps:
            _write(rep, out_dir, json_only=args.json)
        return 0

    # module mode
    if args.all:
        pkg = importlib.import_module(f"{default_package}.sheets")
        mods = getattr(pkg, "SHEETS", [])
        for mod in mods:
            # SHEETS may hold sheet modules, tables.SheetEntry objects (one file
            # -> many tabs), or legacy (name, fn) tuples. probe_module handles
            # modules + SheetEntry; only the legacy tuple is skipped.
            if isinstance(mod, tuple):
                print(f"  skip legacy tuple entry: {mod[0]!r} (module-first only)")
                continue
            _write(probe_module(mod), out_dir, json_only=args.json)
        return 0

    mod = _load_module(args.target)
    _write(probe_module(mod), out_dir, json_only=args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
