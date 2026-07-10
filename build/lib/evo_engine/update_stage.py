from __future__ import annotations

from dataclasses import dataclass

# Imports for type hints:
from evo_engine.events_proposer import EventsProposer


@dataclass
class UpdateStage:
    name: str
    events_proposers: list[EventsProposer]
