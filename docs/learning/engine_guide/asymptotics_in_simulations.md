# Asymptotics in Evolving Simulations

Many textbook complexity examples assume a fixed input size. Simulations can change
their own size through time.

If population at step `t` is `N_t`, a per-step O(N) process has total run cost more
like:

```text
O(sum from t=1..T of N_t)
```

not necessarily O(TN) for one fixed `N`.

If a per-step process is pairwise:

```text
O(sum N_t^2)
```

This is useful for evolutionary/ecological models where birth, death, migration,
or resource dynamics change event/entity counts.

The lesson is to choose variables that match the evolving workload rather than
forcing a static-input algorithm template onto the simulation.
