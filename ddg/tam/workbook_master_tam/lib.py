"""master pipeline bindings.

The OOXML engine lives in the shared ``workbook_core`` package at the workspace
root. This module is intentionally thin: it binds the things specific to this
pipeline (the output path, the extracted-data dir, the docProps identity, the tab
palette), exposes a load_extracted_csv wrapper bound to this pipeline's data dir,
and packages the SHEETS module list via the shared packager.

The extracted/ dir holds clean COMBINED-BY-TYPE CSVs (one per data tab, all three
programs in each) written by ``build_extracted.py``. Cell values are stored as
strings so identifiers keep their exact form; the sheet modules cast the numeric
columns via _cuts.as_int / as_float.
"""
from __future__ import annotations

from pathlib import Path

from workbook_core.lib import (
    package_workbook,
    load_extracted_csv as _core_load_extracted_csv,
)
import workbook_core.groups as _groups

# ---------------------------------------------------------------------------
# Tab palette - per-build override (THIS workbook only)
# ---------------------------------------------------------------------------
# Mirror the muted black / olive / slate / navy scheme used by the SAM
# award_analysis workbook (the shared workbook_core palette reads "loud"). group_color()
# reads workbook_core's _COLOR dict at render time, so mutating it here - before build()
# packages the sheets - repaints the tabs with no change to any sheet module. This
# mutates the shared dict IN THIS PROCESS ONLY; every other pipeline builds in its own
# process and keeps its own colors. Group order / group->sheet assignment are unchanged.
_TAB_PALETTE = {
    "summary":    "262626",   # black / charcoal - the answer page (Executive Summary)
    "guide":      "2C5E5E",   # muted teal       - the framing / method (Methodology)
    "inputs":     "556B2F",   # olive green      - the editable levers (Assumptions)
    "model":      "48596B",   # slate            - the per-program TAM engine
    "data":       "203864",   # navy blue        - the live-formula data spine
    "validation": "595959",   # muted gray       - live in-workbook checks (Checks)
}
_groups._COLOR.update(_TAB_PALETTE)

# ---------------------------------------------------------------------------
# Pipeline bindings
# ---------------------------------------------------------------------------

WORKBOOK_DIR = Path(__file__).resolve().parents[1]   # tam/master/  (build output lands here)
PROJECT_DIR = WORKBOOK_DIR                            # output lands at the master/ root
REPO_ROOT = Path(__file__).resolve().parents[5]      # ooxml_build_pipelines_light/
OUT = PROJECT_DIR / "20260620_Distributed Shipbuilding Master TAM_vS.xlsx"

EXTRACTED = WORKBOOK_DIR / "extracted"

_TITLE = "Distributed Shipbuilding - Master TAM (Virginia / Columbia / DDG-51)"
_CREATOR = "workbook_master_tam build_workbook.py"
_APP = "workbook_master_tam"


def load_extracted_csv(name: str) -> tuple[list[str], list[list]]:
    """Load extracted/<name>.csv from this pipeline's data dir (numeric-coerced)."""
    return _core_load_extracted_csv(name, EXTRACTED)


def build_model() -> list:
    """The registered sheets, in DISPLAY (tab) order, ready to package.

    The model's DEPENDENCY order is one-directional - data flows leaves -> answer:

        Deflators -> SCN Budget / FYDP Outyears / Place of Performance   (sources/derivation)
                  -> Assumptions                                          (knobs)
                  -> OBBBA Mandatory                                      (bridge)
                  -> Virginia / Columbia / DDG-51 TAM                    (model)
                  -> Executive Summary                                   (answer)

    Python's import graph already ENFORCES this: a consumer module cannot import a
    producer's accessor (e.g. `scn_cell`) until the producer has built at import, so
    the order is self-enforcing rather than orchestrated. This function is the single
    documented home for that contract; it returns the SHEETS registry (which is in
    the distinct summary->guide->inputs->model->data *tab* order) unchanged.
    """
    from workbook_master_tam.sheets import SHEETS
    return SHEETS


def build() -> int:
    """Render every registered sheet and package into the output xlsx."""
    return package_workbook(OUT, build_model(), title=_TITLE, creator=_CREATOR,
                            app_name=_APP, normalize_dashes=True)
