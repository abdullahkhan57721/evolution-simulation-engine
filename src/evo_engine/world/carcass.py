"""Carcass entity."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.define(slots=True, kw_only=True)
class Carcass:
    """Represent a carcass in the simulated world.

    Carcass IDs are assigned exactly once by ``WorldState``. Keeping the
    unassigned representation private lets the public ``id`` property expose
    a true ``int`` after insertion, matching the organism-ID contract and
    avoiding optional IDs throughout event code.

    Attributes:
        x: Horizontal grid coordinate.
        y: Vertical grid coordinate.
        resource_units: Resource units remaining in the carcass.
    """

    _id: int | None = attrs.field(
        default=None,
        init=False,
        repr=False,
    )
    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    resource_units: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def id(self) -> int:
        """Return the permanent world-managed carcass ID.

        Returns:
            Assigned carcass ID.

        Raises:
            RuntimeError: If the carcass has not been added to a world.
        """
        if self._id is None:
            raise RuntimeError("Carcass has not been assigned an ID.")

        return self._id

    def _assign_id(
        self,
        carcass_id: int,
    ) -> None:
        """Assign the carcass its world-managed ID.

        Args:
            carcass_id: ID to assign.

        Raises:
            RuntimeError: If the carcass already has an assigned ID.
        """
        if self._id is not None:
            raise RuntimeError("Carcass already has an assigned ID.")

        validators.validate_int_ge(
            carcass_id,
            bound=0,
            name="carcass_id",
        )

        self._id = carcass_id
