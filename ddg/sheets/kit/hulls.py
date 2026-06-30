"""_hulls - the hull-assignment LIVE FORMULA builders (the SWBS analogue for hulls).

The DDG Subaward Transactions sheet resolves each row's hull CLASSIFICATION live, off the curated
`Mapping - PIID to Hull` sheet, so an edit to that map flows through the transaction sheet and every
roll-up (which SUMIFS over these columns). One MATCH per row is hoisted into a hidden `PIID Map Row`
helper; `PIID Map Kind`, `PIID Candidate Hulls`, and a boolean `Hull In Family` are resolved off it,
and the five visible classification columns are nested IFs over those helpers + the materialized
regex evidence (`Direct Hull Count`, `Prime Requirement Hull Count`, `Direct Hull Text`).

These formulas reproduce scripts/_hull_logic.resolve() cell-for-cell (A/B/C/D/X, Exact / PIID family
/ Multi-hull / Conflict). The in-family test is a space-padded SEARCH: hull strings are 3-digit
"DDG NNN" tokens, " / "-joined, so the padding makes the membership test delimiter-safe (no
"DDG 11" matching "DDG 119" - every token is 3 digits and space-bounded). ISNUMBER swallows the
#VALUE! that SEARCH returns when a hull is absent, so a no-match reads FALSE rather than erroring.
"""
from __future__ import annotations


def hull_map_row(piid_cell: str, map_piid_range: str) -> str:
    """The PIID->map MATCH done ONCE per row: 0 if the PIID is not in the map, else its row."""
    return f"=IFERROR(MATCH({piid_cell},{map_piid_range},0),0)"


def from_map(maprow_cell: str, ret_range: str) -> str:
    """A value resolved from the map match-row helper: "" if unmatched, else the INDEXed cell."""
    return f'=IF({maprow_cell}=0,"",INDEX({ret_range},{maprow_cell}))'


def hull_in_family(kind_cell: str, cand_cell: str, dht_cell: str) -> str:
    """Boolean: single-ship -> is the ship (candidate) named in the direct text? multi-hull -> is
    the single direct hull in the candidate family? Space-padded, delimiter-safe."""
    ship_in_direct = f'ISNUMBER(SEARCH(" "&{cand_cell}&" "," "&{dht_cell}&" "))'
    direct_in_family = f'ISNUMBER(SEARCH(" "&{dht_cell}&" "," "&{cand_cell}&" "))'
    return f'=IF({kind_cell}="single-ship",{ship_in_direct},{direct_in_family})'


def assigned_hull(maprow_cell: str, kind_cell: str, dhc_cell: str, infam_cell: str,
                  cand_cell: str, dht_cell: str) -> str:
    """The assigned hull (grades A/B only): single-ship -> the ship unless the direct text names a
    different hull; multi-hull -> the one in-family direct hull; else blank."""
    single = f'IF(AND({dhc_cell}>=1,NOT({infam_cell})),"",{cand_cell})'
    multi = f'IF(AND({dhc_cell}=1,{infam_cell}),{dht_cell},"")'
    return f'=IF({maprow_cell}=0,"",IF({kind_cell}="single-ship",{single},{multi}))'


def hull_scope(maprow_cell: str, kind_cell: str, dhc_cell: str, infam_cell: str) -> str:
    """Exact hull / PIID family / Multi-hull / Conflict / Unassigned."""
    single = f'IF(AND({dhc_cell}>=1,NOT({infam_cell})),"Conflict","Exact hull")'
    multi = (f'IF({dhc_cell}>1,"Multi-hull",'
             f'IF({dhc_cell}=1,IF({infam_cell},"Exact hull","Conflict"),"PIID family"))')
    return f'=IF({maprow_cell}=0,"Unassigned",IF({kind_cell}="single-ship",{single},{multi}))'


def hull_basis(maprow_cell: str, kind_cell: str, dhc_cell: str, infam_cell: str,
               prc_cell: str) -> str:
    """Which evidence drove the assignment."""
    single = (f'IF(AND({dhc_cell}>=1,NOT({infam_cell})),'
              f'"Out-of-family direct text","Single-ship PIID")')
    multi = (f'IF({dhc_cell}>1,"Multiple hulls in subaward text",'
             f'IF({dhc_cell}=1,IF({infam_cell},"Subaward text","Out-of-family direct text"),'
             f'IF({prc_cell}>=1,"Prime requirement text","PIID family")))')
    return f'=IF({maprow_cell}=0,"Unassigned",IF({kind_cell}="single-ship",{single},{multi}))'


def hull_confidence(maprow_cell: str, kind_cell: str, dhc_cell: str, infam_cell: str,
                    prc_cell: str) -> str:
    """A official exact / B in-family direct / C prime-requirement only / D family / X conflict."""
    single = f'IF(AND({dhc_cell}>=1,NOT({infam_cell})),"X","A")'
    multi = (f'IF({dhc_cell}>1,"X",'
             f'IF({dhc_cell}=1,IF({infam_cell},"B","X"),'
             f'IF({prc_cell}>=1,"C","D")))')
    return f'=IF({maprow_cell}=0,"",IF({kind_cell}="single-ship",{single},{multi}))'
