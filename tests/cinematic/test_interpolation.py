"""Tests for presentation-only cinematic position interpolation."""

import pytest

from evo_engine.cinematic.interpolation import interpolate_organism_position
from evo_engine.cinematic.primitives import CinematicOrganismPrimitive


def test_interpolation_preserves_committed_endpoints_exactly() -> None:
    start = _organism(organism_id=7, x=1, y=2)
    end = _organism(organism_id=7, x=5, y=6)

    assert interpolate_organism_position(start, end, fraction=0.0) == (1.0, 2.0)
    assert interpolate_organism_position(start, end, fraction=1.0) == (5.0, 6.0)


def test_interpolation_uses_linear_presentation_geometry() -> None:
    start = _organism(organism_id=7, x=1, y=2)
    end = _organism(organism_id=7, x=5, y=6)

    position = interpolate_organism_position(start, end, fraction=0.25)

    assert position.x == 2.0
    assert position.y == 3.0


def test_interpolation_rejects_different_organisms() -> None:
    with pytest.raises(ValueError, match="same organism"):
        interpolate_organism_position(
            _organism(organism_id=1, x=0, y=0),
            _organism(organism_id=2, x=1, y=1),
            fraction=0.5,
        )


def test_interpolation_rejects_fraction_outside_presentation_interval() -> None:
    organism = _organism(organism_id=1, x=0, y=0)

    with pytest.raises(ValueError, match="fraction"):
        interpolate_organism_position(organism, organism, fraction=1.1)


def _organism(*, organism_id: int, x: int, y: int) -> CinematicOrganismPrimitive:
    return CinematicOrganismPrimitive(
        organism_id=organism_id,
        x=x,
        y=y,
        body_mass=5,
        mating_type="A",
    )
