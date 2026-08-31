"""Domain-neutral cross-component validation for simulation specifications."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from evo_engine.configuration.dependencies import DependencyReport, dependency_report

if TYPE_CHECKING:
    from evo_engine.configuration.spec import SimulationSpec


@attrs.frozen(slots=True)
class SimulationSpecValidator:
    """Validate static domain-neutral invariants for a simulation specification."""

    def validate(self, spec: SimulationSpec) -> DependencyReport:
        """Validate generic component dependencies before runtime creation."""
        components: tuple[object, ...] = (
            spec.step_coordinator,
            spec.stopping_condition,
            *spec.observers,
            *spec.telemetry_observers,
        )
        report = dependency_report(
            components=components,
            required=spec.required_dependencies,
            provided=spec.provided_dependencies,
        )
        report.require_satisfied()
        return report
