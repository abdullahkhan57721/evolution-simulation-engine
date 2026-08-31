"""Tests for immutable biological world mutation records."""

from __future__ import annotations

from evo_engine.world import EnvironmentalValueChanged, ResourcesChanged


def test_resources_changed_reports_signed_delta() -> None:
    """Test resource mutations retain before/after values and signed change."""
    assert ResourcesChanged(x=1, y=2, before=7, after=3).delta == -4
    assert ResourcesChanged(x=1, y=2, before=3, after=8).delta == 5


def test_environmental_value_changed_reports_signed_delta() -> None:
    """Test environmental mutations retain field identity and signed change."""
    mutation = EnvironmentalValueChanged(
        field_name="temperature",
        x=1,
        y=2,
        before=20.0,
        after=17.5,
    )

    assert mutation.field_name == "temperature"
    assert mutation.delta == -2.5
