"""Prepare deterministic cinematic timelines from committed observations."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.observation import PopulationObservation, SpatialObservation
from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class PortfolioAnimationFrame:
    """Pair one committed spatial frame with authoritative population analytics.

    Attributes:
        spatial: Immutable committed spatial observation for the step.
        population: Immutable committed population observation for the same step.
        born_organism_ids: Organism IDs appearing since the preceding frame.
        departed_organism_ids: Organism IDs absent since the preceding frame.
        trait_mean: Recorded mean for the selected trait, or ``None`` for an
            empty population.
    """

    spatial: SpatialObservation = attrs.field(
        validator=attrs.validators.instance_of(SpatialObservation),
    )
    population: PopulationObservation = attrs.field(
        validator=attrs.validators.instance_of(PopulationObservation),
    )
    born_organism_ids: tuple[int, ...] = attrs.field(factory=tuple)
    departed_organism_ids: tuple[int, ...] = attrs.field(factory=tuple)
    trait_mean: float | None = None

    def __attrs_post_init__(self) -> None:
        """Validate aligned step and deterministic identity-transition values."""
        if self.spatial.step_index != self.population.step_index:
            raise ValueError(
                "spatial and population observations must represent the same step."
            )
        _validate_sorted_unique_ids(
            self.born_organism_ids,
            name="born_organism_ids",
        )
        _validate_sorted_unique_ids(
            self.departed_organism_ids,
            name="departed_organism_ids",
        )
        if set(self.born_organism_ids) & set(self.departed_organism_ids):
            raise ValueError(
                "An organism ID cannot be both born and departed in one frame."
            )
        if self.trait_mean is not None:
            validators.validate_float(self.trait_mean, name="trait_mean")

    @property
    def step_index(self) -> int:
        """Return the completed simulation-step index represented by the frame."""
        return self.spatial.step_index


@attrs.frozen(slots=True, kw_only=True)
class PortfolioAnimationTimeline:
    """Store renderer-owned deterministic ordering over committed observations.

    This value is deliberately a cinematic presentation transform, not a generic
    simulation replay contract. Its frames retain only immutable observation
    values that were already committed before rendering begins.

    Attributes:
        trait_name: Recorded genetic-phenotype trait highlighted by the animation.
        frames: Chronological presentation frames.
    """

    trait_name: str = attrs.field(validator=attrs_validators.validate_str)
    frames: tuple[PortfolioAnimationFrame, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate frame types, chronology, and stable world dimensions."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")
        validators.validate_tuple(self.frames, name="frames")
        previous_step: int | None = None
        world_bounds: tuple[int, int] | None = None
        for index, frame in enumerate(self.frames):
            if not isinstance(frame, PortfolioAnimationFrame):
                raise TypeError(
                    f"frames[{index}] must be a PortfolioAnimationFrame; "
                    f"received {frame!r}."
                )
            if previous_step is not None and frame.step_index <= previous_step:
                raise ValueError(
                    "animation frames must have strictly increasing steps."
                )
            previous_step = frame.step_index

            frame_bounds = (frame.spatial.world_width, frame.spatial.world_height)
            if world_bounds is None:
                world_bounds = frame_bounds
            elif frame_bounds != world_bounds:
                raise ValueError("animation world dimensions must remain stable.")

    @property
    def world_bounds(self) -> tuple[int, int] | None:
        """Return stable ``(width, height)`` bounds, or ``None`` when empty."""
        if not self.frames:
            return None
        first = self.frames[0].spatial
        return first.world_width, first.world_height

    @property
    def final_frame(self) -> PortfolioAnimationFrame | None:
        """Return the last presentation frame, if one exists."""
        if not self.frames:
            return None
        return self.frames[-1]


def build_portfolio_animation_timeline(
    *,
    spatial_history: Sequence[SpatialObservation],
    population_history: Sequence[PopulationObservation],
    trait_name: str,
) -> PortfolioAnimationTimeline:
    """Build deterministic cinematic frames from committed observation histories.

    Args:
        spatial_history: Chronological immutable spatial observations.
        population_history: Chronological immutable population observations.
        trait_name: Recorded trait whose authoritative mean should be displayed.

    Returns:
        Renderer-owned timeline containing aligned committed observations and
        deterministic organism identity transitions.

    Raises:
        TypeError: If history entries are not the expected committed value types.
        ValueError: If histories do not align, chronology is invalid, world bounds
            change, or population counts disagree with spatial snapshots.
        KeyError: If a history lacks ``trait_name`` in a population observation.
    """
    validated_trait_name = _validate_trait_name(trait_name)
    spatial_frames = tuple(spatial_history)
    population_frames = tuple(population_history)
    _validate_history_lengths(spatial_frames, population_frames)

    frames = _build_animation_frames(
        spatial_frames,
        population_frames,
        trait_name=validated_trait_name,
    )
    return PortfolioAnimationTimeline(
        trait_name=validated_trait_name,
        frames=frames,
    )


def _validate_trait_name(trait_name: str) -> str:
    validated = validators.validate_str(trait_name, name="trait_name")
    if not validated.strip():
        raise ValueError("trait_name must not be empty or whitespace-only.")
    return validated


def _validate_history_lengths(
    spatial_history: tuple[SpatialObservation, ...],
    population_history: tuple[PopulationObservation, ...],
) -> None:
    if len(spatial_history) != len(population_history):
        raise ValueError(
            "spatial_history and population_history must contain the same number "
            "of committed steps."
        )


def _build_animation_frames(
    spatial_history: tuple[SpatialObservation, ...],
    population_history: tuple[PopulationObservation, ...],
    *,
    trait_name: str,
) -> tuple[PortfolioAnimationFrame, ...]:
    frames: list[PortfolioAnimationFrame] = []
    previous_ids: frozenset[int] | None = None
    for index, (spatial, population) in enumerate(
        zip(spatial_history, population_history, strict=True)
    ):
        frame, previous_ids = _build_animation_frame(
            index=index,
            spatial=spatial,
            population=population,
            trait_name=trait_name,
            previous_ids=previous_ids,
        )
        frames.append(frame)
    return tuple(frames)


def _build_animation_frame(
    *,
    index: int,
    spatial: SpatialObservation,
    population: PopulationObservation,
    trait_name: str,
    previous_ids: frozenset[int] | None,
) -> tuple[PortfolioAnimationFrame, frozenset[int]]:
    _validate_history_pair(index=index, spatial=spatial, population=population)
    current_ids = frozenset(snapshot.organism_id for snapshot in spatial.organisms)
    _validate_population_count(spatial=spatial, population=population, ids=current_ids)
    born_ids, departed_ids = _identity_transitions(previous_ids, current_ids)
    frame = PortfolioAnimationFrame(
        spatial=spatial,
        population=population,
        born_organism_ids=born_ids,
        departed_organism_ids=departed_ids,
        trait_mean=population.trait(trait_name).summary.mean,
    )
    return frame, current_ids


def _validate_history_pair(
    *,
    index: int,
    spatial: SpatialObservation,
    population: PopulationObservation,
) -> None:
    if not isinstance(spatial, SpatialObservation):
        raise TypeError(
            f"spatial_history[{index}] must be a SpatialObservation; "
            f"received {spatial!r}."
        )
    if not isinstance(population, PopulationObservation):
        raise TypeError(
            f"population_history[{index}] must be a PopulationObservation; "
            f"received {population!r}."
        )
    if spatial.step_index != population.step_index:
        raise ValueError(
            f"History step mismatch at index {index}: spatial step "
            f"{spatial.step_index}, population step {population.step_index}."
        )


def _validate_population_count(
    *,
    spatial: SpatialObservation,
    population: PopulationObservation,
    ids: frozenset[int],
) -> None:
    if len(ids) != population.population_size:
        raise ValueError(
            f"Population count mismatch at step {spatial.step_index}: spatial "
            f"frame has {len(ids)} organisms while population observation records "
            f"{population.population_size}."
        )


def _identity_transitions(
    previous_ids: frozenset[int] | None,
    current_ids: frozenset[int],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if previous_ids is None:
        return (), ()
    return (
        tuple(sorted(current_ids - previous_ids)),
        tuple(sorted(previous_ids - current_ids)),
    )


def _validate_sorted_unique_ids(values: tuple[int, ...], *, name: str) -> None:
    validators.validate_tuple(values, name=name)
    previous: int | None = None
    for index, value in enumerate(values):
        validated = validators.validate_int_ge(
            value,
            bound=0,
            name=f"{name}[{index}]",
        )
        if previous is not None and validated <= previous:
            raise ValueError(f"{name} must contain unique IDs in increasing order.")
        previous = validated
