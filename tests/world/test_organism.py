"""Tests for the Organism entity."""

from __future__ import annotations

import copy

import pytest
from attrs.exceptions import FrozenAttributeError

from evo_engine.development import DevelopmentalProfile
from evo_engine.genetics import Genome, Phenotype
from evo_engine.world import Organism
from tests.helpers import (
    make_diploid_genome,
    make_empty_architecture,
    make_empty_genome,
    make_integer_architecture,
    make_organism,
)


def test_unassigned_organism_id_raises() -> None:
    """Test that an organism has no public ID before world insertion."""
    organism = make_organism()

    with pytest.raises(RuntimeError):
        _ = organism.id


def test_assign_id_is_permanent() -> None:
    """Test that an organism ID can be assigned only once."""
    organism = make_organism()

    organism._assign_id(3)

    assert organism.id == 3

    with pytest.raises(RuntimeError):
        organism._assign_id(4)


@pytest.mark.parametrize("organism_id", [True, -1, 1.0, "1"])
def test_assign_id_rejects_invalid_ids(organism_id: object) -> None:
    """Test that organism IDs remain nonnegative exact integers."""
    organism = make_organism()

    with pytest.raises((TypeError, ValueError)):
        organism._assign_id(organism_id)  # type: ignore[arg-type]


def test_from_genome_expresses_phenotype() -> None:
    """Test that from_genome derives phenotype from the architecture."""
    architecture = make_integer_architecture("adult_body_mass")
    genome = make_diploid_genome(
        architecture,
        {"adult_body_mass": 8},
    )

    organism = Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
    )

    assert organism.genome is genome
    assert organism.phenotype["adult_body_mass"] == 8


def test_genome_and_phenotype_are_frozen_on_organism() -> None:
    """Test that lifetime genetic state cannot be replaced directly."""
    organism = make_organism()

    with pytest.raises(FrozenAttributeError):
        organism.genome = Genome(chromosomes=())

    with pytest.raises(FrozenAttributeError):
        organism.phenotype = Phenotype(trait_values=())

    with pytest.raises(FrozenAttributeError):
        organism.developmental_profile = DevelopmentalProfile(target_values=())


def test_age_step_increments_age() -> None:
    """Test that age_step increments exactly one timestep."""
    organism = make_organism(age=4)

    organism.age_step()

    assert organism.age == 5


@pytest.mark.parametrize(
    ("initial_energy", "delta", "expected"),
    [
        (10, 5, 15),
        (10, -4, 6),
        (10, -20, 0),
        (0, 0, 0),
    ],
)
def test_change_energy_updates_and_clamps(
    initial_energy: int,
    delta: int,
    expected: int,
) -> None:
    """Test signed energy changes and zero clamping."""
    organism = make_organism(energy=initial_energy)

    organism.change_energy(delta)

    assert organism.energy == expected


@pytest.mark.parametrize("delta", [True, 1.0, "1", None])
def test_change_energy_rejects_non_int_delta(delta: object) -> None:
    """Test that energy changes require exact integers."""
    organism = make_organism()

    with pytest.raises(TypeError):
        organism.change_energy(delta)  # type: ignore[arg-type]


def test_deepcopy_shares_immutable_genetics() -> None:
    """Test that deep copies duplicate mutable state but share genetics."""
    architecture = make_empty_architecture()
    organism = Organism(
        age=2,
        energy=30,
        genome=make_empty_genome(),
        phenotype=architecture.express(make_empty_genome()),
        developmental_profile=DevelopmentalProfile(target_values=()),
        x=1,
        y=2,
    )
    organism._assign_id(9)

    copied = copy.deepcopy(organism)

    assert copied is not organism
    assert copied.genome is organism.genome
    assert copied.phenotype is organism.phenotype
    assert copied.developmental_profile is organism.developmental_profile
    assert copied.id == organism.id

    copied.energy = 1
    copied.x = 5

    assert organism.energy == 30
    assert organism.x == 1


def test_from_genome_initializes_current_mass_from_adult_mass_trait() -> None:
    """Test inherited adult target mass seeds current mass by default."""
    architecture = make_integer_architecture("adult_body_mass")
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={"adult_body_mass": 8},
    )

    assert organism.body_mass == 8
    assert organism.phenotype["adult_body_mass"] == 8


def test_current_body_mass_can_differ_from_heritable_adult_target() -> None:
    """Test mutable developmental state is separate from fixed phenotype."""
    architecture = make_integer_architecture("adult_body_mass")
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={"adult_body_mass": 12},
        body_mass=3,
    )

    organism.body_mass = 5

    assert organism.body_mass == 5
    assert organism.phenotype["adult_body_mass"] == 12


def test_deepcopy_copies_current_mass_independently() -> None:
    """Test transactional organism copies isolate mutable physical mass."""
    import copy

    organism = make_organism(body_mass=4)
    copied = copy.deepcopy(organism)

    copied.body_mass = 7

    assert organism.body_mass == 4
    assert copied.body_mass == 7
    assert copied.genome is organism.genome
    assert copied.phenotype is organism.phenotype
    assert copied.developmental_profile is organism.developmental_profile


def test_from_genome_can_realize_developmental_target() -> None:
    """Test genotype expression and developmental variation stay separate."""
    import random

    from evo_engine.development import (
        GaussianIntegerDevelopment,
        IndependentDevelopment,
    )
    from evo_engine.genetics import ADULT_BODY_MASS

    architecture = make_integer_architecture(ADULT_BODY_MASS)
    genome = make_diploid_genome(
        architecture,
        {ADULT_BODY_MASS: 20},
    )

    organism = Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
        development_model=IndependentDevelopment(
            trait_models=(
                (
                    ADULT_BODY_MASS,
                    GaussianIntegerDevelopment(
                        standard_deviation=2,
                        minimum=1,
                    ),
                ),
            ),
        ),
        rng=random.Random(1),
    )

    assert organism.phenotype[ADULT_BODY_MASS] == 20
    assert organism.developmental_profile[ADULT_BODY_MASS] == 23
    assert organism.body_mass == 23


def test_from_genome_requires_rng_for_explicit_development_model() -> None:
    """Test stochastic-development configuration cannot use hidden randomness."""
    from evo_engine.development import DeterministicDevelopment

    architecture = make_empty_architecture()

    with pytest.raises(ValueError):
        Organism.from_genome(
            genetic_architecture=architecture,
            genome=make_empty_genome(),
            development_model=DeterministicDevelopment(),
        )
