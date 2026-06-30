"""DDG-scoped SAM integrity guard facade.

The guard implementation still lives with the historical SAM modules while the
runtime data has moved to ``ddg/data``.  Importing this facade patches the one
path that was formerly relative to ``ddg/sam`` and then re-exports the existing
build-stopping checks.
"""
from __future__ import annotations

from ddg.lib import SAM_SCOPE_DATA
from workbook_award_classification_refactor.sheets import _integrity as _ig

_ig._SCOPE_MANIFEST = SAM_SCOPE_DATA / "ddg_prime_contract_scope.csv"

assert_piids_in_manifest = _ig.assert_piids_in_manifest
assert_universes_aligned = _ig.assert_universes_aligned
assert_duplicate_audit_recorded = _ig.assert_duplicate_audit_recorded
assert_archetype_codes_valid = _ig.assert_archetype_codes_valid
assert_naics_rationale_aligned = _ig.assert_naics_rationale_aligned
assert_transaction_dates_covered_by_fiscal_axis = _ig.assert_transaction_dates_covered_by_fiscal_axis
assert_prime_awards_cover_transaction_piids = _ig.assert_prime_awards_cover_transaction_piids
assert_supplier_year_activity_spine = _ig.assert_supplier_year_activity_spine
assert_hull_piids_mapped = _ig.assert_hull_piids_mapped
assert_hull_map_master_consistent = _ig.assert_hull_map_master_consistent
assert_hull_milestones_monotonic = _ig.assert_hull_milestones_monotonic
assert_lifecycle_columns_consistent = _ig.assert_lifecycle_columns_consistent
