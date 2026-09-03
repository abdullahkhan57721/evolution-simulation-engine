# Evolution Simulation Engine Learning Textbook — Guide Specification

This file is the durable design brief for the repository-native textbook. It
exists so the guide's audience, pedagogy, scope, and maintenance rules survive
chat/session boundaries.

The textbook is **pedagogical, not authoritative**. Current code/tests/CI,
`AGENTS.md`, authoritative architecture/subsystem documentation, and ADRs outrank
this guide. The canonical kernel semantics live in
[`docs/kernel_contract.md`](../../kernel_contract.md), and the canonical abstract
evolution model lives in
[`docs/general_evolution_framework.md`](../../general_evolution_framework.md).

## Audience

Assume the reader already understands:

- Python classes, instances, methods, properties, references, and mutation;
- modules/packages/imports;
- ordinary annotations, interfaces, and the basic purpose of `Protocol`.

Do not turn the guide into a beginner Python course. Explain language features
only when their architectural role is easy to misread: positional-only `/`,
keyword-only `*`, `attrs.frozen`, variance when it materially clarifies a
contract, decorators, and the distinction between literal syntactic sugar and
API/construction convenience.

## Final learning goal

After the textbook, the reader should be able to open unfamiliar engine code and:

1. identify the owning architectural layer and responsibility;
2. explain why the abstraction exists and what failure mode it prevents;
3. predict state visibility, mutation, RNG, commit, and observation semantics;
4. identify the invariant and focused tests that protect it;
5. reason about time complexity, memory growth, memory lifetime, and frequency;
6. distinguish asymptotic reasoning from measured profiling/benchmark evidence;
7. evaluate readability, maintainability, extensibility, testability, coupling,
   and cohesion rather than reducing review to correctness alone; and
8. decide whether a proposed change fits an existing contract or demonstrates a
   genuine lower-layer deficiency.

The desired capability ladder is:

```text
RECOGNIZE -> EXPLAIN -> PREDICT -> DIAGNOSE -> DESIGN
```

## Core pedagogical sequence

Use this pattern repeatedly:

```text
problem
  -> naive design
  -> failure mode
  -> abstraction needed
  -> public contract
  -> production implementation
  -> domain example
  -> focused test/invariant
  -> engineering analysis
```

Architecture should feel derived from requirements rather than decorative.

## Teaching principles

### Mental models before terminology

Start with the problem and conceptual picture. Introduce formal vocabulary only
after the reader has something meaningful to attach it to.

### Progressive disclosure

Teach important mechanisms in layers:

```text
plain-language concept
    -> pseudocode/diagram
    -> small real source snippet
    -> complete production flow
    -> validation/typing/telemetry/performance plumbing
```

Do not let incidental implementation complexity hide the semantic core.

### Spiral learning

Revisit major ideas at increasing depth rather than defining them once:

- transaction: work on a copy -> state + RNG rollback -> performance tradeoff;
- simultaneity: avoid order dependence -> exact materialize-before-apply rule;
- propagation: state transfer -> generic evolutionary contract -> inheritance;
- ownership: containment -> responsibility -> authority -> mutation rights;
- performance: Big-O -> frequency/memory -> profile evidence -> design tradeoff.

### Abstraction ladders

Frequently move from general to specialized to concrete:

```text
state transition
    -> transmissible-state propagation
        -> biological inheritance
            -> Mendelian sexual inheritance
                -> one configured simulation
```

### Concept-to-code and code-to-concept maps

Teach both directions. Examples:

```text
transaction envelope -> SimulationState
stage simultaneity    -> StageCoordinator
conflict policy       -> Resolver
```

and:

```text
simulation_state.copy() -> transaction boundary
resolve_events(...)     -> selection, not domain mutation
materialize_event(...)  -> accepted-only deferred consequence
apply_event(...)        -> process-owned domain mutation
```

### Contrast learning and misconception checks

Use paired comparisons for concepts that are easy to collapse mentally:

- state vs context;
- resolver vs process;
- proposal vs resolved vs materialized event vs `AppliedEvent`;
- propagation vs production;
- genetic expression vs developmental realization vs current physiology;
- participant vs investor vs genetic contributor vs production source;
- selection vs a stored scalar named fitness;
- Big-O vs profiling vs benchmarking;
- architectural importance vs computational hotness.

### Invariant-centered source reading

For important invariants provide:

```text
invariant
why it exists
implementation location
focused test
failure if violated
```

