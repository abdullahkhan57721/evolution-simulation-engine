# Architectural Roadmap

This page answers **where the project is going** at the level of coherent
architectural milestones. It is a rolling planning aid, not an implementation-ticket
system.

## Authority and maintenance boundary

GitHub Issues remain authoritative for active scope, acceptance criteria, status, and
dependencies. Architecture/subsystem docs and ADRs remain authoritative for settled
contracts and rationale. Current `main`, tests, and CI override this roadmap whenever
they disagree.

Update this file only when milestone ordering or architectural direction materially
changes. Do not mirror every Issue, PR, commit, or CI result here.

## Guiding direction

The project should continue toward a simulation engine and scientific application in
which:

1. the frozen kernel provides domain-neutral deterministic transactional execution;
2. general-evolution abstractions remain free of unnecessary biological assumptions;
3. genetics, reproduction, development, ecology, and other modeled biology specialize
   those general contracts above the kernel;
4. observation and experiments consume committed evidence;
5. Study authoring compiles into existing typed/scenario composition rather than a
   second simulation architecture;
6. Workbench growth is incremental and use-case driven;
7. PySide6 + Qt Quick/QML is the product frontend over renderer-neutral/scientific
   contracts;
8. cinematic and interactive presentation remain downstream of scientific meaning;
9. the old Streamlit product surface is deprecated reference material, not a second
   frontend that must receive parity;
10. performance/native-backend work begins only from measured need.

The kernel is not the development frontier. New modeled behavior normally belongs
above it unless a genuine generic deficiency is demonstrated.

## Boundaries that remain fixed

Scientific evidence flows in one direction:

```text
modeled system
        ↓
committed state/events
        ↓
pure scientific measurement
        ↓
replicate outcome / treatment comparison
        ↓
scientific interpretation
        ↓
renderer-neutral presentation meaning
        ↓
interactive / cinematic rendering
```

A run/seed is the current stochastic experimental replicate unless a later concrete
design justifies another unit. Event step `t` aligns to committed state `t + 1`.
Extinction, censoring, denominator choice, discovery versus confirmation, and
representative storytelling remain explicit.

Renderer primitives, layout, accessibility, interaction, camera, timing,
interpolation, quality, output format, and desktop preferences remain presentation
concerns. Presentation interpolation is never scientific evidence.

## Completed scientific fronts

### B1–B3 flagship

The B-series established spatial resource geography, an inherited `max_speed`
benefit/cost axis, and a confirmed matched uniform-versus-compact selection study
without kernel changes or a scalar fitness field. Canonical B3 owns its representative
seed, bounded claim, counterbalance, radius sensitivity, and concrete cinematic
story. A radius-2 B3-derived fork preserves origin but not canonical validated
identity or headline-cinematic eligibility.

### E1–E7 controlled science

The completed controlled sequence is:

```text
E1 measurement/reproducibility
 → E2 controlled locomotion
 → E3 performance landscape
 → E4 selection on standing variation
 → E5 finite-population drift/weak selection
 → E6 rare-lineage invasion/candidate stability
 → E7 mutation-driven accessibility
```

E7's frozen assay is a negative convergence result. Do not post-hoc retune it. A
future E-series milestone must begin from a new predeclared scientific question and
identity; there is no automatic E8.

Potential future controlled questions include generational turnover, reproductive or
resource opportunity, richer inheritance/recombination, and changing ecology.

## Completed Workbench foundation: WB1–WB6

WB1–WB6 establish the first stable Workbench architecture:

```text
semantic intent / curated scenario / concrete experiment
        ↓
bounded recipe or experiment resolution
        ↓
immutable manifest / treatment specification
        ↓
existing typed/scenario composition + lower validation
        ↓
frozen kernel
        ↓
committed evidence + authoritative science
        ↓
Study-facing Results
        ↓
Presentation
```

Settled responsibilities include semantic authoring, immutable resolved meaning,
EvidencePlan persistence, exact reproduction compatibility, immutable lineage,
semantic diff, canonical B3 identity/origin, concrete E3/E4 experiment authoring,
bounded Reference Ecology Guided/Advanced authoring, Results association/navigation,
and small Workbench-owned diagnostics.

The Workbench foundation is now in maintenance-and-extension mode. New foundation
work should normally be earned by a concrete use case:

```text
add bounded recipe
or add a semantic choice to an existing recipe
or add evidence backed by an existing recorder
or add a concrete experiment pattern
or promote a support tier with evidence
or add a downstream result/presentation consumer
```

Preserve the support distinction:

```text
engine-valid ≠ Workbench-supported ≠ Guided ≠ experiment factor levels
```

