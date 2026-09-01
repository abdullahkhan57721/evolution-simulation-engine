"""Tests for environment-aware developmental realization."""

from __future__ import annotations

import random

import pytest

from evo_engine.development import (
    DevelopmentLocation,
    EnvironmentalThresholdDevelopment,
    GenotypeScaledEnvironmentalDevelopment,
    IndependentDevelopment,
    LinearEnvironmentalDevelopment,
    WorldMeanEnvironmentalSampling,
)
from evo_engine.engine import SimulationState
from evo_engine.genetics import GeneticPhenotype
from evo_engine.world import EnvironmentalField, WorldState
from tests.helpers import make_empty_architecture


def _state() -> SimulationState:
    world = WorldState(
        width=2,
        height=2,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20),
        ),
    )
    return SimulationState(
        domain_state=world,
        genetic_architecture=make_empty_architecture(),
        rng=random.Random(1),
    )


def test_linear_environmental_development_uses_local_exposure() -> None:
    """Test additive plasticity samples the explicit developmental location."""
    state = _state()
    state.domain_state.set_environmental_value("temperature", x=1, y=1, value=30)
    model = LinearEnvironmentalDevelopment(
        environmental_field_name="temperature",
        reference_environment=20,
        slope=0.5,
    )

    assert (
        model.develop(
            10,
            rng=state.rng,
            simulation_state=state,
            location=DevelopmentLocation(x=1, y=1),
        )
        == 15
    )


def test_genotype_scaled_environment_has_different_reaction_norm_slopes() -> None:
    """Test the environmental response magnitude depends on genetic value."""
    state = _state()
    state.domain_state.set_environmental_value("temperature", x=0, y=0, value=30)
    model = GenotypeScaledEnvironmentalDevelopment(
        environmental_field_name="temperature",
        reference_environment=20,
        sensitivity=0.01,
    )
    location = DevelopmentLocation(x=0, y=0)

    low_genotype = model.develop(
        10,
        rng=state.rng,
        simulation_state=state,
        location=location,
    )
    high_genotype = model.develop(
        20,
        rng=state.rng,
        simulation_state=state,
        location=location,
    )

    assert low_genotype == 11
    assert high_genotype == 22


def test_independent_development_propagates_location_to_trait_models() -> None:
    """Test environment-aware trait models compose with IndependentDevelopment."""
    state = _state()
    state.domain_state.set_environmental_value("temperature", x=1, y=0, value=24)
    phenotype = GeneticPhenotype(trait_values=(("size", 10), ("other", 7)))
    model = IndependentDevelopment(
        trait_models=(
            (
                "size",
                LinearEnvironmentalDevelopment(
                    environmental_field_name="temperature",
                    reference_environment=20,
                    slope=1,
                ),
            ),
        )
    )

    profile = model.develop(
        phenotype,
        rng=state.rng,
        simulation_state=state,
        location=DevelopmentLocation(x=1, y=0),
    )

    assert profile.target_values == (("size", 14), ("other", 7))


def test_world_mean_sampling_supports_global_developmental_exposure() -> None:
    """Test global exposure is explicit and independent of a location."""
    state = _state()
    state.domain_state.set_environmental_value("temperature", x=0, y=0, value=28)
    state.domain_state.set_environmental_value("temperature", x=1, y=0, value=24)
    model = EnvironmentalThresholdDevelopment(
        environmental_field_name="temperature",
        threshold=22,
        below_value="type_a",
        at_or_above_value="type_b",
        sampling=WorldMeanEnvironmentalSampling(),
    )

    assert (
        model.develop(
            "genetic_default",
            rng=state.rng,
            simulation_state=state,
        )
        == "type_b"
    )


def test_local_environmental_development_requires_location_and_state() -> None:
    """Test missing environmental context fails instead of guessing exposure."""
    model = LinearEnvironmentalDevelopment(
        environmental_field_name="temperature",
        reference_environment=20,
        slope=1,
    )

    with pytest.raises(ValueError, match="simulation_state"):
        model.develop(10, rng=random.Random(1))

    with pytest.raises(ValueError, match="location"):
        model.develop(
            10,
            rng=random.Random(1),
            simulation_state=_state(),
        )
