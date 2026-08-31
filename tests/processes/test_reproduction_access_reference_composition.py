"""Tests for reproduction-wide entity access and reference composition."""

from __future__ import annotations

from evo_engine.genetics import ClonalInheritance
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    PairwiseMating,
    SingleParent,
)
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_integer_architecture, make_state


class OffsetOrganismAccess:
    """Expose selected organisms and resolve deliberately non-ID references."""

    def __init__(self, *entities: Organism, offset: int = 100) -> None:
        self._entities = tuple(entities)
        self.offset = offset
        self.references: list[int] = []

    def get(self, reference: int, *, state: WorldState) -> Organism:
        self.references.append(reference)
        return state.organisms[reference - self.offset]

    def entities(self, *, state: WorldState) -> tuple[Organism, ...]:
        del state
        return self._entities


class OffsetOrganismReference:
    """Derive non-ID integer references while recording delegation."""

    def __init__(self, *, offset: int = 100) -> None:
        self.offset = offset
        self.entities: list[Organism] = []

    def reference(self, entity: Organism, *, state: WorldState) -> int:
        self.entities.append(entity)
        assert state.organisms[entity.id] is entity
        return entity.id + self.offset


def test_reproduction_uses_same_reference_policy_across_all_phases() -> None:
    """Test proposal, materialization, and application share entity references."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    excluded = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=10,
    )
    selected = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=10,
    )
    access = OffsetOrganismAccess(selected)
    reference = OffsetOrganismReference()
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
        access_model=access,
        reference_model=reference,
    )

    proposal = process.propose_events(state)[0]
    event = process.materialize_event(state, proposal)
    process.apply_event(state, event)

    expected_reference = selected.id + 100
    assert proposal.parent_energy_contributions == ((expected_reference, 5),)
    assert reference.entities == [selected, selected]
    assert access.references == [
        expected_reference,
        expected_reference,
        expected_reference,
    ]
    assert excluded.energy == 10
    assert selected.energy == 5
    assert len(state.world.organisms) == 3


def test_pairwise_mating_derives_group_ids_through_reference_policy() -> None:
    """Test sexual parent groups do not manufacture references from ``.id``."""
    state = make_state()
    first = add_organism(state, x=0, y=0)
    second = add_organism(state, x=0, y=0)
    reference = OffsetOrganismReference(offset=50)

    groups = PairwiseMating(
        neighborhood=SameCell(),
    ).propose_parent_groups(
        (first, second),
        simulation_state=state,
        reference_model=reference,
    )

    assert groups[0].parent_ids == (first.id + 50, second.id + 50)
    assert reference.entities == [first, second]
