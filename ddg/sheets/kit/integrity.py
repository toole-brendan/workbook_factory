"""Build-stopping DDG CSV universe and semantic-integrity guards."""
from __future__ import annotations

import csv
import re

from ddg.lib import SAM_SCOPE_DATA
from ddg.sheets.kit.cuts import load_table

_PROGRAMS = [("ddg", "DDG")]
_SCOPE_MANIFEST = SAM_SCOPE_DATA / "ddg_prime_contract_scope.csv"

def _diff(a: set, b: set, a_name: str, b_name: str) -> str:
    parts = []
    if a - b:
        parts.append(f"{len(a - b)} in {a_name} not in {b_name} (e.g. {sorted(a - b)[:5]})")
    if b - a:
        parts.append(f"{len(b - a)} in {b_name} not in {a_name} (e.g. {sorted(b - a)[:5]})")
    return "; ".join(parts)

def _single_program_keys(suffix: str) -> set[tuple[str, str]]:
    keys = set()
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_{suffix}")
        j = headers.index("Subawardee UEI")
        for r in rows:
            u = (r[j] if j < len(r) else "").strip()
            if u:
                keys.add((label, u))
    return keys

def _dimension_keys(stem: str) -> set[tuple[str, str]]:
    headers, rows = load_table(stem)
    jp, ju = headers.index("Program"), headers.index("Subawardee UEI")
    return {((r[jp] if jp < len(r) else "").strip(), (r[ju] if ju < len(r) else "").strip())
            for r in rows if ju < len(r) and (r[ju] or "").strip()}

def _tx_piids() -> dict[str, set[str]]:
    out = {}
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_subaward_transactions")
        j = headers.index("Prime PIID")
        out[label] = {(r[j] if j < len(r) else "").strip() for r in rows if j < len(r) and (r[j] or "").strip()}
    return out

def _load_manifest() -> dict[str, str]:
    with _SCOPE_MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        return {(r["piid"] or "").strip(): (r.get("include") or "").strip().upper()
                for r in csv.DictReader(fh) if (r.get("piid") or "").strip()}

def assert_piids_in_manifest() -> None:
    assert _SCOPE_MANIFEST.exists(), f"scope manifest missing: {_SCOPE_MANIFEST}"
    manifest = _load_manifest()
    present = set().union(*_tx_piids().values())
    missing = sorted(p for p in present if p not in manifest)
    assert not missing, f"transaction PIIDs absent from scope manifest: {missing}"
    leaked = sorted(p for p in present if manifest.get(p) == "N")
    assert not leaked, f"include=N PIIDs leaked into transactions: {leaked}"
    zero_rows = sorted(p for p, inc in manifest.items() if inc == "Y" and p not in present)
    if zero_rows:
        print(f"[scope] note: {len(zero_rows)} include=Y prime(s) returned zero subawards: {zero_rows}")

def assert_universes_aligned() -> None:
    pv = _single_program_keys("program_vendors")
    tx = _single_program_keys("subaward_transactions")
    sm = _dimension_keys("supplier_master")
    assert pv == tx, "program-vendor vs transaction drift: " + _diff(pv, tx, "program-vendor", "transaction")
    assert tx == sm, "transaction vs Supplier Master drift: " + _diff(tx, sm, "transaction", "Supplier Master")

def assert_duplicate_audit_recorded() -> None:
    ah, arows = load_table("duplicate_audit")
    total = next((r for r in arows if (r[ah.index("Program")] or "").strip() == "TOTAL"), None)
    assert total is not None, "duplicate_audit.csv missing TOTAL row"
    cand_rows = int(float(total[ah.index("Duplicate-Candidate Rows")] or 0))
    _, log = load_table("duplicate_candidates")
    assert len(log) >= cand_rows, f"duplicate adjudication log incomplete: audit {cand_rows}, log {len(log)}"
    pct = float(str(total[ah.index("Candidate % of Gross")]).rstrip("%") or 0)
    print(f"[dedup] note: {cand_rows} duplicate candidates ({pct:.2f}% of gross), logged + reported")

def assert_archetype_codes_valid() -> None:
    from ddg.sheets.kit import taxonomy as _taxonomy
    valid_d = {t[0] for t in _taxonomy.DOMAINS} | {""}
    valid_p = {t[0] for t in _taxonomy.OUTPUTS} | {""}
    bad = []
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
    assert not bad, "invalid archetype codes: " + "; ".join(bad[:20])

