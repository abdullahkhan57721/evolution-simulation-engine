"""Focused tests for the frozen B3 environment-dependent flagship composition."""

from __future__ import annotations

from collections import Counter
from typing import cast

import attrs
import pytest

from evo_engine.ecology import PatchyResourcePlacement, UniformResourcePlacement
from evo_engine.experiments.b3_flagship import run_b3_matched_pair
from evo_engine.genetics import MAX_SPEED
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_COUNTERBALANCE_SEEDS,
    B3_DISCOVERY_SEEDS,
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_PRIMARY_STEP,
    build_b3_flagship_specification,
    build_b3_flagship_world,
    validate_b3_treatment_integrity,
)
from evo_engine.presets.reference_ecology.genetics import (
    build_reference_genetic_architecture,
)


def _founder_snapshot(world):
    return tuple(
        (
            organism.id,
            organism.x,
            organism.y,
            organism.mating_type,
            organism.age,
            organism.energy,
            organism.body_mass,
            tuple(sorted(organism.genetic_phenotype.items())),
        )
        for organism in world.organisms.values()
    )


def _integer_allele_value(value: object) -> int:
    if type(value) is not int:
        raise TypeError("Expected integer B3 max_speed allele value.")
    return cast(int, value)


def test_b3_seed_sets_and_primary_step_are_frozen() -> None:
    """Test discovery and confirmation identities cannot silently overlap."""
    assert B3_DISCOVERY_SEEDS == (11, 23, 37, 41, 59, 73, 89, 101)
    assert B3_CONFIRMATION_SEEDS == (5, 17, 29, 43, 61, 79, 97, 113)
    assert B3_COUNTERBALANCE_SEEDS == (29, 79)
    assert set(B3_DISCOVERY_SEEDS).isdisjoint(B3_CONFIRMATION_SEEDS)
    assert set(B3_COUNTERBALANCE_SEEDS) <= set(B3_CONFIRMATION_SEEDS)
    assert B3_PRIMARY_STEP == 30


def test_b3_canonical_pair_differs_only_in_resource_placement() -> None:
    """Test the matched B3 treatment-integrity audit accepts the frozen pair."""
    control = build_b3_flagship_specification(seed=5, environment="uniform")
    treatment = build_b3_flagship_specification(seed=5, environment="compact_patch")

    validate_b3_treatment_integrity(control, treatment)

    assert isinstance(
        control.config.resource_placement_model, UniformResourcePlacement
    )
    assert isinstance(
        treatment.config.resource_placement_model, PatchyResourcePlacement
    )
    assert treatment.config.resource_deposits_per_step == 32
    assert treatment.config.resource_generation_amount == 6
    assert treatment.config.mutation_probability_ppm == 0
    assert treatment.config.recombination_probability_ppm == 500_000
    assert treatment.config.mating_radius == 3
    assert treatment.config.traits.max_intake_rate == 8
    assert treatment.config.traits.attack_strength == 0
    assert treatment.config.traits.defense == 1


def test_b3_treatment_integrity_rejects_nonplacement_difference() -> None:
    """Test an unintended scientific-control change fails loudly."""
    control = build_b3_flagship_specification(seed=5, environment="uniform")
    treatment = build_b3_flagship_specification(seed=5, environment="compact_patch")
    invalid = attrs.evolve(
        treatment,
        config=attrs.evolve(treatment.config, resource_request_amount=11),
    )

    with pytest.raises(ValueError, match="outside resource placement"):
        validate_b3_treatment_integrity(control, invalid)


def test_b3_founders_are_balanced_and_matched_across_environments() -> None:
    """Test treatment assignment changes no founder identity or biology."""
    control = build_b3_flagship_specification(seed=17, environment="uniform")
    treatment = build_b3_flagship_specification(seed=17, environment="compact_patch")
    architecture = build_reference_genetic_architecture(control.config)
    control_world = build_b3_flagship_world(architecture, control)
    treatment_world = build_b3_flagship_world(architecture, treatment)

    assert _founder_snapshot(control_world) == _founder_snapshot(treatment_world)

    counts: Counter[tuple[int, str]] = Counter()
    allele_copies: list[int] = []
    for organism in control_world.organisms.values():
        speed = organism.genetic_phenotype.int_value(MAX_SPEED)
        counts[(speed, organism.mating_type)] += 1
        allele_copies.extend(
            _integer_allele_value(allele.value)
            for allele in organism.genome.alleles_at(MAX_SPEED)
        )

    assert counts[(B3_LOW_MAX_SPEED, "type_a")] == 5
    assert counts[(B3_LOW_MAX_SPEED, "type_b")] == 5
    assert counts[(B3_HIGH_MAX_SPEED, "type_a")] == 5
    assert counts[(B3_HIGH_MAX_SPEED, "type_b")] == 5
    assert allele_copies.count(B3_HIGH_MAX_SPEED) / len(allele_copies) == 0.5


def test_b3_swapped_assignment_changes_speed_labels_not_founder_structure() -> None:
    """Test the bounded counterbalance swaps focal labels on fixed founders."""
    standard = build_b3_flagship_specification(seed=29, environment="uniform")
    swapped = build_b3_flagship_specification(
        seed=29,
        environment="uniform",
        founder_assignment="swapped",
    )
    architecture = build_reference_genetic_architecture(standard.config)
    standard_world = build_b3_flagship_world(architecture, standard)
    swapped_world = build_b3_flagship_world(architecture, swapped)

    for organism_id, standard_organism in standard_world.organisms.items():
        swapped_organism = swapped_world.organisms[organism_id]
        assert (standard_organism.x, standard_organism.y) == (
            swapped_organism.x,
            swapped_organism.y,
        )
        assert standard_organism.mating_type == swapped_organism.mating_type
        assert standard_organism.energy == swapped_organism.energy
        assert standard_organism.body_mass == swapped_organism.body_mass
        assert standard_organism.genetic_phenotype.int_value(MAX_SPEED) != (
            swapped_organism.genetic_phenotype.int_value(MAX_SPEED)
        )
        for trait_name in standard_organism.genetic_phenotype:
            if trait_name == MAX_SPEED:
                continue
            assert standard_organism.genetic_phenotype.int_value(trait_name) == (
                swapped_organism.genetic_phenotype.int_value(trait_name)
            )


def test_b3_canonical_seed_exercises_committed_evidence_and_manipulation() -> None:
    """Test one confirmed seed through the durable B3 evidence path."""
    pair = run_b3_matched_pair(seed=5)

    assert pair.primary_effect is not None
    assert pair.primary_effect > 0
    assert pair.control.primary_high_speed_frequency is not None
    assert pair.treatment.primary_high_speed_frequency is not None
    assert pair.control.primary_high_speed_frequency < 0.5
    assert pair.treatment.primary_high_speed_frequency > 0.5

    control_generation = pair.control.resource_generation_audit
    treatment_generation = pair.treatment.resource_generation_audit
    assert control_generation.generation_event_count == 32 * 50
    assert treatment_generation.generation_event_count == 32 * 50
    assert control_generation.total_generated_amount == 32 * 50 * 6
    assert treatment_generation.total_generated_amount == 32 * 50 * 6
    assert control_generation.compact_support_fraction is not None
    assert control_generation.compact_support_fraction < 1.0
    assert treatment_generation.compact_support_fraction == 1.0

    assert pair.control.resource_geography.compact_support_fraction is not None
    assert pair.treatment.resource_geography.compact_support_fraction is not None
    assert (
        pair.treatment.resource_geography.compact_support_fraction
        > pair.control.resource_geography.compact_support_fraction
    )
    assert pair.treatment.mechanism_episodes
