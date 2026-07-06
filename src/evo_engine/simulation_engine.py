from __future__ import annotations

from dataclasses import dataclass

from evo_engine.world_state import WorldState
from evo_engine.stopping_condition import StoppingCondition
from evo_engine.timestep_coordinator import TimestepCoordinator
from evo_engine.history import History

# Imports for type hints.
from evo_engine.timestep_result import TimestepResult


@dataclass
class SimulationEngine:
	world_state: WorldState 
	stopping_condition: StoppingCondition
	timestep_coordinator: TimestepCoordinator
	history: History

	def run(self) -> History:
		"""Runs simulation until stopping condition is met."""
		
		while not self.stopping_condition.is_met(
			world_state=self.world_state,
			history=self.history,
		):
			timestep_result: TimestepResult = self.timestep_coordinator.coordinate(
				world_state=self.world_state,
				history=self.history,
			)
			
			# SimulationEngine updates world_state and history because it owns them.
			self.world_state = timestep_result.updated_world_state
			self.history = timestep_result.updated_history
		
		return self.history