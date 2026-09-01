# 0001 — Keep the simulation kernel domain-neutral

- **Status:** Accepted
- **Date:** 2026-09-01
- **Supersedes:** —
- **Superseded by:** —

## Context

Early engine development mixed generic orchestration concerns with biological
state and lifecycle vocabulary. That coupling would make the scheduler harder to
reuse, test independently, and reason about as biological capabilities such as
sexual reproduction and richer genetics expand.

## Decision

The simulation kernel is a domain-neutral execution layer. `SimulationState`
owns a transactional envelope whose mutable modeled payload is named
`domain_state`. The kernel coordinates processes, events, resolution,
materialization, application, context, effects, telemetry, and transaction/RNG
semantics without assigning biological, ecological, genetic, spatial, or other
modeled meaning to them.

Biological semantics live above the kernel. Domain code may unwrap
`simulation_state.domain_state` into a `WorldState` and then use normal
biological/world vocabulary.

The kernel is considered complete for the current architecture and is now in
maintenance mode. New modeled behavior belongs above it unless an existing
kernel contract cannot express the needed generic semantics correctly.

## Alternatives considered

- **Keep a biology-shaped kernel and rely on protocols.** Rejected because names,
  validation, and lifecycle assumptions still bias generic orchestration even if
  imports are technically decoupled.
- **Generalize only when a second nonbiological product exists.** Rejected because
  current evolution development already benefits from a clean distinction
  between scheduling mechanics and modeled meaning, and architecture tests can
  verify that distinction now.

## Consequences

- Kernel code and kernel-facing tests must avoid modeled-domain dependencies and
  vocabulary.
- Biological configuration compilers may layer on generic `SimulationSpec`.
- Domain-neutral vertical tests and synthetic kernel benchmarks are meaningful.
- Some explicit adaptation/unwrapping is required at the domain boundary.
- Future kernel changes require generic justification rather than domain
  convenience.

## References

- `docs/kernel_contract.md`
- `docs/architecture/index.md`
- `.github/ARCHITECTURE_GUARDRAILS.md`
- `tests/engine/test_domain_neutral_kernel.py`
- PRs #39, #74, and #76