Teach the professional reading loop:

```text
public contract -> focused test -> semantic implementation -> support plumbing
```

### Prediction, retrieval, and fading scaffolds

Readers should predict before running the debugger and commit to an answer before
opening hints. Early source walkthroughs may be heavily annotated; later exercises
remove scaffolding. The cheat sheet supports delayed retrieval, not passive
replacement of deeper chapters.

### Wrong-but-plausible examples

Use designs a competent programmer might reasonably propose, then review them.
Examples include resolver mutation, independent simulation RNGs, accepted-detail
randomness during rejected proposals, observer-as-repair, domain fields on generic
kernel state, and tiny optimization fast paths that duplicate semantic algorithms.

### Tests as teaching material

Tests are executable explanations. The textbook should connect concepts to the
focused tests that establish observable semantics.

## Engineering-analysis framework

The textbook should analyze important code through all of these lenses:

```text
correctness
semantic fidelity
time complexity
memory size and lifetime
execution frequency
measured performance
readability
maintainability
extensibility
testability
coupling/cohesion
```

Do not put mechanical Big-O comments beside every line. Use structured review
cards after meaningful algorithms.

### Complexity discipline

Define scale variables before assigning a complexity class. Preserve delegated
costs rather than hiding them. For example:

```text
SimulationState.copy()
time  = C_domain_copy(N) + fixed kernel overhead
space = M_domain_copy(N) + fixed kernel overhead
```

and for a stage:

```text
kernel structural work
+ proposal algorithm costs
+ resolver cost
+ accepted materialization costs
+ application costs
+ telemetry/effect costs
```

### Memory discipline

Record both growth and lifetime:

```text
persistent domain state       whole run
transactional state copy      one step
proposal/preparation buffers  one stage
retained observation history  potentially whole experiment
```

### Performance discipline

Reason about scaling early, but optimize implementation details only with evidence.
Distinguish:

```text
complexity analysis  -> scaling model
profiling            -> where one run spent time
benchmarking         -> controlled before/after speed
tracemalloc          -> Python allocation/peak-memory evidence
```

Respect the project's measurement-first rule and ADR 0004: semantic correctness,
readability, and maintainability are hard constraints on performance work.

Classify optimizations by risk:

```text
structurally safe
semantics-sensitive
architecture-changing
```

The evidence bar rises across those categories.

## Architecture-quality framework

Readability should be discussed concretely through control-flow locality, naming,
cognitive load, branching, hidden dependencies, cause/effect distance, and
abstraction fit.

Maintainability should be discussed through duplicate policy, parallel semantic
paths, public change radius, explicit dependencies, test localization, and number
of invariants future changes must preserve.

Extensibility means demonstrated axes of variation can change behind stable
contracts; it does **not** mean making every concept maximally generic.

Testability is both a quality and an architecture signal: if a responsibility
cannot be tested without constructing half the application, investigate whether
it is overly entangled.

## Three-example progression

Use three levels throughout:

1. **Counter** — kernel only; proves generic execution mechanics.
2. **Information network** — kernel + general evolution; proves evolution without
   biology.
3. **Biological simulation** — kernel + general evolution + biology; proves
   specialization.

## Source-code strategy

Use small real snippets in conceptual chapters. Do not paste the entire kernel as
one source dump.

The source-reading chapter should cover essentially all semantically important
kernel files in a human reading order. For each file explain:

- the question it answers;
- what to read first;
- what to postpone;
- invariants protected;
- essential semantics vs validation/typing/performance support;
- how it connects to the next file.

Fully annotate `SequentialStepCoordinator.coordinate()` as training wheels.
For `StageCoordinator`, explicitly distinguish:

```text
essential semantics
    propose -> resolve -> materialize-all -> apply

support/optimization
    event dispatch cache
    cached materializer callable
    type-name cache
    prepared-application representation
    effect-journal plumbing
```

## Practice design

Practice should emphasize prediction, comparison, review, and construction rather
than trivia. Include:

- debugger labs;
- architecture/state/RNG exercises;
- complexity and memory exercises;
- a 100–150 line pedagogical mini-kernel;
- tests written from invariants;
- code/PR review exercises;
- change-reasoning and performance-review worksheets;
- delayed retrieval;
- capstones requiring independent design judgment.

The capstones should include:

1. explain the kernel without class names;
2. derive a minimal kernel from requirements;
3. review a deliberately flawed feature across architecture, correctness,
   complexity, memory, performance, and quality;
