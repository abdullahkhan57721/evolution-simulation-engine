from __future__ import annotations

from evo_engine.event import AgingEvent

#Imports for type hints.
from evo_engine.event import Event
from evo_engine.world_state import WorldState


class StateUpdater:
	def apply(
		self,
		events: list[Event],
		world_state: WorldState,
	) -> WorldState:
		working_state = world_state.copy()
		
		for event in events:
			if isinstance(event, AgingEvent):
				# NTS: create a get_organism(organism_id) method within WorldState.
				# NTS: create helper methods for each kind of event
				# NTS: replace if/elif chain with a dispatch dictionary in the future
				for organism in working_state.organisms:
					if organism.id == event.organism_id:
						organism.age += event.amount
						break
		
		return working_state