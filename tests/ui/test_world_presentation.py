"""Tests for UI-only world presentation derived from committed observations."""

from __future__ import annotations

import pytest

from evo_engine.observation import (
    SpatialCarcassSnapshot,
    SpatialObservation,
    SpatialOrganismSnapshot,
    SpatialResourceSnapshot,
)
from evo_engine.ui.world_presentation import (
    available_step_indices,
    build_world_presentation,
    interpolate_organism_positions,
    organism_marker_size,
    spatial_frame_for_step,
)


def _organism(
    organism_id: int,
    *,
    x: int,
    y: int,
    body_mass: int = 2,
) -> SpatialOrganismSnapshot:
    return SpatialOrganismSnapshot(
        organism_id=organism_id,
        x=x,
        y=y,
        age=organism_id + 1,
        energy=20 + organism_id,
        body_mass=body_mass,
        mating_type="type_a",
    )


def _history() -> tuple[SpatialObservation, ...]:
    return (
        SpatialObservation(
            step_index=0,
            world_width=6,
            world_height=5,
            organisms=(
                _organism(0, x=0, y=0, body_mass=2),
                _organism(1, x=4, y=4, body_mass=4),
            ),
            resources=(SpatialResourceSnapshot(x=1, y=1, amount=3),),
        ),
        SpatialObservation(
            step_index=1,
            world_width=6,
            world_height=5,
            organisms=(
                _organism(0, x=1, y=0, body_mass=2),
                _organism(1, x=4, y=3, body_mass=4),
                _organism(2, x=5, y=4, body_mass=3),
            ),
            resources=(SpatialResourceSnapshot(x=2, y=2, amount=7),),
            carcasses=(
                SpatialCarcassSnapshot(
                    carcass_id=10,
                    x=3,
                    y=1,
                    resource_units=4,
                ),
            ),
        ),
        SpatialObservation(
            step_index=2,
            world_width=6,
            world_height=5,
            organisms=(
                _organism(0, x=2, y=1, body_mass=2),
                _organism(2, x=5, y=3, body_mass=3),
            ),
            resources=(SpatialResourceSnapshot(x=4, y=2, amount=9),),
        ),
    )


def test_selected_step_uses_exact_committed_frame_and_resource_snapshot() -> None:
    """Test selected world inputs come from the exact authoritative frame."""
    history = _history()

    assert available_step_indices(history) == (0, 1, 2)
    assert spatial_frame_for_step(history, step_index=1) is history[1]

    presentation = build_world_presentation(
        history,
        step_index=1,
        selected_organism_id=1,
        show_trails=False,
    )

    assert presentation.committed_step_index == 1
    assert tuple((item.x, item.y, item.amount) for item in presentation.resources) == (
        (2, 2, 7),
    )
    assert tuple(item.carcass_id for item in presentation.carcasses) == (10,)
    selected = presentation.selected_organism()
    assert selected is not None
    assert selected.organism_id == 1
    assert [item.selected for item in presentation.organisms] == [False, True, False]


def test_view_layers_can_hide_observed_environment_without_changing_frame() -> None:
    """Test view visibility affects presentation only, not committed selection."""
    presentation = build_world_presentation(
        _history(),
        step_index=1,
        show_resources=False,
        show_carcasses=False,
        show_trails=False,
    )

    assert presentation.committed_step_index == 1
    assert presentation.resources == ()
    assert presentation.carcasses == ()
    assert presentation.trails == ()
    assert len(presentation.organisms) == 3


def test_trails_follow_permanent_ids_over_recent_committed_frames() -> None:
    """Test recent movement is derived only from matching committed organism IDs."""
    presentation = build_world_presentation(
        _history(),
        step_index=2,
        trail_length=3,
    )

    trails = {trail.organism_id: trail.points for trail in presentation.trails}
    assert trails[0] == ((0, 0), (1, 0), (2, 1))
    assert trails[2] == ((5, 4), (5, 3))
    assert 1 not in trails


def test_selection_can_retain_id_that_is_absent_from_selected_frame() -> None:
    """Test focus identity is retained without fabricating an active organism."""
    presentation = build_world_presentation(
        _history(),
        step_index=2,
        selected_organism_id=1,
    )

    assert presentation.selected_organism_id == 1
    assert presentation.selected_organism() is None
    assert all(not organism.selected for organism in presentation.organisms)


def test_body_mass_size_mapping_is_bounded_and_monotonic() -> None:
    """Test physical body mass remains the only generic size meaning."""
    sizes = [organism_marker_size(value) for value in (1, 2, 8, 18, 40)]

    assert sizes == sorted(sizes)
    assert min(sizes) >= 10
    assert max(sizes) <= 26


def test_interpolation_has_exact_endpoints_for_persistent_organisms_only() -> None:
    """Test display interpolation never fabricates births or retained deaths."""
    history = _history()

    left = interpolate_organism_positions(history[0], history[1], alpha=0)
    right = interpolate_organism_positions(history[0], history[1], alpha=1)
    midpoint = interpolate_organism_positions(history[0], history[1], alpha=0.5)

    assert tuple(item.organism_id for item in left) == (0, 1)
    assert tuple((item.x, item.y) for item in left) == ((0.0, 0.0), (4.0, 4.0))
    assert tuple((item.x, item.y) for item in right) == ((1.0, 0.0), (4.0, 3.0))
    assert tuple((item.x, item.y) for item in midpoint) == (
        (0.5, 0.0),
        (4.0, 3.5),
    )
    assert all(item.organism_id != 2 for item in midpoint)


def test_interpolation_rejects_invalid_alpha() -> None:
    """Test display interpolation fraction remains an explicit bounded value."""
    history = _history()

    with pytest.raises(ValueError, match="between 0 and 1"):
        interpolate_organism_positions(history[0], history[1], alpha=1.1)


def test_missing_selected_step_is_rejected() -> None:
    """Test presentation cannot silently substitute a different committed frame."""
    with pytest.raises(KeyError, match="step 99"):
        build_world_presentation(_history(), step_index=99)
