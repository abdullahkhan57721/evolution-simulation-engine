"""Build a complete reference ecology from the engine's public components."""

from __future__ import annotations

import attrs

from evo_engine.behavior import (
    EnergyConservationBehavior,
    EnergyThresholdMovementIntent,
    NearestResourceTarget,
)
from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    KeepEnergyReserve,
    LinearGrowthCost,
    PowerLawLocomotionCost,
    PowerLawMetabolicCost,
    SpendToZero,
)
from evo_engine.engine import (
    MaxSteps,
    Simulation,
    SimulationEngine,
    StageCoordinator,
    build_standard_lifecycle,
)
from evo_engine.genetics import (
    ADULT_BODY_MASS,
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    MATURITY_AGE,
    MAX_SPEED,
    MAXIMUM_AGE,
    OFFSPRING_ENERGY,
    REPRODUCTION_ENERGY_THRESHOLD,
    SENSORY_RANGE,
    Chromosome,
    GeneticArchitecture,
    Genome,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    MeioticGameteFormation,
    SexualInheritance,
    SingleCrossoverRecombination,
    Trait,
    UniformIntegerMutation,
)
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import (
    Aging,
    Decomposition,
    Growth,
    MaximumAgeMortality,
    Metabolism,
    Movement,
    Predation,
    Reproduction,
    ResourceConsumption,
    ResourceGeneration,
    Starvation,
)
from evo_engine.reproduction import (
    AllOfEligibility,
    DevelopmentalMaturityEligibility,
    FractionOfAdultBodyMassAtBirth,
    GeneticPhenotypeEnergyInvestment,
    MinimumEnergyEligibility,
    PairwiseMating,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.predation import PreferenceOrder as PredationPreferenceOrder
from evo_engine.resolvers.reproduction import (
    PreferenceOrder as ReproductionPreferenceOrder,
)
from evo_engine.resolvers.resource_allocation import EqualShare
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import MooreRandom
from evo_engine.spatial.neighborhoods import Moore, SameCell
from evo_engine.validation import attrs_validators, validators
from evo_engine.world import Organism, WorldState

_REFERENCE_CHROMOSOME = "reference"


@attrs.frozen(slots=True, kw_only=True)
class ReferenceTraitValues:
    """Define founder values for the traits used by the reference ecology.

    These values initialize a homozygous founder population. Sexual inheritance,
    recombination, and mutation can subsequently create heritable variation.

    Attributes:
        adult_body_mass: Realized adult body-mass target.
        max_speed: Maximum Euclidean movement distance per timestep.
        sensory_range: Resource-detection radius.
        energy_conservation_threshold: Energy below which nonessential behavior
            is suppressed and movement becomes food-seeking.
        energy_reserve: Energy protected from growth and reproduction spending.
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
    energy_conservation_threshold: int = attrs.field(
        default=15,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )
    energy_reserve: int = attrs.field(
        default=5,
        validator=attrs_validators.validate_int_in_range(0, 100),
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
            ENERGY_CONSERVATION_THRESHOLD: self.energy_conservation_threshold,
            ENERGY_RESERVE: self.energy_reserve,
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
        resource_request_amount: Resource units requested by each consumer.
        metabolic_coefficient: Basal metabolic allometry coefficient.
        metabolic_mass_exponent: Basal metabolic body-mass exponent.
        locomotion_coefficient: Locomotion cost coefficient.
        locomotion_mass_exponent: Locomotion body-mass exponent.
        locomotion_distance_exponent: Locomotion distance exponent.
        growth_amount_per_step: Potential body-mass gain per timestep.
        growth_energy_per_mass: Energy cost per gained body-mass unit.
        predation_radius: Same-species predation interaction radius.
        predation_consumption_percent: Fraction of prey biomass converted directly
            to predator energy, expressed as an integer percentage.
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
    traits: ReferenceTraitValues = attrs.field(factory=ReferenceTraitValues)
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
        default=4,
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


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcology:
    """Bundle a configured reference simulation with its matching engine.

    Attributes:
        config: Numerical configuration used to build the ecology.
        simulation: Mutable simulation state and shared behavior configuration.
        engine: Engine wired with the standard ecological lifecycle.
    """

    config: ReferenceEcologyConfig
    simulation: Simulation
    engine: SimulationEngine


def _trait_domains() -> dict[str, tuple[int, int]]:
    return {
        ADULT_BODY_MASS: (1, 40),
        MAX_SPEED: (0, 4),
        SENSORY_RANGE: (0, 20),
        ENERGY_CONSERVATION_THRESHOLD: (0, 100),
        ENERGY_RESERVE: (0, 100),
        MATURITY_AGE: (0, 100),
        REPRODUCTION_ENERGY_THRESHOLD: (0, 200),
        OFFSPRING_ENERGY: (1, 50),
        MAXIMUM_AGE: (1, 200),
    }


def build_reference_genetic_architecture(
    config: ReferenceEcologyConfig | None = None,
) -> GeneticArchitecture:
    """Build the genetic architecture used by the reference ecology.

    Each modeled trait has one bounded integer locus. All loci share one
    chromosome so sexual reproduction exercises segregation and crossover.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Genetic architecture containing every trait required by the preset.
    """
    config = _resolve_config(config)
    mutation = UniformIntegerMutation(
        probability_ppm=config.mutation_probability_ppm,
        max_change=config.mutation_max_change,
    )

    loci = tuple(
        Locus(
            name=trait_name,
            chromosome_name=_REFERENCE_CHROMOSOME,
            position=index * 100,
            domain=IntegerAlleleDomain(
                minimum=minimum,
                maximum=maximum,
            ),
            mutation=mutation,
        )
        for index, (trait_name, (minimum, maximum)) in enumerate(
            _trait_domains().items(),
            start=1,
        )
    )
    traits = tuple(
        Trait(
            name=trait_name,
            locus_names=(trait_name,),
            expression=MeanIntegerExpression(),
        )
        for trait_name in _trait_domains()
    )

    return GeneticArchitecture(
        loci=loci,
        traits=traits,
    )


def build_reference_founder_genome(
    genetic_architecture: GeneticArchitecture,
    config: ReferenceEcologyConfig | None = None,
) -> Genome:
    """Build the homozygous founder genome used by the reference ecology.

    Args:
        genetic_architecture: Architecture used to create and validate alleles.
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Diploid homozygous founder genome.
    """
    config = _resolve_config(config)
    alleles = tuple(
        genetic_architecture.locus(trait_name).create_allele(value)
        for trait_name, value in config.traits.as_mapping().items()
    )

    return Genome(
        chromosomes=(
            Chromosome(
                name=_REFERENCE_CHROMOSOME,
                alleles=alleles,
            ),
            Chromosome(
                name=_REFERENCE_CHROMOSOME,
                alleles=alleles,
            ),
        )
    )


def build_reference_world(
    genetic_architecture: GeneticArchitecture,
    config: ReferenceEcologyConfig | None = None,
) -> WorldState:
    """Build the reference world and compact founder population.

    Founders occupy distinct cells in row-major order. Compact placement keeps
    early mating and interaction opportunities possible without hidden random
    initialization draws.

    Args:
        genetic_architecture: Architecture shared by all organisms.
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Initialized world containing the founder population.
    """
    config = _resolve_config(config)
    founder_genome = build_reference_founder_genome(
        genetic_architecture,
        config,
    )
    world = WorldState(
        width=config.width,
        height=config.height,
    )

    for index in range(config.initial_population):
        world.add_organism(
            Organism.from_genome(
                genetic_architecture=genetic_architecture,
                genome=founder_genome,
                age=0,
                energy=config.initial_energy,
                x=index % config.width,
                y=index // config.width,
            )
        )

    return world


def build_reference_simulation(
    config: ReferenceEcologyConfig | None = None,
) -> Simulation:
    """Build reference simulation state and organism behavior configuration.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Configured simulation ready for the matching reference engine.
    """
    config = _resolve_config(config)
    genetic_architecture = build_reference_genetic_architecture(config)
    world = build_reference_world(
        genetic_architecture,
        config,
    )
    conservation_threshold = DevelopmentalEnergyThreshold(
        trait_name=ENERGY_CONSERVATION_THRESHOLD,
    )

    return Simulation(
        initial_world_state=world,
        genetic_architecture=genetic_architecture,
        seed=config.seed,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=conservation_threshold,
        ),
    )


def build_reference_engine(
    config: ReferenceEcologyConfig | None = None,
) -> SimulationEngine:
    """Build a simulation engine containing the complete reference lifecycle.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Engine wiring ecology, life history, and mortality into the standard
        lifecycle.
    """
    config = _resolve_config(config)
    reserve = KeepEnergyReserve(
        minimum_energy=DevelopmentalEnergyThreshold(
            trait_name=ENERGY_RESERVE,
        )
    )
    conservation_threshold = DevelopmentalEnergyThreshold(
        trait_name=ENERGY_CONSERVATION_THRESHOLD,
    )

    starvation_stage = _accept_all_stage(Starvation())
    maximum_age_stage = _accept_all_stage(MaximumAgeMortality())
    metabolism_stage = _accept_all_stage(
        Metabolism(
            cost_model=PowerLawMetabolicCost(
                coefficient=config.metabolic_coefficient,
                mass_exponent=config.metabolic_mass_exponent,
                minimum_cost=1,
            )
        )
    )
    environment_stage = _accept_all_stage(
        ResourceGeneration(
            amount=config.resource_generation_amount,
            number_of_deposits=config.resource_deposits_per_step,
        ),
        Decomposition(
            amount=config.decomposition_amount,
        ),
    )
    movement_stage = _accept_all_stage(
        Movement(
            movement_pattern=MooreRandom(),
            boundary_condition=Clamped(),
            locomotion_cost_model=PowerLawLocomotionCost(
                coefficient=config.locomotion_coefficient,
                mass_exponent=config.locomotion_mass_exponent,
                distance_exponent=config.locomotion_distance_exponent,
                minimum_nonzero_cost=1,
            ),
            energy_expenditure_policy=SpendToZero(),
            movement_intent_model=EnergyThresholdMovementIntent(
                energy_threshold=conservation_threshold,
            ),
            movement_target_model=NearestResourceTarget(),
        )
    )
    predation_stage = StageCoordinator(
        processes=(
            Predation(
                neighborhood=SameCell(),
                consumption_percent=config.predation_consumption_percent,
            ),
        ),
        resolver=PredationPreferenceOrder(),
    )
    resource_consumption_stage = StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=config.resource_request_amount,
            ),
        ),
        resolver=EqualShare(),
    )
    growth_stage = _accept_all_stage(
        Growth(
            growth_model=FixedGrowthRate(
                amount_per_timestep=config.growth_amount_per_step,
            ),
            growth_cost_model=LinearGrowthCost(
                energy_per_body_mass_unit=config.growth_energy_per_mass,
                minimum_nonzero_cost=1,
            ),
            energy_expenditure_policy=reserve,
        )
    )
    aging_stage = _accept_all_stage(Aging())
    reproduction_stage = StageCoordinator(
        processes=(
            Reproduction(
                eligibility=AllOfEligibility(
                    eligibilities=(
                        DevelopmentalMaturityEligibility(),
                        MinimumEnergyEligibility(
                            minimum_energy=DevelopmentalEnergyThreshold(
                                trait_name=REPRODUCTION_ENERGY_THRESHOLD,
                            )
                        ),
                    )
                ),
                parent_selection=PairwiseMating(
                    neighborhood=Moore(
                        radius=config.mating_radius,
                    )
                ),
                inheritance_model=SexualInheritance(
                    gamete_formation=MeioticGameteFormation(
                        recombination=SingleCrossoverRecombination(
                            probability_ppm=(config.recombination_probability_ppm),
                        )
                    )
                ),
                parental_investment=GeneticPhenotypeEnergyInvestment(),
                energy_expenditure_policy=reserve,
                offspring_body_mass_model=FractionOfAdultBodyMassAtBirth(
                    numerator=config.newborn_mass_numerator,
                    denominator=config.newborn_mass_denominator,
                ),
            ),
        ),
        resolver=ReproductionPreferenceOrder(),
    )

    lifecycle = build_standard_lifecycle(
        starvation_stage=starvation_stage,
        maximum_age_mortality_stage=maximum_age_stage,
        metabolism_stage=metabolism_stage,
        environment_stage=environment_stage,
        movement_stage=movement_stage,
        predation_stage=predation_stage,
        resource_consumption_stage=resource_consumption_stage,
        growth_stage=growth_stage,
        aging_stage=aging_stage,
        reproduction_stage=reproduction_stage,
    )

    return SimulationEngine(
        step_coordinator=lifecycle,
        stopping_condition=MaxSteps(
            max_steps=config.max_steps,
        ),
    )


def build_reference_ecology(
    config: ReferenceEcologyConfig | None = None,
) -> ReferenceEcology:
    """Build the complete reference simulation and matching engine.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Bundle containing the resolved configuration, simulation, and engine.
    """
    config = _resolve_config(config)
    return ReferenceEcology(
        config=config,
        simulation=build_reference_simulation(config),
        engine=build_reference_engine(config),
    )


def _resolve_config(
    config: ReferenceEcologyConfig | None,
) -> ReferenceEcologyConfig:
    if config is None:
        return ReferenceEcologyConfig()

    if not isinstance(config, ReferenceEcologyConfig):
        raise TypeError("config must be an instance of ReferenceEcologyConfig.")

    return config


def _accept_all_stage(*processes: object) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )
