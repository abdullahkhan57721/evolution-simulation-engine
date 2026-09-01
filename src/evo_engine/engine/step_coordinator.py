"""Coordinate simulation steps by running stages sequentially."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.engine.stage_coordinator import StageCoordinator
from evo_engine.telemetry import AppliedEvent, StepTelemetry


class SequentialStepCoordinator:
    """Coordinate transactional simulation steps through ordered stages."""

    def __init__(
        self,
        stages: Sequence[StageCoordinator],
    ) -> None:
        """Initialize the sequential step coordinator.

        Args:
            stages: Ordered domain-defined update stages.
        """
        self.stages = tuple(stages)

    def coordinate(
        self,
        simulation_state: SimulationState,
    ) -> SimulationState:
        """Coordinate one complete transactional simulation step.

        The authoritative input is copied before any stage executes. If a stage
        raises, the caller retains the original state and RNG stream unchanged.

        Args:
            simulation_state: Current authoritative simulation state.

        Returns:
            Completed working state containing telemetry for the committed step.
        """
        working_state = simulation_state.copy()
        applied_events: list[AppliedEvent] = []

        for stage_index, stage in enumerate(self.stages):
            stage_events = stage.coordinate(
                simulation_state=working_state,
                stage_index=stage_index,
            )
            applied_events.extend(stage_events)

        working_state.step_index += 1
        working_state.last_step_telemetry = StepTelemetry._from_kernel_values(
            completed_step_index=working_state.step_index,
            events=tuple(applied_events),
        )

        return working_state
