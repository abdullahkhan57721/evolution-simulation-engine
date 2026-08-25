"""Tests for domain-neutral linkage maps."""

from __future__ import annotations

import random

import pytest

from evo_engine.evolution import (
    PiecewiseLinkageMap,
    RecombinationInterval,
    UniformLinkageMap,
    sample_linkage_breakpoint,
)


def test_zero_uniform_linkage_rate_prevents_breakpoint() -> None:
    """Test a fully sticky linkage map produces no breakpoint."""
    result = sample_linkage_breakpoint(
        UniformLinkageMap(relative_rate=0),
        linkage_group="g",
        first_position=0,
        last_position=10,
        rng=random.Random(1),
    )

    assert result is None


def test_piecewise_linkage_map_can_force_a_hotspot() -> None:
    """Test a single nonzero interval receives the only possible breakpoint."""
    linkage_map = PiecewiseLinkageMap(
        default_rate=0,
        intervals=(
            RecombinationInterval(
                linkage_group="g",
                start=5,
                end=6,
                relative_rate=1,
            ),
        ),
    )

    result = sample_linkage_breakpoint(
        linkage_map,
        linkage_group="g",
        first_position=0,
        last_position=10,
        rng=random.Random(1),
    )

    assert result == 5


def test_piecewise_linkage_map_rejects_overlapping_intervals() -> None:
    """Test ambiguous local linkage-rate definitions are rejected."""
    with pytest.raises(ValueError, match="must not overlap"):
        PiecewiseLinkageMap(
            intervals=(
                RecombinationInterval(
                    linkage_group="g",
                    start=0,
                    end=5,
                ),
                RecombinationInterval(
                    linkage_group="g",
                    start=4,
                    end=8,
                ),
            )
        )


def test_piecewise_linkage_intervals_may_overlap_across_groups() -> None:
    """Test coordinate ranges are independent across linkage groups."""
    linkage_map = PiecewiseLinkageMap(
        intervals=(
            RecombinationInterval(
                linkage_group="a",
                start=0,
                end=5,
                relative_rate=0.5,
            ),
            RecombinationInterval(
                linkage_group="b",
                start=0,
                end=5,
                relative_rate=2,
            ),
        )
    )

    assert linkage_map.breakpoint_weight(linkage_group="a", position=2) == 0.5
    assert linkage_map.breakpoint_weight(linkage_group="b", position=2) == 2.0
    assert linkage_map.breakpoint_weight(linkage_group="a", position=8) == 1.0
