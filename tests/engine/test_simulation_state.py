"""Tests for domain-neutral SimulationState."""

from __future__ import annotations

import random

from evo_engine.engine import SimulationState
from evo_engine.telemetry import StepTelemetry

from tests.engine.helpers import CounterState


def test_copy_preserves_step_index() -> None:
    """Test transactional copies start at the same simulation step."""
    state = SimulationState(world=CounterState(), step_index=7)

    copied = state.copy()

    assert copied.step_index == 7


def test_copy_shares_immutable_context() -> None:
    """Test state copies reuse immutable configuration services."""
    service = object()
    state = SimulationState(world=CounterState(), service=service)

    copied = state.copy()

    assert copied.context is state.context
    assert copied.service is service


def test_copy_independently_copies_domain_state() -> None:
    """Test working-state mutations do not affect authoritative state."""
    state = SimulationState(world=CounterState(value=20))

    copied = state.copy()
    copied.world.value = 3
    copied.world.notes.append("working")

    assert state.world.value == 20
    assert state.world.notes == []


def test_copy_preserves_rng_state_without_sharing_rng() -> None:
    """Test deterministic RNG cloning for transactional step execution."""
    state = SimulationState(
        world=CounterState(),
        rng=random.Random(17),
    )

    copied = state.copy()

    assert copied.rng is not state.rng
    assert copied.rng.random() == state.rng.random()


def test_copy_rng_advancement_is_independent() -> None:
    """Test advancing a working RNG does not advance authority."""
    state = SimulationState(
        world=CounterState(),
        rng=random.Random(11),
    )
    expected = random.Random(11)

    copied = state.copy()
    copied.rng.random()

    assert state.rng.random() == expected.random()


def test_copy_clears_previous_committed_telemetry() -> None:
    """Test a new working transaction starts without stale telemetry."""
    state = SimulationState(
        world=CounterState(),
        last_step_telemetry=StepTelemetry(
            completed_step_index=2,
            events=(),
        ),
    )

    copied = state.copy()

    assert copied.last_step_telemetry is None
