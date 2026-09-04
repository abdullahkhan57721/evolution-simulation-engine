"""Presentation-only interpolation between committed organism positions."""

from __future__ import annotations

from dataclasses import dataclass

from evo_engine.cinematic.primitives import CinematicOrganismPrimitive
from evo_engine.validation import validators


@dataclass(frozen=True, slots=True)
class CinematicPosition:
    """Store one non-authoritative presentation position between evidence frames.

    Attributes:
        x: Interpolated horizontal presentation coordinate.
        y: Interpolated vertical presentation coordinate.
    """

    x: float
    y: float


def interpolate_organism_position(
    start: CinematicOrganismPrimitive,
    end: CinematicOrganismPrimitive,
    *,
    fraction: float,
) -> CinematicPosition:
    """Linearly interpolate one organism between two committed endpoints.

    The returned position is presentation geometry only. It is not an observed
    simulation state and must not be fed back into scientific analysis.

    Args:
        start: Prepared organism primitive at the earlier committed frame.
        end: Prepared primitive for the same organism at the later committed frame.
        fraction: Presentation fraction in the inclusive interval ``[0.0, 1.0]``.

    Returns:
        Presentation-only interpolated position. Fractions 0 and 1 reproduce the
        two committed endpoints exactly.

    Raises:
        ValueError: If endpoints refer to different organisms or fraction is out
            of range.
    """
    if start.organism_id != end.organism_id:
        raise ValueError("Interpolation endpoints must represent the same organism.")
    validated = validators.validate_float(fraction, name="fraction")
    if validated < 0.0 or validated > 1.0:
        raise ValueError("fraction must lie within [0.0, 1.0].")
    return CinematicPosition(
        x=start.x + (end.x - start.x) * validated,
        y=start.y + (end.y - start.y) * validated,
    )
