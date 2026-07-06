from dataclasses import dataclass


@dataclass(frozen=True) 
class Observation:
	""" Because an observation is a snapshot that shouldn't be tampered with """
	
	time_step: int
	stage_name: str | None
	population_size: int
	moment: str