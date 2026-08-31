"""Tests for domain-neutral exclusive preference-order resolution."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from evo_engine.resolvers._preference_order import resolve_exclusive_preference_order


@dataclass(frozen=True, slots=True)
class JobProposal:
    """Represent a nonbiological job competing for named resources."""

    step_index: int
    preference_score: int
    conflict_keys: tuple[str, ...]


def resolve_jobs(proposals: list[JobProposal]) -> list[JobProposal]:
    """Resolve jobs through the generic exclusive preference algorithm."""
    return resolve_exclusive_preference_order(
        proposals,
        event_type=JobProposal,
        preference_score=lambda proposal: proposal.preference_score,
        participant_keys=lambda proposal: proposal.conflict_keys,
        resolver_name="JobResolver",
    )


def test_exclusive_preference_order_accepts_noninteger_conflict_keys() -> None:
    """Test string resource keys participate in generic conflict resolution."""
    low = JobProposal(
        step_index=0,
        preference_score=1,
        conflict_keys=("machine:lathe", "operator:alex"),
    )
    high = JobProposal(
        step_index=0,
        preference_score=5,
        conflict_keys=("machine:lathe", "operator:bea"),
    )
    disjoint = JobProposal(
        step_index=0,
        preference_score=3,
        conflict_keys=("machine:mill", "operator:chen"),
    )

    assert resolve_jobs([low, high, disjoint]) == [high, disjoint]


def test_exclusive_preference_order_rejects_duplicate_conflict_keys() -> None:
    """Test one proposal may not claim the same conflict key twice."""
    duplicate = JobProposal(
        step_index=0,
        preference_score=1,
        conflict_keys=("machine:lathe", "machine:lathe"),
    )

    with pytest.raises(ValueError, match="duplicate conflict keys"):
        resolve_jobs([duplicate])
