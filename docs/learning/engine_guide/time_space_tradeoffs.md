# Time-Space Tradeoffs in This Engine

## Dispatch metadata

```text
spend:
    O(P) stable stage metadata

gain:
    average O(1) event-type dispatch per accepted event
```

## Context typed cache

```text
spend:
    O(C) cached typed key/value references

gain:
    avoid repeated O(K) scans for successful typed lookups
```

## Transactional state copy

This is not a simple cache tradeoff, but it deliberately spends memory/time:

```text
spend:
    domain copy + RNG clone

gain:
    atomic rollback + deterministic RNG isolation
```

## Telemetry retention

```text
spend:
    event records/history memory

gain:
    causal observability/debugging/scientific analysis
```

## General rule

Do not optimize either time or memory in isolation. Ask what semantic or analytical
capability the cost buys and whether the scale makes the tradeoff problematic.
