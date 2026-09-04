"""Tests for selecting actual committed cinematic events."""

from evo_engine.cinematic.events import (
    select_authoritative_events,
    select_authoritative_events_for_process,
    select_first_authoritative_event,
    select_first_authoritative_event_for_process,
)
from evo_engine.cinematic.timeline import (
    PortfolioAnimationFrame,
    PortfolioAnimationTimeline,
)
from evo_engine.observation import (
    CategoryCounts,
    IntegerSummary,
    IntegerTraitSummary,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent


def test_event_selection_preserves_actual_commit_order() -> None:
    first = _event(event_type="tests.FeedingEvent", stage=2)
    second = _event(event_type="tests.FeedingEvent", stage=3)
    other = _event(event_type="tests.DeathEvent", stage=4)
    timeline = PortfolioAnimationTimeline(
        trait_name="max_speed",
        frames=(_frame(events=(first, second, other)),),
    )

    assert select_authoritative_events(
        timeline,
        event_name="FeedingEvent",
    ) == (first, second)
    assert (
        select_first_authoritative_event(
            timeline,
            event_name="FeedingEvent",
        )
        is first
    )


def test_process_selection_handles_generic_nested_event_class_names() -> None:
    first = _event(
        event_type="tests.ResourceGeneration.Event",
        process_type="tests.ResourceGeneration",
        stage=2,
    )
    other = _event(
        event_type="tests.Movement.Event",
        process_type="tests.Movement",
        stage=3,
    )
    second = _event(
        event_type="tests.ResourceGeneration.Event",
        process_type="tests.ResourceGeneration",
        stage=4,
    )
    timeline = PortfolioAnimationTimeline(
        trait_name="max_speed",
        frames=(_frame(events=(first, other, second)),),
    )

    assert select_authoritative_events_for_process(
        timeline,
        process_name="ResourceGeneration",
    ) == (first, second)
    assert (
        select_first_authoritative_event_for_process(
            timeline,
            process_name="ResourceGeneration",
        )
        is first
    )


def test_identity_change_does_not_create_authoritative_event() -> None:
    timeline = PortfolioAnimationTimeline(
        trait_name="max_speed",
        frames=(
            _frame(
                appeared_ids=(9,),
                events=(),
            ),
        ),
    )

    assert select_authoritative_events(timeline, event_name="BirthEvent") == ()
    assert (
        select_first_authoritative_event(
            timeline,
            event_name="BirthEvent",
        )
        is None
    )
    assert (
        select_first_authoritative_event_for_process(
            timeline,
            process_name="Reproduction",
        )
        is None
    )


def _event(
    *,
    event_type: str,
    stage: int,
    process_type: str = "tests.Process",
) -> AppliedEvent:
    return AppliedEvent(
        event_step_index=0,
        stage_index=stage,
        process_type=process_type,
        event_type=event_type,
        event=object(),
    )


def _frame(
    *,
    events: tuple[AppliedEvent, ...],
    appeared_ids: tuple[int, ...] = (),
) -> PortfolioAnimationFrame:
    summary = IntegerSummary(count=0, total=0)
    population = PopulationObservation(
        step_index=0,
        population_size=0,
        carcass_count=0,
        total_resources=0,
        age=summary,
        energy=summary,
        body_mass=summary,
        mating_type_counts=CategoryCounts(),
        traits=(
            IntegerTraitSummary(
                trait_name="max_speed",
                summary=summary,
                value_counts=(),
            ),
        ),
    )
    return PortfolioAnimationFrame(
        spatial=SpatialObservation(
            step_index=0,
            world_width=2,
            world_height=2,
        ),
        population=population,
        applied_events=events,
        appeared_organism_ids=appeared_ids,
        trait_mean=None,
    )