4. review a performance proposal that targets the wrong layer.

## Architecture smells and healthy counterpatterns

The reference should include project-relevant smells such as biology leakage, god
processes, hidden dependencies, order-dependent science, duplicated policy,
boolean/special-case explosion, premature generalization, fast-path explosion,
observer-as-repair, resolver mutation, hidden stochasticity, and telemetry-as-state.

Smells are prompts to investigate, not automatic verdicts.

## Navigation and ergonomics

The textbook is multi-page and searchable. The primary MkDocs sidebar should
contain only canonical curriculum/reference pages, not design scratch notes.

The landing page should support multiple entry paths: first-time course, kernel
fast path, evolution/reproduction, performance, source-reading rescue, PR review,
and practice.

Each major chapter should, where useful, follow this rhythm:

```text
where you are
why it matters
mental model
problem / naive design
concepts and contrasts
pseudocode / real implementation
tests and invariants
engineering analysis
prediction/retrieval prompt
mastery criteria
next chapter
```

Use compact tables and diagrams where they improve scanning. Avoid one enormous
linear document.

## Canonical chapter set

Keep the durable guide small enough to navigate. The canonical pages are:

- `index.md`
- `architecture_primer.md`
- `architecture_quality.md`
- `computational_complexity.md`
- `simulation_fundamentals.md`
- `general_evolution.md`
- `biological_specialization.md`
- `kernel_mental_model.md`
- `kernel_public_api.md`
- `kernel_runtime.md`
- `kernel_design_rationale.md`
- `architecture_evolution.md`
- `kernel_engineering_anatomy.md`
- `performance_case_studies.md`
- `worked_examples.md`
- `source_code_walkthrough.md`
- `debugger_labs.md`
- `exercises.md`
- `complexity_exercises.md`
- `change_reasoning.md`
- `review_workflows.md`
- `capstones.md`
- `design_smells_reference.md`
- `glossary.md`
- `cheatsheet.md`
- this `guide_spec.md`

Do not retain dozens of tiny design/checklist pages when their durable value can
be represented in these canonical chapters.

## Stable architecture content

The textbook must remain accurate about:

- frozen domain-neutral kernel;
- opaque copyable `SimulationState.domain_state`;
- immutable shared `SimulationContext`;
- simulation-owned transactional RNG in `SimulationState`;
- failed/discarded transactions not advancing committed state or RNG;
- same-stage proposal simultaneity;
- `propose -> resolve -> materialize-all-accepted -> apply`;
- resolver chooses while process owns domain mutation;
- unique process proposal event types per stage;
- `SimulationSpec` as generic preflight/compilation boundary;
- committed `AppliedEvent` / `StepTelemetry` and optional opaque effects;
- non-mutating observation of committed state;
- `transmissible state` as canonical general-evolution vocabulary;
- expression, variation, propagation, linkage, production, access/reference,
  admission, and departure as distinct generic responsibilities;
- inheritance as a biological specialization of propagation;
- selection as usually emergent differential future contribution;
- reproduction separation among participants, proposal-time investors,
  materialization-time genetic contributors, and materialization-time production
  sources.

Avoid transient CI states and volatile commit SHAs in textbook prose.

## Authority and maintenance

Authority order remains:

1. current code/tests/CI;
2. `AGENTS.md`;
3. authoritative architecture/subsystem docs;
4. ADRs;
5. active Issue/PR for in-progress work;
6. textbook.

Update the textbook when a merged milestone materially changes a stable concept it
teaches. Do not churn it for internal refactors that do not alter what a learner
needs to understand.

Markdown in the repository is canonical. DOCX/PDF editions may be derived later
but should never become the maintenance source.

## Scope boundary and stop rule

Do **not** expand this textbook into:

- a full Python tutorial;
- a full algorithms/data-structures course;
- a comprehensive design-pattern catalog;
- a CPython/CPU/cache performance manual;
- a line-by-line dump of every source file;
- a changelog of every historical PR.

The pedagogical design is mature. Add future material only when repository changes
or observed learner difficulty reveal a concrete gap.

## Quality gate

The textbook must pass the repository's strict MkDocs build and normal protected
quality gate. Manual review should confirm navigation is coherent, internal/source
links are useful, diagrams remain readable, snippets match current source, early
chapters provide more scaffolding than later practice, and the cheat sheet supports
retrieval rather than replacing understanding.