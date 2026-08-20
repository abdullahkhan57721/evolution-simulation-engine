"""Simulation processes."""

from evo_engine.processes.aging import Aging
from evo_engine.processes.decomposition import Decomposition
from evo_engine.processes.growth import Growth
from evo_engine.processes.metabolism import Metabolism
from evo_engine.processes.movement import Movement
from evo_engine.processes.predation import Predation
from evo_engine.processes.reproduction import Reproduction
from evo_engine.processes.resource_consumption import ResourceConsumption
from evo_engine.processes.resource_generation import ResourceGeneration
from evo_engine.processes.starvation import Starvation

__all__ = [
    "Aging",
    "Decomposition",
    "Growth",
    "Metabolism",
    "Movement",
    "Predation",
    "Reproduction",
    "ResourceConsumption",
    "ResourceGeneration",
    "Starvation",
]