Do not create a universal Study schema, migration engine, result hierarchy,
diagnostic conversion layer, experiment DSL, or statistics framework without
multiple real consumers demonstrating the same repeated responsibility.

## WU1–WU5 reference sequence

WU1–WU5 established the product semantics first:

```text
HOME
├── New Study
└── Open Study

STUDY
├── Simulation
├── Evidence
├── Experiment
├── Results
└── Presentation

Run = action
```

They proved concrete family routing, exact persistence, semantic authoring,
Guided/Advanced disclosure, immutable fork lineage, semantic diff, readiness,
reviewable Run Plan, family-specific Results, Reference Ecology replay, B3 matched
replay, Focus Mode, and the existing B3 cinematic handoff.

Q5 now closes the migration decision: this sophisticated Streamlit implementation is
deprecated and frozen as regression/reference material. It should receive no new
product features and future milestones do not owe it parity. Physical removal is a
bounded maintenance task after a human native release audit confirms the replacement
product and any remaining compatibility value is deliberately migrated or discarded.

## Native desktop sequence: Q0–Q5

ADR 0010 establishes the product boundary:

```text
Qt Quick / QML
        ↓
curated PySide6 controllers + explicit Qt item models
        ↓
existing Workbench/application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

There is no Qt-specific Study schema, IPC backend, generic form system, native
scientific-analysis layer, or QML-owned scientific identity.

### Q0 — architecture proof (completed)

Proved native launch, exact Reference Ecology persistence/fork/run/result/world,
synchronous Workbench execution off the GUI thread, optional PySide6 dependency
direction, and standalone packaging/launch smoke.

### Q1 — Study shell and concrete routing (completed)

Established Home/New/Open, the persistent five-section shell, `ApplicationController`,
exact five-family routing, failure-atomic Open/Save, active-owner reset semantics,
and curated QML properties/signals/slots/item models.

### Q2 — Simulation, Evidence, Experiment authoring (completed)

Added only supported controlled and Reference authoring, existing evidence-plan
choices, E3/E4 experiment editing, B3 read-only meaning plus radius-2 fork, and
family-specific thin controllers. No reflection-driven form system or generic
experiment abstraction was introduced.

### Q3 — Run and Results breadth (completed)

Added atomic pre-run binding, reviewable Run Plans, one narrow off-GUI execution
adapter for the five existing runners, exact result/provenance association,
family-specific native Results, missing-evidence honesty, and historical-provenance
limitations.

### Q4 — native scientific-world Presentation (completed)

Made `WorldPresentationFrame` the authoritative native world contract. Reference
Ecology has native bounds/organisms/resources/carcasses/trails/labels/legend/
inspector/timeline/playback/Focus Mode. Canonical B3 has side-by-side matched replay
with a shared science-owned trait scale and common committed step. Adjacent
stable-identity interpolation is display-only; non-adjacent or identity-changing
transitions snap to evidence.

Q4 also established repeatable offscreen renderer evidence. No custom
C++/OpenGL/shader/scene-graph renderer was justified.

### Q5 — product integration, accessibility, cinematic, frontend decision (completed)

Q5 turns Q0–Q4 into the primary desktop product without changing scientific
ownership. It establishes:

- responsive desktop composition and hardened visual/accessibility semantics;
- keyboard/focus behavior plus native New/Open/Save/Save As/Run/Home/back/Focus/
  playback commands;
- end-to-end five-family workflow/error-state integration;
- canonical B3 cinematic integration through the existing exact path:

  ```text
  B3 revision + authoritative result
          ↓
  prepare_b3_workbench_cinematic()
          ↓
  existing B3 director
          ↓
  optional renderer
  ```

- renderer availability separate from scientific story eligibility;
- expensive cinematic rendering off the GUI thread;
- quality/output/location strictly presentation-only;
- canonical-headline rejection for radius-2 B3-derived forks;
- explicit WU1–WU5 parity review and **Option B** retirement decision: Qt is the one
  product frontend; Streamlit is deprecated reference code.

See `docs/development/q5_frontend_parity.md`, `docs/desktop_workbench.md`, and
`docs/q4_native_presentation.md`.

## Post-Q5 product direction

There is no automatic Q6 feature milestone. The frontend migration itself is no
longer the development program. The next product work should come from concrete
release/use evidence.

### Human native release audit

Before deleting the deprecated Streamlit surface or claiming release-quality human
accessibility, actually use the native application on supported desktop hardware and
exercise at least:

- keyboard navigation and visible focus order;
- screen-reader/accessibility metadata where supported;
- OS/application font scaling and high-density text;
- contrast and color-vision-safe scientific distinctions;
- live resize across laptop and large displays;
- controlled and Reference Studies;
- E3 and E4 authoring/results;
- canonical B3 and radius-2 fork behavior;
- missing-evidence remediation;
- exact Save/Open/reproduce/fork lineage;
- Reference and paired-B3 native worlds;
- a real canonical B3 film when the optional renderer is installed.

Offscreen CI, screenshot proof, standalone build, and packaged launch smoke are useful
automated evidence but are not this human audit.

### Distribution only from a shipping requirement

Signing, notarization, platform installers, auto-update, and a broader release matrix
should be added only when a real distribution target requires them. They are not
architecture prerequisites for simulation/scientific work.

### Streamlit physical removal

After the human native audit, remove or reduce `evo_engine.ui`, Plotly, and Streamlit
in one bounded maintenance change. First identify any regression/reference tests that
still provide unique value and either move that value to frontend-neutral/native
tests or deliberately drop it. Do not resume feature development in the deprecated
frontend during this window.

## Longer-term modeled fronts

### Richer genetic expression

Potential directions include incomplete dominance, codominance, epistasis,
dosage-sensitive expression, and richer quantitative architecture. Preserve:

```text
genome
  ↓
