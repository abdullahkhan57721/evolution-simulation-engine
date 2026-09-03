"""Tests for spatial placement composition in resource generation."""

from __future__ import annotations

import random

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    ResourcePlacementModel,
    UniformResourcePlacement,
)
from evo_engine.processes import ResourceGeneration
from tests.helpers import make_state


class RecordingPlacement:
    """Record the RNG supplied by ResourceGeneration and return one fixed cell."""

    def __init__(self) -> None:
        self.rng: random.Random | None = None

    def choose_position(
        self,
        *,
        width: int,
        height: int,
        rng: random.Random,
    ) -> tuple[int, int]:
        self.rng = rng
        return width - 1, height - 1


def test_resource_generation_defaults_to_explicit_uniform_placement() -> None:
    """Test existing construction keeps uniform placement by default."""
    process = ResourceGeneration(amount=2, number_of_deposits=1)

    assert isinstance(process.placement_model, UniformResourcePlacement)


def test_default_resource_generation_preserves_fixed_seed_coordinates_and_rng() -> None:
    """Test process-level default behavior exactly replays the old algorithm."""
    state = make_state(width=4, height=3, seed=37)
    control = random.Random(37)
    process = ResourceGeneration(amount=2, number_of_deposits=5)

    events = process.propose_events(state)
    expected_coordinates = tuple(
        (control.randrange(4), control.randrange(3)) for _ in range(5)
    )

    assert tuple((event.x, event.y) for event in events) == expected_coordinates
    assert state.rng.getstate() == control.getstate()


def test_resource_generation_passes_simulation_owned_rng_to_placement() -> None:
    """Test coordinate policy receives the state RNG rather than a private RNG."""
    state = make_state(width=3, height=4, seed=41)
    placement = RecordingPlacement()
    process = ResourceGeneration(
        amount=1,
        number_of_deposits=1,
        placement_model=placement,
    )

    events = process.propose_events(state)

    assert placement.rng is state.rng
    assert [(event.x, event.y) for event in events] == [(2, 3)]


def test_patchy_generation_conserves_exact_configured_quantity() -> None:
    """Test placement changes geography without changing generated quantity."""
    state = make_state(width=7, height=7, seed=43)
    process = ResourceGeneration(
        amount=3,
        number_of_deposits=6,
        placement_model=PatchyResourcePlacement(
            patches=(ResourcePatch(center_x=3, center_y=3, radius=1),)
        ),
    )

    events = process.propose_events(state)
    for event in events:
        process.apply_event(state, event)

    assert len(events) == 6
    assert sum(event.amount for event in events) == 18
    assert sum(state.domain_state.resources.values()) == 18
    assert all(
        (event.x - 3) ** 2 + (event.y - 3) ** 2 <= 1 for event in events
    )
    assert all(0 <= event.x < 7 and 0 <= event.y < 7 for event in events)


def test_resource_generation_accepts_structural_custom_placement_model() -> None:
    """Test callers can compose custom placement models without subclassing."""
    placement: ResourcePlacementModel = RecordingPlacement()
    state = make_state(width=2, height=2, seed=47)

    event = ResourceGeneration(
        amount=4,
        number_of_deposits=1,
        placement_model=placement,
    ).propose_events(state)[0]

    assert (event.x, event.y, event.amount) == (1, 1, 4)
