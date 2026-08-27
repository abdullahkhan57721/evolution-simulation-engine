"""Tests for immutable SimulationContext integration."""

from __future__ import annotations

import pytest

from evo_engine.engine import SimulationContext, SimulationState
from evo_engine.world import WorldState
from tests.helpers import make_integer_architecture, make_state


def test_transactional_copy_shares_simulation_context() -> None:
    """Test immutable configuration is shared across state snapshots."""
    state = make_state()

    copied = state.copy()

    assert copied.context is state.context
    assert copied.genetic_architecture is state.context.require("genetic_architecture")
    assert copied.behavior_selection_model is state.context.require(
        "behavior_selection_model"
    )


def test_simulation_state_accepts_explicit_context() -> None:
    """Test callers may construct state from a complete shared context."""
    architecture = make_integer_architecture()
    context = SimulationContext.from_mapping({"genetic_architecture": architecture})

    state = SimulationState(
        world=WorldState(width=2, height=2),
        context=context,
    )

    assert state.context is context
    assert state.genetic_architecture is architecture


def test_simulation_state_rejects_mixed_context_construction_styles() -> None:
    """Test explicit context cannot conflict with separate context arguments."""
    architecture = make_integer_architecture()
    context = SimulationContext.from_mapping({"genetic_architecture": architecture})

    with pytest.raises(TypeError, match="context cannot be combined"):
        SimulationState(
            world=WorldState(width=2, height=2),
            context=context,
            genetic_architecture=architecture,
        )
