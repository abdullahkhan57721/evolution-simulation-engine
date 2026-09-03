# Source Reading Difficulty Guide

The difficulty label describes first-read cognitive load, not code quality.

```text
simulation.py
    ★☆☆☆☆
    ownership/setup; read early

step_coordinator.py
    ★★☆☆☆
    short and semantically central

simulation_engine.py
    ★★☆☆☆
    simple run/commit/observe loop

protocols.py
    ★★★☆☆
    small but typing/generic variance adds noise

simulation_state.py
    ★★★☆☆
    attrs/custom initialization + copy/RNG semantics

stage_coordinator.py
    ★★★★☆
    simple semantic core surrounded by dispatch/telemetry/effect hot-path support

context.py
    ★★★☆☆
    immutable storage + overloads/cache

configuration/spec.py and dependency traversal
    ★★★★☆
    startup graph/validation concerns rather than runtime semantics
```

If a difficult file feels opaque, return to the concept/test before reading private
helpers line by line.
