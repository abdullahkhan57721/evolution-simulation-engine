"""Represent the state of a simulated world."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from types import MappingProxyType

import attrs

from evo_engine.telemetry import (
    CarcassAdded,
    CarcassRemoved,
    OrganismAdded,
    OrganismMoved,
    OrganismRemoved,
    ResourcesChanged,
    WorldMutation,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism


@attrs.define(slots=True, kw_only=True)
class WorldState:
    """Represent the state of a simulated world.

    Structural world mutations are journaled transaction-locally so the engine
    can associate committed effects with the materialized event that caused
    them. ``copy()`` deliberately starts a fresh journal while preserving all
    ecological state.

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
    _mutations: list[WorldMutation] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    @property
    def organisms(self) -> Mapping[int, Organism]:
        """Return the organisms currently in the world."""
        return MappingProxyType(self._organisms)

    @property
    def carcasses(self) -> Mapping[int, Carcass]:
        """Return the carcasses currently in the world."""
        return MappingProxyType(self._carcasses)

    @property
    def resources(self) -> Mapping[tuple[int, int], int]:
        """Return the spatial resources currently in the world."""
        return MappingProxyType(self._resources)

    @property
    def mutation_count(self) -> int:
        """Return the number of mutations in the current transaction journal."""
        return len(self._mutations)

    def mutations_since(self, checkpoint: int) -> tuple[WorldMutation, ...]:
        """Return transaction-local world mutations after a journal checkpoint.

        Args:
            checkpoint: Previously observed ``mutation_count`` value.

        Returns:
            Mutations recorded at or after the checkpoint in occurrence order.

        Raises:
            ValueError: If checkpoint exceeds the current journal length.
        """
        validators.validate_int_ge(
            checkpoint,
            bound=0,
            name="checkpoint",
        )
        if checkpoint > len(self._mutations):
            raise ValueError("checkpoint cannot exceed current mutation_count.")
        return tuple(self._mutations[checkpoint:])

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
        organism._assign_id(self._next_organism_id)
        self._organisms[organism.id] = organism
        self._next_organism_id += 1
        self._mutations.append(OrganismAdded(organism_id=organism.id))

    def remove_organism(self, organism_id: int) -> Organism:
        """Remove and return an organism from the world.

        Args:
            organism_id: ID of the organism to remove.

        Returns:
            Removed organism.

        Raises:
            KeyError: If no organism has the given ID.
        """
        removed = self._organisms.pop(organism_id)
        self._mutations.append(OrganismRemoved(organism_id=organism_id))
        return removed

    def move_organism(self, *, organism_id: int, x: int, y: int) -> None:
        """Move an organism to a valid world coordinate.

        Args:
            organism_id: ID of the organism to move.
            x: New horizontal coordinate.
            y: New vertical coordinate.
        """
        self._validate_coordinate(x=x, y=y)
        organism = self._organisms[organism_id]
        from_x = organism.x
        from_y = organism.y
        organism.x = x
        organism.y = y

        if (from_x, from_y) != (x, y):
            self._mutations.append(
                OrganismMoved(
                    organism_id=organism_id,
                    from_x=from_x,
                    from_y=from_y,
                    to_x=x,
                    to_y=y,
                )
            )

    def add_carcass(self, carcass: Carcass) -> None:
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

        self._validate_coordinate(x=carcass.x, y=carcass.y)
        carcass._assign_id(self._next_carcass_id)
        self._carcasses[carcass.id] = carcass
        self._next_carcass_id += 1
        self._mutations.append(CarcassAdded(carcass_id=carcass.id))

    def remove_carcass(self, carcass_id: int) -> Carcass:
        """Remove and return a carcass from the world.

        Args:
            carcass_id: ID of the carcass to remove.

        Returns:
            Removed carcass.

        Raises:
            KeyError: If no carcass has the given ID.
        """
        removed = self._carcasses.pop(carcass_id)
        self._mutations.append(CarcassRemoved(carcass_id=carcass_id))
        return removed

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
        before = self._resources.get(coordinate, 0)
        after = before + amount
        self._resources[coordinate] = after
        self._mutations.append(
            ResourcesChanged(
                x=x,
                y=y,
                before=before,
                after=after,
            )
        )

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
        before = self._resources.get(coordinate, 0)

        if amount > before:
            raise ValueError(
                f"Cannot remove {amount} resource units; only {before} are available."
            )

        after = before - amount
        if after == 0:
            self._resources.pop(coordinate, None)
        else:
            self._resources[coordinate] = after

        self._mutations.append(
            ResourcesChanged(
                x=x,
                y=y,
                before=before,
                after=after,
            )
        )

    def _validate_coordinate(self, *, x: int, y: int) -> None:
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
        """Return an independent deep copy with a fresh mutation journal.

        Returns:
            Deep copy of ecological state with no transaction-local mutations.
        """
        copied = copy.deepcopy(self)
        copied._mutations.clear()
        return copied
