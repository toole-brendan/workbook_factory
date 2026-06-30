"""ddg_subaward_transactions - the COMPLETE raw DDG-51 subaward pull, SWBS-tagged.

One row per deduped published subaward record (subAwardReportId) on the DDG-51 program,
carrying every field on the raw FSRS `published` object (50 leaf columns; see
scripts/build_program_transactions.py) PLUS the Ship Work Breakdown Structure (SWBS) tag
(5 columns appended by scripts/tag_ddg_transactions_swbs.py). This is the finest-grain
fact spine behind BOTH roll-ups: the program-vendor sheets key on Subawardee UEI, and the
DDG SWBS by Ship-System roll-up keys on the SWBS Subsystem resolved here.

The SWBS tag: `HII Work-Item Code` + `Builder` are hardcoded leaves (joined / derived by the
tagger). The crosswalk MATCH is done ONCE per row in a sheet-only `SWBS Match Row` helper
(appended after the CSV columns); `SWBS Subsystem`, `SWBS`, `SWBS basis` are LIVE formulas that
INDEX that matched row (Builder-gated, so GD-BIW rows - which carry no SWBS - read blank / n/a
and HII rows with an unmapped code land in U00). One MATCH instead of three over ~6.4k rows.

The hull tag mirrors the SWBS pattern. Only the regex EVIDENCE is materialized by the tagger
(`Direct Hull Text` / `Direct Hull Count` / `Prime Requirement Hull Text` / `... Count`); the
CLASSIFICATION is LIVE off the curated `Mapping - PIID to Hull` sheet, so editing that map updates
the transaction sheet and every roll-up. A hidden `PIID Map Row` helper MATCHes the PIID once;
`PIID Map Kind`, `PIID Candidate Hulls`, and a boolean `Hull In Family` resolve off it, and
`Assigned Hull` / `Hull Assignment Scope` / `Basis` / `Hull Confidence` are nested IFs reproducing
scripts/_hull_logic.resolve() (A/B/C/D/X, conflict-aware). The roll-ups SUMIFS over these columns.

The construction-lifecycle tag (`Lifecycle Stage` / `Lifecycle Stage Basis` / `Date Source Confidence`
/ `Narrowing Result` / `Lifecycle Confidence`) is materialized by scripts/tag_ddg_transactions_lifecycle.py
(a date-window join cannot be a live formula). A/B rows carry the single construction Stage of their
known hull; C/D rows carry the timing Narrowing Result + Lifecycle Confidence (the per-candidate stages
live on DDG C-D Lifecycle Candidates); X / unassigned rows are blank. DDG Hull x Lifecycle Stage SUMIFS
on (Assigned Hull x Lifecycle Stage); DDG C-D Lifecycle Coverage SUMIFS on Narrowing Result.

Promoted accessor (imported by the program-vendor + SWBS + hull roll-up sheets): `ddg_tx_cols`.
"""
from __future__ import annotations

from workbook_award_classification_refactor.sheets._flat import (
    make_flat_sheet, swbs_match_row, swbs_from_row, flat_header_letters,
)
from workbook_award_classification_refactor.sheets._fiscal import (
    TX_EXTRA_COLS, TX_FED_FY, TX_FACTOR, TX_REAL, tx_fy_formulas,
)
from workbook_award_classification_refactor.sheets._tabs import TAB_DDG_TX
from workbook_award_classification_refactor.sheets.hii_swbs_crosswalk import (
    swbs_xwalk_cols,
)
from workbook_award_classification_refactor.sheets.ddg_piid_hull_map import (
    piid_hull_map_cols,
)
from workbook_award_classification_refactor.sheets._hulls import (
    hull_map_row, from_map, hull_in_family, assigned_hull, hull_scope, hull_basis,
    hull_confidence,
)
from workbook_award_classification_refactor.sheets._widths import (
    W_UEI, W_VENDOR, W_REPORTID, W_UUID, W_SUBNUM, W_DATE, W_AMOUNT, W_TEXT,
    W_STREET2, W_CITY, W_CD, W_CODE, W_STATE, W_CC, W_COUNTRY, W_ZIP, W_BIZCODE,
    W_PAY, W_PIID, W_CONTRACTKEY, W_REFIDV, W_AWARDTYPE, W_TCV, W_NAICS,
    W_NAICS_DESC, W_ORGCODE, W_NAME, W_TEXT_WIDE, W_SUPTYPE,
    W_RANK, W_SHORT_FLAG, W_CLASS, W_CATEGORY,
)