genetic expression
  ↓
genetic phenotype
  ↓
development/environment-dependent realization
  ↓
current physiological state
```

### Richer chromosome pairing and recombination

Current responsibilities already separate copy structure, pairing, recombination
eligibility, segregation, and gamete formation. Higher-copy pairing, multivalents,
chromosome-specific crossover behavior, or multiple crossovers belong in biology,
not the kernel/general propagation vocabulary.

### Richer mating systems

Reproduction already separates participants, investors, genetic contributors, and
production sources. Future cases may explore ordered/asymmetric roles,
multi-participant groups, hermaphroditic systems, and role-sensitive choice without
collapsing mating-system composition into inheritance.

### Richer development and G×E

Potential directions include nonlinear reaction norms, developmental history/stages,
richer stochasticity, and reversible adult plasticity. Preserve inheritance,
expression, development, environment, and mutable physiological state as separate
responsibilities.

### Richer evolutionary ecology

Potential directions include resource competition, movement/behavior tradeoffs,
predation/prey coevolution, life-history tradeoffs, spatial population structure, and
fluctuating/heterogeneous selection. Selection should continue to emerge from
differential persistence/propagation rather than a kernel-owned scalar fitness field.

## Observation and statistical analysis

E1–E7 provide real scientific consumers without earning a broad statistics
framework. Promote reusable statistical contracts only after repeated concrete
experiment patterns show what actually repeats. Undefined post-extinction quantities
remain undefined rather than silently becoming zero.

## Performance and future native execution backend

A Rust/C++ execution backend remains evidence-driven future work. If profiling
eventually justifies it, preserve Python modeling/configuration and compile a
validated stable subset to a backend boundary with Python remaining a reference
implementation. Likewise, do not create a custom native renderer before measured Qt
Quick limitations demonstrate a real need.

## Architectural constraints that should survive future work

- Preserve the frozen transactional kernel unless a true generic deficiency appears.
- Preserve simulation-owned RNG and materialize-before-apply semantics.
- Preserve domain-neutral general-evolution vocabulary.
- Keep chromosome structure, pairing, recombination, and segregation separate.
- Keep reproduction participants, investors, contributors, and production sources
  separate.
- Keep genetic expression, development, environment, and current state separate.
- Keep scientific measurement downstream of committed evidence.
- Keep presentation downstream of scientific meaning; interpolation is never
  evidence.
- Keep Workbench above existing typed/scenario composition and lower validation.
- Keep persisted values separate from mutable runtime graphs.
- Preserve scenario origin separately from validated scenario identity.
- Preserve factor identity separately from implementation paths and counterbalancing.
- Normalize inapplicable authoring state before persistence.
- Keep scientific manifests renderer-neutral.
- Keep QML behind curated Qt properties/signals/slots/item models.
- Keep PySide6 optional and downstream of the core engine.
- Allow UI/cinematic to consume Workbench while preventing reverse dependencies.
- Treat Streamlit as deprecated reference code, not a second product surface.
- Prefer readable maintainable architecture over micro-optimization.
- Require evidence before performance/backend work.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier work changed assumptions in this roadmap;
3. start from a concrete modeled, scientific, product, or release use case;
4. settle consequential public architecture before architecture-sensitive execution;
5. create one focused Issue with boundaries, traps, acceptance criteria, tests, and
   manual verification where material;
6. apply `docs/development/validation_workflow.md` rather than stale milestone-local
   validation instructions;
7. update this roadmap only when ordering or architectural direction materially
   changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change it.
