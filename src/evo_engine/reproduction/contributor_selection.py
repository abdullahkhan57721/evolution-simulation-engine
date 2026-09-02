"""Genetic-contributor selection for biological reproduction."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world.organism import Organism


class GeneticContributorSelection(Protocol):
    """Choose which reproductive participants contribute transmissible state."""

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return ordered genetic contributors drawn from the participants.

        Contributor selection occurs only during event materialization so rejected
        reproductive candidates cannot consume stochastic selection RNG.

        Args:
            participants: Resolved reproductive participants in group order.
            simulation_state: Current pre-application simulation state.
            rng: Simulation-owned random-number generator.

        Returns:
            Ordered genetic contributors. The reproduction process validates that
            the tuple is nonempty, unique, and contains only participants.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AllParticipantsContribute:
    """Use every reproductive participant as a genetic contributor."""

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return all participants in their existing order."""
        return participants
