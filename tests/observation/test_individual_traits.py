"""Tests for selective per-organism genetic-phenotype observations."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import (
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitRecorder,
    IndividualGeneticTraitSnapshot,
    SpatialRecorder,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_individual_trait_recorder_records_selected_values_deterministically() -> None:
    """Test selected integer traits remain associated with stable organism IDs."""
    trait_names = ("speed", "intake")
    state = make_state(
        genetic_architecture=make_integer_architecture(*trait_names),
    )
    first = add_organism(
        state,
        trait_values={"speed": 1, "intake": 3},
        x=2,
        y=1,
    )
    second = add_organism(
        state,
        trait_values={"speed": 4, "intake": 7},
        x=0,
        y=2,
    )
    recorder = IndividualGeneticTraitRecorder(trait_names=trait_names)

    recorder.observe(state.domain_state, step_index=3)

    assert recorder.latest == IndividualGeneticTraitObservation(
        step_index=3,
        trait_names=trait_names,
        individuals=(
            IndividualGeneticTraitSnapshot(
                organism_id=first.id,
                trait_values=(1, 3),
            ),
            IndividualGeneticTraitSnapshot(
                organism_id=second.id,
                trait_values=(4, 7),
            ),
        ),
    )
    assert recorder.latest is not None
    assert recorder.latest.trait_value(first.id, "speed") == 1
    assert recorder.latest.trait_value(second.id, "intake") == 7


def test_individual_trait_recorder_exposes_requirements_and_immutable_values() -> None:
    """Test configured traits participate in preflight and records are immutable."""
    recorder = IndividualGeneticTraitRecorder(trait_names=("a", "b"))
    state = make_state(
        genetic_architecture=make_integer_architecture("a", "b"),
    )
    add_organism(state, trait_values={"a": 2, "b": 5})

    recorder.observe(state.domain_state, step_index=0)

    assert recorder.required_traits == frozenset({"a", "b"})
    assert type(recorder.observations) is tuple
    assert recorder.observations[0].individuals[0].trait_values == (2, 5)
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        recorder.observations[0].step_index = 4  # type: ignore[misc]


def test_individual_trait_recorder_allows_empty_selection_and_population() -> None:
    """Test empty opt-in configuration records no gratuitous scientific values."""
    empty_world = make_state()
    recorder = IndividualGeneticTraitRecorder()

    recorder.observe(empty_world.domain_state, step_index=0)

    assert recorder.required_traits == frozenset()
    assert recorder.latest == IndividualGeneticTraitObservation(step_index=0)

    state_with_organism = make_state()
    organism = add_organism(state_with_organism)
    second_recorder = IndividualGeneticTraitRecorder()
    second_recorder.observe(state_with_organism.domain_state, step_index=0)

    assert second_recorder.latest == IndividualGeneticTraitObservation(
        step_index=0,
        individuals=(
            IndividualGeneticTraitSnapshot(
                organism_id=organism.id,
                trait_values=(),
            ),
        ),
    )


def test_individual_trait_recorder_tracks_committed_active_individual_set() -> None:
    """Test admissions and departures change later committed individual records."""
    trait_name = "performance"
    state = make_state(
        genetic_architecture=make_integer_architecture(trait_name),
    )
    first = add_organism(state, trait_values={trait_name: 1})
    recorder = IndividualGeneticTraitRecorder(trait_names=(trait_name,))
    recorder.observe(state.domain_state, step_index=0)

    second = add_organism(state, trait_values={trait_name: 4}, x=1)
    state.domain_state.remove_organism(first.id)
    recorder.observe(state.domain_state, step_index=1)

    assert tuple(
        individual.organism_id for individual in recorder.observations[0].individuals
    ) == (first.id,)
    assert tuple(
        individual.organism_id for individual in recorder.observations[1].individuals
    ) == (second.id,)
    assert recorder.observations[1].trait_value(second.id, trait_name) == 4


def test_individual_trait_recorder_observation_interval_step_zero_and_clear() -> None:
    """Test observer-owned scheduling, duplicate suppression, and reuse."""
    state = make_state()
    recorder = IndividualGeneticTraitRecorder(
        every_n_steps=2,
        include_step_zero=True,
    )

    assert recorder.should_observe(state.domain_state, step_index=0)
    recorder.observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=0)
    assert not recorder.should_observe(state.domain_state, step_index=1)
    assert recorder.should_observe(state.domain_state, step_index=2)

    without_baseline = IndividualGeneticTraitRecorder(include_step_zero=False)
    assert not without_baseline.should_observe(state.domain_state, step_index=0)
    assert without_baseline.should_observe(state.domain_state, step_index=1)

    recorder.clear()
    assert recorder.observations == ()
    assert recorder.latest is None
    assert recorder.should_observe(state.domain_state, step_index=0)


def test_individual_trait_recorder_rejects_non_increasing_manual_observations() -> None:
    """Test manually recorded history cannot duplicate or move backward."""
    state = make_state()
    recorder = IndividualGeneticTraitRecorder()
    recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=2)

    with pytest.raises(ValueError, match="strictly increasing"):
        recorder.observe(state.domain_state, step_index=1)


@pytest.mark.parametrize(
    "trait_names",
    [
        ("",),
        ("   ",),
        ("a", "a"),
    ],
)
def test_individual_trait_recorder_rejects_invalid_trait_names(
    trait_names: tuple[str, ...],
) -> None:
    """Test configured trait names are nonblank and unique."""
    with pytest.raises(ValueError):
        IndividualGeneticTraitRecorder(trait_names=trait_names)


def test_individual_trait_observation_validates_order_and_trait_width() -> None:
    """Test immutable records preserve deterministic join invariants."""
    first = IndividualGeneticTraitSnapshot(organism_id=1, trait_values=(4,))
    second = IndividualGeneticTraitSnapshot(organism_id=0, trait_values=(1,))

    with pytest.raises(ValueError, match="deterministic increasing order"):
        IndividualGeneticTraitObservation(
            step_index=0,
            trait_names=("speed",),
            individuals=(first, second),
        )

    with pytest.raises(ValueError, match="exactly 2 values"):
        IndividualGeneticTraitObservation(
            step_index=0,
            trait_names=("speed", "intake"),
            individuals=(second,),
        )


def test_max_speed_records_join_spatial_history_by_step_and_organism() -> None:
    """Test B2 focal speed evidence composes with spatial replay records."""
    state = make_state(
        width=5,
        height=5,
        genetic_architecture=make_integer_architecture(MAX_SPEED),
    )
    low = add_organism(
        state,
        trait_values={MAX_SPEED: 1},
        x=0,
        y=0,
    )
    high = add_organism(
        state,
        trait_values={MAX_SPEED: 4},
        x=1,
        y=1,
    )
    spatial = SpatialRecorder()
    traits = IndividualGeneticTraitRecorder(trait_names=(MAX_SPEED,))

    spatial.observe(state.domain_state, step_index=0)
    traits.observe(state.domain_state, step_index=0)
    state.domain_state.move_organism(organism_id=high.id, x=4, y=1)
    spatial.observe(state.domain_state, step_index=1)
    traits.observe(state.domain_state, step_index=1)

    assert tuple(frame.step_index for frame in spatial.observations) == (0, 1)
    assert tuple(frame.step_index for frame in traits.observations) == (0, 1)

    expected_speed = {low.id: 1, high.id: 4}
    for spatial_frame, trait_frame in zip(
        spatial.observations,
        traits.observations,
        strict=True,
    ):
        spatial_ids = tuple(organism.organism_id for organism in spatial_frame.organisms)
        trait_ids = tuple(individual.organism_id for individual in trait_frame.individuals)
        assert spatial_ids == trait_ids
        assert {
            organism_id: trait_frame.trait_value(organism_id, MAX_SPEED)
            for organism_id in trait_ids
        } == expected_speed
