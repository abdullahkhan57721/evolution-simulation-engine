"""Tests for reproductive participants versus genetic contributors."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import ClonalInheritance
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    PairwiseMating,
)
from evo_engine.spatial.neighborhoods import Moore
from evo_engine.world.organism import Organism
from tests.helpers import add_organism, make_integer_architecture, make_state


class FirstParticipantContributes:
    """Select only the first resolved participant as genetic parent."""

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return the first participant only."""
        return (participants[0],)


class RecordingRandomContributorSelection:
    """Record materialization-time use of the simulation RNG."""

    def __init__(self) -> None:
        self.calls = 0
        self.received_simulation_rng = False

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Choose one participant using the provided RNG."""
        self.calls += 1
        self.received_simulation_rng = rng is simulation_state.rng
        return (rng.choice(participants),)


class FixedContributorSelection:
    """Return a configured contributor tuple for validation tests."""

    def __init__(self, contributors: tuple[Organism, ...]) -> None:
        self.contributors = contributors

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return the configured contributor tuple."""
        return self.contributors


class SecondParticipantLocation:
    """Place offspring at the second production source participant."""

    def choose_location(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return the second participant's location, proving both sources arrive."""
        return parents[1].x, parents[1].y


def _pair_process(*, contributor_selection) -> Reproduction:
    return Reproduction(
        eligibility=AlwaysEligible(),
        reproductive_group_selection=PairwiseMating(neighborhood=Moore(radius=10)),
        inheritance_model=ClonalInheritance(),
        genetic_contributor_selection=contributor_selection,
        parental_investment=FixedEnergyInvestment(amount=2),
        offspring_placement=SecondParticipantLocation(),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )


def test_two_participants_can_have_one_genetic_parent() -> None:
    """Test participation no longer implies genetic contribution."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture, seed=0)
    first = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=20,
        x=1,
        y=1,
    )
    second = add_organism(
        state,
        trait_values={"offspring_energy": 8},
        energy=20,
        x=4,
        y=4,
    )
    process = _pair_process(contributor_selection=FirstParticipantContributes())

    proposal = process.propose_events(state)[0]
    event = process.materialize_event(state, proposal)

    assert proposal.participant_ids == (first.id, second.id)
    assert event.participant_ids == (first.id, second.id)
    assert event.parent_ids == (first.id,)
    assert event.genetic_contributor_ids == (first.id,)
    assert event.offspring_genome == first.genome
    # Production/placement still receives all participants in this milestone.
    assert (event.x, event.y) == (second.x, second.y)

    process.apply_event(state, event)

    assert first.energy == 18
    assert second.energy == 18


def test_contributor_selection_is_deferred_until_materialization() -> None:
    """Test unresolved candidates do not invoke stochastic contributor choice."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture, seed=7)
    add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    selection = RecordingRandomContributorSelection()
    process = _pair_process(contributor_selection=selection)

    proposal = process.propose_events(state)[0]

    assert selection.calls == 0

    process.materialize_event(state, proposal)

    assert selection.calls == 1
    assert selection.received_simulation_rng


@pytest.mark.parametrize("mode", ["empty", "duplicate", "outsider"])
def test_contributor_selection_rejects_invalid_results(mode: str) -> None:
    """Test contributors must be nonempty unique resolved participants."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    first = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    second = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    outsider = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)

    if mode == "empty":
        contributors: tuple[Organism, ...] = ()
    elif mode == "duplicate":
        contributors = (first, first)
    else:
        contributors = (outsider,)

    process = _pair_process(
        contributor_selection=FixedContributorSelection(contributors)
    )
    proposal = next(
        proposal
        for proposal in process.propose_events(state)
        if proposal.participant_ids == (first.id, second.id)
    )

    with pytest.raises(ValueError):
        process.materialize_event(state, proposal)