def assert_naics_rationale_aligned() -> None:
    headers, rows = load_table("naics6_archetype_map")
    jd, jr = headers.index("Capability Domain (D)"), headers.index("D Rationale")
    bad = []
    for r in rows:
        d = (r[jd] if jd < len(r) else "").strip()
        ms = re.findall(r"D(\d+)", r[jr] if jr < len(r) else "")
        if ms and f"D{ms[-1]}" != d:
            bad.append(f"NAICS {r[headers.index('NAICS-6')]}: assigned {d}, rationale ends D{ms[-1]}")
    assert not bad, "NAICS D-rationale vs assigned-code drift: " + "; ".join(bad[:20])

def assert_transaction_dates_covered_by_fiscal_axis() -> None:
    from ddg.sheets.kit.fiscal import FY_BASE, FY_START
    blank, future, pre_axis = [], [], set()
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
    assert not future, f"transaction federal FY exceeds FY{FY_BASE}: " + "; ".join(future[:20])
    assert pre_axis <= {2002}, "<=FY12 catch-all contains non-FY2002 years: " + ", ".join(map(str, sorted(pre_axis)))

def assert_prime_awards_cover_transaction_piids() -> None:
    headers, rows = load_table("prime_awards")
    j = headers.index("Prime PIID")
    prime = {(r[j] if j < len(r) else "").strip() for r in rows if j < len(r) and r[j].strip()}
    tx = set().union(*_tx_piids().values())
    missing = sorted(tx - prime)
    assert not missing, f"transaction PIIDs missing from Prime Awards: {missing}"

def assert_supplier_year_activity_spine() -> None:
    expected = set()
    for stem, label in _PROGRAMS:
        headers, rows = load_table(f"{stem}_subaward_transactions")
        ju, jd = headers.index("Subawardee UEI"), headers.index("Subaward Date")
        for r in rows:
            uei = (r[ju] if ju < len(r) else "").strip()
            raw = (r[jd] if jd < len(r) else "").strip()
            if not uei or not raw:
                continue
            y, m, _d = (int(x) for x in raw[:10].split("-"))
            expected.add((label, y + int(m >= 10), uei))
    sh, srows = load_table("supplier_year_activity")
    jp, jf, ju = sh.index("Program"), sh.index("Federal FY"), sh.index("Subawardee UEI")
    actual = {((r[jp]).strip(), int(r[jf]), (r[ju]).strip()) for r in srows}
    assert len(actual) == len(srows), f"supplier_year_activity has duplicate keys: {len(srows)} rows, {len(actual)} keys"
    assert actual == expected, "supplier-year spine != transaction-derived universe: " + _diff(actual, expected, "supplier-year", "transactions")

def _hull_set(s: str) -> set[str]:
    return set(re.findall(r"DDG \d{3}", s or ""))

def assert_hull_piids_mapped() -> None:
    th, trows = load_table("ddg_subaward_transactions")
    jp, jb = th.index("Prime PIID"), th.index("Builder")
    hii = {(r[jp] or "").strip() for r in trows if (r[jb] if jb < len(r) else "").strip() == "HII-Ingalls" and (r[jp] or "").strip()}
    mh, mrows = load_table("ddg_piid_hull_map")
    jm = mh.index("Prime PIID")
    mapped = {(r[jm] or "").strip() for r in mrows if (r[jm] or "").strip()}
    missing = sorted(hii - mapped)
    assert not missing, f"HII-Ingalls DDG transaction PIIDs absent from ddg_piid_hull_map.csv: {missing}"

def assert_hull_map_master_consistent() -> None:
    mh, mrows = load_table("ddg_piid_hull_map")
    jc, jk, jp = mh.index("Candidate Hulls"), mh.index("Exact or Family"), mh.index("Prime PIID")
    hm, hrows = load_table("ddg_hull_master")
    jh = hm.index("Hull")
    master = {(r[jh] or "").strip() for r in hrows if (r[jh] or "").strip()}
    missing, bad_single = [], []
    for r in mrows:
        piid = (r[jp] if jp < len(r) else "").strip()
        toks = sorted(_hull_set(r[jc] if jc < len(r) else ""))
        kind = (r[jk] if jk < len(r) else "").strip()
        missing += [f"{piid}:{t}" for t in toks if t not in master]
        if kind == "single-ship" and len(toks) != 1:
            bad_single.append(f"{piid}:{len(toks)} candidates")
    assert not missing, f"PIID-map Candidate Hulls absent from ddg_hull_master.csv: {missing[:20]}"
    assert not bad_single, f"single-ship PIID rows without exactly one candidate: {bad_single}"

