"""Tests for reproductive investors and offspring-production sources."""

from __future__ import annotations

import random

import pytest

from evo_engine.engine.simulation_state import SimulationState
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


class FirstParticipantInvests:
    """Select only the first reproductive participant as energy investor."""

    def __init__(self) -> None:
        self.calls = 0

    def select_investors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return the first participant without consuming reproduction RNG."""
        self.calls += 1
        return (participants[0],)


class SecondParticipantContributes:
    """Select only the second participant as genetic contributor."""

    def select_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return the second participant only."""
        return (participants[1],)


class RecordingFirstProductionSource:
    """Select the first participant and record materialization-time context."""

    def __init__(self) -> None:
        self.calls = 0
        self.received_simulation_rng = False
        self.genetic_contributor_ids: tuple[int, ...] = ()

    def select_sources(
        self,
        participants: tuple[Organism, ...],
        *,
        genetic_contributors: tuple[Organism, ...],
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return the first participant as production context."""
        self.calls += 1
        self.received_simulation_rng = rng is simulation_state.rng
        self.genetic_contributor_ids = tuple(
            contributor.id for contributor in genetic_contributors
        )
        return (participants[0],)


class FixedInvestorSelection:
    """Return a configured investor tuple for validation tests."""

    def __init__(self, investors: tuple[Organism, ...]) -> None:
        self.investors = investors

    def select_investors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return the configured investor tuple."""
        return self.investors


class FixedProductionSourceSelection:
    """Return configured production sources for validation tests."""

    def __init__(self, sources: tuple[Organism, ...]) -> None:
        self.sources = sources

    def select_sources(
        self,
        participants: tuple[Organism, ...],
        *,
        genetic_contributors: tuple[Organism, ...],
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[Organism, ...]:
        """Return the configured production-source tuple."""
        return self.sources


class FirstSourceLocation:
    """Place offspring at the only configured production source."""

    def choose_location(
        self,
        source_entities: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return the single source entity's location."""
        if len(source_entities) != 1:
            raise ValueError("FirstSourceLocation requires exactly one source entity.")
        return source_entities[0].x, source_entities[0].y


class SourceIndependentLocation:
    """Place offspring without requiring any biological production source."""

    def choose_location(
        self,
        source_entities: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return a fixed location regardless of production sources."""
        return 0, 0


def _pair_process(
    *,
    investor_selection: object,
    production_source_selection: object,
    offspring_placement: object | None = None,
) -> Reproduction:
    return Reproduction(
        eligibility=AlwaysEligible(),
        reproductive_group_selection=PairwiseMating(neighborhood=Moore(radius=10)),
        inheritance_model=ClonalInheritance(),
        genetic_contributor_selection=SecondParticipantContributes(),
        reproductive_investor_selection=investor_selection,
        reproductive_energy_investment=FixedEnergyInvestment(amount=3),
        offspring_production_source_selection=production_source_selection,
        offspring_placement=(
            FirstSourceLocation() if offspring_placement is None else offspring_placement
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )


def test_participant_investor_parent_and_production_source_are_independent() -> None:
    """Test one reproductive episode can use four distinct biological roles."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture, seed=9)
    first = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=20,
        x=1,
        y=2,
    )
    second = add_organism(
        state,
        trait_values={"offspring_energy": 9},
        energy=20,
        x=6,
        y=7,
    )
    investors = FirstParticipantInvests()
    production_sources = RecordingFirstProductionSource()
    process = _pair_process(
        investor_selection=investors,
        production_source_selection=production_sources,
    )

    proposal = process.propose_events(state)[0]

    assert proposal.participant_ids == (first.id, second.id)
    assert proposal.investor_ids == (first.id,)
    assert proposal.investor_energy_contributions == ((first.id, 3),)
    assert investors.calls == 1
    assert production_sources.calls == 0

    event = process.materialize_event(state, proposal)

    assert investors.calls == 1
    assert production_sources.calls == 1
    assert production_sources.received_simulation_rng
    assert production_sources.genetic_contributor_ids == (second.id,)
    assert event.participant_ids == (first.id, second.id)
    assert event.investor_ids == (first.id,)
    assert event.parent_ids == (second.id,)
    assert event.production_source_ids == (first.id,)
    assert event.offspring_genome == second.genome
    assert (event.x, event.y) == (first.x, first.y)

    process.apply_event(state, event)

    assert first.energy == 17
    assert second.energy == 20


@pytest.mark.parametrize("mode", ["empty", "duplicate", "outsider"])
def test_investor_selection_rejects_invalid_results(mode: str) -> None:
    """Test investors must be a nonempty unique participant subset."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    first = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    second = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    outsider = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)

    if mode == "empty":
        selected: tuple[Organism, ...] = ()
    elif mode == "duplicate":
        selected = (first, first)
    else:
        selected = (outsider,)

    process = _pair_process(
        investor_selection=FixedInvestorSelection(selected),
        production_source_selection=RecordingFirstProductionSource(),
    )

    with pytest.raises(ValueError):
        process.propose_events(state)


@pytest.mark.parametrize("mode", ["duplicate", "outsider"])
def test_production_source_selection_rejects_invalid_results(mode: str) -> None:
    """Test production sources must be unique resolved participants."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    first = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    second = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    outsider = add_organism(state, trait_values={"offspring_energy": 5}, energy=20)

    sources = (first, first) if mode == "duplicate" else (outsider,)
    process = _pair_process(
        investor_selection=FirstParticipantInvests(),
        production_source_selection=FixedProductionSourceSelection(sources),
    )
    proposal = next(
        proposal
        for proposal in process.propose_events(state)
        if proposal.participant_ids == (first.id, second.id)
    )

    with pytest.raises(ValueError):
        process.materialize_event(state, proposal)


def test_empty_production_source_selection_supports_source_independent_production() -> None:
    """Test the shared production-source boundary permits zero source entities."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    add_organism(state, trait_values={"offspring_energy": 5}, energy=20)
    add_organism(state, trait_values={"offspring_energy": 8}, energy=20)
    process = _pair_process(
        investor_selection=FirstParticipantInvests(),
        production_source_selection=FixedProductionSourceSelection(()),
        offspring_placement=SourceIndependentLocation(),
    )

    event = process.materialize_event(state, process.propose_events(state)[0])

    assert event.production_source_ids == ()
    assert (event.x, event.y) == (0, 0)