# 76 columns = 50 raw (build_program_transactions.COLUMNS order, UEI = column B) + 5 SWBS
# + 4 hull regex evidence (materialized by scripts/tag_ddg_transactions_hulls.py)
# + 5 construction-lifecycle (materialized by scripts/tag_ddg_transactions_lifecycle.py)
# + 12 sheet-only formula columns (3 SWBS/hull helpers below + the hull classification + fiscal).
_WIDTHS = [
    W_UEI, W_VENDOR, W_VENDOR, W_UEI, W_VENDOR,                 # subawardee entity
    W_REPORTID, W_UUID, W_SUBNUM, W_DATE, W_DATE, W_AMOUNT, W_TEXT,   # the subaward
    W_VENDOR, W_STREET2, W_CITY, W_CD, W_CODE, W_STATE, W_CC, W_COUNTRY, W_ZIP,  # address
    W_BIZCODE, W_TEXT, W_PAY, W_VENDOR,                          # business types / exec comp
    W_PIID, W_CONTRACTKEY, W_CODE, W_PIID, W_REFIDV, W_AWARDTYPE, W_TCV, W_DATE,  # prime ctx
    W_UEI, W_VENDOR, W_TEXT_WIDE, W_NAICS, W_NAICS_DESC,         # prime entity / naics
    W_ORGCODE, W_NAME, W_ORGCODE, W_NAME, W_ORGCODE, W_NAME,     # funding org
    W_ORGCODE, W_NAME, W_ORGCODE, W_NAME, W_ORGCODE, W_NAME,     # contracting org
    W_CODE, W_SUPTYPE, W_CODE, W_TEXT_WIDE, W_TEXT,            # SWBS: code | builder | subsystem | SWBS | basis
    # hull regex evidence (CSV): direct text | count | prime-req text | count
    W_SUBNUM, W_RANK, W_SUBNUM, W_RANK,
    # construction-lifecycle (CSV, tag_ddg_transactions_lifecycle): stage | basis | date-source conf |
    #   narrowing result | lifecycle confidence. A/B carry the stage; C/D carry the narrowing; X blank.
    W_SUPTYPE, W_TEXT_WIDE, W_SHORT_FLAG, W_CATEGORY, W_CLASS,
    # sheet-only formula columns (extra_cols order): SWBS match-row helper |
    #   PIID map row | PIID map kind | hull-in-family (3 hidden helpers) |
    #   PIID candidate hulls | assigned hull | scope | basis | confidence |
    #   Federal FY | Deflator Factor | Subaward $ FY2026$
    W_CD,
    W_CD, W_CLASS, W_CD,
    W_TEXT_WIDE, W_SHORT_FLAG, W_CLASS, W_CATEGORY, W_CODE,
    W_CD, W_CD, W_AMOUNT,
]
assert len(_WIDTHS) == 76, len(_WIDTHS)

_DATE_COLS = ["Subaward Date", "Submitted Date", "Base Award Date Signed"]
_FLOAT_COLS = ["Subaward Amount $", "Total Contract Value $"]
# materialized hull regex-evidence counts (the text evidence columns render as default text)
_HULL_INT = ["Direct Hull Count", "Prime Requirement Hull Count"]

# SWBS tag: MATCH the row's HII work-item code into the crosswalk ONCE (the SWBS Match Row
# helper, a sheet-only column appended after the CSV), gated on Builder; the three SWBS outputs
# then INDEX that matched row. Builder / code / match-row column letters are resolved by NAME
# (flat_header_letters) so no column letter is hardcoded in this module.
# Sheet-only formula columns appended after the CSV, in this order:
#   - SWBS Match Row : the crosswalk MATCH, once per row (hidden helper)
#   - the hull classification (LIVE, off the curated PIID->Hull map) -> 3 hidden helpers + 5 shown:
#       PIID Map Row : the map MATCH, once per row
#       PIID Map Kind / Hull In Family : resolved off the match-row (single-ship vs in-family test)
#       PIID Candidate Hulls / Assigned Hull / Hull Assignment Scope / Basis / Confidence
#   - Federal FY / Deflator Factor / Subaward $ FY2026$ (fiscal)
_SWBS_EXTRA = ["SWBS Match Row"]
_HULL_HELPERS = ["PIID Map Row", "PIID Map Kind", "Hull In Family"]
_HULL_CLASS = ["PIID Candidate Hulls", "Assigned Hull", "Hull Assignment Scope",
               "Hull Assignment Basis", "Hull Confidence"]
_HIDDEN = _SWBS_EXTRA + _HULL_HELPERS
_EXTRA = _SWBS_EXTRA + _HULL_HELPERS + _HULL_CLASS + TX_EXTRA_COLS
_L = flat_header_letters("ddg_subaward_transactions", extra_cols=_EXTRA)
_XW_CODE = swbs_xwalk_cols("HII Work-Item Code")
_XW_SUBSYS = swbs_xwalk_cols("SWBS Subsystem")
_XW_SWBS = swbs_xwalk_cols("SWBS")
_XW_BASIS = swbs_xwalk_cols("SWBS basis")

