# DDG workbook data tree

This folder is the workbook-ready CSV input tree for the fully flattened DDG-51 workbook.

Files whose row universe was filtered to DDG-51 carry a `ddg_` prefix.  Pure reference
tables carry a `ref_` prefix.  The TAM and SAM source-workbook lineage is represented by
subfolders under `workbook_inputs/`; it is no longer represented as runtime package halves.

```text
data/
  workbook_inputs/
    reference/       shared references such as the one procurement-deflator table
    tam_budget/      DDG TAM budget / coefficient inputs
    sam_awards/      DDG SAM award, supplier, hull, SWBS and lifecycle inputs
  audit/             build-stopping guard inputs that are not visible worksheet tabs
  research_worklists/ workbook-adjacent worklists retained for guard lineage
  manifest.yaml      legacy stem to consolidated file map
```

Sheet modules request stable stems such as `scn_budget`, `supplier_master`, and
`ddg_subaward_transactions`; `ddg.lib` maps those stems to the explicit files here.
