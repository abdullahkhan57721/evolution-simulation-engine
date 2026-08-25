"""Configuration values for the complete reference ecology preset."""

from __future__ import annotations

import attrs

from evo_engine.genetics import (
    ADULT_BODY_MASS,
    ASSIMILATION_EFFICIENCY,
    ATTACK_STRENGTH,
    CHOOSINESS,
    DEFENSE,
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    GROWTH_RATE,
    LOCOMOTION_COST_COEFFICIENT,
    MATE_SEARCH_RANGE,
    MATING_SIGNAL,
    MATURITY_AGE,
    MAX_INTAKE_RATE,
    MAX_SPEED,
    MAXIMUM_AGE,
    METABOLIC_COST_COEFFICIENT,
    OFFSPRING_ENERGY,
    REPRODUCTION_ENERGY_THRESHOLD,
    SENSORY_ACCURACY,
    SENSORY_RANGE,
)
from evo_engine.presets.reference_ecology.reproductive_investment import (
    ReferenceMatingTypeInvestmentScales,
)
from evo_engine.validation import attrs_validators, validators

REFERENCE_CHROMOSOME = "reference"
REFERENCE_TRAIT_DOMAINS: dict[str, tuple[int, int]] = {
    ADULT_BODY_MASS: (1, 40),
    GROWTH_RATE: (0, 4),
    MAX_SPEED: (0, 4),
    LOCOMOTION_COST_COEFFICIENT: (0, 200),
    SENSORY_RANGE: (0, 20),
    SENSORY_ACCURACY: (0, 100),
    MAX_INTAKE_RATE: (0, 50),
    ASSIMILATION_EFFICIENCY: (0, 100),
    METABOLIC_COST_COEFFICIENT: (0, 200),
    ENERGY_CONSERVATION_THRESHOLD: (0, 100),
    ENERGY_RESERVE: (0, 100),
    ATTACK_STRENGTH: (0, 50),
    DEFENSE: (0, 50),
    MATE_SEARCH_RANGE: (0, 20),
    CHOOSINESS: (0, 50),
    MATING_SIGNAL: (0, 50),
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

    Energetic cost coefficients are stored as integer hundredths so the genetic
    architecture remains integer-valued while cost models can use fractional
    coefficients. For example, ``metabolic_cost_coefficient=30`` represents
    ``0.30`` after scaling by 100.

    Attributes:
        adult_body_mass: Realized adult body-mass target.
        growth_rate: Potential body-mass units gained per growth timestep.
        max_speed: Maximum Euclidean movement distance per timestep.
        locomotion_cost_coefficient: Hundredths of the locomotion power-law
            coefficient used by each organism.
        sensory_range: Resource-detection radius.
        sensory_accuracy: Percentage probability of detecting each resource
            deposit inside sensory range.
        max_intake_rate: Maximum environmental resource units consumable per
            timestep.
        assimilation_efficiency: Percentage of consumed environmental resource
            converted to usable energy.
        metabolic_cost_coefficient: Hundredths of the basal metabolic power-law
            coefficient used by each organism.
        energy_conservation_threshold: Energy below which nonessential behavior
            is suppressed and movement becomes food-seeking.
        energy_reserve: Energy protected from growth and reproduction spending.
        attack_strength: Predator performance used against prey defense.
        defense: Prey defensive performance opposed to predator attack.
        mate_search_range: Chebyshev distance within which both parents must be
            able to discover one another for mating.
        choosiness: Minimum partner mating signal accepted by an organism.
        mating_signal: Signal strength presented to potential mates.
        maturity_age: Age at reproductive maturity.
        reproduction_energy_threshold: Minimum current energy for reproduction.
        offspring_energy: Base energy investment before mating-type scaling.
        maximum_age: Hard maximum completed age.
    """

    adult_body_mass: int = attrs.field(
        default=8,
        validator=attrs_validators.validate_int_in_range(1, 40),
    )
    growth_rate: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_in_range(0, 4),
    )
    max_speed: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_in_range(0, 4),
    )
    locomotion_cost_coefficient: int = attrs.field(
        default=20,
        validator=attrs_validators.validate_int_in_range(0, 200),
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
    metabolic_cost_coefficient: int = attrs.field(
        default=30,
        validator=attrs_validators.validate_int_in_range(0, 200),
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
    mate_search_range: int = attrs.field(
        default=3,
        validator=attrs_validators.validate_int_in_range(0, 20),
    )
    choosiness: int = attrs.field(
        default=5,
        validator=attrs_validators.validate_int_in_range(0, 50),
    )
    mating_signal: int = attrs.field(
        default=8,
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
            GROWTH_RATE: self.growth_rate,
            MAX_SPEED: self.max_speed,
            LOCOMOTION_COST_COEFFICIENT: self.locomotion_cost_coefficient,
            SENSORY_RANGE: self.sensory_range,
            SENSORY_ACCURACY: self.sensory_accuracy,
            MAX_INTAKE_RATE: self.max_intake_rate,
            ASSIMILATION_EFFICIENCY: self.assimilation_efficiency,
            METABOLIC_COST_COEFFICIENT: self.metabolic_cost_coefficient,
            ENERGY_CONSERVATION_THRESHOLD: self.energy_conservation_threshold,
            ENERGY_RESERVE: self.energy_reserve,
            ATTACK_STRENGTH: self.attack_strength,
            DEFENSE: self.defense,
            MATE_SEARCH_RANGE: self.mate_search_range,
            CHOOSINESS: self.choosiness,
            MATING_SIGNAL: self.mating_signal,
            MATURITY_AGE: self.maturity_age,
            REPRODUCTION_ENERGY_THRESHOLD: self.reproduction_energy_threshold,
            OFFSPRING_ENERGY: self.offspring_energy,
            MAXIMUM_AGE: self.maximum_age,
        }


@attrs.frozen(slots=True, kw_only=True)
class ReferencePhysiologicalTradeoffs:
    """Configure explicit maintenance costs for reference performance traits.

    Cost numerators are expressed in hundredths of an energy unit per realized
    developmental trait unit by default. These values are intentionally simple
    integration defaults, not calibrated biological estimates.

    Attributes:
        cost_denominator: Shared denominator applied to all cost numerators.
        max_speed_cost: Cost numerator per unit of realized maximum speed.
        sensory_range_cost: Cost numerator per unit of realized sensory range.
        sensory_accuracy_cost: Cost numerator per accuracy point above baseline.
        sensory_accuracy_baseline: Accuracy with no maintenance burden.
        max_intake_rate_cost: Cost numerator per unit of intake capacity.
        assimilation_efficiency_cost: Cost numerator per efficiency point above
            baseline.
        assimilation_efficiency_baseline: Efficiency with no maintenance burden.
        attack_strength_cost: Cost numerator per unit of attack strength.
        defense_cost: Cost numerator per unit of defense.
    """

    cost_denominator: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_gt(0),
    )
    max_speed_cost: int = attrs.field(
        default=15,
        validator=attrs_validators.validate_int_ge(0),
    )
    sensory_range_cost: int = attrs.field(
        default=5,
        validator=attrs_validators.validate_int_ge(0),
    )
    sensory_accuracy_cost: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    sensory_accuracy_baseline: int = attrs.field(
        default=50,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    max_intake_rate_cost: int = attrs.field(
        default=2,
        validator=attrs_validators.validate_int_ge(0),
    )
    assimilation_efficiency_cost: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    assimilation_efficiency_baseline: int = attrs.field(
        default=50,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    attack_strength_cost: int = attrs.field(
        default=3,
        validator=attrs_validators.validate_int_ge(0),
    )
    defense_cost: int = attrs.field(
        default=3,
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcologyConfig:
    """Define the numerical baseline for the reference ecology.

    The defaults are deliberately modest and transparent rather than intended
    as calibrated biological claims. The reference ecology is an integration
    baseline for experiments and examples; callers should replace parameter
    values for substantive scientific work.

    Organism-specific growth rate and metabolic/locomotion cost coefficients
    live in ``traits`` rather than this simulation-wide configuration. The
    exponents remain configuration because they define the shared scaling laws
    under which individual trait values operate. ``physiological_tradeoffs``
    makes selected realized performance capabilities carry ongoing maintenance
    costs instead of allowing independent performance improvements for free.
    ``mating_type_investment_scales`` modifies the heritable base offspring-energy
    investment by reproductive identity without changing parent ordering into a
    biological role.

    Attributes:
        width: World width in grid cells.
        height: World height in grid cells.
        initial_population: Number of homozygous founders.
        initial_energy: Initial founder energy.
        max_steps: Number of timesteps run by the reference engine.
        seed: Simulation random seed.
        traits: Founder life-history, physiological, and ecological trait values.
        physiological_tradeoffs: Maintenance-cost coefficients for realized
            performance traits.
        mating_type_investment_scales: Rational scales applied to each reference
            mating type's heritable offspring-energy investment.
        mutation_probability_ppm: Per-transmitted-allele mutation probability.
        mutation_max_change: Maximum absolute integer mutation step.
        recombination_probability_ppm: Single-crossover probability per meiosis.
        resource_generation_amount: Resource units per generated deposit.
        resource_deposits_per_step: Number of deposits generated each timestep.
        decomposition_amount: Maximum carcass units decomposed per timestep.
        resource_request_amount: Behavioral resource demand before an
            organism-specific intake-capacity ceiling is applied.
        metabolic_mass_exponent: Basal metabolic body-mass exponent.
        locomotion_mass_exponent: Locomotion body-mass exponent.
        locomotion_distance_exponent: Locomotion distance exponent.
        growth_energy_per_mass: Energy cost per gained body-mass unit.
        predation_radius: Chebyshev radius for predation interactions.
        predation_consumption_percent: Percentage of prey biomass converted
            directly to predator energy.
        mating_radius: Maximum Chebyshev distance at which compatible parents
            may actually reproduce after mate-seeking movement.
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
    physiological_tradeoffs: ReferencePhysiologicalTradeoffs = attrs.field(
        factory=ReferencePhysiologicalTradeoffs,
        validator=attrs.validators.instance_of(ReferencePhysiologicalTradeoffs),
    )
    mating_type_investment_scales: ReferenceMatingTypeInvestmentScales = attrs.field(
        factory=ReferenceMatingTypeInvestmentScales,
        validator=attrs.validators.instance_of(ReferenceMatingTypeInvestmentScales),
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
    metabolic_mass_exponent: int | float = 0.75
    locomotion_mass_exponent: int | float = 0.50
    locomotion_distance_exponent: int | float = 1.0
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

        validators.validate_number_ge(
            self.growth_energy_per_mass,
            bound=0,
            name="growth_energy_per_mass",
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
