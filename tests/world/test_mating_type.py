"""Tests for organism mating-type state."""

from __future__ import annotations

import copy

import pytest
from attrs.exceptions import FrozenAttributeError

from tests.helpers import make_organism


def test_organism_mating_type_is_immutable() -> None:
    """Test reproductive mating type cannot change during an organism's life."""
    organism = make_organism(mating_type="alpha")

    with pytest.raises(FrozenAttributeError):
        organism.mating_type = "beta"


def test_organism_rejects_empty_mating_type() -> None:
    """Test mating-type labels must contain non-whitespace text."""
    with pytest.raises(ValueError, match="mating_type"):
        make_organism(mating_type="   ")


def test_deepcopy_preserves_mating_type() -> None:
    """Test transactional copies retain immutable reproductive identity."""
    organism = make_organism(mating_type="gamma")

    copied = copy.deepcopy(organism)

    assert copied.mating_type == "gamma"
