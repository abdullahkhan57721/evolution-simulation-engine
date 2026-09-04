"""Tests for immutable event telemetry records."""

from __future__ import annotations

from typing import cast

import attrs
import pytest

from evo_engine.telemetry import AppliedEvent, StepTelemetry


@attrs.frozen(slots=True, kw_only=True)
class ExampleEvent:
    """Minimal materialized event for telemetry tests."""

    step_index: int
    amount: int


@attrs.frozen(slots=True, kw_only=True)
class ExampleEffect:
    """Nonbiological domain effect for telemetry tests."""

    resource: str
    before: int
    after: int


def test_applied_event_exposes_metadata_and_opaque_domain_effects() -> None:
    """Test committed telemetry preserves arbitrary domain effect objects."""
    event = ExampleEvent(step_index=2, amount=4)
    effect = ExampleEffect(resource="machine:lathe", before=0, after=1)
    applied = AppliedEvent(
        event_step_index=2,
        stage_index=3,
        process_type="example.module.ExampleProcess",
        event_type="example.module.ExampleEvent",
        event=event,
        effects=(effect,),
    )

    assert applied.process_name == "ExampleProcess"
    assert applied.event_name == "ExampleEvent"
    assert applied.event is event
    assert applied.effects == (effect,)
    assert applied.completed_step_index == 3


def test_applied_event_public_constructor_still_validates_metadata() -> None:
    """Test trusted kernel construction does not weaken the public constructor."""
    with pytest.raises(ValueError, match="process_type must not be empty"):
        AppliedEvent(
            event_step_index=0,
            stage_index=0,
            process_type="   ",
            event_type="example.module.ExampleEvent",
            event=ExampleEvent(step_index=0, amount=1),
        )


def test_applied_event_kernel_construction_matches_validated_record() -> None:
    """Test kernel construction preserves the immutable telemetry representation."""
    event = ExampleEvent(step_index=2, amount=4)
    effect = ExampleEffect(resource="machine:lathe", before=0, after=1)
    validated = AppliedEvent(
        event_step_index=2,
        stage_index=3,
        process_type="example.module.ExampleProcess",
        event_type="example.module.ExampleEvent",
        event=event,
        effects=(effect,),
    )
    kernel_built = AppliedEvent._from_kernel_values(
        event_step_index=2,
        stage_index=3,
        process_type="example.module.ExampleProcess",
        event_type="example.module.ExampleEvent",
        event=event,
        effects=(effect,),
    )

    assert kernel_built == validated


def test_applied_event_kernel_construction_validates_event_step_index() -> None:
    """Test process-carried event indexes retain runtime validation."""
    with pytest.raises(ValueError, match="AppliedEvent.event_step_index"):
        AppliedEvent._from_kernel_values(
            event_step_index=-1,
            stage_index=0,
            process_type="example.module.ExampleProcess",
            event_type="example.module.ExampleEvent",
            event=ExampleEvent(step_index=0, amount=1),
            effects=(),
        )


def test_step_telemetry_filters_events_by_process_name() -> None:
    """Test process filtering accepts qualified and unqualified names."""
    first = AppliedEvent(
        event_step_index=0,
        stage_index=0,
        process_type="pkg.Dispatch",
        event_type="pkg.Dispatch.Event",
        event=ExampleEvent(step_index=0, amount=1),
    )
    second = AppliedEvent(
        event_step_index=0,
        stage_index=1,
        process_type="pkg.Archive",
        event_type="pkg.Archive.Event",
        event=ExampleEvent(step_index=0, amount=2),
    )
    telemetry = StepTelemetry(
        completed_step_index=1,
        events=(first, second),
    )

    assert telemetry.events_for_process("Dispatch") == (first,)
    assert telemetry.events_for_process("pkg.Archive") == (second,)


def test_step_telemetry_public_constructor_still_validates_events() -> None:
    """Test trusted kernel construction does not weaken public event validation."""
    invalid_events = cast(tuple[AppliedEvent, ...], (object(),))

    with pytest.raises(TypeError, match=r"events\[0\] must be an AppliedEvent"):
        StepTelemetry(
            completed_step_index=1,
            events=invalid_events,
        )


def test_step_telemetry_rejects_misaligned_event_step() -> None:
    """Test an event must correspond to the telemetry envelope's committed state."""
    applied = AppliedEvent(
        event_step_index=0,
        stage_index=0,
        process_type="pkg.Dispatch",
        event_type="pkg.Dispatch.Event",
        event=ExampleEvent(step_index=0, amount=1),
    )

    with pytest.raises(ValueError, match="does not align"):
        StepTelemetry(
            completed_step_index=2,
            events=(applied,),
        )


def test_step_telemetry_kernel_construction_matches_validated_record() -> None:
    """Test kernel construction preserves the immutable step telemetry record."""
    applied = AppliedEvent(
        event_step_index=2,
        stage_index=3,
        process_type="example.module.ExampleProcess",
        event_type="example.module.ExampleEvent",
        event=ExampleEvent(step_index=2, amount=4),
    )
    validated = StepTelemetry(
        completed_step_index=3,
        events=(applied,),
    )
    kernel_built = StepTelemetry._from_kernel_values(
        completed_step_index=3,
        events=(applied,),
    )

    assert kernel_built == validated


def test_step_telemetry_kernel_construction_validates_completed_index() -> None:
    """Test kernel construction retains runtime validation of the step index."""
    with pytest.raises(ValueError, match="StepTelemetry.completed_step_index"):
        StepTelemetry._from_kernel_values(
            completed_step_index=0,
            events=(),
        )


def test_step_telemetry_kernel_construction_rejects_misaligned_event_step() -> None:
    """Test trusted construction enforces event-to-committed-state alignment."""
    applied = AppliedEvent(
        event_step_index=0,
        stage_index=0,
        process_type="pkg.Dispatch",
        event_type="pkg.Dispatch.Event",
        event=ExampleEvent(step_index=0, amount=1),
    )

    with pytest.raises(ValueError, match="does not align"):
        StepTelemetry._from_kernel_values(
            completed_step_index=2,
            events=(applied,),
        )
