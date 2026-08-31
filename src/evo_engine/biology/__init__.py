"""Biological specializations layered on generic simulation infrastructure."""

from evo_engine.biology.configuration import (
    BEHAVIOR_SELECTION_MODEL,
    CHARACTERISTIC,
    ENVIRONMENTAL_FIELD,
    GENETIC_ARCHITECTURE,
    TRAIT,
    BiologicalSimulationSpec,
    collect_biological_dependencies,
    provided_biological_dependencies,
)
from evo_engine.biology.lifecycle import build_standard_lifecycle

__all__ = [
    "BEHAVIOR_SELECTION_MODEL",
    "CHARACTERISTIC",
    "ENVIRONMENTAL_FIELD",
    "GENETIC_ARCHITECTURE",
    "TRAIT",
    "BiologicalSimulationSpec",
    "build_standard_lifecycle",
    "collect_biological_dependencies",
    "provided_biological_dependencies",
]
