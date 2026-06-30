"""executive_summary - the front-door dashboard tab.

The first sheet: orients a cold reader and carries the headline numbers, all as LIVE
formulas off the model / summary sheets (so they never drift). Answer-first order - market
scale, then where the dollars sit, then accessibility:

  - Purpose + scope (static intro).
  - §1 Scope & how to read these figures (the denominator caveat - what is and isn't counted,
    and why submarine shares are NOT total-boat-construction shares).
  - §2 Observed SAM by program and fiscal year (per-program $ by FY, lifetime memo, FY2025 reach).
  - §3 Capability Domain mix by fiscal year (one matrix, the three programs side by side).
  - §4 FY2025 where-to-play scorecard (per program x domain: size, parent concentration,
    incumbency, retention, entry and the Structure Class read - all read off Where to Play).
  - §5 Supplier continuity by program and fiscal year (incumbent $ share + retention by FY,
    program grain, off Supplier-Year Activity).
  - §6 Primary Output mix by fiscal year (one matrix).
  - §7 DDG SWBS mix by FY (HII-Ingalls only).

Cells reference the program-vendor per-FY / archetype columns, the Where to Play scorecard and
the Supplier-Year Activity model via their promoted cols accessors, the same way those sheets
reference the transaction leaf. Carries no native table (a legend/dashboard).
"""
from __future__ import annotations

from workbook_core.primitives import worksheet
from workbook_core.styles import (
    S_DEFAULT, S_BOLD, S_HEADER_LEFT, S_HEADER_CENTER,
    S_HEADER_CENTER_LEFT, S_HEADER_CENTER_RIGHT,
    S_LABEL_INDENT_1,
    S_NUM, S_PCT, S_PCT_LEFT, S_PCT_RIGHT, S_INT,
)
from workbook_core.tables import WorksheetSpec, SheetEntry
from workbook_core.groups import group_color
from sheets._sam_layout import RowCursor
from sheets._sam_italic import S_ITALIC
from sheets._tabs import TAB_SAM_EXEC_SUMMARY
from sheets._sam_taxonomy import (
    DOMAINS, OUTPUTS, SWBS_GROUPS,
)
from sheets.ddg_program_vendors import ddg_pv_cols
from sheets.ddg_swbs_rollup import swbs_rollup_cols
from sheets.where_to_play import where_to_play_cols
from sheets.supplier_year_activity import (
    supplier_year_cols,
)

_GROUP = "summary"

# Programs, side by side, in the user's order. (display name, cols accessor)
PROGRAMS = [
    ("DDG-51", ddg_pv_cols),
]
# Display label -> internal program key (the Supplier-Year Activity / spine key; DDG-51 -> DDG).
_PROGRAM_KEY = {"DDG-51": "DDG"}
# (column label, the per-FY header on the program-vendor sheet)
FYS = [("FY22", "FY22 $M"), ("FY23", "FY23 $M"),
       ("FY24", "FY24 $M"), ("FY25", "FY25 $M")]
FY_NUMS = [2022, 2023, 2024, 2025]

# B label + 3 programs x 4 FY = 13 content columns (gutter A added by worksheet()).
_NCOLS = 1 + len(PROGRAMS) * len(FYS)
_COLS = [44] + [13] * (_NCOLS - 1)

# Supplier-Year Activity ranges (program-grain continuity + FY reach).
_SY_PROG = supplier_year_cols("Program")
_SY_FY = supplier_year_cols("Federal FY")
_SY_POS = supplier_year_cols("Positive Supplier $M")
_SY_STATUS = supplier_year_cols("Activity Status")

# Where to Play lookup columns (the FY2025 scorecard reads its rows by Axis / Program / FY / code).
_W_AXIS = where_to_play_cols("Axis")
_W_CODE = where_to_play_cols("Archetype Code")
_W_PROGRAM = where_to_play_cols("Program")
_W_FY = where_to_play_cols("Federal FY")

INTRO = "Reported first-tier hull-builder subawards; constant FY2026$."

CAVEATS = [
    "Reported first-tier subawards (FFATA); excludes scope retained in-house by HII-Ingalls / GD-BIW.",
    "Hull and SWBS attribution is HII-Ingalls DDG-51 only (GD-BIW carries no SWBS).",
]


