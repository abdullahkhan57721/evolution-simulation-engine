from __future__ import annotations

from dataclasses import dataclass

from evo_engine.organism import Organism

@dataclass
class WorldState:
	time_step: int
	organisms: list[Organism]
	
	def copy(self) -> WorldState:
		copied_organisms = [
			Organism(
				id=organism.id,
				age=organism.age,
				is_alive=organism.is_alive,
			)
			for organism in self.organisms
		]
		
		# This is to ensure that the copied WorldState doesn't have the same
		# organisms as the original WorldState, so that changing organisms
		# in one WorldState doesn't change it in the other WorldState.
		# Integers like time_step are not subject to this.
		
		return WorldState(
			time_step=self.time_step, 
			organisms=copied_organisms)
		
	def advance_time(self) -> None:
		self.time_step += 1