"""Represent a simulation and its stateful objects."""

from __future__ import annotations

import random

from evo_engine.behavior import BehaviorSelectionModel, UnrestrictedBehavior
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.world.world_state import WorldState


class Simulation:
    """Represent one simulation and its stateful objects."""

    def __init__(
        self,
        initial_world_state: WorldState,
        genetic_architecture: GeneticArchitecture,
        seed: int | None = None,
        behavior_selection_model: BehaviorSelectionModel | None = None,
    ) -> None:
        """Initialize a simulation.

        Args:
            initial_world_state: Initial state of the simulated world.
            genetic_architecture: Shared genetic architecture for the run.
            seed: Seed for the simulation random number generator.
            behavior_selection_model: Policy deciding whether organisms attempt
                behavioral purposes. Defaults to unrestricted behavior.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If an initial organism's genetic phenotype is inconsistent
                with its genome under the supplied genetic architecture.
        """
        if not isinstance(initial_world_state, WorldState):
            raise TypeError("initial_world_state must be an instance of WorldState.")

        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be an instance of GeneticArchitecture."
            )

        if behavior_selection_model is None:
            behavior_selection_model = UnrestrictedBehavior()
        elif not isinstance(behavior_selection_model, BehaviorSelectionModel):
            raise TypeError(
                "behavior_selection_model must satisfy BehaviorSelectionModel."
            )

        # The caller's initial world is treated as input, not as the
        # simulation's authoritative mutable state.
        world = initial_world_state.copy()

        # Genetic phenotype is cached on each organism for fast ecological access.
        # Validate the cache once at the simulation boundary so processes can
        # trust it for the rest of the run.
        for organism in world.organisms.values():
            expected_genetic_phenotype = genetic_architecture.express(organism.genome)

            if organism.genetic_phenotype != expected_genetic_phenotype:
                raise ValueError(
                    f"Organism {organism.id} genetic phenotype is inconsistent "
                    "with its genome under the simulation's genetic "
                    "architecture."
                )

        self.state = SimulationState(
            world=world,
            genetic_architecture=genetic_architecture,
            behavior_selection_model=behavior_selection_model,
            rng=random.Random(seed),
        )

    @property
    def genetic_architecture(self) -> GeneticArchitecture:
        """Return the simulation's shared genetic architecture.

        Returns:
            Shared genetic architecture.
        """
        return self.state.genetic_architecture
