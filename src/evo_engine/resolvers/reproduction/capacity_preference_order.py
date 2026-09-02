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
    """Resolve preferred matings subject to per-participant stage capacity.

    Higher-preference proposals are considered first and proposal order breaks
    ties. A proposal is accepted only when every reproductive participant has
    been used fewer than ``max_events_per_participant`` times in the resolved set.

    ``max_events_per_participant=1`` reproduces exclusive-participant resolution.
    Larger capacities permit mating systems in which an individual may participate
    in multiple successful reproductive events during one lifecycle stage.

    Genetic contribution is intentionally irrelevant to resolver capacity. This
    adapter maps proposal preference and participant references into the generic
    capacity-resolution primitive before contributor selection occurs.

    Attributes:
        max_events_per_participant: Maximum accepted reproductive events involving
            any one participant in the stage.
    """

    max_events_per_participant: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[Reproduction.Proposal]:
        """Return preferred proposals that fit every participant's stage capacity."""
        return resolve_capacity_preference_order(
            proposed_events,
            event_type=Reproduction.Proposal,
            preference_score=lambda proposal: proposal.preference_score,
            participant_keys=lambda proposal: proposal.participant_ids,
            max_events_per_key=self.max_events_per_participant,
            resolver_name=type(self).__name__,
        )
