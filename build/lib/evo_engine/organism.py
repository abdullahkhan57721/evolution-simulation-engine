from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Organism:
    id: int
    age: int = 0
    is_alive: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.id < 0:
            raise ValueError("Organism id must be non-negative.")

        if self.age < 0:
            raise ValueError("Organism age must be non-negative.")

        if type(self.is_alive) is not bool:
            raise TypeError("Organism is_alive must be a bool.")

        if type(self.id) is not int:
            raise TypeError("Organism id must be an int.")

        if type(self.age) is not int:
            raise TypeError("Organism age must be an int.")
