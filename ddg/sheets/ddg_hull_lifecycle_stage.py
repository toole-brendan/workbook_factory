"""ddg_hull_lifecycle_stage - DDG Hull x Lifecycle Stage: exact (A/B) subaward $ by build stage.

The construction-stage cut of the EXACT-hull dollars: rows are hulls, columns are the four build
stages (Long-lead / Construction / Outfit-test / Post-delivery). Each cell is a two-criteria SUMIFS
over the DDG Subaward Transactions leaf - keyed on the live `Assigned Hull` (the row) AND the
materialized `Lifecycle Stage` (the column). Constant FY2026$.

Only A/B rows carry an Assigned Hull, so this is the $1.27B exact-hull spend split across phases -
'which suppliers hit in early material vs late outfitting' (briefing §6A). The four stages partition
each hull's Total: every assigned row falls in exactly one stage (a not-yet-launched hull has no
Outfit window, so its in-build spend reads as Construction). Both builders appear (timing, unlike
SWBS, is not HII-only). C/D family-level rows are NOT here - their per-candidate stages live on
DDG C-D Lifecycle Candidates, because a family-level row has no single hull to sum onto.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._fiscal import TX_REAL
from workbook_award_classification_refactor.sheets._tabs import TAB_HULL_LIFECYCLE
from workbook_award_classification_refactor.sheets._cuts import load_table
from workbook_award_classification_refactor.sheets.ddg_subaward_transactions import (
    ddg_tx_cols,
)
from workbook_award_classification_refactor.sheets._widths import W_SHORT_FLAG, W_SUPTYPE, W_DOLLAR

# build stages, in lifecycle order; the label IS the SUMIFS criterion (the materialized `Lifecycle
# Stage` value). These MUST match scripts/_lifecycle.STAGE_* - _integrity.assert_lifecycle_labels_known
# fails the build if a materialized stage ever falls outside this set (the live-vs-Python drift guard).
_STAGES = ["Long-lead", "Construction", "Outfit / test", "Post-delivery"]
HEADERS = ["Hull", "Builder", *_STAGES, "Total $M"]
_WIDTHS = [W_SHORT_FLAG, W_SUPTYPE, *([W_DOLLAR] * len(_STAGES)), W_DOLLAR]

_AHULL = ddg_tx_cols("Assigned Hull")
_STAGE = ddg_tx_cols("Lifecycle Stage")
_REAL = ddg_tx_cols(TX_REAL)


def _spine():
    """(HEADERS, rows) = every hull from the Hull Master, sorted by hull number; Builder filled,
    every dollar cell blank (a live SUMIFS)."""
    hm_headers, hm_rows = load_table("ddg_hull_master")
    hi, bi = hm_headers.index("Hull"), hm_headers.index("Builder")
    out = []
    for r in hm_rows:
        row = [""] * len(HEADERS)
        row[0] = r[hi] if hi < len(r) else ""
        row[1] = r[bi] if bi < len(r) else ""
        out.append(row)
    out.sort(key=lambda x: int("".join(ch for ch in x[0] if ch.isdigit()) or 0))
    return HEADERS, out


_FORMULAS = {
    stage: (lambda crit: lambda r:
            f'=SUMIFS({_REAL},{_AHULL},$B{r},{_STAGE},"{crit}")/1000000')(stage)
    for stage in _STAGES
}
_FORMULAS["Total $M"] = lambda r: f"=SUMIFS({_REAL},{_AHULL},$B{r})/1000000"

DDG_HULL_LIFECYCLE, hull_lifecycle_cols = make_flat_sheet(
    tab=TAB_HULL_LIFECYCLE, group="model",
    csv_name="ddg_hull_lifecycle_stage", table_name="DdgHullLifecycle",
    table=_spine(),
    banner="§1 - DDG-51 exact-hull subaward $ by construction stage ($M)",
    intro="Hull x build stage; A/B exact-hull subawards in constant FY2026$. The four stages "
          "partition each hull's total (not-yet-launched hulls carry no Outfit yet).",
    widths=_WIDTHS,
    float_cols=[*_STAGES, "Total $M"],
    formula_cols=_FORMULAS,
    input_cols=["Hull"],
)
