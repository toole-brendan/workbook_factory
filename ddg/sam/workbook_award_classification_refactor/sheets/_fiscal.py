"""_fiscal - the single definition of the federal-fiscal-year axis (non-sheet helper).

The workbook splits subaward $ into one fixed FY axis: an open-below ≤FY12 catch-all plus
FY2013..FY2026 (FY2026 = the constant-dollar base year). That axis is used by the Deflators
tab (row order), the per-transaction Federal-FY / constant-$ columns, the program-vendor $M
split, and the SWBS roll-up. Defining it ONCE here keeps those in lockstep - changing the
window or base year is a one-edit change, not four parallel edits that can drift.

The economic transformation (calendar date -> federal FY -> constant FY2026$) lives at the
TRANSACTION grain: each fact sheet carries `Federal FY`, `Deflator Factor`, and
`Subaward $ FY2026$` computed columns (tx_fy_formulas), so the program-vendor per-FY cells are
a single SUMIFS over the constant-$ column keyed on UEI + Federal FY (pv_fy_formula), instead
of a date-bounded SUMIFS multiplied by a deflator cell.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import flat_header_letters

FY_BASE = 2026                                  # constant-dollar base year
FY_START = 2013
FY_YEARS = list(range(FY_START, FY_BASE + 1))   # [2013 .. 2026]
LE_CUTOFF = 2012                                # ≤FY12 = federal FY on/before this year
LE_KEY = "≤FY12"

# Deflators tab FY-key column order (one row per bin) - MUST match extracted/deflators.csv.
FY_BIN_KEYS = [LE_KEY] + [f"FY{y}" for y in FY_YEARS]
# Program-vendor $M split headers (≤FY12 $M, FY13 $M .. FY26 $M).
FY_HEADERS = [f"{LE_KEY} $M"] + [f"FY{y % 100} $M" for y in FY_YEARS]

# Per-transaction computed-column headers (sheet-only; passed as make_flat_sheet extra_cols).
TX_FED_FY = "Federal FY"
TX_FACTOR = "Deflator Factor"
TX_REAL = "Subaward $ FY2026$"
TX_EXTRA_COLS = [TX_FED_FY, TX_FACTOR, TX_REAL]


def _federal_fy_expr(date_cell: str) -> str:
    """Federal FY of a calendar action date (the fiscal year starts Oct 1)."""
    return f"YEAR({date_cell})+--(MONTH({date_cell})>=10)"


def tx_fy_formulas(csv_name: str, *, date_header: str, amount_header: str,
                   extra_cols: list, note_from=None) -> dict:
    """{header: fn(r)->'=...'} for the three transaction-grain FY columns, every column
    letter resolved by NAME (flat_header_letters). `extra_cols` is the sheet's FULL extra
    list (e.g. SWBS Match Row + the three FY columns) so the resolved letters line up with
    what make_flat_sheet builds. Deflator Factor maps this row's Federal FY to the matching
    Deflators-tab factor; Subaward $ FY2026$ = nominal amount x that factor."""
    from workbook_award_classification_refactor.sheets.deflators import deflators_cols
    L = flat_header_letters(csv_name, note_from=note_from, extra_cols=extra_cols)
    fy_keys = deflators_cols("FY")                    # 'Deflators'!$B$f:$B$l (text bin keys)
    factors = deflators_cols("Factor to FY2026 $")    # 'Deflators'!$D$f:$D$l

    def fed_fy(r):
        date_cell = f"${L[date_header]}{r}"
        # A blank date must stay blank. Without this guard Excel treats the blank as serial 0,
        # maps it to FY1900 / the <=FY12 bucket, and silently deflates an undated transaction.
        return f'=IF({date_cell}="","",{_federal_fy_expr(date_cell)})'

    def factor(r):
        fy = f"${L[TX_FED_FY]}{r}"
        key = f'IF({fy}<={LE_CUTOFF},"{LE_KEY}","FY"&{fy})'
        # A post-axis FY intentionally remains #N/A via MATCH, forcing the deflator table / axis
        # to be extended rather than silently dropping or mis-binning new transactions.
        return f'=IF({fy}="","",INDEX({factors},MATCH({key},{fy_keys},0)))'

    def real(r):
        amount = f"${L[amount_header]}{r}"
        factor_cell = f"${L[TX_FACTOR]}{r}"
        return f'=IF(OR({amount}="",{factor_cell}=""),"",{amount}*{factor_cell})'

    return {TX_FED_FY: fed_fy, TX_FACTOR: factor, TX_REAL: real}


def pv_fy_formula(real_range: str, uei_range: str, fedfy_range: str, header: str):
    """fn(r)->'=...' for a program-vendor per-FY $M cell: SUMIFS the transaction constant-
    FY2026$ column keyed on this row's UEI and the FY bin for `header` (exact federal year,
    or '<=2012' for the ≤FY12 catch-all), expressed in $M."""
    if header == f"{LE_KEY} $M":
        crit = f'{fedfy_range},"<={LE_CUTOFF}"'
    else:
        crit = f"{fedfy_range},{2000 + int(header[2:4])}"     # "FY13 $M" -> 2013
    return lambda r: f"=SUMIFS({real_range},{uei_range},$B{r},{crit})/1000000"


def pv_lifetime_formula(real_range: str, uei_range: str):
    """fn(r)->'=...' for the lifetime Subaward $M: full constant-FY2026$ over this UEI, $M.
    Equals the sum of the per-FY split as long as no transaction post-dates FY2026."""
    return lambda r: f"=SUMIFS({real_range},{uei_range},$B{r})/1000000"


def first_last_or_na(date_range: str, key_range: str, kind: str = "MIN"):
    """fn(r)->'=...' for a First / Last Subaward date that shows "n/a" instead of the 1900 epoch
    when the row's key (col B) matches zero transactions. MINIFS / MAXIFS return 0 over an empty
    set, which a date format renders as 1900-01-00; guard on a COUNTIFS over the same key so a
    keyless row (e.g. a hull with no assigned subaward) reads "n/a" rather than a phantom date."""
    fn = "MINIFS" if kind == "MIN" else "MAXIFS"
    return lambda r: (f'=IF(COUNTIFS({key_range},$B{r})=0,"n/a",'
                      f'_xlfn.{fn}({date_range},{key_range},$B{r}))')
