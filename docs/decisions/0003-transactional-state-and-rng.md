# 0003 — Own transactional state and randomness in SimulationState

- **Status:** Accepted
- **Date:** 2026-09-01
- **Supersedes:** —
- **Superseded by:** —

## Context

The engine needs reproducible stochastic simulation while preserving
transactional execution. A failed working step must not mutate committed modeled
state or advance the committed random-number stream. Hidden generators owned by
individual processes would make exact replay and rollback difficult to reason
about.

## Decision

`SimulationState` owns both the mutable `domain_state` payload and the simulation
RNG state. `SimulationState.copy()` independently copies `domain_state`, clones
the complete RNG state, and shares immutable `SimulationContext` by reference.

Processes that make stochastic simulation decisions consume
`simulation_state.rng`. They do not create hidden independent RNGs for those
decisions.

A completed transaction replaces authoritative state only after the coordinated
step succeeds. Failed or discarded transactions do not advance committed modeled
state or committed RNG state.

## Alternatives considered

- **Global module-level RNG.** Rejected because ownership and rollback semantics
  would be implicit and difficult to isolate in tests.
- **One RNG per process.** Rejected because deterministic replay would depend on a
  second hidden state graph and process-specific cloning/checkpoint rules.
- **Share the same RNG object across transactional copies.** Rejected because a
  failed working transaction could advance the committed random stream.

## Consequences

- Equal initial state, configuration, seed, and component ordering reproduce equal
  kernel outcomes.
- Transaction-copy tests must verify domain-state isolation, RNG equivalence, and
  immutable context sharing.
- New stochastic components should use the supplied simulation RNG unless they
  are explicitly modeling an independent persisted random source as domain state.
- RNG ownership is part of the kernel contract and cannot be changed as a local
  optimization.

## References

- `docs/kernel_contract.md`
- `src/evo_engine/engine/simulation_state.py`
- `tests/engine/test_simulation_state_copy_semantics.py`
- `tests/engine/test_kernel_determinism.py`
- PRs #69 and #76
