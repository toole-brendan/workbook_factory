# Session 02 — Consolidated DDG sheet registry and data tree

## Scope

Implement the agreed consolidation direction from the review session:

- promote `ddg/build_workbook.py` as the primary DDG workbook entrypoint;
- add one merged `ddg.sheets` registry instead of a TAM block followed by a SAM block;
- replace the two source-workbook executive summaries with one merged DDG front door;
- add a consolidated `ddg/data/` tree with DDG-specific CSV names and reference/audit namespaces;
- route TAM/SAM CSV loaders through `ddg.lib` so legacy stems resolve to the new data tree.

## Compatibility note

The sheet implementations are still reused from the already-DDG-sliced TAM/SAM modules in this
branch.  That keeps the formula-heavy workbook stable while making the runtime unit DDG-specific.
A later mechanical cleanup can rewrite internal imports and remove the historical package shells
once the generated workbook is recalc-verified.
