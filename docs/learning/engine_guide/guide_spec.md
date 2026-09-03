# Evolution Simulation Engine Learning Textbook — Guide Specification

This file is the durable design brief for the repository-native learning textbook.
It records the intended audience, learning goals, pedagogy, structure, and
maintenance rules so future revisions do not depend on chat history.

The textbook is **pedagogical, not authoritative**. When any explanation here or
in the learning guide conflicts with current code, tests, architecture docs, or
ADRs, repository truth wins. The canonical kernel contract is
[`docs/kernel_contract.md`](../../kernel_contract.md), and the canonical general
evolution overview is
[`docs/general_evolution_framework.md`](../../general_evolution_framework.md).

## Audience and assumptions

The primary reader is technically comfortable with:

- the basic Python object model;
- modules, packages, imports, and ordinary project organization;
- ordinary type annotations, interfaces, and the basic purpose of `Protocol`.

Do not turn the textbook into a beginner-Python course. Explain language features
only where their use carries architectural meaning or is easy to misread. Useful
examples include positional-only parameters, keyword-only parameters,
`attrs.frozen`, covariance/contravariance when it clarifies a contract, and the
difference between literal syntactic sugar and API/construction sugar.

## Learning goals

After completing the guide, the reader should be able to:

1. explain the separation among simulation mechanics, general evolutionary
   semantics, and biological specialization;
2. derive the need for stages, proposal simultaneity, resolvers,
   materialization, transactional state/RNG, immutable context, telemetry, and
   preflight from concrete failure modes rather than memorizing class names;
3. explain the abstract evolution model independently of biology;
4. map general concepts such as transmissible state, propagation, expression,
   variation, linkage, and production onto biological genetics and reproduction;
5. distinguish easy-to-conflate relationships such as propagation versus
   production and reproductive participants versus investors, genetic
   contributors, and production sources;
6. assemble and run a small simulation through the public kernel API;
7. open the kernel source and recognize the architectural purpose of each major
   section;
8. identify kernel invariants, the code that enforces them, and focused tests that
   protect them;
9. debug one simulation step while correctly distinguishing authoritative state,
   transactional working state, committed telemetry, and domain mutation; and
10. reason about a proposed change by asking which layer owns the concept and
    whether a lower-level abstraction genuinely needs to change.

## Core pedagogical sequence

Use this sequence repeatedly:

```text
problem
  |
  v
naive/simple design
  |
  v
failure mode
  |
  v
abstraction we need
  |
  v
public contract
  |
  v
production implementation
  |
  v
concrete domain example
```

The goal is to make architecture feel *derived* rather than arbitrary.

## Additional pedagogical principles

### Progressive disclosure

Present important mechanisms in layers:

1. plain-language concept;
2. tiny diagram or pseudocode;
3. small real source snippet;
4. complete production flow;
5. validation, telemetry, typing, and performance plumbing.

Do not let incidental implementation complexity hide the semantic core.

### Spiral learning

Revisit central ideas at increasing depth. For example:

- transaction: first as “work on a copy,” later as domain-state + RNG rollback;
- simultaneity: first as avoiding order dependence, later as the exact
  materialize-before-apply semantics;
- propagation: first as state transfer, later as the abstraction specialized by
  biological inheritance;
- ownership: first as object containment, later as separate questions of
  responsibility, authority, mutation rights, and randomness ownership.

### Abstraction ladders

Frequently show general-to-concrete ladders, for example:

```text
state transition
    -> transmissible-state propagation
        -> biological inheritance
            -> Mendelian sexual inheritance
                -> one configured simulation
```

and:

```text
entity
    -> evolving entity (conceptual role)
        -> organism
            -> Organism instance #527
```

### Concept-to-code and code-to-concept maps

Teach both directions.

Concept to code:

```text
transaction envelope -> SimulationState
stage simultaneity    -> StageCoordinator
conflict policy       -> Resolver
```

Code to concept:

```text
simulation_state.copy()  -> transaction boundary
resolve_events(...)      -> selection among candidate transitions, not mutation
materialize_event(...)   -> accepted-only deferred consequence
apply_event(...)         -> domain mutation owned by the process
```

### Invariant-centered reading

For major invariants provide:

```text
invariant
why it exists
implementation location
focused test
failure mode if violated
```

