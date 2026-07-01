# Plan A — Procurement-Timing Refactor

## Outcome
Retire the whole-program lifecycle-staging layer, keep **procurement timing** as the coverage anchor (100% of rows, live formula), and replace the misleading program-wide stage exhibit with a scoped, honest **drill-down on the only two full-span hulls (DDG 125, DDG 128)**. Net tab count 38 → 32.

## What this supersedes
This completes the cut list from our discussion. That sketch missed one sheet: **DDG Hull x Lifecycle Stage is included in the deletions here.** It is the sheet that produces the misleading program-level "87% long-lead" aggregate (driven by not-yet-keeled hulls 143/145/146/149 dumping their whole total into Long-lead), and it reads the `Lifecycle Stage` column we're dropping, so it can't stay. The 2-hull drill-down is its honest replacement.

## Preconditions / assumptions
- Nature tagging (Plan B) is **not** part of this plan; do it after.
- Infra I'm inferring from imports (verify the names locally): `ddg/sheets/kit/tabs.py` (the `TAB_*` constants), the workbook assembly / **SHEETS registry** (the module that collects every `SheetEntry`/sheet object and sets tab order), `scripts/tag_ddg_transactions_lifecycle.py`, `scripts/build_ddg_cd_lifecycle.py`, `scripts/build_ddg_vendor_hull.py`, `validate_workbook.py`, and `scripts/_lifecycle.py` + `_integrity.assert_lifecycle_labels_known`.

---

## 1. Delete these 7 modules + their tabs

| Module | Tab | ~Rows |
|---|---|---|
| `ddg_cd_lifecycle_candidates.py` | DDG C-D Lifecycle Candidates | 17,613 |
| `ddg_cd_lifecycle_rollup.py` | DDG C-D Lifecycle Rollup | 2,835 |
| `ddg_cd_lifecycle_coverage.py` | DDG C-D Lifecycle Coverage | 24 |
| `ddg_archetype_lifecycle.py` | DDG Archetype x Lifecycle | 27 |
| `ddg_vendor_hull_lifecycle.py` | DDG Vendor x Hull Lifecycle | 1,201 |
| `ddg_hull_lifecycle_stage.py` | DDG Hull x Lifecycle Stage | 43 |
| `lifecycle_methodology.py` | Lifecycle Methodology | — |

Remove their constants from `kit/tabs.py`: `TAB_CD_LC_CANDIDATES, TAB_CD_LC_ROLLUP, TAB_CD_LC_COVERAGE, TAB_ARCHETYPE_LIFECYCLE, TAB_VENDOR_HULL_LIFECYCLE, TAB_HULL_LIFECYCLE, TAB_LIFECYCLE_METHOD`. Remove all 7 from the SHEETS registry / tab order.

## 2. Slim the transaction sheet (`ddg_subaward_transactions.py`)
Drop the 5 materialized lifecycle columns (currently BI–BM): `Lifecycle Stage`, `Lifecycle Stage Basis`, `Date Source Confidence`, `Narrowing Result`, `Lifecycle Confidence`.

- **Retire `scripts/tag_ddg_transactions_lifecycle.py` from the CSV build chain** — this is what physically removes the 5 columns from `ddg_subaward_transactions.csv`. Keep the SWBS and hull-regex taggers.
- In the module: delete the 5 width entries in the "construction-lifecycle (CSV …)" block (`W_SUPTYPE, W_TEXT_WIDE, W_SHORT_FLAG, W_CATEGORY, W_CLASS`) and change `assert len(_WIDTHS) == 77` → `== 72`. Trim the lifecycle paragraph from the docstring.
- **No formula edits needed on this sheet.** `flat_header_letters` reads the CSV, so every downstream column (SWBS Match Row, PIID Map Row, Assigned Hull, Procurement Timing, Federal FY …) shifts left by 5 automatically and stays correct — they resolve by name. The bottom `_GUARD_COLS` assert is name-based and still holds.
- **Safety grep before building:** no remaining `ddg_tx_cols("<one of the 5 names>")` anywhere. Step 3 removes the two known callers.

## 3. Fix the sheets that referenced the deleted columns/sheets
If skipped, these throw `#REF!` / `KeyError` and the master check fails.

**`checks.py`** — remove 3 imports (`cd_lc_rollup_cols`, `vendor_hull_lifecycle_cols`, `archetype_lifecycle_cols`), 4 range vars (`_CD_ROLLUP_RID`, `_VHL_TOTAL`, `_AL_AXIS`, `_AL_TOTAL`), and 4 reconciliation checks: *Vendor-hull lifecycle reconciles to A/B*, *Archetype lifecycle D-axis…*, *Archetype lifecycle P-axis…*, *C/D lifecycle rollup row count reconciles to transactions*. The master-check range auto-shrinks. Optional add: a *Full-span drill-down reconciles to A/B $ for DDG 125/128* check.

**`executive_summary.py` §6** — remove `_TX_NARROW`, `_TX_LCONF`, `_sum_narrow`, `_sum_lconf`, `narrowed_raw`, `high_med_raw`, and the two rows *"C/D narrowed to 1-3 candidates"* and *"C/D high/medium lifecycle confidence"*. Keep `cd_raw` and the hull-coverage rows. (Plan B re-fills §6 with a nature row.)

