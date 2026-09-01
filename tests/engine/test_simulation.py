"""Tests for domain-neutral Simulation behavior."""

from __future__ import annotations

import pytest

from evo_engine.context import SimulationContext
from evo_engine.engine import Simulation
from tests.engine.helpers import CounterState


def test_simulation_copies_initial_state() -> None:
    """Test callers retain an independent initial-state object."""
    initial_state = CounterState(value=20)
    simulation = Simulation(initial_world_state=initial_state, seed=3)
    simulation.state.world.value = 1
    assert initial_state.value == 20


def test_simulation_exposes_arbitrary_shared_service_through_context() -> None:
    """Test named domain configuration is consumed explicitly from context."""
    service = object()
    simulation = Simulation(
        initial_world_state=CounterState(),
        scoring_rule=service,
    )
    assert simulation.context.require("scoring_rule") is service
    assert not hasattr(simulation, "scoring_rule")
    assert not hasattr(simulation.state, "scoring_rule")


def test_simulation_seed_makes_rng_reproducible() -> None:
    """Test deterministic run-level random-number initialization."""
    first = Simulation(initial_world_state=CounterState(), seed=9)
    second = Simulation(initial_world_state=CounterState(), seed=9)
    assert first.state.rng.random() == second.state.rng.random()


@pytest.mark.parametrize("initial_world_state", [None, object(), "state"])
def test_simulation_rejects_noncopyable_state(initial_world_state: object) -> None:
    """Test Simulation requires transactionally copyable model state."""
    with pytest.raises(TypeError, match="callable copy"):
        Simulation(initial_world_state=initial_world_state)


def test_simulation_rejects_boolean_seed() -> None:
    """Test Boolean seeds are rejected despite bool being an int subclass."""
    with pytest.raises(TypeError, match="seed"):
        Simulation(initial_world_state=CounterState(), seed=True)


def test_simulation_rejects_context_mixed_with_context_values() -> None:
    """Test explicit context cannot be combined with separate services."""
    context = SimulationContext.from_mapping({"service": object()})
    with pytest.raises(TypeError, match="context cannot be combined"):
        Simulation(
            initial_world_state=CounterState(),
            context=context,
            other_service=object(),
        )


def test_missing_context_attribute_uses_normal_attribute_semantics() -> None:
    """Test the kernel never synthesizes attributes from context service names."""
    simulation = Simulation(initial_world_state=CounterState())
    with pytest.raises(AttributeError, match="missing_service"):
        _ = simulation.missing_service  # type: ignore[attr-defined]
