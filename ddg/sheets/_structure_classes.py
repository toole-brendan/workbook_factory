"""Shared thresholds and labels for the annual structure screen.

One source of truth for the Program x Archetype x FY "structure class" screen that
Where to Play computes and the Executive Summary / Methodology present. The five
classes are MECE over the two underlying dimensions (Parent HHI, incumbent-dollar
share) plus a low-supplier-count exception, so each label maps directly to the math
that produced it instead of the former interpretive partner-led / rotating vocabulary.
Where to Play's _f_structure() emits these; guide_methodology renders STRUCTURE_RULES
as a definition table so the legend cannot drift from the formula.
"""
from __future__ import annotations

MIN_ACTIVE_SUPPLIERS = 3
HIGH_PARENT_HHI = 0.40
HIGH_INCUMBENT_DOLLAR_SHARE = 0.75

LOW_COUNT = "Low Count"
HHI_H_INC_H = "HHI-H / Inc-H"
HHI_H_INC_L = "HHI-H / Inc-L"
HHI_L_INC_H = "HHI-L / Inc-H"
HHI_L_INC_L = "HHI-L / Inc-L"

STRUCTURE_CLASSES = (
    LOW_COUNT,
    HHI_H_INC_H,
    HHI_H_INC_L,
    HHI_L_INC_H,
    HHI_L_INC_L,
)

STRUCTURE_RULES = (
    (LOW_COUNT, "Active suppliers < 3"),
    (HHI_H_INC_H, "Parent HHI >= 0.40; incumbent $ >= 75%"),
    (HHI_H_INC_L, "Parent HHI >= 0.40; incumbent $ < 75%"),
    (HHI_L_INC_H, "Parent HHI < 0.40; incumbent $ >= 75%"),
    (HHI_L_INC_L, "Parent HHI < 0.40; incumbent $ < 75%"),
)
