"""deflators - shared DoD price-deflator index for constant-dollar restatement.

Single source of truth for converting the DDG and submarine TAM/SAM workbooks from
nominal then-year dollars to constant FY2026 dollars. Pure data + helpers (no styling),
mirroring the data-only convention of groups.py - each workbook's data_deflators sheet
renders this table as auditable work and promotes a deflator_factor_cell(fy) that the
budget sheets link to.

Source: OSD National Defense Budget Estimates for FY2025 ("Green Book"), Table 5-4
"DoD Deflators - TOA by Public Law Title", Procurement column (FY2025 = 100). SCN is a
procurement appropriation and inherits the Procurement deflator - the Green Book
publishes no Navy- or SCN-specific deflator. Base year 2025; rebased here to FY2026.

  factor(fy) = PROCUREMENT_TOA[2026] / PROCUREMENT_TOA[fy]
  constant_FY2026_$ = then_year_$ * factor(fy)
"""
from __future__ import annotations

FY_RANGE = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031]
BASE_FY = 2026

# Green Book FY2025 edition, Table 5-4, Procurement TOA, FY2025 = 100 (pp. 58-59).
# Table 5-4 ends at FY2029; FY2030-FY2031 are extrapolated at the Green Book's
# steady-state purchases inflation, 2.1%/yr (Table 5-3, Other Purchases).
PROCUREMENT_TOA = {
    2022: 93.13,
    2023: 95.77,
    2024: 97.92,
    2025: 100.00,
    2026: 102.10,
    2027: 104.24,
    2028: 106.43,
    2029: 108.67,
    2030: 110.95,  # 108.67 * 1.021
    2031: 113.28,  # 110.95 * 1.021
}

EXTRAPOLATED_FYS = {2030, 2031}

GREEN_BOOK_CITE = (
    "OSD National Defense Budget Estimates for FY2025 (Green Book), Table 5-4 "
    "Procurement TOA, FY2025=100 (pp. 58-59 / PDF pp. 65-66); rebased to FY2026=1.000"
)

GREEN_BOOK_EXTRAP_CITE = (
    "FY2030-FY2031 extrapolated at 2.1%/yr (Green Book Table 5-3 steady-state "
    "purchases inflation); Table 5-4 ends at FY2029"
)


def raw_index(fy: int) -> float:
    """Green Book Procurement TOA deflator for `fy` (FY2025 = 100)."""
    if fy not in PROCUREMENT_TOA:
        raise ValueError(f"FY {fy!r} outside {FY_RANGE!r}")
    return PROCUREMENT_TOA[fy]


def factor(fy: int) -> float:
    """Multiplier converting then-year `fy` dollars to constant FY2026 dollars."""
    return PROCUREMENT_TOA[BASE_FY] / raw_index(fy)
