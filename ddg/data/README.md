# DDG-51 workbook data

Every file here is consumed by `build_workbook.py` — either rendered onto a sheet or
read by a build-stopping guard in `sheets/_sam_integrity.py`. Nothing here is a raw
research dump; the unread extraction artifacts were left behind in the source pipelines.

The sheet code references each CSV by a terse **logical stem** (`supplier_master`,
`scn_budget`, `deflators`); the **physical file** carries a DDG-specific or reference
name in a category folder. `sheets/_data.py` is the single bridge between the two — the
runtime manifest (and the place to add a row when a new input is introduced). It resolves
side-aware (`tam` vs `sam`) because both pipelines have a `deflators` stem.

## Layout

```
data/
  workbook_inputs/                 # every file is a rendered-sheet or guard input
    tam_budget/                    # DDG slice of the Master TAM budget spine
      ddg_scn_budget.csv
      ddg_ap_lltm.csv
      ddg_place_of_performance.csv
      ddg_obbba.csv
      ddg_fydp_outyears.csv
      ref_tam_procurement_deflators_fy2026.csv
    sam_awards/                    # DDG slice of the Master SAM subaward base
      scope/        ddg_prime_awards.csv, ddg_prime_contract_scope.csv
      transactions/ ddg_subaward_transactions.csv
      supplier/     ddg_supplier_master.csv, ddg_supplier_year_activity.csv
      classification/ ddg_naics6_archetype_map.csv, ddg_vendor_archetype_overrides.csv
      swbs/         ddg_hii_swbs_crosswalk.csv, ddg_swbs_by_subsystem.csv
      hull/         ddg_piid_hull_map, ddg_hull_master, ddg_hull_exceptions,
                    ddg_vendor_hull_exposure, ddg_vendor_hull_swbs
      lifecycle/    ddg_cd_lifecycle_rollup.csv, ddg_cd_lifecycle_candidates.csv
      reference/    ref_sam_procurement_deflators_fy2026.csv
  audit/                           # guard-only inputs (not rendered sheets)
    duplicate_audit.csv
    duplicate_candidates.csv
```

## Naming rules

1. **`ddg_`** — the row universe was filtered from a broader multi-program universe
   (budget rows, prime contracts, subaward transactions, supplier dimensions, hull/SWBS/
   lifecycle spines). The prefix means "DDG-51 rows only," not "about DDG."
2. **`ref_`** — a general reference table that is *not* a DDG row universe. The two
   procurement-deflator tables are `ref_` (the TAM budget deflator spans the FY2022–31
   budget sheets; the SAM deflator drives the subaward fiscal axis through FY2026). They
   carry a `_tam`/`_sam` qualifier because they are different tables with different rows.
3. **`tam_budget/` vs `sam_awards/`** is *data lineage*, not a package split — the old
   TAM and SAM workbooks are source families, no longer runtime package roots.

A future Virginia/Columbia extraction must add its own `_data.py` rows + files; it cannot
silently reuse a `ddg_`-named file.

## Not carried here

- `ddg_program_vendors.csv` — the program-vendor roll-up is now an in-memory cut of
  Supplier Master, so it is not a sheet input. The universe guard was refactored to compare
  the two real runtime sources (`ddg_subaward_transactions` ↔ `ddg_supplier_master`), so
  this file is no longer a build input at all.
- `taxonomy.csv` — the D/P vocabulary is hardcoded in `sheets/_sam_taxonomy.py`; the
  Taxonomy tab renders from those constants, not a CSV.
- The unread research artifacts (`classifications`, `vendor_context`, `*_archetype_results`,
  `*.pre_mece`, `ddg_top_vendors`, `ddg_subaward_research_results`, `parent_concentration`,
  `swbs_curated_c`) — not read by the build.
