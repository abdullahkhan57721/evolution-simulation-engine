"""Context describing where developmental realization occurs."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class DevelopmentLocation:
    """Represent the world coordinate at which development is realized.

    Developmental models remain separate from world-state ownership. A model
    that responds to a spatial environmental field can combine this location
    with the supplied simulation state to read the local environment.

    Attributes:
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
    """

    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
