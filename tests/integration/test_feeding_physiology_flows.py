"""Integration tests for feeding physiology and resource competition."""

from __future__ import annotations

from evo_engine.engine import StageCoordinator
from evo_engine.feeding import (
    GeneticPhenotypeAssimilationEfficiency,
    GeneticPhenotypeIntakeCapacity,
)
from evo_engine.genetics import ASSIMILATION_EFFICIENCY, MAX_INTAKE_RATE
from evo_engine.processes import ResourceConsumption
from evo_engine.resolvers.resource_allocation import EqualShare
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_intake_capacity_and_assimilation_shape_resource_competition_outcomes() -> None:
    """Test food allocation stays separate from organism energy assimilation."""
    architecture = make_integer_architecture(
        MAX_INTAKE_RATE,
        ASSIMILATION_EFFICIENCY,
    )
    state = make_state(
        genetic_architecture=architecture,
    )
    low_capacity_parent = add_organism(
        state,
        trait_values={
            MAX_INTAKE_RATE: 2,
            ASSIMILATION_EFFICIENCY: 50,
        },
        energy=10,
        x=1,
        y=1,
    )
    high_capacity_parent = add_organism(
        state,
        trait_values={
            MAX_INTAKE_RATE: 6,
            ASSIMILATION_EFFICIENCY: 100,
        },
        energy=10,
        x=1,
        y=1,
    )
    state.domain_state.add_resources(
        x=1,
        y=1,
        amount=6,
    )
    stage = StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=10,
                intake_capacity_model=GeneticPhenotypeIntakeCapacity(),
                assimilation_model=GeneticPhenotypeAssimilationEfficiency(),
            ),
        ),
        resolver=EqualShare(),
    )

    stage.coordinate(state)

    assert low_capacity_parent.energy == 11
    assert high_capacity_parent.energy == 14
    assert (1, 1) not in state.domain_state.resources
