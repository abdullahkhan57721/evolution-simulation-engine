"""Feeding physiology models for intake capacity and energy assimilation."""

from evo_engine.feeding.assimilation import (
    AssimilationModel,
    FixedAssimilationEfficiency,
    FullAssimilation,
    GeneticPhenotypeAssimilationEfficiency,
    determine_assimilated_energy,
)
from evo_engine.feeding.intake import (
    FixedIntakeCapacity,
    GeneticPhenotypeIntakeCapacity,
    IntakeCapacityModel,
    determine_intake_capacity,
)

__all__ = [
    "AssimilationModel",
    "FixedAssimilationEfficiency",
    "FixedIntakeCapacity",
    "FullAssimilation",
    "GeneticPhenotypeAssimilationEfficiency",
    "GeneticPhenotypeIntakeCapacity",
    "IntakeCapacityModel",
    "determine_assimilated_energy",
    "determine_intake_capacity",
]
