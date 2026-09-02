"""Offspring-production source selection for biological reproduction."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world.organism import Organism


class OffspringProductionSourceSelection(Protocol):
    """Choose reproductive participants supplied as offspring-production context."""

    def select_sources(
        self,
        participants: tuple[Organism, ...],
        *,
        genetic_contributors: tuple[Organism, ...],
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return ordered production sources drawn from reproductive participants.

        Selection occurs only during event materialization so accepted-event
        production context may use the simulation-owned RNG without rejected
        reproductive candidates consuming stochastic state.

        Args:
            participants: Resolved reproductive participants in group order.
            genetic_contributors: Resolved genetic contributors in inheritance order.
            simulation_state: Current pre-application simulation state.
            rng: Simulation-owned random-number generator.

        Returns:
            Ordered production sources. The reproduction process validates that the
            tuple is unique and contains only participants. An empty tuple is valid
            at this shared boundary because generic entity production permits zero
            or more source entities; concrete source-dependent production policies
            may impose stronger requirements.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AllParticipantsAsProductionSources:
    """Use every reproductive participant as offspring-production context."""

    def select_sources(
        self,
        participants: tuple[Organism, ...],
        *,
        genetic_contributors: tuple[Organism, ...],
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return all participants in their existing order."""
        return participants
