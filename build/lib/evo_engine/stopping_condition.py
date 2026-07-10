from __future__ import annotations

from dataclasses import dataclass

from evo_engine.history import History

# Imports for type hints:
from evo_engine.world_state import WorldState


@dataclass
class StoppingCondition:
    max_time_steps: int = 10

    def is_met(
        self,
        world_state: WorldState,
        history: History,
    ) -> bool:
        return world_state.time_step >= self.max_time_steps
