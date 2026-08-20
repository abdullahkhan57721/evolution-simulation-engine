"""Represent mutable simulation run state."""

from __future__ import annotations

import copy
import random

import attrs

from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.validation import attrs_validators
from evo_engine.world.world_state import WorldState


@attrs.define(slots=True, kw_only=True)
class SimulationState:
    """Represent the mutable state and shared model of one simulation run.

    The genetic architecture is immutable shared configuration. Copies of the
    simulation state share that architecture while independently copying the
    mutable world and random-number-generator state.

    Attributes:
        world: Current state of the simulated world.
        genetic_architecture: Shared genotype-to-phenotype and mutation rules.
        step_index: Index of the current simulation step.
        rng: Random number generator for the simulation.
    """

    world: WorldState = attrs.field(
        validator=attrs.validators.instance_of(WorldState),
    )
    genetic_architecture: GeneticArchitecture = attrs.field(
        validator=attrs.validators.instance_of(GeneticArchitecture),
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

    def copy(self) -> SimulationState:
        """Return an independent transactional copy of the simulation state.

        The mutable world and RNG state are copied. The immutable genetic
        architecture is shared by reference.

        Returns:
            Independent working simulation state.
        """
        # World and RNG are transactional state: failed steps must be able
        # to discard both ecological mutations and consumed random draws.
        # GeneticArchitecture is frozen configuration, so sharing it is safe.
        return SimulationState(
            world=self.world.copy(),
            genetic_architecture=self.genetic_architecture,
            step_index=self.step_index,
            rng=copy.deepcopy(self.rng),
        )
