"""Tests for lifespan trait requirements propagated through lifecycle stages."""

from __future__ import annotations

import pytest

from evo_engine.biology import build_standard_lifecycle
from evo_engine.configuration import SimulationSpec
from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import MaxSteps, StageCoordinator
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


def _lifespan_spec(*, architecture) -> SimulationSpec:
    return SimulationSpec(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        step_coordinator=_developmental_lifespan_lifecycle(),
        stopping_condition=MaxSteps(max_steps=0),
    )


def test_default_age_mortality_propagates_maximum_age_requirement() -> None:
    """Test the standard lifecycle exposes nested developmental lifespan traits."""
    lifecycle = _developmental_lifespan_lifecycle()

    assert lifecycle.required_traits == frozenset({MAXIMUM_AGE})


def test_compile_rejects_missing_maximum_age_trait_before_runtime() -> None:
    """Test developmental lifespan misconfiguration fails during compilation."""
    spec = _lifespan_spec(architecture=make_empty_architecture())

    with pytest.raises(ValueError, match=MAXIMUM_AGE):
        spec.compile()


def test_compile_accepts_configured_maximum_age_trait() -> None:
    """Test lifespan preflight succeeds when the architecture defines the trait."""
    spec = _lifespan_spec(architecture=make_integer_architecture(MAXIMUM_AGE))

    compiled = spec.compile()

    assert compiled.simulation.state.step_index == 0
