"""Tests for immutable committed spatial observations."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.observation import (
    SpatialCarcassSnapshot,
    SpatialObservation,
    SpatialOrganismSnapshot,
    SpatialRecorder,
    SpatialResourceSnapshot,
)
from evo_engine.world import Carcass
from tests.helpers import add_organism, make_state


def test_spatial_recorder_copies_visualization_state_deterministically() -> None:
    """Test spatial frames contain scalar state in deterministic order."""
    state = make_state(width=4, height=3)
    first = add_organism(
        state,
        age=2,
        energy=17,
        body_mass=5,
        mating_type="beta",
        x=2,
        y=1,
    )
    second = add_organism(
        state,
        age=1,
        energy=23,
        body_mass=3,
        mating_type="alpha",
        x=0,
        y=2,
    )
    state.domain_state.add_resources(x=2, y=0, amount=7)
    state.domain_state.add_resources(x=0, y=1, amount=4)
    second_carcass = Carcass(x=3, y=2, resource_units=6)
    first_carcass = Carcass(x=1, y=0, resource_units=9)
    state.domain_state.add_carcass(second_carcass)
    state.domain_state.add_carcass(first_carcass)
    recorder = SpatialRecorder()

    recorder.observe(state.domain_state, step_index=4)

    assert recorder.latest == SpatialObservation(
        step_index=4,
        world_width=4,
        world_height=3,
        organisms=(
            SpatialOrganismSnapshot(
                organism_id=first.id,
                x=2,
                y=1,
                age=2,
                energy=17,
                body_mass=5,
                mating_type="beta",
            ),
            SpatialOrganismSnapshot(
                organism_id=second.id,
                x=0,
                y=2,
                age=1,
                energy=23,
                body_mass=3,
                mating_type="alpha",
            ),
        ),
        resources=(
            SpatialResourceSnapshot(x=0, y=1, amount=4),
            SpatialResourceSnapshot(x=2, y=0, amount=7),
        ),
        carcasses=(
            SpatialCarcassSnapshot(
                carcass_id=second_carcass.id,
                x=3,
                y=2,
                resource_units=6,
            ),
            SpatialCarcassSnapshot(
                carcass_id=first_carcass.id,
                x=1,
                y=0,
                resource_units=9,
            ),
        ),
    )


def test_spatial_recorder_retains_values_not_mutable_world_references() -> None:
    """Test later live-world mutation cannot change an earlier spatial frame."""
    state = make_state(width=3, height=3)
    organism = add_organism(
        state,
        energy=12,
        body_mass=4,
        x=1,
        y=1,
    )
    state.domain_state.add_resources(x=2, y=2, amount=5)
    recorder = SpatialRecorder()
    recorder.observe(state.domain_state, step_index=0)
    recorded = recorder.observations[0]

    state.domain_state.move_organism(organism_id=organism.id, x=0, y=0)
    organism.change_energy(7)
    state.domain_state.remove_resources(x=2, y=2, amount=5)

    assert recorded.organisms[0].x == 1
    assert recorded.organisms[0].y == 1
    assert recorded.organisms[0].energy == 12
    assert recorded.resources == (SpatialResourceSnapshot(x=2, y=2, amount=5),)


def test_spatial_recorder_records_empty_world_and_exposes_immutable_history() -> None:
    """Test empty spatial frames are valid immutable values."""
    state = make_state(width=2, height=3)
    recorder = SpatialRecorder()

    recorder.observe(state.domain_state, step_index=0)

    assert recorder.observations == (
        SpatialObservation(step_index=0, world_width=2, world_height=3),
    )
    assert type(recorder.observations) is tuple
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        recorder.observations[0].world_width = 5  # type: ignore[misc]


def test_spatial_recorder_observation_interval_step_zero_and_clear() -> None:
    """Test observer-owned scheduling, duplicate suppression, and reuse."""
    state = make_state()
    recorder = SpatialRecorder(every_n_steps=2, include_step_zero=True)

    assert recorder.should_observe(state.domain_state, step_index=0)
    recorder.observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=1)
    assert recorder.should_observe(state.domain_state, step_index=2)

    without_baseline = SpatialRecorder(include_step_zero=False)
    assert not without_baseline.should_observe(state.domain_state, step_index=0)
    assert without_baseline.should_observe(state.domain_state, step_index=1)

    recorder.clear()
    assert recorder.observations == ()
    assert recorder.latest is None
    assert recorder.should_observe(state.domain_state, step_index=0)


def test_spatial_recorder_requires_strictly_increasing_manual_observations() -> None:
    """Test manually recorded history cannot duplicate or move backward."""
    state = make_state()
    recorder = SpatialRecorder()
    recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=1)


def test_spatial_observation_validates_bounds_order_and_uniqueness() -> None:
    """Test spatial values preserve deterministic render-safe invariants."""
    organism_1 = SpatialOrganismSnapshot(
        organism_id=1,
        x=0,
        y=0,
        age=0,
        energy=1,
        body_mass=1,
        mating_type="a",
    )
    organism_0 = attrs.evolve(organism_1, organism_id=0)

    with pytest.raises(ValueError, match="deterministic increasing order"):
        SpatialObservation(
            step_index=0,
            world_width=2,
            world_height=2,
            organisms=(organism_1, organism_0),
        )

    with pytest.raises(ValueError, match="must lie within world bounds"):
        SpatialObservation(
            step_index=0,
            world_width=2,
            world_height=2,
            resources=(SpatialResourceSnapshot(x=2, y=0, amount=1),),
        )

    with pytest.raises(ValueError, match="must be unique"):
        SpatialObservation(
            step_index=0,
            world_width=2,
            world_height=2,
            resources=(
                SpatialResourceSnapshot(x=0, y=0, amount=1),
                SpatialResourceSnapshot(x=0, y=0, amount=2),
            ),
        )
