"""Tests for locomotion measurements derived from committed event evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from evo_engine.experiments.b3_flagship import run_b3_flagship
from evo_engine.experiments.export import write_locomotion_measurements_json
from evo_engine.experiments.locomotion import (
    measure_applied_movement,
    summarize_locomotion_replicate,
)
from evo_engine.experiments.science import (
    ScientificRunProvenance,
    canonical_treatment_specification,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    build_b3_flagship_specification,
)
from evo_engine.processes import Movement
from evo_engine.telemetry import AppliedEvent
from evo_engine.world import OrganismMoved


def _provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="e2-locomotion-mechanics",
        scenario_id="minimal-clonal-locomotion-v1",
        treatment_id="speed-4",
        treatment_specification_json=canonical_treatment_specification(
            {"max_speed": 4, "locomotion_cost_exponent": 2}
        ),
        seed=17,
        horizon_step_index=20,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("max_speed", "realized_distance"),
        run_role="confirmation",
    )


def _movement_event(
    *,
    step_index: int = 3,
    organism_id: int = 5,
    dx: int = 3,
    dy: int = 4,
    new_x: int = 7,
    new_y: int = 9,
    energy_cost: int = 25,
    effects: tuple[object, ...] | None = None,
) -> AppliedEvent:
    event = Movement.Event(
        step_index=step_index,
        organism_id=organism_id,
        dx=dx,
        dy=dy,
        new_x=new_x,
        new_y=new_y,
        energy_cost=energy_cost,
    )
    resolved_effects = (
        (
            OrganismMoved(
                organism_id=organism_id,
                from_x=4,
                from_y=5,
                to_x=new_x,
                to_y=new_y,
            ),
        )
        if effects is None
        else effects
    )
    return AppliedEvent(
        event_step_index=step_index,
        stage_index=0,
        process_type="evo_engine.processes.movement.Movement",
        event_type="evo_engine.processes.movement.Movement.Event",
        event=event,
        effects=resolved_effects,
    )


def test_applied_movement_separates_attempted_and_realized_displacement() -> None:
    """Test actual displacement is derived from the committed move effect."""
    measurement = measure_applied_movement(_movement_event())

    assert measurement.event_step_index == 3
    assert measurement.completed_step_index == 4
    assert measurement.attempted_distance == 5.0
    assert measurement.realized_distance == 5.0
    assert measurement.locomotion_energy_expenditure == 25


def test_applied_movement_no_coordinate_effect_has_zero_realized_distance() -> None:
    """Test an applied no-op endpoint is not mistaken for attempted travel."""
    measurement = measure_applied_movement(_movement_event(effects=()))

    assert measurement.attempted_distance == 5.0
    assert measurement.realized_distance == 0.0
    assert measurement.locomotion_energy_expenditure == 25


def test_applied_movement_rejects_inconsistent_committed_endpoint() -> None:
    """Test contradictory movement event/effect evidence fails loudly."""
    effect = OrganismMoved(
        organism_id=5,
        from_x=4,
        from_y=5,
        to_x=6,
        to_y=9,
    )

    with pytest.raises(ValueError, match="endpoint must match"):
        measure_applied_movement(_movement_event(effects=(effect,)))


def test_applied_movement_rejects_malformed_event_evidence() -> None:
    """Test movement measurement rejects wrong type, timing, and effect identity."""
    with pytest.raises(TypeError, match="must be an AppliedEvent"):
        measure_applied_movement(cast(AppliedEvent, object()))

    nonmovement = AppliedEvent(
        event_step_index=0,
        stage_index=0,
        process_type="tests.Process",
        event_type="tests.Event",
        event=object(),
    )
    with pytest.raises(TypeError, match="must contain a Movement.Event"):
        measure_applied_movement(nonmovement)

    movement = _movement_event()
    mismatched_step = AppliedEvent(
        event_step_index=2,
        stage_index=movement.stage_index,
        process_type=movement.process_type,
        event_type=movement.event_type,
        event=movement.event,
        effects=movement.effects,
    )
    with pytest.raises(ValueError, match="step_index must match"):
        measure_applied_movement(mismatched_step)

    mismatched_identity = OrganismMoved(
        organism_id=99,
        from_x=4,
        from_y=5,
        to_x=7,
        to_y=9,
    )
    with pytest.raises(ValueError, match="organism IDs must match"):
        measure_applied_movement(_movement_event(effects=(mismatched_identity,)))

    move_effect = cast(OrganismMoved, movement.effects[0])
    with pytest.raises(ValueError, match="multiple move effects"):
        measure_applied_movement(
            _movement_event(effects=(move_effect, move_effect)),
        )


def test_locomotion_summary_uses_applied_movement_as_explicit_denominator() -> None:
    """Test replicate means use the committed applied-movement denominator."""
    first = _movement_event()
    second = _movement_event(
        step_index=4,
        dx=1,
        dy=0,
        new_x=5,
        new_y=5,
        energy_cost=1,
        effects=(),
    )

    result = summarize_locomotion_replicate(
        provenance=_provenance(),
        events=(first, second),
    )

    assert result.applied_movement_count == 2
    assert result.total_attempted_distance == 6.0
    assert result.total_realized_distance == 5.0
    assert result.mean_realized_distance_per_applied_movement == 2.5
    assert result.total_locomotion_energy_expenditure == 26
    assert result.mean_locomotion_energy_expenditure_per_applied_movement == 13.0


def test_locomotion_summary_keeps_empty_denominator_undefined() -> None:
    """Test no applied movements produces None rather than false zero means."""
    result = summarize_locomotion_replicate(
        provenance=_provenance(),
        events=(),
    )

    assert result.applied_movement_count == 0
    assert result.total_attempted_distance == 0.0
    assert result.total_realized_distance == 0.0
    assert result.mean_realized_distance_per_applied_movement is None
    assert result.mean_locomotion_energy_expenditure_per_applied_movement is None


def test_b3_seed_5_movement_matches_committed_flagship_evidence() -> None:
    """Test E1 measurement reproduces the frozen B3 representative movement."""
    evidence = run_b3_flagship(
        build_b3_flagship_specification(seed=5, environment="compact_patch")
    )
    applied_event = next(
        event
        for event in evidence.events
        if isinstance(event.event, Movement.Event)
        and event.event.organism_id == 1
        and event.completed_step_index == 5
    )

    measurement = measure_applied_movement(applied_event)

    assert measurement.completed_step_index == 5
    assert measurement.organism_id == 1
    assert measurement.realized_distance == 4.0
    assert measurement.locomotion_energy_expenditure == 2


def test_locomotion_export_preserves_scientific_provenance(tmp_path: Path) -> None:
    """Test durable JSON keeps treatment identity and explicit measurement names."""
    result = summarize_locomotion_replicate(
        provenance=_provenance(),
        events=(_movement_event(),),
    )

    destination = write_locomotion_measurements_json(
        result,
        tmp_path / "locomotion.json",
    )
    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["provenance"]["experiment_id"] == "e2-locomotion-mechanics"
    assert payload["provenance"]["treatment_id"] == "speed-4"
    assert payload["provenance"]["seed"] == 17
    assert payload["provenance"]["horizon_step_index"] == 20
    assert payload["provenance"]["observation_every_n_steps"] == 1
    assert payload["provenance"]["observation_include_step_zero"] is True
    assert payload["provenance"]["run_role"] == "confirmation"
    assert payload["mean_realized_distance_per_applied_movement"] == 5.0
    assert (
        payload["mean_locomotion_energy_expenditure_per_applied_movement"]
        == 25.0
    )
