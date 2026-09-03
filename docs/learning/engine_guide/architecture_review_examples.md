# Architecture Review Mini-Examples

These are short practice cases.

## Hidden RNG

```python
rng = random.Random()
choice = rng.choice(candidates)
```

Inside a simulation decision this is suspicious because stochastic state is no
longer transaction-owned/reproducible through `SimulationState.rng`.

## Observer repairs state

```python
def observe(world, *, step_index):
    remove_conflicting_entities(world)
```

Observation is now mutation/repair rather than measurement. Correctness belongs in
transition selection/application before commit.

## Generic flag explosion

```python
StageCoordinator(..., biological=True, sexual=True, spatial=True)
```

This moves domain meaning into generic orchestration. Prefer domain processes,
resolvers, and policies.

## Useful policy abstraction

Two mating systems need different participant-capacity rules while stage semantics
remain identical. A resolver/policy axis is real and can vary independently.

## Premature abstraction

One implementation gains a registry/factory hierarchy with no second use, no
replacement need, and no invariant benefit. The extra concepts are maintenance
cost until real variation appears.
