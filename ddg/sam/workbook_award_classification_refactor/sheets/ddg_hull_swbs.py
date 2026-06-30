"""ddg_hull_swbs - DDG Hull x SWBS: assigned subaward $ by hull and ship-system major group.

A matrix roll-up: rows are HII-Ingalls hulls, columns are SWBS major groups (100..700 plus the
X00 / L00 cross-cutting and U00 unmapped tails). Each cell is a two-criteria SUMIFS over the DDG
Subaward Transactions leaf - keyed on the materialized `Assigned Hull` (the row) AND a wildcard on
the live `SWBS` display column (whose value starts with the major-group number, e.g. "500 ...").
Constant FY2026$.

HII-Ingalls only by design: GD-BIW subawards carry no SWBS classification (their `SWBS` reads
"n/a (non-HII-Ingalls)"), so a BIW hull row would be all zeros and read misleadingly as "no spend"
rather than "not classified". The spine is therefore filtered to HII hulls; `Total $M` is the
hull's full assigned $ and equals the row's group sum (the SWBS groups partition every HII row).
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._fiscal import TX_REAL
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_SWBS
from workbook_award_classification_refactor.sheets._cuts import load_table
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)
from workbook_award_classification_refactor.sheets._widths import W_SHORT_FLAG, W_DOLLAR

# (column label, SWBS-display wildcard). The wildcard matches the major-group number the SWBS
# display string starts with. 800/900 do not occur in the DDG-HII data; if they appear later they
# surface as a gap between Total $M and the visible group columns.
_GROUPS = [
    ("100 Hull", "100*"), ("200 Prop", "200*"), ("300 Elec", "300*"),
    ("400 C4ISR", "400*"), ("500 Aux", "500*"), ("600 Outfit", "600*"),
    ("700 Arm", "700*"), ("X00 Cross", "X00*"), ("L00 Legacy", "L00*"),
    ("U00 None", "U00*"),
]
HEADERS = ["Hull", *[lab for lab, _ in _GROUPS], "Total $M"]
_WIDTHS = [W_SHORT_FLAG, *([W_DOLLAR] * len(_GROUPS)), W_DOLLAR]

_AHULL = ddg_tx_cols("Assigned Hull")
_SWBS = ddg_tx_cols("SWBS")
_REAL = ddg_tx_cols(TX_REAL)


def _spine():
    """(HEADERS, rows) = HII-Ingalls hulls from the Hull Master, sorted by hull number; every
    dollar cell blank (a live formula)."""
    hm_headers, hm_rows = load_table("ddg_hull_master")
    hi, bi = hm_headers.index("Hull"), hm_headers.index("Builder")
    out = []
    for r in hm_rows:
        if (r[bi] if bi < len(r) else "").strip() != "HII-Ingalls":
            continue
        row = [""] * len(HEADERS)
        row[0] = r[hi] if hi < len(r) else ""
        out.append(row)
    out.sort(key=lambda x: int("".join(ch for ch in x[0] if ch.isdigit()) or 0))
    return HEADERS, out


_FORMULAS = {
    lab: (lambda crit: lambda r:
          f'=SUMIFS({_REAL},{_AHULL},$B{r},{_SWBS},"{crit}")/1000000')(c)
    for lab, c in _GROUPS
}
_FORMULAS["Total $M"] = lambda r: f"=SUMIFS({_REAL},{_AHULL},$B{r})/1000000"

DDG_HULL_SWBS, hull_swbs_cols = make_flat_sheet(
    tab=TAB_HULL_SWBS, group="model",
    csv_name="ddg_hull_swbs", table_name="DdgHullSwbs",
    table=_spine(),
    banner="§1 - DDG-51 HII hulls x SWBS ship-system ($M)",
    intro="HII-Ingalls hulls x SWBS major group; assigned subawards in constant FY2026$.",
    widths=_WIDTHS,
    float_cols=[lab for lab, _ in _GROUPS] + ["Total $M"],
    formula_cols=_FORMULAS,
    input_cols=["Hull"],
)
