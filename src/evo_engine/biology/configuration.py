"""Biological configuration layered on the domain-neutral compiler."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.behavior import (
    BEHAVIOR_SELECTION_MODEL,
    BehaviorSelectionModel,
    UnrestrictedBehavior,
)
from evo_engine.configuration import CompiledSimulation, Dependency, SimulationSpec
from evo_engine.configuration.dependencies import iter_configuration_components
from evo_engine.context import SimulationContext
from evo_engine.engine import (
    Observer,
    StepCoordinator,
    StoppingCondition,
)
from evo_engine.evolution import CharacteristicRequirementProvider
from evo_engine.genetics import GENETIC_ARCHITECTURE, GeneticArchitecture
from evo_engine.genetics.requirements import TraitRequirementProvider
from evo_engine.telemetry import TelemetryObserver
from evo_engine.world import WorldState

TRAIT = "trait"
CHARACTERISTIC = "characteristic"
ENVIRONMENTAL_FIELD = "environmental_field"


@attrs.frozen(slots=True, kw_only=True)
class BiologicalSimulationSpec:
    """Describe a biological simulation on top of the generic compiler."""

    initial_world_state: WorldState = attrs.field(
        validator=attrs.validators.instance_of(WorldState),
    )
    genetic_architecture: GeneticArchitecture = attrs.field(
        validator=attrs.validators.instance_of(GeneticArchitecture),
    )
    step_coordinator: StepCoordinator
    stopping_condition: StoppingCondition
    seed: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(int)),
    )
    behavior_selection_model: BehaviorSelectionModel = attrs.field(
        factory=UnrestrictedBehavior,
        validator=attrs.validators.instance_of(BehaviorSelectionModel),
    )
    observers: tuple[Observer, ...] = ()
    telemetry_observers: tuple[TelemetryObserver, ...] = ()

    def __attrs_post_init__(self) -> None:
        if type(self.seed) is bool:
            raise TypeError("seed must be an integer or None, not a Boolean.")
        if not callable(getattr(self.step_coordinator, "coordinate", None)):
            raise TypeError(
                "step_coordinator must provide a callable coordinate method."
            )
        if not callable(getattr(self.stopping_condition, "should_stop", None)):
            raise TypeError(
                "stopping_condition must provide a callable should_stop method."
            )
        if type(self.observers) is not tuple:
            raise TypeError("observers must be a tuple.")
        if type(self.telemetry_observers) is not tuple:
            raise TypeError("telemetry_observers must be a tuple.")

    @classmethod
    def from_iterables(
        cls,
        *,
        initial_world_state: WorldState,
        genetic_architecture: GeneticArchitecture,
        step_coordinator: StepCoordinator,
        stopping_condition: StoppingCondition,
        seed: int | None = None,
        behavior_selection_model: BehaviorSelectionModel | None = None,
        observers: Iterable[Observer] = (),
        telemetry_observers: Iterable[TelemetryObserver] = (),
    ) -> BiologicalSimulationSpec:
        """Build a biological specification from observer iterables."""
        kwargs: dict[str, object] = {
            "initial_world_state": initial_world_state,
            "genetic_architecture": genetic_architecture,
            "step_coordinator": step_coordinator,
            "stopping_condition": stopping_condition,
            "seed": seed,
            "observers": tuple(observers),
            "telemetry_observers": tuple(telemetry_observers),
        }
        if behavior_selection_model is not None:
            kwargs["behavior_selection_model"] = behavior_selection_model
        return cls(**kwargs)  # type: ignore[arg-type]

    def compile(self) -> CompiledSimulation:
        """Run biological preflight, then delegate runtime compilation generically."""
        self._validate_initial_organisms()
        components: tuple[object, ...] = (
            self.step_coordinator,
            self.stopping_condition,
            self.behavior_selection_model,
            *self.observers,
            *self.telemetry_observers,
        )
        context = SimulationContext.from_mapping(
            {
                GENETIC_ARCHITECTURE.name: self.genetic_architecture,
                BEHAVIOR_SELECTION_MODEL.name: self.behavior_selection_model,
            }
        )
        generic_spec = SimulationSpec(
            initial_domain_state=self.initial_world_state,
            step_coordinator=self.step_coordinator,
            stopping_condition=self.stopping_condition,
            seed=self.seed,
            context=context,
            observers=self.observers,
            telemetry_observers=self.telemetry_observers,
            required_dependencies=collect_biological_dependencies(*components),
            provided_dependencies=provided_biological_dependencies(
                self.genetic_architecture,
                self.initial_world_state,
            ),
        )
        return generic_spec.compile()

    def _validate_initial_organisms(self) -> None:
        architecture = self.genetic_architecture
        for organism in self.initial_world_state.organisms.values():
            architecture.validate_genome(organism.genome)
            expected = architecture.express(organism.genome)
            if organism.genetic_phenotype != expected:
                raise ValueError(
                    f"Organism {organism.id} genetic phenotype is inconsistent "
                    "with its genome under the biological simulation specification's "
                    "genetic architecture."
                )
            organism.developmental_profile.validate_against(expected)


def collect_biological_dependencies(*components: object) -> frozenset[Dependency]:
    """Collect biological trait, characteristic, and environment dependencies."""
    dependencies: set[Dependency] = set()
    for component in iter_configuration_components(*components):
        _collect_biological_requirements(component, dependencies=dependencies)
    return frozenset(dependencies)


def provided_biological_dependencies(
    genetic_architecture: GeneticArchitecture,
    world: WorldState,
) -> frozenset[Dependency]:
    """Return dependencies supplied by a configured biological context."""
    provided: set[Dependency] = set()
    for trait_name in genetic_architecture.trait_names:
        provided.add(Dependency(category=TRAIT, name=trait_name))
        provided.add(Dependency(category=CHARACTERISTIC, name=trait_name))
    for field_name in world.environmental_field_names:
        provided.add(Dependency(category=ENVIRONMENTAL_FIELD, name=field_name))
    return frozenset(provided)


def _collect_biological_requirements(
    value: object,
    *,
    dependencies: set[Dependency],
) -> None:
    if isinstance(value, TraitRequirementProvider):
        dependencies.update(
            Dependency(category=TRAIT, name=name) for name in value.required_traits
        )
    if isinstance(value, CharacteristicRequirementProvider):
        dependencies.update(
            Dependency(category=CHARACTERISTIC, name=name)
            for name in value.required_characteristics
        )
    _collect_environmental_field_requirements(value, dependencies=dependencies)


def _collect_environmental_field_requirements(
    value: object,
    *,
    dependencies: set[Dependency],
) -> None:
    environmental_fields = getattr(value, "required_environmental_fields", None)
    if environmental_fields is None:
        return
    if type(environmental_fields) is not frozenset:
        raise TypeError(
            f"{type(value).__name__}.required_environmental_fields must be a frozenset."
        )
    dependencies.update(
        Dependency(category=ENVIRONMENTAL_FIELD, name=name)
        for name in environmental_fields
    )
