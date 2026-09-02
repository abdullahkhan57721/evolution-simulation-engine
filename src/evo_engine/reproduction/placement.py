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
        source_entities: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Choose the offspring's birth coordinate.

        Args:
            source_entities: Biological offspring-production source organisms.
            simulation_state: Current simulation state.
            rng: Simulation random-number generator.

        Returns:
            Horizontal and vertical birth coordinates.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class RandomProductionSourceLocation:
    """Place offspring at the location of a randomly selected production source."""

    def choose_location(
        self,
        source_entities: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Choose one production source's current coordinate as the birth location.

        Args:
            source_entities: Biological offspring-production source organisms.
            simulation_state: Current simulation state.
            rng: Simulation random-number generator.

        Returns:
            Selected source organism's horizontal and vertical coordinates.

        Raises:
            ValueError: If ``source_entities`` is empty.
        """
        if not source_entities:
            raise ValueError("source_entities must contain at least one organism.")

        source = (
            source_entities[0]
            if len(source_entities) == 1
            else rng.choice(source_entities)
        )

        return source.x, source.y
