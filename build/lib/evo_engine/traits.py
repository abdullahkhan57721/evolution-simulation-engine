"""This module defines the inherited traits carried by organisms."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class TraitSet:
    """Stores inherited traits for one organism.

    Attributes:
            energy_efficiency:
                    A value from 0.0 to 1.0 representing how efficiently an organism conserves energy. Lower values represent higher energy loss per step.
    """

    energy_efficiency: float = 0.50

    def validate(
        self, min_energy_efficiency: float = 0.0, max_energy_efficiency: float = 1.0
    ) -> None:
        """Raise ValueError if energy_efficiency value is outside the allowed range"""

        if min_energy_efficiency >= max_energy_efficiency:
            raise ValueError(
                "min_energy_efficiency must be less than max_energy_efficiency."
            )
        if not min_energy_efficiency <= self.energy_efficiency <= max_energy_efficiency:
            raise ValueError(
                "energy_efficiency must be between "
                f"{min_energy_efficiency} and {max_energy_efficiency}."
            )

    def copy(self) -> "TraitSet":
        """Return an independent copy of this trait set."""

        return TraitSet(energy_efficiency=self.energy_efficiency)

    def to_dict(self) -> dict[str, float]:
        """Return the trait set as a dictionary."""

        return asdict(self)
