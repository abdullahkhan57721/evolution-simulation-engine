"""Tests for behavioral-purpose vocabulary and declarations."""

from __future__ import annotations

import pytest

from evo_engine.behavior import (
    BUILTIN_BEHAVIORAL_PURPOSES,
    ENERGY_ACQUISITION,
    EXPLORATION,
    REPRODUCTION,
    SOMATIC_INVESTMENT,
    SURVIVAL,
    BehavioralPurposeProvider,
    validate_behavioral_purpose,
)
from evo_engine.processes import (
    Growth,
    Movement,
    Predation,
    Reproduction,
    ResourceConsumption,
)


def test_builtin_behavioral_purposes_define_shared_vocabulary() -> None:
    """Test the built-in vocabulary contains each canonical purpose once."""
    assert BUILTIN_BEHAVIORAL_PURPOSES == frozenset(
        {
            ENERGY_ACQUISITION,
            EXPLORATION,
            REPRODUCTION,
            SOMATIC_INVESTMENT,
            SURVIVAL,
        }
    )


def test_custom_behavioral_purpose_is_allowed() -> None:
    """Test simulations may define purposes outside the built-in vocabulary."""
    assert validate_behavioral_purpose("thermoregulation") == "thermoregulation"


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        1,
        1.0,
    ],
)
def test_behavioral_purpose_rejects_non_strings(value: object) -> None:
    """Test behavioral-purpose names must be strings."""
    with pytest.raises(TypeError):
        validate_behavioral_purpose(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "\t",
    ],
)
def test_behavioral_purpose_rejects_blank_strings(value: str) -> None:
    """Test behavioral-purpose names must contain non-whitespace characters."""
    with pytest.raises(ValueError):
        validate_behavioral_purpose(value)


def test_provider_protocol_accepts_class_attribute_declaration() -> None:
    """Test a static class attribute satisfies the behavioral capability."""

    class StaticPurpose:
        behavioral_purpose = ENERGY_ACQUISITION

    assert isinstance(StaticPurpose(), BehavioralPurposeProvider)


def test_provider_protocol_accepts_dynamic_property() -> None:
    """Test future components may calculate behavioral purpose dynamically."""

    class DynamicPurpose:
        @property
        def behavioral_purpose(self) -> str:
            return SURVIVAL

    assert isinstance(DynamicPurpose(), BehavioralPurposeProvider)


def test_fixed_purpose_processes_declare_behavioral_purpose() -> None:
    """Test processes with intrinsic purposes expose canonical declarations."""
    assert Growth.behavioral_purpose == SOMATIC_INVESTMENT
    assert Reproduction.behavioral_purpose == REPRODUCTION
    assert ResourceConsumption.behavioral_purpose == ENERGY_ACQUISITION
    assert Predation.behavioral_purpose == ENERGY_ACQUISITION


def test_movement_has_no_generic_behavioral_purpose() -> None:
    """Test Movement remains open to action-specific intent instead of one purpose."""
    assert not hasattr(Movement, "behavioral_purpose")