def _program_fy_totals(c: RowCursor) -> None:
    """§2 - per-program $ by fiscal year, with a lifetime memo and FY2025 reach."""
    total_fy25 = "+".join(f"SUM({cols('FY25 $M')})" for _n, cols in PROGRAMS)
    # Headers are left-aligned: none are bare fiscal years (FY22..FY25) - those are
    # the only headers that stay centered (see _matrix / continuity / SWBS).
    c.write(["Program", "FY22 $M", "FY23 $M", "FY24 $M", "FY25 $M",
             "Lifetime $M", "FY25 active UEIs", "FY25 share"],
            styles=[S_HEADER_LEFT] * 8)
    for name, cols in PROGRAMS:
        key = _PROGRAM_KEY[name]
        c.write([
            name,
            f"=SUM({cols('FY22 $M')})",
            f"=SUM({cols('FY23 $M')})",
            f"=SUM({cols('FY24 $M')})",
            f"=SUM({cols('FY25 $M')})",
            f"=SUM({cols('Subaward $M')})",
            f'=COUNTIFS({_SY_PROG},"{key}",{_SY_FY},2025,{_SY_POS},">0")',
            lambda r: f'=IFERROR(F{r}/({total_fy25}),"")',
        ], styles=[S_DEFAULT, S_NUM, S_NUM, S_NUM, S_NUM, S_NUM, S_INT, S_PCT])
    c.write(["Constant FY2026$; lifetime is all years. FY25 share = the program's share of the "
             "FY2025 total."],
            styles=[S_ITALIC])


def _wtp(metric: str, program_disp: str, code: str) -> str:
    """One FY2025 Where to Play cell, by axis D / program display label / archetype code."""
    vals = where_to_play_cols(metric)
    match = (f'MATCH(1,INDEX(({_W_AXIS}="D")*({_W_PROGRAM}="{program_disp}")'
             f'*({_W_FY}=2025)*({_W_CODE}="{code}"),0),0)')
    return f'=IFERROR(INDEX({vals},{match}),"")'


def _fy25_domain_scorecard(c: RowCursor) -> None:
    """§4 - one row per program x capability domain, FY2025, read off Where to Play."""
    # Left-aligned headers (none are bare fiscal years, so none stay centered).
    c.write(["Capability Domain", "FY25 $M", "Program Share", "Active UEIs", "Parent Top-1",
             "Parent HHI", "Incumbent $", "Retention", "First-observed $", "Class"],
            styles=[S_HEADER_LEFT] * 10)
    for disp, _cols in PROGRAMS:
        c.write([disp], styles=[S_BOLD])           # bolded sub-header (flush left)
        for code, name, _defn in DOMAINS:
            c.write([
                f"{code}  {name}",                 # detail row label: indented under the sub-header
                _wtp("Net Subaward $M", disp, code),
                _wtp("Program Share", disp, code),
                _wtp("Active Suppliers", disp, code),
                _wtp("Parent Top-1", disp, code),
                _wtp("Parent HHI", disp, code),
                _wtp("Incumbent $ %", disp, code),
                _wtp("Retention %", disp, code),
                _wtp("First-observed $ %", disp, code),
                _wtp("Observed Structure", disp, code),
            ], styles=[S_LABEL_INDENT_1, S_NUM, S_PCT, S_INT, S_PCT, S_NUM,
                       S_PCT, S_PCT, S_PCT, S_DEFAULT])
    c.write(["Concentration and incumbency use positive spend at the ultimate-parent grain. Class "
             "is a screen, not proof of contestability - see Methodology. Detail on Where to Play."],
            styles=[S_ITALIC])


def _continuity_incumbent(key: str, fy: int) -> str:
    cont = f'SUMIFS({_SY_POS},{_SY_PROG},"{key}",{_SY_FY},{fy},{_SY_STATUS},"Continued")'
    tot = f'SUMIFS({_SY_POS},{_SY_PROG},"{key}",{_SY_FY},{fy})'
    return f'=IFERROR({cont}/{tot},"")'


def _continuity_retention(key: str, fy: int) -> str:
    cont = (f'COUNTIFS({_SY_PROG},"{key}",{_SY_FY},{fy},'
            f'{_SY_STATUS},"Continued",{_SY_POS},">0")')
    prior = f'COUNTIFS({_SY_PROG},"{key}",{_SY_FY},{fy - 1},{_SY_POS},">0")'
    return f'=IFERROR({cont}/{prior},"")'


