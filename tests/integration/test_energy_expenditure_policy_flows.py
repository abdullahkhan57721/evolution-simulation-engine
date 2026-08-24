"""Integration tests for energy-expenditure policy flows."""

from __future__ import annotations

from evo_engine.energetics import KeepFixedReserve, LinearGrowthCost
from evo_engine.genetics import ClonalInheritance
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import Growth, Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def _reserve_growth(*, minimum_energy: int) -> Growth:
    return Growth(
        growth_model=FixedGrowthRate(
            amount_per_timestep=3,
        ),
        growth_cost_model=LinearGrowthCost(
            energy_per_body_mass_unit=1,
        ),
        energy_expenditure_policy=KeepFixedReserve(
            minimum_energy=minimum_energy,
        ),
    )


def _reserve_reproduction(*, minimum_energy: int) -> Reproduction:
    return Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        energy_expenditure_policy=KeepFixedReserve(
            minimum_energy=minimum_energy,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )


def test_growth_reserve_policy_blocks_then_allows_exact_reserve() -> None:
    """Test Growth respects the configured post-expenditure reserve."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=6,
    )
    process = _reserve_growth(minimum_energy=4)

    assert process.propose_events(state) == []

    organism.energy = 7
    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert organism.body_mass == 13
    assert organism.energy == 4


def test_growth_application_rechecks_fixed_reserve() -> None:
    """Test stale Growth events cannot violate a fixed energy reserve."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=7,
    )
    process = _reserve_growth(minimum_energy=4)
    event = process.propose_events(state)[0]
    organism.energy = 6

    try:
        process.apply_event(state, event)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected stale Growth event to violate reserve policy.")

    assert organism.body_mass == 10
    assert organism.energy == 6


def test_reproduction_reserve_policy_blocks_then_allows_exact_reserve() -> None:
    """Test Reproduction preserves each parent's configured energy reserve."""
    state = make_state()
    parent = add_organism(state, energy=10)
    process = _reserve_reproduction(minimum_energy=6)

    assert process.propose_events(state) == []

    parent.energy = 11
    proposal = process.propose_events(state)[0]
    event = process.materialize_event(state, proposal)
    process.apply_event(state, event)

    assert parent.energy == 6
    assert state.world.organisms[1].energy == 5


def test_reproduction_materialization_rechecks_reserve_before_rng() -> None:
    """Test stale reserve violations are rejected before offspring RNG work."""
    state = make_state(seed=23)
    parent = add_organism(state, energy=10)
    process = _reserve_reproduction(minimum_energy=5)
    proposal = process.propose_events(state)[0]
    rng_state = state.rng.getstate()
    parent.energy = 9

    try:
        process.materialize_event(state, proposal)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected stale Reproduction proposal to violate reserve.")

    assert state.rng.getstate() == rng_state
    assert len(state.world.organisms) == 1


def test_reproduction_application_rechecks_reserve_atomically() -> None:
    """Test a materialized birth cannot later violate the parent's reserve."""
    state = make_state()
    parent = add_organism(state, energy=10)
    process = _reserve_reproduction(minimum_energy=5)
    proposal = process.propose_events(state)[0]
    event = process.materialize_event(state, proposal)
    parent.energy = 9

    try:
        process.apply_event(state, event)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected materialized birth to violate reserve policy.")

    assert parent.energy == 9
    assert len(state.world.organisms) == 1


def test_growth_collects_expenditure_policy_trait_requirements() -> None:
    """Test Growth exposes nested expenditure-policy trait requirements."""

    class TraitDrivenReserve:
        @property
        def required_traits(self) -> frozenset[str]:
            return frozenset({"energy_reserve"})

        def can_spend(
            self,
            organism,
            *,
            energy_cost,
            simulation_state,
        ) -> bool:
            return True

    process = Growth(
        growth_model=FixedGrowthRate(amount_per_timestep=1),
        growth_cost_model=LinearGrowthCost(energy_per_body_mass_unit=1),
        energy_expenditure_policy=TraitDrivenReserve(),
    )

    assert process.required_traits == frozenset(
        {
            ADULT_BODY_MASS,
            "energy_reserve",
        }
    )


def test_reproduction_collects_expenditure_policy_trait_requirements() -> None:
    """Test Reproduction exposes nested expenditure-policy trait requirements."""

    class TraitDrivenReserve:
        @property
        def required_traits(self) -> frozenset[str]:
            return frozenset({"reproductive_reserve"})

        def can_spend(
            self,
            organism,
            *,
            energy_cost,
            simulation_state,
        ) -> bool:
            return True

    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        energy_expenditure_policy=TraitDrivenReserve(),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )

    assert process.required_traits == frozenset({"reproductive_reserve"})