Teach the professional reading loop:

```text
public contract -> focused test -> implementation
```

rather than always reading production files top-to-bottom.

### Misconception checks

Explicitly contrast concepts readers are likely to merge mentally:

- syntax versus semantics;
- literal syntactic sugar versus convenience/construction sugar;
- abstraction versus generic implementation;
- interface/contract versus implementation;
- ownership versus responsibility versus authority;
- state versus immutable configuration/context;
- authoritative state versus transactional working state;
- proposal versus resolved event versus materialized event versus `AppliedEvent`
  telemetry;
- resolver selection versus process mutation;
- propagation versus entity production;
- transmitted information versus expressed characteristics versus realized
  phenotype/current physiological state;
- selection versus a stored scalar named fitness;
- reproductive participant versus investor versus genetic contributor versus
  production source.

### Prediction and comparison

Prefer exercises that ask the reader to predict observable semantics before
running code, or compare two designs and identify consequences. Avoid relying on
vocabulary recall alone.

### Mastery criteria

End major chapters with “You understand this chapter if you can…” prompts that
measure design-level competence.

## Architectural layer labels

Use consistent labels in prose and tables:

- **[KERNEL]** — domain-neutral execution mechanics;
- **[GENERAL EVOLUTION]** — evolutionary semantics that do not assume biology;
- **[BIOLOGY]** — biological specialization;
- **[COMPOSITION]** — presets, experiments, interfaces, and other high-level
  assembly concerns.

The labels are pedagogical orientation aids, not import-linter declarations.

## Three-example progression

Use three increasingly rich examples throughout:

1. **Counter** — kernel only. No evolution, no biology. Proves execution mechanics.
2. **Information network** — kernel + general evolution. Persistent nodes carry
   transmissible strategy tokens that spread horizontally. Proves the evolution
   abstraction is not renamed biology.
3. **Biological simulation** — kernel + general evolution + biology. Use the
   repository's aging/reference examples and focused reproduction/genetics
   discussion to show specialization.

This progression should be revisited across chapters rather than used only once.

## Code presentation strategy

Use small real source snippets where a concept is introduced. Do not paste the
entire kernel verbatim into one appendix.

The source-reading chapter should nevertheless cover essentially all semantically
important kernel code. For each important file explain:

- the question the file answers;
- what the reader should already understand;
- public objects defined there;
- what to read first;
- what can be ignored on a first pass;
- architectural invariants the file protects;
- essential semantics versus validation/typing/performance support;
- how the file connects to the next file.

Heavily annotate at least one small, important method as training wheels. The
preferred target is `SequentialStepCoordinator.coordinate()` because it is short
and exposes the transaction boundary directly.

For `StageCoordinator`, explicitly separate:

```text
essential semantics
    propose -> resolve -> materialize-all -> apply

implementation support
    event dispatch cache
    cached materializer callable
    qualified type-name cache
    prepared-application tuple layout
    effect-journal plumbing
```

Include a deliberately simplified pedagogical mini-kernel so the production
implementation has a simple conceptual anchor.

## Navigation and ergonomics

The guide is a multi-page MkDocs textbook, not one giant document.

The landing page must support at least these entry paths:

- **First time learning the architecture**;
- **I want to understand the kernel now**;
- **I am reading code and I am lost**;
- **I want to understand reproduction/evolution**;
- **I want to practice**.

Use descriptive headings that work well with MkDocs search. Cross-link related
chapters, authoritative docs, source files, tests, and ADRs. At major transitions,
include a compact “where you are in the architecture” diagram.

Provide:

- a concept dependency graph;
- a master architecture/ownership diagram;
- terminology-family diagrams;
- file reading-order and difficulty guidance;
- a compact cheat sheet that remains useful months later.

Keep individual pages focused enough to scan. The guide should work both as a
front-to-back course and as a reference manual.

## Required textbook chapters

The durable content plan is:

1. **Start Here** — learning paths, dependency graph, master architecture map,
   source-of-truth warning.
2. **Software Architecture Primer** — abstraction, contracts/implementations,
   specialization/generalization, generic vs abstract vs concrete, composition,
   dependency direction/injection/inversion, layers/boundaries, coupling/cohesion,
   separation of concerns, orchestration, policies/adapters/capabilities, state
   vs configuration, mutability/transactions/determinism/side effects, telemetry,
   preflight, and construction/syntactic sugar where relevant.
