"""Tests for the standard ecological lifecycle preset."""

from __future__ import annotations

from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import StageCoordinator, build_standard_lifecycle
from evo_engine.processes import Aging, MaximumAgeMortality, Metabolism, Starvation
from evo_engine.resolvers import AcceptAll
from tests.helpers import add_organism, make_state


def _stage(*processes) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )


def test_standard_lifecycle_orders_checkpoints_and_optional_stages() -> None:
    """Test the preset encodes the documented lifecycle order exactly."""
    starvation = _stage()
    maximum_age = _stage()
    metabolism = _stage()
    environment = _stage()
    movement = _stage()
    predation = _stage()
    resource_consumption = _stage()
    growth = _stage()
    reproduction = _stage()
    aging = _stage()

    lifecycle = build_standard_lifecycle(
        starvation_stage=starvation,
        maximum_age_mortality_stage=maximum_age,
        metabolism_stage=metabolism,
        environment_stage=environment,
        movement_stage=movement,
        predation_stage=predation,
        resource_consumption_stage=resource_consumption,
        growth_stage=growth,
        reproduction_stage=reproduction,
        aging_stage=aging,
    )

    assert lifecycle.stages == (
        starvation,
        maximum_age,
        metabolism,
        starvation,
        environment,
        movement,
        predation,
        resource_consumption,
        growth,
        reproduction,
        starvation,
        aging,
        maximum_age,
    )


def test_standard_lifecycle_omits_optional_stages_without_dummy_placeholders() -> None:
    """Test minimal simulations can reuse the preset without empty ecology stages."""
    starvation = _stage()
    maximum_age = _stage()
    metabolism = _stage()
    aging = _stage()

    lifecycle = build_standard_lifecycle(
        starvation_stage=starvation,
        maximum_age_mortality_stage=maximum_age,
        metabolism_stage=metabolism,
        aging_stage=aging,
    )

    assert lifecycle.stages == (
        starvation,
        maximum_age,
        metabolism,
        starvation,
        starvation,
        aging,
        maximum_age,
    )


def test_entry_maximum_age_checkpoint_removes_overage_organism_before_metabolism() -> None:
    """Test an organism already at maximum age cannot begin another timestep."""
    state = make_state()
    organism = add_organism(
        state,
        age=5,
        energy=10,
        body_mass=4,
    )
    lifecycle = build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(
            MaximumAgeMortality(maximum_age=5),
        ),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=10)),
        ),
        aging_stage=_stage(Aging()),
    )

    next_state = lifecycle.coordinate(state)

    assert organism.id in state.world.organisms
    assert organism.id not in next_state.world.organisms
    assert next_state.step_index == 1
    carcass = next(iter(next_state.world.carcasses.values()))
    assert carcass.resource_units == 4


def test_post_aging_checkpoint_removes_organism_when_age_reaches_maximum() -> None:
    """Test maximum age counts completed timesteps without an extra turn."""
    state = make_state()
    organism = add_organism(
        state,
        age=4,
        energy=10,
        body_mass=3,
    )
    lifecycle = build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(
            MaximumAgeMortality(maximum_age=5),
        ),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=0)),
        ),
        aging_stage=_stage(Aging()),
    )

    next_state = lifecycle.coordinate(state)

    assert organism.id not in next_state.world.organisms
    carcass = next(iter(next_state.world.carcasses.values()))
    assert carcass.resource_units == 3


def test_post_aging_checkpoint_keeps_organism_below_maximum_age() -> None:
    """Test organisms remain active while completed age is below the limit."""
    state = make_state()
    organism = add_organism(
        state,
        age=3,
        energy=10,
    )
    lifecycle = build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(
            MaximumAgeMortality(maximum_age=5),
        ),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=0)),
        ),
        aging_stage=_stage(Aging()),
    )

    next_state = lifecycle.coordinate(state)

    assert next_state.world.organisms[organism.id].age == 4
    assert not next_state.world.carcasses


def test_post_metabolism_starvation_checkpoint_prevents_aging() -> None:
    """Test failure to pay maintenance ends the turn before later lifecycle stages."""
    state = make_state()
    organism = add_organism(
        state,
        age=2,
        energy=1,
        body_mass=2,
    )
    lifecycle = build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(
            MaximumAgeMortality(maximum_age=10),
        ),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=1)),
        ),
        aging_stage=_stage(Aging()),
    )

    next_state = lifecycle.coordinate(state)

    assert organism.id not in next_state.world.organisms
    carcass = next(iter(next_state.world.carcasses.values()))
    assert carcass.resource_units == 2