**`market_bridge.py`** — remove `_TX_NARROW`, `_TX_LCONF`, `_narrow_raw`, `_lconf_raw`, `narrowed_raw`, `high_med_raw`, and the two §2 ladder rows *"C/D narrowed"* and *"C/D lifecycle confidence"*. In §3, **keep** the "Family-level C/D" row but edit its "good for" text to drop "lifecycle confidence" (it's a hull-confidence row, still valid).

**`hull_mapping_methodology.py`** — remove the `TAB_LIFECYCLE_METHOD` import and rewrite the §6 *"Lifecycle layer"* row. Use it to **preserve the load-bearing negative**: state that procurement timing covers 100% of rows and is the anchor, and that timing-narrowing was tested on the family-level (C/D) bulk and rarely resolves below 4+ candidate hulls — which is why no per-hull dollar is allocated. This is where the ~20k-row C/D narrowing result now lives, as one sentence.

## 4. Add the drill-down (new module)
New: `ddg_full_span_drilldown.py` → tab e.g. `"DDG 125/128 Full-Span"` (add `TAB_*` constant + register in SHEETS).

**Design — no stage column reintroduced.** Build the stage split as date-window `SUMIFS` directly over the transaction leaf, keyed on `Assigned Hull` + a date band bounded by that hull's own milestones from Hull Master. No per-row stage tag is needed, and the split is inherently scoped to the 2 hulls (this is what avoids re-creating the program-wide-stage trap).

For each hull H ∈ {DDG 125, DDG 128}, pull milestones live:
```
fabH    = INDEX(hull_master_cols("Start Fabrication"), MATCH("DDG 125", hull_master_cols("Hull"), 0))
launchH = INDEX(hull_master_cols("Launch"),           MATCH(..., ...))
delivH  = INDEX(hull_master_cols("Delivery"),         MATCH(..., ...))
```
Then a 2×4 matrix (rows = hulls, cols = stages); each cell a `SUMIFS` over `ddg_tx_cols(TX_REAL)`:
- **Long-lead:** `Assigned Hull = H`, `Subaward Date < fabH`
- **Construction:** `date >= fabH`, `date < launchH`
- **Outfit / test:** `date >= launchH`, `date < delivH`
- **Post-delivery:** `date >= delivH`

Plus `Total = SUMIFS(Assigned Hull = H)` and an **Undated** residual `= SUMIFS(Assigned Hull = H, Date = "")` so bands + undated = Total. Add a short vendor view (top suppliers × stage, same `SUMIFS` pattern with a `Subawardee UEI` criterion) for the "who supplies each stage" narrative.

**Labeling (in-sheet):**
- Intro: *"Illustrative full-span exhibit — the only two hulls (DDG 125, DDG 128) with unclipped AP/LLTM-to-delivery subaward coverage (~$47M, 358 subawards). Not class-representative. Stages referenced to each hull's own Start Fabrication / Launch / Delivery."*
- Caveat: *"Long-lead here = pre-fabrication material for that hull. Clean for 125/128 because they predate the FY18-22 block-outsourcing program (that activity is on 135/137/139)."*

**Reconciliation checkpoint.** The two hull totals should equal the tx Assigned-Hull `SUMIFS` in FY2026$. These differ from the findings-doc per-hull figures, which are *nominal* Subaward Amount $ (125 ≈ $25.7M nominal / ~$27.3M FY2026$). Watch DDG 128: it reads ~$17.6M in the shipped Hull-Lifecycle sheet vs $21.2M nominal in the coverage memo — the deflation direction is backwards there, so verify the 128 row set / attribution during implementation rather than assuming it ties.

## 5. Optional but recommended — honest milestone label
Rename the PIID-map column `"Earliest Keel"` → `"Earliest Fab Start"`. It is populated by min `Start Fabrication`, so the current label conflates keel and fabrication-start — the exact thing that made own-keel staging misleading. Touch points: CSV header in `extracted/ddg_piid_hull_map.csv`; `date_cols=[...]` in `ddg_piid_hull_map.py`; `_MAP_KEEL = piid_hull_map_cols("Earliest Fab Start")` in `ddg_subaward_transactions.py`; the prose in `ddg_procurement_timing.py` intro (*"predates the block's earliest fabrication start"*) and the two docstrings. Low risk, and it makes the Advance/LLTM phase read as *"committed before any hull in the block began fabricating"* — a stronger, self-consistent claim.

## 6. Build & validate
1. Regenerate `ddg_subaward_transactions.csv` without the lifecycle tagger (5 cols gone).
2. Delete the 7 modules; prune `kit/tabs.py` and the SHEETS registry; add the drill-down.
3. Apply the Step 3 edits.
4. Retire/repoint `_integrity.assert_lifecycle_labels_known` (it guarded the now-absent materialized stage set; the drill-down computes stage live from date bands, so no label-set guard is needed). Also drop `scripts/build_ddg_cd_lifecycle.py` (built the deleted candidates + rollup). **Keep** `scripts/build_ddg_vendor_hull.py` — it still feeds DDG Vendor x Hull Exposure and DDG Vendor x Hull x SWBS.
5. Rebuild; run `validate_workbook.py`; update its baselines (deleted-sheet anchors, the 77→72 tx column count, any lifecycle value anchors).
6. `python scripts/recalc.py <workbook>.xlsx` → confirm **zero formula errors** and Checks master = OK.

## Definition of done
32 tabs; no `Lifecycle*` / `Narrowing Result` columns or sheets remain; procurement timing unchanged and still ~63 / 36 / 1; drill-down reconciles to A/B for 125/128; recalc clean; master check OK.