3. **Simulation Fundamentals** — state-transition view, ordered stages,
   simultaneity, conflicts, stochasticity, authoritative/working state, commit,
   observation.
4. **General Evolution** — evolving entities, transmissible state, expression,
   realization, propagation, variation, linkage/co-transmission,
   persistence/removal, entity production, interaction/competition, selection,
   evolution.
5. **Biological Specialization** — complete mapping from general evolution to
   biology, including the participant/investor/genetic-contributor/production-
   source distinctions.
6. **Kernel Mental Model** — responsibilities/non-responsibilities,
   ownership/authority, object graph, minimum pedagogical kernel.
7. **Kernel Public API** — assembly/runtime API and extension protocols.
8. **Kernel Runtime** — exact call flow, transactions/RNG, stage phases,
   telemetry/effects, observers, commit semantics.
9. **Kernel Design Rationale and Invariants** — why not simpler designs; invariant
   catalog tied to tests and ADRs.
10. **Worked Examples Across the Layers** — counter -> nonbiological evolution ->
    biological example, with side-by-side comparison.
11. **Reading the Kernel Source** — guided file order, heavily annotated method,
    semantic vs optimization code, source-reading strategy.
12. **Debugger Labs** — breakpoints and state/RNG/event inspection.
13. **Exercises** — predictions, design comparisons, and a mini-kernel build.
14. **Glossary** — project-specific architecture/evolution vocabulary.
15. **Cheat Sheet** — printable quick-reference maps and invariants.

Split or combine pages only when doing so improves navigation without removing
substance.

## Current architecture that must remain accurate

The textbook must track stable current contracts, including:

- the frozen domain-neutral kernel;
- `SimulationState.domain_state` as an opaque copyable modeled payload;
- immutable `SimulationContext` shared across transactional copies;
- simulation-owned RNG stored in `SimulationState`;
- failed/discarded transactions leaving committed state and RNG unchanged;
- same-stage proposal simultaneity;
- `propose all -> resolve -> materialize all accepted -> apply`;
- resolvers choosing transitions while processes own domain mutation;
- unique process event types within one stage;
- `SimulationSpec` as the generic preflight/compilation boundary;
- committed `AppliedEvent` / `StepTelemetry` and optional opaque domain effects;
- non-mutating observation of committed state;
- `transmissible state` as canonical general-evolution vocabulary;
- expression, variation, propagation, linkage/co-transmission, production,
  access/reference, admission, and departure as distinct responsibilities;
- biological inheritance as a specialization of general propagation;
- selection as generally emergent differential contribution rather than a
  required intrinsic scalar;
- biological reproduction separating reproductive participants, proposal-time
  investors, materialization-time genetic contributors, and materialization-time
  offspring-production sources, while current defaults may choose all
  participants for each role.

Avoid volatile current ticket numbers or transient CI state in ordinary textbook
prose unless needed in historical/rationale context.

## Authority and maintenance

The textbook deliberately repeats authoritative material for teaching, but it
must never become the source of truth for public semantics.

Authority order remains:

1. current code/tests/CI;
2. `AGENTS.md`;
3. authoritative architecture/subsystem docs;
4. ADRs;
5. active Issue/PR for in-progress work;
6. learning textbook.

When a merged milestone materially changes a stable concept taught here, update
the affected chapter in the same or a closely related documentation change.
Do not churn the textbook for internal refactors that do not change what a learner
needs to understand.

Prefer links to authoritative docs/tests over duplicating precise low-level rules
that are likely to evolve. Avoid volatile SHAs in the textbook.

## Binary editions

Markdown in the repository is canonical for the textbook. DOCX or PDF editions
may be produced as derived offline artifacts when useful, but should not replace
the repository-native source or become the maintenance target.

## Quality checks

Documentation changes must pass the repository's strict MkDocs build. Manual
review should verify:

- learning paths are navigable;
- internal links work;
- diagrams remain readable in plain Markdown rendering;
- code snippets match current `main`;
- authoritative and pedagogical sources are clearly distinguished;
- chapter mastery criteria actually test reasoning rather than trivia.
