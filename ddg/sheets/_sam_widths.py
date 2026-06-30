"""_widths - standardized column widths + header-alignment helper.

Local non-sheet helper (like _layout / _cuts). Centralizes the column-width
vocabulary so every sheet sizes a given column TYPE the same way instead of
hand-picking a number per sheet - the workbook reads as one ruled system. Widths
are Excel character units (the `cols=[...]` values passed to worksheet()); the
~1.5-char gutter is prepended by worksheet(with_gutter=True), so these map to
content columns starting at column B.

These sheets carry long free-text columns (work descriptions, definitions,
verification notes, source-URL lists). The workbook standard is no wrapped text,
so a prose column is sized wide enough to read the opening clause; the rest
overflows into neighbouring blank cells / is reached by widening or via the
formula bar. Identifier and numeric columns stay compact.

header_styles() encodes the header-alignment rule: every column header is
left-aligned EXCEPT numeric columns named in center_headers, which are centered.
(Numbers right-align in the data rows via their number formats; this is only the
header cell.)
"""
from __future__ import annotations

from workbook_core.styles import S_HEADER_LEFT, S_HEADER_CENTER

# ---------------------------------------------------------------------------
# Column widths by semantic type (Excel character units)
# ---------------------------------------------------------------------------

# Identifiers / short labels
W_RANK       = 10    # Rank / Input Row / input_row_number (1, 2, 3, ...)
W_UEI        = 14    # vendor UEI
W_CAGE       = 10    # CAGE code
W_CODE       = 10    # taxonomy ID / code (01, EM, VB, ...)
W_NAICS      = 11    # NAICS code
W_SHORT_FLAG = 15    # short code / basis / date-range column (archetype codes, bases, first/last)
W_DOMFOR     = 20    # domestic-or-foreign flag
W_PIID       = 22    # prime contract PIID
W_REPORTID   = 16    # subaward report id
W_DATE       = 14    # ISO date (real date serial)
W_PROGRAM    = 10    # program label (DDG / Virginia / Columbia)
W_COUNTRY    = 16    # country of performance / origin
W_FY         = 10    # federal fiscal year

# Names / terms
W_VENDOR     = 31    # vendor name (long edge-case names clip)
W_NAME       = 27    # normalized vendor / business-unit name
W_TERM       = 30    # taxonomy term (capability domain / role / physical-form name)
W_SUPTYPE    = 16    # supplier type (integrator/OEM, manufacturer, ...)

# Numeric
W_DOLLAR     = 12    # $M summary columns (Total / Submarines / DDG-51)
W_COUNT      = 13    # record-count column
W_RATIO      = 14    # percentage / rate columns (share, retention, incumbency)
W_STATUS     = 18    # medium status or descriptive header columns
W_METRIC     = 18    # effective-count and similar metric columns
W_CLASS      = 16    # compact classification-code columns (e.g. Structure Class)

# Short-phrase categorical columns
W_WORKTYPE   = 30    # work type / work-type id (the bucketed label)
W_CATEGORY   = 28    # delivery / output / assignment category labels
W_NAICS_DESC = 31    # NAICS description

# Free text (no-wrap; sized to read the opening clause)
W_TEXT       = 35    # general prose (basis, what-they-make, products)
W_TEXT_WIDE  = 42    # long prose (definitions, role summaries, evidence notes)
W_URL        = 44    # source-URL list

# Raw subaward-transaction fields (the faithful FSRS published-record pull)
W_UUID       = 31    # subaward report number (UUID)
W_SUBNUM     = 18    # subaward number (810920-1 / PPC085=031)
W_AMOUNT     = 16    # raw subaward amount in dollars
W_TCV        = 18    # total prime contract value in dollars
W_STREET2    = 14    # address line 2 (mostly blank)
W_CITY       = 18    # city
W_CD         = 12    # congressional district
W_STATE      = 16    # state name
W_CC         = 12    # country code
W_ZIP        = 12    # zip
W_BIZCODE    = 14    # joined business-type codes
W_PAY        = 16    # joined top-pay salaries
W_CONTRACTKEY= 34    # prime contract key (CONT_AWD_...)
W_REFIDV     = 14    # referenced IDV agency id (blank field, kept)
W_AWARDTYPE  = 14    # prime award type (AWARD)
W_ORGCODE    = 12    # funding/contracting agency-office-dept codes


# ---------------------------------------------------------------------------
# Header alignment
# ---------------------------------------------------------------------------

def header_styles(headers: list[str], center_headers=()) -> list[int]:
    """Header-row styles: left-align text headers; center any numeric columns
    named in `center_headers`. Pass the same header strings used in the header
    write_row plus the subset that are numeric, e.g.

        c.write(HEADERS, styles=header_styles(HEADERS, center_headers=NUMERIC))
    """
    centered = set(center_headers)
    return [S_HEADER_CENTER if h in centered else S_HEADER_LEFT for h in headers]
