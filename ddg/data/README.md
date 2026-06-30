# DDG workbook data tree

This folder is the workbook-ready CSV input tree for the consolidated DDG-51 workbook.

The repo began as a physical combination of two already-DDG-sliced workbooks:

- TAM: DDG-51 addressable new-construction opportunity.
- SAM: DDG-51 reported first-tier subaward / supplier classification model.

The old `ddg/tam/extracted/` and `ddg/sam/extracted/` stems are still recognized by
compatibility loaders, but the primary runtime location is now this program-scoped
data tree.  Files whose row universe was filtered to DDG-51 carry a `ddg_` prefix.
Pure reference tables that are not a DDG row universe carry a `ref_` prefix.

## Layout

```text
data/
  workbook_inputs/
    tam_budget/       DDG TAM budget / coefficient inputs
    sam_awards/       DDG SAM award, supplier, hull, SWBS and lifecycle inputs
  audit/              build-stopping guard inputs that are not visible worksheet tabs
  research_worklists/ workbook-adjacent research worklists retained for guard lineage
  manifest.yaml       data-contract map from legacy stems to the consolidated files
```

## Runtime rule

Sheet modules still ask for legacy stems such as `scn_budget`, `supplier_master`,
and `ddg_subaward_transactions`.  `ddg.lib` maps those stems to the explicit files
here, so the workbook can keep formula code stable while the repo structure becomes
DDG-specific and source-family-aware.

## DDG specificity

Program-universe files are DDG-specific.  Reference files are intentionally not
DDG-specific unless the row universe itself was filtered.
