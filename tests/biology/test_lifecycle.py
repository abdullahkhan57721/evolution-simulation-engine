"""Tests for the standard biological and ecological lifecycle preset."""

from __future__ import annotations

import attrs

from evo_engine.biology import build_standard_lifecycle
from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import StageCoordinator
from evo_engine.processes import Aging, MaximumAgeMortality, Metabolism, Starvation
from evo_engine.resolvers import AcceptAll
from evo_engine.validation import attrs_validators
from tests.helpers import add_organism, make_state


def _stage(*processes) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )


class BirthAtBoundary:
    """Test process that inserts one age-zero organism when applied."""

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent one boundary birth."""

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    @property
    def event_type(self) -> type[BirthAtBoundary.Event]:
        """Return the boundary-birth event type."""
        return self.Event

    def propose_events(self, simulation_state):
        """Propose one boundary birth."""
        return [self.Event(step_index=simulation_state.step_index)]

    def apply_event(self, simulation_state, resolved_event):
        """Insert one age-zero organism."""
        add_organism(simulation_state, age=0)


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
        aging,
        maximum_age,
        reproduction,
        starvation,
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
        aging,
        maximum_age,
        starvation,
    )


def test_entry_max_age_checkpoint_prevents_overage_turn() -> None:
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


def test_boundary_birth_occurs_after_aging_and_newborn_remains_age_zero() -> None:
    """Test standard ordering does not age offspring during their birth step."""
    state = make_state()
    founder = add_organism(
        state,
        age=0,
        energy=10,
    )
    lifecycle = build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(
            MaximumAgeMortality(maximum_age=10),
        ),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=0)),
        ),
        aging_stage=_stage(Aging()),
        reproduction_stage=_stage(BirthAtBoundary()),
    )

    next_state = lifecycle.coordinate(state)

    assert next_state.world.organisms[founder.id].age == 1
    newborns = [
        organism
        for organism_id, organism in next_state.world.organisms.items()
        if organism_id != founder.id
    ]
    assert len(newborns) == 1
    assert newborns[0].age == 0
