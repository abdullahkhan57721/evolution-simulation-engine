"""Stopping conditions for simulations."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class MaxSteps:
    """Stop a simulation after a maximum number of steps.

    Attributes:
        max_steps: Maximum number of completed simulation steps.
    """

    max_steps: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def should_stop(
        self,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the maximum number of steps is reached.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Whether the simulation should stop.
        """
        return simulation_state.step_index >= self.max_steps
