from __future__ import annotations

# Imports for type hints.
from evo_engine.event import Event
from evo_engine.world_state import WorldState
from evo_engine.history import History


class EventsResolver:
	def resolve(
		self,
		proposed_events: list[Event],
		world_state: WorldState,
		history: History,
	) -> list[Event]:
		resolved_events: list[Event] = proposed_events
		
		return resolved_events