# HANDOFF — promote the DDG-51 research findings into the workbook

**Written:** 2026-06-30
**For:** the next agent, who will *actually update the workbook* (this session did the research + staging; **nothing has been promoted into the build yet**).
**Read this whole file before touching any CSV.** The single biggest trap is in §3 (the factory renders *pre-computed* CSVs — most promotions are NOT simple file edits).

---

## 1. What you're picking up

`workbook_factory/` builds one combined **TAM + SAM** workbook per Navy program. Only **DDG-51** exists so far (`ddg/`). A prior session investigated the DDG SAM research backlog with four parallel agents, cross-checked against an external ship registry (MIRS / S&P Global) and the federal awards APIs, and produced a fully-cited findings report with concrete, grain-safe promotion proposals. **Your job: promote the approved items into the curated inputs, regenerate what needs regenerating, rebuild, and QA.**

### Read these first, in order
1. **`ddg/docs/ddg_sam_research_findings.md`** — THE reference. Every promotable item with exact target file, current→proposed value, source evidence, and a grain-discipline note. Everything below points into it.
2. `ddg/docs/ddg_sam_model_goals.md` — the framing (denominator ladder, grain discipline).
3. `ddg/docs/ddg_sam_research_backlog.md` — the original research queue + the 5-point **promotion checklist** (apply it to every change).
4. `log/2026-06-30_session-0*.md` — how the workbook was built (flatten, FY-window, kit split).

---

## 2. Build + verify loop (run after EVERY change)

```bash
# Build (stdlib-only, Python 3.9, no openpyxl in the build path)
cd /Users/brendantoole/projects3/workbook_factory/ddg
python3 build_ddg.py
# -> writes "20260630_Distributed Shipbuilding DDG51_vS.xlsx", currently 37 sheets
```

