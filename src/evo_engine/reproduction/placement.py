"""Offspring-placement policies for reproduction."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world.organism import Organism


class OffspringPlacement(Protocol):
    """Define where a resolved reproductive event places its offspring."""

    def choose_location(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Choose the offspring's birth coordinate.

        Args:
            parents: One or more resolved reproductive parents.
            simulation_state: Current simulation state.
            rng: Simulation random-number generator.

        Returns:
            Horizontal and vertical birth coordinates.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class RandomParentLocation:
    """Place offspring at the location of a randomly selected parent."""

    def choose_location(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Choose one parent's current coordinate as the birth location.

        Args:
            parents: One or more resolved reproductive parents.
            simulation_state: Current simulation state.
            rng: Simulation random-number generator.

        Returns:
            Selected parent's horizontal and vertical coordinates.

        Raises:
            ValueError: If parents is empty.
        """
        if not parents:
            raise ValueError("parents must contain at least one organism.")

        parent = parents[0] if len(parents) == 1 else rng.choice(parents)

        return parent.x, parent.y
