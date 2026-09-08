"""Streamlit compatibility facade for frontend-neutral Simulation authoring."""

from evo_engine.workbench.simulation_authoring import (
    EditableSimulationRevision,
    ReferenceDisclosure,
    SimulationDiff,
    SimulationRevision,
    controlled_draft_readiness,
    normalize_reference_draft,
    reference_draft_readiness,
    reference_has_expert_controls,
    reference_slots_for_disclosure,
    save_b3_radius_sensitivity_child,
    save_controlled_child,
    save_reference_child,
    semantic_slot_label,
    simulation_semantic_diff,
)

__all__ = [
    "EditableSimulationRevision",
    "ReferenceDisclosure",
    "SimulationDiff",
    "SimulationRevision",
    "controlled_draft_readiness",
    "normalize_reference_draft",
    "reference_draft_readiness",
    "reference_has_expert_controls",
    "reference_slots_for_disclosure",
    "save_b3_radius_sensitivity_child",
    "save_controlled_child",
    "save_reference_child",
    "semantic_slot_label",
    "simulation_semantic_diff",
]
