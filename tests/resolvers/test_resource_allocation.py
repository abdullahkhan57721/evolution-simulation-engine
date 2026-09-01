"""Tests for resource-allocation resolvers."""

from __future__ import annotations

import pytest

from evo_engine.processes import Aging, ResourceConsumption
from evo_engine.resolvers.resource_allocation import (
    EqualShare,
    ProposalOrder,
    RandomOrder,
    WeightedShare,
)
from tests.helpers import add_organism, make_state


def make_event(
    organism_id: int,
    *,
    x: int = 0,
    y: int = 0,
    amount: int = 10,
) -> ResourceConsumption.Event:
    """Return a resource-consumption proposal."""
    return ResourceConsumption.Event(
        step_index=0,
        organism_id=organism_id,
        x=x,
        y=y,
        amount=amount,
    )


def make_resource_state(
    *,
    available: int,
    organism_count: int = 3,
):
    """Return a state with organisms and local resources."""
    state = make_state(seed=1)
    for _ in range(organism_count):
        add_organism(state)
    state.domain_state.add_resources(
        x=0,
        y=0,
        amount=available,
    )
    return state


def allocations(events) -> list[tuple[int, int]]:
    """Return ``(organism_id, amount)`` pairs from resolved events."""
    return [
        (
            event.organism_id,
            event.amount,
        )
        for event in events
    ]


def test_proposal_order_fully_satisfies_earlier_requests_first() -> None:
    """Test sequential allocation by proposal order."""
    state = make_resource_state(
        available=12,
    )

    resolved = ProposalOrder().resolve_events(
        state,
        [
            make_event(0, amount=10),
            make_event(1, amount=10),
            make_event(2, amount=10),
        ],
    )

    assert allocations(resolved) == [
        (0, 10),
        (1, 2),
    ]


def test_equal_share_redistributes_unused_share() -> None:
    """Test water-filling when one request is smaller than its share."""
    state = make_resource_state(
        available=10,
    )

    resolved = EqualShare().resolve_events(
        state,
        [
            make_event(0, amount=1),
            make_event(1, amount=10),
            make_event(2, amount=10),
        ],
    )

    assert allocations(resolved) == [
        (0, 1),
        (1, 5),
        (2, 4),
    ]


def test_equal_share_integer_remainder_follows_proposal_order() -> None:
    """Test deterministic integer remainder allocation."""
    state = make_resource_state(
        available=2,
    )

    resolved = EqualShare().resolve_events(
        state,
        [
            make_event(0, amount=10),
            make_event(1, amount=10),
            make_event(2, amount=10),
        ],
    )

    assert allocations(resolved) == [
        (0, 1),
        (1, 1),
    ]


def test_allocation_is_independent_between_coordinates() -> None:
    """Test each resource cell forms its own allocation problem."""
    state = make_resource_state(
        available=4,
        organism_count=2,
    )
    state.domain_state.add_resources(
        x=1,
        y=1,
        amount=3,
    )

    resolved = ProposalOrder().resolve_events(
        state,
        [
            make_event(
                0,
                x=0,
                y=0,
                amount=10,
            ),
            make_event(
                1,
                x=1,
                y=1,
                amount=10,
            ),
        ],
    )

    assert allocations(resolved) == [
        (0, 4),
        (1, 3),
    ]


def test_random_order_is_reproducible_from_simulation_rng() -> None:
    """Test seeded random allocation."""
    first_state = make_resource_state(
        available=10,
    )
    second_state = make_resource_state(
        available=10,
    )
    proposals = [
        make_event(0, amount=10),
        make_event(1, amount=10),
        make_event(2, amount=10),
    ]

    first = RandomOrder().resolve_events(
        first_state,
        proposals,
    )
    second = RandomOrder().resolve_events(
        second_state,
        proposals,
    )

    assert first == second


def test_random_order_retains_original_proposal_order_in_output() -> None:
    """Test random priority does not reorder resolved event application."""
    state = make_resource_state(
        available=15,
    )
    proposals = [
        make_event(0, amount=10),
        make_event(1, amount=10),
        make_event(2, amount=10),
    ]

    resolved = RandomOrder().resolve_events(
        state,
        proposals,
    )

    output_ids = [event.organism_id for event in resolved]

    assert output_ids == sorted(output_ids)


def test_weighted_share_allocates_proportionally() -> None:
    """Test proportional integer weighted allocation."""
    state = make_resource_state(
        available=12,
        organism_count=2,
    )

    resolved = WeightedShare(
        weight_function=lambda organism, state: organism.id + 1,
    ).resolve_events(
        state,
        [
            make_event(0, amount=20),
            make_event(1, amount=20),
        ],
    )

    assert allocations(resolved) == [
        (0, 4),
        (1, 8),
    ]


def test_weighted_share_redistributes_after_request_cap() -> None:
    """Test resources left by a capped request are redistributed."""
    state = make_resource_state(
        available=10,
        organism_count=2,
    )

    resolved = WeightedShare(
        weight_function=lambda organism, state: 1,
    ).resolve_events(
        state,
        [
            make_event(0, amount=2),
            make_event(1, amount=20),
        ],
    )

    assert allocations(resolved) == [
        (0, 2),
        (1, 8),
    ]


def test_weighted_share_zero_weights_receive_nothing() -> None:
    """Test zero weight excludes a request from weighted allocation."""
    state = make_resource_state(
        available=5,
        organism_count=2,
    )

    resolved = WeightedShare(
        weight_function=lambda organism, state: organism.id,
    ).resolve_events(
        state,
        [
            make_event(0, amount=5),
            make_event(1, amount=5),
        ],
    )

    assert allocations(resolved) == [
        (1, 5),
    ]


@pytest.mark.parametrize(
    "weight",
    [
        -1,
        1.5,
        True,
    ],
)
def test_weighted_share_rejects_invalid_weights(weight: object) -> None:
    """Test allocation-weight contract."""
    state = make_resource_state(
        available=5,
        organism_count=1,
    )

    resolver = WeightedShare(
        weight_function=lambda organism, state: weight,  # type: ignore[arg-type]
    )

    with pytest.raises((TypeError, ValueError)):
        resolver.resolve_events(
            state,
            [
                make_event(0, amount=5),
            ],
        )


def test_resource_resolvers_reject_non_consumption_events() -> None:
    """Test resource-allocation resolver domain."""
    state = make_resource_state(
        available=5,
        organism_count=1,
    )

    with pytest.raises(TypeError):
        EqualShare().resolve_events(
            state,
            [
                Aging.Event(
                    step_index=0,
                    organism_id=0,
                )
            ],
        )


def test_weighted_share_can_declare_custom_weight_trait_dependencies() -> None:
    """Test opaque resource-weight callbacks participate in preflight checks."""
    from evo_engine.genetics import MAX_INTAKE_RATE

    resolver = WeightedShare(
        weight_function=lambda organism, state: 1,
        required_traits=frozenset({MAX_INTAKE_RATE}),
    )

    assert resolver.required_traits == frozenset({MAX_INTAKE_RATE})
