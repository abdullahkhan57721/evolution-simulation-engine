# 0002 — Preserve stage simultaneity with materialize-before-apply

- **Status:** Accepted
- **Date:** 2026-09-01
- **Supersedes:** —
- **Superseded by:** —

## Context

A simulation stage may contain multiple processes whose proposals should reflect
the same stage-start state. Accepted events may also require stochastic or
deferred consequences that should be determined only after conflict resolution.
Materializing and applying one event before preparing the next would allow later
accepted events to observe state mutations that were not part of the proposal or
resolution snapshot.

## Decision

`StageCoordinator` preserves the semantic sequence:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

All processes propose against the same stage-start `SimulationState`. The
resolver chooses accepted events and their order. Every accepted event is
materialized before any accepted event is applied. Prepared events are then
applied in resolver order.

This ordering is part of the public kernel contract rather than an incidental
implementation detail.

## Alternatives considered

- **Materialize immediately before each application.** Rejected because later
  materialization could observe state already changed by earlier accepted events,
  weakening stage simultaneity.
- **Materialize before conflict resolution.** Rejected because rejected events
  would consume randomness or other deferred work unnecessarily and could change
  deterministic trajectories.
- **Apply proposals directly without a materialization phase.** Rejected because
  some accepted transitions need deferred stochastic/domain consequences while
  keeping proposal/resolution pure.

## Consequences

- Processes can propose candidates without consuming randomness that belongs only
  to accepted outcomes.
- Accepted-event materialization must not depend on mutations from other accepted
  events in the same stage.
- Tests must protect materialize-before-apply behavior and stage-start proposal
  semantics.
- Optimizations must preserve this order even if a different loop structure would
  be faster.

## References

- `docs/kernel_contract.md`
- `src/evo_engine/engine/stage_coordinator.py`
- `tests/engine/test_stage_coordinator.py`
- PR #74
