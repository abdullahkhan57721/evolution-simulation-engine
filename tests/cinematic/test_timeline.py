"""Tests for deterministic science-aware cinematic timeline preparation."""

from __future__ import annotations

from collections import Counter

import pytest

from evo_engine.cinematic import build_portfolio_animation_timeline
from evo_engine.observation import (
    CategoryCounts,
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitSnapshot,
    IntegerSummary,
    IntegerTraitSummary,
    PopulationObservation,
    SpatialObservation,
    SpatialOrganismSnapshot,
    SpatialResourceSnapshot,
)
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.telemetry import AppliedEvent, StepTelemetry

_TRAIT_NAME = "growth_rate"
_FOCAL_TRAIT = "max_speed"


def test_timeline_aligns_authoritative_values_and_identity_transitions() -> None:
    spatial_history = (
        _spatial(step=0, organism_ids=(1, 2)),
        _spatial(step=1, organism_ids=(2, 3)),
        _spatial(step=2, organism_ids=()),
    )
    population_history = (
        _population(step=0, trait_values=(1, 2)),
        _population(step=1, trait_values=(2, 4)),
        _population(step=2, trait_values=()),
    )

    timeline = build_portfolio_animation_timeline(
        spatial_history=spatial_history,
        population_history=population_history,
        trait_name=_TRAIT_NAME,
    )

    assert timeline.world_bounds == (4, 4)
    assert tuple(frame.step_index for frame in timeline.frames) == (0, 1, 2)
    assert timeline.frames[0].appeared_organism_ids == ()
    assert timeline.frames[0].departed_organism_ids == ()
    assert timeline.frames[1].appeared_organism_ids == (3,)
    assert timeline.frames[1].departed_organism_ids == (1,)
    assert timeline.frames[2].appeared_organism_ids == ()
    assert timeline.frames[2].departed_organism_ids == (2, 3)
    assert timeline.frames[0].trait_mean == 1.5
    assert timeline.frames[1].trait_mean == 3.0
    assert timeline.frames[2].trait_mean is None
    assert tuple(item.organism_id for item in timeline.frames[0].organisms) == (1, 2)
    assert all(item.focal_value is None for item in timeline.frames[0].organisms)


def test_timeline_joins_committed_individual_trait_values() -> None:
    encoding = _encoding()
    timeline = build_portfolio_animation_timeline(
        spatial_history=(_spatial(step=0, organism_ids=(1, 2)),),
        population_history=(_population(step=0, trait_values=(1, 2)),),
        trait_name=_TRAIT_NAME,
        individual_trait_history=(
            _individual_traits(step=0, values=((1, 1), (2, 5))),
        ),
        focal_encoding=encoding,
    )

    first = timeline.frames[0]
    assert first.organism(1).focal_value == 1
    assert first.organism(1).focal_normalized == 0.0
    assert first.organism(2).focal_value == 5
    assert first.organism(2).focal_normalized == 1.0
    assert timeline.focal_encoding is encoding


def test_timeline_rejects_missing_or_misaligned_focal_evidence() -> None:
    encoding = _encoding()
    spatial = (_spatial(step=0, organism_ids=(1, 2)),)
    population = (_population(step=0, trait_values=(1, 2)),)

    with pytest.raises(ValueError, match="requires committed"):
        build_portfolio_animation_timeline(
            spatial_history=spatial,
            population_history=population,
            trait_name=_TRAIT_NAME,
            focal_encoding=encoding,
        )

    with pytest.raises(ValueError, match="organism IDs"):
        build_portfolio_animation_timeline(
            spatial_history=spatial,
            population_history=population,
            trait_name=_TRAIT_NAME,
            individual_trait_history=(
                _individual_traits(step=0, values=((1, 1),)),
            ),
            focal_encoding=encoding,
        )


def test_timeline_attaches_authoritative_events_in_commit_order() -> None:
    first_event = _event(step=0, stage=0, event_type="FeedingEvent")
    second_event = _event(step=0, stage=1, event_type="MovementEvent")
    third_event = _event(step=1, stage=0, event_type="DeathEvent")
    timeline = build_portfolio_animation_timeline(
        spatial_history=(
            _spatial(step=0, organism_ids=(1,)),
            _spatial(step=1, organism_ids=(1,)),
            _spatial(step=2, organism_ids=()),
        ),
        population_history=(
            _population(step=0, trait_values=(1,)),
            _population(step=1, trait_values=(1,)),
            _population(step=2, trait_values=()),
        ),
        trait_name=_TRAIT_NAME,
        event_history=(
            StepTelemetry(
                completed_step_index=1,
                events=(first_event, second_event),
            ),
            StepTelemetry(
                completed_step_index=2,
                events=(third_event,),
            ),
        ),
    )

    assert timeline.frames[0].applied_events == ()
    assert timeline.frames[1].applied_events == (first_event, second_event)
    assert timeline.frames[2].applied_events == (third_event,)
    assert timeline.frames[2].departed_organism_ids == (1,)


def test_identity_transition_is_not_reclassified_as_authoritative_event() -> None:
    timeline = build_portfolio_animation_timeline(
        spatial_history=(
            _spatial(step=0, organism_ids=(1,)),
            _spatial(step=1, organism_ids=(1, 2)),
        ),
        population_history=(
            _population(step=0, trait_values=(1,)),
            _population(step=1, trait_values=(1, 2)),
        ),
        trait_name=_TRAIT_NAME,
    )

    assert timeline.frames[1].appeared_organism_ids == (2,)
    assert timeline.frames[1].applied_events == ()


