"""_periods - the single source of truth for the model's fiscal-year windows.

FY  = the FY2022-2027 budget window every cost grid spans (P-5c, OBBBA, the
      per-program TAM-by-FY grids, the cumulative/average roll-up).
OY  = the FY2028-2031 FYDP outyear window the outlook band projects over.

Centralizing these stops the list from drifting across the sheet modules (it was
previously copy-pasted in assumptions, scn_budget, obbba, and the program builder).
The window is FIXED - the model is not parameterized over an arbitrary FY range -
so these are plain module constants, not workbook knobs.
"""
from __future__ import annotations

FY = [2022, 2023, 2024, 2025, 2026, 2027]
OY = [2028, 2029, 2030, 2031]
