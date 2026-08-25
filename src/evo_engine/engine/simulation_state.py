"""Represent mutable simulation run state."""

from __future__ import annotations

import copy
import random

import attrs

from evo_engine.behavior import BehaviorSelectionModel, UnrestrictedBehavior
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.telemetry import StepTelemetry
from evo_engine.validation import attrs_validators
from evo_engine.world.world_state import WorldState


@attrs.define(slots=True, kw_only=True)
class SimulationState:
    """Represent the mutable state and shared models of one simulation run.

    Genetic architecture and behavior selection are shared simulation
    configuration. Copies share those models while independently copying the
    mutable world and random-number-generator state. ``last_step_telemetry`` is
    populated only after a complete transactional step succeeds.

    Attributes:
        world: Current state of the simulated world.
        genetic_architecture: Shared genotype-to-phenotype and mutation rules.
        behavior_selection_model: Shared policy deciding whether organisms
            attempt behavioral purposes.
        step_index: Index of the current simulation state.
        rng: Random number generator for the simulation.
        last_step_telemetry: Telemetry for the most recently committed step.
    """

    world: WorldState = attrs.field(
        validator=attrs.validators.instance_of(WorldState),
    )
    genetic_architecture: GeneticArchitecture = attrs.field(
        validator=attrs.validators.instance_of(GeneticArchitecture),
        on_setattr=attrs.setters.frozen,
    )
    behavior_selection_model: BehaviorSelectionModel = attrs.field(
        factory=UnrestrictedBehavior,
        validator=attrs.validators.instance_of(BehaviorSelectionModel),
        on_setattr=attrs.setters.frozen,
    )
    step_index: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    rng: random.Random = attrs.field(
        factory=random.Random,
        validator=attrs.validators.instance_of(random.Random),
        repr=False,
    )
    last_step_telemetry: StepTelemetry | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(StepTelemetry)),
    )

    def copy(self) -> SimulationState:
        """Return an independent transactional copy of the simulation state.

        Mutable world and RNG state are copied. Shared immutable/pure
        configuration is retained by reference. Previous committed telemetry is
        intentionally not copied into the new working transaction.

        Returns:
            Independent working simulation state.
        """
        return SimulationState(
            world=self.world.copy(),
            genetic_architecture=self.genetic_architecture,
            behavior_selection_model=self.behavior_selection_model,
            step_index=self.step_index,
            rng=copy.deepcopy(self.rng),
            last_step_telemetry=None,
        )
