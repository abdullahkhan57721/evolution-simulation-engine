"""Tests for durable controlled-experiment scientific semantics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import attrs
import pytest

from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    RunRole,
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


def _provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="e3-locomotion-performance",
        scenario_id="minimal-clonal-locomotion-v1",
        treatment_id="sparse-speed-4",
        treatment_specification_json=canonical_treatment_specification(
            {
                "environment": "sparse",
                "max_speed": 4,
                "mutation_probability_ppm": 0,
            }
        ),
        seed=17,
        horizon_step_index=60,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("max_speed", "resource_acquired"),
        run_role="confirmation",
    )


def test_scientific_provenance_preserves_predeclared_run_identity() -> None:
    """Test one seed is identified as one experiment replicate with its design."""
    provenance = _provenance()

    assert provenance.seed == 17
    assert provenance.observation_include_step_zero is True
    assert provenance.run_role == "confirmation"
    assert provenance.treatment_specification_json == (
        '{"environment":"sparse","max_speed":4,"mutation_probability_ppm":0}'
    )


def test_scientific_provenance_rejects_noncanonical_treatment_json() -> None:
    """Test treatment provenance has one stable serialized representation."""
    with pytest.raises(ValueError, match="canonical sorted compact JSON"):
        attrs.evolve(
            _provenance(),
            treatment_specification_json='{"max_speed": 4}',
        )


def test_scientific_provenance_rejects_duplicate_focal_variables() -> None:
    """Test predeclared focal-variable identity stays unambiguous."""
    with pytest.raises(ValueError, match="must not contain duplicates"):
        attrs.evolve(
            _provenance(),
            focal_variables=("max_speed", "max_speed"),
        )


def test_scientific_provenance_rejects_ambiguous_identity_and_schedule() -> None:
    """Test provenance requires usable focal variables, role, and cadence shape."""
    with pytest.raises(ValueError, match="focal_variables must not be empty"):
        attrs.evolve(_provenance(), focal_variables=())
    with pytest.raises(ValueError, match="run_role must be"):
        attrs.evolve(
            _provenance(),
            run_role=cast(RunRole, "storytelling"),
        )
    with pytest.raises(TypeError, match="observation_include_step_zero"):
        attrs.evolve(
            _provenance(),
            observation_include_step_zero=cast(bool, 1),
        )


def test_scientific_provenance_rejects_invalid_treatment_json_shape() -> None:
    """Test serialized scientific treatment provenance must be a JSON object."""
    with pytest.raises(ValueError, match="valid JSON"):
        attrs.evolve(
            _provenance(),
            treatment_specification_json="not-json",
        )
    with pytest.raises(ValueError, match="JSON object"):
        attrs.evolve(
            _provenance(),
            treatment_specification_json="[]",
        )


def test_fixed_horizon_time_to_event_keeps_right_censoring_explicit() -> None:
    """Test an unobserved outcome is censored rather than assigned a false time."""
    outcome = FixedHorizonTimeToEvent(
        start_step_index=5,
        horizon_step_index=30,
    )

    assert outcome.observed_step_index is None
    assert outcome.right_censored is True
    assert outcome.exposure_steps == 25


def test_fixed_horizon_time_to_event_preserves_late_entry_exposure() -> None:
    """Test observed exposure starts at the declared committed-state entry."""
    outcome = FixedHorizonTimeToEvent(
        start_step_index=8,
        horizon_step_index=30,
        observed_step_index=19,
    )

    assert outcome.right_censored is False
    assert outcome.exposure_steps == 11


def test_fixed_horizon_time_to_event_rejects_observation_beyond_horizon() -> None:
    """Test fixed-horizon comparison cannot record a later observed outcome."""
    with pytest.raises(ValueError, match="must not exceed horizon_step_index"):
        FixedHorizonTimeToEvent(
            start_step_index=8,
            horizon_step_index=30,
            observed_step_index=31,
        )


def test_treatment_specification_validation_stays_small_and_json_only() -> None:
    """Test canonical treatment serialization rejects unsupported inputs."""
    with pytest.raises(TypeError, match="must be a mapping"):
        canonical_treatment_specification(cast(Mapping[str, object], object()))
    with pytest.raises(TypeError, match="keys must be strings"):
        canonical_treatment_specification(
            cast(Mapping[str, object], {1: "invalid-key"})
        )
    with pytest.raises(TypeError, match="JSON-serializable"):
        canonical_treatment_specification({"unsupported": object()})
    with pytest.raises(ValueError, match="finite JSON numeric values"):
        canonical_treatment_specification({"unsupported": float("nan")})


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


def test_treatment_integrity_rejects_empty_declared_difference() -> None:
    """Test a treatment audit cannot hide behind an unnamed manipulation."""
    with pytest.raises(ValueError, match="declared_difference must not be empty"):
        validate_declared_treatment_difference(
            control=_Treatment(focal_value=1, fixed_value=7),
            normalized_treatment=_Treatment(focal_value=1, fixed_value=7),
            declared_difference="   ",
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
