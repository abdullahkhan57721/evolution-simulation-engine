"""Capacity-aware preference resolver for Reproduction proposals."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.processes.reproduction import Reproduction
from evo_engine.resolvers._preference_order import resolve_capacity_preference_order
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class CapacityPreferenceOrder:
    """Resolve preferred matings subject to per-parent stage capacity.

    Higher-preference proposals are considered first and proposal order breaks
    ties. A proposal is accepted only when every participating parent has been
    used fewer than ``max_events_per_parent`` times in the resolved set.

    ``max_events_per_parent=1`` reproduces exclusive-parent resolution. Larger
    capacities permit mating systems in which an individual may participate in
    multiple successful reproductive events during one lifecycle stage.

    The greedy capacity algorithm itself is domain-neutral; this adapter only
    maps Reproduction proposal preference and parent references into that
    generic conflict-resolution primitive.

    Attributes:
        max_events_per_parent: Maximum accepted reproductive events involving
            any one parent in the stage.
    """

    max_events_per_parent: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[Reproduction.Proposal]:
        """Return preferred proposals that fit every parent's stage capacity."""
        return resolve_capacity_preference_order(
            proposed_events,
            event_type=Reproduction.Proposal,
            preference_score=lambda proposal: proposal.preference_score,
            participant_keys=lambda proposal: proposal.parent_ids,
            max_events_per_key=self.max_events_per_parent,
            resolver_name=type(self).__name__,
        )
