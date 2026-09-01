# 0004 — Prefer readability before micro-optimization

- **Status:** Accepted
- **Date:** 2026-09-01
- **Supersedes:** —
- **Superseded by:** —

## Context

The engine contains both generic orchestration and potentially expensive domain
processes. Reference-ecology timing therefore mixes kernel cost with biological
and ecological work. Repeated micro-optimization can make orchestration harder
to understand while producing small or misleading improvements.

## Decision

Readability and maintainability take precedence over micro-optimization.
Performance work requires measurement and should target a clearly identified
hotspot or structural cost.

Kernel optimization claims use synthetic domain-neutral kernel benchmarks.
Reference-ecology profiles remain integration signals but are not treated as
isolated kernel measurements.

Once an optimization campaign removes the measured structural hotspots, stop
optimizing unless new evidence reveals another meaningful opportunity. Do not
sacrifice clear orchestration semantics merely to reduce small helper-call or
allocation counts.

## Alternatives considered

- **Continuously optimize reference-scenario wall time.** Rejected because domain
  process costs confound kernel costs and can steer generic architecture toward
  one preset.
- **Optimize any measurable micro-cost.** Rejected because local speedups can
  accumulate readability debt without meaningful end-to-end benefit.
- **Never optimize until the whole product is feature-complete.** Rejected because
  genuine structural hotspots such as transactional copying can distort later
  architecture and should be addressed when evidence is strong.

## Consequences

- Performance PRs should include profiling or benchmark evidence appropriate to
  the layer being changed.
- Synthetic kernel benchmarks act primarily as regression guards now that the
  current kernel optimization campaign is complete.
- Clear data structures and procedural flow may be retained even when a more
  opaque representation is marginally faster.
- A representation redesign needs independent justification beyond benchmark
  score chasing.

## References

- `docs/performance.md`
- `docs/kernel_contract.md`
- `scripts/profile_kernel.py`
- `scripts/profile_reference.py`
- performance PRs #59–#73
