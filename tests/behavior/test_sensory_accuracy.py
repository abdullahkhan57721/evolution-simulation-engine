"""Tests for sensory accuracy models."""

from __future__ import annotations

import pytest

from evo_engine.behavior import (
    FixedSensoryAccuracy,
    GeneticPhenotypeSensoryAccuracy,
    SensoryAccuracyModel,
    determine_sensory_accuracy,
)
from evo_engine.genetics import SENSORY_ACCURACY
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_fixed_sensory_accuracy_returns_configured_percentage() -> None:
    """Test fixed sensory accuracy is deterministic configuration."""
    state = make_state()
    organism = add_organism(state)

    assert (
        determine_sensory_accuracy(
            FixedSensoryAccuracy(accuracy_percent=37),
            organism,
            simulation_state=state,
        )
        == 37
    )


@pytest.mark.parametrize("accuracy_percent", [-1, 101, True, 1.5])
def test_fixed_sensory_accuracy_rejects_invalid_percentages(
    accuracy_percent: object,
) -> None:
    """Test sensory accuracy remains a bounded integer percentage."""
    with pytest.raises((TypeError, ValueError)):
        FixedSensoryAccuracy(accuracy_percent=accuracy_percent)  # type: ignore[arg-type]


def test_genetic_sensory_accuracy_reads_trait_and_declares_requirement() -> None:
    """Test expressed sensory accuracy participates in trait preflight."""
    architecture = make_integer_architecture(SENSORY_ACCURACY)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={SENSORY_ACCURACY: 72},
    )
    model = GeneticPhenotypeSensoryAccuracy()

    assert model.required_traits == frozenset({SENSORY_ACCURACY})
    assert (
        determine_sensory_accuracy(
            model,
            organism,
            simulation_state=state,
        )
        == 72
    )


def test_sensory_accuracy_protocol_accepts_structural_implementation() -> None:
    """Test custom sensory models need not inherit from engine classes."""

    class CustomAccuracy:
        def determine_accuracy_percent(self, organism, *, simulation_state) -> int:
            return 50

    assert isinstance(CustomAccuracy(), SensoryAccuracyModel)


def test_determine_sensory_accuracy_rejects_invalid_model_output() -> None:
    """Test the public model boundary validates custom return values."""

    class InvalidAccuracy:
        def determine_accuracy_percent(self, organism, *, simulation_state) -> int:
            return 101

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_sensory_accuracy(
            InvalidAccuracy(),
            organism,
            simulation_state=state,
        )
