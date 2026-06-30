"""_integrity - build-stopping cross-CSV universe checks (non-sheet helper).

The program-vendor sheets, the per-UEI dimension sheets, and the transaction fact
sheets must ALL describe the same (Program x UEI) universe. An independent CSV
refresh that updates one pull but not another silently strips the orphaned rows to
dash / D0 / P0: the program-vendor dimension lookups find no matching dimension row,
so the supplier name / NAICS / parent resolve to "-" and the archetype falls to the
unresolved default. That is exactly the 2026-06 Virginia drift - the
N00024-20-C-2120 prime was added to the transaction + program-vendor pulls but not
the dimension pulls, leaving 36 Virginia UEIs unresolved (that prime has since been
removed from scope - 2026-06-21 - but the guard remains the structural guarantee).

`assert_universes_aligned()` is called from lib.build() so `python build_workbook.py`
fails LOUDLY (with the offending keys) rather than shipping a silently drifted
workbook. It is the structural guarantee behind "regenerate the dimensions" - the
re-sync can never quietly come undone again.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from workbook_award_classification_refactor.sheets._cuts import load_table

# (csv stem prefix, Program label) for the per-program single-program CSVs.
# DDG-51-only slice: the universe guards check the DDG program alone.
_PROGRAMS = [("ddg", "DDG")]

# Versioned prime-contract scope manifest, at the workbook root (two levels up from sheets/).
_SCOPE_MANIFEST = Path(__file__).resolve().parents[2] / "prime_contract_scope.csv"


def _single_program_keys(suffix: str) -> set[tuple[str, str]]:
    """{(Program, UEI)} union over the three <prog>_<suffix>.csv files - Program from
    the file, UEI from the 'Subawardee UEI' column."""
    keys: set[tuple[str, str]] = set()
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_{suffix}")
        j = headers.index("Subawardee UEI")
        for r in rows:
            u = (r[j] if j < len(r) else "").strip()
            if u:
                keys.add((label, u))
    return keys


def _dimension_keys(stem: str) -> set[tuple[str, str]]:
    """{(Program, UEI)} from a dimension CSV that carries its own 'Program' column."""
    headers, rows = load_table(stem)
    jp, ju = headers.index("Program"), headers.index("Subawardee UEI")
    keys: set[tuple[str, str]] = set()
    for r in rows:
        u = (r[ju] if ju < len(r) else "").strip()
        if u:
            keys.add(((r[jp] if jp < len(r) else "").strip(), u))
    return keys


def _diff(a: set, b: set, a_name: str, b_name: str) -> str:
    parts = []
    if a - b:
        parts.append(f"{len(a - b)} in {a_name} not in {b_name} (e.g. {sorted(a - b)[:5]})")
    if b - a:
        parts.append(f"{len(b - a)} in {b_name} not in {a_name} (e.g. {sorted(b - a)[:5]})")
    return "; ".join(parts)


def _tx_piids() -> dict[str, set[str]]:
    """{Program label -> {Prime PIID}} over the three transaction CSVs."""
    out: dict[str, set[str]] = {}
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_subaward_transactions")
        j = headers.index("Prime PIID")
        out[label] = {(r[j] if j < len(r) else "").strip()
                      for r in rows if j < len(r) and (r[j] or "").strip()}
    return out


def _load_manifest() -> dict[str, str]:
    """{PIID -> include flag (Y/N)} from the scope manifest."""
    with _SCOPE_MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        return {(r["piid"] or "").strip(): (r.get("include") or "").strip().upper()
                for r in csv.DictReader(fh) if (r.get("piid") or "").strip()}


def assert_piids_in_manifest() -> None:
    """Fail the build unless every prime PIID in the transaction CSVs is present in the
    versioned scope manifest with include=Y, and no include=N prime leaked through. Warns
    (does not fail) when an include=Y prime returned zero transactions, so an omitted query
    cannot quietly masquerade as a genuine zero (reviewer finding #1)."""
    assert _SCOPE_MANIFEST.exists(), f"scope manifest missing: {_SCOPE_MANIFEST}"
    manifest = _load_manifest()
    present = set().union(*_tx_piids().values())

    missing = sorted(p for p in present if p not in manifest)
    assert not missing, f"transaction PIIDs absent from scope manifest: {missing}"

    leaked = sorted(p for p in present if manifest.get(p) == "N")
    assert not leaked, f"include=N PIIDs leaked into transactions (exclusion not applied): {leaked}"

    zero_rows = sorted(p for p, inc in manifest.items() if inc == "Y" and p not in present)
    if zero_rows:
        print(f"[scope] note: {len(zero_rows)} include=Y prime(s) returned zero subawards "
              f"(queried, accounted): {zero_rows}")


# Warn if semantic duplicate candidates exceed this share of the gross reported total.
_DUP_WARN_PCT = 2.0


def assert_duplicate_audit_recorded() -> None:
    """Reviewer build-stopping test #3: there must be no semantic duplicate candidates without
    an adjudication record. Reads the build-time audit summary + log; asserts the per-row log
    accounts for every candidate, and warns when candidate $ exceeds _DUP_WARN_PCT of gross."""
    ah, arows = load_table("duplicate_audit")
    total = next((r for r in arows if (r[ah.index("Program")] or "").strip() == "TOTAL"), None)
    assert total is not None, "duplicate_audit.csv missing TOTAL row (run build_program_transactions)"
    cand_rows = int(float(total[ah.index("Duplicate-Candidate Rows")] or 0))

    _, log = load_table("duplicate_candidates")
    assert len(log) >= cand_rows, (
        f"duplicate adjudication log incomplete: audit reports {cand_rows} candidates, "
        f"log has {len(log)} rows")

    pct = float(str(total[ah.index("Candidate % of Gross")]).rstrip("%") or 0)
    if pct > _DUP_WARN_PCT:
        print(f"[dedup] WARNING: duplicate candidates are {pct:.2f}% of gross reported "
              f"(> {_DUP_WARN_PCT}% threshold) - review extracted/duplicate_candidates.csv")
    else:
        print(f"[dedup] note: {cand_rows} duplicate candidates ({pct:.2f}% of gross), logged + reported")


def assert_archetype_codes_valid() -> None:
    """Every D/P code in the editable inputs (Vendor Archetype Overrides + NAICS-6 Archetype
    Map) must be a valid taxonomy code OR blank. Combined with the axis-specific override-or-
    blank resolution and the valid D0/P0 default, this guarantees every RESOLVED D in D0..D11
    and P in P0..P6 - no blank or numeric-zero archetype can survive (reviewer finding #3)."""
    from workbook_award_classification_refactor.sheets import _taxonomy
    valid_d = {t[0] for t in _taxonomy.DOMAINS} | {""}
    valid_p = {t[0] for t in _taxonomy.OUTPUTS} | {""}
    bad: list[str] = []
    for stem in ("vendor_archetype_overrides", "naics6_archetype_map"):
        headers, rows = load_table(stem)
        jd, jp = headers.index("Capability Domain (D)"), headers.index("Primary Output (P)")
        for i, r in enumerate(rows, start=2):
            d = (r[jd] if jd < len(r) else "").strip()
            p = (r[jp] if jp < len(r) else "").strip()
            if d not in valid_d:
                bad.append(f"{stem} row {i}: D={d!r}")
            if p not in valid_p:
                bad.append(f"{stem} row {i}: P={p!r}")
    assert not bad, "invalid archetype codes (not in D0..D11 / P0..P6 or blank): " + "; ".join(bad[:20])


def assert_naics_rationale_aligned() -> None:
    """Every NAICS-6 D-Rationale that ends in a terminal 'Dxx' code must agree with the assigned
    Capability Domain (D). Stops the auditability drift the reviewer flagged (finding #5) - a note
    concluding '-> D0' while the row is assigned D11 - from recurring after a refresh. Rationales
    with no explicit terminal code (e.g. 'no defensible single D') are skipped."""
    headers, rows = load_table("naics6_archetype_map")
    jd = headers.index("Capability Domain (D)")
    jr = headers.index("D Rationale")
    bad: list[str] = []
    for r in rows:
        d = (r[jd] if jd < len(r) else "").strip()
        ms = re.findall(r"D(\d+)", r[jr] if jr < len(r) else "")
        if ms and f"D{ms[-1]}" != d:
            bad.append(f"NAICS {r[headers.index('NAICS-6')]}: assigned {d}, rationale ends D{ms[-1]}")
    assert not bad, "NAICS D-rationale vs assigned-code drift: " + "; ".join(bad[:20])


def assert_universes_aligned() -> None:
    """Fail the build unless program-vendor == transaction == Supplier Master on the
    (Program x UEI) universe."""
    pv = _single_program_keys("program_vendors")
    tx = _single_program_keys("subaward_transactions")
    sm = _dimension_keys("supplier_master")

    assert pv == tx, "program-vendor vs transaction (Program x UEI) drift: " + _diff(
        pv, tx, "program-vendor", "transaction")
    assert pv == sm, "program-vendor vs Supplier Master drift: " + _diff(
        pv, sm, "program-vendor", "Supplier Master")


def assert_transaction_dates_covered_by_fiscal_axis() -> None:
    """Fail before workbook build if a transaction has no action date or falls outside the
    fixed deflator axis. The <=FY12 catch-all intentionally uses the FY2002 Procurement index,
    so any newly introduced pre-FY2013 federal year other than FY2002 requires a real historical
    deflator row rather than silent reuse of the FY2002 factor."""
    from workbook_award_classification_refactor.sheets._fiscal import FY_BASE, FY_START

    blank: list[str] = []
    future: list[str] = []
    pre_axis: set[int] = set()
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_subaward_transactions")
        jd = headers.index("Subaward Date")
        jr = headers.index("subAwardReportId") if "subAwardReportId" in headers else None
        for i, r in enumerate(rows, start=2):
            raw = (r[jd] if jd < len(r) else "").strip()
            rid = ((r[jr] if jr is not None and jr < len(r) else "") or f"row {i}").strip()
            if not raw:
                blank.append(f"{label}:{rid}")
                continue
            try:
                y, m, _d = (int(x) for x in raw[:10].split("-"))
            except Exception:
                blank.append(f"{label}:{rid} invalid date {raw!r}")
                continue
            fy = y + int(m >= 10)
            if fy > FY_BASE:
                future.append(f"{label}:{rid}=FY{fy}")
            if fy < FY_START:
                pre_axis.add(fy)

    assert not blank, "blank / invalid Subaward Date would be mis-binned: " + "; ".join(blank[:20])
    assert not future, (
        f"transaction federal FY exceeds FY{FY_BASE}; extend _fiscal + Deflators first: "
        + "; ".join(future[:20]))
    assert pre_axis <= {2002}, (
        "<=FY12 catch-all is keyed to the FY2002 deflator but newly contains other fiscal years: "
        + ", ".join(str(x) for x in sorted(pre_axis)))


def assert_prime_awards_cover_transaction_piids() -> None:
    """Every transaction PIID must have a Prime Awards row, otherwise Subaward Activity's
    Block/MYP and prime-PoP lookups fall to '-' / blank while the dollars still remain in scope."""
    headers, rows = load_table("prime_awards")
    j = headers.index("Prime PIID")
    prime = {(r[j] if j < len(r) else "").strip() for r in rows if j < len(r) and r[j].strip()}
    tx = set().union(*_tx_piids().values())
    missing = sorted(tx - prime)
    assert not missing, f"transaction PIIDs missing from Prime Awards: {missing}"


def assert_supplier_year_activity_spine() -> None:
    """The Supplier-Year Activity spine must be EXACTLY the (Program, Federal FY, Subawardee UEI)
    universe derived from the three transaction CSVs - one row per key, no missing/extra key. A
    drift would silently leave Where to Play cells empty (a missing supplier-year) or double-count
    (a duplicate row), so fail the build loudly instead. Federal FY = calendar year, +1 from October
    on (the same convention as _fiscal / build_supplier_year_activity)."""
    expected: set[tuple[str, int, str]] = set()
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_subaward_transactions")
        ju = headers.index("Subawardee UEI")
        jd = headers.index("Subaward Date")
        for r in rows:
            uei = (r[ju] if ju < len(r) else "").strip()
            raw = (r[jd] if jd < len(r) else "").strip()
            if not uei or not raw:
                continue
            y, m, _d = (int(x) for x in raw[:10].split("-"))
            expected.add((label, y + int(m >= 10), uei))

    sh, srows = load_table("supplier_year_activity")
    jp, jf, ju = (sh.index("Program"), sh.index("Federal FY"), sh.index("Subawardee UEI"))
    actual = {((r[jp]).strip(), int(r[jf]), (r[ju]).strip()) for r in srows}

    assert len(actual) == len(srows), (
        f"supplier_year_activity has duplicate (Program, FY, UEI) rows: "
        f"{len(srows)} rows, {len(actual)} distinct keys")
    assert actual == expected, (
        "supplier-year spine != transaction-derived (Program x FY x UEI) universe: "
        + _diff(actual, expected, "supplier-year", "transactions"))


def _hull_set(s: str) -> set[str]:
    """The set of 'DDG NNN' hull tokens in a candidate-hulls / direct-text string."""
    return set(re.findall(r"DDG \d{3}", s or ""))


def assert_hull_piids_mapped() -> None:
    """Every HII-Ingalls DDG transaction PIID must be present in the curated PIID->Hull map
    (extracted/ddg_piid_hull_map.csv), or the hull tagger / roll-ups silently treat the row's hull
    family as unknown. The hull analogue of assert_piids_in_manifest."""
    th, trows = load_table("ddg_subaward_transactions")
    jp, jb = th.index("Prime PIID"), th.index("Builder")
    hii = {(r[jp] or "").strip() for r in trows
           if (r[jb] if jb < len(r) else "").strip() == "HII-Ingalls" and (r[jp] or "").strip()}
    mh, mrows = load_table("ddg_piid_hull_map")
    jm = mh.index("Prime PIID")
    mapped = {(r[jm] or "").strip() for r in mrows if (r[jm] or "").strip()}
    missing = sorted(hii - mapped)
    assert not missing, (
        f"HII-Ingalls DDG transaction PIIDs absent from ddg_piid_hull_map.csv: {missing}")


def assert_hull_map_master_consistent() -> None:
    """The hull classification is now LIVE on the transaction sheet - it INDEXes the curated
    PIID->Hull map and the roll-ups key on the resulting Assigned Hull. So the map must be internally
    consistent with the Hull Master that supplies the roll-up spines: every `Candidate Hulls` token
    has a Hull Master row (else a live INDEX resolves a hull no roll-up row exists for), and every
    `single-ship` PIID lists exactly one candidate (the single-ship formula branch assigns that one
    hull). The conflict-aware formula cannot itself assign an out-of-family hull, so validating these
    inputs is what keeps the live layer sound (the prior assignment-level check read materialized
    columns that are now sheet formulas)."""
    mh, mrows = load_table("ddg_piid_hull_map")
    jc, jk, jp = (mh.index("Candidate Hulls"), mh.index("Exact or Family"), mh.index("Prime PIID"))
    hm, hrows = load_table("ddg_hull_master")
    jh = hm.index("Hull")
    master = {(r[jh] or "").strip() for r in hrows if (r[jh] or "").strip()}

    missing: list[str] = []
    bad_single: list[str] = []
    for r in mrows:
        piid = (r[jp] if jp < len(r) else "").strip()
        toks = sorted(_hull_set(r[jc] if jc < len(r) else ""))
        kind = (r[jk] if jk < len(r) else "").strip()
        missing += [f"{piid}:{t}" for t in toks if t not in master]
        if kind == "single-ship" and len(toks) != 1:
            bad_single.append(f"{piid}:{len(toks)} candidates")
    assert not missing, f"PIID-map Candidate Hulls absent from ddg_hull_master.csv: {missing[:20]}"
    assert not bad_single, f"single-ship PIID rows without exactly one candidate: {bad_single}"


# --- construction-lifecycle layer guards ---------------------------------------------------

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

# Known lifecycle labels (mirror scripts/_lifecycle.STAGE_* / NR_*; the sheet SUMIFS criteria use the
# same strings). A materialized value outside these sets is drift between the Python materializer and
# the live sheet - fail the build, the lifecycle analogue of the hull recalc QA.
_STAGE_LABELS = {"Long-lead", "Construction", "Outfit / test", "Post-delivery", "No schedule data"}
_NARROW_LABELS = {"Single candidate", "2-3 candidates", "Still family-level",
                  "Exception (no window match)", "No schedule data"}


def _ym(s: str):
    """'Sep 2017' -> (2017, 9) for ordering; None if blank / unparseable."""
    parts = (s or "").strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    mon = _MONTHS.get(parts[0][:3].lower())
    return (int(parts[1]), mon) if mon else None


def assert_hull_milestones_monotonic() -> None:
    """The curated DDG Hull Master milestones must satisfy Start Fabrication <= Launch <= Delivery
    wherever present, so the lifecycle windows are well-formed - a launch before fab start, or a
    delivery before launch, would invert a stage boundary and mis-tag every purchase against it."""
    headers, rows = load_table("ddg_hull_master")
    jh = headers.index("Hull")
    js, jl, jd = (headers.index("Start Fabrication"), headers.index("Launch"),
                  headers.index("Delivery"))
    bad: list[str] = []
    for r in rows:
        hull = (r[jh] if jh < len(r) else "").strip()
        seq = [(n, _ym(r[j] if j < len(r) else "")) for n, j in
               (("start", js), ("launch", jl), ("delivery", jd))]
        present = [(n, v) for n, v in seq if v]
        for (n1, v1), (n2, v2) in zip(present, present[1:]):
            if v1 > v2:
                bad.append(f"{hull}: {n1} {v1} > {n2} {v2}")
    assert not bad, "DDG Hull Master milestone dates out of order: " + "; ".join(bad[:20])


def assert_lifecycle_columns_consistent() -> None:
    """The construction-lifecycle layer's materialized columns must be well-formed and the per-row tx
    columns must agree with the C/D candidate + rollup spines (the lifecycle analogue of the hull
    recalc QA). Guards:
      (a) every materialized Lifecycle Stage / Narrowing Result is a KNOWN label (drift vs sheet criteria);
      (b) Lifecycle Stage (A/B) and Narrowing Result (C/D) are mutually exclusive per row;
      (c) the rollup is one row per C/D tx and its Narrowing Result matches the tx column;
      (d) each rollup Timing Candidate Count equals that tx's TRUE (matched) candidate rows;
      (e) the candidate / rollup spines carry NO per-hull dollar (attribution, not allocation - the wall).
    """
    th, trows = load_table("ddg_subaward_transactions")
    jstage, jnarrow, jrid = (th.index("Lifecycle Stage"), th.index("Narrowing Result"),
                             th.index("Subaward Report ID"))
    bad_label: set[str] = set()
    both: list[str] = []
    tx_narrow: dict[str, str] = {}
    for r in trows:
        stage = (r[jstage] if jstage < len(r) else "").strip()
        narrow = (r[jnarrow] if jnarrow < len(r) else "").strip()
        rid = (r[jrid] if jrid < len(r) else "").strip()
        if stage and stage not in _STAGE_LABELS:
            bad_label.add(f"stage {stage!r}")
        if narrow and narrow not in _NARROW_LABELS:
            bad_label.add(f"narrowing {narrow!r}")
        if stage and narrow:
            both.append(rid)
        if narrow:
            tx_narrow[rid] = narrow
    assert not bad_label, ("unknown lifecycle labels (drift vs sheet SUMIFS criteria): "
                           + "; ".join(sorted(bad_label)[:20]))
    assert not both, ("rows carry BOTH a Lifecycle Stage and a Narrowing Result "
                      f"(A/B and C/D must be exclusive): {both[:10]}")

    rh, rrows = load_table("ddg_cd_lifecycle_rollup")
    money_r = [h for h in rh if "$" in h or "amount" in h.lower() or "allocat" in h.lower()]
    assert not money_r, f"rollup spine carries a $ / allocation column (the wall): {money_r}"
    jr_rid, jr_nr, jr_cnt = (rh.index("Subaward Report ID"), rh.index("Narrowing Result"),
                             rh.index("Timing Candidate Count"))
    rollup_nr: dict[str, str] = {}
    rollup_cnt: dict[str, int] = {}
    for r in rrows:
        rid = (r[jr_rid] if jr_rid < len(r) else "").strip()
        assert rid not in rollup_nr, f"duplicate rollup row for transaction {rid}"
        rollup_nr[rid] = (r[jr_nr] if jr_nr < len(r) else "").strip()
        try:
            rollup_cnt[rid] = int((r[jr_cnt] if jr_cnt < len(r) else "0") or 0)
        except ValueError:
            rollup_cnt[rid] = -1
    assert set(rollup_nr) == set(tx_narrow), ("C/D rollup vs transaction report-id set drift: "
                                              + _diff(set(rollup_nr), set(tx_narrow), "rollup", "tx"))
    mism = [rid for rid, nr in rollup_nr.items() if nr != tx_narrow.get(rid)]
    assert not mism, f"rollup Narrowing Result disagrees with the tx column for: {mism[:10]}"

    ch, crows = load_table("ddg_cd_lifecycle_candidates")
    money_c = [h for h in ch if "$" in h or "amount" in h.lower() or "allocat" in h.lower()]
    assert not money_c, f"candidate spine carries a $ / allocation column (the wall): {money_c}"
    jc_rid, jc_match = ch.index("Subaward Report ID"), ch.index("Window Match Flag")
    matched: dict[str, int] = {}
    for r in crows:
        rid = (r[jc_rid] if jc_rid < len(r) else "").strip()
        if (r[jc_match] if jc_match < len(r) else "").strip() == "TRUE":
            matched[rid] = matched.get(rid, 0) + 1
    cnt_bad = [f"{rid}: rollup {rollup_cnt[rid]} vs candidate TRUE {matched.get(rid, 0)}"
               for rid in rollup_cnt if matched.get(rid, 0) != rollup_cnt[rid]]
    assert not cnt_bad, ("Timing Candidate Count disagrees with TRUE candidate rows: "
                         + "; ".join(cnt_bad[:10]))
