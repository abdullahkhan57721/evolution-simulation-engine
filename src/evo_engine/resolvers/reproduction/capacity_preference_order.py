"""Capacity-aware preference resolver for Reproduction proposals."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.processes.reproduction import Reproduction
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
        proposals: list[tuple[int, Reproduction.Proposal]] = []
        for index, event in enumerate(proposed_events):
            if not isinstance(event, Reproduction.Proposal):
                raise TypeError(
                    f"{type(self).__name__} requires Reproduction.Proposal events."
                )
            proposals.append((index, event))

        proposals.sort(key=lambda indexed: (-indexed[1].preference_score, indexed[0]))
        accepted: list[Reproduction.Proposal] = []
        counts: dict[int, int] = {}
        for _, proposal in proposals:
            if any(
                counts.get(parent_id, 0) >= self.max_events_per_parent
                for parent_id in proposal.parent_ids
            ):
                continue
            accepted.append(proposal)
            for parent_id in proposal.parent_ids:
                counts[parent_id] = counts.get(parent_id, 0) + 1
        return accepted
