"""Canonical names for commonly modeled heritable genetic phenotype traits.

These constants provide a shared vocabulary for built-in engine policies. They
are plain strings rather than an enum so simulations remain free to introduce
custom traits without modifying the engine.
"""

# Morphology
ADULT_BODY_MASS = "adult_body_mass"

# Locomotion
MAX_SPEED = "max_speed"
ENDURANCE = "endurance"

# Sensory systems
SENSORY_RANGE = "sensory_range"
SENSORY_ACCURACY = "sensory_accuracy"

# Energetics and feeding
ASSIMILATION_EFFICIENCY = "assimilation_efficiency"
METABOLIC_EFFICIENCY = "metabolic_efficiency"
MAX_INTAKE_RATE = "max_intake_rate"

# Predation and defense
ATTACK_STRENGTH = "attack_strength"
DEFENSE = "defense"

# Life history
MATURITY_AGE = "maturity_age"
REPRODUCTION_ENERGY_THRESHOLD = "reproduction_energy_threshold"
OFFSPRING_ENERGY = "offspring_energy"
OFFSPRING_COUNT = "offspring_count"
MAXIMUM_AGE = "maximum_age"

# Mating and sexual selection
MATE_SEARCH_RANGE = "mate_search_range"
CHOOSINESS = "choosiness"
MATING_SIGNAL = "mating_signal"

# Disease ecology
DISEASE_RESISTANCE = "disease_resistance"

# Environmental adaptation
TEMPERATURE_OPTIMUM = "temperature_optimum"
TEMPERATURE_TOLERANCE = "temperature_tolerance"

BUILTIN_TRAITS = frozenset(
    {
        ADULT_BODY_MASS,
        MAX_SPEED,
        ENDURANCE,
        SENSORY_RANGE,
        SENSORY_ACCURACY,
        ASSIMILATION_EFFICIENCY,
        METABOLIC_EFFICIENCY,
        MAX_INTAKE_RATE,
        ATTACK_STRENGTH,
        DEFENSE,
        MATURITY_AGE,
        REPRODUCTION_ENERGY_THRESHOLD,
        OFFSPRING_ENERGY,
        OFFSPRING_COUNT,
        MAXIMUM_AGE,
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
        DISEASE_RESISTANCE,
        TEMPERATURE_OPTIMUM,
        TEMPERATURE_TOLERANCE,
    }
)
