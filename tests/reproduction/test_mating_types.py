"""Tests for general mating-type compatibility and offspring assignment."""

from __future__ import annotations

import random

import pytest

from evo_engine.development import DevelopmentalProfile
from evo_engine.genetics import GeneticPhenotype
from evo_engine.reproduction import (
    DevelopmentalProfileMatingType,
    DifferentMatingTypes,
    FixedMatingType,
    GeneticPhenotypeMatingType,
    OffspringMatingTypeModel,
    RandomMatingType,
    determine_offspring_mating_type,
)
from tests.helpers import make_organism, make_state


def _determine(
    model: OffspringMatingTypeModel,
    *,
    state_seed: int = 1,
) -> tuple[str, random.Random, random.Random]:
    state = make_state(seed=state_seed)
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())
    offspring = make_organism()
    mating_type = determine_offspring_mating_type(
        model,
        (make_organism(),),
        offspring_genome=offspring.genome,
        offspring_genetic_phenotype=offspring.genetic_phenotype,
        offspring_developmental_profile=offspring.developmental_profile,
        simulation_state=state,
        rng=state.rng,
    )
    return mating_type, state.rng, expected_rng


def test_different_mating_types_accepts_unlike_labels() -> None:
    """Test compatibility depends on mating-type identity, not label semantics."""
    state = make_state()
    first = make_organism(mating_type="alpha")
    second = make_organism(mating_type="beta")

    assert DifferentMatingTypes()(first, second, state) is True


def test_different_mating_types_rejects_matching_labels() -> None:
    """Test organisms sharing a mating type are incompatible under the rule."""
    state = make_state()
    first = make_organism(mating_type="alpha")
    second = make_organism(mating_type="alpha")

    assert DifferentMatingTypes()(first, second, state) is False


def test_fixed_mating_type_does_not_advance_rng() -> None:
    """Test deterministic assignment leaves the simulation RNG untouched."""
    mating_type, actual_rng, expected_rng = _determine(
        FixedMatingType(mating_type="worker"),
        state_seed=17,
    )

    assert mating_type == "worker"
    assert actual_rng.random() == expected_rng.random()


def test_random_mating_type_uses_supplied_rng() -> None:
    """Test stochastic assignment is reproducible from the supplied RNG state."""
    model = RandomMatingType(mating_types=("alpha", "beta", "gamma"))
    actual, actual_rng, expected_rng = _determine(model, state_seed=23)

    assert actual == expected_rng.choice(model.mating_types)
    assert actual_rng.random() == expected_rng.random()


def test_genetic_phenotype_mating_type_reads_offspring_expression() -> None:
    """Test genetic assignment reads the offspring rather than either parent."""
    state = make_state()
    offspring = make_organism()
    phenotype = GeneticPhenotype(
        trait_values=(("reproductive_identity", "genetic_type"),),
    )
    profile = DevelopmentalProfile(
        target_values=(("reproductive_identity", "developmental_type"),),
    )
    model = GeneticPhenotypeMatingType(trait_name="reproductive_identity")

    actual = determine_offspring_mating_type(
        model,
        (make_organism(mating_type="parent_type"),),
        offspring_genome=offspring.genome,
        offspring_genetic_phenotype=phenotype,
        offspring_developmental_profile=profile,
        simulation_state=state,
        rng=state.rng,
    )

    assert actual == "genetic_type"
    assert model.required_traits == frozenset({"reproductive_identity"})


def test_developmental_profile_mating_type_reads_realized_offspring_value() -> None:
    """Test developmental assignment can differ from genetic expectation."""
    state = make_state()
    offspring = make_organism()
    phenotype = GeneticPhenotype(
        trait_values=(("reproductive_identity", "genetic_type"),),
    )
    profile = DevelopmentalProfile(
        target_values=(("reproductive_identity", "environmental_type"),),
    )
    model = DevelopmentalProfileMatingType(trait_name="reproductive_identity")

    actual = determine_offspring_mating_type(
        model,
        (make_organism(),),
        offspring_genome=offspring.genome,
        offspring_genetic_phenotype=phenotype,
        offspring_developmental_profile=profile,
        simulation_state=state,
        rng=state.rng,
    )

    assert actual == "environmental_type"
    assert model.required_traits == frozenset({"reproductive_identity"})


@pytest.mark.parametrize(
    "model",
    [
        GeneticPhenotypeMatingType(trait_name="reproductive_identity"),
        DevelopmentalProfileMatingType(trait_name="reproductive_identity"),
    ],
)
def test_state_aware_mating_type_models_require_string_labels(
    model: OffspringMatingTypeModel,
) -> None:
    """Test categorical assignment rejects non-string offspring trait values."""
    state = make_state()
    offspring = make_organism()
    phenotype = GeneticPhenotype(trait_values=(("reproductive_identity", 1),))
    profile = DevelopmentalProfile(target_values=(("reproductive_identity", 1),))

    with pytest.raises(TypeError):
        determine_offspring_mating_type(
            model,
            (make_organism(),),
            offspring_genome=offspring.genome,
            offspring_genetic_phenotype=phenotype,
            offspring_developmental_profile=profile,
            simulation_state=state,
            rng=state.rng,
        )


@pytest.mark.parametrize(
    "mating_types",
    [
        (),
        ("alpha", "alpha"),
        ("", "beta"),
        ("   ", "beta"),
    ],
)
def test_random_mating_type_rejects_invalid_type_sets(
    mating_types: tuple[str, ...],
) -> None:
    """Test random assignment requires unique nonempty labels."""
    with pytest.raises(ValueError):
        RandomMatingType(mating_types=mating_types)


@pytest.mark.parametrize(
    "model_type",
    [GeneticPhenotypeMatingType, DevelopmentalProfileMatingType],
)
def test_state_aware_mating_type_models_reject_blank_trait_name(
    model_type: type[GeneticPhenotypeMatingType] | type[DevelopmentalProfileMatingType],
) -> None:
    """Test state-aware assignment requires a meaningful trait dependency."""
    with pytest.raises(ValueError, match="trait_name"):
        model_type(trait_name="   ")
