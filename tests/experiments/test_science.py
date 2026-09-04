"""Tests for durable controlled-experiment scientific semantics."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    ScientificRunProvenance,
    canonical_treatment_specification,
    validate_declared_treatment_difference,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    build_b3_flagship_specification,
)


@attrs.frozen(slots=True, kw_only=True)
class _Treatment:
    focal_value: int
    fixed_value: int


def test_scientific_provenance_preserves_predeclared_run_identity() -> None:
    """Test one seed is identified as one experiment replicate with its design."""
    treatment_json = canonical_treatment_specification(
        {
            "environment": "sparse",
            "max_speed": 4,
            "mutation_probability_ppm": 0,
        }
    )

    provenance = ScientificRunProvenance(
        experiment_id="e3-locomotion-performance",
        scenario_id="minimal-clonal-locomotion-v1",
        treatment_id="sparse-speed-4",
        treatment_specification_json=treatment_json,
        seed=17,
        horizon_step_index=60,
        observation_every_n_steps=1,
        focal_variables=("max_speed", "resource_acquired"),
        run_role="confirmation",
    )

    assert provenance.seed == 17
    assert provenance.run_role == "confirmation"
    assert provenance.treatment_specification_json == (
        '{"environment":"sparse","max_speed":4,"mutation_probability_ppm":0}'
    )


def test_scientific_provenance_rejects_noncanonical_treatment_json() -> None:
    """Test treatment provenance has one stable serialized representation."""
    with pytest.raises(ValueError, match="canonical sorted compact JSON"):
        ScientificRunProvenance(
            experiment_id="experiment",
            scenario_id="scenario",
            treatment_id="treatment",
            treatment_specification_json='{"max_speed": 4}',
            seed=1,
            horizon_step_index=10,
            observation_every_n_steps=1,
            focal_variables=("max_speed",),
        )


def test_scientific_provenance_rejects_duplicate_focal_variables() -> None:
    """Test predeclared focal-variable identity stays unambiguous."""
    with pytest.raises(ValueError, match="must not contain duplicates"):
        ScientificRunProvenance(
            experiment_id="experiment",
            scenario_id="scenario",
            treatment_id="treatment",
            treatment_specification_json=canonical_treatment_specification(
                {"max_speed": 4}
            ),
            seed=1,
            horizon_step_index=10,
            observation_every_n_steps=1,
            focal_variables=("max_speed", "max_speed"),
        )


def test_fixed_horizon_time_to_event_keeps_right_censoring_explicit() -> None:
    """Test an unobserved event is censored rather than assigned a false time."""
    outcome = FixedHorizonTimeToEvent(
        start_step_index=5,
        horizon_step_index=30,
    )

    assert outcome.event_step_index is None
    assert outcome.right_censored is True
    assert outcome.exposure_steps == 25


def test_fixed_horizon_time_to_event_preserves_late_entry_exposure() -> None:
    """Test observed exposure starts at the declared entry state."""
    outcome = FixedHorizonTimeToEvent(
        start_step_index=8,
        horizon_step_index=30,
        event_step_index=19,
    )

    assert outcome.right_censored is False
    assert outcome.exposure_steps == 11


def test_treatment_integrity_accepts_only_the_declared_normalized_difference() -> None:
    """Test a concrete experiment may normalize its one intended manipulation."""
    control = _Treatment(focal_value=1, fixed_value=7)
    treatment = _Treatment(focal_value=4, fixed_value=7)
    normalized = attrs.evolve(treatment, focal_value=control.focal_value)

    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=normalized,
        declared_difference="max_speed",
    )


def test_treatment_integrity_rejects_an_unintended_second_difference() -> None:
    """Test hidden non-treatment differences fail loudly after normalization."""
    control = _Treatment(focal_value=1, fixed_value=7)
    treatment = _Treatment(focal_value=4, fixed_value=9)
    normalized = attrs.evolve(treatment, focal_value=control.focal_value)

    with pytest.raises(ValueError, match="outside max_speed"):
        validate_declared_treatment_difference(
            control=control,
            normalized_treatment=normalized,
            declared_difference="max_speed",
        )


def test_treatment_integrity_helper_supports_real_b3_normalization() -> None:
    """Test the thin helper preserves B3's one-declared-difference pattern."""
    control = build_b3_flagship_specification(seed=5, environment="uniform")
    treatment = build_b3_flagship_specification(
        seed=5,
        environment="compact_patch",
    )
    normalized = attrs.evolve(
        treatment,
        environment="uniform",
        config=attrs.evolve(
            treatment.config,
            resource_placement_model=control.config.resource_placement_model,
        ),
    )

    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=normalized,
        declared_difference="resource placement",
    )

    invalid_treatment = attrs.evolve(
        treatment,
        config=attrs.evolve(
            treatment.config,
            resource_request_amount=treatment.config.resource_request_amount + 1,
        ),
    )
    invalid_normalized = attrs.evolve(
        invalid_treatment,
        environment="uniform",
        config=attrs.evolve(
            invalid_treatment.config,
            resource_placement_model=control.config.resource_placement_model,
        ),
    )

    with pytest.raises(ValueError, match="outside resource placement"):
        validate_declared_treatment_difference(
            control=control,
            normalized_treatment=invalid_normalized,
            declared_difference="resource placement",
        )
