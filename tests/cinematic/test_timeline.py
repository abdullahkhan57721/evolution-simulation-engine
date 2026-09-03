"""Tests for deterministic cinematic timeline preparation."""

from __future__ import annotations

from collections import Counter

import pytest

from evo_engine.cinematic import build_portfolio_animation_timeline
from evo_engine.observation import (
    CategoryCounts,
    IntegerSummary,
    IntegerTraitSummary,
    PopulationObservation,
    SpatialObservation,
    SpatialOrganismSnapshot,
)

_TRAIT_NAME = "growth_rate"


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
    assert timeline.frames[0].born_organism_ids == ()
    assert timeline.frames[0].departed_organism_ids == ()
    assert timeline.frames[1].born_organism_ids == (3,)
    assert timeline.frames[1].departed_organism_ids == (1,)
    assert timeline.frames[2].born_organism_ids == ()
    assert timeline.frames[2].departed_organism_ids == (2, 3)
    assert timeline.frames[0].trait_mean == 1.5
    assert timeline.frames[1].trait_mean == 3.0
    assert timeline.frames[2].trait_mean is None
    assert timeline.frames[2].population.population_size == 0


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


def test_timeline_rejects_missing_selected_trait() -> None:
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


def _spatial(
    *,
    step: int,
    organism_ids: tuple[int, ...],
    width: int = 4,
    height: int = 4,
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
