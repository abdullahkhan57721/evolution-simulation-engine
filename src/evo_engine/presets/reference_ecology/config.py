"""Configuration values for the complete reference ecology preset."""

from __future__ import annotations

import attrs

from evo_engine.genetics import (
    ADULT_BODY_MASS,
    ASSIMILATION_EFFICIENCY,
    ATTACK_STRENGTH,
    DEFENSE,
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    MATURITY_AGE,
    MAX_INTAKE_RATE,
    MAX_SPEED,
    MAXIMUM_AGE,
    OFFSPRING_ENERGY,
    REPRODUCTION_ENERGY_THRESHOLD,
    SENSORY_ACCURACY,
    SENSORY_RANGE,
)
from evo_engine.validation import attrs_validators, validators

REFERENCE_CHROMOSOME = "reference"
REFERENCE_TRAIT_DOMAINS: dict[str, tuple[int, int]] = {
    ADULT_BODY_MASS: (1, 40),
    MAX_SPEED: (0, 4),
    SENSORY_RANGE: (0, 20),
    SENSORY_ACCURACY: (0, 100),
    MAX_INTAKE_RATE: (0, 50),
    ASSIMILATION_EFFICIENCY: (0, 100),
    ENERGY_CONSERVATION_THRESHOLD: (0, 100),
    ENERGY_RESERVE: (0, 100),
    ATTACK_STRENGTH: (0, 50),
    DEFENSE: (0, 50),
    MATURITY_AGE: (0, 100),
    REPRODUCTION_ENERGY_THRESHOLD: (0, 200),
    OFFSPRING_ENERGY: (1, 50),
    MAXIMUM_AGE: (1, 200),
}


