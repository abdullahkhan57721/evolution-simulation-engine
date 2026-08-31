"""Immutable records for structural biological world mutations."""

from __future__ import annotations

import math
from typing import TypeAlias

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class OrganismAdded:
    """Record an organism added to the world.

    Attributes:
        organism_id: Permanent ID assigned to the added organism.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class OrganismRemoved:
    """Record an organism removed from the active world.

    Attributes:
        organism_id: Permanent ID of the removed organism.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class OrganismMoved:
    """Record an organism coordinate change.

    Attributes:
        organism_id: Permanent organism ID.
        from_x: Previous horizontal coordinate.
        from_y: Previous vertical coordinate.
        to_x: New horizontal coordinate.
        to_y: New vertical coordinate.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    from_x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    from_y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    to_x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    to_y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class CarcassAdded:
    """Record a carcass added to the world.

    Attributes:
        carcass_id: Permanent ID assigned to the carcass.
    """

    carcass_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class CarcassRemoved:
    """Record a carcass removed from the world.

    Attributes:
        carcass_id: Permanent ID of the removed carcass.
    """

    carcass_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class ResourcesChanged:
    """Record a resource quantity change at one coordinate.

    Attributes:
        x: Horizontal coordinate.
        y: Vertical coordinate.
        before: Resource quantity before the mutation.
        after: Resource quantity after the mutation.
    """

    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    before: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    after: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def delta(self) -> int:
        """Return signed resource change."""
        return self.after - self.before


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentalValueChanged:
    """Record one spatial environmental scalar-value change.

    Attributes:
        field_name: Name of the environmental field that changed.
        x: Horizontal coordinate.
        y: Vertical coordinate.
        before: Finite field value before the mutation.
        after: Finite field value after the mutation.
    """

    field_name: str = attrs.field(validator=attrs_validators.validate_str)
    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    before: int | float
    after: int | float

    def __attrs_post_init__(self) -> None:
        """Validate field naming and finite before/after values."""
        if not self.field_name.strip():
            raise ValueError("field_name must not be empty or whitespace-only.")
        _validate_finite_number(self.before, name="before")
        _validate_finite_number(self.after, name="after")

    @property
    def delta(self) -> int | float:
        """Return signed environmental-value change."""
        return self.after - self.before


WorldMutation: TypeAlias = (
    OrganismAdded
    | OrganismRemoved
    | OrganismMoved
    | CarcassAdded
    | CarcassRemoved
    | ResourcesChanged
    | EnvironmentalValueChanged
)


def _validate_finite_number(value: object, *, name: str) -> int | float:
    number = validators.validate_number(value, name=name)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite; received {number!r}.")
    return number
