"""Tests for reproduction-domain policies."""

from __future__ import annotations

import random

import pytest

from evo_engine.reproduction import (
    AlwaysEligible,
    FixedEnergyInvestment,
    GeneticPhenotypeEnergyInvestment,
    MinimumEnergyEligibility,
    PairwiseMating,
    ParentGroup,
    RandomParentLocation,
    SingleParent,
)
from evo_engine.spatial.neighborhoods import SameCell
from tests.helpers import (
    add_organism,
    make_integer_architecture,
    make_state,
)


@pytest.mark.parametrize(
    ("energy", "minimum", "expected"),
    [
        (9, 10, False),
        (10, 10, True),
        (11, 10, True),
    ],
)
def test_minimum_energy_eligibility(
    energy: int,
    minimum: int,
    expected: bool,
) -> None:
    """Test minimum-energy reproductive eligibility."""
    state = make_state()
    organism = add_organism(
        state,
        energy=energy,
    )

    assert (
        MinimumEnergyEligibility(
            minimum_energy=minimum,
        ).is_eligible(
            organism,
            simulation_state=state,
        )
        is expected
    )


def test_always_eligible_returns_true() -> None:
    """Test the unconditional eligibility policy."""
    state = make_state()
    organism = add_organism(state)

    assert AlwaysEligible().is_eligible(
        organism,
        simulation_state=state,
    )


@pytest.mark.parametrize(
    "parent_ids",
    [
        (),
        (1, 2, 3),
        (1, 1),
    ],
)
def test_parent_group_rejects_invalid_parent_membership(
    parent_ids: tuple[int, ...],
) -> None:
    """Test one- or two-parent group invariants."""
    with pytest.raises(ValueError):
        ParentGroup(
            parent_ids=parent_ids,
        )


def test_single_parent_proposes_one_group_per_parent() -> None:
    """Test one-parent candidate formation."""
    state = make_state()
    first = add_organism(state)
    second = add_organism(state)

    groups = SingleParent().propose_parent_groups(
        (
            first,
            second,
        ),
        simulation_state=state,
    )

    assert [group.parent_ids for group in groups] == [
        (first.id,),
        (second.id,),
    ]


def test_pairwise_mating_proposes_each_unique_pair_once() -> None:
    """Test unique unordered mating-pair enumeration."""
    state = make_state()
    parents = tuple(
        add_organism(
            state,
            x=0,
            y=0,
        )
        for _ in range(3)
    )

    groups = PairwiseMating(
        neighborhood=SameCell(),
    ).propose_parent_groups(
        parents,
        simulation_state=state,
    )

    assert [group.parent_ids for group in groups] == [
        (0, 1),
        (0, 2),
        (1, 2),
    ]


def test_pairwise_mating_filters_by_neighborhood() -> None:
    """Test spatial mating eligibility."""
    state = make_state()
    first = add_organism(
        state,
        x=0,
        y=0,
    )
    second = add_organism(
        state,
        x=1,
        y=0,
    )

    groups = PairwiseMating(
        neighborhood=SameCell(),
    ).propose_parent_groups(
        (
            first,
            second,
        ),
        simulation_state=state,
    )

    assert groups == []


def test_pairwise_mating_filters_by_biological_compatibility() -> None:
    """Test custom pair compatibility."""
    state = make_state()
    parents = (
        add_organism(state),
        add_organism(state),
    )

    groups = PairwiseMating(
        neighborhood=SameCell(),
        can_mate=lambda first, second, state: False,
    ).propose_parent_groups(
        parents,
        simulation_state=state,
    )

    assert groups == []


def test_pairwise_mating_records_preference_score() -> None:
    """Test resolver-facing mating preference."""
    state = make_state()
    parents = (
        add_organism(state),
        add_organism(state),
    )

    groups = PairwiseMating(
        neighborhood=SameCell(),
        preference_function=lambda first, second, state: 7,
    ).propose_parent_groups(
        parents,
        simulation_state=state,
    )

    assert groups[0].preference_score == 7


@pytest.mark.parametrize(
    ("function_name", "value"),
    [
        ("can_mate", 1),
        ("preference", True),
    ],
)
def test_pairwise_mating_requires_exact_callback_return_types(
    function_name: str,
    value: object,
) -> None:
    """Test strict pair-policy callback contracts."""
    state = make_state()
    parents = (
        add_organism(state),
        add_organism(state),
    )

    if function_name == "can_mate":
        policy = PairwiseMating(
            neighborhood=SameCell(),
            can_mate=lambda first, second, state: value,  # type: ignore[arg-type]
        )
    else:
        policy = PairwiseMating(
            neighborhood=SameCell(),
            preference_function=(lambda first, second, state: value),  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError):
        policy.propose_parent_groups(
            parents,
            simulation_state=state,
        )


