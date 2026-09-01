"""Tests for immutable population observations and recording."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.observation import (
    CategoryCounts,
    IntegerSummary,
    IntegerTraitSummary,
    PopulationObservation,
    PopulationRecorder,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_population_recorder_summarizes_world_and_integer_traits() -> None:
    """Test population, ecosystem, mating-type, and genetic-trait summaries."""
    trait_name = "performance"
    architecture = make_integer_architecture(trait_name)
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={trait_name: 1},
        age=1,
        energy=10,
        body_mass=2,
        mating_type="alpha",
    )
    add_organism(
        state,
        trait_values={trait_name: 3},
        age=3,
        energy=20,
        body_mass=6,
        mating_type="beta",
        x=1,
    )
    state.domain_state.add_resources(
        x=0,
        y=0,
        amount=7,
    )
    state.domain_state.add_resources(
        x=1,
        y=1,
        amount=5,
    )
    recorder = PopulationRecorder(
        trait_names=(trait_name,),
    )

    recorder.observe(
        state.domain_state,
        step_index=0,
    )

    observation = recorder.latest
    assert observation is not None
    assert observation.step_index == 0
    assert observation.population_size == 2
    assert observation.carcass_count == 0
    assert observation.total_resources == 12
    assert observation.age == IntegerSummary(
        count=2,
        total=4,
        mean=2.0,
        minimum=1,
        maximum=3,
    )
    assert observation.energy == IntegerSummary(
        count=2,
        total=30,
        mean=15.0,
        minimum=10,
        maximum=20,
    )
    assert observation.body_mass == IntegerSummary(
        count=2,
        total=8,
        mean=4.0,
        minimum=2,
        maximum=6,
    )
    assert observation.mating_type_counts == CategoryCounts(
        value_counts=(("alpha", 1), ("beta", 1))
    )
    assert observation.mating_type_counts.count_for("alpha") == 1
    assert observation.mating_type_counts.frequency_for("alpha") == 0.5

    trait = observation.trait(trait_name)
    assert trait.summary == IntegerSummary(
        count=2,
        total=4,
        mean=2.0,
        minimum=1,
        maximum=3,
    )
    assert trait.value_counts == ((1, 1), (3, 1))
    assert trait.count_for(1) == 1
    assert trait.count_for(2) == 0


def test_population_recorder_records_empty_population() -> None:
    """Test extinction states produce valid empty summaries and category counts."""
    state = make_state()
    recorder = PopulationRecorder()

    recorder.observe(
        state.domain_state,
        step_index=4,
    )

    observation = recorder.latest
    assert observation is not None
    assert observation.population_size == 0
    assert observation.age == IntegerSummary(count=0, total=0)
    assert observation.energy == IntegerSummary(count=0, total=0)
    assert observation.body_mass == IntegerSummary(count=0, total=0)
    assert observation.mating_type_counts == CategoryCounts()
    assert observation.mating_type_counts.frequency_for("alpha") is None


def test_population_recorder_observation_interval_and_step_zero() -> None:
    """Test interval scheduling, baseline control, and duplicate suppression."""
    state = make_state()
    recorder = PopulationRecorder(
        every_n_steps=2,
        include_step_zero=True,
    )

    assert recorder.should_observe(state.domain_state, step_index=0)
    recorder.observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=1)
    assert recorder.should_observe(state.domain_state, step_index=2)

    recorder_without_baseline = PopulationRecorder(
        include_step_zero=False,
    )
    assert not recorder_without_baseline.should_observe(
        state.domain_state, step_index=0
    )
    assert recorder_without_baseline.should_observe(state.domain_state, step_index=1)


def test_population_recorder_requires_strictly_increasing_observation_steps() -> None:
    """Test manually recorded history cannot move backward or duplicate a step."""
    state = make_state()
    recorder = PopulationRecorder()
    recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=1)


def test_population_recorder_exposes_trait_requirements_and_immutable_history() -> None:
    """Test recorder dependencies and returned history snapshots."""
    recorder = PopulationRecorder(
        trait_names=("a", "b"),
    )
    state = make_state(
        genetic_architecture=make_integer_architecture("a", "b"),
    )
    add_organism(
        state,
        trait_values={"a": 1, "b": 2},
    )
    recorder.observe(state.domain_state, step_index=0)

    assert recorder.required_traits == frozenset({"a", "b"})
    assert type(recorder.observations) is tuple

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        recorder.observations[0].population_size = 10  # type: ignore[misc]


def test_population_recorder_clear_resets_history() -> None:
    """Test recorded history can be explicitly cleared for recorder reuse."""
    state = make_state()
    recorder = PopulationRecorder()
    recorder.observe(state.domain_state, step_index=0)

    recorder.clear()

    assert recorder.observations == ()
    assert recorder.latest is None
    assert recorder.should_observe(state.domain_state, step_index=0)


@pytest.mark.parametrize(
    "trait_names",
    [
        ("",),
        ("   ",),
        ("a", "a"),
    ],
)
def test_population_recorder_rejects_invalid_trait_names(
    trait_names: tuple[str, ...],
) -> None:
    """Test configured trait names are nonblank and unique."""
    with pytest.raises(ValueError):
        PopulationRecorder(
            trait_names=trait_names,
        )


def test_integer_summary_rejects_inconsistent_empty_state() -> None:
    """Test empty summary invariants are enforced."""
    with pytest.raises(ValueError, match="total=0"):
        IntegerSummary(
            count=0,
            total=1,
        )


def test_integer_trait_summary_validates_distribution_count() -> None:
    """Test trait value-count distributions match their numerical summary."""
    with pytest.raises(ValueError, match="sum to summary.count"):
        IntegerTraitSummary(
            trait_name="trait",
            summary=IntegerSummary(
                count=2,
                total=2,
                mean=1.0,
                minimum=1,
                maximum=1,
            ),
            value_counts=((1, 1),),
        )


def test_category_counts_require_unique_sorted_nonempty_labels() -> None:
    """Test categorical observations have deterministic validated labels."""
    with pytest.raises(ValueError, match="strictly increasing"):
        CategoryCounts(value_counts=(("beta", 1), ("alpha", 1)))

    with pytest.raises(ValueError, match="whitespace-only"):
        CategoryCounts(value_counts=(("   ", 1),))


def test_population_observation_validates_mating_type_count_total() -> None:
    """Test mating-type counts must account for the complete population."""
    summary = IntegerSummary(count=1, total=1, mean=1.0, minimum=1, maximum=1)

    with pytest.raises(ValueError, match="mating_type_counts.total_count"):
        PopulationObservation(
            step_index=0,
            population_size=1,
            carcass_count=0,
            total_resources=0,
            age=summary,
            energy=summary,
            body_mass=summary,
            mating_type_counts=CategoryCounts(),
        )


def test_population_observation_trait_lookup_rejects_missing_trait() -> None:
    """Test trait lookup fails clearly when a trait was not configured."""
    empty = IntegerSummary(count=0, total=0)
    observation = PopulationObservation(
        step_index=0,
        population_size=0,
        carcass_count=0,
        total_resources=0,
        age=empty,
        energy=empty,
        body_mass=empty,
        mating_type_counts=CategoryCounts(),
    )

    with pytest.raises(KeyError, match="missing"):
        observation.trait("missing")
