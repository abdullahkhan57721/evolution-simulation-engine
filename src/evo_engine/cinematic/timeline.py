"""Prepare deterministic cinematic timelines from committed observations."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.cinematic.primitives import CinematicOrganismPrimitive
from evo_engine.observation import PopulationObservation, SpatialObservation
from evo_engine.observation.individual_traits import IndividualGeneticTraitObservation
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.telemetry import AppliedEvent, StepTelemetry
from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class PortfolioAnimationFrame:
    """Pair one committed world frame with prepared cinematic evidence.

    Attributes:
        spatial: Immutable committed spatial observation for the step.
        population: Immutable committed population observation for the same step.
        organisms: Renderer-ready organism values derived only from committed
            observations.
        applied_events: Authoritative events committed since the preceding
            displayed scientific frame, in commit order.
        appeared_organism_ids: IDs newly visible since the preceding frame.
        departed_organism_ids: IDs no longer visible since the preceding frame.
        trait_mean: Recorded mean for the selected population trait.
    """

    spatial: SpatialObservation = attrs.field(
        validator=attrs.validators.instance_of(SpatialObservation),
    )
    population: PopulationObservation = attrs.field(
        validator=attrs.validators.instance_of(PopulationObservation),
    )
    organisms: tuple[CinematicOrganismPrimitive, ...] = attrs.field(factory=tuple)
    applied_events: tuple[AppliedEvent, ...] = attrs.field(factory=tuple)
    appeared_organism_ids: tuple[int, ...] = attrs.field(factory=tuple)
    departed_organism_ids: tuple[int, ...] = attrs.field(factory=tuple)
    trait_mean: float | None = None

    def __attrs_post_init__(self) -> None:
        """Validate aligned evidence and deterministic prepared values."""
        if self.spatial.step_index != self.population.step_index:
            raise ValueError(
                "spatial and population observations must represent the same step."
            )
        _validate_organisms(self.organisms, spatial=self.spatial)
        _validate_applied_events(self.applied_events)
        _validate_sorted_unique_ids(
            self.appeared_organism_ids,
            name="appeared_organism_ids",
        )
        _validate_sorted_unique_ids(
            self.departed_organism_ids,
            name="departed_organism_ids",
        )
        if set(self.appeared_organism_ids) & set(self.departed_organism_ids):
            raise ValueError(
                "An organism ID cannot both appear and depart in one frame."
            )
        if self.trait_mean is not None:
            validators.validate_float(self.trait_mean, name="trait_mean")

    @property
    def step_index(self) -> int:
        """Return the completed simulation-step index represented by the frame."""
        return self.spatial.step_index

    def organism(self, organism_id: int) -> CinematicOrganismPrimitive:
        """Return one prepared organism primitive by permanent organism ID.

        Args:
            organism_id: Permanent organism ID.

        Returns:
            Matching cinematic organism primitive.

        Raises:
            KeyError: If the organism is absent from this frame.
        """
        validated = validators.validate_int_ge(
            organism_id,
            bound=0,
            name="organism_id",
        )
        for organism in self.organisms:
            if organism.organism_id == validated:
                return organism
        raise KeyError(f"No cinematic organism {validated} in step {self.step_index}.")


@attrs.frozen(slots=True, kw_only=True)
class PortfolioAnimationTimeline:
    """Store renderer-owned ordering over committed scientific observations.

    Attributes:
        trait_name: Recorded population trait highlighted by the animation.
        frames: Chronological presentation frames.
        focal_encoding: Optional shared scientific encoding for individual fill.
    """

    trait_name: str = attrs.field(validator=attrs_validators.validate_str)
    frames: tuple[PortfolioAnimationFrame, ...] = attrs.field(factory=tuple)
    focal_encoding: ContinuousTraitEncoding | None = None

    def __attrs_post_init__(self) -> None:
        """Validate frame types, chronology, world bounds, and focal encoding."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")
        validators.validate_tuple(self.frames, name="frames")
        if self.focal_encoding is not None and not isinstance(
            self.focal_encoding,
            ContinuousTraitEncoding,
        ):
            raise TypeError(
                "focal_encoding must be a ContinuousTraitEncoding or None."
            )

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
    individual_trait_history: Sequence[IndividualGeneticTraitObservation] | None = None,
    event_history: Sequence[StepTelemetry] = (),
    focal_encoding: ContinuousTraitEncoding | None = None,
) -> PortfolioAnimationTimeline:
    """Build deterministic cinematic frames from committed scientific evidence.

    Args:
        spatial_history: Chronological immutable spatial observations.
        population_history: Chronological immutable population observations.
        trait_name: Recorded population trait whose mean should be displayed.
        individual_trait_history: Optional per-organism committed trait records.
        event_history: Optional committed step telemetry in chronological order.
        focal_encoding: Optional shared scientific encoding for one individual
            genetic-phenotype trait.

    Returns:
        Renderer-owned timeline containing prepared immutable evidence.

    Raises:
        TypeError: If history entries are not the expected committed value types.
        ValueError: If histories, scientific encodings, or chronology misalign.
        KeyError: If required population or individual trait evidence is absent.
    """
    validated_trait_name = _validate_trait_name(trait_name)
    spatial_frames = tuple(spatial_history)
    population_frames = tuple(population_history)
    individual_frames = (
        None
        if individual_trait_history is None
        else tuple(individual_trait_history)
    )
    telemetry_steps = tuple(event_history)

    _validate_history_lengths(spatial_frames, population_frames)
    _validate_focal_inputs(
        spatial_frames=spatial_frames,
        individual_frames=individual_frames,
        focal_encoding=focal_encoding,
    )
    _validate_event_history(telemetry_steps)

    frames = _build_animation_frames(
        spatial_frames,
        population_frames,
        trait_name=validated_trait_name,
        individual_frames=individual_frames,
        event_history=telemetry_steps,
        focal_encoding=focal_encoding,
    )
    return PortfolioAnimationTimeline(
        trait_name=validated_trait_name,
        frames=frames,
        focal_encoding=focal_encoding,
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


def _validate_focal_inputs(
    *,
    spatial_frames: tuple[SpatialObservation, ...],
    individual_frames: tuple[IndividualGeneticTraitObservation, ...] | None,
    focal_encoding: ContinuousTraitEncoding | None,
) -> None:
    if focal_encoding is None:
        if individual_frames is not None:
            raise ValueError(
                "individual_trait_history requires a focal_encoding so committed "
                "values are not silently ignored."
            )
        return
    if not isinstance(focal_encoding, ContinuousTraitEncoding):
        raise TypeError("focal_encoding must be a ContinuousTraitEncoding or None.")
    if individual_frames is None:
        raise ValueError(
            "focal_encoding requires committed individual_trait_history."
        )
    if len(individual_frames) != len(spatial_frames):
        raise ValueError(
            "individual_trait_history must align one-for-one with spatial_history."
        )

    for index, (spatial, individual) in enumerate(
        zip(spatial_frames, individual_frames, strict=True)
    ):
        if not isinstance(individual, IndividualGeneticTraitObservation):
            raise TypeError(
                f"individual_trait_history[{index}] must be an "
                "IndividualGeneticTraitObservation."
            )
        if spatial.step_index != individual.step_index:
            raise ValueError(
                f"Individual-trait step mismatch at index {index}: spatial step "
                f"{spatial.step_index}, individual step {individual.step_index}."
            )
        spatial_ids = tuple(item.organism_id for item in spatial.organisms)
        individual_ids = tuple(item.organism_id for item in individual.individuals)
        if spatial_ids != individual_ids:
            raise ValueError(
                f"Individual-trait organism IDs must match spatial IDs at step "
                f"{spatial.step_index}."
            )
        if focal_encoding.trait_name not in individual.trait_names:
            raise KeyError(
                "No individual genetic trait recorded for "
                f"{focal_encoding.trait_name!r} at step {spatial.step_index}."
            )


def _validate_event_history(event_history: tuple[StepTelemetry, ...]) -> None:
    previous_step: int | None = None
    for index, telemetry in enumerate(event_history):
        if not isinstance(telemetry, StepTelemetry):
            raise TypeError(
                f"event_history[{index}] must be a StepTelemetry; "
                f"received {telemetry!r}."
            )
        if (
            previous_step is not None
            and telemetry.completed_step_index <= previous_step
        ):
            raise ValueError(
                "event_history must have strictly increasing completed steps."
            )
        previous_step = telemetry.completed_step_index


def _build_animation_frames(
    spatial_history: tuple[SpatialObservation, ...],
    population_history: tuple[PopulationObservation, ...],
    *,
    trait_name: str,
    individual_frames: tuple[IndividualGeneticTraitObservation, ...] | None,
    event_history: tuple[StepTelemetry, ...],
    focal_encoding: ContinuousTraitEncoding | None,
) -> tuple[PortfolioAnimationFrame, ...]:
    frames: list[PortfolioAnimationFrame] = []
    previous_ids: frozenset[int] | None = None
    previous_step: int | None = None
    for index, (spatial, population) in enumerate(
        zip(spatial_history, population_history, strict=True)
    ):
        individual = None if individual_frames is None else individual_frames[index]
        frame, previous_ids = _build_animation_frame(
            index=index,
            spatial=spatial,
            population=population,
            trait_name=trait_name,
            individual=individual,
            event_history=event_history,
            focal_encoding=focal_encoding,
            previous_ids=previous_ids,
            previous_step=previous_step,
        )
        frames.append(frame)
        previous_step = spatial.step_index
    return tuple(frames)


def _build_animation_frame(
    *,
    index: int,
    spatial: SpatialObservation,
    population: PopulationObservation,
    trait_name: str,
    individual: IndividualGeneticTraitObservation | None,
    event_history: tuple[StepTelemetry, ...],
    focal_encoding: ContinuousTraitEncoding | None,
    previous_ids: frozenset[int] | None,
    previous_step: int | None,
) -> tuple[PortfolioAnimationFrame, frozenset[int]]:
    _validate_history_pair(index=index, spatial=spatial, population=population)
    current_ids = frozenset(snapshot.organism_id for snapshot in spatial.organisms)
    _validate_population_count(spatial=spatial, population=population, ids=current_ids)
    appeared_ids, departed_ids = _identity_transitions(previous_ids, current_ids)

    frame = PortfolioAnimationFrame(
        spatial=spatial,
        population=population,
        organisms=_prepare_organisms(
            spatial=spatial,
            individual=individual,
            focal_encoding=focal_encoding,
        ),
        applied_events=_events_since_previous_frame(
            event_history,
            previous_step=previous_step,
            current_step=spatial.step_index,
        ),
        appeared_organism_ids=appeared_ids,
        departed_organism_ids=departed_ids,
        trait_mean=population.trait(trait_name).summary.mean,
    )
    return frame, current_ids


def _prepare_organisms(
    *,
    spatial: SpatialObservation,
    individual: IndividualGeneticTraitObservation | None,
    focal_encoding: ContinuousTraitEncoding | None,
) -> tuple[CinematicOrganismPrimitive, ...]:
    prepared: list[CinematicOrganismPrimitive] = []
    for snapshot in spatial.organisms:
        focal_value: int | None = None
        focal_normalized: float | None = None
        if focal_encoding is not None:
            if individual is None:
                raise ValueError("focal_encoding requires individual trait evidence.")
            focal_value = individual.trait_value(
                snapshot.organism_id,
                focal_encoding.trait_name,
            )
            focal_normalized = focal_encoding.normalize(focal_value)
        prepared.append(
            CinematicOrganismPrimitive(
                organism_id=snapshot.organism_id,
                x=snapshot.x,
                y=snapshot.y,
                body_mass=snapshot.body_mass,
                mating_type=snapshot.mating_type,
                focal_value=focal_value,
                focal_normalized=focal_normalized,
            )
        )
    return tuple(prepared)


def _events_since_previous_frame(
    event_history: tuple[StepTelemetry, ...],
    *,
    previous_step: int | None,
    current_step: int,
) -> tuple[AppliedEvent, ...]:
    if previous_step is None:
        return ()
    return tuple(
        event
        for telemetry in event_history
        if previous_step < telemetry.completed_step_index <= current_step
        for event in telemetry.events
    )


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


def _validate_organisms(
    organisms: tuple[CinematicOrganismPrimitive, ...],
    *,
    spatial: SpatialObservation,
) -> None:
    validators.validate_tuple(organisms, name="organisms")
    ids: list[int] = []
    for index, organism in enumerate(organisms):
        if not isinstance(organism, CinematicOrganismPrimitive):
            raise TypeError(
                f"organisms[{index}] must be a CinematicOrganismPrimitive."
            )
        ids.append(organism.organism_id)
    spatial_ids = [snapshot.organism_id for snapshot in spatial.organisms]
    if ids != spatial_ids:
        raise ValueError(
            "prepared organism IDs must preserve authoritative spatial ordering."
        )


def _validate_applied_events(events: tuple[AppliedEvent, ...]) -> None:
    validators.validate_tuple(events, name="applied_events")
    for index, event in enumerate(events):
        if not isinstance(event, AppliedEvent):
            raise TypeError(
                f"applied_events[{index}] must be an AppliedEvent; "
                f"received {event!r}."
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
