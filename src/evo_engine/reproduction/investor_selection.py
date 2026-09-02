"""Reproductive-investor selection for biological reproduction."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world.organism import Organism


class ReproductiveInvestorSelection(Protocol):
    """Choose which reproductive participants invest offspring energy."""

    def select_investors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return ordered investors drawn from reproductive participants.

        Investor selection occurs during proposal generation because affordability
        determines whether the candidate reproductive event may be proposed. The
        contract therefore intentionally has no RNG parameter: rejected candidates
        must not consume stochastic investor-selection randomness.

        Args:
            participants: Candidate reproductive participants in group order.
            simulation_state: Current simulation state.

        Returns:
            Ordered reproductive investors. The reproduction process validates that
            the tuple is nonempty, unique, and contains only participants.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AllParticipantsInvest:
    """Use every reproductive participant as an energy investor."""

    def select_investors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return all participants in their existing order."""
        return participants
