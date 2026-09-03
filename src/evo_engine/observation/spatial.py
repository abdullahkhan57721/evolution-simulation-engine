"""Record immutable spatial snapshots of committed ecological state."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators
from evo_engine.world import WorldState


@attrs.frozen(slots=True, kw_only=True)
class SpatialOrganismSnapshot:
    """Record visualization-relevant scalar state for one organism.

    Attributes:
        organism_id: Permanent world-managed organism ID.
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
        age: Current organism age in simulation timesteps.
        energy: Current organism energy.
        body_mass: Current positive physical body mass.
        mating_type: Immutable reproductive mating-type label.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    age: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    body_mass: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    mating_type: str = attrs.field(
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the mating-type label."""
        if not self.mating_type.strip():
            raise ValueError("mating_type must not be empty or whitespace-only.")


@attrs.frozen(slots=True, kw_only=True)
class SpatialResourceSnapshot:
    """Record one spatial environmental resource deposit.

    Attributes:
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
        amount: Positive resource units present at the coordinate.
    """

    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    amount: int = attrs.field(
        validator=attrs_validators.validate_int_gt(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class SpatialCarcassSnapshot:
    """Record visualization-relevant scalar state for one carcass.

    Attributes:
        carcass_id: Permanent world-managed carcass ID.
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
        resource_units: Resource units remaining in the carcass.
    """

    carcass_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
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


@attrs.frozen(slots=True, kw_only=True)
class SpatialObservation:
    """Record one immutable committed spatial world frame.

    Snapshot tuples use deterministic ordering so equality, serialization, tests,
    and downstream rendering do not depend on mutable mapping iteration order.

    Attributes:
        step_index: Completed simulation-step index represented by the frame.
        world_width: Width of the world in grid cells.
        world_height: Height of the world in grid cells.
        organisms: Organism snapshots ordered by permanent organism ID.
        resources: Resource snapshots ordered lexicographically by ``(x, y)``.
        carcasses: Carcass snapshots ordered by permanent carcass ID.
    """

    step_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    world_width: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    world_height: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    organisms: tuple[SpatialOrganismSnapshot, ...] = attrs.field(factory=tuple)
    resources: tuple[SpatialResourceSnapshot, ...] = attrs.field(factory=tuple)
    carcasses: tuple[SpatialCarcassSnapshot, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate snapshot types, bounds, uniqueness, and deterministic order."""
        validators.validate_tuple(self.organisms, name="organisms")
        validators.validate_tuple(self.resources, name="resources")
        validators.validate_tuple(self.carcasses, name="carcasses")

        organism_ids: list[int] = []
        for index, organism in enumerate(self.organisms):
            if not isinstance(organism, SpatialOrganismSnapshot):
                raise TypeError(
                    f"organisms[{index}] must be a SpatialOrganismSnapshot; "
                    f"received {organism!r}."
                )
            _validate_coordinate(
                x=organism.x,
                y=organism.y,
                width=self.world_width,
                height=self.world_height,
                name=f"organisms[{index}]",
            )
            organism_ids.append(organism.organism_id)
        _validate_unique_sorted(organism_ids, name="organism IDs")

        resource_coordinates: list[tuple[int, int]] = []
        for index, resource in enumerate(self.resources):
            if not isinstance(resource, SpatialResourceSnapshot):
                raise TypeError(
                    f"resources[{index}] must be a SpatialResourceSnapshot; "
                    f"received {resource!r}."
                )
            _validate_coordinate(
                x=resource.x,
                y=resource.y,
                width=self.world_width,
                height=self.world_height,
                name=f"resources[{index}]",
            )
            resource_coordinates.append((resource.x, resource.y))
        _validate_unique_sorted(resource_coordinates, name="resource coordinates")

        carcass_ids: list[int] = []
        for index, carcass in enumerate(self.carcasses):
            if not isinstance(carcass, SpatialCarcassSnapshot):
                raise TypeError(
                    f"carcasses[{index}] must be a SpatialCarcassSnapshot; "
                    f"received {carcass!r}."
                )
            _validate_coordinate(
                x=carcass.x,
                y=carcass.y,
                width=self.world_width,
                height=self.world_height,
                name=f"carcasses[{index}]",
            )
            carcass_ids.append(carcass.carcass_id)
        _validate_unique_sorted(carcass_ids, name="carcass IDs")


@attrs.define(slots=True, kw_only=True)
class SpatialRecorder:
    """Record immutable spatial frames from authoritative committed worlds.

    The recorder stores scalar value snapshots only. It never retains mutable
    ``WorldState``, organism, carcass, resource-mapping, genome, or phenotype
    references.

    Attributes:
        every_n_steps: Positive observation interval. A value of 1 records every
            committed state offered by the engine.
        include_step_zero: Whether to record the pre-step founder baseline.
    """

    every_n_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    include_step_zero: bool = attrs.field(
        default=True,
        validator=attrs_validators.validate_bool,
    )
    _observations: list[SpatialObservation] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    @property
    def observations(self) -> tuple[SpatialObservation, ...]:
        """Return recorded frames as an immutable tuple."""
        return tuple(self._observations)

    @property
    def latest(self) -> SpatialObservation | None:
        """Return the latest recorded frame, if one has been recorded."""
        if not self._observations:
            return None
        return self._observations[-1]

    def should_observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> bool:
        """Return whether the current committed state should be recorded."""
        _validate_observation_inputs(world_state, step_index=step_index)

        if self._observations and self._observations[-1].step_index == step_index:
            return False
        if step_index == 0 and not self.include_step_zero:
            return False
        return step_index % self.every_n_steps == 0

    def observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> None:
        """Record one immutable committed spatial observation.

        Args:
            world_state: Current authoritative committed world state.
            step_index: Current completed simulation-step index.

        Raises:
            ValueError: If observations are supplied out of chronological order.
        """
        _validate_observation_inputs(world_state, step_index=step_index)
        if self._observations and step_index <= self._observations[-1].step_index:
            raise ValueError(
                "SpatialRecorder observations must have strictly increasing "
                "step_index values."
            )

        self._observations.append(
            SpatialObservation(
                step_index=step_index,
                world_width=world_state.width,
                world_height=world_state.height,
                organisms=tuple(
                    SpatialOrganismSnapshot(
                        organism_id=organism_id,
                        x=organism.x,
                        y=organism.y,
                        age=organism.age,
                        energy=organism.energy,
                        body_mass=organism.body_mass,
                        mating_type=organism.mating_type,
                    )
                    for organism_id, organism in sorted(world_state.organisms.items())
                ),
                resources=tuple(
                    SpatialResourceSnapshot(
                        x=x,
                        y=y,
                        amount=amount,
                    )
                    for (x, y), amount in sorted(world_state.resources.items())
                ),
                carcasses=tuple(
                    SpatialCarcassSnapshot(
                        carcass_id=carcass_id,
                        x=carcass.x,
                        y=carcass.y,
                        resource_units=carcass.resource_units,
                    )
                    for carcass_id, carcass in sorted(world_state.carcasses.items())
                ),
            )
        )

    def clear(self) -> None:
        """Remove all recorded spatial observations."""
        self._observations.clear()


def _validate_observation_inputs(
    world_state: WorldState,
    *,
    step_index: int,
) -> None:
    if not isinstance(world_state, WorldState):
        raise TypeError("world_state must be an instance of WorldState.")
    validators.validate_int_ge(step_index, bound=0, name="step_index")


def _validate_coordinate(
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    name: str,
) -> None:
    if x >= width or y >= height:
        raise ValueError(
            f"{name} coordinate ({x}, {y}) must lie within world bounds "
            f"{width}x{height}."
        )


def _validate_unique_sorted(values: list[object], *, name: str) -> None:
    if values != sorted(values):
        raise ValueError(f"{name} must be in deterministic increasing order.")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique.")
