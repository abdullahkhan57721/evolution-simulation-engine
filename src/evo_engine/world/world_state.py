"""Represent the state of a simulated world."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

import attrs

from evo_engine.validation import attrs_validators, validators
from evo_engine.world.carcass import Carcass
from evo_engine.world.environment import EnvironmentalField
from evo_engine.world.mutations import (
    CarcassAdded,
    CarcassRemoved,
    EnvironmentalValueChanged,
    OrganismAdded,
    OrganismMoved,
    OrganismRemoved,
    ResourcesChanged,
    WorldMutation,
)
from evo_engine.world.organism import Organism


@attrs.define(slots=True, kw_only=True)
class WorldState:
    """Represent the state of a simulated world.

    Structural world mutations are journaled transaction-locally so the engine
    can associate committed effects with the materialized event that caused
    them. ``copy()`` deliberately starts a fresh journal while preserving all
    ecological state.

    Environmental fields are immutable definitions paired with sparse mutable
    spatial overrides. Cells without an override use the field's configured
    default value.

    Attributes:
        width: Width of the world in grid cells.
        height: Height of the world in grid cells.
        environmental_fields: Immutable named scalar environmental definitions.
    """

    width: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
        on_setattr=attrs.setters.frozen,
    )
    height: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
        on_setattr=attrs.setters.frozen,
    )
    environmental_fields: tuple[EnvironmentalField, ...] = attrs.field(
        factory=tuple,
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
    _environmental_values: dict[str, dict[tuple[int, int], int | float]] = attrs.field(
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

    def __attrs_post_init__(self) -> None:
        """Validate environmental field definitions."""
        validators.validate_tuple(
            self.environmental_fields,
            name="environmental_fields",
        )
        seen: set[str] = set()
        for index, field in enumerate(self.environmental_fields):
            if not isinstance(field, EnvironmentalField):
                raise TypeError(
                    f"environmental_fields[{index}] must be an EnvironmentalField; "
                    f"received {field!r}."
                )
            if field.name in seen:
                raise ValueError(
                    "environmental_fields must not contain duplicate names; "
                    f"received {field.name!r}."
                )
            seen.add(field.name)
            self._environmental_values[field.name] = {}

    @property
    def organisms(self) -> Mapping[int, Organism]:
        """Return the organisms currently in the world."""
        return MappingProxyType(self._organisms)

    @property
    def carcasses(self) -> Mapping[int, Carass]:
        """Return the carcasses currently in the world."""
        return MappingProxyType(self._carcasses)

    @property
    def resources(self) -> Mapping[tuple[int, int], int]:
        """Return the spatial resources currently in the world."""
        return MappingProxyType(self._resources)

    @property
    def environmental_field_names(self) -> tuple[str, ...]:
        """Return configured environmental field names in definition order."""
        return tuple(field.name for field in self.environmental_fields)

    @property
    def effect_count(self) -> int:
        """Return the number of domain effects in the transaction journal."""
        return len(self._mutations)

    def effects_since(self, checkpoint: int) -> tuple[WorldMutation, ...]:
        """Return transaction-local world effects after a journal checkpoint.

        Args:
            checkpoint: Previously observed ``effect_count`` value.

        Returns:
            World mutations exposed as domain effects at or after the checkpoint,
            in occurrence order.

        Raises:
            ValueError: If checkpoint exceeds the current journal length.
        """
        validators.validate_int_ge(checkpoint, bound=0, name="checkpoint")
        if checkpoint > len(self._mutations):
            raise ValueError("checkpoint cannot exceed current effect_count.")
        return tuple(self._mutations[checkpoint:])

    def environmental_value(self, field_name: str, *, x: int, y: int) -> int | float:
        """Return one environmental field value at a world coordinate.

        Args:
            field_name: Configured environmental field name.
            x: Horizontal coordinate.
            y: Vertical coordinate.

        Returns:
            Explicit spatial override or the field's default value.

        Raises:
            KeyError: If field_name is not configured.
            ValueError: If the coordinate is outside world bounds.
        """
        field = self._environmental_field(field_name)
        self._validate_coordinate(x=x, y=y)
        return self._environmental_values[field.name].get((x, y), field.default_value)

    def environmental_overrides(
        self,
        field_name: str,
    ) -> Mapping[tuple[int, int], int | float]:
        """Return explicit sparse overrides for one environmental field.

        Args:
            field_name: Configured environmental field name.

        Returns:
            Read-only coordinate-to-value mapping containing only values that
            differ from the field default.
        """
        field = self._environmental_field(field_name)
        return MappingProxyType(self._environmental_values[field.name])

    def set_environmental_value(
        self,
        field_name: str,
        *,
        x: int,
        y: int,
        value: int | float,
    ) -> None:
        """Set one finite environmental value at a coordinate.

        Setting a value back to the field default removes the sparse override.
        No mutation is journaled when the effective value does not change.

        Args:
            field_name: Configured environmental field name.
            x: Horizontal coordinate.
            y: Vertical coordinate.
            value: New finite scalar value.
        """
        field = self._environmental_field(field_name)
        self._validate_coordinate(x=x, y=y)
        validated_value = field.validate_value(value)
        coordinate = (x, y)
        before = self._environmental_values[field.name].get(
            coordinate,
            field.default_value,
        )
        if validated_value == before:
            return

        if validated_value == field.default_value:
            self._environmental_values[field.name].pop(coordinate, None)
        else:
            self._environmental_values[field.name][coordinate] = validated_value

        self._mutations.append(
            EnvironmentalValueChanged(
                field_name=field.name,
                x=x,
                y=y,
                before=before,
                after=validated_value,
            )
        )

    def change_environmental_value(
        self,
        field_name: str,
        *,
        x: int,
        y: int,
        delta: int | float,
    ) -> None:
        """Change one environmental field value by a finite signed amount.

        Args:
            field_name: Configured environmental field name.
            x: Horizontal coordinate.
            y: Vertical coordinate.
            delta: Finite signed change to apply.
        """
        field = self._environmental_field(field_name)
        validated_delta = field.validate_value(delta, name="delta")
        before = self.environmental_value(field.name, x=x, y=y)
        self.set_environmental_value(
            field.name,
            x=x,
            y=y,
            value=before + validated_delta,
        )

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
        self._mutations.append(ResourcesChanged(x=x, y=y, before=before, after=after))

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

        self._mutations.append(ResourcesChanged(x=x, y=y, before=before, after=after))

    def _environmental_field(self, field_name: str) -> EnvironmentalField:
        validated_name = validators.validate_str(field_name, name="field_name")
        for field in self.environmental_fields:
            if field.name == validated_name:
                return field
        raise KeyError(f"World has no environmental field named {validated_name!r}.")

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
        validators.validate_int_gt(value=amount, bound=0, name="amount")

    def copy(self) -> WorldState:
        """Return an independent semantic copy with a fresh mutation journal.

        Immutable world definitions and immutable organism genetics/developmental
        state are intentionally shared. Mutable entity state, sparse resources,
        environmental overrides, and allocation counters are copied explicitly.

        Returns:
            Independent ecological state with no transaction-local mutations.
        """
        copied = type(self)(
            width=self.width,
            height=self.height,
            environmental_fields=self.environmental_fields,
        )
        copied._organisms = {
            organism_id: _copy_organism(organism)
            for organism_id, organism in self._organisms.items()
        }
        copied._resources = self._resources.copy()
        copied._environmental_values = {
            field_name: overrides.copy()
            for field_name, overrides in self._environmental_values.items()
        }
        copied._next_organism_id = self._next_organism_id
        copied._carcasses = {
            carcass_id: _copy_carcass(carcass)
            for carcass_id, carcass in self._carcasses.items()
        }
        copied._next_carcass_id = self._next_carcass_id
        return copied


def _copy_organism(organism: Organism) -> Organism:
    copied = attrs.evolve(organism)
    copied._assign_id(organism.id)
    return copied


def _copy_carcass(carcass: Carcass) -> Carcass:
    copied = attrs.evolve(carcass)
    copied._assign_id(carcass.id)
    return copied