def _program_fy_continuity(c: RowCursor) -> None:
    """§5 - program-grain supplier continuity across the FY window (off Supplier-Year Activity)."""
    c.write(["Continuity (program x FY)", "FY22", "FY23", "FY24", "FY25"],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * 4)
    c.write(["Incumbent $ share (dollars to suppliers active the prior FY)"], styles=[S_BOLD])
    for name, _cols in PROGRAMS:
        key = _PROGRAM_KEY[name]
        c.write([name] + [_continuity_incumbent(key, fy) for fy in FY_NUMS],
                styles=[S_LABEL_INDENT_1] + [S_PCT] * 4)
    c.write(["Retention (prior-FY suppliers still active this FY)"], styles=[S_BOLD])
    for name, _cols in PROGRAMS:
        key = _PROGRAM_KEY[name]
        c.write([name] + [_continuity_retention(key, fy) for fy in FY_NUMS],
                styles=[S_LABEL_INDENT_1] + [S_PCT] * 4)
    c.write(["Both pool all archetypes; archetype detail is on Where to Play."],
            styles=[S_ITALIC])


def _matrix(c: RowCursor, axis_header: str, codes: list[tuple[str, str, str]],
            row_header: str) -> None:
    """A mix-by-FY matrix: archetype rows x (program x FY) columns. Body cells = the
    archetype's share of that program-FY's reported subaward $; bottom row = the $M total
    that is the share denominator. `codes` = (code, name, definition) tuples. `row_header`
    titles the archetype-label column on the FY sub-header row."""
    # group header (program name at each block's first column) + FY sub-header. The
    # group row's top-left cell is left blank: a program name is not a header for the
    # archetype column beneath it (the real row-label header - "Capability Domain" /
    # "Primary Output" - sits on the FY sub-header row). The program-name row carries
    # its own continuous bottom underline (S_HEADER_LEFT on every block cell, gaps
    # included) on top of the FY row's underline, so the double header reads as one.
    # Each program block is fenced by a vertical rule - a left border on its first FY
    # column, a right border on its last - running from the FY header row down through
    # the body to D0. The far-right edge (the last program's last FY) stays open, and
    # the Total divider below stays open.
    last_prog = len(PROGRAMS) - 1
    last_fy = len(FYS) - 1

    def _fence(p: int, j: int, left_style: int, right_style: int, plain_style: int) -> int:
        if j == 0:
            return left_style                       # block's first FY -> left fence
        if j == last_fy and p != last_prog:
            return right_style                      # inner block's last FY -> right fence
        return plain_style                          # middle FYs + the open far-right edge

    grp, gsty = [""], [S_DEFAULT]
    fy, fsty = [row_header], [S_HEADER_LEFT]
    for p, (name, _cols) in enumerate(PROGRAMS):
        grp += [name] + [""] * (len(FYS) - 1)
        gsty += [S_HEADER_LEFT] * len(FYS)
        for j, (lbl, _h) in enumerate(FYS):
            fy.append(lbl)
            fsty.append(_fence(p, j, S_HEADER_CENTER_LEFT, S_HEADER_CENTER_RIGHT, S_HEADER_CENTER))
    c.write(grp, styles=gsty)
    c.write(fy, styles=fsty)
    # body: one row per archetype code
    for code, name, _defn in codes:
        vals, sty = [f"{code}  {name}"], [S_DEFAULT]
        for p, (_name, cols) in enumerate(PROGRAMS):
            axis = cols(axis_header)
            for j, (_lbl, fyh) in enumerate(FYS):
                fyr = cols(fyh)
                vals.append(f'=IFERROR(SUMIFS({fyr},{axis},"{code}")/SUM({fyr}),"")')
                sty.append(_fence(p, j, S_PCT_LEFT, S_PCT_RIGHT, S_PCT))
        c.write(vals, styles=sty)
    # total $M (FY2026$) row - the per-program-FY denominator, as a bordered divider
    tvals, tsty = ["Total $M (FY26$)"], [S_BOLD]
    for _name, cols in PROGRAMS:
        for _lbl, fyh in FYS:
            tvals.append(f"=SUM({cols(fyh)})")
            tsty.append(S_NUM)
    c.total(tvals, styles=tsty, n_cols=_NCOLS)


