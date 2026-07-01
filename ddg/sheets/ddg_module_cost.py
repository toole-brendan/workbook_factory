"""ddg_module_cost - the "DDG Module Cost & Grand Blocks" tab (model group).

The HII modular build hierarchy costed top-down and evidenced bottom-up on one tab:

  §1 Hierarchy      - ship -> 4 modules -> 21 grand blocks -> 72 structural units
                      (HII source counts; a PWBS - physical/production - not SWBS).
  §2 Cost anchor    - per-ship Basic Construction resolved LIVE from SCN Budget /
                      FYDP Outyears (FY2025 3-ship MYP rate, constant FY2026 $M).
  §3 Even split     - the anchor divided down the hierarchy; the per-grand-block
                      figure is the comparator for the outsourcing evidence below.
  §4 Evidence       - the 22 subaward actions whose SOW text NAMES a grand block
                      ("GB B15", "GB A16 & A21", "C15GB", "GRAND BLOCK", "(D52)").
                      Curated spine (then-year $); FY2026$ and a nominal tie-back
                      resolve LIVE against the transaction leaf by Report ID.
                      Actions dated beyond the reader-facing observed-SAM window
                      (lib.SAM_TX_FY_END) - if any - are carried from the FSRS
                      record only and flagged; the live columns and the Checks tie
                      cover the in-window actions.
  §5 Roll-ups       - by yard, by hull, and DDG 137 (the rich-coverage hull) by
                      named grand block - all SUMIFS over the §4 table.
  §6 Anchor vs obs. - outsourced structural fabrication per block vs the model's
                      per-block allocation (a floor, an order-of-magnitude band).
  §7 Bridge notes   - why module attribution needs explicit text, and why this
                      lens sees only the OUTSOURCED tail of make-vs-buy.

Reconciled on the Checks tab: the in-window curated rows tie to the transaction
leaf; the DDG 137 block roll-up partitions its hull total; the per-ship anchor sits
in its band.

Promoted accessors (Checks):
  gb_range(header)          -> a §4 column range ("Then-yr $M" / "FY2026 $M" / "Leaf $M")
  gb_window_total_cell()    -> the §4 in-window then-year subtotal (leaf-tie basis)
  per_ship_bc_cell()        -> the §2 per-ship Basic Construction cell
  per_block_model_cell()    -> the §3 per-grand-block even-split cell
  ddg137_total_cell()       -> the §5 by-hull DDG 137 then-year total
  ddg137_block_total_cell() -> the §5 DDG 137 by-block then-year total
"""
from __future__ import annotations

import re

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_NOTE, S_HEADER_LEFT, S_HEADER_CENTER,
    S_NUM, S_INT, S_PCT, S_LINK_NUM, S_LINK_INT,
    S_NUM_INPUT, S_INT_INPUT, S_DATE_INPUT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color

from ddg.lib import SAM_TX_WINDOW_LABEL, SAM_TX_FY_END
from ddg.sheets.kit.cuts import load_rows, as_float, date_serial
from ddg.sheets.kit.layout import RowCursor
from ddg.sheets.kit.styles import S_ITALIC, S_TEXT_INPUT
from ddg.sheets.kit.tabs import TAB_MODULE_COST, TAB_SWBS_ROLLUP, TAB_PROC_TIMING
from ddg.sheets.kit.fiscal import TX_REAL
from ddg.sheets.kit.widths import (
    W_REPORTID, W_DATE, W_DOLLAR, W_COUNT, W_SHORT_FLAG,
)
from ddg.sheets.scn_budget import scn_cell
from ddg.sheets.fydp_outyears import fydp_qty_cell
from ddg.sheets.ddg_subaward_transactions import ddg_tx_cols

_GROUP = "model"
_NCOLS = 9   # B label/yard | C value/report id | D date | E hull | F block | G then-yr | H FY2026 | I leaf | J description
_COLS = [46, W_REPORTID, W_DATE, 11, W_SHORT_FLAG, W_DOLLAR, W_DOLLAR, W_DOLLAR, 56]

_LI_DDG = 2122

_TX_RID = ddg_tx_cols("Subaward Report ID")
_TX_REAL_R = ddg_tx_cols(TX_REAL)
_TX_NOM = ddg_tx_cols("Subaward Amount $")

# Display order for the three outsourcing yards (matches the §5 roll-up).
_YARDS = [("GULF COPPER", "Gulf Copper"),
          ("BAE SYSTEMS", "BAE Jacksonville"),
          ("EASTERN SHIPBUILDING", "Eastern Shipbuilding")]


