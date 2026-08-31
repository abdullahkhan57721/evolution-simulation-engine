"""Configuration, dependency analysis, and generic simulation compilation APIs."""

from evo_engine.configuration.dependencies import (
    Dependency,
    DependencyReport,
    DependencyRequirementProvider,
    collect_component_dependencies,
    dependency_report,
)
from evo_engine.configuration.spec import CompiledSimulation, SimulationSpec
from evo_engine.configuration.validation import SimulationSpecValidator

__all__ = [
    "CompiledSimulation",
    "Dependency",
    "DependencyReport",
    "DependencyRequirementProvider",
    "SimulationSpec",
    "SimulationSpecValidator",
    "collect_component_dependencies",
    "dependency_report",
]
