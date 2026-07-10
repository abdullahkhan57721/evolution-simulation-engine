from __future__ import annotations

from evo_engine.event import AgingEvent, Event
from evo_engine.history import History

# Imports for type hints
from evo_engine.world_state import WorldState


class EventsProposer:
    def propose(
        self,
        world_state: WorldState,
        history: History,
    ) -> list[Event]:
        raise NotImplementedError


class AgingEventsProposer(EventsProposer):
    def propose(
        self,
        world_state: WorldState,
        history: History,
    ) -> list[Event]:
        aging_events: list[Event] = []

        for organism in world_state.organisms:
            if organism.is_alive:
                aging_events.append(
                    AgingEvent(
                        organism_id=organism.id,
                        time_step=world_state.time_step,
                    )
                )

        return aging_events
