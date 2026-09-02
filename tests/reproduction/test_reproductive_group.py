"""Tests for shared reproductive-group invariants."""

from __future__ import annotations

import pytest

from evo_engine.reproduction import ReproductiveGroup


def test_reproductive_group_accepts_three_or_more_unique_participants() -> None:
    """Test shared groups do not impose one/two-participant arity."""
    group = ReproductiveGroup(participant_ids=(1, 2, 3, 4))

    assert group.participant_ids == (1, 2, 3, 4)


def test_reproductive_group_rejects_empty_membership() -> None:
    """Test every reproductive group is nonempty."""
    with pytest.raises(ValueError, match="at least one"):
        ReproductiveGroup(participant_ids=())


def test_reproductive_group_rejects_duplicate_participant_ids() -> None:
    """Test one organism cannot occupy duplicate entries in a group."""
    with pytest.raises(ValueError, match="duplicate"):
        ReproductiveGroup(participant_ids=(1, 2, 1))
