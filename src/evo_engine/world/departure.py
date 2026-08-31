"""World-specific entity departure adapters."""

from __future__ import annotations

import attrs

from evo_engine.departure import EntityDepartureModel
from evo_engine.world.carcass import Carcass
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


@attrs.frozen(slots=True, kw_only=True)
class WorldCarcassDeparture:
    """Remove a carcass from ``WorldState`` through the generic contract."""

    def depart(
        self,
        reference: int,
        *,
        state: WorldState,
    ) -> Carcass:
        """Remove and return the referenced carcass from world state.

        Args:
            reference: Permanent world carcass ID.
            state: Biological world state containing the carcass.

        Returns:
            Carcass removed from the world.
        """
        return state.remove_carcass(reference)


def _satisfies_organism_contract(
    model: EntityDepartureModel[int, WorldState, Organism],
) -> EntityDepartureModel[int, WorldState, Organism]:
    """Return model unchanged while statically checking organism departure."""
    return model


def _satisfies_carcass_contract(
    model: EntityDepartureModel[int, WorldState, Carcass],
) -> EntityDepartureModel[int, WorldState, Carcass]:
    """Return model unchanged while statically checking carcass departure."""
    return model


_WORLD_ORGANISM_DEPARTURE_CONTRACT = _satisfies_organism_contract(
    WorldOrganismDeparture()
)
_WORLD_CARCASS_DEPARTURE_CONTRACT = _satisfies_carcass_contract(
    WorldCarcassDeparture()
)
