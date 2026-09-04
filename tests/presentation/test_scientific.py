"""Tests for renderer-neutral continuous scientific encoding."""

import pytest

from evo_engine.presentation import ContinuousTraitEncoding


def test_continuous_trait_encoding_normalizes_shared_scale() -> None:
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=5,
    )

    assert encoding.normalize(1) == 0.0
    assert encoding.normalize(3) == 0.5
    assert encoding.normalize(5) == 1.0


@pytest.mark.parametrize("value", (0, 6))
def test_continuous_trait_encoding_rejects_values_outside_scale(value: int) -> None:
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=5,
    )

    with pytest.raises(ValueError, match="must lie within"):
        encoding.normalize(value)


def test_continuous_trait_encoding_requires_increasing_bounds() -> None:
    with pytest.raises(ValueError, match="greater than"):
        ContinuousTraitEncoding(
            trait_name="max_speed",
            label="Maximum speed",
            lower_bound=4,
            upper_bound=4,
        )
