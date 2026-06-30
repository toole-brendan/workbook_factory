# DDG-51 SAM research backlog

This backlog keeps the research queue outside the workbook. The workbook should show coverage and confidence; this markdown file should track the research that could improve those coverage and confidence measures.

## Operating rule

Promote research into workbook inputs only when it can change a curated mapping, date, classification, or confidence grade with source evidence. Do not use this backlog to force family-level or multi-hull dollars into exact-hull assignments.

## Priority 1 - Hull attribution coverage

Goal: move defensible rows from family-level or conflict status toward better hull evidence, while preserving the A/B/C/D/X discipline.

### 1. Prime PIID / hull-family validation

Current workbook inputs show the PIID-to-hull map as the single source of truth for candidate families. Single-ship PIIDs exist for DDG 113 and DDG 114; later PIIDs are multi-hull families such as FY13-17, FY18-22, and FY23-27 MYP blocks.

Research actions:

- Validate whether any multi-hull PIID can be split into smaller subfamilies using award/modification evidence.
- Validate FY23-27 MYP hull-family membership, especially future or unvalidated hulls.
- Replace weak or secondary sources with primary sources where possible.
- Record the source and rationale in `ddg_piid_hull_map.csv` notes when the candidate set changes.

Useful targets from current inputs:

- `N0002413C2307` - HII FY13-17 family: DDG 117 / 119 / 121 / 123 / 125.
- `N0002413C2305` - BIW FY13-17 family: DDG 118 / 122 / 124 / 126 / 127.
- `N0002418C2307` - HII FY18-22 family: DDG 128 / 129 / 131 / 133 / 135 / 137 / 139.
- `N0002418C2305` - BIW FY18-22 family: DDG 130 / 132 / 134 / 136 / 138.
- `N0002423C2307` - HII FY23-27 family: DDG 141 / 142 / 143 / 145 / 146 / 147 / 149.
- `N0002423C2305` - BIW FY23-27 family: DDG 140 / 144 / 148.

### 2. High-dollar C/D transaction review

Current methodology keeps grade C/D rows family-level. The research opportunity is to find direct subaward evidence, source-backed hull references, or PIID refinements that can defensibly upgrade a row.

Research actions:

- Sort C/D rows by constant FY2026 dollars.
- Review Subaward Number, Subaward Description, Prime PIID, and prime Description of Requirement.
- Search supplier press releases, shipbuilder supplier references, and Navy/DoD announcements for the exact subaward or item.
- Promote only rows with one clear in-family hull to exact assignment.

Potential workbook input outcome:

- Add a curated transaction override table only if repeat manual evidence is found and the same logic cannot safely be encoded in the existing PIID/hull rules.

### 3. Conflict / X cleanup

Current hull methodology treats direct hull references outside the PIID family as conflicts and leaves them unassigned. Some of these are likely REBUY or origin-hull references.

Research actions:

- Classify high-dollar X rows into: true conflict, origin-hull / rebuy reference, multi-hull buy, or possible exact assignment.
- Record why the row should remain X when the direct hull appears to be an origin-hull reference.
- Only upgrade to A/B-style assignment when evidence names a single in-family build hull rather than a prior origin hull.

## Priority 2 - Lifecycle coverage

Goal: improve lifecycle confidence by strengthening the hull milestone calendar and candidate-family timing logic.

### 1. Replace projected / estimated milestone dates

Current `ddg_hull_master.csv` has Actual, Projected, Inferred, and Needs validation rows. Several newer hulls have missing launch dates or projected delivery dates.

Research actions:

- Source actual start fabrication, launch, christening, delivery, and relevant milestone dates from Navy, NAVSEA, shipbuilder, or program-report sources.
- Replace projected dates when actual dates become available.
- Keep milestone source URLs in `ddg_hull_master.csv` current.

High-priority date gaps from current inputs:

- Future HII hulls with projected launch/delivery or blank launch fields.
- Future BIW hulls with projected launch/delivery or blank launch fields.
- DDG 150, currently shown as TBD / unvalidated.

### 2. Improve C/D timing narrowing

Current lifecycle logic narrows C/D rows to hulls in build at the purchase date but does not collapse the set to a single hull.

Research actions:

- Identify high-dollar C/D rows where timing currently stays at 4+ candidates.
- Validate whether the PIID family can be narrowed by award year, option year, procurement year, or supplier-specific shipset evidence.
- Add evidence only to curated source inputs; do not split dollars across candidate hulls.

### 3. Long-lead interpretation

Long-lead is a confounder: material for a later hull can be purchased while earlier hulls are in build.

Research actions:

- Identify transactions that look like LLTM / EOQ / shipset material.
- Add notes or flags only when the evidence supports a stronger timing interpretation.
- Avoid converting long-lead timing into exact-hull assignment unless separate hull evidence exists.

## Priority 3 - SWBS mapping coverage

Goal: improve HII ship-system classification while keeping BIW outside the SWBS universe unless a separate BIW crosswalk exists.

Current `ddg_hii_swbs_crosswalk.csv` maps HII Work-Item Codes to SWBS subsystems and distinguishes observed crosswalk evidence from curated inference.

Research actions:

- Sort HII U00 rows by dollars and record count.
- Identify unmapped HII Work-Item Codes with enough component text to support a curated inference.
- Promote code-level mappings into `ddg_hii_swbs_crosswalk.csv` with evidence notes.
- Keep GD-BIW rows outside SWBS mapping unless a defensible BIW-specific system-code source is found.

## Priority 4 - Supplier classification coverage

Goal: reduce high-dollar D0 / P0 or weak NAICS-default classifications.

Research actions:

- Sort supplier rows by observed subaward dollars where D = D0 or P = P0.
- Review supplier websites, product pages, contract descriptions, and Navy/shipbuilder references.
- Add overrides to `ddg_vendor_archetype_overrides.csv` only when the supplier's recurring DDG role is clear.
- Preserve the two-axis rule: D = technical ship area; P = physical output / integration level.

## Promotion checklist

Before moving any research into workbook inputs, answer:

1. What exact workbook field changes?
2. What is the source URL or document evidence?
3. Does this change improve a confidence grade, mapping, date, or classification?
4. Does the change preserve the grain discipline?
5. Could it accidentally allocate C/D family-level dollars to a single hull? If yes, do not promote it into the evidence model.

## Do not do

- Do not add a workbook research tab unless an audience explicitly needs embedded worklists.
- Do not force multi-hull or family-level rows into single-hull assignments.
- Do not treat SWBS coverage as available for GD-BIW rows without a separate source.
- Do not treat observed SAM / TAM as market penetration.
