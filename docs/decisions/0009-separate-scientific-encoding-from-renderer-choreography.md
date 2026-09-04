# 0009 — Separate scientific encoding from renderer choreography

- **Status:** Accepted
- **Date:** 2026-09-03
- **Supersedes:** —
- **Superseded by:** —

## Context

Post-v0.1 visualization work needs richer individual scientific encoding and a more
simulation-centered interactive/cinematic experience. The project now has at least
two distinct presentation media: an interactive application and a deterministic
cinematic renderer. B2 also exposed a concrete shared-data need: a focal
per-organism `max_speed` value must be available beside committed spatial replay
without adding renderer concepts to biological objects or turning spatial
observation into a universal snapshot.

Two tempting designs are both undesirable:

1. let each renderer independently decide what scientific variables mean visually,
   which risks semantic drift between interactive and cinematic presentation; or
2. create one universal renderer/replay/scene abstraction, which would couple media
   with fundamentally different interaction, camera, timing, and asset needs.

## Decision

Scientific visualization uses three responsibility layers:

```text
committed scientific evidence
        ↓
scenario-specific scientific encoding
        ↓
renderer-specific primitives and choreography
```

Visual primitives form a shared conceptual vocabulary, not a required shared scene
runtime. Scenario-specific scientific encoding is renderer-neutral and determines
which authoritative variables are focal, what visual channels mean, which events
matter, which statistics are primary, and which comparisons must remain matched.
Interactive and cinematic renderers independently own concrete graphics,
interaction/camera behavior, timing, easing, layout, and storytelling choreography.

Committed observation/result values remain the scientific source of truth.
Presentation interpolation is never treated as independently simulated evidence.
When a shared scientific-data gap appears, add the smallest renderer-neutral
observation contract at the appropriate observation/domain boundary rather than
adding display state to modeled entities.

The first such gap is solved with an opt-in sibling per-organism genetic-phenotype
trait observation rather than expanding `SpatialOrganismSnapshot` with arbitrary
focal traits.

A broad `ScenarioPresentationSpec` is not introduced yet. The responsibility is
real, but the exact shared value shape should wait until B3 plus another concrete
scenario demonstrate repeated fields worth encoding as a public abstraction.

## Alternatives considered

### Renderer-specific scientific mappings

Rejected because the same scenario could silently assign different meanings,
scales, colors, or comparison semantics in interactive and cinematic outputs.
Scientific meaning should be shared even when renderer mechanics differ.

### Universal visual/replay abstraction

Rejected because browser interaction and authored cinematic storytelling have
substantially different scene, camera, timing, and control requirements. A common
runtime would generalize implementation mechanics before a reusable need has been
demonstrated.

### Add focal traits directly to spatial snapshots

Rejected because spatial observation already has a focused world-state role.
Arbitrary trait growth would turn it into a presentation catch-all and duplicate
other observation responsibilities.

### Implement a large scenario-presentation schema immediately

Rejected because the current concrete evidence is B2/B3 plus the existing
max-intake scenario. That is enough to establish responsibility boundaries but not
enough to justify a wide optional-field abstraction for future imagined biology.

## Consequences

- Interactive and cinematic presentation can change technology independently.
- Both media must consume the same authoritative evidence and preserve the same
  scenario-level scientific meaning where they show the same variable.
- Renderer-specific objects, materials, layout, camera, timing, and easing remain
  outside shared scientific presentation values.
- Observation contracts should remain scientifically named and selective rather
  than generic renderer property bags.
- `SpatialObservation` remains focused; per-organism focal genetic traits use a
  sibling committed observation layer joined downstream by `(step_index,
  organism_id)`.
- Future scenario-presentation abstractions must be earned by repeated concrete
  consumers rather than speculative field inventories.
- Documentation and review should distinguish authoritative configuration,
  committed state, committed events, derived statistics, presentation
  interpolation, and explanatory annotations.

## References

- [Scientific Visualization Architecture](../architecture/scientific_visualization.md)
- [Evolution Observability](../observability.md)
- [Issue #132](https://github.com/abdullahkhan57721/evolution-simulation-engine/issues/132)
- [B2 Issue #129](https://github.com/abdullahkhan57721/evolution-simulation-engine/issues/129)
