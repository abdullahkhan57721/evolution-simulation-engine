"""Tests for pedigree and lifetime-fitness observation."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.observation import PedigreeRecorder
from evo_engine.telemetry import AppliedEvent, StepTelemetry
from evo_engine.world import OrganismAdded, OrganismRemoved
from tests.helpers import add_organism, make_state


class _StepIndexedEvent(Protocol):
    @property
    def step_index(self) -> int:
        """Return the event's simulation step index."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class BirthEvent:
    """Minimal structural parentage event for recorder tests."""

    step_index: int
    parent_ids: tuple[int, ...]


@attrs.frozen(slots=True, kw_only=True)
class ParticipantBirthEvent:
    """Minimal birth exposing participation separately from genetic parentage."""

    step_index: int
    participant_ids: tuple[int, ...]
    parent_ids: tuple[int, ...]


@attrs.frozen(slots=True, kw_only=True)
class DeathEvent:
    """Minimal structural mortality event for recorder tests."""

    step_index: int
    deceased_organism_ids: tuple[int, ...]


@attrs.frozen(slots=True, kw_only=True)
class RemovalEvent:
    """Represent non-mortality removal from the active world."""

    step_index: int


def _applied_event(
    event: _StepIndexedEvent,
    *,
    process_type: str,
    effects: tuple[object, ...],
) -> AppliedEvent:
    return AppliedEvent(
        event_step_index=event.step_index,
        stage_index=0,
        process_type=process_type,
        event_type=f"tests.{type(event).__name__}",
        event=event,
        effects=effects,
    )


def test_pedigree_recorder_tracks_birth_parentage_death_and_fitness() -> None:
    """Test one offspring links to both parents and closes fitness at death."""
    state = make_state()
    parent_a = add_organism(state, age=2)
    parent_b = add_organism(state, age=3)
    recorder = PedigreeRecorder()
    recorder.observe(state.domain_state, step_index=0)
    child_id = max(parent_a.id, parent_b.id) + 100

    recorder.observe_telemetry(
        StepTelemetry(
            completed_step_index=1,
            events=(
                _applied_event(
                    BirthEvent(
                        step_index=0,
                        parent_ids=(parent_a.id, parent_b.id),
                    ),
                    process_type="evo_engine.processes.reproduction.Reproduction",
                    effects=(OrganismAdded(organism_id=child_id),),
                ),
            ),
        )
    )

    child = recorder.record(child_id)
    assert child.parent_ids == (parent_a.id, parent_b.id)
    assert child.birth_step == 1
    assert child.is_alive
    assert child.lifetime_reproductive_success is None
    assert recorder.offspring_of(parent_a.id) == (child_id,)
    assert recorder.offspring_of(parent_b.id) == (child_id,)
    assert recorder.record(parent_a.id).realized_reproductive_success == 1

    recorder.observe_telemetry(
        StepTelemetry(
            completed_step_index=2,
            events=(
                _applied_event(
                    DeathEvent(
                        step_index=1,
                        deceased_organism_ids=(child_id,),
                    ),
                    process_type="evo_engine.processes.starvation.Starvation",
                    effects=(OrganismRemoved(organism_id=child_id),),
                ),
            ),
        )
    )

    dead_child = recorder.record(child_id)
    assert not dead_child.is_alive
    assert dead_child.death_step == 2
    assert dead_child.death_cause == "Starvation"
    assert dead_child.lifespan_steps == 1
    assert dead_child.lifetime_reproductive_success == 0


def test_pedigree_credits_genetic_parents_not_all_reproductive_participants() -> None:
    """Test participation alone does not create genetic ancestry or fitness credit."""
    state = make_state()
    genetic_parent = add_organism(state)
    noncontributing_participant = add_organism(state)
    recorder = PedigreeRecorder()
    recorder.observe(state.domain_state, step_index=0)
    child_id = 100

    recorder.observe_telemetry(
        StepTelemetry(
            completed_step_index=1,
            events=(
                _applied_event(
                    ParticipantBirthEvent(
                        step_index=0,
                        participant_ids=(
                            genetic_parent.id,
                            noncontributing_participant.id,
                        ),
                        parent_ids=(genetic_parent.id,),
                    ),
                    process_type="evo_engine.processes.reproduction.Reproduction",
                    effects=(OrganismAdded(organism_id=child_id),),
                ),
            ),
        )
    )

    assert recorder.record(child_id).parent_ids == (genetic_parent.id,)
    assert recorder.offspring_of(genetic_parent.id) == (child_id,)
    assert recorder.offspring_of(noncontributing_participant.id) == ()
    assert recorder.record(genetic_parent.id).realized_reproductive_success == 1
    assert (
        recorder.record(noncontributing_participant.id).realized_reproductive_success
        == 0
    )


def test_non_mortality_removal_does_not_become_a_death() -> None:
    """Test active-world removal is not automatically interpreted as mortality."""
    state = make_state()
    organism = add_organism(state)
    recorder = PedigreeRecorder()
    recorder.observe(state.domain_state, step_index=0)

    recorder.observe_telemetry(
        StepTelemetry(
            completed_step_index=1,
            events=(
                _applied_event(
                    RemovalEvent(step_index=0),
                    process_type="tests.Migration",
                    effects=(OrganismRemoved(organism_id=organism.id),),
                ),
            ),
        )
    )

    record = recorder.record(organism.id)
    assert record.is_alive
    assert record.death_step is None
    assert record.lifetime_reproductive_success is None
