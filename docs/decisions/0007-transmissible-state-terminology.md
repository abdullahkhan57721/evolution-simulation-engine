# 0007 — Use transmissible state as the canonical general-evolution term

- **Status:** Accepted
- **Date:** 2026-09-02
- **Supersedes:** —
- **Superseded by:** —

## Context

The general-evolution layer originally exposed `EvolutionaryEntity.heritable_state`
and `HeritableStateExpression`, reflecting the biological inheritance path by
which those abstractions were introduced. Later propagation work generalized the
same source-state concept to horizontal, oblique, replacement, zero-source, and
multi-source transfer through `TransmissibleStateCarrier.transmissible_state` and
`PropagationModel`.

The nonbiological information-propagation vertical slice demonstrated that the
older expression vocabulary was now misleading: one strategy token was exposed
and propagated as transmissible state but had to be passed to expression under a
`heritable_state` name despite no descendant relationship.

## Decision

`transmissible state` is the canonical generic term for information that may be
expressed, varied, or propagated in an evolutionary system.

- Rename `HeritableStateExpression` to `TransmissibleStateExpression`.
- Make the expression input positional-only so domain specializations can retain
  native parameter names such as `express(genome)` without weakening the generic
  contract.
- Remove the redundant `EvolutionaryEntity` / `heritable_state` Protocol rather
  than maintaining two one-property carrier contracts.
- Keep `TransmissibleStateCarrier` and `PropagationModel` unchanged in
  `evo_engine.propagation`.
- Keep "evolving entity" as a useful architectural concept without introducing a
  marker Protocol that adds no independent capability.
- Keep biological terms such as genome, inheritance, parent, offspring, and
  heritable where biological lineage semantics are actually intended.
- Because the project is pre-1.0, perform one atomic migration without
  compatibility aliases.

## Alternatives considered

- **Keep both heritable and transmissible state as generic contracts.** Rejected
  because the current architecture does not encode a generic lineage-restricted
  state category; biology would continue exposing the same genome through two
  aliases and horizontal systems would retain misleading terminology.
- **Retain `EvolutionaryEntity` but rename its property to `transmissible_state`.**
  Rejected because it would remain structurally redundant with
  `TransmissibleStateCarrier` while adding no independent entity semantics.
- **Rename only the expression Protocol.** Rejected because leaving
  `EvolutionaryEntity.heritable_state` would preserve the same conceptual split
  in the public API.

## Consequences

- General expression, variation, and propagation now share one state vocabulary.
- Biological implementations keep their domain-native APIs; for example,
  `GeneticArchitecture.express(genome)` can structurally satisfy
  `TransmissibleStateExpression`.
- Generic consumers that used the removed pre-1.0 names must migrate atomically.
- A future lineage-specific generic contract remains possible if concrete domain
  evidence establishes semantics beyond ordinary transmissible-state carrying.
- Frozen kernel execution, source-state/recipient propagation semantics,
  production, lifecycle, genetics, reproduction, RNG, transaction, and telemetry
  contracts are unchanged.

## References

- GitHub Issue #86
- PR #90
- `docs/general_evolution_framework.md`
- `src/evo_engine/evolution/contracts.py`
- `src/evo_engine/propagation.py`
- `examples/nonbiological_evolution.py`
