"""World adapters for deriving entity references."""

from __future__ import annotations

import attrs

from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class WorldOrganismReference:
    """Return the permanent world ID of an admitted organism.

    The adapter verifies that the organism is the exact entity registered under
    its ID in the supplied world. This keeps reference derivation read-only while
    preserving the state-local meaning of a world-managed organism ID.
    """

    def reference(
        self,
        entity: Organism,
        *,
        state: WorldState,
    ) -> int:
        """Return an organism's permanent reference in the supplied world.

        Args:
            entity: Already-admitted organism whose reference is requested.
            state: Biological world in which the reference must resolve.

        Returns:
            Permanent organism ID.

        Raises:
            ValueError: If entity is not registered in state under its own ID.
        """
        reference = entity.id
        if state.organisms.get(reference) is not entity:
            raise ValueError(
                "entity must be the organism registered under its ID in state."
            )
        return reference


@attrs.frozen(slots=True, kw_only=True)
class WorldCarcassReference:
    """Return the permanent world ID of an admitted carcass.

    The adapter verifies exact membership in the supplied world so carcass IDs
    retain state-local reference meaning rather than becoming global identity.
    """

    def reference(
        self,
        entity: Carcass,
        *,
        state: WorldState,
    ) -> int:
        """Return a carcass's permanent reference in the supplied world.

        Args:
            entity: Already-admitted carcass whose reference is requested.
            state: Biological world in which the reference must resolve.

        Returns:
            Permanent carcass ID.

        Raises:
            ValueError: If entity is not registered in state under its own ID.
        """
        reference = entity.id
        if state.carcasses.get(reference) is not entity:
            raise ValueError(
                "entity must be the carcass registered under its ID in state."
            )
        return reference
