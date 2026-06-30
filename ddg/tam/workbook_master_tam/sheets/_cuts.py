"""DDG TAM CSV accessors.

Historical TAM sheet modules still request legacy CSV stems such as
``scn_budget``.  The files now live in the consolidated DDG data tree with
explicit DDG/reference names; ``ddg.lib`` owns that mapping.
"""
from __future__ import annotations

import csv

from ddg.lib import resolve_tam_csv

def load_grid(name: str) -> list[list[str]]:
    """Full row-major grid for a DDG TAM workbook-input CSV as raw strings."""
    with resolve_tam_csv(name).open(encoding="utf-8", newline="") as fh:
        return [list(r) for r in csv.reader(fh)]

def load_table(name: str) -> tuple[list[str], list[list[str]]]:
    """(headers, data_rows) for a flat-table CSV: row 0 is the header row."""
    grid = load_grid(name)
    if not grid:
        return [], []
    return grid[0], grid[1:]

def load_rows(name: str) -> list[dict[str, str]]:
    """List of {header: cell} dicts (DictReader-style), raw strings."""
    headers, rows = load_table(name)
    return [dict(zip(headers, r)) for r in rows]

def as_int(s):
    """'' / None -> None; '5' -> 5 (rank / count / FY columns)."""
    s = (s or "").strip()
    return int(s) if s else None

def as_float(s):
    """'' / None -> None; '2001.391' -> 2001.391 ($M columns)."""
    s = (s or "").strip()
    return float(s.replace(",", "")) if s else None

def cell(s):
    """Raw text cell -> the string, or None for blank."""
    s = s if s is not None else ""
    return s if s != "" else None
