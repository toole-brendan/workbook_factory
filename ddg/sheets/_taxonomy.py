"""_taxonomy - the finalized classification vocabulary (shared leaf).

NON-sheet helper module (renders nothing; NOT registered in SHEETS). It is the
single source of truth for the entity-level classification schema, so the two
guide sheets that present it - ``taxonomy`` (the legend) and ``guide_methodology``
(the method) - both import the SAME constants instead of retyping them. Mirrors
the ``_taxonomy`` leaf in the DDG/submarine workbooks: a true leaf with no sheet
dependencies, so any consumer can depend on it without importing a renderer.

The schema is two independent published axes, each answering exactly one question, plus a
forced catch-all per axis so every UEI x Program receives exactly one label on
every axis (MECE):

  - Capability Domain (D, published) - what technical ship area the vendor supports
  - Primary Output     (P, published) - what physically leaves the vendor

Output is assigned from its own physical-form evidence.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Grain / framing
# ---------------------------------------------------------------------------

GRAIN_INTRO = (
    "Classification definitions."
)

# ---------------------------------------------------------------------------
# Section 1 - Capability Domain archetypes (published)   (code, name, definition)
# ---------------------------------------------------------------------------

DOMAIN_INTRO = (
    "Technical ship area supported by the supplier."
)

DOMAINS: list[tuple[str, str, str]] = [
    ("D1", "Hull, Structures & Marine Fabrication",
     "Hull, superstructure, decks, structural assemblies, weldments, foundations, and structural construction of the ship and its zones."),
    ("D2", "Propulsion & Power-Transmission Machinery",
     "Prime movers and mechanical/electric drive that propel the ship or transmit propulsive power: gas turbines, diesels, propulsion motors and drives, reduction gears, shafting, propulsors, bearings."),
    ("D3", "Electrical Power - Generation, Conversion & Distribution",
     "Generates, converts, switches, protects, or distributes ship-service electrical power: generator sets, switchboards, load centers, transformers, power electronics, switchgear, motor controls."),
    ("D4", "Fluid, Pressure & Piping Systems",
     "Moves, controls, or stores fluids and gases: valves, pumps, actuators, manifolds, compressors, high-pressure air, piping and fittings, seals, filtration."),
    ("D5", "Thermal, HVAC & Life-Support",
     "Transfers heat and conditions the shipboard environment: chillers, HVAC and refrigeration, heat exchangers, condensers, ventilation, atmosphere and life-support equipment."),
    ("D6", "Mission, Combat & Communications Systems",
     "System-level sensing, communications, control, and weapon systems: sonar/acoustic arrays, radar, electronic warfare, communications, mission and fire-control systems, imaging masts, and ordnance (naval guns, missile launch systems and tubes, weapon-handling). Ordnance is kept here rather than as a separate domain - see tie-breaks."),
    ("D7", "Electronic Components, Interconnect & Cable",
     "Component-level electrical/electronic hardware that connects and carries power or signal: hull penetrators, connectors, feedthroughs, cable and wire harnesses, circuit cards, and instrumentation components."),
    ("D8", "Mechanical Handling & Deck Machinery",
     "Shipboard handling and access machinery: davits, cranes, hoists, winches, capstans, elevators, boat- and weapons-handling gear, and specialty/hangar/access doors. Bounded to handling and access mechanisms - general fluid, thermal, or electrical machinery resolves to D4 / D5 / D3 by function, not here."),
    ("D9", "Specialty Materials & Precision Processes",
     "A material- or process-defined competence whose specific ship application is NOT determinable from the industry code: forging, casting, machining, rolled rings, composites, elastomers, acoustic/signature treatments, isolation mounts. This is a process/material axis, not a ship-system area - the same forging or composite feeds many systems. Assign a functional domain (D1-D8) whenever the ship application IS known; D9 is the application-agnostic fallback for material/process specialists."),
    ("D10", "Interiors, Habitability & Outfitting",
     "Shipboard interiors and habitability outfit: furniture and joinery, galley and berthing outfit, insulation and deck covering, and habitability / safety / egress gear. Bounded to interior and habitability outfitting - NOT a residual for otherwise-unclassified manufactured goods (those resolve by function or to D0)."),
    ("D11", "Services & Non-Material Support",
     "The entity's competence is non-material support rather than a ship technical/material area: engineering / test / R&D services, installation and field service, repair and overhaul, logistics and transportation, software and IT, training and workforce development, or facilities and construction. The domain-axis counterpart of Primary Output P6 - use when the deliverable is labor or an intangible, not a ship article. Pure material distributors are NOT here: they take the domain of the material they handle, or D0 if indeterminate (distribution is a role, not a service)."),
    ("D0", "Unresolved / Insufficient Evidence",
     "No single technical domain is defensible (a genuinely multi-domain firm with no primary, or insufficient evidence); still gives every UEI x Program exactly one domain label."),
]

# Domain boundary tie-breaks (situation, rule) - rendered as a sub-table.
DOMAIN_TIEBREAKS: list[tuple[str, str]] = [
    ("D2 vs D3 (turbine-generators)",
     "Ship-service power generation to D3; main propulsion drive to D2."),
    ("D6 vs D7 vs D3 (electronics)",
     "System-level sensing/combat/comms to D6; component-level interconnect, cable, penetrators to D7; ship-service power components to D3. Classify by function and integration level."),
    ("D9 vs a system domain",
     "Classify by the vendor's differentiating competence: the material/process itself to D9; a complete functional system to the system domain (a sonar-array maker to D6; a composite-acoustic-parts maker to D9)."),
    ("D1 vs D4 (pressure boundaries)",
     "Structural / pressure-vessel fabrication to D1; functional fluid/pressure equipment (valves, pumps) to D4."),
    ("D2 vs D3 (electric drive & power)",
     "A firm spanning propulsion motors/drives (D2) and power generation, conversion, or distribution (D3) - e.g. an integrated electric-plant or motor-and-generator supplier (NAICS 335312) - is assigned by its dollar-dominant ship function, never D0: propulsion-motor / electric-drive dominant to D2; ship-service power dominant to D3."),
    ("Ordnance",
     "Naval guns, missile launch systems and tubes, and weapon-handling stay in D6; there is no separate ordnance domain - under the hull-builder scope the dedicated weapons GFE primes are out of scope, so standalone ordnance content is sparse."),
    ("Service firms",
     "A service firm whose specialty maps unambiguously to one technical area keeps that area (a propulsion test house to D2); a firm whose deliverable is general non-material support with no single technical area to D11 Services (no longer D0)."),
    ("Pure distributors",
     "Assign the domain of the material handled; D0 only when even that is indeterminate."),
]

# ---------------------------------------------------------------------------
# Section 2 - Primary Output archetypes (published)   (code, name, definition)
# ---------------------------------------------------------------------------

OUTPUT_INTRO = (
    "Primary delivered form and integration level."
)

OUTPUTS: list[tuple[str, str, str]] = [
    ("P1", "Materials, Stock & Bulk Inputs",
     "Material not yet a finished ship item: requires substantial downstream machining, fabrication, or qualification (plate, bar, structural shapes, near-net forgings, rough castings, blanks, rolled rings), or is consumed in process (coatings, sealants, resins, welding consumables, gases, lubricants)."),
    ("P2", "Finished Parts & Fabricated Components",
     "Dimensionally complete or fit-ready parts and fabrications that install into a larger item and do not independently perform the principal shipboard function: machined parts, fittings, bearings, seals, mounts, gaskets, composite panels, weldments, pipe spools, foundations, harnesses."),
    ("P3", "Functional Equipment & Machinery",
     "A bounded, acceptance-testable unit that performs a defined function once connected or installed: engines, generator sets, reduction gears, pumps, valves, compressors, HVAC plants, switchboards, transformers, actuators, davits."),
    ("P4", "Integrated Systems & Configured Shipsets",
     "Multiple interdependent hardware, software, control, or sensor elements delivered as one configured solution with system-level integration or interface responsibility: sonar shipsets, integrated communications, electric-propulsion packages, fire-control, naval gun systems."),
    ("P5", "Outfitted Structures & Ship Modules",
     "A major structural section or spatially organized module assembled from multiple parts and trades, transferred as a defined shipbuilding unit: hull/superstructure units, outfitted modules, deck modules, completed submarine decks."),
    ("P6", "Services & Technical Work Products",
     "A labor-led or primarily intangible handoff used to construct, qualify, or support the vessel: engineering packages, test and qualification, calibration, installation, repair, production support, shipyard labor, standalone software or technical data."),
    ("P0", "Unresolved / Attribution-Only",
     "No defensible operating output can be assigned, or the record reflects a parent, investor, or holding-company attribution rather than an operating supplier."),
]

# Primary Output boundary tests (pair, test) - the MECE boundaries.
OUTPUT_BOUNDARIES: list[tuple[str, str]] = [
    ("P1 vs P2",
     "Substantial manufacturing remains after delivery (P1) vs. dimensionally complete / fit-ready (P2). A rough shaft forging is P1; a fully machined propulsion shaft is P2."),
    ("P2 vs P3",
     "Performs its function only after being built into another device (P2) vs. can be individually specified, acceptance-tested, and connected as a functional unit (P3). A gasket, bearing, or flange is P2; a valve, pump, or switchboard is P3."),
    ("P3 vs P4",
     "Requires ACTUAL functional integration, not mere co-delivery. 100 independent valves shipped together stay P3; a propulsion package with motor, drives, switchgear, controls and configured interfaces is P4. 'Shipset' alone does not trigger P4."),
    ("P4 vs P5",
     "Organized around a shipboard FUNCTION (P4) vs. a physical ship ZONE or structure (P5). A sonar array or electric-drive package is P4; an outfitted command-and-control deck module is P5, even though it contains functional equipment."),
    ("Hardware vs P6",
     "When hardware and services are bundled, classify the hardware output unless labor or technical work is clearly the principal contractual handoff. An OEM supplying an HVAC plant plus install support is P3; a firm engaged principally for test, repair, or industrial labor is P6."),
]

# ---------------------------------------------------------------------------
# Assignment rule
# ---------------------------------------------------------------------------

ASSIGNMENT_RULE = (
    "For each UEI x Program, classify the most representative recurring output "
    "transferred across the vendor's contractual boundary, not the most "
    "sophisticated item in its portfolio. With several items, take the highest "
    "integration level only when they ship as one configured system."
)

# ---------------------------------------------------------------------------
# Section 3 - Ship-System Application (SWBS) - transaction-level, HII-DDG only
# ---------------------------------------------------------------------------
#
# A different-grain COMPANION dimension, not a fourth entity archetype: it is
# carried on the subaward TRANSACTION (one HII-DDG subaward to one ship-system
# application), where D / P are entity-level (UEI x Program). A UEI keeps one
# Capability Domain / Output while its transactions hit many SWBS groups.

SWBS_INTRO = (
    "Ship-system application from observed HII-DDG work-item codes."
)

# (code, ship-system application, example subsystems / drill-down)
SWBS_GROUPS: list[tuple[str, str, str]] = [
    ("100", "Hull Structure",
     "Structural units, hull accesses, foundations, structural closures."),
    ("200", "Propulsion Plant",
     "234 propulsion gas turbines; 241 reduction gears; 244 shaft bearings; 245 propulsors; 262 lube oil."),
    ("300", "Electric Plant",
     "310 power generation; 314 power conversion; 324 switchgear and panels."),
    ("400", "Command, Control & Surveillance",
     "431 interior-comms switchboards; 433 announcing; 436 alarm/safety/warning; 451 radar; 475 degaussing."),
    ("500", "Auxiliary Systems",
     "Pumps, piping, ventilation, refrigeration, cooling water, compressed air, fire extinguishing, steering, deck handling."),
    ("600", "Outfit & Furnishings",
     "624 non-structural closures; 633 cathodic protection."),
    ("700", "Armament",
     "712 ammunition handling and other weapons-related system elements."),
    ("800", "Integration / Engineering",
     "Design integration, engineering, logistics, system-integration work. Program/contract decomposition, not an installed ship system."),
    ("900", "Ship Assembly & Support Services",
     "Ship assembly, production support, testing, trials, shipbuilder-support. Program/support activity, not an installed ship system."),
    ("X00", "Cross-Cutting Design & Construction Requirements",
     "Requirements applied across systems rather than installed as one - e.g. 730 to 7300 Noise & Vibration. Bounded by an explicit code list, not 'anything that spans systems'."),
    ("L00", "Legacy / Unmapped SWBS Reference",
     "A plausible SWBS or product-structure reference that does not resolve against the current codebook (e.g. 351, pending validation)."),
    ("U00", "No SWBS Evidence",
     "No defensible ship-system application can be extracted or inferred."),
]

SWBS_HIERARCHY_NOTE = (
    "HII work-item codes remain drill-down fields; SWBS is the comparable headline."
)
