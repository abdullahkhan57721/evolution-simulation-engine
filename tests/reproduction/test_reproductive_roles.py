"""Tests for contextual reproductive roles and directed mating systems."""

from __future__ import annotations

import pytest

from evo_engine.genetics import CHOOSINESS, MATING_SIGNAL
from evo_engine.reproduction import (
    ChooserSignalCompatibility,
    ChooserSignalMarginPreference,
    DirectedPairwiseMating,
    MatingTypeCompatibilityMatrix,
    MatingTypeRoles,
)
from evo_engine.spatial.neighborhoods import Moore
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_mating_type_roles_support_multiple_roles_per_type() -> None:
    """Test reproductive roles are contextual capabilities, not identities."""
    state = make_state()
    organism = add_organism(state, mating_type="hermaphrodite")
    roles = MatingTypeRoles(
        roles_by_mating_type=(("hermaphrodite", ("chooser", "signaler")),)
    )

    assert roles.roles_for(organism, state) == frozenset({"chooser", "signaler"})


def test_mating_type_roles_use_explicit_default_for_unlisted_type() -> None:
    """Test unlisted mating types do not inherit a configured role accidentally."""
    state = make_state()
    organism = add_organism(state, mating_type="unlisted")
    roles = MatingTypeRoles(
        roles_by_mating_type=(("type_a", ("chooser",)),),
        default_roles=("generalist",),
    )

    assert roles.roles_for(organism, state) == frozenset({"generalist"})


def test_mating_type_compatibility_matrix_is_unordered() -> None:
    """Test compatibility is symmetric while allowing arbitrary type networks."""
    state = make_state()
    first = add_organism(state, mating_type="a")
    second = add_organism(state, mating_type="c")
    matrix = MatingTypeCompatibilityMatrix(
        compatible_pairs=(("c", "a"), ("b", "b")),
    )

    assert matrix(first, second, state)
    assert matrix(second, first, state)


def test_mating_type_compatibility_matrix_rejects_duplicate_unordered_pair() -> None:
    """Test reversed duplicate compatibility entries are rejected."""
    with pytest.raises(ValueError, match="duplicate"):
        MatingTypeCompatibilityMatrix(
            compatible_pairs=(("a", "b"), ("b", "a")),
        )


def test_directed_pairwise_mating_preserves_configured_role_order() -> None:
    """Test parent tuple order follows explicit reproductive roles."""
    architecture = make_integer_architecture(CHOOSINESS, MATING_SIGNAL)
    state = make_state(width=5, height=5, genetic_architecture=architecture)
    chooser = add_organism(
        state,
        mating_type="type_a",
        trait_values={CHOOSINESS: 5, MATING_SIGNAL: 1},
        x=1,
        y=1,
    )
    weak = add_organism(
        state,
        mating_type="type_b",
        trait_values={CHOOSINESS: 0, MATING_SIGNAL: 6},
        x=1,
        y=1,
    )
    strong = add_organism(
        state,
        mating_type="type_b",
        trait_values={CHOOSINESS: 0, MATING_SIGNAL: 9},
        x=1,
        y=1,
    )
    role_model = MatingTypeRoles(
        roles_by_mating_type=(
            ("type_a", ("chooser",)),
            ("type_b", ("signaler",)),
        )
    )
    selection = DirectedPairwiseMating(
        first_role="chooser",
        second_role="signaler",
        role_model=role_model,
        neighborhood=Moore(radius=0),
        can_mate=ChooserSignalCompatibility(
            chooser_threshold_trait=CHOOSINESS,
            signal_trait=MATING_SIGNAL,
        ),
        preference_function=ChooserSignalMarginPreference(
            chooser_threshold_trait=CHOOSINESS,
            signal_trait=MATING_SIGNAL,
        ),
    )

    groups = selection.propose_parent_groups(
        tuple(state.world.organisms.values()),
        simulation_state=state,
    )

    assert [group.parent_ids for group in groups] == [
        (chooser.id, weak.id),
        (chooser.id, strong.id),
    ]
    assert [group.preference_score for group in groups] == [1, 4]
    assert selection.required_traits == frozenset({CHOOSINESS, MATING_SIGNAL})


def test_directed_pairwise_mating_skips_self_for_multi_role_organism() -> None:
    """Test a multi-role organism cannot occupy both positions in one mating."""
    state = make_state()
    first = add_organism(state, mating_type="h")
    second = add_organism(state, mating_type="h")
    roles = MatingTypeRoles(
        roles_by_mating_type=(("h", ("chooser", "signaler")),),
    )
    selection = DirectedPairwiseMating(
        first_role="chooser",
        second_role="signaler",
        role_model=roles,
        neighborhood=Moore(radius=0),
    )

    groups = selection.propose_parent_groups(
        tuple(state.world.organisms.values()),
        simulation_state=state,
    )

    assert {group.parent_ids for group in groups} == {
        (first.id, second.id),
        (second.id, first.id),
    }