def _swbs_matrix(c: RowCursor) -> None:
    """§7 - DDG SWBS mix by FY: one DDG block (subs carry no SWBS). Rows = SWBS major
    groups (+U00); cells = the group's share of HII-Ingalls DDG reported subaward $ for the
    FY, off the per-subsystem roll-up rolled to major group. Columns sum to 100% incl. U00."""
    n = 1 + len(FYS)   # B label + FY22..FY25
    grp = swbs_rollup_cols("SWBS Major Group")
    c.write(["SWBS Group"] + [lbl for lbl, _h in FYS],
            styles=[S_HEADER_LEFT] + [S_HEADER_CENTER] * len(FYS))
    for code, name, _ex in SWBS_GROUPS:
        vals, sty = [f"{code}  {name}"], [S_DEFAULT]
        for _lbl, fyh in FYS:
            fyr = swbs_rollup_cols(fyh)
            vals.append(f'=IFERROR(SUMIFS({fyr},{grp},"{code}")/SUM({fyr}),"")')
            sty.append(S_PCT)
        c.write(vals, styles=sty)
    tvals, tsty = ["Total $M (FY26$)"], [S_BOLD]
    for _lbl, fyh in FYS:
        tvals.append(f"=SUM({swbs_rollup_cols(fyh)})")
        tsty.append(S_NUM)
    c.total(tvals, styles=tsty, n_cols=n)
    sm = swbs_rollup_cols("Subaward $M")
    c.write(["SWBS coverage (HII-Ingalls DDG $ mapped)",
             f'=IFERROR(1-SUMIFS({sm},{grp},"U00")/SUM({sm}),"")'],
            styles=[S_ITALIC, S_PCT])


def _make_exec_summary():
    def render() -> WorksheetSpec:
        c = RowCursor(2)
        c.title(TAB_SAM_EXEC_SUMMARY, _NCOLS)
        c.caption(INTRO)
        c.blank(2)

        # Spacing rhythm: every section opens with one blank row under its banner -
        # placed directly below the banner when the body leads with a table/caveat,
        # or below the italic caption when the section has one (so the caption hugs
        # the banner and the gap falls between caption and table).
        c.section("§1 - Scope & how to read these figures", _NCOLS)
        c.blank()
        for line in CAVEATS:
            c.write([line], styles=[S_DEFAULT])
        c.blank(2)

        c.section("§2 - Observed SAM by program and fiscal year", _NCOLS)
        c.blank()
        _program_fy_totals(c)
        c.blank(2)

        c.section("§3 - Capability Domain mix by fiscal year", _NCOLS)
        c.write(["FY2022-FY2025 share of reported subawards; each program-year column sums to 100%."],
                styles=[S_ITALIC])
        c.blank()
        _matrix(c, "Capability Domain Archetype (D)", DOMAINS, "Capability Domain")
        c.blank(2)

        c.section("§4 - FY2025 where-to-play scorecard", _NCOLS)
        c.write(["FY2025 size, parent concentration and supplier continuity by capability domain."],
                styles=[S_ITALIC])
        c.blank()
        _fy25_domain_scorecard(c)
        c.blank(2)

        c.section("§5 - Supplier continuity by program and fiscal year", _NCOLS)
        c.write(["Incumbent spend and supplier retention by program."],
                styles=[S_ITALIC])
        c.blank()
        _program_fy_continuity(c)
        c.blank(2)

        c.section("§6 - Primary Output mix by fiscal year", _NCOLS)
        c.write(["FY2022-FY2025 share of reported subawards; each program-year column sums to 100%."],
                styles=[S_ITALIC])
        c.blank()
        _matrix(c, "Primary Output Archetype (P)", OUTPUTS, "Primary Output")
        c.blank(2)

        c.section("§7 - DDG SWBS mix by fiscal year", _NCOLS)
        c.write(["HII-Ingalls DDG only; shares include U00 unmapped."],
                styles=[S_ITALIC])
        c.blank()
        _swbs_matrix(c)

        ws = worksheet(c.rows, cols=_COLS, tab_color=group_color(_GROUP),
                       with_gutter=True, show_outline_symbols=False)
        return WorksheetSpec(ws)

    return SheetEntry(TAB_SAM_EXEC_SUMMARY, _GROUP, render)


EXECUTIVE_SUMMARY = _make_exec_summary()
