"""Tests for domain-neutral SimulationState."""

from __future__ import annotations

import random

from evo_engine.engine import SimulationState
from evo_engine.telemetry import StepTelemetry
from tests.engine.helpers import CounterState


def test_copy_preserves_step_index() -> None:
    state = SimulationState(world=CounterState(), step_index=7)
    assert state.copy().step_index == 7


def test_copy_shares_immutable_context() -> None:
    service = object()
    state = SimulationState(world=CounterState(), service=service)
    copied = state.copy()
    assert copied.context is state.context
    assert copied.context.require("service") is service
    assert not hasattr(copied, "service")


def test_copy_independently_copies_domain_state() -> None:
    state = SimulationState(world=CounterState(value=20))
    copied = state.copy()
    copied.world.value = 3
    copied.world.notes.append("working")
    assert state.world.value == 20
    assert state.world.notes == []


def test_copy_preserves_rng_state_without_sharing_rng() -> None:
    state = SimulationState(world=CounterState(), rng=random.Random(17))
    copied = state.copy()
    assert copied.rng is not state.rng
    assert copied.rng.random() == state.rng.random()


def test_copy_rng_advancement_is_independent() -> None:
    state = SimulationState(world=CounterState(), rng=random.Random(11))
    expected = random.Random(11)
    copied = state.copy()
    copied.rng.random()
    assert state.rng.random() == expected.random()


def test_copy_clears_previous_committed_telemetry() -> None:
    state = SimulationState(
        world=CounterState(),
        last_step_telemetry=StepTelemetry(completed_step_index=2, events=()),
    )
    assert state.copy().last_step_telemetry is None
