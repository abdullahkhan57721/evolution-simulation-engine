"""Integration tests for multi-component simulation flows."""

from __future__ import annotations

import pytest

from evo_engine.behavior import UnrestrictedBehavior
from evo_engine.energetics import FixedMetabolicCost, LinearGrowthCost
from evo_engine.engine import SequentialStepCoordinator, Simulation, StageCoordinator
from evo_engine.genetics import ClonalInheritance
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import (
    Growth,
    Metabolism,
    Reproduction,
    ResourceConsumption,
    Starvation,
)
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.resource_allocation import EqualShare
from evo_engine.world import WorldState
from tests.helpers import (
    add_organism,
    make_empty_architecture,
    make_integer_architecture,
    make_organism,
)


def test_resource_competition_resolves_before_application() -> None:
    """Test simultaneous local requests share pre-application resources."""
    architecture = make_empty_architecture()
    world = WorldState(
        width=3,
        height=3,
    )
    simulation = Simulation(
        initial_domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    first = add_organism(
        simulation.state,
        energy=0,
        x=1,
        y=1,
    )
    second = add_organism(
        simulation.state,
        energy=0,
        x=1,
        y=1,
    )
    simulation.state.domain_state.add_resources(
        x=1,
        y=1,
        amount=5,
    )

    StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=5,
            ),
        ),
        resolver=EqualShare(),
    ).coordinate(simulation.state)

    assert first.energy == 3
    assert second.energy == 2
    assert (1, 1) not in simulation.state.domain_state.resources


def test_metabolism_then_starvation_across_sequential_stages() -> None:
    """Test later stages observe mutations from earlier stages in a step."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    world = WorldState(
        width=3,
        height=3,
    )
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={ADULT_BODY_MASS: 4},
        energy=2,
    )
    world.add_organism(organism)
    simulation = Simulation(
        initial_domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )

    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(
                    Metabolism(
                        cost_model=FixedMetabolicCost(
                            amount=2,
                        ),
                    ),
                ),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(Starvation(),),
                resolver=AcceptAll(),
            ),
        )
    )

    simulation.state = coordinator.coordinate(simulation.state)

    assert not simulation.state.domain_state.organisms
    assert (
        next(iter(simulation.state.domain_state.carcasses.values())).resource_units == 4
    )


def test_reproduction_materializes_only_resolved_births() -> None:
    """Test reproduction integrates with the stage materialization phase."""
    architecture = make_integer_architecture(
        "offspring_energy",
    )
    world = WorldState(
        width=3,
        height=3,
    )
    parent = make_organism(
        genetic_architecture=architecture,
        trait_values={"offspring_energy": 5},
        energy=20,
    )
    world.add_organism(parent)
    simulation = Simulation(
        initial_domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
        seed=2,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )

    StageCoordinator(
        processes=(process,),
        resolver=AcceptAll(),
    ).coordinate(simulation.state)

    assert len(simulation.state.domain_state.organisms) == 2
    assert simulation.state.domain_state.organisms[0].energy == 15
    assert simulation.state.domain_state.organisms[1].energy == 5


def test_growth_then_starvation_uses_grown_body_mass_for_carcass() -> None:
    """Test final growth energy can cause later starvation at updated mass."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    world = WorldState(
        width=3,
        height=3,
    )
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={ADULT_BODY_MASS: 5},
        body_mass=3,
        energy=2,
    )
    world.add_organism(organism)
    simulation = Simulation(
        initial_domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(
                    Growth(
                        growth_model=FixedGrowthRate(
                            amount_per_timestep=2,
                        ),
                        growth_cost_model=LinearGrowthCost(
                            energy_per_body_mass_unit=1,
                        ),
                    ),
                ),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(Starvation(),),
                resolver=AcceptAll(),
            ),
        )
    )

    simulation.state = coordinator.coordinate(simulation.state)

    assert not simulation.state.domain_state.organisms
    carcass = next(iter(simulation.state.domain_state.carcasses.values()))
    assert carcass.resource_units == 5


def test_same_stage_growth_energy_oversubscription_rolls_back_step() -> None:
    """Test stale Growth affordability fails transactionally within a step."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    world = WorldState(
        width=3,
        height=3,
    )
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={ADULT_BODY_MASS: 12},
        body_mass=10,
        energy=5,
    )
    world.add_organism(organism)
    simulation = Simulation(
        initial_domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(
                    Metabolism(
                        cost_model=FixedMetabolicCost(
                            amount=3,
                        ),
                    ),
                    Growth(
                        growth_model=FixedGrowthRate(
                            amount_per_timestep=2,
                        ),
                        growth_cost_model=LinearGrowthCost(
                            energy_per_body_mass_unit=2,
                        ),
                    ),
                ),
                resolver=AcceptAll(),
            ),
        )
    )

    with pytest.raises(RuntimeError, match="no longer affordable"):
        coordinator.coordinate(simulation.state)

    authoritative = simulation.state.domain_state.organisms[organism.id]
    assert authoritative.body_mass == 10
    assert authoritative.energy == 5
    assert simulation.state.step_index == 0
