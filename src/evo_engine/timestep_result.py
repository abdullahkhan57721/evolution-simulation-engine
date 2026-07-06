from __future__ import annotations

from dataclasses import dataclass

# Imports for type hints:
from evo_engine.world_state import WorldState
from evo_engine.history import History

@dataclass
class TimestepResult:
	updated_world_state: WorldState
	updated_history: History