# Curated PIID->Hull map ranges (the live classification INDEXes these by the matched row).
_MAP_PIID = piid_hull_map_cols("Prime PIID")
_MAP_CAND = piid_hull_map_cols("Candidate Hulls")
_MAP_KIND = piid_hull_map_cols("Exact or Family")


def _bld(r):  return f"${_L['Builder']}{r}"
def _code(r): return f"${_L['HII Work-Item Code']}{r}"
def _mrow(r): return f"${_L['SWBS Match Row']}{r}"
def _piid(r): return f"${_L['Prime PIID']}{r}"
def _dht(r):  return f"${_L['Direct Hull Text']}{r}"
def _dhc(r):  return f"${_L['Direct Hull Count']}{r}"
def _prc(r):  return f"${_L['Prime Requirement Hull Count']}{r}"
def _maprow(r): return f"${_L['PIID Map Row']}{r}"
def _kind(r):   return f"${_L['PIID Map Kind']}{r}"
def _infam(r):  return f"${_L['Hull In Family']}{r}"
def _cand(r):   return f"${_L['PIID Candidate Hulls']}{r}"


_FORMULAS = {
    "SWBS Match Row": lambda r: swbs_match_row(_bld(r), _code(r), _XW_CODE),
    "SWBS Subsystem": lambda r: swbs_from_row(_bld(r), _mrow(r), _XW_SUBSYS,
                                              na="", unmapped="U00"),
    "SWBS":           lambda r: swbs_from_row(_bld(r), _mrow(r), _XW_SWBS,
                                              na="n/a (non-HII-Ingalls)",
                                              unmapped="U00 No SWBS Evidence"),
    "SWBS basis":     lambda r: swbs_from_row(_bld(r), _mrow(r), _XW_BASIS,
                                              na="-", unmapped="U - no SWBS evidence"),
    # hull classification, live off the PIID->Hull map (reproduces scripts/_hull_logic.resolve()).
    "PIID Map Row":         lambda r: hull_map_row(_piid(r), _MAP_PIID),
    "PIID Map Kind":        lambda r: from_map(_maprow(r), _MAP_KIND),
    "PIID Candidate Hulls": lambda r: from_map(_maprow(r), _MAP_CAND),
    "Hull In Family":       lambda r: hull_in_family(_kind(r), _cand(r), _dht(r)),
    "Assigned Hull":        lambda r: assigned_hull(_maprow(r), _kind(r), _dhc(r), _infam(r),
                                                    _cand(r), _dht(r)),
    "Hull Assignment Scope":      lambda r: hull_scope(_maprow(r), _kind(r), _dhc(r), _infam(r)),
    "Hull Assignment Basis":      lambda r: hull_basis(_maprow(r), _kind(r), _dhc(r), _infam(r),
                                                       _prc(r)),
    "Hull Confidence":            lambda r: hull_confidence(_maprow(r), _kind(r), _dhc(r),
                                                            _infam(r), _prc(r)),
}
_FORMULAS.update(tx_fy_formulas(
    "ddg_subaward_transactions", date_header="Subaward Date",
    amount_header="Subaward Amount $", extra_cols=_EXTRA))

DDG_SUBAWARD_TX, ddg_tx_cols = make_flat_sheet(
    tab=TAB_DDG_TX, group="data",
    csv_name="ddg_subaward_transactions", table_name="DdgSubawardTx",
    banner="§1 - DDG-51 subaward transactions",
    intro="Deduplicated DDG-51 first-tier subaward reports; nominal and constant FY2026$.",
    widths=_WIDTHS,
    int_cols=_SWBS_EXTRA + ["PIID Map Row"] + _HULL_INT + [TX_FED_FY],
    float_cols=_FLOAT_COLS + [TX_FACTOR, TX_REAL],
    date_cols=_DATE_COLS, input_cols=_FLOAT_COLS + _DATE_COLS,
    formula_cols=_FORMULAS, extra_cols=_EXTRA,
    # the once-per-row crosswalk / PIID-map match indices + the in-family flag are formula
    # plumbing, not reader content.
    hidden_headers=_HIDDEN,
)

# Guard: the pre-build letter resolver must agree with the sheet make_flat_sheet actually built,
# so the same-sheet SWBS / hull / FY formulas reference the real columns.
_GUARD_COLS = ("Builder", "HII Work-Item Code", "SWBS Match Row", "Direct Hull Count",
               "PIID Map Row", "Assigned Hull", "Hull Confidence", TX_FED_FY, TX_FACTOR, TX_REAL)
assert all(f"!${_L[h]}$" in ddg_tx_cols(h) for h in _GUARD_COLS), {
    h: (_L[h], ddg_tx_cols(h)) for h in _GUARD_COLS}
