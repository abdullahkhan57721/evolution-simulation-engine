from __future__ import annotations

from dataclasses import dataclass

# Imports for type hints:
from evo_engine.observation import Observation

@dataclass	
class History:
	observations: list[Observation]
	
	def copy(self) -> History:
		copied_observations = [
			Observation(
				time_step=observation.time_step,
				stage_name=observation.stage_name,
				population_size=observation.population_size,
				moment=observation.moment,
			)
			for observation in self.observations
		]
		# Because each of the observations are immutable, there is no risk
		# of accidentally mutating them while mutating the copy. So,
		# return(History(observations=self.observations.copy())) will suffice. 
		
		return History(observations=copied_observations)
	
	# may not be needed
	def add(self, observation: Observation,) -> None:
		self.observations.append(observation)
	
	#may not be needed	
	def add_many(self, observations: list[Observation],) -> None:
		self.observations.extend(observations)