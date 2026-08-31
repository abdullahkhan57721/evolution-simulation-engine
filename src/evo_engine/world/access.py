"""World adapters for read-only entity access."""

from __future__ import annotations

import attrs

from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class WorldOrganismAccess:
    """Read organisms from biological world state without mutating membership."""

    def get(
        self,
        reference: int,
        *,
        state: WorldState,
    ) -> Organism:
        """Return one organism by stable world identifier.

        Args:
            reference: Stable organism identifier.
            state: Biological world containing the organism.

        Returns:
            Referenced organism.
        """
        return state.organisms[reference]

    def entities(
        self,
        *,
        state: WorldState,
    ) -> tuple[Organism, ...]:
        """Return a stable snapshot of organisms in world iteration order.

        Args:
            state: Biological world whose organisms are read.

        Returns:
            Tuple snapshot of current organisms.
        """
        return tuple(state.organisms.values())


@attrs.frozen(slots=True, kw_only=True)
class WorldCarcassAccess:
    """Read carcasses from biological world state without mutating membership."""

    def get(
        self,
        reference: int,
        *,
        state: WorldState,
    ) -> Carcass:
        """Return one carcass by stable world identifier.

        Args:
            reference: Stable carcass identifier.
            state: Biological world containing the carcass.

        Returns:
            Referenced carcass.
        """
        return state.carcasses[reference]

    def entities(
        self,
        *,
        state: WorldState,
    ) -> tuple[Carcass, ...]:
        """Return a stable snapshot of carcasses in world iteration order.

        Args:
            state: Biological world whose carcasses are read.

        Returns:
            Tuple snapshot of current carcasses.
        """
        return tuple(state.carcasses.values())
