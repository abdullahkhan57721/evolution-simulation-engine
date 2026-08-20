"""Coordinate simulation steps by running stages sequentially."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.engine.stage_coordinator import StageCoordinator
from evo_engine.genetics.requirements import collect_required_traits


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
        """Coordinate one complete simulation step.

        Args:
            simulation_state: Current authoritative simulation state.

        Returns:
            Completed simulation state for the next step.
        """
        # Run the whole step against a transactional copy. If any stage
        # raises, the caller still owns the untouched authoritative state.
        working_state = simulation_state.copy()

        for stage in self.stages:
            stage.coordinate(
                simulation_state=working_state,
            )

        # A step counts as completed only after every stage succeeds.
        working_state.step_index += 1

        return working_state
