"""Simulation and engine builders for the complete reference ecology."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import attrs

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EnergyBelowThresholdMovementCondition,
    EnergyConservationBehavior,
    GeneticPhenotypeSensoryAccuracy,
    MovementIntentRule,
    NearestResourceTarget,
    PrioritizedMovementIntent,
    PurposeMovementTargetRouter,
    PurposeTargetRoute,
)
from evo_engine.behavior import (
    REPRODUCTION as REPRODUCTION_PURPOSE,
)
from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    GeneticPhenotypeCoefficient,
    KeepEnergyReserve,
    LinearGrowthCost,
    PowerLawLocomotionCost,
    PowerLawMetabolicCost,
    SpendToZero,
)
from evo_engine.engine import (
    MaxSteps,
    Observer,
    Process,
    Simulation,
    SimulationEngine,
    StageCoordinator,
    build_standard_lifecycle,
)
from evo_engine.feeding import (
    GeneticPhenotypeAssimilationEfficiency,
    GeneticPhenotypeIntakeCapacity,
)
from evo_engine.genetics import (
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    LOCOMOTION_COST_COEFFICIENT,
    METABOLIC_COST_COEFFICIENT,
    REPRODUCTION_ENERGY_THRESHOLD,
    MeioticGameteFormation,
    SexualInheritance,
    SingleCrossoverRecombination,
)
from evo_engine.growth import GeneticPhenotypeGrowthRate
from evo_engine.observation import PopulationRecorder
from evo_engine.predation import (
    AllOfPredationEligibility,
    GeneticAttackAdvantagePreference,
    GeneticAttackDefenseEligibility,
    LargerPredatorEligibility,
)
from evo_engine.presets.reference_ecology.config import (
    ReferenceEcologyConfig,
    resolve_reference_config,
)
from evo_engine.presets.reference_ecology.genetics import (
    build_reference_genetic_architecture,
    build_reference_world,
)
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
    AllOfMatingCompatibility,
    DevelopmentalMaturityEligibility,
    FractionOfAdultBodyMassAtBirth,
    GeneticPhenotypeEnergyInvestment,
    MinimumEnergyEligibility,
    MutualMateSearchRange,
    MutualSignalCompatibility,
    MutualSignalMarginPreference,
    PairwiseMating,
    PreferredMateTarget,
    ReproductiveEligibilityMovementCondition,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.predation import PreferenceOrder as PredationPreferenceOrder
from evo_engine.resolvers.reproduction import (
    PreferenceOrder as ReproductionPreferenceOrder,
)
from evo_engine.resolvers.resource_allocation import EqualShare
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import MooreRandom
from evo_engine.spatial.neighborhoods import Moore


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcology:
    """Bundle a configured reference simulation with its matching engine.

    Attributes:
        config: Numerical configuration used to build the ecology.
        simulation: Mutable simulation state and shared behavior configuration.
        engine: Engine wired with the standard ecological lifecycle.
        recorder: Population recorder attached to the reference engine.
    """

    config: ReferenceEcologyConfig = attrs.field(
        validator=attrs.validators.instance_of(ReferenceEcologyConfig),
    )
    simulation: Simulation = attrs.field(
        validator=attrs.validators.instance_of(Simulation),
    )
    engine: SimulationEngine = attrs.field(
        validator=attrs.validators.instance_of(SimulationEngine),
    )
    recorder: PopulationRecorder = attrs.field(
        validator=attrs.validators.instance_of(PopulationRecorder),
    )


def build_reference_simulation(
    config: ReferenceEcologyConfig | None = None,
) -> Simulation:
    """Build reference simulation state and organism behavior configuration.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Configured simulation ready for the matching reference engine.
    """
    config = resolve_reference_config(config)
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
    *,
    observers: Iterable[Observer] = (),
) -> SimulationEngine:
    """Build a simulation engine containing the complete reference lifecycle.

    Args:
        config: Optional reference configuration. Defaults to standard values.
        observers: Optional observers attached to committed reference states.

    Returns:
        Engine wiring ecology, life history, mortality, and observation into the
        standard lifecycle.
    """
    config = resolve_reference_config(config)
    reserve = KeepEnergyReserve(
        minimum_energy=DevelopmentalEnergyThreshold(
            trait_name=ENERGY_RESERVE,
        )
    )
    conservation_threshold = DevelopmentalEnergyThreshold(
        trait_name=ENERGY_CONSERVATION_THRESHOLD,
    )
    reproductive_eligibility = AllOfEligibility(
        eligibilities=(
            DevelopmentalMaturityEligibility(),
            MinimumEnergyEligibility(
                minimum_energy=DevelopmentalEnergyThreshold(
                    trait_name=REPRODUCTION_ENERGY_THRESHOLD,
                )
            ),
        )
    )
    mating_compatibility = AllOfMatingCompatibility(
        compatibilities=(
            MutualMateSearchRange(),
            MutualSignalCompatibility(),
        )
    )
    mating_preference = MutualSignalMarginPreference()

    starvation_stage = _accept_all_stage(Starvation())
    maximum_age_stage = _accept_all_stage(MaximumAgeMortality())
    metabolism_stage = _accept_all_stage(
        Metabolism(
            cost_model=PowerLawMetabolicCost(
                coefficient=GeneticPhenotypeCoefficient(
                    trait_name=METABOLIC_COST_COEFFICIENT,
                ),
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
                coefficient=GeneticPhenotypeCoefficient(
                    trait_name=LOCOMOTION_COST_COEFFICIENT,
                ),
                mass_exponent=config.locomotion_mass_exponent,
                distance_exponent=config.locomotion_distance_exponent,
                minimum_nonzero_cost=1,
            ),
            energy_expenditure_policy=SpendToZero(),
            movement_intent_model=PrioritizedMovementIntent(
                rules=(
                    MovementIntentRule(
                        behavioral_purpose=ENERGY_ACQUISITION,
                        condition=EnergyBelowThresholdMovementCondition(
                            energy_threshold=conservation_threshold,
                        ),
                    ),
                    MovementIntentRule(
                        behavioral_purpose=REPRODUCTION_PURPOSE,
                        condition=ReproductiveEligibilityMovementCondition(
                            eligibility=reproductive_eligibility,
                        ),
                    ),
                ),
            ),
            movement_target_model=PurposeMovementTargetRouter(
                routes=(
                    PurposeTargetRoute(
                        behavioral_purpose=ENERGY_ACQUISITION,
                        target_model=NearestResourceTarget(
                            sensory_accuracy_model=(GeneticPhenotypeSensoryAccuracy()),
                        ),
                    ),
                    PurposeTargetRoute(
                        behavioral_purpose=REPRODUCTION_PURPOSE,
                        target_model=PreferredMateTarget(
                            eligibility=reproductive_eligibility,
                            compatibility=mating_compatibility,
                            preference=mating_preference,
                        ),
                    ),
                ),
            ),
        )
    )
    predation_stage = StageCoordinator(
        processes=(
            Predation(
                neighborhood=Moore(
                    radius=config.predation_radius,
                ),
                consumption_percent=config.predation_consumption_percent,
                can_predate=AllOfPredationEligibility(
                    eligibilities=(
                        LargerPredatorEligibility(),
                        GeneticAttackDefenseEligibility(),
                    )
                ),
                preference_function=GeneticAttackAdvantagePreference(),
            ),
        ),
        resolver=PredationPreferenceOrder(),
    )
    resource_consumption_stage = StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=config.resource_request_amount,
                intake_capacity_model=GeneticPhenotypeIntakeCapacity(),
                assimilation_model=GeneticPhenotypeAssimilationEfficiency(),
            ),
        ),
        resolver=EqualShare(),
    )
    growth_stage = _accept_all_stage(
        Growth(
            growth_model=GeneticPhenotypeGrowthRate(),
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
                eligibility=reproductive_eligibility,
                parent_selection=PairwiseMating(
                    neighborhood=Moore(
                        radius=config.mating_radius,
                    ),
                    can_mate=mating_compatibility,
                    preference_function=mating_preference,
                ),
                inheritance_model=SexualInheritance(
                    gamete_formation=MeioticGameteFormation(
                        recombination=SingleCrossoverRecombination(
                            probability_ppm=config.recombination_probability_ppm,
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
        observers=observers,
    )


def build_reference_ecology(
    config: ReferenceEcologyConfig | None = None,
) -> ReferenceEcology:
    """Build the complete observable reference simulation and matching engine.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Bundle containing the resolved configuration, simulation, engine, and a
        recorder tracking all reference integer traits each step.
    """
    config = resolve_reference_config(config)
    recorder = PopulationRecorder(
        trait_names=tuple(config.traits.as_mapping()),
    )

    return ReferenceEcology(
        config=config,
        simulation=build_reference_simulation(config),
        engine=build_reference_engine(
            config,
            observers=(recorder,),
        ),
        recorder=recorder,
    )


def _accept_all_stage(
    *processes: Process[Any, Any],
) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )
