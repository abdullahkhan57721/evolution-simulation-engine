"""Tests for domain-neutral greedy preference-order resolution."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from evo_engine.resolvers._preference_order import (
    resolve_capacity_preference_order,
    resolve_exclusive_preference_order,
)


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


def resolve_jobs_with_capacity(
    proposals: list[JobProposal],
    *,
    max_events_per_key: int,
) -> list[JobProposal]:
    """Resolve jobs through the generic capacity-aware preference algorithm."""
    return resolve_capacity_preference_order(
        proposals,
        event_type=JobProposal,
        preference_score=lambda proposal: proposal.preference_score,
        participant_keys=lambda proposal: proposal.conflict_keys,
        max_events_per_key=max_events_per_key,
        resolver_name="CapacityJobResolver",
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


def test_capacity_preference_order_allows_repeated_resource_use_up_to_capacity() -> None:
    """Test a named resource may participate in multiple accepted events."""
    first = JobProposal(
        step_index=0,
        preference_score=5,
        conflict_keys=("machine:lathe", "operator:alex"),
    )
    second = JobProposal(
        step_index=0,
        preference_score=4,
        conflict_keys=("machine:lathe", "operator:bea"),
    )
    third = JobProposal(
        step_index=0,
        preference_score=3,
        conflict_keys=("machine:lathe", "operator:chen"),
    )

    assert resolve_jobs_with_capacity(
        [third, second, first],
        max_events_per_key=2,
    ) == [first, second]


def test_capacity_preference_order_enforces_capacity_for_every_key() -> None:
    """Test any exhausted resource key rejects an otherwise available event."""
    first = JobProposal(
        step_index=0,
        preference_score=5,
        conflict_keys=("machine:lathe", "operator:alex"),
    )
    second = JobProposal(
        step_index=0,
        preference_score=4,
        conflict_keys=("machine:mill", "operator:alex"),
    )
    independent = JobProposal(
        step_index=0,
        preference_score=3,
        conflict_keys=("machine:mill", "operator:bea"),
    )

    assert resolve_jobs_with_capacity(
        [first, second, independent],
        max_events_per_key=1,
    ) == [first, independent]


def test_capacity_preference_order_validates_capacity() -> None:
    """Test capacity must be a positive non-Boolean integer."""
    proposal = JobProposal(
        step_index=0,
        preference_score=1,
        conflict_keys=("machine:lathe",),
    )

    with pytest.raises(TypeError, match="integer"):
        resolve_jobs_with_capacity([proposal], max_events_per_key=True)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="at least 1"):
        resolve_jobs_with_capacity([proposal], max_events_per_key=0)


def test_capacity_preference_order_rejects_duplicate_conflict_keys() -> None:
    """Test capacity does not make duplicate keys within one event meaningful."""
    duplicate = JobProposal(
        step_index=0,
        preference_score=1,
        conflict_keys=("machine:lathe", "machine:lathe"),
    )

    with pytest.raises(ValueError, match="duplicate conflict keys"):
        resolve_jobs_with_capacity([duplicate], max_events_per_key=2)
