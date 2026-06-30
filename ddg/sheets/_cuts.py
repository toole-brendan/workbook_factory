"""DDG workbook CSV accessors for the consolidated data tree."""
from __future__ import annotations

import csv
from datetime import date
from functools import lru_cache

from ddg.lib import resolve_csv, SAM_TX_FY_START, SAM_TX_FY_END

_EPOCH = date(1899, 12, 30)


def _federal_fy(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        y, m, _d = (int(x) for x in raw[:10].split("-"))
    except Exception:
        return None
    return y + int(m >= 10)


def _in_sam_window(fy: int | None) -> bool:
    return fy is not None and SAM_TX_FY_START <= fy <= SAM_TX_FY_END


def load_grid(name: str) -> list[list[str]]:
    with resolve_csv(name).open(encoding="utf-8", newline="") as fh:
        return [list(r) for r in csv.reader(fh)]


def _load_table_raw(name: str) -> tuple[list[str], list[list[str]]]:
    grid = load_grid(name)
    if not grid:
        return [], []
    return grid[0], grid[1:]


@lru_cache(maxsize=1)
def _window_tx_keys() -> frozenset[tuple[str, str]]:
    headers, rows = _load_table_raw("ddg_subaward_transactions")
    if not headers:
        return frozenset()
    ju, jd = headers.index("Subawardee UEI"), headers.index("Subaward Date")
    keys: set[tuple[str, str]] = set()
    for r in rows:
        fy = _federal_fy(r[jd] if jd < len(r) else "")
        uei = (r[ju] if ju < len(r) else "").strip()
        if _in_sam_window(fy) and uei:
            keys.add(("DDG", uei))
    return frozenset(keys)


@lru_cache(maxsize=1)
def _window_tx_report_ids() -> frozenset[str]:
    headers, rows = _load_table_raw("ddg_subaward_transactions")
    if not headers:
        return frozenset()
    jd = headers.index("Subaward Date")
    jr = headers.index("Subaward Report ID") if "Subaward Report ID" in headers else headers.index("subAwardReportId")
    ids: set[str] = set()
    for r in rows:
        fy = _federal_fy(r[jd] if jd < len(r) else "")
        rid = (r[jr] if jr < len(r) else "").strip()
        if _in_sam_window(fy) and rid:
            ids.add(rid)
    return frozenset(ids)


def _filter_sam_window(name: str, headers: list[str], rows: list[list[str]]) -> list[list[str]]:
    """Runtime SAM transaction window, leaving archived source CSVs intact.

    The visible workbook uses FY2016-FY2025 for DDG observed SAM.  Raw CSV files stay as
    the full pull; this accessor trims transaction-derived spines so all downstream
    formulas, guards and roll-ups share the same reader-facing window.
    """
    if not headers or not rows:
        return rows

    if name == "ddg_subaward_transactions" and "Subaward Date" in headers:
        jd = headers.index("Subaward Date")
        return [r for r in rows if _in_sam_window(_federal_fy(r[jd] if jd < len(r) else ""))]

    if name == "supplier_year_activity" and "Federal FY" in headers:
        jf = headers.index("Federal FY")
        out = []
        for r in rows:
            raw = (r[jf] if jf < len(r) else "").strip()
            fy = int(raw) if raw.isdigit() else None
            if _in_sam_window(fy):
                out.append(r)
        return out

    if name == "supplier_master" and {"Program", "Subawardee UEI"} <= set(headers):
        jp, ju = headers.index("Program"), headers.index("Subawardee UEI")
        keys = _window_tx_keys()
        return [r for r in rows
                if (((r[jp] if jp < len(r) else "").strip(),
                     (r[ju] if ju < len(r) else "").strip()) in keys)]

    if name == "ddg_program_vendors" and "Subawardee UEI" in headers:
        ju = headers.index("Subawardee UEI")
        ueis = {uei for program, uei in _window_tx_keys() if program == "DDG"}
        return [r for r in rows if (r[ju] if ju < len(r) else "").strip() in ueis]

    if name in {"ddg_hull_exceptions", "ddg_cd_lifecycle_rollup", "ddg_cd_lifecycle_candidates"}:
        rid_header = "Subaward Report ID"
        if rid_header in headers:
            jr = headers.index(rid_header)
            ids = _window_tx_report_ids()
            return [r for r in rows if (r[jr] if jr < len(r) else "").strip() in ids]

    return rows


def load_table(name: str) -> tuple[list[str], list[list[str]]]:
    headers, rows = _load_table_raw(name)
    return headers, _filter_sam_window(name, headers, rows)


def load_headers(name: str) -> list[str]:
    with resolve_csv(name).open(encoding="utf-8", newline="") as fh:
        return next(csv.reader(fh), [])


def load_rows(name: str) -> list[dict[str, str]]:
    headers, rows = load_table(name)
    return [dict(zip(headers, r)) for r in rows]


def cy_bounds(stem: str, date_header: str = "Subaward Date") -> tuple[int | None, int | None]:
    headers, rows = load_table(stem)
    j = headers.index(date_header)
    yrs = [int(r[j][:4]) for r in rows if j < len(r) and (r[j] or "").strip()[:4].isdigit()]
    return (min(yrs), max(yrs)) if yrs else (None, None)


def cy_span(stem: str, date_header: str = "Subaward Date") -> str:
    lo, hi = cy_bounds(stem, date_header)
    return f"CY{lo}-{hi}" if lo is not None else ""


def cy_span_union(stems: list[str], date_header: str = "Subaward Date") -> str:
    bounds = [cy_bounds(s, date_header) for s in stems]
    los = [lo for lo, _ in bounds if lo is not None]
    his = [hi for _, hi in bounds if hi is not None]
    return f"CY{min(los)}-{max(his)}" if los else ""


def as_int(s):
    s = (s or "").strip()
    return int(s) if s else None


def as_float(s):
    s = (s or "").strip()
    return float(s.replace(",", "")) if s else None


def cell(s):
    s = s if s is not None else ""
    return s if s != "" else None


def date_serial(s):
    if not s:
        return None
    y, m, d = (int(p) for p in str(s)[:10].split("-"))
    return (date(y, m, d) - _EPOCH).days
