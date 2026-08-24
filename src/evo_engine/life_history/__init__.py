"""Life-history strategy models shared across simulation domains."""

from evo_engine.life_history.energy_thresholds import (
    DevelopmentalEnergyThreshold,
    EnergyThresholdModel,
    EnergyThresholdSource,
    FixedEnergyThreshold,
    determine_energy_threshold,
    validate_energy_threshold_source,
)
from evo_engine.life_history.lifespan import (
    DevelopmentalMaximumAge,
    FixedMaximumAge,
    MaximumAgeModel,
    MaximumAgeSource,
    determine_maximum_age,
    validate_maximum_age_source,
)

__all__ = [
    "DevelopmentalEnergyThreshold",
    "DevelopmentalMaximumAge",
    "EnergyThresholdModel",
    "EnergyThresholdSource",
    "FixedEnergyThreshold",
    "FixedMaximumAge",
    "MaximumAgeModel",
    "MaximumAgeSource",
    "determine_energy_threshold",
    "determine_maximum_age",
    "validate_energy_threshold_source",
    "validate_maximum_age_source",
]
