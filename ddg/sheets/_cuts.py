"""DDG workbook CSV accessors for the consolidated data tree."""
from __future__ import annotations

import csv
from datetime import date

from ddg.lib import resolve_csv

_EPOCH = date(1899, 12, 30)

def load_grid(name: str) -> list[list[str]]:
    with resolve_csv(name).open(encoding="utf-8", newline="") as fh:
        return [list(r) for r in csv.reader(fh)]

def load_table(name: str) -> tuple[list[str], list[list[str]]]:
    grid = load_grid(name)
    if not grid:
        return [], []
    return grid[0], grid[1:]

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
