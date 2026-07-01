# DDG-51 SAM research findings (round 1)

**Date:** 2026-06-30
**Companion to:** [`ddg_sam_research_backlog.md`](ddg_sam_research_backlog.md) (the queue) and [`ddg_sam_model_goals.md`](ddg_sam_model_goals.md) (the framing).
**Status:** Investigation only — **no curated input files were edited.** Every item below is a *proposal* gated by the backlog's promotion checklist. Promotion is a separate, deliberate step.

This document records what a four-stream investigation of the backlog turned up using **evidence already in the repo** (the workbook's own subaward corpus + the upstream research packages under `ooxml_build_pipelines_light`), plus a small amount of web sourcing for hull milestone dates (Priority 2 only). It cites, for every finding, the exact source file and field so a zero-context reader can verify and promote.

---

## Method

For each backlog priority, the current curated workbook input was compared against (a) the workbook's own transaction/supplier corpus and (b) the upstream already-generated research packages. Hull and SWBS grading logic was re-implemented from the upstream tagging scripts and re-run over the full corpus to confirm the curated grades, rather than trusting the cached columns.

**Key structural fact that frames everything:** the curated `ddg_hull_master.csv`, `ddg_piid_hull_map.csv`, `ddg_hii_swbs_crosswalk.csv`, `ddg_hull_exceptions.csv`, and `ddg_cd_lifecycle_candidates.csv` are **byte-identical** to their upstream `extracted/` copies. So the upstream `extracted/` folder holds **no new information** for those. The genuinely new leverage is in:
1. the upstream **research packages** that were generated but never fully promoted (`sam_entity_enrichment/`, `supplier_bucketing/`, `ddg_hii_swbs_subaward_package/`, `corpus/extracted/`), and
2. **cross-referencing the workbook's own transaction corpus** (hull/lifecycle/SWBS columns already tagged on 5,006 logical records).

### Grain-discipline guardrails (held throughout)
- Hull grades: **A/B** = exact single build hull (direct evidence); **C/D** = family-level candidate *set* (never collapsed to one hull, dollars never split per-hull); **X** = conflict/unassigned.
- Vendor archetype is two-axis: **D** = Capability Domain (technical ship area); **P** = Primary Output (physical output / integration level). **D0/P0** are the unclassified defaults.
- SWBS mapping is **HII-Ingalls only**; GD-BIW stays out of the SWBS universe.

### Source inventory (files consulted)

**Workbook curated inputs** — `workbook_factory/ddg/data/workbook_inputs/sam_awards/`
- `hull/ddg_piid_hull_map.csv`, `hull/ddg_hull_master.csv`, `hull/ddg_hull_exceptions.csv`
- `lifecycle/ddg_cd_lifecycle_candidates.csv`, `lifecycle/ddg_cd_lifecycle_rollup.csv`
- `transactions/ddg_subaward_transactions.csv` (5,006 logical records)
- `swbs/ddg_hii_swbs_crosswalk.csv`, `swbs/ddg_swbs_by_subsystem.csv`
- `classification/ddg_vendor_archetype_overrides.csv`, `classification/ddg_naics6_archetype_map.csv`
- `supplier/ddg_supplier_master.csv`, `supplier/ddg_supplier_year_activity.csv`

**Upstream research packages** — `ooxml_build_pipelines_light/projects/distributed_shipbuilding/`
- `sam/sam_awards_data/workbook_award_classification_refactor/scripts/{_hull_logic.py, _lifecycle.py, tag_ddg_transactions_*.py, build_*.py}` (grading logic)
- `sam/sam_awards_data/workbook_award_classification_refactor/extracted/swbs_curated_c.csv`
- `sam/sam_awards_data/ddg_hii_swbs_subaward_package/{hii_ddg_code_dictionary.csv, hii_ddg_record_components.csv, swbs_hierarchy.csv, MANIFEST.md}`
- `sam/sam_awards_data/corpus/extracted/{coverage_unclassified_top.csv, vendor_class_matrix.csv, registry_additions_worksheet.csv, piid_profile.csv}`
- `sam/sam_awards_data/supplier_bucketing/vendor_evidence_registry.csv`
- `sam/sam_awards_data/sam_entity_enrichment/{unique_uei_sam_enrichment.csv, raw/<UEI>.json}`
- `tam/ddg_research/extracted/{_discovered_piids.csv, nc_annual_by_piid.csv, sam_vs_usaspending_per_piid.csv}`

**Web sources** — Priority 2 milestone dates (cited inline in §2); Wikipedia `List_of_Arleigh_Burke-class_destroyers` for the DDG 137-149 name↔hull pairing (§P2-5).

**External commercial source** — `~/Downloads/MIRS_US Built_Destroyers.xlsx` (S&P Global / IHS *Sea-web* registry extract, generated 2026-06-30; not yet copied into the repo). Drives §P2-5 and the staged crosswalk `data/research_worklists/ddg_hull_name_mirs_crosswalk.csv`.

---

## Priority 1 — Hull attribution coverage

**Headline:** the curated map and A/B/C/D/X grading are **already tight**. Re-parsing raw hull text vs the `Direct Hull Text` column across all 5,006 records produced **0 regex mismatches**, and no high-dollar C/D row hides a recoverable single hull. There is exactly **one** promotable item.

### P1-1 — PROMOTABLE: add DDG 150 to the HII FY23-27 family

- **Target:** `hull/ddg_piid_hull_map.csv`, row `N0002423C2307` — Candidate Hulls `DDG 141 / 142 / 143 / 145 / 146 / 147 / 149` → **add `DDG 150`**. (Map note currently reads *"DDG 150 unvalidated (excluded from family)."*)
- **Downstream effect:** `transactions/ddg_subaward_transactions.csv` **Subaward Report ID 29918038** (ESPEY MFG AND ELECTRONICS CORP, UEI `Z89SS59265U9`), currently graded **X** and logged in `hull/ddg_hull_exceptions.csv` as "Direct hull outside PIID family," flips to **B (exact) → DDG 150**.
- **Source evidence (internal, already held):** the subaward record itself —
  - `Subaward Number = 31688-0`
  - `Subaward Description = "DDG 150 04090-01 CSE PS 310-03A"`
  - `Direct Hull Count = 1`, `Prime PIID = N0002423C2307`
  - `Prime Entity Name = HUNTINGTON INGALLS INCORPORATED`
  - `Description of Requirement = "CONSTRUCTION OF DDG 51 SHIPS FY23-27"`
  - `Builder = HII-Ingalls`, `Subaward Date = 2026-01-30`
  - A direct supplier to HII billing a **build** CSE/PS-310 item (no REBUY/REPAIR keyword) explicitly tagged DDG 150 under HII's own FY23-27 construction MYP.
- **Proposed grade:** **B** (exact, single in-family *build* hull — not an origin/rebuy reference).
- **Grain note:** adding a hull *expands* the candidate set; it does not collapse family-level dollars onto one hull. ✅
- **Caveat / data gap:** rests on a **single data point**. DDG 150 appears in *zero* other files — `grep "DDG 150"` across `tam/ddg_research/extracted/_discovered_piids.csv`, `corpus/extracted/piid_profile.csv`, and `nc_annual_by_piid.csv` returns nothing. Yard alternation (148-BIW / 149-HII / 150-?) is externally ambiguous; the discriminating internal signal is that the subaward sits under HII's PIID. **One external NAVSEA/USNI FY23-27 MYP hull-to-yard line would harden this** before promotion.
- **⚠ Update (MIRS / Wikipedia cross-check, this round) — this recommendation is now REVISED, see [P2-5](#p2-5--mirs-sp-global--ihs-sea-web-cross-check--provenance-upgrade).** Independent sourcing shows the **FY23-27 MYP is exactly 10 ships = DDG 140-149** (Wikipedia's `List_of_Arleigh_Burke-class_destroyers` confirms every name↔builder pairing, and they match our `ddg_piid_hull_map` family split exactly), and **DDG 150 is the next block (FY28+), still unnamed/unassigned.** So the Espey "DDG 150" line under the FY23-27 PIID is best read as **long-lead / advance procurement for a future hull**, not a build hull of that contract. Under grain discipline (don't convert long-lead into exact-hull assignment), the correct action is **NOT** to add 150 to the FY23-27 family and **NOT** to flip the Espey row to exact B — **leave it X (or flag long-lead).** The only defensible residue is a Low-confidence `ddg_hull_master.csv` note: DDG 150 builder `TBD → HII (FY28+, advance-procurement observed)`.

### P1-2 — Investigated, cannot promote (confirms model is sound)

- **Top-30 high-dollar C/D rows ($43.9M → ~$7.5M each):** all bulk GFE/CSE major equipment (Rolls-Royce/GE gas turbines, York/Johnson Controls A/C plants, DRS/Espey switchgear, CAPEX SOWs) with SWBS-coded descriptions carrying **no** hull, or a multi-hull prime-requirement list (e.g. `DDG 117 / 119 / 120 / 122 / 124`, spanning both yards). Correctly family-level.
- **No regex-missed single hulls:** every C/D row scanned for `HULL`/`H/N`/`HN` keywords and 21 in-window ship names (Jack H. Lucas=125, Ted Stevens=128, …). **0 rows** name a single in-family hull the regex missed.
- **60 rebuy/rework exceptions ($4.27M):** e.g. Report ID 21030670 "REBUY SO12 R-396633 / DDG119" under `N0002418C2307` (family 128-139). The named hull is the part's **prior origin hull**, not a build hull — the grain rule bars upgrading to an origin/rebuy hull. *Optional methodology tweak only (not a promotion):* these could be re-graded **X→D** to move $4.27M from "conflict" into family coverage, but it yields **no exact attribution** and carries REBUY-vs-REPAIR ambiguity (4 rows say "REPAIR" of a delivered hull and must stay X).
- **Report ID 29385211** (ADI TECHNOLOGIES, $82,190, "REBUY … DDG133 & DDG131"): both in-family → **true multi-hull**, stays X.
- **Report ID 20700971** (LAKE SHORE, $164,822, "RTV … DDG121/128"): names two hulls → multi-hull, stays X.
- **4 REPAIR rows** under single-ship FY10/11 contracts (Report IDs 20684535 / 20684385 / 20684263 / 20684618 under `N0002411C2307`/`C2309`) referencing later hulls (119/121/123): genuine cross-hull conflicts, stay X.
- **41 lifecycle reports timing-narrowed to ONE candidate ($15.5M, mostly DDG 141 the FY23-27 lead hull):** this is **timing inference**, not direct evidence — correctly handled today as an `Include as Timing Candidate?` flag in `ddg_cd_lifecycle_candidates.csv`, *not* a grade change. Must not be promoted to A/B.

### P1-3 — Data gaps / needs external sourcing
1. **DDG 150 builder confirmation** (hardens P1-1) — one NAVSEA/USNI line.
2. **`N0002423C2305` (GD-BIW FY23-27, family 140/144/148) still has 0 subawards in the corpus** — confirmed (0 rows mention DDG 140/144/148 anywhere). The map note "No subawards in corpus yet; needs validation" remains accurate. Revisit after the next SAM subaward pull.
3. **Unmapped DDG PIIDs with real upstream dollars, absent from the workbook corpus** (from `corpus/extracted/piid_profile.csv`): `N0002419C2322` (GD-BIW orders, $18.2M FY22-25, 45 vendors) and `N0002419C4452` (GD-BIW PIO, $24.6M, 54 vendors), plus thinner `N0002414C4313`, `N0002412C2312`. These are **PIO / blanket-order / design vehicles that span hulls** — non-hull, family-level-unassignable even if ingested. A *corpus-scope* decision, not a hull-mapping gap; do **not** add to the family map.
4. **Per-hull award/option-year subdivision of multi-hull families** would require NAVSEA CLIN/option-exercise records not in the repo — and even then yields a *subset*, not exact, under grain rules.

---

## Priority 2 — Lifecycle coverage

**Headline (honest result):** a consistency check of `ddg_cd_lifecycle_rollup.csv` against `ddg_hull_master.csv` found **0 post-delivery inclusions and 0 too-early (>48 mo) inclusions** — the rollup is already fully self-consistent with every date the master holds. Because the lifecycle logic (`_lifecycle.stage_for`) windows on the **date value**, not the confidence flag, and the master already carried these launch/delivery dates as *Projected*, the web research below **hardens provenance (Projected→Actual) and confirms the model is current; it does not move candidate-set membership or stage tags.**

### P2-1 — PROMOTABLE: 6 milestone updates

Target file: `hull/ddg_hull_master.csv`. Where only a launch is now Actual but delivery is still future, the per-hull `Schedule Confidence` should stay *Projected* until delivery; the individual milestone date/source still upgrades.

| Hull | Field | Current | Proposed | Source | Confidence change |
|---|---|---|---|---|---|
| DDG 128 Ted Stevens | Delivery | Dec 2025 (Actual) | **Dec 29 2025** (Actual) | navsea.navy.mil `…/Article/4368261/`; hii.com `/news/hii-delivers-destroyer-ted-stevens-ddg-128` | source upgrade Wikipedia→NAVSEA/HII primary |
| DDG 124 Harvey C. Barnum Jr. | Delivery | Nov 2025 (Actual) | **Nov 17 2025** (Actual) | navy.mil `…/Article/4337290/`; navsea `…/4334978/` | source upgrade Wikipedia→navy.mil |
| DDG 127 Patrick Gallagher | Delivery | May 2026 (Actual) | **May 28 2026** (Actual, ~2 mo early) | globalsecurity.org `…/mil-260601-usnpr01.htm` (navy.mil release); collins.senate.gov newsroom | source upgrade Wikipedia→navy.mil |
| DDG 129 Jeremiah Denton | Launch | Mar 2025 (Projected) | **Mar 25 2025** (Actual launch; christened Jun 28 2025) | hii.com `/news/hii-christens-guided-missile-destroyer-jeremiah-denton-ddg-129`; en.wikipedia.org `/wiki/USS_Jeremiah_Denton` | **Launch Projected→Actual** (row stays Projected; delivery Aug 2027 future) |
| DDG 131 George M. Neal | Launch | Apr 2026 (Projected) | **Apr 1 2026** (Actual launch) | hii.com `/news/hiis-ingalls-shipbuilding-launches-guided-missile-destroyer-george-m-neal-ddg-131`; navalnews.com `/2026/04/hii-launches-flight-iii-destroyer-george-m-neal-ddg-131/` | **Launch Projected→Actual** (row stays Projected; delivery Nov 2028 future) |
| DDG 126 Louis H. Wilson Jr. | Launch | Sep 2025 (Projected) | **Sep 27 2025** (Actual, christened/floated at BIW) | navy.mil `…/Article/4315850/`; gdbiw.com `/press-media/…-christens-future-uss-louis-h-wilson-jr/` | **Launch Projected→Actual** (row stays Projected; delivery still future) |

**Keel-laying actuals found (evidence-only; NOT one of the three schema columns Start Fab / Launch / Delivery, so not promotable into the calendar and they do not affect narrowing):** DDG 130 keel Aug 29 2024 (navy.mil 3890997); DDG 132 keel May 20 2025 (navy.mil 4190031 / navsea 4193360); DDG 133 keel authenticated Nov 22 2024 (navsea 3976349 + HII); DDG 135 keel authenticated Oct 23 2025 (HII / globenewswire 2025-10-23). These confirm early construction, pre-launch.

### P2-2 — C/D timing narrowing (essentially nothing left to harvest)

Dollar concentration in 4+ candidate rows totals **$1.206B**, of which **$850.1M** is the HII FY18-22 7-hull family (`N0002418C2307`), **$297.6M** the HII FY13-17 5-hull family (`N0002413C2307`), **$52.3M** GD-BIW FY18-22 (`N0002418C2305`), **$5.9M** GD-BIW FY13-17 (`N0002413C2305`).

- **HII FY18-22 ($850M) — already at the timing ceiling.** DDG 128's Dec 29 2025 delivery is already reflected: the 5 rows dated after it (Report IDs 29993703 / 30017851 / 30017845 / 29863208 / 30017835, Jan–Mar 2026, $604K) already show 6-hull sets with **128 correctly dropped**. No further set reduction without single-hull evidence the data doesn't contain. Do **not** collapse.
- **Stage-precision refinement (not count), 74 rows / $21.7M:** post-launch subawards on DDG 129 (after Mar 25 2025) and DDG 131 (after Apr 1 2026) sit in those hulls' outfit/test windows. The master already carries the launch dates so the rollup already tags them Outfit; the web confirmation lets `Schedule Confidence` / `Date Source Confidence` move Projected→Actual, firming the stage-consensus columns. Sharpens *stage*, not the candidate set.
- **GD-BIW FY13-17 ($5.9M, 81 rows):** timing already drops DDG 118 (delivered Mar 2021) on most rows, narrowing 5→4 (e.g. Report IDs 20699721 / 20699716 / 20699723 → set 122/124/126/127). Remaining 4-hull sets are dated ≤ May 2024 (before DDG 122's Jul 2024 delivery) — all four physically in build, honest set, do not collapse.

### P2-3 — Guardrail finding: do NOT narrow on `Prime Requirement Hull Text`

707 of the 4+ timing rows carry a single-hull `Prime Requirement Hull Text` (e.g. 20700075="DDG 117", 20701725="DDG 119" $5.20M, 20701724="DDG 125" $3.74M). It is tempting as a narrowing key but is **demonstrably unreliable** — it names out-of-family hulls (Report IDs 21030313 and 21030184 carry "DDG 125" while sitting in the `N0002418C2307` family where DDG 125 isn't even a candidate). This is exactly why upstream `_hull_logic` kept these C/D. **Flag as a known false-precision trap; do not use to collapse C/D sets.**

### P2-4 — Investigated, cannot confirm (blanks are correct, not gaps)
- **DDG 130 delivery** — Aug 2024 keel release said "delivery in 2026," conflicting with the master's Nov 2028 and BIW's ~3-yr Flight-III span; ship has not delivered. Leave Nov 2028 Projected; "2026" looks like a since-slipped early plan.
- **DDG 132/133/134/135/136 launches** — confirmed **still pre-launch** ("under construction"/"in fabrication" in the Dec 2025 Ted Stevens and Nov 2025 Barnum releases). Blank Launch fields are **correct**.
- **DDG 133 "start fabrication Dec 1 2025" web snippet** — contradicts its own Nov 22 2024 keel authentication; treated as garbled, not used. Master's Start Fab = Dec 2022 (Inferred) retained.
- **DDG 137/139 (HII) and 138 (BIW)** — still pre-planning, no events to source. Projected dates stand.
- **DDG 150** — still "Needs validation," builder TBD, no milestones.

### P2-5 — MIRS (S&P Global / IHS Sea-web) cross-check & provenance upgrade

A new external source arrived this round: **`MIRS_US Built_Destroyers.xlsx`** — an S&P Global / IHS *Sea-web* registry extract generated **2026-06-30**, carrying order / keel / launch / delivery / est-completion at **monthly** granularity for every US-built destroyer. It is **keyed by ship name + IMO number — no hull (DDG-XXX) numbers — and has no supplier / PIID / SWBS content**, so its value is **confined to this lifecycle section**; it does nothing for P1 attribution, P3, or P4.

Joined to `ddg_hull_master.csv` via a name↔hull crosswalk built from our own wiki URLs (DDG 113-136) plus Wikipedia's `List_of_Arleigh_Burke-class_destroyers` (137-149), then triangulated — **MIRS builder, Wikipedia builder, and our `ddg_piid_hull_map` builder split all agree across 137-149.** Staged artifact: **`data/research_worklists/ddg_hull_name_mirs_crosswalk.csv`** (35 hulls; 34 matched to MIRS; builders **34/34** agree; launches **13/14** month-exact).

**QA result — corroborates the model.** Every comparable launch date matches MIRS to the month (12 of 13), and where our master is blank on launch (130/132/133/134/135/136) **MIRS is also blank** ("Keel Laid"/"On Order") — independently confirming P2-4 that *those blanks are correct, not gaps*.

**Provenance-upgrade opportunity (the main promotable here).** ~20 milestone rows are currently cited to **Wikipedia** in `Milestone Source URL`; MIRS lets them be re-cited to one authoritative, IMO-numbered commercial registry. Serves backlog P2.1 ("keep milestone source URLs current"). Model-neutral (dates already agree) — a pure credibility upgrade.

**Concrete corrections surfaced:**

| Hull | Field | Issue | Action |
|---|---|---|---|
| DDG 134 Kilmer | Start Fab | master = Nov 2023 (Inferred); MIRS "On Order/Not Commenced", **no keel** as of Jun 2026 | date too early — blank or push out |
| DDG 136 Lugar | Start Fab | master = Apr 2024 (Inferred); MIRS "On Order", **no keel** | date too early — blank or push out |
| DDG 127 Gallagher | Launch | master **Oct 2024** vs MIRS **Jul 2024** | reconcile (3-mo gap) |
| DDG 126 Wilson | Launch | master **Sep 2025**; MIRS still "Keel Laid", **no float-off launch** | master's Sep 2025 is the *christening*; BIW launch (float-off) ≠ christening — relabel |

**"Start Fabrication" is semantically mixed.** For older hulls (113-125) it equals MIRS keel exactly (9/9 of the in-service set), but for recent hulls it sits 2-3 years *before* keel (DDG 126: ours Mar 2020 vs keel May 2023). MIRS supplies a uniform **keel** series — worth adding as its own column rather than overwriting Start Fab.

**Delivery is NOT a clean drop-in.** MIRS "Delivery Date" tracks **Navy delivery** for recent hulls (118/122/123/124/125/128 match ours) but **commissioning** for older ones (113/114/117/119 run 3-7 months later). Reconcile per-hull; do not bulk-overwrite our acceptance-date column.

**DDG 150 correction (feeds back to [P1-1](#p1-1--promotable-add-ddg-150-to-the-hii-fy23-27-family)).** Wikipedia shows the FY23-27 MYP as exactly **10 ships = DDG 140-149**, and **DDG 150 unnamed/unassigned (next block, FY28+)**. This **revises P1-1**: the Espey "DDG 150" subaward is most likely **long-lead for a future hull**, so 150 should **not** be added to the FY23-27 family and the Espey transaction should stay **X** (not exact B). Defensible residue: a Low-confidence `hull_master` note that DDG 150 is a future **HII** hull.

**Scope limits / caveats:** monthly granularity only (coarser than the day-level dates in P2-1); MIRS misspells "Peters**o**n" (DDG 121); Zumwalt-class, Taiwan Kidd-class, and Flight I/II Burkes (DDG 51-112) appear in the file but are outside our FY11+ corpus.

---

## Priority 3 — SWBS mapping coverage (HII only)

**Headline:** of the **$264.8M** in the unmapped **U00** bucket (230 of 365 codes in `hii_ddg_code_dictionary.csv` are unmapped vs the 135 in `ddg_hii_swbs_crosswalk.csv`), **~$84.8M is promotable now on observed component-text evidence**, rising to **~$99.0M** with same-base curated inferences. The 22 `swbs_curated_c.csv` rows are **already fully absorbed** into the crosswalk (zero new promotions there).

Scope: the upstream `hii_ddg_record_components.csv` is already filtered to HII-Ingalls (421 GD-BIW rows dropped at source), so no BIW mappings are possible or proposed. Dollar figures are `total_usd` from `hii_ddg_code_dictionary.csv`; target subsystem names validated against `swbs_hierarchy.csv` (`NNN`→`NNN00` nomenclature).

### P3-1 — PROMOTABLE (observed evidence) — 46 codes, ~$84.8M → `ddg_hii_swbs_crosswalk.csv`

The component text itself names the part, and the mapping follows the crosswalk's own established convention (valves→505, pumps→503, gauges/indicators→504). Top 25 by $:

| HII Code | total_usd | → SWBS | Evidence (`hii_ddg_record_components.csv` component text) |
|---|---:|---|---|
| 07012-01 | $13,180,521 | **505** General piping | "VALVE, BUTTERFLY" |
| 09137-01 | $7,415,962 | **631** Painting | "HIGH SOLIDS PAINT" / "COATING APPLICATION" |
| 03106-01 | $7,153,156 | **504** Instruments & instrument boards | "GAUGES, PRESS" / "GAGES PRESSURE" |
| 03078-01 | $6,131,517 | **505** | "CONTROL VALVE" |
| 07003-01 | $3,613,922 | **505** | "VALVE, GLOBE QK CLOSE" |
| 07000-01 | $3,432,485 | **505** | "VALVE, GATE" |
| 07056-01 | $3,070,559 | **505** | "VALVE, GLOBE" |
| 02004-02 | $2,931,863 | **505** | "VALVE, SOLENOID" (sibling 02004-01 already→505) |
| 03217-01 | $2,839,457 | **505** | "VALVE, CONTROL" |
| 07057-01 | $2,477,090 | **505** | "VALVE, GLOBE" |
| 07022-01 | $2,403,144 | **505** | "VALVE, SWING CHECK" |
| 07094-01 | $2,314,787 | **505** | "STRAINER" / "STRAINER WYE" |
| 07009-01 | $2,126,115 | **505** | "VALVE, RELIEF" |
| 07014-02 | $1,910,454 | **505** | "VALVES" |
| 07014-01 | $1,897,405 | **505** | "VALVE, PLUG" |
| 07000-02 | $1,887,990 | **505** | "VALVE, GLOBE" |
| 07058-01 | $1,875,394 | **505** | "VALVE, GLOBE" |
| 04022-01 | $1,663,860 | **314** Power conversion equipment | "400Hz TRANSFORMERS" (sibling 04022-02 already→314) |
| 07094-02 | $1,584,048 | **505** | "STRAINER" |
| 07075-01 | $1,511,861 | **505** | "VALVE, BALL" |
| 07008-01 | $1,464,750 | **505** | "VALVE, CONTROL" |
| 05013-01 | $1,289,225 | **561** Steering & diving control | "RUDDER BEARINGS" |
| 07000-03 | $1,159,145 | **505** | "VALVE, SWING" |
| 04041-01 | $1,130,352 | **504** Instruments & instrument boards | "INDICATOR" |
| 05006-01 | $1,053,890 | **561** Steering & diving control | "RUDDER BEARING SLEEVE / RUDDER SLEEVES" |

Plus 21 smaller codes (each <$1M), all valves/strainers/traps/connectors→**505**, rudder parts→**561**, pump→**503**, refrigeration→**516**: 07005-01, 07065-01, 07021-01, 07002-01, **07042-01 ($606,138)→561** "SEAL ASSY, RUDDER STK", 03215-01, 03137-01, **05007-01 ($474,779)→561** "RUDDER HUB CASTINGS", 02533-01, 07006-01, **07338-01 ($300,102)→503** Pumps "PUMP, ROTARY VANE", 07105-01, **07095-01→505** "TRAP, CONDENSATE", 02021-01, 07053-01, **07085-01→505** "CONNECTOR, FLEXIBLE", 07067-01, 07154-01, 07079-01, 07273-01, **02000-02 ($47,913)→516** "REFRIGERATION COOLERS".

The dominant win is the **07xxx/03xxx valve, strainer, trap and flex-connector family → SWBS 505**, consistent with the four valve codes already mapped to 505 in the crosswalk (02004-01, 03031-01, 03072-01, 03202-02).

### P3-2 — PROMOTABLE (curated inference) — 9 codes, ~$14.2M

No own component text, but a same-base sibling is already mapped, or the word reasons cleanly to one system.

| HII Code | total_usd | → SWBS | Rationale |
|---|---:|---|---|
| 07012-02 | $4,285,920 | **505** General piping | same base 07012 ("VALVE, BUTTERFLY") |
| 01006-01 | $2,451,829 | **572** Ship stores & equipment handling | "PACKAGE CONVEYOR". **572 is not yet a subsystem row in `ddg_swbs_by_subsystem.csv` — would be a new row.** |
| 03202-01 | $2,235,814 | **505** | same base 03202 (03202-02 already→505) |
| 01019-01 | $1,790,916 | **583** Boats, boat handling & stowage | "LIFE RAFTS" |
| 01039-05 | $1,042,757 | **651** Commissary spaces | same base 01039 (01039-01/-02/-03 all→651, "COMMISSARY EQUIPMENT") |
| 07012-03 | $858,496 | **505** | same base 07012 (butterfly valve) |
| 07046-01 | $735,967 | **529** Drainage & ballasting | "EDUCTOR" (bilge/drainage) |
| 07214-01 | $500,188 | **521** Firemain & flushing (sea water) | "NOZZLE, FIRE HOSE" |
| 07317-01 | $288,375 | **512** Ventilation system | "FILTER, CARBON AIR" / "FILTER, AIR" |

Two further same-base parallels are tiny **REBUY/rework credit lines** — flagged, **not** recommended: 04016-91 ($34,860, base→633), 03174-91 ($28,908, base→555).

### P3-3 — Promotable long-tail (curated, needs individual judgement) — 39 codes, ~$20.0M
Has component text but no single auto-mappable answer. Highest: 05007-02 $2.29M "LEAD & TRAIL CASTINGS" (rudder/appendage, likely 561), 01040-02 $1.89M "WINDOW, FXD TILTED" (→624?), 05003-01 $1.57M "BOLSTER CASTINGS", 05049-02 $1.34M "DOORS, CIWS EQUIP" (→624/167?), 04100-01 $1.18M "AESS" (→320s), 05000-01 $0.70M "STEM BAR CASTING" (hull→16x), plus lockers/laundry/ladders/hose-reels. Not forced without a defensible single target.

### P3-4 — Investigated, cannot map (stay U00) — 140 codes, ~$154.3M
No component text at all — only the bare work-item code (± hull number). Top offenders:

| HII Code | total_usd | pattern |
|---|---:|---|
| 01056-01 | $26,564,653 | code only — **single largest U00, unmappable** |
| 08253-01 | $7,818,609 | code only |
| 07047-01 | $6,013,777 | code only (07xxx family) |
| 08254-01 | $4,842,703 | code only |
| 05149-01 | $4,659,597 | code only |
| 07020-01 | $4,658,346 | code only (07xxx family) |
| 01061-01 | $4,544,755 | code only |
| 07016-01 | $4,391,741 | code only (07xxx family) |
| 05246-01 | $4,334,658 | code only |
| 01040-01 | $3,359,980 | code only |

**Family-pattern note (option, NOT recommended under "promote only with evidence"):** 38 no-text codes are in the 07xxx valve/piping family totalling **$41.42M** (07047-01, 07020-01, 07016-01, 07055-01, 07018-01, 07011-01, 07027-01, 07280-01, …). Every 07xxx code that *does* carry text resolves to a valve/strainer→505 (only 3 exceptions: 07042→561, 07338→503, 07214→521), so 505 is a plausible family-prefix target — but with no per-code text it is withheld. Single biggest reclaimable block *if* the team ever accepts family-prefix inference.

### P3-5 — $ recoverable summary

| Tier | Codes | $ reclassified | Cumulative |
|---|---:|---:|---:|
| Observed evidence (high confidence) | 46 | $84.77M | $84.8M |
| + curated same-base / clean reasoning | +9 | +$14.19M | **$99.0M** |
| + curated long-tail (individual assignment) | +39 | +$19.96M | $118.9M |
| *(optional)* 07xxx no-text by family pattern | +38 | +$41.42M | $160.3M |
| Truly unmappable (no evidence) | ~96 | — | ~$104.4M stays U00 |

All proposed targets (505, 504, 503, 314, 561, 631, 516, 521, 529, 512, 583, 651) already exist as subsystem rows in `ddg_swbs_by_subsystem.csv`; only **572** (for 01006-01) would be a new row.

---

## Priority 4 — Supplier classification coverage

### P4-0 — Scope correction (important)
`classification/ddg_vendor_archetype_overrides.csv` = **101 DDG rows** (746 physical lines; embedded newlines in note fields inflate the line count). Its 101 DDG rows are **identical** to the 101 DDG rows in the upstream `extracted/vendor_archetype_overrides.csv` (which is 292 data rows: 101 DDG / 101 Virginia / 90 Columbia) — **zero drift, nothing to back-fill from the overrides file.** `supplier/ddg_supplier_master.csv` = **399 DDG suppliers** (96 with override, **303 NO-OVERRIDE** riding the NAICS-6 fallback). `supplier/ddg_supplier_year_activity.csv` carries **no dollar values** (computed inside the workbook); the authoritative dollar source is `corpus/extracted/coverage_unclassified_top.csv`.

The recoverable gap is therefore **not** in the overrides file (in sync) — it is (a) deliberate P0 placeholders inside the 101 overrides, (b) the 303 NO-OVERRIDE suppliers whose NAICS fallback resolves to D0/P0, and (c) **curated `vendor_evidence_registry` buckets never propagated into the override file.**

### P4-1 — Gap summary
- **Inside the 101 override rows:** D0 rows = 6, P0 rows = 14, empty-P = 2 → **19 distinct D0/P0 rows.** Most P0s are *deliberate* (confident D, but "no public source ties a specific delivered DDG item") — the output level P is usually recoverable from product nature even where the specific part isn't.
- **NO-OVERRIDE suppliers:** of 303, **145** fall to NAICS-fallback D0/P0 or have no NAICS. Driving codes: `423830`/`423840`/`423860` (merchant wholesalers), `339999`, `336413`, `336611` (Unresolved), and blanks.
- **Dollar exposure** (DDG `coverage_unclassified_top.csv`, 282 distinct UEIs, $43.55M FY22-25 / $242.1M all-time flagged), split by *actual workbook* status:

| Workbook status | nUEI | $M FY22-25 | $M all-time |
|---|---:|---:|---:|
| override-OK (stale upstream flag) | 14 | 10.22 | 89.45 |
| NO-OVR, NAICS fallback = real D/P (soft-covered) | 95 | 18.59 | 66.99 |
| **NO-OVR, NAICS fallback = D0/P0 (true gap)** | **116** | **9.86** | **37.54** |
| not in supplier_master (out of scope) | 52 | 4.22 | 24.16 |
| **override = D0/P0** | **5** | **0.65** | **23.96** |
| **Effective actionable D0/P0** | | **≈14.7** | **≈85.7** |

Top unclassified DDG vendors by $ FY22-25: MMC Metrology $3.61M, NAG LLC $2.45M, Hitachi $2.20M, U.S. Pioneer $1.26M, Quality Performance $1.21M, TCH Distributors $1.11M, Milwaukee Composites $0.97M, Cameron Energy $0.82M, ONEX/RFD Beaufort $0.74M, Mississippi Security Police $0.73M, ABC Applicators $0.71M, Critical Communications $0.62M.

D/P vocabulary (from `ddg_naics6_archetype_map.csv`): D1 structural, D2 propulsion/mechanical drive, D3 electrical power, D4 fluid/piping, D5 HVAC, D6 mission/comms, D7 instruments/electronic, D8 auxiliary craft, D9 material process, D11 services; P1 raw stock, P2 finished component, P3 bounded functional equipment, P5 integrated structural module, P6 services.

### P4-2 — PROMOTABLE now (~25, highest $ first) → `ddg_vendor_archetype_overrides.csv`

| UEI | Vendor | $M 22-25 / all | D | P | Evidence (source file · field) | Conf |
|---|---|---|---|---|---|---|
| JU2ME5ZK8VL3 | MMC Metrology Lab | 3.61 / 6.22 | D7 | P3 | `unique_uei_sam_enrichment` naics6=334513 + psc 6685 (pressure/temp/humidity instr); name "Metrology Lab"; calibration NAICS 811210/811310 | Med |
| F3XKPA82MHQ5 | NAG, LLC | 2.45 / 4.42 | D7 | P3 | sam naics6=334513, psc 6680;6685;7B22 (liquid-level+instr), org=Manufacturer | Med |
| QEP4TKLKQDV3 | U.S. Pioneer LLC | 1.26 / 2.82 | D7 | P2 | sam naics6=334419, psc 5935(connectors);5975;5999;6150, org=Manufacturer | Med |
| D9T3VK42BLV7 | Milwaukee Composites | 0.97 / 0.97 | D1 | P2 | sam naics6=326130, psc 9330; FRP composite deck/panel maker (upgrades NAICS default D9/P1) | Med |
| C1NAJQ34VWM5 | Cameron Energy Services | 0.82 / 0.82 | D7 | P3 | sam naics6=334513, psc 6680 (liquid-level instr), org=Manufacturer | Med |
| V32LJNFLKBT7 | ONEX Corp / RFD Beaufort | 0.74 / 0.74 | D8 | P3 | `coverage_unclassified_top` alt-name "RFD BEAUFORT" + `supplier_master` Parent=Survitec → marine liferafts/survival craft | Med |
| KB45YQR3KSL5 | Mississippi Security Police | 0.73 / 1.48 | D11 | P6 | `supplier_master` naics6=561612 (Security Guards), psc R430;S201;S206 — service, not material | High |
| KK9FFUUML8N1 | ABC Applicators Inc | 0.71 / 0.71 | D9 | P6 | `supplier_master` naics6=238320 (Painting Contractors) → coatings/painting service | Med |
| DH7CZ5SHWTN7 | Critical Communications, Controls & Instruments | 0.62 / 0.62 | D6 | P3 | sam naics6=334511 (Search/Detection/Nav/Guidance); all_naics6 334290/334511/336611 | Med |
| C4C1WKKFJ8H5 | Energy Rental Solutions | 0.47 / 0.59 | D11 | P6 | `supplier_master` naics6=532490 (Machinery Rental) — equipment-rental service | Med |
| LN9YKAX66918 | Kulite Semiconductor | 0.44 / 0.82 | D7 | P3 | **fixes a D0/P0 fallback**: naics6=336413→D0/P0 artifact; firm = pressure-transducer/sensor maker | Med |
| KN2BBGWNLKJ8 | Asco Power Technologies | 0.41 / 0.41 | D3 | P3 | sam naics6=335313 (Switchgear); automatic transfer switches / power control | Med |
| J2DMF1YRKD96 | Standard Calibrations Inc | 0.40 / 0.40 | D11 | P6 | `supplier_master` naics6=811210 (Precision Equip Repair/Calibration) — service | Med |
| YULJLSW1N2G4 | Cygnus LLC | 0.39 / 0.39 | D7 | P2 | sam naics6=334418 (PCB Assembly), psc 5963;5975;5998 | Med |
| TKE2CB4A5YW4 | Honeywell International | 0.33 / 0.33 | D7 | P3 | sam naics6=334519 (Other Measuring/Controlling Device) | Med |
| HYGLK2BNFKB3 | Rolls-Royce Holdings | 0 / 15.82 | D2 | **P3** (was P0) | override Dnote "diesel-engine prime movers"; prime mover = bounded functional equipment | Med |
| ZLM5NQE8LSR8 | IMECO (J.F. Lehman) | 0.06 / 6.83 | **D5** (was D0) | P3 | `supplier_master` role = marine HVAC/electrical/machinery integrator; naics6=333415; HVAC-dominant | Med |
| MD21J51WM123 | Tyco Fire Products LP | 0 / 0 | D4 | **P3** (was P0) | sibling UEI H1PAVTLJBJ88 (same JCI/Tyco fire-suppression) already D4/P3 — match sibling | Med |
| J3AFGKXWYK73 | York Intl / JCI | 0 / 0 | D5 | **P3** (was P0) | `vendor_evidence_registry` bucket=hvac conf=med; naics6=333415; HVAC/refrigeration | Med |
| TSCZLHCGNQ53 | Facet (Oklahoma) | 0 / 0 | D4 | **P3** (was P0) | `vendor_class_matrix` work_type=piping; fuel-filtration/coalescer equipment | Med |
| F42BKS7EHCL8 | EMS Development / Ultra | 0 / 0 | D3 | **P2** (was P0) | naics6=334416 (Capacitor/Transformer); transformers/power supplies | Med |
| EVZMB1757DW5 | SteelFab Inc | 0 / 0 | D1 | **P2** (was P0) | `vendor_class_matrix` work_type=structural; naics6=332312 (Fab Structural Metal) | Med |
| C12YPM9YKQA5 | GE / Panametrics | 0.04 / 0.04 | D7 | **P3** (was P0) | override Dnote "flowmeters, dew-point indicators, gas analyzers" = measurement equipment | Med |
| FRJQGQHDX4J3 | L3 / Comm Systems-West | 0 / 0 | D6 | **P3** (was P0) | naics6=334220; secure tactical comms electronics | Med |
| T2VFE1NGR3G5 | DRS Training & Control / Leonardo | 0 / 0 | D6 | **P3** (was P0) | `vendor_evidence_registry` role=mission_systems conf=med; naics6=334220. **NOTE** registry flag "VLS launch-control boundary (sensitivity-in only)" — confirm whether P0 was an intentional sensitivity hold | Med |

### P4-3 — Cleanest promotions: curated upstream, never propagated to the workbook
Strongest provenance — a confident bucket in `supplier_bucketing/vendor_evidence_registry.csv` (and/or `corpus/extracted/registry_additions_worksheet.csv`), in DDG `supplier_master` scope, yet D0/P0 or NO-OVERRIDE in the workbook. (`registry$M` = `ddg_signed_$M`, a program-signed figure, larger than subaward-line dollars.)

| UEI | Vendor | Registry bucket (conf) | Workbook now | Proposed D/P | Anchor |
|---|---|---|---|---|---|
| J3AFGKXWYK73 | Johnson Controls / York | hvac (med) | override D5/**P0** | D5/**P3** | registry bucket=hvac; naics 333415→P3 |
| N1PJDANWUJ61 | Scot Forge Company | castings (high) | override D2/(empty P) | D2/**P1** | registry castings/forgings high; naics 332111 (Iron/Steel Forging)→P1 |
| CBMZJ3Z5SC89 | Goodrich / Collins EPP | coatings (med) | override D1/(empty P) | D1/**P2** | registry+additions coatings; Engineered Polymer Products (acoustic/coating) |
| S3GFGJ1QGAE6 | M.S.M. Industries | coatings (high) | NO-OVR | **D9/P2** | registry coatings high; naics 326291 (Rubber Product, Mechanical Use) |
| NYGUEDY27AM8 | Curtiss-Wright Flow Control | piping (high) | NO-OVR | **D4/P3** | registry piping high; naics 332911 (Industrial Valve) |
| GV6WMAJUK1R9 | Sioux Manufacturing | structural (high) | NO-OVR | **D1** (P3/P2) | registry structural high; no SAM NAICS → name/registry basis |
| MSYWUDGYPKF5 | Everest Kanto Cylinder | structural (high) | NO-OVR | **D4/P3** | registry; naics 332420 (Metal Tank, heavy gauge); high-pressure gas cylinders (alt D1) |
| HUYTR5ZGSSN6 / LGVPVLMRHH51 | W. & O. Supply | piping (high) | NO-OVR | **D4/P3** | registry piping high; marine pipe/valve/fittings distributor (one variant naics 423840→D0/P0) |
| RLXQHCXFT513 | Citadel Capital (pipe-fab portfolio) | piping (high) | NO-OVR | **D4/P2** | registry; naics 332996 (Fab Pipe/Fitting) |
| DJG7NEG7QRK5 | Arcline Investment (valve portfolio) | piping (high) | NO-OVR | **D4/P3** | registry; naics 332911 (Industrial Valve) |
| WVW5FMYALEL6 | Plainville Electrical Products | electrical (high) | NO-OVR | **D3/P3** | registry; naics 335313 (Switchgear) |
| NTREK31GP8N3 | Ksaria Corporation | electrical (high) | NO-OVR | **D7/P2** | registry+additions; naics 334417 (Electronic Connector); fiber-optic interconnect |
| FWF8QBPCGLG3 | General Tool Company | machining (med) | NO-OVR | **D9/P2** | registry+additions; naics 336419 |

### P4-4 — Investigated, weak evidence (NAICS-default only / unresolvable — low confidence)
- **VXJMLWN9XU18 Hitachi, Ltd** ($2.20M/$4.40M) — no SAM record, no NAICS, conglomerate; cannot resolve a single ship domain. **Leave D0**; needs raw-award drill-in (n=25).
- **NBM4G4SAFQM3 Quality Performance Inc** ($1.21M, parent Valkyrie) — **conflicting axes**: naics 334419→D7/P2 but psc service-dominant (H163;H166;H263;J063;K063;L063;N063;W063). Lean **D11/P6** (services).
- **FUNJJEK23XN5 TCH Distributors** ($1.11M) — naics 423840 merchant wholesaler→D0/P0; pass-through distributor. Tentative D0 (or D11/P6).
- **F98TZC6J5XV1 Hexcel Corp** ($0.45M) — naics 334515→D7/P3 but firm is advanced composites (carbon fiber/honeycomb) → real archetype likely **D9/P1**; NAICS looks like a registration artifact. Do not auto-accept.
- **TMDVSPNEFR69 Ives Equipment** ($0.36M) — naics 423840→D0/P0; process-instrumentation/valve distributor → tentative **D4/P3** (distributor).
- **ED16VKVTCHC8 ECI Defense Group** ($0.30M) — naics 423860→D0/P0; all_naics6 incl 332911(valves)/333914(pumps) → tentative **D4**.
- **VWX3JEES4FF7 Triman Industries** ($0.34M) — naics 423710→D10/P0; textile/rubber/metal spread.
- **DV6YQV71ME11 Mar-Vac Products**, **HNJDANSKDZK9 Spectronics**, **XNR9ZJ9VKZG5 Temeku Technologies** — no NAICS; tentative D7 / D7-or-D9 / D11 respectively; need raw drill-in.
- **HNAECT5M9TM4 SOCAIL, Lda** (override D0/P0) — role notes "industrial-piping/plumbing" → weak **D4** lean; analyst kept D0.

### P4-5 — Correctly D0/P0, do NOT promote (evidence affirmatively excludes a ship domain)
- **FG7CGCHSNML9 L-3 Communications** — security-screening line, no DDG nexus.
- **K574V7KEQUC8 CIRCOR Aerospace** — Corona CA aerospace op, explicitly *not* the naval-valve business.
- **LCZDJ6YPNYG6 Martin Energy Services** (D0/P1) — construction/sea-trial **fuel** consumable.
- **QV38GMJUBJQ3 L3Harris Maritime** (D0/P6) — multi-trade shipyard installation labor; D0 defensible (D11/P6 arguably cleaner).

---

## Cross-cutting finding (UPDATED 2026-06-30 — the "gap" was an artifact, now DISPROVEN)

**Original hypothesis:** `supplier_bucketing/vendor_evidence_registry.csv` lists very large "DDG-signed" vendors absent from the workbook's 399-row `ddg_supplier_master.csv` — Major Tool & Machine **$986.9M**, etc. (~$1.4B total) — looking like a supplier-coverage gap "bigger than classification."

**Verification (SAM Contract Awards API by UEI, per `Federal_Awards_API_HowTo.md` recipe A; raw + summary in [`data/research_worklists/ddg_large_vendor_attribution_check.csv`](../data/research_worklists/ddg_large_vendor_attribution_check.csv)):** the gap is **not real.** For **all seven** vendors, **NAVSEA-shipbuilding (contracting office N00024) obligation = $0.00M**, and a shipbuilding-NAICS filter (336611/336612, counted over each vendor's *full* footprint) returns **zero awards for 5 of 7** (2 incidental, non-N00024 records for Major Tool and M.S.M.).

| UEI | Vendor (correct name) | reg ddg_signed_$M | actual primary customer | NAVSEA N00024 $M |
|---|---|---:|---|---:|
| YHJESY2TDP23 | Major Tool & Machine | 986.9 | **Air Force** (AFLCMC) | **0.00** |
| E582KXT4RVH6 | Superior Electromechanical | 146.3 | Navy warfare centers (NSWC) | **0.00** |
| ZRS3MA6VK271 | Merrill Technologies | 93.1 | NSWC Crane/Dahlgren | **0.00** |
| GU4MZLMEJN94 | Seyer Industries | 63.1 | NAVAIR (aviation) | **0.00** |
| M1LQD44NEJ56 | Applied Composite Structures *(P4 agent mislabeled this UEI "AC&A Enterprises")* | 50.2 | DLA / aviation | **0.00** |
| L2WVLS5L4WS3 | Futuramic Tool & Eng | 41.8 | Army TACOM | **0.00** |
| S3GFGJ1QGAE6 | M.S.M. Industries | 41.8 | DLA Troop Support | **0.00** |

**Why the registry was wrong:** `ddg_signed_$M` was produced by a NAICS "tail pass" (332710 machine shops, 326291 rubber, 336413 aircraft parts) that (a) swept in vendors whose real customers are Air Force / Army / DLA / NAVAIR — **not** NAVSEA shipbuilding — and (b) summed the **ceiling** field (`totalBaseAndAllOptionsValue`), not realized obligation. Major Tool's ceiling sum over just its top-100 records is **$50.7 billion** (shared IDIQ ceilings; see how-to §7), so $986.9M is a ceiling-derived phantom — its actual realized obligation is ~$110M, 98% **Air Force**.

**Consequences:** (1) **Do not ingest these into `supplier_master` as DDG suppliers** — there is no DDG spend to add. (2) Treat the registry's `ddg_signed_$M` column as **unreliable for sizing** generally, especially "tail pass" rows. The registry's *classification buckets* (machining/coatings/piping) for vendors that **are** in-corpus remain usable for D/P archetype work (P4-3); only the dollar figures and the absent-vendor "coverage gap" are discredited.

---

## Promotion summary (APPLIED 2026-06-30 — branch `promote-sam-findings-round1`)

**Status: promoted into the workbook_factory build and QA-verified (37 sheets, 0 recalc error cells, all reconciliation checks OK).**

Key implementation note that changed the mechanics vs. the HANDOFF: the `workbook_factory` computes SWBS **live** (the `ddg_swbs_by_subsystem.csv` dollar cells are empty and filled by build-time `SUMIFS`; the transaction `SWBS Subsystem` cells are filled by `INDEX/MATCH` over the crosswalk keyed on the already-materialized `HII Work-Item Code`). So promotion required **no upstream regeneration or cross-repo resync** — editing the crosswalk leaf CSV + rebuilding propagated the reclassification. Applied outcomes:

- **P3 SWBS** — 55 codes appended (46 observed `X`, 9 curated `C`) + new subsystem-572 spine row. Live rollup **U00 $518.88M → $431.56M (−$87.3M constant-FY2026$)**; SWBS 505 $29.8M→$93.6M, 504 +$8.3M, 631 +$7.0M, 561 +$2.4M, etc.; HII rollup total conserved at $3,110.94M. (Constant-$ FY16-25 window, so magnitude differs from the nominal all-time $84.8M–$99.0M dictionary figure; 3 codes — 07154-01, 02000-02, 01006-01 — are zero-movers whose transactions fall outside the FY window, so subsystem 572 currently shows $0.)
- **P4 supplier** — strong set of **23** applied (12 in-place D/P updates + 11 new rows); medium NAICS-only rows deferred per scope. Codes validated by `assert_archetype_codes_valid`; domain concentration repopulated. `T2VFE1NGR3G5` filled D6/P3 with a sensitivity caveat noted (revert to P0 if the VLS launch-control hold was intentional).
- **P2 hull** — 6 primary-source re-cites, 4 corrections (134/136 Start Fab blanked; 127 launch Oct 2024→Jul 2024; 126 launch blanked as christening≠launch), 9 MIRS re-cites (in-service hulls); MIRS source file copied to `data/workbook_inputs/reference/`. Display-only + model-neutral (factory lifecycle is frozen/materialized, not recomputed from hull dates).
- **P1 hull** — DDG 150 row: Builder TBD→HII-Ingalls, MYP→FY28+ (future block), Confidence→Inferred. PIID map + Espey exception left untouched (Espey stays X).

| Priority | Promotable items | Magnitude | Confidence | Target file |
|---|---|---|---|---|
| **P3 SWBS** | 46 observed + 9 same-base codes | **$84.8M → $99.0M** out of $264.8M U00 | High / defensible | `swbs/ddg_hii_swbs_crosswalk.csv` (+1 new subsystem row 572 in `ddg_swbs_by_subsystem.csv`) |
| **P4 supplier** | ~13 registry-curated + ~9 P0→P fills (strong); ~12 NAICS+PSC (med) | ≈$14.7M FY22-25 / $85.7M all-time actionable D0/P0 | Strong → medium | `classification/ddg_vendor_archetype_overrides.csv` |
| **P1 hull** | ~~DDG 150 → HII FY23-27 family~~ **REVISED by P2-5**: keep Espey row **X** (long-lead); only note DDG 150 = future HII hull | — | — | `hull/ddg_hull_master.csv` (DDG 150 builder note, Low conf) |
| **P2 lifecycle** | 6 milestone date/provenance updates + MIRS re-cite (~20 rows) + 4 corrections (134/136 Start-Fab too-early, 127/126 launch) | provenance + small fixes; model-neutral | High (web + S&P Global) | `hull/ddg_hull_master.csv`; staged `research_worklists/ddg_hull_name_mirs_crosswalk.csv` |

### Held back (not promoting)
- P1 $4.27M rebuy bucket X→D (methodology change, no exact gain, REBUY/REPAIR ambiguity).
- P3 07xxx valve family by prefix (+$41M, no per-code text — violates evidence-only rule).
- P2 narrowing on `Prime Requirement Hull Text` (proven false-precision trap).
- P4 NAICS-default-only weak vendors (Hitachi, TCH, Triman, etc.).

### Needs external sourcing
- ~~DDG 150 builder (HII vs BIW)~~ — **resolved (P2-5)**: DDG 150 is a future (FY28+) hull, unnamed/unassigned; the FY23-27 MYP is DDG 140-149. The subaward signal points to HII but is long-lead, not a build-hull assignment.
- `N0002423C2305` BIW FY23-27 family — awaits next SAM subaward pull (0 subawards today).
- ~~Supplier-coverage ingestion of the large registry vendors~~ — **closed (2026-06-30)**: SAM-CA verification shows these are not DDG suppliers (N00024 = $0 for all 7); the "$1.4B gap" was a ceiling/NAICS artifact. See Cross-cutting finding + `research_worklists/ddg_large_vendor_attribution_check.csv`.
- Optional: copy `MIRS_US Built_Destroyers.xlsx` into `data/.../reference/` as a cited source before promoting any P2-5 milestone re-cites.

---

## Promotion checklist reminder (from the backlog)
Before promoting any item: (1) what exact workbook field changes; (2) source URL / document evidence; (3) does it improve a grade/mapping/date/classification; (4) does it preserve grain discipline; (5) could it accidentally allocate C/D family-level dollars to a single hull (if yes, do not promote). Every proposal above is annotated against these.
