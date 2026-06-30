"""ddg_tam - the "DDG-51 TAM" tab (model group).

DDG-51 Arleigh Burke (LI 2122): BC stream + AP/LLTM stream (P-10 Ship Construction
EOQ) + OBBBA mandatory stream (Sec. 20002(17)), plus the folded FY2028-31 outyear
projection. The BC coefficient is FY2022-vintage (FY18-22 masters) for FY2022 and
MYP-corrected (FY23-27 masters folded into the corpus) for FY2023-27.
"""
from __future__ import annotations

from workbook_master_tam.sheets._program_tam import build_program_tam
from workbook_master_tam.sheets._tabs import TAB_DDG_TAM
from workbook_master_tam.sheets.place_of_performance import (
    ddg_bc_coeff_cell, ddg_bc_coeff_fy22_cell,
)

DDG_TAM, _A = build_program_tam(
    li=2122, name="DDG-51", tab=TAB_DDG_TAM,
    intro="DDG-51 BC, AP/LLTM, and OBBBA TAM, FY2022-31",
    bc_coeff_cell=ddg_bc_coeff_cell, bc_coeff_fy22_cell=ddg_bc_coeff_fy22_cell,
    obbba="const", ap=True, biw_carveout=True)

tam_cell = _A["tam_cell"]
cum_tam_cell = _A["cum_tam_cell"]
avg_annual_tam_cell = _A["avg_annual_tam_cell"]
applied_coeff_cell = _A["applied_coeff_cell"]
pen_fy2225_cell = _A["pen_fy2225_cell"]
outyear_low_avg_cell = _A["outyear_low_avg_cell"]
outyear_high_avg_cell = _A["outyear_high_avg_cell"]
outyear_low_cell = _A["outyear_low_cell"]
outyear_high_cell = _A["outyear_high_cell"]
obbba_tam_cell = _A["obbba_tam_cell"]
