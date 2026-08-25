"""Tests for capacity-aware reproduction conflict resolution."""

from __future__ import annotations

import pytest

from evo_engine.processes import Reproduction
from evo_engine.resolvers.reproduction import CapacityPreferenceOrder
from tests.helpers import make_state


def _proposal(
    first_id: int,
    second_id: int,
    *,
    preference_score: int,
) -> Reproduction.Proposal:
    return Reproduction.Proposal(
        step_index=0,
        parent_energy_contributions=((first_id, 1), (second_id, 1)),
        preference_score=preference_score,
    )


def test_capacity_one_preserves_exclusive_parent_resolution() -> None:
    """Test capacity one accepts only the highest-preference use of a parent."""
    resolver = CapacityPreferenceOrder(max_events_per_parent=1)
    lower = _proposal(0, 1, preference_score=2)
    higher = _proposal(0, 2, preference_score=5)

    assert resolver.resolve_events(make_state(), (lower, higher)) == [higher]


def test_capacity_two_allows_parent_in_two_successful_matings() -> None:
    """Test larger capacity permits multiple stage matings for one parent."""
    resolver = CapacityPreferenceOrder(max_events_per_parent=2)
    first = _proposal(0, 1, preference_score=5)
    second = _proposal(0, 2, preference_score=4)
    third = _proposal(0, 3, preference_score=3)

    assert resolver.resolve_events(make_state(), (first, second, third)) == [
        first,
        second,
    ]


def test_capacity_is_enforced_for_every_participant() -> None:
    """Test a proposal fails when either parent has exhausted capacity."""
    resolver = CapacityPreferenceOrder(max_events_per_parent=1)
    first = _proposal(0, 1, preference_score=5)
    second = _proposal(2, 1, preference_score=4)
    independent = _proposal(2, 3, preference_score=3)

    assert resolver.resolve_events(make_state(), (first, second, independent)) == [
        first,
        independent,
    ]


def test_capacity_resolver_rejects_non_reproduction_events() -> None:
    """Test the specialized resolver rejects unrelated event types."""
    resolver = CapacityPreferenceOrder(max_events_per_parent=1)

    with pytest.raises(TypeError, match="Reproduction.Proposal"):
        resolver.resolve_events(make_state(), (object(),))  # type: ignore[arg-type]
