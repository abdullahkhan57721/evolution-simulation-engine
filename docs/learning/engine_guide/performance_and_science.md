# Performance and Scientific Semantics

Simulation optimization is constrained by the model's meaning.

A faster algorithm is not equivalent if it changes:

```text
who can interact
which candidates compete
ordering semantics
random-choice distribution
state visible to decisions
evolutionary outcomes
```

For example, replacing an all-pairs biological interaction with a neighborhood
index can be an excellent optimization **if** the scientific model already defines
local interactions and the index returns the same eligible neighborhood. It is not
an optimization if it silently drops distant interactions that the model intended
to permit.

Performance validation should therefore include both software behavior and
scientifically relevant outcome equivalence where the optimization touches domain
algorithms.