def test_timeline_preserves_actual_resource_deposits() -> None:
    spatial = _spatial(
        step=0,
        organism_ids=(1,),
        resources=(
            SpatialResourceSnapshot(x=0, y=0, amount=3),
            SpatialResourceSnapshot(x=3, y=3, amount=7),
        ),
    )
    timeline = build_portfolio_animation_timeline(
        spatial_history=(spatial,),
        population_history=(_population(step=0, trait_values=(1,)),),
        trait_name=_TRAIT_NAME,
    )

    assert timeline.frames[0].spatial.resources == spatial.resources


def test_empty_histories_produce_empty_renderer_owned_timeline() -> None:
    timeline = build_portfolio_animation_timeline(
        spatial_history=(),
        population_history=(),
        trait_name=_TRAIT_NAME,
    )

    assert timeline.frames == ()
    assert timeline.world_bounds is None
    assert timeline.final_frame is None


def test_timeline_rejects_history_length_mismatch() -> None:
    with pytest.raises(ValueError, match="same number"):
        build_portfolio_animation_timeline(
            spatial_history=(_spatial(step=0, organism_ids=(1,)),),
            population_history=(),
            trait_name=_TRAIT_NAME,
        )


def test_timeline_rejects_step_mismatch() -> None:
    with pytest.raises(ValueError, match="History step mismatch"):
        build_portfolio_animation_timeline(
            spatial_history=(_spatial(step=1, organism_ids=(1,)),),
            population_history=(_population(step=0, trait_values=(1,)),),
            trait_name=_TRAIT_NAME,
        )


def test_timeline_rejects_unstable_world_bounds() -> None:
    with pytest.raises(ValueError, match="world dimensions"):
        build_portfolio_animation_timeline(
            spatial_history=(
                _spatial(step=0, organism_ids=(1,), width=4),
                _spatial(step=1, organism_ids=(1,), width=5),
            ),
            population_history=(
                _population(step=0, trait_values=(1,)),
                _population(step=1, trait_values=(1,)),
            ),
            trait_name=_TRAIT_NAME,
        )


def test_timeline_rejects_population_count_mismatch() -> None:
    with pytest.raises(ValueError, match="Population count mismatch"):
        build_portfolio_animation_timeline(
            spatial_history=(_spatial(step=0, organism_ids=(1, 2)),),
            population_history=(_population(step=0, trait_values=(1,)),),
            trait_name=_TRAIT_NAME,
        )


def test_timeline_rejects_missing_selected_population_trait() -> None:
    population = _population(step=0, trait_values=(1,))
    population_without_traits = PopulationObservation(
        step_index=population.step_index,
        population_size=population.population_size,
        carcass_count=population.carcass_count,
        total_resources=population.total_resources,
        age=population.age,
        energy=population.energy,
        body_mass=population.body_mass,
        mating_type_counts=population.mating_type_counts,
        traits=(),
    )

    with pytest.raises(KeyError, match="no recorded trait"):
        build_portfolio_animation_timeline(
            spatial_history=(_spatial(step=0, organism_ids=(1,)),),
            population_history=(population_without_traits,),
            trait_name=_TRAIT_NAME,
        )


def _encoding() -> ContinuousTraitEncoding:
    return ContinuousTraitEncoding(
        trait_name=_FOCAL_TRAIT,
        label="Maximum speed",
        lower_bound=1,
        upper_bound=5,
    )


def _individual_traits(
    *,
    step: int,
    values: tuple[tuple[int, int], ...],
) -> IndividualGeneticTraitObservation:
    return IndividualGeneticTraitObservation(
        step_index=step,
        trait_names=(_FOCAL_TRAIT,),
        individuals=tuple(
            IndividualGeneticTraitSnapshot(
                organism_id=organism_id,
                trait_values=(value,),
            )
            for organism_id, value in values
        ),
    )


def _event(*, step: int, stage: int, event_type: str) -> AppliedEvent:
    return AppliedEvent(
        event_step_index=step,
        stage_index=stage,
        process_type="tests.Process",
        event_type=f"tests.{event_type}",
        event=object(),
    )


def _spatial(
    *,
    step: int,
    organism_ids: tuple[int, ...],
    width: int = 4,
    height: int = 4,
    resources: tuple[SpatialResourceSnapshot, ...] = (),
) -> SpatialObservation:
    organisms = tuple(
        SpatialOrganismSnapshot(
            organism_id=organism_id,
            x=index % width,
            y=index // width,
            age=step,
            energy=20,
            body_mass=5,
            mating_type="A",
        )
        for index, organism_id in enumerate(organism_ids)
    )
    return SpatialObservation(
        step_index=step,
        world_width=width,
        world_height=height,
        organisms=organisms,
        resources=resources,
    )


def _population(*, step: int, trait_values: tuple[int, ...]) -> PopulationObservation:
    population_size = len(trait_values)
    standard_values = (1,) * population_size
    trait_summary = _integer_summary(trait_values)
    value_counts = tuple(sorted(Counter(trait_values).items()))
    categories = () if population_size == 0 else (("A", population_size),)
    return PopulationObservation(
        step_index=step,
        population_size=population_size,
        carcass_count=0,
        total_resources=0,
        age=_integer_summary(standard_values),
        energy=_integer_summary(standard_values),
        body_mass=_integer_summary(standard_values),
        mating_type_counts=CategoryCounts(value_counts=categories),
        traits=(
            IntegerTraitSummary(
                trait_name=_TRAIT_NAME,
                summary=trait_summary,
                value_counts=value_counts,
            ),
        ),
    )


def _integer_summary(values: tuple[int, ...]) -> IntegerSummary:
    if not values:
        return IntegerSummary(count=0, total=0)
    total = sum(values)
    return IntegerSummary(
        count=len(values),
        total=total,
        mean=total / len(values),
        minimum=min(values),
        maximum=max(values),
    )
