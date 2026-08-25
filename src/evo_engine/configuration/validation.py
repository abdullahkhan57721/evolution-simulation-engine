"""Cross-component validation for complete simulation specifications."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from evo_engine.configuration.dependencies import DependencyReport, dependency_report

if TYPE_CHECKING:
    from evo_engine.configuration.spec import SimulationSpec


@attrs.frozen(slots=True)
class SimulationSpecValidator:
    """Validate static invariants spanning a complete simulation object graph."""

    def validate(self, spec: SimulationSpec) -> DependencyReport:
        """Validate a complete specification before mutable runtime is created.

        Validation performed here is deliberately static: component dependency
        satisfaction, initial genome/phenotype consistency, and developmental
        trait-set consistency. State-dependent invariants remain runtime event
        responsibilities because they cannot be proven before the run.

        Args:
            spec: Complete simulation specification to validate.

        Returns:
            Dependency report for the validated component graph.

        Raises:
            ValueError: If a dependency is missing or initial biological state
                is inconsistent with the configured architecture.
        """
        components: tuple[object, ...] = (
            spec.step_coordinator,
            spec.stopping_condition,
            spec.behavior_selection_model,
            *spec.observers,
            *spec.telemetry_observers,
        )
        report = dependency_report(
            components=components,
            genetic_architecture=spec.genetic_architecture,
            world=spec.initial_world_state,
        )
        report.require_satisfied()
        self._validate_initial_organisms(spec)
        return report

    @staticmethod
    def _validate_initial_organisms(spec: SimulationSpec) -> None:
        architecture = spec.genetic_architecture
        for organism in spec.initial_world_state.organisms.values():
            architecture.validate_genome(organism.genome)
            expected = architecture.express(organism.genome)
            if organism.genetic_phenotype != expected:
                raise ValueError(
                    f"Organism {organism.id} genetic phenotype is inconsistent "
                    "with its genome under the simulation specification's "
                    "genetic architecture."
                )
            organism.developmental_profile.validate_against(expected)
