"""Focused tests for SimulationState transaction copy semantics."""

from __future__ import annotations

import random

from evo_engine.engine import SimulationState
from tests.engine.helpers import CounterState


def test_copy_preserves_exact_rng_state_without_sharing_generator() -> None:
    """Test transaction copies clone the complete RNG state exactly."""
    rng = random.Random(91)
    rng.gauss(0.0, 1.0)
    state = SimulationState(world=CounterState(), rng=rng)

    copied = state.copy()

    assert copied.rng is not state.rng
    assert copied.rng.getstate() == state.rng.getstate()

    copied.rng.random()

    assert copied.rng.getstate() != state.rng.getstate()
