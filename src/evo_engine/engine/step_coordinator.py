"""Coordinate simulation steps by running stages sequentially."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.engine.stage_coordinator import StageCoordinator
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.telemetry import AppliedEvent, StepTelemetry


class SequentialStepCoordinator:
    """Coordinate simulation steps by running stages sequentially."""

    def __init__(
        self,
        stages: Sequence[StageCoordinator],
    ) -> None:
        """Initialize the sequential step coordinator.

        Args:
            stages: Ordered simulation update stages.
        """
        self.stages = tuple(stages)
        self.required_traits = collect_required_traits(*self.stages)

    def coordinate(
        self,
        simulation_state: SimulationState,
    ) -> SimulationState:
        """Coordinate one complete transactional simulation step.

        Args:
            simulation_state: Current authoritative simulation state.

        Returns:
            Completed state containing telemetry for the committed step.
        """
        working_state = simulation_state.copy()
        applied_events: list[AppliedEvent] = []

        for stage_index, stage in enumerate(self.stages):
            stage_events = stage.coordinate(
                simulation_state=working_state,
            )
            if stage_events is None:
                continue

            applied_events.extend(
                attrs.evolve(event, stage_index=stage_index)
                for event in stage_events
            )

        working_state.step_index += 1
        working_state.last_step_telemetry = StepTelemetry(
            completed_step_index=working_state.step_index,
            events=tuple(applied_events),
        )

        return working_state