def test_fixed_energy_investment_returns_one_value_per_parent() -> None:
    """Test fixed parental investment alignment."""
    state = make_state()
    parents = (
        add_organism(state),
        add_organism(state),
    )

    assert FixedEnergyInvestment(
        amount=6,
    ).determine_investments(
        parents,
        simulation_state=state,
    ) == (6, 6)


def test_phenotype_energy_investment_reads_each_parent_trait() -> None:
    """Test genetically expressible parental investment."""
    architecture = make_integer_architecture(
        "offspring_energy",
    )
    state = make_state(
        genetic_architecture=architecture,
    )
    first = add_organism(
        state,
        trait_values={"offspring_energy": 8},
    )
    second = add_organism(
        state,
        trait_values={"offspring_energy": 12},
    )

    assert GeneticPhenotypeEnergyInvestment().determine_investments(
        (
            first,
            second,
        ),
        simulation_state=state,
    ) == (8, 12)


def test_random_parent_location_one_parent_is_deterministic() -> None:
    """Test one-parent offspring placement."""
    state = make_state()
    parent = add_organism(
        state,
        x=3,
        y=4,
    )

    assert RandomParentLocation().choose_location(
        (parent,),
        simulation_state=state,
        rng=random.Random(1),
    ) == (3, 4)


def test_random_parent_location_two_parents_uses_parent_coordinate() -> None:
    """Test two-parent placement never invents a third coordinate."""
    state = make_state()
    first = add_organism(
        state,
        x=1,
        y=1,
    )
    second = add_organism(
        state,
        x=4,
        y=4,
    )

    result = RandomParentLocation().choose_location(
        (
            first,
            second,
        ),
        simulation_state=state,
        rng=random.Random(1),
    )

    assert result in {
        (1, 1),
        (4, 4),
    }


def test_adult_body_mass_at_birth_uses_offspring_target_trait() -> None:
    """Test default developmental policy preserves fixed-size behavior."""
    from evo_engine.reproduction import AdultBodyMassAtBirth
    from tests.helpers import developmental_profile

    state = make_state()

    assert (
        AdultBodyMassAtBirth().determine_body_mass(
            developmental_profile(adult_body_mass=9),
            (),
            simulation_state=state,
        )
        == 9
    )


def test_fixed_body_mass_at_birth_requires_no_phenotype_trait() -> None:
    """Test developmental policy can decouple birth mass from genetics."""
    from evo_engine.reproduction import FixedBodyMassAtBirth
    from tests.helpers import developmental_profile

    policy = FixedBodyMassAtBirth(
        body_mass=2,
    )

    assert (
        policy.determine_body_mass(
            developmental_profile(),
            (),
            simulation_state=make_state(),
        )
        == 2
    )
    assert not hasattr(policy, "required_traits")


def test_pairwise_mating_exposes_explicit_custom_callback_dependencies() -> None:
    """Test opaque mating callbacks can declare genetic phenotype traits they read."""
    from evo_engine.genetics import CHOOSINESS, MATING_SIGNAL

    policy = PairwiseMating(
        neighborhood=SameCell(),
        required_traits=frozenset(
            {
                CHOOSINESS,
                MATING_SIGNAL,
            }
        ),
    )

    assert policy.required_traits == frozenset(
        {
            CHOOSINESS,
            MATING_SIGNAL,
        }
    )


def test_fraction_of_adult_body_mass_at_birth_uses_developmental_target() -> None:
    """Test birth mass can scale from realized rather than genetic adult mass."""
    from evo_engine.reproduction import FractionOfAdultBodyMassAtBirth
    from tests.helpers import developmental_profile

    policy = FractionOfAdultBodyMassAtBirth(
        numerator=1,
        denominator=4,
        minimum_body_mass=2,
    )

    assert (
        policy.determine_body_mass(
            developmental_profile(adult_body_mass=20),
            (),
            simulation_state=make_state(),
        )
        == 5
    )

    assert (
        policy.determine_body_mass(
            developmental_profile(adult_body_mass=3),
            (),
            simulation_state=make_state(),
        )
        == 2
    )
