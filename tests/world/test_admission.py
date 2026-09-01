"""Tests for biological world admission adapters."""

from __future__ import annotations

from evo_engine.world import WorldOrganismAdmission
from tests.helpers import make_organism, make_state


def test_world_organism_admission_delegates_world_entry_mechanics() -> None:
    """Test world admission assigns identity and population membership."""
    state = make_state()
    organism = make_organism(x=2, y=3)

    WorldOrganismAdmission().admit(
        organism,
        state=state.domain_state,
    )

    assert organism.id == 0
    assert state.domain_state.organisms == {0: organism}
    assert state.domain_state.effect_count == 1
