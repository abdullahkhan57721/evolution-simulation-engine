from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Organism:
    id: int
    age: int = 0
    is_alive: bool = True