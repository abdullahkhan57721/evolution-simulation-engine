"""Immutable cinematic primitives prepared only from committed scientific evidence."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class CinematicOrganismPrimitive:
    """Store renderer-ready organism values for one committed scientific frame.

    Attributes:
        organism_id: Permanent organism identifier.
        x: Authoritative committed horizontal coordinate.
        y: Authoritative committed vertical coordinate.
        body_mass: Authoritative committed body mass.
        mating_type: Authoritative committed secondary category.
        focal_value: Optional committed focal scientific value.
        focal_normalized: Optional normalized value under the shared encoding.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    body_mass: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    mating_type: str = attrs.field(validator=attrs_validators.validate_str)
    focal_value: int | None = None
    focal_normalized: float | None = None

    def __attrs_post_init__(self) -> None:
        """Validate optional focal values and category label."""
        if not self.mating_type.strip():
            raise ValueError("mating_type must not be empty or whitespace-only.")
        if self.focal_value is None:
            if self.focal_normalized is not None:
                raise ValueError(
                    "focal_normalized requires a committed focal_value."
                )
            return

        validators.validate_int(self.focal_value, name="focal_value")
        if self.focal_normalized is None:
            raise ValueError("focal_value requires focal_normalized.")
        normalized = validators.validate_float(
            self.focal_normalized,
            name="focal_normalized",
        )
        if normalized < 0.0 or normalized > 1.0:
            raise ValueError("focal_normalized must lie within [0.0, 1.0].")
