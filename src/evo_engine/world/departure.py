"""World-specific entity departure adapters."""

from __future__ import annotations

import attrs

from evo_engine.departure import EntityDepartureModel
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class WorldOrganismDeparture:
    """Remove an organism from ``WorldState`` through the generic contract."""

    def depart(
        self,
        reference: int,
        *,
        state: WorldState,
    ) -> Organism:
        """Remove and return the referenced organism from world state.

        Args:
            reference: Permanent world organism ID.
            state: Biological world state containing the organism.

        Returns:
            Organism removed from the world.
        """
        return state.remove_organism(reference)


def _satisfies_generic_contract(
    model: EntityDepartureModel[int, WorldState, Organism],
) -> EntityDepartureModel[int, WorldState, Organism]:
    """Return model unchanged while statically checking the adapter contract."""
    return model


_WORLD_ORGANISM_DEPARTURE_CONTRACT = _satisfies_generic_contract(
    WorldOrganismDeparture()
)
