"""Tests for reproduction entity-admission composition."""

from __future__ import annotations

from evo_engine.genetics import ClonalInheritance
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_state


class RecordingAdmission:
    """Record admission and delegate actual entry to biological world state."""

    def __init__(self) -> None:
        self.admitted: list[Organism] = []
        self.states: list[WorldState] = []

    def admit(
        self,
        entity: Organism,
        *,
        state: WorldState,
    ) -> None:
        self.admitted.append(entity)
        self.states.append(state)
        state.add_organism(entity)


def test_reproduction_delegates_offspring_entry_to_admission_model() -> None:
    """Test application composes expenditure with configurable admission."""
    state = make_state()
    parent = add_organism(
        state,
        energy=20,
    )
    admission = RecordingAdmission()
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
        offspring_admission_model=admission,
    )
    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )

    assert len(state.world.organisms) == 1

    process.apply_event(
        state,
        event,
    )

    assert parent.energy == 15
    assert admission.admitted == [event.offspring]
    assert admission.states == [state.world]
    assert state.world.organisms[event.offspring.id] is event.offspring
