"""Logical tab groups - one color per group, contiguous in tab order.

The single source of truth for how tabs are grouped, colored, and ordered. A sheet
module declares its group:

    from workbook_core.groups import group_color
    SHEET_GROUP = "model"
    TAB_COLOR = group_color(SHEET_GROUP)

and the registry lists sheets grouped in this order. package_workbook() asserts the
groups stay contiguous and in canonical order (so "same group -> same color ->
together" is a build-time guarantee, not a convention). Color is a 6-hex RGB string
(no leading '#'); tab order = the order of SHEET_GROUPS below.

Groups are internal ordering + color metadata, NOT a checklist of tabs to create.
A workbook should declare only the groups it naturally needs and skip the rest; no
group is required to appear. In particular, do not add a guide/readme/instructions
tab just because the `guide` group exists - use it only when such a tab would
appear in a human-built workbook or the user explicitly asks for one (see the
"Human workbook standard" in sheet_guide.md).

The groups, in canonical order - what a tab in each is FOR:
  summary     the reader-facing answer page (headline result, bridge, audit status)
  guide       optional/rare: only if a human-built workbook here would carry one
  inputs      the editable knobs (the only place you change numbers)
  model       the calc / analysis engine (e.g. a TAM -> SAM model, or a set of
              derived analytical cuts)
  data        extracted source evidence / data dumps
  outputs     the deck-facing figure contract
  validation  audit, checks, sensitivity, exclusion trails
  sources     provenance / citations
  chartdata   the deck chart-data loader tab (machine-readable; sorts last, own color)

Reader flow: answer (summary) -> scope/method (guide) -> assumptions (inputs) ->
the model -> the data appendix it draws on (data) -> the deck contract
(outputs) -> checks (validation) -> provenance (sources) -> the deck chart-data
loader (chartdata, last). `model` precedes `data` so the calc sheets sit ahead of
the evidence dump; `chartdata` is a machine-readable loader tab parked last.
"""
from __future__ import annotations

# Ordered: defines BOTH the canonical tab-block order and each group's color.
# Palette: the muted charcoal / teal / olive / slate / navy scheme the Distributed
# Shipbuilding SAM + TAM workbooks adopted (the loud default read poorly). Baked in
# here as the factory default so every program folder inherits it without each
# pipeline's lib.py having to re-override _COLOR at import.
SHEET_GROUPS = [
    ("summary",    "Executive summary", "262626"),   # charcoal
    ("guide",      "Guide & scope",     "2C5E5E"),   # muted teal
    ("inputs",     "Inputs & levers",   "556B2F"),   # olive
    ("model",      "Model",             "48596B"),   # slate (calc / analysis engine)
    ("data",       "Source data",       "203864"),   # navy
    ("outputs",    "Outputs",           "2E7D4F"),   # green
    ("validation", "Validation",        "595959"),   # muted gray
    ("sources",    "Sources",           "1F3A5F"),   # navy
    ("chartdata",  "Chart data",        "404040"),   # charcoal (deck chart-data loader; sorts last)
]

_COLOR = {k: c for k, _label, c in SHEET_GROUPS}
GROUP_ORDER = {k: i for i, (k, _label, _c) in enumerate(SHEET_GROUPS)}
GROUP_LABEL = {k: label for k, label, _c in SHEET_GROUPS}


def group_color(key: str) -> str:
    """Tab color (6-hex RGB) for a group key. Raises on an unknown key."""
    if key not in _COLOR:
        raise ValueError(
            f"unknown SHEET_GROUP {key!r}; expected one of {list(_COLOR)}"
        )
    return _COLOR[key]