**Recalc QA (the project's standing bar — 0 error cells required).** LibreOffice is at `/Applications/LibreOffice.app/Contents/MacOS/soffice`. Force recalc-on-load, convert, scan for `t="e"` cells:

```bash
SC=/tmp/lo_recalc; mkdir -p $SC/prof/user $SC/in $SC/out
cat > $SC/prof/user/registrymodifications.xcu <<'XCU'
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
XCU
cp "ddg/20260630_Distributed Shipbuilding DDG51_vS.xlsx" $SC/in/wb.xlsx
/Applications/LibreOffice.app/Contents/MacOS/soffice -env:UserInstallation="file://$SC/prof" \
  --headless --calc --convert-to xlsx:"Calc MS Excel 2007 XML" --outdir $SC/out $SC/in/wb.xlsx
python3 - <<'PY'
import zipfile
from xml.etree import ElementTree as ET
NS="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
z=zipfile.ZipFile("/tmp/lo_recalc/out/wb.xlsx"); errs=0
for n in z.namelist():
    if n.startswith("xl/worksheets/") and n.endswith(".xml"):
        for c in ET.fromstring(z.read(n)).iter(NS+"c"):
            if c.get("t")=="e": errs+=1
print("ERROR CELLS:", errs, "->", "PASS" if errs==0 else "FAIL")
PY
```
`errs == 0` is the pass condition (checks `#REF!/#DIV0!/#VALUE!/#NAME?/#NUM!/#NULL!/#N/A`).

---

## 3. ⚠️ CRITICAL ARCHITECTURE — read before editing any CSV

**`workbook_factory/ddg` is a *rendering layer* over pre-computed CSVs. It carries NO generation/tagging tooling.** The tagging + rollup *generators* live UPSTREAM at:

```
ooxml_build_pipelines_light/projects/distributed_shipbuilding/sam/sam_awards_data/workbook_award_classification_refactor/scripts/
```

So each curated input is one of two kinds — **and you must know which before editing:**

| Kind | Meaning | How to promote |
|---|---|---|
| **Leaf input** | Read directly; downstream sheets reference it via **live build-time formulas** | Edit the factory CSV → rebuild. Propagates. |
| **Pre-aggregated output** | A CSV that was *computed upstream* from other inputs (e.g. a $ rollup, or transaction tag columns) | Edit the upstream *source* → **re-run the upstream generator** → **copy the regenerated CSV(s) into the factory** → rebuild. Editing the factory copy alone is wrong/inconsistent. |

**The trap:** `ddg_hii_swbs_crosswalk.csv` is displayed as its own sheet, but the SWBS **dollar rollup** (`ddg_swbs_by_subsystem.csv`) and the transaction-level `SWBS`/`SWBS Subsystem` columns are **pre-aggregated**. Appending 55 codes to the crosswalk changes the *displayed crosswalk* but reclassifies **$0** of the U00 bucket, because the rollup is static. You must regenerate.

**Data-flow map (verify each before you rely on it):**
- **SWBS** — `build_swbs_crosswalk.py` → `hii_swbs_crosswalk.csv`; `build_ddg_swbs_rollup.py` reads crosswalk → `ddg_swbs_by_subsystem.csv`; `tag_ddg_transactions_swbs.py` reads `hii_ddg_record_components.csv` + crosswalk → appends SWBS cols to `ddg_subaward_transactions.csv`. **Promoting SWBS = edit crosswalk upstream, re-run both scripts, sync all 3 CSVs into the factory.**
- **Lifecycle/hull** — `ddg_hull_master.csv` is a leaf input. But `ddg_cd_lifecycle_candidates.csv` / `ddg_cd_lifecycle_rollup.csv` are **pre-computed** by `build_ddg_cd_lifecycle.py` (+ `tag_ddg_transactions_lifecycle.py`, `_lifecycle.py`). Editing hull dates updates the hull-master sheet (and live-formula consumers) but does NOT move lifecycle stage tags unless you re-run those. *(Per findings §P2-5 the date updates are model-neutral, so this is usually fine — but the Kilmer/Lugar start-fab corrections could shift windows if regenerated.)*
- **Vendor archetype (P4)** — `vendor_archetype_overrides.csv` is a **leaf input**; other sheets pull it via live formulas (`overrides_cols`). Editing it *likely* propagates at build time — **but verify** whether `where_to_play` / `domain_concentration` / `archetype_application_audit` consume a pre-computed `ddg_archetype_results.csv` (generated upstream by `merge_archetype_pulls.py` / `build_archetype_overrides.py`); if so, regen that too.

**Known-broken generator:** `build_program_transactions.py` (the base 50-column transaction generator) **cannot run** — the tam restructure relocated its scope file (documented in `tag_ddg_transactions_swbs.py`'s header). The *taggers* (`tag_ddg_transactions_swbs/lifecycle/hulls.py`) DO run because they only need the already-built transactions CSV + the SWBS package. So SWBS/lifecycle re-tagging is feasible; a full base-transaction rebuild is not (don't attempt it).

---

## 4. Promotion worklist (prioritized)

Details, exact rows, and evidence are in `ddg/docs/ddg_sam_research_findings.md` — the sections are named (P3-1, P4-2, etc.). Do them in this order; rebuild + recalc-QA after each.

### P3 — SWBS crosswalk (~$99M, highest value) — findings §P3-1, §P3-2
- **What:** add 46 observed + 9 same-base curated HII codes (55 total) to `hii_swbs_crosswalk.csv`. One new subsystem row **572** in `ddg_swbs_by_subsystem.csv` (for 01006-01).
- **Kind:** PRE-AGGREGATED → follow §3 regen path (edit crosswalk upstream → `build_ddg_swbs_rollup.py` + `tag_ddg_transactions_swbs.py` → sync `hii_swbs_crosswalk.csv`, `ddg_swbs_by_subsystem.csv`, `ddg_subaward_transactions.csv` into `ddg/data/workbook_inputs/sam_awards/{swbs,transactions}/`).
- **Guardrails:** HII-Ingalls ONLY (no BIW). Basis column = `Observed` (component text names the part) or `Curated inference` (same-base sibling). Do NOT promote the 07xxx no-text family by prefix (§P3-4) or the $104M unmappable tail.
- **Expected effect:** U00 bucket $264.8M → ~$166M. Verify the rollup actually moved (this is the whole point — if U00 is unchanged you didn't regen).

### P4 — vendor archetype overrides (~22 strong) — findings §P4-2, §P4-3
- **What:** add/update ~13 registry-curated UEIs + ~9 P0→P fills in `ddg_vendor_archetype_overrides.csv` (cols: Program, Subawardee UEI, Capability Domain (D), Primary Output (P), + two Note cols). Skip the ~12 medium NAICS-only (§P4-2 lower rows) unless asked.
- **Kind:** leaf input (likely live-formula) — **verify** per §3 whether an archetype-results regen is also needed.
- **Guardrails:** two-axis rule (D = technical ship area; P = physical output/integration level). Only vendors already in `ddg_supplier_master.csv`. **Do NOT** use `vendor_evidence_registry.csv`'s `ddg_signed_$M` for anything — it's discredited (see §6). Its *bucket* labels are fine; its dollars are not.

### P2 — hull_master milestones + MIRS provenance — findings §P2-1, §P2-5
- **What:** (a) 6 date/provenance updates (deliveries 128/124/127 re-sourced; launches 129/131/126 Projected→Actual); (b) re-cite ~20 `Milestone Source URL`s from Wikipedia → MIRS (S&P Global); (c) corrections: DDG 134 Kilmer & 136 Lugar Start-Fab too-early (blank or push out), DDG 127 launch reconcile, DDG 126 relabel christening≠launch. Consider adding a proper **Keel** column from MIRS (our "Start Fabrication" is semantically mixed).
- **Kind:** `ddg_hull_master.csv` is a leaf input → edit + rebuild. (Lifecycle regen only if you want stage tags to move; findings says model-neutral.)
- **Join key:** `ddg/data/research_worklists/ddg_hull_name_mirs_crosswalk.csv` (hull↔name↔IMO + MIRS schedule, triangulated, builders 34/34 agree). Source registry file: `~/Downloads/MIRS_US Built_Destroyers.xlsx` — **copy it into `ddg/data/workbook_inputs/reference/` first** as a cited source before using it in citations.

### P1 — hull attribution — findings §P1-1 (REVISED)
- **DO NOT** add DDG 150 to the FY23-27 family. The MIRS/Wikipedia cross-check showed the FY23-27 MYP is exactly DDG 140-149 (10 ships) and DDG 150 is the next block (FY28+, unnamed). The Espey "DDG 150" subaward is long-lead → **keep it X**.
- **Only** defensible edit: `ddg_hull_master.csv` DDG 150 row builder `TBD → HII (FY28+, advance procurement observed)`, confidence Low.

---

## 5. Guardrails (apply to every change)

- **Promotion checklist** (backlog): (1) exact field changing? (2) source evidence? (3) improves a grade/mapping/date/classification? (4) preserves grain discipline? (5) could it push C/D family dollars onto one hull? → if yes, STOP.
- **Grain discipline:** A/B = exact single hull; **C/D = candidate SET — never collapse to one hull, never split dollars**; X = conflict. Two-axis D/P for vendors. SWBS = HII only.
- **Do NOT** narrow lifecycle on `Prime Requirement Hull Text` — proven false-precision trap (§P2-3).
- **Do NOT** trust `vendor_evidence_registry.csv` `ddg_signed_$M` (§6).

---

## 6. Closed / disproven this session — do NOT re-open

- **"~$1.4B of DDG supplier-coverage gap" (Major Tool & Machine et al.) — DISPROVEN.** SAM Contract Awards API verification: NAVSEA-shipbuilding (office N00024) obligation = **$0.00M** for all 7 vendors; they're Air Force / Army / DLA / NAVAIR machining shops. The `$986.9M` was a NAICS-tail-pass **ceiling** artifact (Major Tool's top-100 ceiling sum = $50.7B). Evidence: `ddg/data/research_worklists/ddg_large_vendor_attribution_check.csv` + findings "Cross-cutting finding". **Do not ingest these as DDG suppliers.**
- **DDG 150 builder external sourcing** — resolved (future FY28+ hull; not an attribution question).
- **HII work-item-code dictionary (would crack the $104M U00 tail)** — not obtainable; don't chase.

---

## 7. Optional future work (not blocking)

- **BIW FY23-27 subawards** (`N0002423C2305` = DDG 140/144/148) — 0 subawards in corpus today; awaits the next SAM/FSRS subaward pull. API how-to + key below.
- **SEC EDGAR TAM cross-check** — HII Ingalls-segment revenue/backlog time series (XBRL `companyconcept`, no key) as a top-down check on TAM. **Caveat:** Ingalls segment = DDG + LHA amphibs + NSC cutters (not DDG-pure); BIW is invisible (buried in GD Marine Systems w/ Electric Boat). Good for magnitude context, not hull detail.

---

## 8. File & credential map

**Curated inputs (edit targets):** `ddg/data/workbook_inputs/sam_awards/{hull,lifecycle,swbs,classification,supplier,transactions,scope}/`
**Build:** `ddg/build_ddg.py`, `ddg/lib.py`, `ddg/sheets/` (37 tab modules), `ddg/sheets/kit/` (helpers).
**Docs:** `ddg/docs/ddg_sam_research_findings.md` (reference), `ddg_sam_model_goals.md`, `ddg_sam_research_backlog.md`.
**Staged artifacts (this session, NOT wired into build):** `ddg/data/research_worklists/ddg_hull_name_mirs_crosswalk.csv`, `ddg_large_vendor_attribution_check.csv`.
**Upstream generators + evidence:** `ooxml_build_pipelines_light/projects/distributed_shipbuilding/sam/sam_awards_data/workbook_award_classification_refactor/scripts/` (generators) and `.../ddg_hii_swbs_subaward_package/`, `.../supplier_bucketing/`, `.../sam_entity_enrichment/`, `.../corpus/extracted/` (evidence).
**External:** `~/Downloads/MIRS_US Built_Destroyers.xlsx` (ship registry); `ooxml_build_pipelines_light/.env` → `SAM_API_KEY` (entity-role, 1,000/day; force IPv4 on macOS); `ooxml_build_pipelines_light/Federal_Awards_API_HowTo.md` (API guide — read §0, §4, §7 before any pull).

---

## 9. Before you commit

1. `python3 build_ddg.py` succeeds, sheet count sane (37 unless you intentionally added a tab).
2. LibreOffice recalc QA → **0 error cells** (§2).
3. For SWBS: confirm the U00 rollup actually shrank (else the regen didn't take).
4. Sanity-check headline numbers didn't move unexpectedly (findings §P3-5 has the target U00 figures; session-01 log has TAM headline sanity values).
5. `workbook_factory` is its own git repo — branch, don't commit straight to `main`; end commit messages with the Co-Authored-By trailer.
6. Update `ddg/docs/ddg_sam_research_findings.md` promotion-summary table to mark what you actually applied, and add a `log/` session entry.
