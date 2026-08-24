"""Tests for lifespan trait requirements propagated through lifecycle stages."""

from __future__ import annotations

import pytest

from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import (
    MaxSteps,
    Simulation,
    SimulationEngine,
    StageCoordinator,
    build_standard_lifecycle,
)
from evo_engine.genetics import MAXIMUM_AGE
from evo_engine.processes import Aging, MaximumAgeMortality, Metabolism, Starvation
from evo_engine.resolvers import AcceptAll
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture, make_integer_architecture


def _stage(*processes) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )


def _developmental_lifespan_lifecycle():
    return build_standard_lifecycle(
        starvation_stage=_stage(Starvation()),
        maximum_age_mortality_stage=_stage(MaximumAgeMortality()),
        metabolism_stage=_stage(
            Metabolism(cost_model=FixedMetabolicCost(amount=0)),
        ),
        aging_stage=_stage(Aging()),
    )


def test_default_age_mortality_propagates_maximum_age_requirement() -> None:
    """Test the standard lifecycle exposes nested developmental lifespan traits."""
    lifecycle = _developmental_lifespan_lifecycle()

    assert lifecycle.required_traits == frozenset({MAXIMUM_AGE})


def test_engine_rejects_missing_maximum_age_trait_before_step_zero() -> None:
    """Test developmental lifespan misconfiguration fails during preflight."""
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=make_empty_architecture(),
    )
    engine = SimulationEngine(
        step_coordinator=_developmental_lifespan_lifecycle(),
        stopping_condition=MaxSteps(max_steps=0),
    )

    with pytest.raises(ValueError, match=MAXIMUM_AGE):
        engine.run(simulation)

    assert simulation.state.step_index == 0


def test_engine_accepts_configured_maximum_age_trait() -> None:
    """Test lifespan preflight succeeds when the architecture defines the trait."""
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=make_integer_architecture(MAXIMUM_AGE),
    )
    engine = SimulationEngine(
        step_coordinator=_developmental_lifespan_lifecycle(),
        stopping_condition=MaxSteps(max_steps=0),
    )

    engine.run(simulation)

    assert simulation.state.step_index == 0
