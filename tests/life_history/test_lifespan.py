"""Tests for fixed and developmental maximum-age models."""

from __future__ import annotations

import pytest

from evo_engine.genetics import MAXIMUM_AGE
from evo_engine.life_history import (
    DevelopmentalMaximumAge,
    FixedMaximumAge,
    MaximumAgeModel,
    determine_maximum_age,
    validate_maximum_age_source,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


@pytest.mark.parametrize("maximum_age", [1, 2, 100])
def test_fixed_maximum_age_returns_configured_value(maximum_age: int) -> None:
    """Test fixed maximum-age models return their configured positive age."""
    state = make_state()
    organism = add_organism(state)

    assert (
        FixedMaximumAge(maximum_age=maximum_age).determine_maximum_age(
            organism,
            simulation_state=state,
        )
        == maximum_age
    )


@pytest.mark.parametrize("maximum_age", [0, -1, -100])
def test_fixed_maximum_age_rejects_nonpositive_values(maximum_age: int) -> None:
    """Test fixed maximum age must be at least one."""
    with pytest.raises(ValueError):
        FixedMaximumAge(maximum_age=maximum_age)


@pytest.mark.parametrize("maximum_age", [True, False, 1.0, "1", None])
def test_fixed_maximum_age_rejects_nonintegers(maximum_age: object) -> None:
    """Test fixed maximum age rejects booleans and non-integer values."""
    with pytest.raises(TypeError):
        FixedMaximumAge(maximum_age=maximum_age)  # type: ignore[arg-type]


def test_developmental_maximum_age_reads_default_builtin_trait() -> None:
    """Test developmental lifespan reads the canonical maximum-age target."""
    architecture = make_integer_architecture(MAXIMUM_AGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAXIMUM_AGE: 12},
    )
    model = DevelopmentalMaximumAge()

    assert model.required_traits == frozenset({MAXIMUM_AGE})
    assert model.determine_maximum_age(organism, simulation_state=state) == 12


def test_developmental_maximum_age_supports_custom_trait_name() -> None:
    """Test custom simulations can use a noncanonical lifespan trait."""
    architecture = make_integer_architecture("lifespan")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"lifespan": 9},
    )
    model = DevelopmentalMaximumAge(trait_name="lifespan")

    assert model.required_traits == frozenset({"lifespan"})
    assert model.determine_maximum_age(organism, simulation_state=state) == 9


def test_developmental_maximum_age_rejects_nonpositive_target() -> None:
    """Test developmental maximum age must remain biologically positive."""
    architecture = make_integer_architecture(MAXIMUM_AGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAXIMUM_AGE: 0},
    )

    with pytest.raises(ValueError):
        DevelopmentalMaximumAge().determine_maximum_age(
            organism,
            simulation_state=state,
        )


def test_developmental_maximum_age_rejects_blank_trait_name() -> None:
    """Test lifespan trait names must be usable mapping keys."""
    with pytest.raises(ValueError):
        DevelopmentalMaximumAge(trait_name=" ")


def test_maximum_age_model_protocol_is_structural() -> None:
    """Test custom lifespan models need not inherit from an engine base class."""

    class CustomMaximumAge:
        def determine_maximum_age(self, organism, *, simulation_state):
            return 7

    assert isinstance(CustomMaximumAge(), MaximumAgeModel)


def test_determine_maximum_age_accepts_plain_integer() -> None:
    """Test callers may use a plain integer for simple fixed lifespans."""
    state = make_state()
    organism = add_organism(state)

    assert determine_maximum_age(4, organism, simulation_state=state) == 4


def test_determine_maximum_age_validates_custom_model_return_value() -> None:
    """Test malformed custom lifespan outputs fail at the shared boundary."""

    class InvalidMaximumAge:
        def determine_maximum_age(self, organism, *, simulation_state):
            return 0

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_maximum_age(
            InvalidMaximumAge(),
            organism,
            simulation_state=state,
        )


@pytest.mark.parametrize("value", [True, False, 0.5, "5", object()])
def test_validate_maximum_age_source_rejects_invalid_sources(value: object) -> None:
    """Test malformed maximum-age sources fail during configuration."""
    with pytest.raises(TypeError):
        validate_maximum_age_source(value)
