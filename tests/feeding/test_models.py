"""Tests for feeding physiology models."""

from __future__ import annotations

import pytest

from evo_engine.feeding import (
    FixedAssimilationEfficiency,
    FixedIntakeCapacity,
    FullAssimilation,
    GeneticPhenotypeAssimilationEfficiency,
    GeneticPhenotypeIntakeCapacity,
    determine_assimilated_energy,
    determine_intake_capacity,
)
from evo_engine.genetics import ASSIMILATION_EFFICIENCY, MAX_INTAKE_RATE
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_fixed_intake_capacity_returns_configured_amount() -> None:
    """Test fixed intake capacity ignores organism-specific state."""
    state = make_state()
    organism = add_organism(state)

    assert (
        determine_intake_capacity(
            FixedIntakeCapacity(amount=7),
            organism,
            simulation_state=state,
        )
        == 7
    )


def test_genetic_intake_capacity_reads_trait_and_declares_requirement() -> None:
    """Test genetically expressed maximum intake drives capacity."""
    architecture = make_integer_architecture(MAX_INTAKE_RATE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAX_INTAKE_RATE: 6},
    )
    model = GeneticPhenotypeIntakeCapacity()

    assert model.required_traits == frozenset({MAX_INTAKE_RATE})
    assert determine_intake_capacity(model, organism, simulation_state=state) == 6


def test_intake_capacity_rejects_negative_model_output() -> None:
    """Test intake-capacity helper enforces a nonnegative integer contract."""
    state = make_state()
    organism = add_organism(state)

    class NegativeCapacity:
        def determine_capacity(self, organism, *, simulation_state):
            return -1

    with pytest.raises(ValueError, match="intake capacity"):
        determine_intake_capacity(
            NegativeCapacity(),
            organism,
            simulation_state=state,
        )


def test_full_assimilation_converts_resources_one_for_one() -> None:
    """Test default assimilation preserves historical one-to-one conversion."""
    state = make_state()
    organism = add_organism(state)

    assert (
        determine_assimilated_energy(
            FullAssimilation(),
            organism,
            consumed_amount=5,
            simulation_state=state,
        )
        == 5
    )


@pytest.mark.parametrize(
    ("consumed_amount", "efficiency_percent", "expected_energy"),
    [
        (4, 0, 0),
        (3, 50, 2),
        (4, 75, 3),
        (4, 100, 4),
    ],
)
def test_fixed_assimilation_efficiency_uses_half_up_rounding(
    consumed_amount: int,
    efficiency_percent: int,
    expected_energy: int,
) -> None:
    """Test percentage assimilation and deterministic integer rounding."""
    state = make_state()
    organism = add_organism(state)

    energy_gain = determine_assimilated_energy(
        FixedAssimilationEfficiency(
            efficiency_percent=efficiency_percent,
        ),
        organism,
        consumed_amount=consumed_amount,
        simulation_state=state,
    )

    assert energy_gain == expected_energy


def test_genetic_assimilation_reads_trait_and_declares_requirement() -> None:
    """Test genetically expressed assimilation efficiency controls energy gain."""
    architecture = make_integer_architecture(ASSIMILATION_EFFICIENCY)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={ASSIMILATION_EFFICIENCY: 25},
    )
    model = GeneticPhenotypeAssimilationEfficiency()

    assert model.required_traits == frozenset({ASSIMILATION_EFFICIENCY})
    assert (
        determine_assimilated_energy(
            model,
            organism,
            consumed_amount=6,
            simulation_state=state,
        )
        == 2
    )


def test_genetic_assimilation_rejects_efficiency_above_one_hundred() -> None:
    """Test expressed percentage efficiencies remain biologically bounded."""
    architecture = make_integer_architecture(ASSIMILATION_EFFICIENCY)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={ASSIMILATION_EFFICIENCY: 101},
    )

    with pytest.raises(ValueError, match="assimilation_efficiency"):
        determine_assimilated_energy(
            GeneticPhenotypeAssimilationEfficiency(),
            organism,
            consumed_amount=4,
            simulation_state=state,
        )


def test_assimilation_helper_rejects_negative_model_output() -> None:
    """Test assimilation helper enforces nonnegative energy output."""
    state = make_state()
    organism = add_organism(state)

    class NegativeAssimilation:
        def determine_energy_gain(
            self,
            organism,
            *,
            consumed_amount,
            simulation_state,
        ):
            return -1

    with pytest.raises(ValueError, match="assimilated energy gain"):
        determine_assimilated_energy(
            NegativeAssimilation(),
            organism,
            consumed_amount=1,
            simulation_state=state,
        )
