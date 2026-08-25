# Spatial Environmental Fields

The world can represent spatially varying scalar environmental variables without
coupling biological processes to one hard-coded concept such as temperature.

An `EnvironmentalField` is immutable configuration containing a unique name and a
finite numerical default value:

```python
from evo_engine.world import EnvironmentalField, WorldState

world = WorldState(
    width=100,
    height=100,
    environmental_fields=(
        EnvironmentalField(name="temperature", default_value=20.0),
        EnvironmentalField(name="salinity", default_value=0.0),
    ),
)
```

## Sparse spatial storage

A field's default applies everywhere unless a cell has an explicit override.
`WorldState` stores only those overrides:

```python
world.set_environmental_value(
    "temperature",
    x=10,
    y=4,
    value=25.5,
)

world.environmental_value("temperature", x=10, y=4)  # 25.5
world.environmental_value("temperature", x=11, y=4)  # 20.0
```

Setting a cell back to the field default removes its sparse override. This is
important for large worlds in which most cells share a background condition.

Fields accept finite integers or floats. Boolean and non-finite values are
rejected.

## Mutable ecological state, immutable definitions

Field definitions are immutable and configured when a `WorldState` is created.
Spatial field values are mutable ecological state owned by the world.

This distinction mirrors other engine boundaries:

```text
EnvironmentalField definition
    → stable meaning/default of an environmental variable

WorldState environmental values
    → current spatial ecological state
```

Processes should read values through `WorldState.environmental_value()` and
mutate them through `set_environmental_value()` or
`change_environmental_value()`. They should not maintain separate ad-hoc spatial
dictionaries.

## Transactional execution

Environmental values participate automatically in `WorldState.copy()`. A working
simulation step can therefore change environmental conditions without affecting
the authoritative state until the entire step commits.

A copied world starts with the same environmental values but an empty
transaction-local mutation journal, exactly like the existing organism, carcass,
and resource state.

Exact reference checkpoints serialize the complete world object graph, so any
configured environmental fields and spatial overrides are preserved without a
separate persistence format.

## Causal telemetry

An effective environmental mutation produces `EnvironmentalValueChanged` with:

```text
field_name
x, y
before
after
delta
```

No record is emitted for a no-op assignment. Environmental processes can
therefore participate in the same committed event telemetry as movement,
resources, births, and mortality.

## Why this precedes plasticity

The development API already permits a `DevelopmentModel` to inspect
`SimulationState`, but until now there was no general environmental quantity for
such a model to read.

Spatial environmental fields create that missing substrate. The intended next
layer is an environment-aware trait development model or reaction norm:

```text
Genome
    → GeneticPhenotype
        + local environmental field value
            → DevelopmentModel
                → DevelopmentalProfile
```

That architecture can support genotype-by-environment interactions,
condition-dependent developmental targets, habitat-specific phenotypes, and
environmental sex or mating-type determination while keeping genetic expression
deterministic.

## Current boundary

This milestone supplies environmental **state**, not environmental dynamics.
There is not yet a built-in temperature cycle, seasonality process, diffusion
model, reaction norm, or reference-environment calibration. Those should be
separate policies/processes built on this substrate rather than hidden behavior in
`WorldState`.
