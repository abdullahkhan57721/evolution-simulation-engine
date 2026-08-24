"""Tests for sensory-range models."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.behavior import (
    FixedSensoryRange,
    GeneticPhenotypeSensoryRange,
    SensoryRangeModel,
    determine_sensory_range,
)
from evo_engine.genetics.builtin_traits import SENSORY_RANGE
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_fixed_sensory_range_returns_configured_radius() -> None:
    """Test fixed sensing is independent of organism genetics."""
    state = make_state()
    organism = add_organism(state)

    assert (
        FixedSensoryRange(radius=4).determine_range(
            organism,
            simulation_state=state,
        )
        == 4
    )


@pytest.mark.parametrize(
    "radius",
    [
        -1,
        1.0,
        True,
        "1",
        None,
    ],
)
def test_fixed_sensory_range_rejects_invalid_radius(radius: object) -> None:
    """Test fixed sensory radius must be a nonnegative integer."""
    with pytest.raises((TypeError, ValueError)):
        FixedSensoryRange(radius=radius)  # type: ignore[arg-type]


def test_genetic_sensory_range_reads_expressed_trait() -> None:
    """Test trait-driven sensing uses the organism's genetic phenotype."""
    architecture = make_integer_architecture(SENSORY_RANGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={SENSORY_RANGE: 6},
    )
    model = GeneticPhenotypeSensoryRange()

    assert model.determine_range(organism, simulation_state=state) == 6
    assert model.required_traits == frozenset({SENSORY_RANGE})


def test_genetic_sensory_range_rejects_negative_expressed_trait() -> None:
    """Test sensory-range semantics reject negative expressed values."""
    architecture = make_integer_architecture(SENSORY_RANGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={SENSORY_RANGE: -1},
    )

    with pytest.raises(ValueError):
        GeneticPhenotypeSensoryRange().determine_range(
            organism,
            simulation_state=state,
        )


def test_sensory_range_protocol_accepts_structural_implementation() -> None:
    """Test custom sensory models need not inherit from engine classes."""

    class CustomRange:
        def determine_range(self, organism, *, simulation_state) -> int:
            return 2

    assert isinstance(CustomRange(), SensoryRangeModel)


def test_determine_sensory_range_validates_custom_model_output() -> None:
    """Test the sensing boundary validates custom model return values."""

    class InvalidRange:
        def determine_range(self, organism, *, simulation_state):
            return -1

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_sensory_range(
            cast(SensoryRangeModel, InvalidRange()),
            organism,
            simulation_state=state,
        )
