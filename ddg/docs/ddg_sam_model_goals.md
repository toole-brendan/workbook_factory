# DDG-51 TAM/SAM model goals

This note captures the target framing for the DDG-51 workbook after the SAM-modeling discussion. It is intended to guide workbook changes and review, not to become a generated workbook tab.

## Workbook caveat

Use a short workbook-facing caveat rather than a long methodology paragraph:

> Observed SAM uses reported first-tier subawards as evidence of supplier structure and timing; it is not the full outsourced-market total.

The slide deck can carry the longer explanation. The workbook should keep the caveat close to the TAM-to-SAM bridge and repeat it only where a reader could mistake an evidence subset for the full market.

## Core framing

The workbook should answer two related but different questions:

1. **TAM:** How large is the supplier-addressable outsourced DDG-51 new-construction opportunity?
2. **SAM evidence layer:** What do reported first-tier subawards reveal about the shape, concentration, supplier continuity, ship-system application, hull traceability, and lifecycle timing of that opportunity?

TAM is the top-down denominator. Observed SAM is a bottom-up evidence layer. Observed SAM should inform market structure, coverage, and where-to-play analysis, but it should not be presented as the complete outsourced-market total.

## Denominator hierarchy

The workbook should make denominator changes visible before showing detailed cuts.

| Denominator | What it supports | Key limitation |
| --- | --- | --- |
| TAM | Size of the outsourced new-construction opportunity by FY | Does not identify individual suppliers or ship systems |
| Observed SAM | Reported first-tier subaward activity and supplier ecosystem evidence | Not the full outsourced-market total |
| Archetype-classified SAM | Supplier/entity structure by D and P archetypes | Depends on UEI x Program classification quality |
| HII SWBS universe | Ship-system application for HII-Ingalls rows | Not available for GD-BIW rows |
| SWBS mapped dollars | HII ship-system rollups outside U00 | Mapping gaps can change system mix |
| Exact-hull A/B dollars | Hull and hull-stage rollups | Only rows with single-ship or direct in-family hull evidence |
| Family-level C/D dollars | Candidate-family and lifecycle-narrowing evidence | Candidate sets are not per-hull dollar allocations |
| Conflict / X dollars | Review queue for hull-text conflicts and multi-hull rows | Not interpretable as exact-hull spend |

## Grain discipline

The workbook should keep the following grains separate and roll them up intentionally.

### Transaction grain

The subaward transaction is the evidence source. It carries the purchase date, amount, Prime PIID, subaward text, builder, SWBS evidence, hull evidence, fiscal-year fields, and lifecycle fields. Hull confidence, lifecycle stage, and C/D narrowing should be assigned at this grain first.

### Supplier/entity grain

UEI x Program is the supplier-classification grain. D and P archetypes describe the supplier entity, not each individual subaward line. Parent-level concentration should be calculated after UEIs are resolved to a standardized parent.

### Ship-system grain

SWBS is a transaction-level ship-system companion dimension, currently HII-DDG only. SWBS should answer where observed HII work appears on the ship, not serve as a universal market taxonomy for both builders unless a separate representativeness assumption is introduced.

### Hull and lifecycle grain

Hull and lifecycle should remain evidence-limited.

- A/B rows can be assigned to a single hull and stage-tagged by lifecycle period.
- C/D rows can be narrowed to candidate hull sets and lifecycle-confidence buckets.
- C/D dollars should not be split across candidate hulls inside the evidence model.
- X rows should remain a research/review queue unless evidence supports reclassification.

## Target analytical outputs

The workbook should aim for five end products.

### 1. Annual opportunity bridge

Show TAM by FY, observed SAM by FY, observed SAM / TAM, and the reporting caveat. The goal is to anchor the market size while making subaward coverage boundaries explicit.

### 2. Where-to-play market map

Use D and P archetypes to show observed spend, annual growth, active suppliers, parent concentration, incumbent-dollar share, retention, first-observed spend, and reactivated spend. This is the primary SAM analytical view.

### 3. Supplier control map

Use UEI and parent rollups to show supplier concentration, parent Top-1 share, parent HHI, effective number of firms, and continuity by FY. UEI is the operating-entity view; parent is the market-control view.

### 4. Ship-construction traceability map

Show SWBS, hull, and lifecycle coverage with confidence grades. This is where the workbook explains how far the evidence can be pushed.

### 5. Research backlog

Keep research work outside the workbook tabs in `ddg/docs/ddg_sam_research_backlog.md`. Promote completed research into curated workbook inputs only after the evidence is strong enough.

## Workbook changes to aim for

The following changes should be evaluated in this order.

1. **Add a Market Bridge tab.** Use the existing `TAB_MARKET_BRIDGE` name if it stays unused. The tab should show TAM vs observed SAM by FY, the observed-SAM denominator ladder, and what each denominator can and cannot support.
2. **Add the short observed-SAM caveat to Executive Summary.** Put it near observed SAM or the TAM-to-SAM bridge.
3. **Expand Executive Summary coverage metrics.** Add exact A/B share, C/D family-level share, X share, SWBS mapped share, and C/D lifecycle narrowing summary.
4. **Add exact-hull `Vendor x Hull x Lifecycle` rollup.** Grain: UEI x Assigned Hull x Lifecycle Stage, A/B only.
5. **Add evidence-limited archetype x lifecycle views.** Exact A/B rows can support D/P x lifecycle stage. C/D rows should support D/P x narrowing result / lifecycle confidence, not per-hull dollars.
6. **Keep the research queue in markdown.** Do not add a workbook research tab unless the audience needs an embedded worklist.
7. **Remove hard-coded dollar values from captions.** Captions should describe the coverage universe without embedding dollar amounts that can drift.
8. **Reorder summary tabs if a Market Bridge tab is added.** Suggested order: Executive Summary, Market Bridge, Where to Play, Domain Concentration.
9. **Add reconciliation checks for any new rollup.** A new exact-hull lifecycle rollup should reconcile to total A/B exact-hull transaction dollars.

## Non-goals

The workbook should not try to build one definitive cube at `FY x UEI x parent x D x P x SWBS x hull x lifecycle` without coverage caveats. That mixes incompatible grains and would encourage readers to over-interpret sparse evidence.

The workbook should also avoid modeled per-hull allocation of C/D family-level dollars inside the evidence workflow. If a modeled allocation is ever needed, it should live in a separate, clearly labeled scenario view.

## Recommended reader path

1. Executive Summary: market size and key observations.
2. Market Bridge: denominator ladder and coverage caveats.
3. Where to Play: annual D/P market map.
4. Domain Concentration: lifetime structure and parent concentration.
5. Supplier detail: UEI and parent drilldowns.
6. SWBS evidence: HII ship-system view.
7. Hull and lifecycle evidence: exact-hull and family-level timing views.
8. Data, mappings, assumptions, and checks.
