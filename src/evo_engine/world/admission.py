"""World adapters for admitting entities into biological state."""

from __future__ import annotations

import attrs

from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class WorldOrganismAdmission:
    """Admit a fully produced organism into a biological world.

    World admission owns world-specific entry mechanics such as coordinate
    validation, permanent ID assignment, population membership, and mutation
    journaling by delegating to ``WorldState.add_organism``.
    """

    def admit(
        self,
        entity: Organism,
        *,
        state: WorldState,
    ) -> None:
        """Add an already-produced organism to world state.

        Args:
            entity: Fully produced organism ready to enter the world.
            state: Biological world receiving the organism.
        """
        state.add_organism(entity)


@attrs.frozen(slots=True, kw_only=True)
class WorldCarcassAdmission:
    """Admit a carcass into biological world state.

    The adapter delegates coordinate validation, permanent carcass ID
    assignment, membership mutation, and mutation journaling to
    ``WorldState.add_carcass``.
    """

    def admit(
        self,
        entity: Carcass,
        *,
        state: WorldState,
    ) -> None:
        """Add an already-created carcass to world state.

        Args:
            entity: Carcass ready to enter the world.
            state: Biological world receiving the carcass.
        """
        state.add_carcass(entity)
