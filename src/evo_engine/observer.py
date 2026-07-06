from __future__ import annotations

from evo_engine.observation import Observation

# Imports for type hints.
from evo_engine.world_state import WorldState
from evo_engine.event import Event


class Observer:
	def should_observe(
		self,
		world_state: WorldState,
		proposed_events: list[Event],
		resolved_events: list[Event],
		stage_name: str,
	) -> bool:
		return True
	
	def observe(
		self,
		world_state: WorldState,
		proposed_events: list[Event],
		resolved_events: list[Event],
		stage_name: str,
	) -> Observation:
		population_size = 0
		
		# NTS: create population_size method within WorldState later
		for organism in world_state.organisms:
			if organism.is_alive:
				population_size += 1
				
		return Observation(
			time_step=world_state.time_step,
			stage_name=stage_name,
			population_size=population_size,
			moment=f"after {stage_name}"
		)