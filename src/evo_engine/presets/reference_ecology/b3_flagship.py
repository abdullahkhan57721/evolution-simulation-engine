"""Frozen B3 environment-dependent selection scenario composition."""

from __future__ import annotations

from typing import Literal, TypeAlias

import attrs

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    ResourcePlacementModel,
    UniformResourcePlacement,
)
from evo_engine.genetics import MAX_SPEED, GeneticArchitecture
from evo_engine.presets.reference_ecology.config import (
    ReferenceEcologyConfig,
    ReferencePhysiologicalTradeoffs,
    ReferenceTraitValues,
)
from evo_engine.presets.reference_ecology.genetics import (
    build_balanced_reference_trait_world,
)
from evo_engine.presets.reference_ecology.movement import ReferenceMooreMovement
from evo_engine.presets.reference_ecology.reproductive_investment import (
    ReferenceMatingTypeInvestmentScales,
)
from evo_engine.world import WorldState

B3_DISCOVERY_SEEDS: tuple[int, ...] = (11, 23, 37, 41, 59, 73, 89, 101)
B3_CONFIRMATION_SEEDS: tuple[int, ...] = (5, 17, 29, 43, 61, 79, 97, 113)
B3_COUNTERBALANCE_SEEDS: tuple[int, ...] = (29, 79)

B3_LOW_MAX_SPEED = 1
B3_HIGH_MAX_SPEED = 4
B3_PRIMARY_STEP = 30
B3_MAX_STEPS = 50
B3_RESOURCE_DEPOSITS_PER_STEP = 32
B3_RESOURCE_GENERATION_AMOUNT = 6
B3_COMPACT_PATCH_RADIUS = 1
B3_BROAD_PATCH_RADIUS = 2
B3_PATCH_CENTERS: tuple[tuple[int, int], ...] = ((2, 5), (9, 5))

B3Environment: TypeAlias = Literal["uniform", "compact_patch", "broad_patch"]
B3FounderAssignment: TypeAlias = Literal["standard", "swapped"]


@attrs.frozen(slots=True, kw_only=True)
class B3FlagshipSpecification:
    """Describe one frozen B3 reference-ecology run.

    Attributes:
        environment: Resource-geography condition for the run.
        founder_assignment: Deterministic mapping of focal values onto founder IDs.
        seed: Simulation seed used for this run.
        config: Fully explicit reference-ecology configuration.
        focal_trait: Genetic-phenotype trait under environment-dependent selection.
        variant_values: Homozygous founder values supplied to the balanced builder.
        primary_step: Predeclared committed timestep for the headline comparison.
    """

    environment: B3Environment
    founder_assignment: B3FounderAssignment
    seed: int
    config: ReferenceEcologyConfig
    focal_trait: str = MAX_SPEED
    variant_values: tuple[int, int] = (B3_LOW_MAX_SPEED, B3_HIGH_MAX_SPEED)
    primary_step: int = B3_PRIMARY_STEP


def build_b3_flagship_specification(
    *,
    seed: int,
    environment: B3Environment,
    founder_assignment: B3FounderAssignment = "standard",
) -> B3FlagshipSpecification:
    """Build one fully explicit frozen B3 scenario specification.

    The specification intentionally spells out scientifically relevant reference
    values rather than inheriting future preset defaults. Control and treatment
    therefore remain reproducible even if the ordinary reference preset changes.

    Args:
        seed: Simulation seed for the run.
        environment: Uniform control, compact treatment, or broad-patch sensitivity.
        founder_assignment: Standard or swapped focal-value assignment used for
            the bounded founder-confounding check.

    Returns:
        Immutable B3 run specification.

    Raises:
        ValueError: If the environment or founder assignment is unsupported.
    """
    placement = _b3_resource_placement(environment)
    variant_values = _b3_variant_values(founder_assignment)
    config = ReferenceEcologyConfig(
        width=12,
        height=12,
        initial_population=20,
        initial_energy=30,
        max_steps=B3_MAX_STEPS,
        seed=seed,
        exploration_movement=ReferenceMooreMovement(),
        traits=ReferenceTraitValues(
            adult_body_mass=8,
            growth_rate=1,
            max_speed=B3_LOW_MAX_SPEED,
            locomotion_cost_coefficient=20,
            sensory_range=4,
            sensory_accuracy=90,
            max_intake_rate=8,
            assimilation_efficiency=75,
            metabolic_cost_coefficient=30,
            energy_conservation_threshold=15,
            energy_reserve=5,
            attack_strength=0,
            defense=1,
            mate_search_range=3,
            choosiness=5,
            mating_signal=8,
            maturity_age=4,
            reproduction_energy_threshold=20,
            offspring_energy=4,
            maximum_age=30,
        ),
        physiological_tradeoffs=ReferencePhysiologicalTradeoffs(
            cost_denominator=100,
            max_speed_cost=15,
            sensory_range_cost=5,
            sensory_accuracy_cost=1,
            sensory_accuracy_baseline=50,
            max_intake_rate_cost=2,
            assimilation_efficiency_cost=1,
            assimilation_efficiency_baseline=50,
            attack_strength_cost=3,
            defense_cost=3,
        ),
        mating_type_investment_scales=ReferenceMatingTypeInvestmentScales(
            denominator=2,
            type_a_numerator=3,
            type_b_numerator=1,
        ),
        mutation_probability_ppm=0,
        mutation_max_change=1,
        recombination_probability_ppm=500_000,
        resource_generation_amount=B3_RESOURCE_GENERATION_AMOUNT,
        resource_deposits_per_step=B3_RESOURCE_DEPOSITS_PER_STEP,
        resource_placement_model=placement,
        decomposition_amount=2,
        resource_request_amount=10,
        metabolic_mass_exponent=0.75,
        locomotion_mass_exponent=0.50,
        locomotion_distance_exponent=1.0,
        growth_energy_per_mass=2.0,
        predation_radius=0,
        predation_consumption_percent=75,
        mating_radius=3,
        newborn_mass_numerator=1,
        newborn_mass_denominator=4,
    )
    return B3FlagshipSpecification(
        environment=environment,
        founder_assignment=founder_assignment,
        seed=seed,
        config=config,
        variant_values=variant_values,
    )


