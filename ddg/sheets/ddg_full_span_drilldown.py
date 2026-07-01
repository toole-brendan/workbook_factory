"""ddg_full_span_drilldown - DDG 125/128: exact-hull subaward $ by build stage, own-schedule.

A SCOPED, honest replacement for the retired program-wide hull x lifecycle-stage exhibit. It shows
the five-stage split for the ONLY two hulls (DDG 125, DDG 128) whose exact-hull (A/B) subaward
coverage spans the full advance-material-to-delivery arc unclipped by the SAM window - so their
stage mix is not an artifact of a truncated observation period. It is deliberately NOT
class-representative; the whole-program timing story lives on DDG Procurement Timing (all rows,
grain-safe). This sheet exists so the reader can see one clean per-hull build sequence WITHOUT the
old program-wide aggregate that dumped not-yet-keeled hulls' whole totals into Long-lead.

No stage column is reintroduced on the transaction leaf. Each stage cell is a date-window SUMIFS
over the leaf, keyed on the live `Assigned Hull` (grades A/B only) AND a date band bounded by THAT
hull's own Start Fabrication / Keel / Launch / Delivery, pulled live from DDG Hull Master (the 'Mon YYYY'
milestone text converted to a serial in-formula, locale-independent). The bands + an Undated
residual partition each hull's exact-hull total; the Checks tab asserts the partition. Constant
FY2026$. Both hulls carry complete, curated (MIRS-sourced) milestones, so every band bound resolves.

Promoted accessor (Checks): full_span_cols(header) -> "'DDG 125 & 128 Full-Span'!$X$first:$X$last".
"""
from __future__ import annotations

from ddg.sheets.kit.flat import make_flat_sheet
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.kit.tabs import TAB_FULL_SPAN
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols
from ddg.sheets.ddg_hull_master import hull_master_cols
from ddg.sheets.kit.widths import W_SHORT_FLAG, W_DATE, W_DOLLAR, W_COUNT

# The two full-span hulls (their own schedules bound the stage bands). Deliberately fixed - this is a
# scoped illustration, not a class rollup; do not derive from the Hull Master (that is the trap the
# retired program-wide sheet fell into).
_HULLS = ["DDG 125", "DDG 128"]

# Hull | Start Fab | Keel | Launch | Delivery || Long-lead | Fabrication | Construction | Outfit/test |
#   Post-delivery | Undated | Total | Records   (the four milestone serials are $C/$D/$E/$F per row)
HEADERS = ["Hull", "Start Fab", "Keel", "Launch", "Delivery",
           "Long-lead $M", "Fabrication $M", "Construction $M", "Outfit / test $M",
           "Post-delivery $M", "Undated $M", "Total $M", "Records"]
_WIDTHS = [W_SHORT_FLAG, W_DATE, W_DATE, W_DATE, W_DATE,
           W_DOLLAR, W_DOLLAR, W_DOLLAR, W_DOLLAR, W_DOLLAR, W_DOLLAR, W_DOLLAR, W_COUNT]

_REAL = ddg_tx_cols(TX_REAL)
_AHULL = ddg_tx_cols("Assigned Hull")
_DATE = ddg_tx_cols("Subaward Date")
_HM_HULL = hull_master_cols("Hull")
_HM_FAB = hull_master_cols("Start Fabrication")
_HM_KEEL = hull_master_cols("Keel Laid")
_HM_LAUNCH = hull_master_cols("Launch")
_HM_DELIV = hull_master_cols("Delivery")

# Convert a curated 'Mon YYYY' milestone (Hull Master text) to a date serial, locale-independent:
# DATE(year, month-number, 1). LEFT/RIGHT split the token; the month array maps the 3-letter month.
_MONTHS = '{"Jan";"Feb";"Mar";"Apr";"May";"Jun";"Jul";"Aug";"Sep";"Oct";"Nov";"Dec"}'


def _milestone(col_range):
    """This row hull's milestone from Hull Master (INDEX/MATCH on the hull name in $B), as a serial."""
    def f(r):
        text = f"INDEX({col_range},MATCH($B{r},{_HM_HULL},0))"
        return (f'=IFERROR(DATE(RIGHT({text},4),'
                f'MATCH(LEFT({text},3),{_MONTHS},0),1),"")')
    return f


def _spine():
    """(HEADERS, rows): one row per full-span hull, Hull filled, every computed cell blank."""
    rows = []
    for h in _HULLS:
        row = [""] * len(HEADERS)
        row[0] = h
        rows.append(row)
    return HEADERS, rows


# Stage bands over the leaf: Assigned Hull = this row's hull AND Subaward Date in the band bounded by
# the row's own Start Fab ($C) / Keel ($D) / Launch ($E) / Delivery ($F) serials. Long-lead is now
# strictly pre-first-steel; Fabrication (Start Fab -> Keel) is split out from Construction (Keel ->
# Launch). Undated = the blank-date residual; Total = the direct SUMIFS (Checks partition is independent).
_FORMULAS = {
    "Start Fab": _milestone(_HM_FAB),
    "Keel":      _milestone(_HM_KEEL),
    "Launch":    _milestone(_HM_LAUNCH),
    "Delivery":  _milestone(_HM_DELIV),
    "Long-lead $M":     lambda r: f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},"<"&$C{r})/1000000',
    "Fabrication $M":   lambda r: (f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},">="&$C{r},'
                                   f'{_DATE},"<"&$D{r})/1000000'),
    "Construction $M":  lambda r: (f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},">="&$D{r},'
                                   f'{_DATE},"<"&$E{r})/1000000'),
    "Outfit / test $M": lambda r: (f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},">="&$E{r},'
                                   f'{_DATE},"<"&$F{r})/1000000'),
    "Post-delivery $M": lambda r: f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},">="&$F{r})/1000000',
    "Undated $M":       lambda r: f'=SUMIFS({_REAL},{_AHULL},$B{r},{_DATE},"")/1000000',
    "Total $M":         lambda r: f'=SUMIFS({_REAL},{_AHULL},$B{r})/1000000',
    "Records":          lambda r: f'=COUNTIFS({_AHULL},$B{r})',
}

DDG_FULL_SPAN, full_span_cols = make_flat_sheet(
    tab=TAB_FULL_SPAN, group="model",
    csv_name="ddg_full_span_drilldown", table_name="DdgFullSpanDrilldown",
    table=_spine(),
    banner="§1 - DDG 125/128 exact-hull subaward $ by build stage ($M)",
    intro="Illustrative full-span exhibit: the only two hulls (DDG 125, DDG 128) with unclipped "
          "AP/LLTM-to-delivery exact-hull coverage - not class-representative (the whole-program "
          "timing story is on DDG Procurement Timing). Stages are referenced to each hull's own "
          "Start Fabrication / Keel / Launch / Delivery from DDG Hull Master: Long-lead = pre-first-"
          "steel advance material; Fabrication = first-steel to keel; Construction = keel to launch; "
          "Outfit / test = launch to delivery. Both hulls predate the FY18-22 block-outsourcing "
          "program (that activity is on 135/137/139). Constant FY2026$.",
    widths=_WIDTHS,
    date_cols=["Start Fab", "Keel", "Launch", "Delivery"],
    float_cols=["Long-lead $M", "Fabrication $M", "Construction $M", "Outfit / test $M",
                "Post-delivery $M", "Undated $M", "Total $M"],
    int_cols=["Records"],
    formula_cols=_FORMULAS,
    input_cols=["Hull"],
    link_cols=["Start Fab", "Keel", "Launch", "Delivery", "Records"],
)
