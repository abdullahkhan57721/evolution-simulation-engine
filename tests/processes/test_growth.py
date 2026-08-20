"""Tests for the Growth simulation process."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.development import DevelopmentalProfile
from evo_engine.energetics import GrowthCostModel, LinearGrowthCost
from evo_engine.engine import SimulationState
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.growth import FixedGrowthRate, GrowthModel
from evo_engine.processes import Growth
from evo_engine.world import Organism
from tests.helpers import (
    add_organism,
    make_diploid_genome,
    make_integer_architecture,
    make_state,
)


def _add_developmentally_varied_organism(
    *,
    genetic_adult_mass: int,
    developmental_adult_mass: int,
    body_mass: int,
    energy: int = 100,
) -> tuple[SimulationState, Organism]:
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    genome = make_diploid_genome(
        architecture,
        {ADULT_BODY_MASS: genetic_adult_mass},
    )
    genetic_phenotype = architecture.express(genome)
    developmental_profile = DevelopmentalProfile(
        target_values=((ADULT_BODY_MASS, developmental_adult_mass),),
    )
    organism = Organism(
        energy=energy,
        body_mass=body_mass,
        genome=genome,
        genetic_phenotype=genetic_phenotype,
        developmental_profile=developmental_profile,
    )
    state.world.add_organism(organism)
    return state, organism


def _growth(
    *,
    gain: int = 3,
    energy_per_unit: int | float = 2,
) -> Growth:
    return Growth(
        growth_model=FixedGrowthRate(
            amount_per_timestep=gain,
        ),
        growth_cost_model=LinearGrowthCost(
            energy_per_body_mass_unit=energy_per_unit,
        ),
    )


def test_growth_uses_developmental_target_not_genetic_expectation() -> None:
    """Test realized individual target controls growth completion."""
    state, organism = _add_developmentally_varied_organism(
        genetic_adult_mass=20,
        developmental_adult_mass=22,
        body_mass=20,
    )

    events = _growth(
        gain=5,
        energy_per_unit=1,
    ).propose_events(state)

    assert events == [
        Growth.Event(
            step_index=0,
            organism_id=organism.id,
            body_mass_gain=2,
            energy_cost=2,
        )
    ]


def test_growth_caps_gain_before_pricing_energy() -> None:
    """Test organisms do not pay for growth beyond their target."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=19,
        energy=10,
    )

    events = _growth(
        gain=10,
        energy_per_unit=3,
    ).propose_events(state)

    assert events == [
        Growth.Event(
            step_index=0,
            organism_id=organism.id,
            body_mass_gain=1,
            energy_cost=3,
        )
    ]


@pytest.mark.parametrize(
    "body_mass",
    [
        20,
        25,
    ],
)
def test_growth_does_not_propose_at_or_above_target(body_mass: int) -> None:
    """Test completed growth produces no event."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=body_mass,
    )

    assert _growth().propose_events(state) == []


def test_growth_does_not_propose_when_model_returns_zero_gain() -> None:
    """Test zero potential growth produces no event."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
    )

    assert _growth(gain=0).propose_events(state) == []


def test_growth_requires_full_energy_cost() -> None:
    """Test unaffordable growth is not partially applied."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=5,
    )

    assert (
        _growth(
            gain=3,
            energy_per_unit=2,
        ).propose_events(state)
        == []
    )


def test_growth_allows_exact_energy_expenditure() -> None:
    """Test affordable growth may spend an organism's final energy unit."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=6,
    )
    process = _growth(
        gain=3,
        energy_per_unit=2,
    )
    event = process.propose_events(state)[0]

    process.apply_event(
        state,
        event,
    )

    assert organism.body_mass == 13
    assert organism.energy == 0


def test_growth_apply_rejects_stale_unaffordable_event() -> None:
    """Test same-stage energy changes cannot create unpaid body mass."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=6,
    )
    process = _growth(
        gain=3,
        energy_per_unit=2,
    )
    event = process.propose_events(state)[0]
    organism.energy = 5

    with pytest.raises(RuntimeError, match="no longer affordable"):
        process.apply_event(
            state,
            event,
        )

    assert organism.body_mass == 10
    assert organism.energy == 5


def test_growth_declares_target_and_nested_trait_requirements() -> None:
    """Test Growth aggregates configured genetic trait dependencies."""

    class TraitDrivenGrowth:
        @property
        def required_traits(self) -> frozenset[str]:
            return frozenset({"growth_rate"})

        def determine_body_mass_gain(
            self,
            organism,
            *,
            target_body_mass,
            simulation_state,
        ) -> int:
            return 1

    process = Growth(
        growth_model=TraitDrivenGrowth(),
        growth_cost_model=LinearGrowthCost(
            energy_per_body_mass_unit=1,
        ),
    )

    assert process.required_traits == frozenset(
        {
            ADULT_BODY_MASS,
            "growth_rate",
        }
    )


def test_growth_rejects_invalid_target_value() -> None:
    """Test adult body-mass developmental targets must remain positive."""
    state, _ = _add_developmentally_varied_organism(
        genetic_adult_mass=20,
        developmental_adult_mass=0,
        body_mass=1,
    )

    with pytest.raises(ValueError):
        _growth().propose_events(state)


@pytest.mark.parametrize(
    "returned_gain",
    [
        -1,
        1.5,
        True,
    ],
)
def test_growth_rejects_invalid_growth_model_return(returned_gain: object) -> None:
    """Test Growth enforces the growth-model return contract."""

    class InvalidGrowthModel:
        def determine_body_mass_gain(
            self,
            organism,
            *,
            target_body_mass,
            simulation_state,
        ):
            return returned_gain

    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
    )
    process = Growth(
        growth_model=cast(
            GrowthModel,
            InvalidGrowthModel(),
        ),
        growth_cost_model=LinearGrowthCost(
            energy_per_body_mass_unit=1,
        ),
    )

    with pytest.raises((TypeError, ValueError)):
        process.propose_events(state)


@pytest.mark.parametrize(
    "returned_cost",
    [
        -1,
        1.5,
        True,
    ],
)
def test_growth_rejects_invalid_cost_model_return(returned_cost: object) -> None:
    """Test Growth enforces the growth-cost-model return contract."""

    class InvalidCostModel:
        def calculate_cost(
            self,
            organism,
            *,
            body_mass_gain,
            simulation_state,
        ):
            return returned_cost

    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
    )
    process = Growth(
        growth_model=FixedGrowthRate(
            amount_per_timestep=1,
        ),
        growth_cost_model=cast(
            GrowthCostModel,
            InvalidCostModel(),
        ),
    )

    with pytest.raises((TypeError, ValueError)):
        process.propose_events(state)


def test_growth_rejects_blank_trait_name() -> None:
    """Test configured developmental target names must be nonblank."""
    with pytest.raises(ValueError, match="trait_name"):
        Growth(
            growth_model=FixedGrowthRate(
                amount_per_timestep=1,
            ),
            growth_cost_model=LinearGrowthCost(
                energy_per_body_mass_unit=1,
            ),
            trait_name="   ",
        )
