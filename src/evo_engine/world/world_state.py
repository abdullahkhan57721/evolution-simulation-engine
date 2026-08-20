"""Represent the state of a simulated world."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from types import MappingProxyType

import attrs

from evo_engine.validation import attrs_validators, validators
from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism


@attrs.define(slots=True, kw_only=True)
class WorldState:
    """Represent the state of a simulated world.

    Attributes:
        width: Width of the world in grid cells.
        height: Height of the world in grid cells.
    """

    width: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
        on_setattr=attrs.setters.frozen,
    )
    height: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
        on_setattr=attrs.setters.frozen,
    )

    _organisms: dict[int, Organism] = attrs.field(
        factory=dict,
        init=False,
        repr=False,
    )
    _resources: dict[tuple[int, int], int] = attrs.field(
        factory=dict,
        init=False,
        repr=False,
    )
    _next_organism_id: int = attrs.field(
        default=0,
        init=False,
        repr=False,
        validator=attrs_validators.validate_int_ge(0),
    )
    _carcasses: dict[int, Carcass] = attrs.field(
        factory=dict,
        init=False,
        repr=False,
    )
    _next_carcass_id: int = attrs.field(
        default=0,
        init=False,
        repr=False,
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def organisms(self) -> Mapping[int, Organism]:
        """Return the organisms currently in the world."""
        # Expose a live read-only structural view. Entity objects remain
        # mutable because processes legitimately update organism state.
        return MappingProxyType(self._organisms)

    @property
    def carcasses(self) -> Mapping[int, Carcass]:
        """Return the carcasses currently in the world."""
        return MappingProxyType(self._carcasses)

    @property
    def resources(self) -> Mapping[tuple[int, int], int]:
        """Return the spatial resources currently in the world."""
        return MappingProxyType(self._resources)

    def add_organism(self, organism: Organism) -> None:
        """Assign an ID to an organism and add it to the world.

        Args:
            organism: Organism to add.

        Raises:
            TypeError: If organism is not an Organism.
            ValueError: If the organism is outside the world.
            RuntimeError: If the organism already has an ID.
        """
        if not isinstance(organism, Organism):
            raise TypeError("organism must be an instance of Organism.")

        self._validate_coordinate(x=organism.x, y=organism.y)

        # IDs are monotonic and intentionally never recycled. Historical
        # observations can therefore refer to an organism unambiguously even
        # after it has left the active world.
        organism._assign_id(self._next_organism_id)

        self._organisms[organism.id] = organism
        self._next_organism_id += 1

    def remove_organism(
        self,
        organism_id: int,
    ) -> Organism:
        """Remove and return an organism from the world.

        Args:
            organism_id: ID of the organism to remove.

        Returns:
            Removed organism.

        Raises:
            KeyError: If no organism has the given ID.
        """
        return self._organisms.pop(organism_id)

    def move_organism(self, *, organism_id: int, x: int, y: int) -> None:
        """Move an organism to a valid world coordinate.

        Args:
            organism_id: ID of the organism to move.
            x: New horizontal coordinate.
            y: New vertical coordinate.
        """
        self._validate_coordinate(x=x, y=y)

        organism = self._organisms[organism_id]

        organism.x = x
        organism.y = y

    def add_carcass(
        self,
        carcass: Carcass,
    ) -> None:
        """Assign an ID to a carcass and add it to the world.

        Args:
            carcass: Carcass to add.

        Raises:
            TypeError: If carcass is not a Carcass.
            ValueError: If the carcass is outside the world.
            RuntimeError: If the carcass already has an ID.
        """
        if not isinstance(carcass, Carcass):
            raise TypeError("carcass must be an instance of Carcass.")

        self._validate_coordinate(
            x=carcass.x,
            y=carcass.y,
        )

        carcass._assign_id(self._next_carcass_id)

        self._carcasses[carcass.id] = carcass
        self._next_carcass_id += 1

    def remove_carcass(
        self,
        carcass_id: int,
    ) -> Carcass:
        """Remove and return a carcass from the world.

        Args:
            carcass_id: ID of the carcass to remove.

        Returns:
            Removed carcass.

        Raises:
            KeyError: If no carcass has the given ID.
        """
        return self._carcasses.pop(carcass_id)

    def add_resources(self, *, x: int, y: int, amount: int) -> None:
        """Add resource units at a coordinate.

        Args:
            x: Horizontal coordinate.
            y: Vertical coordinate.
            amount: Resource units to add.
        """
        self._validate_coordinate(x=x, y=y)
        self._validate_resource_amount(amount=amount)

        coordinate = (x, y)

        # Resources use sparse storage: absent coordinates are semantically
        # equivalent to zero resource units.
        self._resources[coordinate] = self._resources.get(coordinate, 0) + amount

    def remove_resources(self, *, x: int, y: int, amount: int) -> None:
        """Remove resource units from a coordinate.

        Args:
            x: Horizontal coordinate.
            y: Vertical coordinate.
            amount: Resource units to remove.

        Raises:
            ValueError: If insufficient resources are available.
        """
        self._validate_coordinate(x=x, y=y)
        self._validate_resource_amount(amount=amount)

        coordinate = (x, y)
        available = self._resources.get(coordinate, 0)

        if amount > available:
            raise ValueError(
                f"Cannot remove {amount} resource units; "
                f"only {available} are available."
            )

        remaining = available - amount

        if remaining == 0:
            # Keep the sparse-map invariant by removing empty cells entirely.
            self._resources.pop(coordinate, None)
        else:
            self._resources[coordinate] = remaining

    def _validate_coordinate(
        self,
        *,
        x: int,
        y: int,
    ) -> None:
        """Validate a coordinate against the world bounds."""
        validators.validate_int_in_range(
            x,
            lower=0,
            upper=self.width - 1,
            name="x",
        )
        validators.validate_int_in_range(
            y,
            lower=0,
            upper=self.height - 1,
            name="y",
        )

    @staticmethod
    def _validate_resource_amount(*, amount: int) -> None:
        """Validate a resource amount."""
        validators.validate_int_gt(
            value=amount,
            bound=0,
            name="amount",
        )

    def copy(self) -> WorldState:
        """Return an independent deep copy of the world state.

        Returns:
            Deep copy of this world state.
        """
        return copy.deepcopy(self)
