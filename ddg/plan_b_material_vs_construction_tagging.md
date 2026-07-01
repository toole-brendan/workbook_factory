# Plan B — Material vs Construction (Work-Nature) Tagging

*Sequenced after Plan A.*

## Outcome
Add a **binary, transaction-grain Work Nature axis — Material vs Construction** — resolved text-first with a material default, orthogonal to Capability Domain (D), Primary Output (P) and SWBS. Capacity SOWs and services are **scope carve-outs beside the axis, not values on it**. The headline payoff is **Nature × Procurement Timing** (advance *material* vs early *fabrication*), which closes the one conceptual seam in the timing anchor.

## Why after Plan A
One axis of change at a time (isolated validation), and the headline exhibit assumes the Plan-A timing anchor is in place. Plan B also re-fills the Executive Summary / Market Bridge rows that Plan A vacated.

## Design decisions (locked from our discussion)
- **Binary axis.** Material / Construction only — not a four-way schema. Enumeration in a memo ≠ a schema value.
- **Resolution order inverts D/P.** Transaction-truth first: `Work Nature = IF(override, override, IF(fabrication-text, "Construction", "Material"))`. Material is the default because most rows are textless components and the firm's NAICS is the *worst* guide to a single transaction's nature (the Marmon CAPEX line; Gulf Copper's block-vs-part split). **Do not** build a NAICS→nature map as the primary path; a NAICS fallback for textless rows is optional and, if added, flagged low-confidence.
- **Capacity + services are carve-outs**, handled like the workbook's existing GFE/design exclusions — netted out of the axis, optionally surfaced in their own small exhibit — never Material/Construction values.
- **Grain = transaction.** This is the entire point: the firm grain (D/P via UEI×NAICS) structurally cannot separate a firm's fabrication line from its component line, because they share a UEI.

---

## 1. Inputs — new override sheet
New leaf `ddg_work_nature_overrides.py` (mirror `vendor_archetype_overrides.py`) → tab `"Mapping - Work Nature Overrides"`, CSV `extracted/ddg_work_nature_overrides.csv`.
Columns: key (`Subaward Report ID`, or `Program|Report ID`), `Work Nature` (Material/Construction/Capacity/Service), `Note` (+ Source URL → hover note). Pale-yellow input fill. This is the hand-verified override tier for rows the text rule gets wrong — e.g. the Gulf Copper −$7.19M D52 deobligation, any block row whose text doesn't match the regex, and BAE Jacksonville GB B15 (uncorroborated in public reporting, so flag it explicitly).

## 2. Transaction sheet — add the tag
Follow the repo's own pattern (materialize only the *evidence*, classify *live*), exactly as the hull classification does off the PIID map.

**Materialized on the CSV** (new `scripts/tag_ddg_transactions_work_nature.py`, mirroring the hull-regex evidence):
- `Fabrication Text Flag` (int/bool) — description matches structural-fab language.
- `Nature Text Class` (optional) — Construction / Capacity / Service / "" from the regex, so capacity/service are separable for the carve-out.

**Regex seeds** (from the grand-block findings; case-insensitive; **order matters**):
- **Capacity** (carve-out): `CAPEX:?\s*SOW\s+FOR` — one-time capital SOWs (Marmon, SteelFab, Espey). Match capacity **before** construction so `"CAPEX: SOW FOR STEELFAB"` doesn't fall into the fabrication bucket.
- **Construction:** `UNIT\s+OUTSOURC`, `GRAND\s*BLOCK`, `\bGB\s*[A-D]?\d`, `SOW.*(UNIT|OUTSOURC)` — but not if the capacity pattern already matched.
- **Service** (carve-out): `SURFACE\s*PREP|COATING|FIBER\s*OPTIC.*TEST|\bTEST(ING)?\b|TRIAL|WARRANTY`.
- **Else:** no flag → defaults to **Material**.

Coverage reality: ~$213M of the U00-in-build tail is bare work-item-coded components with no text — correctly defaults to Material; the large majority of the ~5,006 rows are textless → Material. Only the text-bearing minority moves. The axis is high-value at the seams, not a rich distribution.

**Live formula columns** (add to `_FORMULAS`, mirror the hull classification):
- `Work Nature Override Row` (hidden helper): `MATCH(key, overrides-key-range, 0)` → 0 if none.
- `Work Nature` (live): `IF(override row>0, INDEX(override nature, row), IF(Fabrication Text Flag=1, "Construction", "Material"))`. If you carry `Nature Text Class`, resolve Capacity/Service here too (the column can read all four; the *axis* exhibits filter to Material/Construction).
- `Work Nature Basis` (live): Override / Description-tagged / Default-material — the auditability sub-column, like SWBS basis and the D/P bases.

**Module bookkeeping:** extend `_WIDTHS` (72 → 72 + N) and bump the `== 72` assert to match; add the new hidden helper to `hidden_headers`; import `work_nature_overrides_cols` and wire the override ranges; update the docstring. Column letters stay name-resolved, so nothing downstream hardcodes them.

## 3. New exhibits
1. **DDG Work-Nature Coverage** (mirror DDG Hull Coverage): $ and share by Work Nature (Material, Construction), with Capacity/Service as separate carve-out lines below the axis subtotal, **plus a by-basis split** (Description-tagged vs Default-material) so a reader sees how much of "Construction" is text-confirmed vs assumed. This is the auditability sheet — keep it in the workbook's ethos of showing your work.
2. **Nature × Procurement Timing** (the payoff): a small matrix, Work Nature (rows) × timing phase (cols: Advance/LLTM, In-build, Post-delivery), `$` cells via `SUMIFS` on both columns. This resolves the single ~63% Advance headline into advance *material* vs early *fabrication*, and puts the grand-block fabrication in in-build/early-construction rather than lumped with turbines.
3. **Optional — Nature × SWBS (leak repair):** show Construction-nature dollars concentrating in U00/unmapped, demonstrating the axis rescues what SWBS's HII-only functional taxonomy misses (grand-block PWBS coding is orthogonal to SWBS).
4. **Optional — Supply-base investment exhibit:** the Capacity carve-out (~$60M CAPEX SOWs, 2021–22) as its own small table — the "the prime funds supplier capacity, not just output" story, on-thesis for distributed shipbuilding. Explicitly separate from the axis **and** from the 2024–25 grand-block fabrication (different mechanism, different vintage — don't let them collapse into one narrative).

## 4. Guides
- **Taxonomy tab:** add a Work Nature legend — Material / Construction definitions, plus the note that Capacity and Service are scope carve-outs, not axis values. In the wording, keep **"material"** (nature — is it a thing at all) distinct from P's **"component"** (integration level — how finished the thing is); that's the easiest conflation.
- **guide_methodology (classification tab):** add a Work Nature block — text-first + material default + override; state that its resolution order intentionally **inverts** D/P (because nature is the least firm-stable property); and its orthogonality to P and SWBS.

## 5. Checks + summaries
- **`checks.py`:** add a partition check — Material + Construction + Capacity + Service (+ undated/other) = observed SAM total, i.e. the nature tag is MECE over the universe (same shape as the existing procurement-timing partition check). Optional sanity anchor: Construction ≈ the grand-block magnitude, Capacity ≈ the CAPEX-SOW magnitude — treat as a *range*, not an exact reconciliation, since the findings-doc figures are for the U00-in-build subset, not the whole corpus.
- **Executive Summary §6 / Market Bridge §2:** add a Work-Nature row (e.g., Construction share of observed SAM), reusing the slots Plan A vacated. Nice symmetry — Plan A removed the C/D-lifecycle rows; Plan B fills them with the nature axis.

## 6. Build & validate
1. Add the override CSV + module + tab; add the work-nature tagger to the CSV build chain; regenerate `ddg_subaward_transactions.csv`.
2. Extend the tx module (widths / assert / formulas / hidden helper / overrides wiring).
3. Add the coverage + Nature×Timing (+ optional) exhibits, `TAB_*` constants, SHEETS registration.
4. Taxonomy + methodology edits; summary-row edits.
5. Rebuild; `validate_workbook.py` (add baselines for the new sheets + new tx column count); `recalc.py` → zero errors, master check OK (including the new partition check).

## Definition of done
A binary Work Nature column resolving text-first with a material default and an override tier; capacity/services carved out, not on the axis; a coverage sheet with a basis split; a Nature × Timing matrix that splits the ~63% Advance bucket into material vs fabrication; MECE partition check green; recalc clean.
