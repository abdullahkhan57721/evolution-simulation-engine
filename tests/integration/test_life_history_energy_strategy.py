"""Integration tests for life-history energy-strategy composition."""

from __future__ import annotations

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    REPRODUCTION,
    EnergyConservationBehavior,
    EnergyThresholdMovementIntent,
    behavior_is_allowed,
    determine_movement_purpose,
)
from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    FixedLocomotionCost,
    KeepEnergyReserve,
)
from evo_engine.engine import SimulationState
from evo_engine.genetics import (
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    MATURITY_AGE,
    MAX_SPEED,
    REPRODUCTION_ENERGY_THRESHOLD,
    ClonalInheritance,
)
from evo_engine.processes import Movement, Reproduction
from evo_engine.reproduction import (
    AllOfEligibility,
    DevelopmentalMaturityEligibility,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    MinimumEnergyEligibility,
    SingleParent,
)
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.world import WorldState
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_developmental_conservation_threshold_varies_behavior_by_organism() -> None:
    """Test heritable/developmental conservation thresholds alter behavior."""
    architecture = make_integer_architecture(ENERGY_CONSERVATION_THRESHOLD)
    threshold = DevelopmentalEnergyThreshold(trait_name=ENERGY_CONSERVATION_THRESHOLD)
    state = SimulationState(
        domain_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=threshold,
        ),
    )
    lower_threshold = add_organism(
        state,
        trait_values={ENERGY_CONSERVATION_THRESHOLD: 10},
        energy=15,
    )
    higher_threshold = add_organism(
        state,
        trait_values={ENERGY_CONSERVATION_THRESHOLD: 20},
        energy=15,
    )

    assert behavior_is_allowed(
        lower_threshold,
        behavioral_purpose=REPRODUCTION,
        simulation_state=state,
    )
    assert not behavior_is_allowed(
        higher_threshold,
        behavioral_purpose=REPRODUCTION,
        simulation_state=state,
    )

    intent = EnergyThresholdMovementIntent(energy_threshold=threshold)

    assert (
        determine_movement_purpose(
            intent,
            lower_threshold,
            simulation_state=state,
        )
        == EXPLORATION
    )
    assert (
        determine_movement_purpose(
            intent,
            higher_threshold,
            simulation_state=state,
        )
        == ENERGY_ACQUISITION
    )


def test_reproduction_layers_maturity_energy_and_reserve_requirements() -> None:
    """Test reproductive attempt, eligibility, and spending gates stay separate."""
    architecture = make_integer_architecture(
        MATURITY_AGE,
        REPRODUCTION_ENERGY_THRESHOLD,
        ENERGY_RESERVE,
    )
    state = make_state(genetic_architecture=architecture)
    parent = add_organism(
        state,
        trait_values={
            MATURITY_AGE: 5,
            REPRODUCTION_ENERGY_THRESHOLD: 20,
            ENERGY_RESERVE: 18,
        },
        age=4,
        energy=23,
    )
    process = Reproduction(
        eligibility=AllOfEligibility(
            eligibilities=(
                DevelopmentalMaturityEligibility(),
                MinimumEnergyEligibility(
                    minimum_energy=DevelopmentalEnergyThreshold(
                        trait_name=REPRODUCTION_ENERGY_THRESHOLD,
                    ),
                ),
            ),
        ),
        reproductive_group_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        energy_expenditure_policy=KeepEnergyReserve(
            minimum_energy=DevelopmentalEnergyThreshold(
                trait_name=ENERGY_RESERVE,
            ),
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )

    assert process.propose_events(state) == []

    parent.age = 5
    parent.energy = 19
    assert process.propose_events(state) == []

    parent.energy = 20
    assert process.propose_events(state) == []

    parent.energy = 23
    proposal = process.propose_events(state)[0]
    event = process.materialize_event(state, proposal)
    process.apply_event(state, event)

    assert parent.energy == 18
    assert len(state.domain_state.organisms) == 2
    assert process.required_traits == frozenset(
        {
            MATURITY_AGE,
            REPRODUCTION_ENERGY_THRESHOLD,
            ENERGY_RESERVE,
        }
    )


def test_movement_reserve_policy_blocks_then_allows_exact_reserve() -> None:
    """Test locomotion uses the same post-expenditure reserve contract."""

    class StepRight:
        def choose_displacement(self, *, rng, max_speed):
            return (1, 0)

    architecture = make_integer_architecture(MAX_SPEED, ENERGY_RESERVE)
    state = make_state(width=5, height=5, genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAX_SPEED: 1, ENERGY_RESERVE: 3},
        energy=6,
        x=1,
        y=1,
    )
    process = Movement(
        movement_pattern=StepRight(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=4),
        energy_expenditure_policy=KeepEnergyReserve(
            minimum_energy=DevelopmentalEnergyThreshold(trait_name=ENERGY_RESERVE),
        ),
    )

    assert process.propose_events(state) == []

    organism.energy = 7
    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert (organism.x, organism.y) == (2, 1)
    assert organism.energy == 3
    assert process.required_traits == frozenset({MAX_SPEED, ENERGY_RESERVE})


def test_movement_application_rechecks_reserve_before_mutating_position() -> None:
    """Test stale locomotion events fail atomically when reserve becomes unsafe."""

    class StepRight:
        def choose_displacement(self, *, rng, max_speed):
            return (1, 0)

    architecture = make_integer_architecture(MAX_SPEED, ENERGY_RESERVE)
    state = make_state(width=5, height=5, genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAX_SPEED: 1, ENERGY_RESERVE: 3},
        energy=7,
        x=1,
        y=1,
    )
    process = Movement(
        movement_pattern=StepRight(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=4),
        energy_expenditure_policy=KeepEnergyReserve(
            minimum_energy=DevelopmentalEnergyThreshold(trait_name=ENERGY_RESERVE),
        ),
    )
    event = process.propose_events(state)[0]
    organism.energy = 6

    with pytest.raises(RuntimeError, match="locomotion energy cost"):
        process.apply_event(state, event)

    assert (organism.x, organism.y) == (1, 1)
    assert organism.energy == 6


def test_default_movement_policy_can_spend_exactly_to_zero_but_not_overdraw() -> None:
    """Test default locomotion may cause later starvation without overspending."""

    class StepRight:
        def choose_displacement(self, *, rng, max_speed):
            return (1, 0)

    architecture = make_integer_architecture(MAX_SPEED)
    state = make_state(width=5, height=5, genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAX_SPEED: 1},
        energy=3,
        x=1,
        y=1,
    )
    process = Movement(
        movement_pattern=StepRight(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=4),
    )

    assert process.propose_events(state) == []

    organism.energy = 4
    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert (organism.x, organism.y) == (2, 1)
    assert organism.energy == 0
