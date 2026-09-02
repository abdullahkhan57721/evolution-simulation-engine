# Architectural Roadmap

This page answers **where the project is going** at the level of coherent
architectural milestones. It is a rolling planning aid, not an implementation
ticket system.

## Authority and maintenance boundary

GitHub Issues remain authoritative for the scope, acceptance criteria, status,
and dependencies of active implementation work. Architecture/subsystem docs and
ADRs remain authoritative for settled contracts and rationale.

This roadmap should change when milestone ordering or architectural direction
materially changes. It should not mirror every Issue, PR, commit, or transient
status update.

## Guiding direction

The project is moving toward a simulation engine in which:

1. the frozen kernel provides domain-neutral deterministic transactional
   execution;
2. the general evolution layer expresses evolution without assuming biology;
3. biological genetics, reproduction, development, and ecology specialize those
   settled general contracts;
4. richer modeled biology is added only after the abstraction boundary it depends
   on is coherent;
5. experiments, observation, and interfaces expose the resulting model without
   pushing domain assumptions back into lower layers.

The kernel is not the current development frontier. New modeled behavior normally
belongs above it unless a genuine generic deficiency is demonstrated.

## Near-term dependency graph

```text
#84 / #85
nonbiological evolutionary vertical slice
        |
        v
#86
normalize general-evolution transmissible-state contracts
        |
        v
biological specialization hardening
        |
        v
richer genetics and reproduction
        |
        +-------------------------+
        |                         |
        v                         v
richer development / GxE    richer mating / inheritance
        |                         |
        +------------+------------+
                     |
                     v
           richer evolutionary ecology
```

The exact Issue numbers after #86 should be assigned only when those milestones
are scoped against current `main`.

## Milestone 1 — General-evolution contract normalization

**Current ticket:** Issue #86.

**Goal:** reconcile the biology-shaped `EvolutionaryEntity` /
`HeritableStateExpression` / `heritable_state` vocabulary with the broader
`TransmissibleStateCarrier` / `transmissible_state` model demonstrated by the
nonbiological vertical slice.

**Why now:** #85 supplied concrete nonbiological evidence. Normalizing before
additional biological growth prevents new code from depending on an awkward
split that is already known.

**Constraints:**

- preserve source/recipient propagation semantics;
- preserve the frozen kernel;
- avoid redesigning production/lifecycle/genetics merely for naming consistency;
- prefer one coherent pre-1.0 migration over compatibility aliases if a public
  rename is chosen.

**Implementation mode:** primarily ChatGPT Chat because the difficult work is a
small, consequential public-contract decision. Codex is not the default here.

## Milestone 2 — Harden biology as a specialization of the settled model

**Goal:** after #86, audit the biological genetics/reproduction path against the
settled general-evolution contracts and remove any remaining accidental mismatch
without rewriting working biology.

The desired conceptual path is:

```text
organism
    |
    v
transmissible biological state / genome
    |
    v
gamete or source-state formation
    |
    v
recombination + variation
    |
    v
recipient/offspring transmissible state
    |
    v
expression + development
    |
    v
new or updated biological entity
```

**Why before richer genetics:** richer dominance, ploidy, mating, and
recombination behavior should specialize a coherent generic model rather than
forcing another foundational cleanup later.

**Implementation mode:** architecture and representative changes in ChatGPT;
Codex can be useful if the settled design requires a broad mechanical migration
across many biological files/tests.

## Milestone 3 — Richer genetic expression

**Goal:** extend biological expression beyond the simplest current assumptions so
architecture can naturally support dominance and other non-additive effects,
context-sensitive expression, and future ploidy variation.

**Design questions to settle before implementation include:**

- where genotype-to-expressed-state rules live;
- how allele interactions are represented without baking one dominance model into
  the generic layer;
- how ploidy affects locus/genotype representation;
- how development/GxE consumes expressed genetic state versus transmissible
  state.

**Implementation mode:** ChatGPT for public-model design; Codex selectively for
settled migrations and exhaustive test matrices.

## Milestone 4 — Richer transmission and sexual reproduction

**Goal:** deepen the biological specialization toward richer sexual reproduction
without narrowing general propagation.

Likely fronts include:

- chromosome-specific recombination behavior;
- configurable mutation/recombination models;
- variable contributor counts and reproductive roles;
- richer gamete formation;
- mating-system composition that remains separate from low-level inheritance;
- clear separation of state propagation from entity production/placement.

**Implementation mode:** mixed. Architecture stays in ChatGPT; repetitive adapter,
test, and migration work is a strong Codex candidate once contracts are settled.

## Milestone 5 — Richer development and phenotype realization

**Goal:** expand the path from transmitted genetic state to realized operative
characteristics while preserving a clean separation between inheritance,
expression, development, environment, and behavior/physiology.

Potential fronts include stronger G×E/plasticity models, developmental stochasticity,
and richer composition between genetic expression and environment-dependent
realization.

This milestone may overlap with richer genetics only after the responsibility
boundary is explicit.

## Milestone 6 — Richer evolutionary ecology

**Goal:** use the stable genetics/reproduction/development foundations to model
more consequential ecological selection pressures and interactions without
pushing ecological meaning into general evolution or the kernel.

Possible fronts include richer resource competition, movement/behavior,
predation, life-history tradeoffs, and environment-dependent reproductive
outcomes. Selection should continue to emerge from differential persistence and
propagation rather than becoming an intrinsic generic scalar field.

## Cross-cutting fronts

The following concerns continue alongside modeled-domain milestones when there is
concrete need:

- observation and analysis of evolutionary outcomes;
- reproducible experiment composition and export;
- checkpoint/resume guarantees;
- documentation and examples;
- performance measurement based on evidence;
- interfaces/UI only when the underlying public construction path is stable enough
  to expose cleanly.

Do not turn these into foundational redesigns merely because they are
cross-cutting.

## ChatGPT versus Codex allocation

Use ChatGPT Chat primarily when work is:

- architecture-heavy;
- a consequential public-contract decision;
- tightly scoped and sequential;
- easier because the design conversation itself is important context;
- an independent architectural review.

Use Codex selectively when work is:

- execution-heavy behind settled contracts;
- broad and repetitive;
- a mechanical migration across many files;
- validation/debug-cycle intensive;
- independently parallelizable;
- valuable to run unattended while other design work continues.

Optimize for total time and attention required to reach a correct merged change,
not for a blanket preference for one implementation agent.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier milestones changed the assumptions in this roadmap;
3. settle consequential architecture in Chat before implementation when needed;
4. create a focused Issue with explicit dependencies, boundaries, non-goals,
   acceptance criteria, and verification;
5. update this roadmap in the same PR when the milestone materially changes
   ordering or architectural direction.

A roadmap is a hypothesis about the best sequence. Evidence from implementation
may change it.
