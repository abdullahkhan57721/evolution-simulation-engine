"""Derive interactive world presentation values from committed observations."""

from __future__ import annotations

import attrs

from evo_engine.observation import SpatialObservation, SpatialOrganismSnapshot


@attrs.frozen(slots=True, kw_only=True)
class OrganismPrimitive:
    """Describe one organism glyph from one authoritative committed snapshot."""

    organism_id: int
    x: float
    y: float
    age: int
    energy: int
    body_mass: int
    mating_type: str
    marker_size: int
    selected: bool = False


@attrs.frozen(slots=True, kw_only=True)
class ResourcePrimitive:
    """Describe one observed environmental-resource glyph."""

    x: int
    y: int
    amount: int


@attrs.frozen(slots=True, kw_only=True)
class CarcassPrimitive:
    """Describe one observed carcass glyph."""

    carcass_id: int
    x: int
    y: int
    resource_units: int


@attrs.frozen(slots=True, kw_only=True)
class MovementTrail:
    """Describe recent committed positions for one permanent organism ID."""

    organism_id: int
    points: tuple[tuple[int, int], ...]


@attrs.frozen(slots=True, kw_only=True)
class WorldPresentationFrame:
    """Describe one renderer-ready view of an authoritative committed world frame."""

    committed_step_index: int
    world_width: int
    world_height: int
    organisms: tuple[OrganismPrimitive, ...]
    resources: tuple[ResourcePrimitive, ...]
    carcasses: tuple[CarcassPrimitive, ...]
    trails: tuple[MovementTrail, ...]
    selected_organism_id: int | None = None

    def selected_organism(self) -> OrganismPrimitive | None:
        """Return the selected active organism, if present in this committed frame."""
        if self.selected_organism_id is None:
            return None
        for organism in self.organisms:
            if organism.organism_id == self.selected_organism_id:
                return organism
        return None


@attrs.frozen(slots=True, kw_only=True)
class InterpolatedOrganismPosition:
    """Describe one display-only organism position between committed endpoints."""

    organism_id: int
    x: float
    y: float
    left_step_index: int
    right_step_index: int
    alpha: float


def available_step_indices(
    history: tuple[SpatialObservation, ...],
) -> tuple[int, ...]:
    """Return authoritative committed spatial step indices in recorded order."""
    return tuple(frame.step_index for frame in history)


def spatial_frame_for_step(
    history: tuple[SpatialObservation, ...],
    *,
    step_index: int,
) -> SpatialObservation:
    """Return the committed spatial frame for one exact authoritative step."""
    for frame in history:
        if frame.step_index == step_index:
            return frame
    raise KeyError(f"No committed spatial observation for step {step_index}.")


def build_world_presentation(
    history: tuple[SpatialObservation, ...],
    *,
    step_index: int,
    selected_organism_id: int | None = None,
    show_resources: bool = True,
    show_carcasses: bool = True,
    show_trails: bool = True,
    trail_length: int = 5,
) -> WorldPresentationFrame:
    """Build UI-only primitives from one selected committed spatial frame."""
    if type(trail_length) is not int:
        raise TypeError("trail_length must be an integer.")
    if trail_length < 1:
        raise ValueError("trail_length must be at least 1.")
    if selected_organism_id is not None and type(selected_organism_id) is not int:
        raise TypeError("selected_organism_id must be an integer or None.")

    frame = spatial_frame_for_step(history, step_index=step_index)
    organisms = tuple(
        _organism_primitive(
            organism,
            selected=organism.organism_id == selected_organism_id,
        )
        for organism in frame.organisms
    )
    resources = (
        tuple(
            ResourcePrimitive(x=item.x, y=item.y, amount=item.amount)
            for item in frame.resources
        )
        if show_resources
        else ()
    )
    carcasses = (
        tuple(
            CarcassPrimitive(
                carcass_id=item.carcass_id,
                x=item.x,
                y=item.y,
                resource_units=item.resource_units,
            )
            for item in frame.carcasses
        )
        if show_carcasses
        else ()
    )
    trails = (
        _movement_trails(
            history,
            step_index=step_index,
            active_organism_ids=tuple(item.organism_id for item in frame.organisms),
            trail_length=trail_length,
        )
        if show_trails
        else ()
    )
    return WorldPresentationFrame(
        committed_step_index=frame.step_index,
        world_width=frame.world_width,
        world_height=frame.world_height,
        organisms=organisms,
        resources=resources,
        carcasses=carcasses,
        trails=trails,
        selected_organism_id=selected_organism_id,
    )


def organism_marker_size(body_mass: int) -> int:
    """Map authoritative body mass to a bounded monotonic display size."""
    if type(body_mass) is not int:
        raise TypeError("body_mass must be an integer.")
    if body_mass < 1:
        raise ValueError("body_mass must be at least 1.")
    return max(10, min(26, 8 + body_mass))


def interpolate_organism_positions(
    left: SpatialObservation,
    right: SpatialObservation,
    *,
    alpha: float,
) -> tuple[InterpolatedOrganismPosition, ...]:
    """Interpolate display positions only for organisms present at both endpoints."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise TypeError("alpha must be a real number between 0 and 1.")
    resolved_alpha = float(alpha)
    if not 0.0 <= resolved_alpha <= 1.0:
        raise ValueError("alpha must be between 0 and 1 inclusive.")
    if left.world_width != right.world_width or left.world_height != right.world_height:
        raise ValueError("interpolation endpoints must use identical world bounds.")

    right_by_id = {item.organism_id: item for item in right.organisms}
    positions: list[InterpolatedOrganismPosition] = []
    for left_item in left.organisms:
        right_item = right_by_id.get(left_item.organism_id)
        if right_item is None:
            continue
        positions.append(
            InterpolatedOrganismPosition(
                organism_id=left_item.organism_id,
                x=_lerp(left_item.x, right_item.x, resolved_alpha),
                y=_lerp(left_item.y, right_item.y, resolved_alpha),
                left_step_index=left.step_index,
                right_step_index=right.step_index,
                alpha=resolved_alpha,
            )
        )
    return tuple(positions)


def _organism_primitive(
    snapshot: SpatialOrganismSnapshot,
    *,
    selected: bool,
) -> OrganismPrimitive:
    return OrganismPrimitive(
        organism_id=snapshot.organism_id,
        x=float(snapshot.x),
        y=float(snapshot.y),
        age=snapshot.age,
        energy=snapshot.energy,
        body_mass=snapshot.body_mass,
        mating_type=snapshot.mating_type,
        marker_size=organism_marker_size(snapshot.body_mass),
        selected=selected,
    )


def _movement_trails(
    history: tuple[SpatialObservation, ...],
    *,
    step_index: int,
    active_organism_ids: tuple[int, ...],
    trail_length: int,
) -> tuple[MovementTrail, ...]:
    selected_position = next(
        index for index, frame in enumerate(history) if frame.step_index == step_index
    )
    start = max(0, selected_position - trail_length + 1)
    recent_frames = history[start : selected_position + 1]
    trails: list[MovementTrail] = []
    for organism_id in active_organism_ids:
        points = tuple(
            (organism.x, organism.y)
            for frame in recent_frames
            for organism in frame.organisms
            if organism.organism_id == organism_id
        )
        if len(points) >= 2:
            trails.append(MovementTrail(organism_id=organism_id, points=points))
    return tuple(trails)


def _lerp(left: int, right: int, alpha: float) -> float:
    return float(left) + (float(right) - float(left)) * alpha