_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
def _ym(s: str):
    parts = (s or "").strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    mon = _MONTHS.get(parts[0][:3].lower())
    return (int(parts[1]), mon) if mon else None

def assert_hull_milestones_monotonic() -> None:
    headers, rows = load_table("ddg_hull_master")
    jh, js, jl, jd = headers.index("Hull"), headers.index("Start Fabrication"), headers.index("Launch"), headers.index("Delivery")
    bad = []
    for r in rows:
        hull = (r[jh] if jh < len(r) else "").strip()
        seq = [(n, _ym(r[j] if j < len(r) else "")) for n, j in (("start", js), ("launch", jl), ("delivery", jd))]
        present = [(n, v) for n, v in seq if v]
        for (n1, v1), (n2, v2) in zip(present, present[1:]):
            if v1 > v2:
                bad.append(f"{hull}: {n1} {v1} > {n2} {v2}")
    assert not bad, "DDG Hull Master milestone dates out of order: " + "; ".join(bad[:20])

_STAGE_LABELS = {"Long-lead", "Construction", "Outfit / test", "Post-delivery", "No schedule data"}
_NARROW_LABELS = {"Single candidate", "2-3 candidates", "Still family-level", "Exception (no window match)", "No schedule data"}

def assert_lifecycle_columns_consistent() -> None:
    th, trows = load_table("ddg_subaward_transactions")
    jstage, jnarrow, jrid = th.index("Lifecycle Stage"), th.index("Narrowing Result"), th.index("Subaward Report ID")
    bad_label, both, tx_narrow = set(), [], {}
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
    assert not bad_label, "unknown lifecycle labels: " + "; ".join(sorted(bad_label)[:20])
    assert not both, f"rows carry BOTH Lifecycle Stage and Narrowing Result: {both[:10]}"
    rh, rrows = load_table("ddg_cd_lifecycle_rollup")
    assert not [h for h in rh if "$" in h or "amount" in h.lower() or "allocat" in h.lower()]
    jr_rid, jr_nr, jr_cnt = rh.index("Subaward Report ID"), rh.index("Narrowing Result"), rh.index("Timing Candidate Count")
    rollup_nr, rollup_cnt = {}, {}
    for r in rrows:
        rid = (r[jr_rid] if jr_rid < len(r) else "").strip()
        assert rid not in rollup_nr, f"duplicate rollup row for transaction {rid}"
        rollup_nr[rid] = (r[jr_nr] if jr_nr < len(r) else "").strip()
        rollup_cnt[rid] = int((r[jr_cnt] if jr_cnt < len(r) else "0") or 0)
    assert set(rollup_nr) == set(tx_narrow), "C/D rollup vs transaction report-id set drift: " + _diff(set(rollup_nr), set(tx_narrow), "rollup", "tx")
    mism = [rid for rid, nr in rollup_nr.items() if nr != tx_narrow.get(rid)]
    assert not mism, f"rollup Narrowing Result disagrees with tx column: {mism[:10]}"
    ch, crows = load_table("ddg_cd_lifecycle_candidates")
    assert not [h for h in ch if "$" in h or "amount" in h.lower() or "allocat" in h.lower()]
    jc_rid, jc_match = ch.index("Subaward Report ID"), ch.index("Window Match Flag")
    matched = {}
    for r in crows:
        rid = (r[jc_rid] if jc_rid < len(r) else "").strip()
        if (r[jc_match] if jc_match < len(r) else "").strip() == "TRUE":
            matched[rid] = matched.get(rid, 0) + 1
    cnt_bad = [f"{rid}: rollup {rollup_cnt[rid]} vs candidate TRUE {matched.get(rid, 0)}" for rid in rollup_cnt if matched.get(rid, 0) != rollup_cnt[rid]]
    assert not cnt_bad, "Timing Candidate Count disagrees with TRUE candidate rows: " + "; ".join(cnt_bad[:10])
