# Complexity Walkthrough: One Run

Let:

```text
T = completed steps
N_t = domain scale at step t
E_t = committed events in step t
```

A useful run-level model is:

```text
Total time ~=
    initial observation
    + sum over t=1..T (
        stopping_condition_cost_t
        + C_domain_copy(N_t)
        + sum(stage_costs_t)
        + O(E_t) step telemetry work
        + telemetry_observer_cost_t
        + domain_observer_cost_t
      )
```

If per-step workload is stable, runtime may grow roughly linearly with `T`.
Evolutionary simulations often change population/event counts, so using `N_t` and
`E_t` avoids the false assumption that every step costs the same.

## Memory

Live memory may include:

```text
current committed domain state
working transaction copy during step
stage temporaries
current step telemetry
observer state
```

Cumulative experiment memory depends heavily on what observers retain. Full
snapshots can grow with `sum(N_t)` across steps even when live state remains near
`N_t`.
