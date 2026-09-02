"""Tests for shared reproductive parent-group invariants."""

from __future__ import annotations

import pytest

from evo_engine.reproduction import ParentGroup


def test_parent_group_accepts_three_or_more_unique_parents() -> None:
    """Test shared parent groups do not impose one/two-parent arity."""
    group = ParentGroup(parent_ids=(1, 2, 3, 4))

    assert group.parent_ids == (1, 2, 3, 4)


def test_parent_group_rejects_empty_membership() -> None:
    """Test every reproductive parent group is nonempty."""
    with pytest.raises(ValueError, match="at least one"):
        ParentGroup(parent_ids=())


def test_parent_group_rejects_duplicate_parent_ids() -> None:
    """Test one organism cannot occupy duplicate entries in a parent group."""
    with pytest.raises(ValueError, match="duplicate"):
        ParentGroup(parent_ids=(1, 2, 1))
