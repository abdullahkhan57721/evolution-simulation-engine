from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    time_step: int


@dataclass(frozen=True)  
class AgingEvent(Event):
    organism_id: int
    amount: int = 1