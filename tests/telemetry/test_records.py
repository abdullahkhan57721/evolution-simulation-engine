"""Tests for immutable event telemetry records."""

from __future__ import annotations

import attrs

from evo_engine.telemetry import (
    AppliedEvent,
    EnvironmentalValueChanged,
    OrganismAdded,
    OrganismRemoved,
    ResourcesChanged,
    StepTelemetry,
)


@attrs.frozen(slots=True, kw_only=True)
class ExampleEvent:
    """Minimal materialized event for telemetry tests."""

    step_index: int
    amount: int


def test_applied_event_exposes_process_names_and_entity_effects() -> None:
    """Test event metadata and structural entity effects are queryable."""
    event = ExampleEvent(step_index=2, amount=4)
    applied = AppliedEvent(
        event_step_index=2,
        stage_index=3,
        process_type="example.module.ExampleProcess",
        event_type="example.module.ExampleEvent",
        event=event,
        world_mutations=(
            OrganismAdded(organism_id=8),
            OrganismRemoved(organism_id=3),
        ),
    )

    assert applied.process_name == "ExampleProcess"
    assert applied.event_name == "ExampleEvent"
    assert applied.added_organism_ids == (8,)
    assert applied.removed_organism_ids == (3,)
    assert applied.event is event


def test_resources_changed_reports_signed_delta() -> None:
    """Test resource telemetry retains before/after values and signed change."""
    assert ResourcesChanged(x=1, y=2, before=7, after=3).delta == -4
    assert ResourcesChanged(x=1, y=2, before=3, after=8).delta == 5


def test_environmental_value_changed_reports_signed_delta() -> None:
    """Test environmental telemetry retains field identity and signed change."""
    mutation = EnvironmentalValueChanged(
        field_name="temperature",
        x=1,
        y=2,
        before=20.0,
        after=17.5,
    )

    assert mutation.field_name == "temperature"
    assert mutation.delta == -2.5


def test_step_telemetry_filters_events_by_process_name() -> None:
    """Test process filtering accepts qualified and unqualified names."""
    first = AppliedEvent(
        event_step_index=0,
        stage_index=0,
        process_type="pkg.Growth",
        event_type="pkg.Growth.Event",
        event=ExampleEvent(step_index=0, amount=1),
    )
    second = AppliedEvent(
        event_step_index=0,
        stage_index=1,
        process_type="pkg.Movement",
        event_type="pkg.Movement.Event",
        event=ExampleEvent(step_index=0, amount=2),
    )
    telemetry = StepTelemetry(
        completed_step_index=1,
        events=(first, second),
    )

    assert telemetry.events_for_process("Growth") == (first,)
    assert telemetry.events_for_process("pkg.Movement") == (second,)
