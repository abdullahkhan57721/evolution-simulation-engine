"""Configuration, dependency analysis, and simulation compilation APIs."""

from evo_engine.configuration.dependencies import (
    CHARACTERISTIC,
    ENVIRONMENTAL_FIELD,
    TRAIT,
    Dependency,
    DependencyReport,
    collect_component_dependencies,
    dependency_report,
    provided_biological_dependencies,
)
from evo_engine.configuration.spec import CompiledSimulation, SimulationSpec
from evo_engine.configuration.validation import SimulationSpecValidator

__all__ = [
    "CHARACTERISTIC",
    "ENVIRONMENTAL_FIELD",
    "TRAIT",
    "CompiledSimulation",
    "Dependency",
    "DependencyReport",
    "SimulationSpec",
    "SimulationSpecValidator",
    "collect_component_dependencies",
    "dependency_report",
    "provided_biological_dependencies",
]
