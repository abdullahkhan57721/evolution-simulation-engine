# Model Notes

## Version 1 Scenario

The first version of the simulation models a one-trait energy survival scenario.

Each organism has one inherited trait:

- `energy_efficiency`

Higher `energy_efficiency` means the organism is better at conserving energy.

## TraitSet

`TraitSet` stores inherited trait values for one organism.

Version 1 has one trait:

- `energy_efficiency: float`

Higher `energy_efficiency` means the organism conserves more energy per time step.

Default value:

- `0.50`

Allowed range:

- minimum: `0.0`
- maximum: `1.0`