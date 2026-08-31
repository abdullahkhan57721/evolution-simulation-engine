"""Preference-order Reproduction resolver."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.processes.reproduction import Reproduction
from evo_engine.resolvers._preference_order import (
    resolve_exclusive_preference_order,
)


class PreferenceOrder:
    """Resolve Reproduction proposals by preference with exclusive parents."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[Reproduction.Proposal]:
        """Resolve competing Reproduction proposals.

        Higher preference scores are considered first. An organism may
        contribute to at most one resolved reproductive proposal in the stage.
        Proposal order breaks preference ties.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            Compatible resolved Reproduction proposals.
        """
        return resolve_exclusive_preference_order(
            proposed_events,
            event_type=Reproduction.Proposal,
            preference_score=lambda proposal: proposal.preference_score,
            participant_keys=lambda proposal: proposal.parent_ids,
            resolver_name=type(self).__name__,
        )
