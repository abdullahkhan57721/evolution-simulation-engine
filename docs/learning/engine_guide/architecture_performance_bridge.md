# Architecture and Performance Are Connected

Architecture determines where computational costs live and which optimizations are
safe.

Examples:

```text
transaction boundary
    -> copy time/memory
    -> rollback simplicity

stage simultaneity
    -> proposal/preparation storage
    -> prevents accidental order causality

accepted-only materialization
    -> deferred work scales with accepted events
    -> preserves rejected-candidate RNG semantics

explicit resolver policy
    -> resolver algorithm can vary independently
    -> complexity belongs to policy, not kernel assumption

observer separation
    -> scientific history can grow independently of live state
    -> observation cost can be measured separately
```

This is why the textbook does not teach complexity as an isolated mathematics
chapter. Computational behavior is one consequence of architectural choices.
