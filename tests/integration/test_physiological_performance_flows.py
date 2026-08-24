"""Integration tests for heritable physiological performance."""

from __future__ import annotations

import random

from evo_engine.energetics import (
    GeneticPhenotypeCoefficient,
    LinearGrowthCost,
    PowerLawLocomotionCost,
    PowerLawMetabolicCost,
)
from evo_engine.genetics import (
    ADULT_BODY_MASS,
    GROWTH_RATE,
    LOCOMOTION_COST_COEFFICIENT,
    MAX_SPEED,
    METABOLIC_COST_COEFFICIENT,
)
from evo_engine.growth import GeneticPhenotypeGrowthRate
from evo_engine.processes import Growth, Metabolism, Movement
from evo_engine.spatial.boundary_conditions import Clamped
from tests.helpers import add_organism, make_integer_architecture, make_state


class _MoveRight:
    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        return (1, 0) if max_speed >= 1 else (0, 0)


def test_growth_rate_changes_growth_speed_and_energy_demand() -> None:
    """Test faster genetic growth realizes more mass at a larger immediate cost."""
    architecture = make_integer_architecture(
        ADULT_BODY_MASS,
        GROWTH_RATE,
    )
    state = make_state(
        genetic_architecture=architecture,
    )
    slow = add_organism(
        state,
        trait_values={
            ADULT_BODY_MASS: 10,
            GROWTH_RATE: 1,
        },
        energy=20,
        body_mass=2,
    )
    fast = add_organism(
        state,
        trait_values={
            ADULT_BODY_MASS: 10,
            GROWTH_RATE: 3,
        },
        energy=20,
        body_mass=2,
    )
    process = Growth(
        growth_model=GeneticPhenotypeGrowthRate(),
        growth_cost_model=LinearGrowthCost(
            energy_per_body_mass_unit=2,
        ),
    )

    events = process.propose_events(state)
    events_by_id = {event.organism_id: event for event in events}

    assert events_by_id[slow.id].body_mass_gain == 1
    assert events_by_id[slow.id].energy_cost == 2
    assert events_by_id[fast.id].body_mass_gain == 3
    assert events_by_id[fast.id].energy_cost == 6

    for event in events:
        process.apply_event(state, event)

    assert slow.body_mass == 3
    assert slow.energy == 18
    assert fast.body_mass == 5
    assert fast.energy == 14


def test_metabolic_coefficient_changes_mandatory_maintenance_expenditure() -> None:
    """Test genetic basal-cost variation changes energy remaining after metabolism."""
    architecture = make_integer_architecture(METABOLIC_COST_COEFFICIENT)
    state = make_state(
        genetic_architecture=architecture,
    )
    lower_cost = add_organism(
        state,
        trait_values={METABOLIC_COST_COEFFICIENT: 25},
        energy=10,
        body_mass=4,
    )
    higher_cost = add_organism(
        state,
        trait_values={METABOLIC_COST_COEFFICIENT: 50},
        energy=10,
        body_mass=4,
    )
    process = Metabolism(
        cost_model=PowerLawMetabolicCost(
            coefficient=GeneticPhenotypeCoefficient(
                trait_name=METABOLIC_COST_COEFFICIENT,
            ),
            mass_exponent=1.0,
        )
    )

    events = process.propose_events(state)
    events_by_id = {event.organism_id: event for event in events}

    assert events_by_id[lower_cost.id].energy_cost == 1
    assert events_by_id[higher_cost.id].energy_cost == 2

    for event in events:
        process.apply_event(state, event)

    assert lower_cost.energy == 9
    assert higher_cost.energy == 8


def test_locomotion_coefficient_changes_cost_of_same_displacement() -> None:
    """Test equal movement can impose genetically different energetic costs."""
    architecture = make_integer_architecture(
        MAX_SPEED,
        LOCOMOTION_COST_COEFFICIENT,
    )
    state = make_state(
        width=10,
        height=3,
        genetic_architecture=architecture,
    )
    lower_cost = add_organism(
        state,
        trait_values={
            MAX_SPEED: 1,
            LOCOMOTION_COST_COEFFICIENT: 50,
        },
        energy=10,
        body_mass=4,
        x=0,
        y=0,
    )
    higher_cost = add_organism(
        state,
        trait_values={
            MAX_SPEED: 1,
            LOCOMOTION_COST_COEFFICIENT: 150,
        },
        energy=10,
        body_mass=4,
        x=2,
        y=0,
    )
    process = Movement(
        movement_pattern=_MoveRight(),
        boundary_condition=Clamped(),
        locomotion_cost_model=PowerLawLocomotionCost(
            coefficient=GeneticPhenotypeCoefficient(
                trait_name=LOCOMOTION_COST_COEFFICIENT,
            ),
            mass_exponent=0.0,
            distance_exponent=1.0,
        ),
    )

    events = process.propose_events(state)
    events_by_id = {event.organism_id: event for event in events}

    assert events_by_id[lower_cost.id].energy_cost == 1
    assert events_by_id[higher_cost.id].energy_cost == 2

    for event in events:
        process.apply_event(state, event)

    assert (lower_cost.x, lower_cost.energy) == (1, 9)
    assert (higher_cost.x, higher_cost.energy) == (3, 8)
