"""prime_awards - the in-scope prime contracts (USAspending award detail).

A data-group reference sheet, one row per in-scope prime PIID (13 today), pulled by
scripts/pull_prime_awards.py from USAspending award detail. It carries the authoritative
prime period of performance and obligations - the prime fields embedded on the subaward
rows are per-report snapshots and must not be trusted for the prime timeline.

Prime dollars are NOMINAL cumulative obligations (not deflated to FY2026$ like the subaward
columns); the PoP runs through option years. Pure materialized reference - no live formulas.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import make_flat_sheet
from workbook_award_classification_refactor.sheets._tabs import TAB_PRIME_AWARDS
from workbook_award_classification_refactor.sheets._widths import (
    W_PROGRAM, W_PIID, W_VENDOR, W_TEXT_WIDE, W_DATE, W_DOLLAR, W_COUNT, W_SUPTYPE,
)

# Program | PIID | Entity | Description | Block/MYP | DateSigned | PoP x3 | $ x2 | count | $
_WIDTHS = [W_PROGRAM, W_PIID, W_VENDOR, W_TEXT_WIDE, W_SUPTYPE,
           W_DATE, W_DATE, W_DATE, W_DATE,
           W_DOLLAR, W_DOLLAR, W_COUNT, W_DOLLAR]

PRIME_AWARDS, prime_awards_cols = make_flat_sheet(
    tab=TAB_PRIME_AWARDS, group="data",
    csv_name="prime_awards", table_name="PrimeAwards",
    banner="§1 - In-scope prime contracts (USAspending award detail)",
    intro=("One row per in-scope prime PIID: prime period of performance (through option "
           "years) and obligations (nominal)."),
    widths=_WIDTHS,
    int_cols=["USAspending Subaward Count"],
    float_cols=["Total Obligated $M (nominal)", "Base + All Options $M (nominal)",
                "USAspending Subaward $M"],
    date_cols=["Date Signed", "PoP Start", "PoP Current End", "PoP Potential End"],
    input_cols=["Prime PIID"],
    # Shorten the verbose numeric headers (display only; the canonical names still drive the
    # cols accessor that subaward_activity reads) so they sit over their dollar/count columns.
    display_headers={
        "Total Obligated $M (nominal)": "Total Oblig $M",
        "Base + All Options $M (nominal)": "Base+Options $M",
        "USAspending Subaward Count": "Subaward Count",
        "USAspending Subaward $M": "Subaward $M",
    },
)