def build_b3_flagship_world(
    genetic_architecture: GeneticArchitecture,
    specification: B3FlagshipSpecification,
) -> WorldState:
    """Build the deterministic balanced-founder world for one B3 specification.

    Args:
        genetic_architecture: Architecture shared by the reference ecology.
        specification: Frozen B3 run specification.

    Returns:
        World containing the balanced speed-1/speed-4 founder population.
    """
    return build_balanced_reference_trait_world(
        genetic_architecture,
        trait_name=specification.focal_trait,
        variant_values=specification.variant_values,
        config=specification.config,
    )


def validate_b3_treatment_integrity(
    control: B3FlagshipSpecification,
    treatment: B3FlagshipSpecification,
) -> None:
    """Fail unless a B3 matched pair differs only by canonical resource placement.

    Args:
        control: Uniform-resource B3 specification.
        treatment: Compact-patch B3 specification using the same seed and founder
            assignment.

    Raises:
        ValueError: If either arm has the wrong placement or any unintended
            configuration/specification difference is present.
    """
    if control.environment != "uniform":
        raise ValueError("B3 control environment must be 'uniform'.")
    if not isinstance(
        control.config.resource_placement_model, UniformResourcePlacement
    ):
        raise ValueError("B3 control must use UniformResourcePlacement.")

    expected_treatment_placement = _patchy_resource_placement(
        radius=B3_COMPACT_PATCH_RADIUS
    )
    if treatment.environment != "compact_patch":
        raise ValueError("B3 treatment environment must be 'compact_patch'.")
    if treatment.config.resource_placement_model != expected_treatment_placement:
        raise ValueError("B3 treatment must use the frozen compact patch geometry.")

    normalized_treatment = attrs.evolve(
        treatment,
        environment="uniform",
        config=attrs.evolve(
            treatment.config,
            resource_placement_model=control.config.resource_placement_model,
        ),
    )
    if normalized_treatment != control:
        raise ValueError(
            "B3 matched control/treatment differ outside resource placement."
        )


def _b3_resource_placement(environment: B3Environment) -> ResourcePlacementModel:
    if environment == "uniform":
        return UniformResourcePlacement()
    if environment == "compact_patch":
        return _patchy_resource_placement(radius=B3_COMPACT_PATCH_RADIUS)
    if environment == "broad_patch":
        return _patchy_resource_placement(radius=B3_BROAD_PATCH_RADIUS)
    raise ValueError(f"Unsupported B3 environment: {environment!r}.")


def _patchy_resource_placement(*, radius: int) -> PatchyResourcePlacement:
    return PatchyResourcePlacement(
        patches=tuple(
            ResourcePatch(
                center_x=center_x,
                center_y=center_y,
                radius=radius,
                weight=1,
            )
            for center_x, center_y in B3_PATCH_CENTERS
        )
    )


def _b3_variant_values(
    founder_assignment: B3FounderAssignment,
) -> tuple[int, int]:
    if founder_assignment == "standard":
        return (B3_LOW_MAX_SPEED, B3_HIGH_MAX_SPEED)
    if founder_assignment == "swapped":
        return (B3_HIGH_MAX_SPEED, B3_LOW_MAX_SPEED)
    raise ValueError(f"Unsupported B3 founder assignment: {founder_assignment!r}.")


__all__ = [
    "B3_COMPACT_PATCH_RADIUS",
    "B3_CONFIRMATION_SEEDS",
    "B3_COUNTERBALANCE_SEEDS",
    "B3_DISCOVERY_SEEDS",
    "B3_HIGH_MAX_SPEED",
    "B3_LOW_MAX_SPEED",
    "B3_MAX_STEPS",
    "B3_PATCH_CENTERS",
    "B3_PRIMARY_STEP",
    "B3_RESOURCE_DEPOSITS_PER_STEP",
    "B3_RESOURCE_GENERATION_AMOUNT",
    "B3FlagshipSpecification",
    "B3FounderAssignment",
    "build_b3_flagship_specification",
    "build_b3_flagship_world",
    "validate_b3_treatment_integrity",
]