def _yard_short(vendor: str) -> str:
    v = vendor.upper()
    for prefix, short in _YARDS:
        if v.startswith(prefix):
            return short
    return vendor.title()


def _block_label(desc: str) -> str:
    """The PWBS grand-block / zone code named in the SOW text ('(unlabeled)' if none)."""
    d = desc.upper()
    m = re.search(r"GB\s*([A-D]\d{2})\s*&\s*([A-D]\d{2})", d)
    if m:
        return f"{m.group(1)} & {m.group(2)}"
    if re.search(r"\bC15GB\b", d):
        return "C15"
    m = re.search(r"GB\s*([A-D]\d{2})", d)
    if m:
        return m.group(1)
    m = re.search(r"\(([A-D]\d{2}(?:\s*[,/]\s*[A-D]\d{2})*)\)", d)
    if m:
        return re.sub(r"\s+", "", m.group(1)).replace(",", "/")
    return "(unlabeled)"


def _in_window(date: str) -> bool:
    """Federal FY of the subaward date <= the reader-facing SAM window end."""
    y, m = int(date[:4]), int(date[5:7])
    return (y + 1 if m >= 10 else y) <= SAM_TX_FY_END


def _load():
    rows = []
    for r in load_rows("ddg_grand_block_subawards"):
        desc = (r.get("Subaward Description") or "").strip()
        date = (r.get("Subaward Date") or "").strip()
        rows.append(dict(
            rid=(r.get("Subaward Report ID") or "").strip(),
            date=date,
            yard=_yard_short((r.get("Subawardee Vendor Name") or "").strip()),
            hull=(r.get("Direct Hull Text") or "").strip(),
            block=_block_label(desc),
            amt_m=(as_float(r.get("Subaward Amount $")) or 0.0) / 1e6,
            desc=desc,
            in_window=_in_window(date),
        ))
    order = {short: i for i, (_p, short) in enumerate(_YARDS)}
    rows.sort(key=lambda x: (order.get(x["yard"], 99), x["date"]))
    return rows


def _make():
    gb = _load()
    P: dict = {}
    c = RowCursor(2)
    c.title(TAB_MODULE_COST, _NCOLS)
    c.caption("HII's modular build hierarchy costed top-down, and the subawards where whole "
              "grand blocks were fabricated outside the prime yard.")
    c.blank(2)

    # §1 hierarchy ----------------------------------------------------------------------
    c.section("§1 - The HII modular build hierarchy (a PWBS, not SWBS)", _NCOLS)
    c.blank()
    c.write(["Level", "Count", "", "", "Description"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_DEFAULT, S_DEFAULT, S_HEADER_LEFT])
    c.write(["Ship (per hull)", 1, None, None,
             "One complete DDG-51 (Arleigh Burke) hull."],
            styles=[S_BOLD, S_INT, S_DEFAULT, S_DEFAULT, S_DEFAULT])
    P["n_modules"] = c.write(["Hull modules", 4, None, None,
                              "Hull modules 1-3 + the deckhouse (module 4)."],
                             styles=[S_DEFAULT, S_INT_INPUT, S_DEFAULT, S_DEFAULT, S_DEFAULT])
    P["n_blocks"] = c.write(["Grand blocks", 21, None, None,
                             "Integrated from units; erected into the hull modules."],
                            styles=[S_DEFAULT, S_INT_INPUT, S_DEFAULT, S_DEFAULT, S_DEFAULT])
    P["n_units"] = c.write(["Structural units (assemblies)", 72, None, None,
                            "Base assemblies: CAM-cut plate, bent pipe; pre-outfitted."],
                           styles=[S_DEFAULT, S_INT_INPUT, S_DEFAULT, S_DEFAULT, S_DEFAULT])
    c.write(['HII (verbatim): "72 structural assemblies (units) are integrated, forming 21 grand '
             'blocks. These grand blocks are integrated, creating the ship\'s hull modules 1, 2 '
             'and 3." Source: HII / Ingalls Arleigh Burke capability page (archive capture '
             "2026-04-02). Module / grand block / unit is the yard's PHYSICAL production breakdown "
             "(PWBS); SWBS is the FUNCTIONAL system taxonomy - see §7."],
            styles=[S_NOTE])
    c.blank(2)

    # §2 cost anchor ----------------------------------------------------------------------
    c.section("§2 - Per-ship cost anchor (live, constant FY2026 $M)", _NCOLS)
    c.blank()
    c.write(["Measure", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
    bc = c.write(["FY2025 Basic Construction, 3-ship MYP (SCN Budget)",
                  f"={scn_cell(_LI_DDG, 2025, 'basic')}"],
                 styles=[S_DEFAULT, S_LINK_NUM])
    qty = c.write(["FY2025 procurement quantity (FYDP Outyears)",
                   f"={fydp_qty_cell(_LI_DDG, 2025)}"],
                  styles=[S_DEFAULT, S_LINK_INT])
    P["per_ship"] = c.write(["Per-ship Basic Construction",
                             f"=C{bc}/C{qty}"],
                            styles=[S_BOLD, S_NUM])
    c.write(["Memo: FY2027 single-ship rate",
             f"=({scn_cell(_LI_DDG, 2027, 'basic')})/{fydp_qty_cell(_LI_DDG, 2027)}"],
            styles=[S_DEFAULT, S_NUM])
    c.write(["The FY2025 3-ship rate is the headline; the single-ship buy carries rate + "
             "nonrecurring loading."], styles=[S_NOTE])
    c.blank(2)

    # §3 even split -----------------------------------------------------------------------
    c.section("§3 - Cost per structural level (even split, constant FY2026 $M)", _NCOLS)
    c.blank()
    c.write(["Level", "Count", "Avg per item"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER])
    for key, label in [("n_modules", "Hull module"),
                       ("n_blocks", "Grand block"),
                       ("n_units", "Structural unit")]:
        r = c.write([label, f"=C{P[key]}", f"=C{P['per_ship']}/C{P[key]}"],
                    styles=[S_DEFAULT, S_INT, S_NUM])
        if key == "n_blocks":
            P["per_block"] = r
    c.write(["An even split is the honest first-order average; weighting modules (e.g. the "
             "machinery-dense aft module) is scenario analysis, deliberately not modeled here."],
            styles=[S_NOTE])
    c.blank(2)

    # §4 evidence table ---------------------------------------------------------------------
    c.section("§4 - Grand-block outsourcing: the subawards that name a block", _NCOLS)
    c.blank()
    n_out = sum(1 for r in gb if not r["in_window"])
    intro = ("Three yards fabricated whole grand blocks for the FY2018-22 MYP hulls under "
             "subaward; the SOW text names the PWBS block. Then-year $ from the curated spine; "
             "FY2026$ and the nominal tie-back resolve live from DDG Subaward Transactions by "
             "Report ID")
    if n_out:
        intro += (f" for actions inside the {SAM_TX_WINDOW_LABEL} observed-SAM window "
                  f"({n_out} of {len(gb)} actions post-date it - carried from the FSRS "
                  "record only)")
    c.write([intro + "."], styles=[S_ITALIC])
    c.blank()
    c.write(["Yard", "Report ID", "Date", "Hull", "Grand Block",
             "Then-yr $M", "FY2026 $M", "Leaf $M", "Subaward Description (verbatim)"],
            styles=[S_HEADER_LEFT, S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_LEFT,
                    S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER,
                    S_HEADER_LEFT])
    g0 = c.at()
    win_rows: list[int] = []
    for row in gb:
        live_real = (lambda r: f"=SUMIFS({_TX_REAL_R},{_TX_RID},$C{r})/1000000") \
            if row["in_window"] else None
        live_nom = (lambda r: f"=SUMIFS({_TX_NOM},{_TX_RID},$C{r})/1000000") \
            if row["in_window"] else None
        r = c.write([row["yard"], row["rid"], date_serial(row["date"]), row["hull"],
                     row["block"], row["amt_m"], live_real, live_nom, row["desc"]],
                    styles=[S_DEFAULT, S_TEXT_INPUT, S_DATE_INPUT, S_DEFAULT, S_DEFAULT,
                            S_NUM_INPUT, S_LINK_NUM, S_LINK_NUM, S_DEFAULT])
        if row["in_window"]:
            win_rows.append(r)
    g1 = c.at() - 1
    P["gb_total"] = c.total(
        [f"All grand-block subawards ({len(gb)} actions)", "", None, "", "",
         f"=SUM(G{g0}:G{g1})", f"=SUM(H{g0}:H{g1})", f"=SUM(I{g0}:I{g1})", ""],
        styles=[S_BOLD, S_DEFAULT, S_DEFAULT, S_DEFAULT, S_DEFAULT,
                S_NUM, S_NUM, S_NUM, S_DEFAULT], n_cols=_NCOLS)
    if n_out:
        P["gb_window_total"] = c.write(
            [f"  of which {SAM_TX_WINDOW_LABEL} ({len(win_rows)} actions; the leaf-tie basis)",
             "", None, "", "", "=" + "+".join(f"G{r}" for r in win_rows), "", "", ""],
            styles=[S_DEFAULT, S_DEFAULT, S_DEFAULT, S_DEFAULT, S_DEFAULT,
                    S_NUM, S_DEFAULT, S_DEFAULT, S_DEFAULT])
    else:
        P["gb_window_total"] = P["gb_total"]   # all actions in-window: the tie basis IS the total
    c.write(["Net of credits (the Oct-2025 D52 rescope deobligated $7.2M of an $8.2M award). "
             "The then-yr leaf-tie basis vs Leaf $M reconciles on Checks - those curated rows "
             "ARE transaction-leaf rows, keyed by Report ID."], styles=[S_NOTE])
    c.blank(2)

    _Y, _H, _B = f"$B${g0}:$B${g1}", f"$E${g0}:$E${g1}", f"$F${g0}:$F${g1}"
    _G, _HH = f"$G${g0}:$G${g1}", f"$H${g0}:$H${g1}"

    # §5 roll-ups -----------------------------------------------------------------------------
    c.section("§5 - Roll-ups (live over §4)", _NCOLS)
    c.blank()
    c.write(["By yard", "Then-yr $M", "FY2026 $M", "Actions"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    y0 = c.at()
    for _prefix, short in _YARDS:
        c.write([short,
                 lambda r: f"=SUMIFS({_G},{_Y},$B{r})",
                 lambda r: f"=SUMIFS({_HH},{_Y},$B{r})",
                 lambda r: f"=COUNTIFS({_Y},$B{r})"],
                styles=[S_DEFAULT, S_NUM, S_NUM, S_INT])
    y1 = c.at() - 1
    c.total(["All yards", f"=SUM(C{y0}:C{y1})", f"=SUM(D{y0}:D{y1})", f"=SUM(E{y0}:E{y1})"],
            styles=[S_BOLD, S_NUM, S_NUM, S_INT], n_cols=4)
    c.blank()

    hulls = sorted({r["hull"] for r in gb},
                   key=lambda h: -sum(x["amt_m"] for x in gb if x["hull"] == h))
    c.write(["By hull", "Then-yr $M", "FY2026 $M", "Actions"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    for h in hulls:
        r = c.write([h,
                     lambda rr: f"=SUMIFS({_G},{_H},$B{rr})",
                     lambda rr: f"=SUMIFS({_HH},{_H},$B{rr})",
                     lambda rr: f"=COUNTIFS({_H},$B{rr})"],
                    styles=[S_DEFAULT, S_NUM, S_NUM, S_INT])
        if h == "DDG 137":
            P["hull_137"] = r
    hull_note = (f"All actions sit on the FY2018-22 block-buy hulls and read In-build on the "
                 f"{TAB_PROC_TIMING} axis.")
    if n_out:
        hull_note += (f" FY2026 $M columns carry only the {SAM_TX_WINDOW_LABEL} actions; "
                      "Then-yr $M carries all of them.")
    c.write([hull_note], styles=[S_NOTE])
    c.blank()

    blocks_137 = sorted({r["block"] for r in gb if r["hull"] == "DDG 137"},
                        key=lambda b: -sum(x["amt_m"] for x in gb
                                           if x["hull"] == "DDG 137" and x["block"] == b))
    c.write(["DDG 137 by grand block", "Then-yr $M", "FY2026 $M", "Actions"],
            styles=[S_HEADER_LEFT, S_HEADER_CENTER, S_HEADER_CENTER, S_HEADER_CENTER])
    b0 = c.at()
    for b in blocks_137:
        c.write([b,
                 lambda rr: f'=SUMIFS({_G},{_B},$B{rr},{_H},"DDG 137")',
                 lambda rr: f'=SUMIFS({_HH},{_B},$B{rr},{_H},"DDG 137")',
                 lambda rr: f'=COUNTIFS({_B},$B{rr},{_H},"DDG 137")'],
                styles=[S_DEFAULT, S_NUM, S_NUM, S_INT])
    b1 = c.at() - 1
    P["blocks_137_total"] = c.total(
        ["DDG 137 total", f"=SUM(C{b0}:C{b1})", f"=SUM(D{b0}:D{b1})", f"=SUM(E{b0}:E{b1})"],
        styles=[S_BOLD, S_NUM, S_NUM, S_INT], n_cols=4)
    P["blocks_137_max"] = (b0, b1)
    c.blank(2)

    # §6 anchor vs observed ---------------------------------------------------------------------
    c.section("§6 - Cost anchor vs observed outsourced fabrication", _NCOLS)
    c.blank()
    c.write(["Measure", "Value"], styles=[S_HEADER_LEFT, S_HEADER_CENTER])
    model_r = c.write(["Model allocation per grand block (even split, FY2026 $M)",
                       f"=D{P['per_block']}"],
                      styles=[S_DEFAULT, S_NUM])
    max_r = c.write(["Largest outsourced block (GB B15, then-yr $M)",
                     f"=MAX(C{b0}:C{b1})"],
                    styles=[S_DEFAULT, S_NUM])
    c.write(["  as share of the model per-block allocation",
             f"=C{max_r}/C{model_r}"],
            styles=[S_DEFAULT, S_PCT])
    c.blank()
    c.write(["Outsourced work is bare structural fabrication (steel + welding) - a FLOOR on the "
             "block's cost. Observed blocks run ~$1.7-17.7M, roughly 2-24% of the model's "
             "fully-burdened per-block Basic Construction; erection, outfitting, systems "
             "integration and test stay at the prime yard."], styles=[S_NOTE])
    c.write(["The model figure is an even split (and constant FY2026$; the 2024-25 evidence "
             "deflates ~2-4%, immaterial to the band); the outsourced hull-structure blocks are "
             "likely below-average-cost blocks, so read the share as an order-of-magnitude band, "
             "not a ratio."], styles=[S_NOTE])
    c.blank(2)

    # §7 bridge notes -----------------------------------------------------------------------------
    c.section("§7 - SAM-to-module bridge (attribution discipline)", _NCOLS)
    c.blank()
    for topic, note in [
        ("Two different axes", "SWBS is a FUNCTIONAL system taxonomy (which system a part serves); "
                               "module / grand block / unit is HII's PHYSICAL production breakdown "
                               "(where in the build it is assembled). A part has both; a subaward "
                               "usually reveals only the functional side."),
        ("Attribution rule", "Attribute a subaward to a physical module / grand block ONLY when its "
                             "text explicitly names one. The §4 rows are exactly that rare case - "
                             "no notional spreading of $ across blocks."),
        ("Why the lens is a floor", "Only OUTSOURCED blocks generate a block-named subaward; in-house "
                                    "blocks never enter the subaward corpus. §4 sees the outsourced "
                                    "tail of make-vs-buy, not the block population."),
        ("Ship-system mix", f"Subaward $ by SWBS major group lives on the {TAB_SWBS_ROLLUP} tab - "
                            "that is supplier spend by SYSTEM, not a structural cost weight."),
    ]:
        c.write([topic, note], styles=[S_BOLD, S_DEFAULT])
    c.write(["Sources: SAM.gov FSRS first-tier subawards (curated grand-block spine, captured "
             "2026-07-01); PWBS lineage NSRP-0164 (1982). Evidence $ then-year net of credits; "
             "model $ constant FY2026."], styles=[S_NOTE])

    def render() -> WorksheetSpec:
        ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                       with_gutter=True, show_outline_symbols=False)
        return WorksheetSpec(ws)

    _GB_COL = {"Then-yr $M": "G", "FY2026 $M": "H", "Leaf $M": "I"}

    def gb_range(header: str) -> str:
        return f"'{TAB_MODULE_COST}'!${_GB_COL[header]}${g0}:${_GB_COL[header]}${g1}"

    def gb_window_total_cell() -> str:
        return f"'{TAB_MODULE_COST}'!$G${P['gb_window_total']}"

    def per_ship_bc_cell() -> str:
        return f"'{TAB_MODULE_COST}'!$C${P['per_ship']}"

    def per_block_model_cell() -> str:
        return f"'{TAB_MODULE_COST}'!$D${P['per_block']}"

    def ddg137_total_cell() -> str:
        return f"'{TAB_MODULE_COST}'!$C${P['hull_137']}"

    def ddg137_block_total_cell() -> str:
        return f"'{TAB_MODULE_COST}'!$C${P['blocks_137_total']}"

    return (SheetEntry(TAB_MODULE_COST, _GROUP, render),
            dict(gb_range=gb_range, gb_window_total_cell=gb_window_total_cell,
                 per_ship_bc_cell=per_ship_bc_cell,
                 per_block_model_cell=per_block_model_cell,
                 ddg137_total_cell=ddg137_total_cell,
                 ddg137_block_total_cell=ddg137_block_total_cell))


(DDG_MODULE_COST, _A) = _make()
gb_range = _A["gb_range"]
gb_window_total_cell = _A["gb_window_total_cell"]
per_ship_bc_cell = _A["per_ship_bc_cell"]
per_block_model_cell = _A["per_block_model_cell"]
ddg137_total_cell = _A["ddg137_total_cell"]
ddg137_block_total_cell = _A["ddg137_block_total_cell"]