@attrs.frozen(slots=True, kw_only=True)
class ReferenceTraitValues:
    """Define founder values for the traits used by the reference ecology.

    These values initialize a homozygous founder population. Sexual inheritance,
    recombination, and mutation can subsequently create heritable variation.

    Attributes:
        adult_body_mass: Realized adult body-mass target.
        max_speed: Maximum Euclidean movement distance per timestep.
        sensory_range: Resource-detection radius.
        sensory_accuracy: Percentage probability of detecting each resource
            deposit inside sensory range.
        max_intake_rate: Maximum environmental resource units consumable per
            timestep.
        assimilation_efficiency: Percentage of consumed environmental resource
            converted to usable energy.
        energy_conservation_threshold: Energy below which nonessential behavior
            is suppressed and movement becomes food-seeking.
        energy_reserve: Energy protected from growth and reproduction spending.
        attack_strength: Predator performance used against prey defense.
        defense: Prey defensive performance opposed to predator attack.
        maturity_age: Age at reproductive maturity.
        reproduction_energy_threshold: Minimum current energy for reproduction.
        offspring_energy: Energy invested by each reproductive parent.
        maximum_age: Hard maximum completed age.
    """

    adult_body_mass: int = attrs.field(
        default=8,
        validator=attrs_validators.validate_int_in_range(1, 40),
    )
    max_speed: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_in_range(0, 4),
    )
    sensory_range: int = attrs.field(
        default=4,
        validator=attrs_validators.validate_int_in_range(0, 20),
    )
    sensory_accuracy: int = attrs.field(
        default=90,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    max_intake_rate: int = attrs.field(
        default=4,
        validator=attrs_validators.validate_int_in_range(0, 50),
    )
    assimilation_efficiency: int = attrs.field(
        default=75,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    energy_conservation_threshold: int = attrs.field(
        default=15,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    energy_reserve: int = attrs.field(
        default=5,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    attack_strength: int = attrs.field(
        default=8,
        validator=attrs_validators.validate_int_in_range(0, 50),
    )
    defense: int = attrs.field(
        default=5,
        validator=attrs_validators.validate_int_in_range(0, 50),
    )
    maturity_age: int = attrs.field(
        default=4,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    reproduction_energy_threshold: int = attrs.field(
        default=20,
        validator=attrs_validators.validate_int_in_range(0, 200),
    )
    offspring_energy: int = attrs.field(
        default=4,
        validator=attrs_validators.validate_int_in_range(1, 50),
    )
    maximum_age: int = attrs.field(
        default=30,
        validator=attrs_validators.validate_int_in_range(1, 200),
    )

    def as_mapping(self) -> dict[str, int]:
        """Return founder trait values keyed by canonical trait name.

        Returns:
            Mapping used to build founder alleles.
        """
        return {
            ADULT_BODY_MASS: self.adult_body_mass,
            MAX_SPEED: self.max_speed,
            SENSORY_RANGE: self.sensory_range,
            SENSORY_ACCURACY: self.sensory_accuracy,
            MAX_INTAKE_RATE: self.max_intake_rate,
            ASSIMILATION_EFFICIENCY: self.assimilation_efficiency,
            ENERGY_CONSERVATION_THRESHOLD: self.energy_conservation_threshold,
            ENERGY_RESERVE: self.energy_reserve,
            ATTACK_STRENGTH: self.attack_strength,
            DEFENSE: self.defense,
            MATURITY_AGE: self.maturity_age,
            REPRODUCTION_ENERGY_THRESHOLD: self.reproduction_energy_threshold,
            OFFSPRING_ENERGY: self.offspring_energy,
            MAXIMUM_AGE: self.maximum_age,
        }


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcologyConfig:
    """Define the numerical baseline for the reference ecology.

    The defaults are deliberately modest and transparent rather than intended
    as calibrated biological claims. The reference ecology is an integration
    baseline for experiments and examples; callers should replace parameter
    values for substantive scientific work.

    Attributes:
        width: World width in grid cells.
        height: World height in grid cells.
        initial_population: Number of homozygous founders.
        initial_energy: Initial founder energy.
        max_steps: Number of timesteps run by the reference engine.
        seed: Simulation random seed.
        traits: Founder life-history and ecological trait values.
        mutation_probability_ppm: Per-transmitted-allele mutation probability.
        mutation_max_change: Maximum absolute integer mutation step.
        recombination_probability_ppm: Single-crossover probability per meiosis.
        resource_generation_amount: Resource units per generated deposit.
        resource_deposits_per_step: Number of deposits generated each timestep.
        decomposition_amount: Maximum carcass units decomposed per timestep.
        resource_request_amount: Behavioral resource demand before an
            organism-specific intake-capacity ceiling is applied.
        metabolic_coefficient: Basal metabolic allometry coefficient.
        metabolic_mass_exponent: Basal metabolic body-mass exponent.
        locomotion_coefficient: Locomotion cost coefficient.
        locomotion_mass_exponent: Locomotion body-mass exponent.
        locomotion_distance_exponent: Locomotion distance exponent.
        growth_amount_per_step: Potential body-mass gain per timestep.
        growth_energy_per_mass: Energy cost per gained body-mass unit.
        predation_radius: Chebyshev radius for predation interactions.
        predation_consumption_percent: Percentage of prey biomass converted
            directly to predator energy.
        mating_radius: Maximum Chebyshev distance for candidate mates.
        newborn_mass_numerator: Numerator of newborn/adult body-mass fraction.
        newborn_mass_denominator: Denominator of newborn/adult body-mass fraction.
    """

    width: int = attrs.field(
        default=12,
        validator=attrs_validators.validate_int_ge(1),
    )
    height: int = attrs.field(
        default=12,
        validator=attrs_validators.validate_int_ge(1),
    )
    initial_population: int = attrs.field(
        default=20,
        validator=attrs_validators.validate_int_ge(1),
    )
    initial_energy: int = attrs.field(
        default=30,
        validator=attrs_validators.validate_int_ge(0),
    )
    max_steps: int = attrs.field(
        default=50,
        validator=attrs_validators.validate_int_ge(1),
    )
    seed: int = attrs.field(
        default=42,
        validator=attrs_validators.validate_int,
    )
    traits: ReferenceTraitValues = attrs.field(
        factory=ReferenceTraitValues,
        validator=attrs.validators.instance_of(ReferenceTraitValues),
    )
    mutation_probability_ppm: int = attrs.field(
        default=10_000,
        validator=attrs_validators.validate_int_in_range(0, 1_000_000),
    )
    mutation_max_change: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    recombination_probability_ppm: int = attrs.field(
        default=500_000,
        validator=attrs_validators.validate_int_in_range(0, 1_000_000),
    )
    resource_generation_amount: int = attrs.field(
        default=6,
        validator=attrs_validators.validate_int_ge(1),
    )
    resource_deposits_per_step: int = attrs.field(
        default=8,
        validator=attrs_validators.validate_int_ge(1),
    )
    decomposition_amount: int = attrs.field(
        default=2,
        validator=attrs_validators.validate_int_ge(0),
    )
    resource_request_amount: int = attrs.field(
        default=10,
        validator=attrs_validators.validate_int_ge(0),
    )
    metabolic_coefficient: int | float = 0.30
    metabolic_mass_exponent: int | float = 0.75
    locomotion_coefficient: int | float = 0.20
    locomotion_mass_exponent: int | float = 0.50
    locomotion_distance_exponent: int | float = 1.0
    growth_amount_per_step: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    growth_energy_per_mass: int | float = 2.0
    predation_radius: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    predation_consumption_percent: int = attrs.field(
        default=75,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    mating_radius: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    newborn_mass_numerator: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    newborn_mass_denominator: int = attrs.field(
        default=4,
        validator=attrs_validators.validate_int_ge(1),
    )

    def __attrs_post_init__(self) -> None:
        """Validate cross-field and finite-number configuration invariants."""
        if self.initial_population > self.width * self.height:
            raise ValueError(
                "initial_population must not exceed the number of world cells."
            )

        if self.newborn_mass_numerator > self.newborn_mass_denominator:
            raise ValueError(
                "newborn_mass_numerator must be less than or equal to "
                "newborn_mass_denominator."
            )

        for name in (
            "metabolic_coefficient",
            "locomotion_coefficient",
            "growth_energy_per_mass",
        ):
            validators.validate_number_ge(
                getattr(self, name),
                bound=0,
                name=name,
            )

        for name in (
            "metabolic_mass_exponent",
            "locomotion_mass_exponent",
            "locomotion_distance_exponent",
        ):
            validators.validate_number(
                getattr(self, name),
                name=name,
            )


def resolve_reference_config(
    config: ReferenceEcologyConfig | None,
) -> ReferenceEcologyConfig:
    """Return a validated explicit reference configuration.

    Args:
        config: Optional reference configuration.

    Returns:
        Supplied configuration or a new default configuration.

    Raises:
        TypeError: If config is not a ReferenceEcologyConfig.
    """
    if config is None:
        return ReferenceEcologyConfig()

    if not isinstance(config, ReferenceEcologyConfig):
        raise TypeError("config must be an instance of ReferenceEcologyConfig.")

    return config
