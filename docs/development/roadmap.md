# Architectural Roadmap

This page answers **where the project is going** at the level of coherent
architectural milestones. It is a rolling planning aid, not an implementation
ticket system.

## Authority and maintenance boundary

GitHub Issues remain authoritative for active scope, acceptance criteria, status,
and dependencies. Architecture/subsystem docs and ADRs remain authoritative for
settled contracts and rationale.

Update this roadmap only when milestone ordering or architectural direction
materially changes. Do not mirror every Issue, PR, commit, or CI result here.

## Guiding direction

The project should continue toward a simulation engine and scientific application in
which:

1. the frozen kernel provides domain-neutral deterministic transactional execution;
2. the general-evolution layer expresses evolution without assuming biology;
3. genetics, reproduction, development, and ecology specialize those settled
   general contracts;
4. richer modeled biology is added against explicit public responsibilities rather
   than by broadening lower layers speculatively;
5. observation, experiments, and presentation remain downstream of committed
   simulation evidence;
6. scientific-study authoring compiles down into existing typed/scenario
   composition rather than becoming a second simulation architecture;
7. Workbench foundation growth is incremental and use-case driven;
8. the primary product UI is a native PySide6 + Qt Quick/QML application over those
   existing Workbench contracts;
9. Streamlit remains a reference frontend during native migration rather than a
   second scientific authority;
10. performance/native-execution-backend work begins only from measured need.

The kernel is not the development frontier. New modeled behavior normally belongs
above it unless a genuine generic deficiency is demonstrated.

## Stable scientific and presentation boundaries

The durable evidence path is:

```text
modeled system
        ↓
committed state / committed events
        ↓
pure scientific measurement
        ↓
replicate outcome
        ↓
treatment comparison
        ↓
experiment-level reporting / scientific meaning
        ↓
presentation
```

One simulation run/seed is the current stochastic experimental replicate. Event
step `t` aligns to committed state `t + 1`; denominators, extinction,
right-censoring, discovery versus confirmation, and representative storytelling
remain explicit.

Presentation branches by medium only after scientific meaning:

```text
committed scientific evidence
        ↓
scenario-specific scientific meaning
        ↓
   +--------+---------+
   |                  |
   v                  v
native interactive  cinematic
```

Renderer primitives, layout, interaction, camera, timing, interpolation, and
choreography remain downstream. Presentation interpolation is never scientific
evidence.

## Completed scientific flagship sequence

The B-series flagship established a robust environment-dependent selection story
without kernel changes or scalar fitness:

```text
B1 spatial resource geography
        ↓
B2 inherited max_speed benefit/cost axis
        ↓
B3 matched uniform-versus-compact selection study
        ↓
independent confirmation + mechanism + sensitivity
        ↓
renderer-neutral B3 scientific handoff
        ↓
concrete B3 flagship cinematic director
```

Canonical B3 remains the richer integrated reference-ecology demonstration. Its
representative run, bounded claim, counterbalance, and sensitivity are selected and
interpreted by science rather than by UI/cinematic code. A B3-derived radius-2 fork
retains scenario origin but not canonical validated identity.

## Completed E1–E7 controlled-science sequence

A deliberately simpler controlled program isolates causal mechanics:

```text
E1 experimental-science foundation
        ↓
E2 minimal clonal locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
        ↓
E6 rare-lineage invasion and candidate stability
        ↓
E7 mutation-driven adaptation and convergence
```

The sequence establishes a causal chain from locomotion mechanics through
performance, standing-variation selection, finite-population stochasticity, bounded
reciprocal rare-lineage invasion, and finally mutation-driven accessibility. It
remains separate from B3 and does not authorize universal
fitness/statistics/population-genetics abstractions.

E7 is an important negative result. Under the frozen 60-step focal-only `±1`
mutation assay, independent low/near/high starting populations do **not** converge
toward a shared distribution around speeds 2..4. Start 3 remains bounded in that
region; start 1 develops upward descendants but also substantial speed-0 boundary
accumulation; start 7 repeatedly creates speed-6/8 descendants that do not reproduce
and therefore cannot propagate further mutational steps toward the reference
region. Future science should preserve this result rather than post-hoc retuning E7
until convergence appears.

## Completed Workbench foundation: WB1–WB6

WB1–WB6 establish and review the first complete Evolution Experiment Workbench
architecture:

```text
semantic Study / curated scenario / concrete experiment definition
        ↓
bounded recipe or experiment-pattern resolution
        ↓
immutable manifest / treatment specification
        ↓
existing typed/scenario composition
        ↓
authoritative lower validation / preflight
        ↓
frozen kernel
        ↓
committed evidence + existing scientific results
        ↓
Study-facing Results navigation
        ↓
interactive / cinematic Presentation
```

### What is settled

- WB1 established bounded semantic authoring, immutable manifest meaning,
  EvidencePlan persistence, exact compatibility-aware reproduction, run provenance,
  immutable fork lineage, and recipe-scoped semantic diff.
- WB2 pressure-tested those contracts against canonical B3 and established scenario
  origin versus validated scenario identity.
- WB3 added concrete E3/E4 experiment authoring while keeping factor, treatment,
  counterbalance, replicate, and measurement distinct.
- WB4 added richer bounded reference-ecology authoring with explicit
  Guided/Advanced/Expert/Extension support, recipe-local applicability and
  normalization, and concrete evidence options.
- WB5 added Results navigation and downstream V2/V3 presentation integration without
  a universal result/presentation framework.
- WB6 audited the complete implementation and promoted only one genuinely repeated
  responsibility: a small Workbench-owned diagnostic value.

The final review is in `docs/workbench_architecture_review.md`.

## Workbench direction after WB6

The Workbench foundation is in **maintenance-and-extension mode**. Future foundation
changes should normally begin from a real scientific/product use case and take one of
these forms:

```text
add bounded recipe
or
add semantic choice to an existing recipe
or
add evidence option backed by an existing recorder
or
add concrete experiment pattern
or
promote a support tier with evidence
or
add a downstream result/presentation consumer
```

A new shared abstraction should require repeated consumers demonstrating the same
responsibility. Architecture redesign is no longer the default milestone shape.

### Support boundary that must remain explicit

```text
engine-valid
    ≠ Workbench-supported
    ≠ Guided
    ≠ experiment factor levels
```

The current bounded reference-ecology recipe keeps its existing tier assignment:
Guided stable core; Advanced selected richer movement/resource/mutation/
recombination controls; Expert empty; arbitrary policy/genetics/inheritance/
reproduction/lifecycle/development composition Extension/Internal. No support tier
is promoted merely because lower engine validators allow broader values.

### Diagnostics boundary

Workbench diagnostics cover only Workbench-owned support/status facts demonstrated
by real workflows. Lower validators remain authoritative:

- `DependencyReport` + `SimulationSpecValidator` for generic preflight;
- `BiologicalSimulationSpec` for biological preflight;
- `GeneticArchitecture` for genetic coherence;
- concrete experiment integrity checks for scientific treatment validity.

Do not create a universal diagnostic conversion layer or parse arbitrary exception
prose into Workbench semantics.

### Persistence and migration boundary

Exact reproduction continues to mean stored immutable manifest plus compatible
recipe/compiler/software identity. It does not mean re-resolving old intent under
current defaults.

No migration engine is currently justified. If future saved-study incompatibility
creates a real migration need, migration must create new scientific identity rather
than masquerade as exact reproduction.

## Completed Streamlit reference sequence: WU1–WU5

WU1–WU5 established the concrete product semantics before the native technology
choice was frozen:

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

The Streamlit reference product proves concrete Study-family routing, exact
persistence, semantic authoring, Guided/Advanced disclosure, immutable revisions and
forks, semantic diff, readiness, reviewable Run Plan, exact execution/result
ownership, family-specific Results, Reference Ecology world replay, B3 matched replay,
Focus Mode, and the B3 cinematic handoff. It remains a compatibility oracle during
native migration.

The earlier WU6 concept—product hardening, accessibility, visual completion, and
release readiness—remains a valid set of product concerns, but **is no longer the
primary next milestone**. Those concerns should be applied to the native application
once enough Q-series breadth exists to harden the product that will actually ship.
Streamlit should not receive a parallel final-product polish program unless a future
concrete need justifies it.

## Native desktop product sequence

ADR 0010 establishes PySide6 + Qt Quick/QML as the primary Workbench frontend. The
architecture remains:

```text
Qt Quick / QML
        ↓
curated PySide6 controller / item-model boundary
        ↓
existing Workbench/application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

There is no Qt-specific Study schema, IPC backend, generic QML form system, or native
scientific-analysis layer.

### Q0 — desktop architecture and vertical slice

Q0 is the technology-decision proof. Reference Ecology provides the deep vertical
because existing Workbench contracts already own its exact revision persistence,
fork semantics, authoritative Results, and recorded spatial evidence.

Q0 proves:

- native application launch;
- create/open of an exact existing `ReferenceStudyRevision`;
- one semantic edit with Workbench-owned explicit/derived meaning;
- immutable child revision creation through the existing fork API;
- exact synchronous Workbench execution off the GUI thread through a narrow Qt
  worker;
- one authoritative existing Results value;
- `WorldPresentationFrame` preparation from recorded evidence and native QML world
  rendering;
- optional PySide6 dependency direction;
- standalone deployment through Qt for Python tooling with packaged launch smoke.

The shared Workbench world-presentation adapter is frontend-neutral and moves to the
presentation layer only because Streamlit and Qt are now two real consumers.

### Q1 — native Study shell and concrete routing (completed)

Q1 turns the Q0 proof into the persistent native Workbench application shell:

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

Q1 establishes:

1. native Home/New/Open routing plus the persistent five-section Study shell;
2. an application-level `ApplicationController` that owns transient route, active
   concrete artifact, section, current-session result, Run Plan placeholder,
   presentation owner/reset state, file location, and status only;
3. exact routing for the existing five-family support envelope through the owning
   concrete Workbench constructors, format/pattern identities, loaders, and
   serializers rather than a universal persistence envelope;
4. failure-atomic Open/Save behavior and explicit exact-reproduction diagnostics;
5. active-owner reset semantics: successful scientific replacement/fork/immutable
   child commit clears stale result, Run Plan, presentation, and family transient
   state, while section navigation cannot mutate science;
6. non-destructive Open from an already-active Study: the native file dialog operates
   over the Study route so cancellation or failed/unknown/incompatible Open leaves the
   exact owner accessible;
7. the retained Q0 Reference Ecology edit/immutable-child/run/result/world path as a
   family-specific child controller rather than a universal desktop authoring model;
8. a curated QML scalar/property/signal/slot/item-model boundary, with typed Python
   helpers for controller-to-controller state;
9. reusable native shell/navigation/panel/button/field/diagnostic/badge/disclosure
   primitives earned by the real shell;
10. continued Streamlit semantic compatibility and standalone native deployment
    proof without broadening into signing/installers/release-matrix work.

The exact Q1 boundary and downstream interfaces are in `docs/desktop_workbench.md`.

### Q2 — Native Simulation, Evidence, and Experiment authoring (completed)

Q2 intentionally combines the previously separate Simulation and
Evidence/Experiment authoring fronts because one coherent product task owns the full
pre-execution scientific Study definition. It reuses the Q1 application shell, exact
artifact routing, active-owner/reset semantics, and family-controller seam rather
than redesigning them.

Q2 establishes:

1. controlled-locomotion Simulation authoring for only maximum speed, resource
   geography, and seed, with existing readiness, immutable child revision, and
   semantic-diff contracts;
2. bounded Reference Ecology Guided/Advanced authoring using WB4 applicability and
   transient reconciliation, with Expert still empty and Extension/Internal still
   non-authorable;
3. inspectable selected, derived, and frozen recipe meaning through curated Qt item
   models rather than Python object dumps;
4. canonical B3 read-only Simulation semantics plus only the existing radius-2
   sensitivity fork and explicit validated-identity loss;
5. controlled/reference Evidence authoring through only the existing concrete
   EvidencePlan types and immutable child revisions, while required B3/E3/E4 evidence
   remains locked and missing-evidence implications stay explicit;
6. concrete E3 level/seed and E4 seed editing with authoritative Workbench expansion
   rows preserving factor, role, standing-composition, and counterbalance semantics;
7. curated/read-only B3 Experiment case counts and explicit controlled/reference
   single-run semantics rather than a generic experiment definition;
8. thin `SimulationAuthoringController`, `EvidenceAuthoringController`, and
   `ExperimentAuthoringController` seams plus Reference-specific authoring retained in
   `ReferenceStudyController`;
9. application-level stale result, Run Plan, and presentation reset on scientific
   draft/owner changes while section navigation remains scientifically inert; and
10. native QML authoring views and read-only Qt item models without a universal Study
    schema, reflection-driven form system, generic experiment DSL, or QML-owned
    scientific validation.

### Q3 — execution and Results breadth

Q3 should broaden execution and Results beyond the retained Q0/Q2 Reference path
using only existing concrete Workbench runners, result inspectors, provenance, and
WB5 association rules. Result binding must continue to require exact active-owner
compatibility, and missing evidence must remain unavailable rather than reconstructed.

Add family-specific Qt item models/view models only where concrete Results consumers
need them. Do not flatten heterogeneous controlled/E3/E4/B3/Reference results into a
universal result or statistics model. Preserve the Q2 authoring-draft rule: Run must
operate on exact saved scientific ownership, with pending revision-backed edits
committed through their existing immutable contracts before execution rather than
mutating saved science in place.

### Later native product direction

After Q3, expand Presentation from recorded evidence: broader Reference world
exploration, canonical B3 matched replay and existing cinematic handoff, then native
accessibility, visual completion, packaging/release hardening, and an explicit
Streamlit parity/removal decision when justified.

Do not predeclare a large generic Qt application framework. Each later Q milestone
should earn shared controller/view-model helpers only after multiple concrete native
consumers demonstrate the same responsibility.

The Q-series does **not** authorize:

- a universal Study schema;
- a generic experiment DSL or statistics framework;
- reflection-driven policy/form introspection;
- a universal scene/camera DSL;
- QML-owned scientific identity or analysis;
- a generic background-job/cancellation framework before concrete needs exist;
- native 3D/C++ rendering without evidence;
- Streamlit removal before an explicit parity/removal decision.

## Controlled-science direction after E7

E7 closes the first planned E-series causal sequence. There is no automatic E8. The
next controlled-science milestone should be chosen only after reassessing the new
unresolved mechanism rather than assuming the previous hypothesis was supposed to
succeed.

Potential future questions include:

- whether longer **generational turnover**, rather than merely more simulation
  steps, changes mutational accessibility;
- how reproductive opportunity and resource renewal alter the ability of
  intermediate mutants to propagate;
- whether richer genetic architectures or recombination change accessibility;
- how temporal or spatial environmental change reshapes the locally favored region;
- whether repeated independent consumers now justify any small reusable analysis
  contract beyond the current experiment-specific measurements.

Those are new experiments with new scientific identities. They must use their own
discovery/freeze/confirmation protocols rather than changing E7 after seeing its
confirmed negative result.

A later product milestone may expose E7 through a concrete Workbench experiment
pattern, but the Workbench should consume the settled E7 science rather than become
a dependency of it.

## Presentation continuation

The presentation direction now has two interactive consumers of shared
renderer-neutral meaning: the Streamlit reference frontend and the native QML product.
Both must preserve:

- exact Study/run/treatment/replicate identity;
- B3 control/treatment semantics;
- fixed shared scientific trait scales;
- matched committed timestep convention;
- primary versus mechanism versus diagnostic evidence;
- representative storytelling versus multi-seed robustness;
- bounded claim/nonclaim status.

Renderer-specific controls, layout, charts, selection, accessibility, animation,
camera, timing, and export remain presentation responsibilities. The B3 cinematic
director remains concrete. Do not generalize it into a camera DSL, universal
storyboard, scene graph, or broad `ScenarioPresentationSpec` without multiple future
scenarios demonstrating a repeated responsibility.

## Longer-term modeled fronts

### Front A — richer genetic expression

Potential directions include incomplete dominance, codominance, epistasis,
dosage-sensitive expression, and richer quantitative architectures. Preserve:

```text
genome
  ↓
genetic expression
  ↓
genetic phenotype
  ↓
development / environment-dependent realization
  ↓
current physiological state
```

### Front B — richer chromosome pairing and recombination

Current responsibilities already separate chromosome-copy structure, pairing,
recombination eligibility, segregation, and gamete formation. Future biology may
earn higher-copy pairing, multivalents, chromosome-specific crossover behavior, or
multiple crossovers. Keep meiosis vocabulary outside the kernel/general propagation
contracts.

### Front C — richer mating systems

Shared reproduction already separates participants, investors, genetic
contributors, and production sources. Future cases may explore ordered/asymmetric
roles, multi-participant groups, hermaphroditic systems, or role-sensitive choice.
Keep mating-system composition separate from low-level inheritance.

### Front D — richer development and G×E

Possible directions include nonlinear reaction norms, developmental history/stages,
richer developmental stochasticity, and reversible adult plasticity. Preserve
inheritance, expression, development, environment, and current mutable state as
separate responsibilities.

### Front E — richer evolutionary ecology

Possible directions include richer resource competition, movement/behavior
tradeoffs, predation/prey coevolution, life-history tradeoffs, spatial population
structure, and fluctuating/heterogeneous selection. Selection should continue to
emerge from differential persistence/propagation rather than a kernel-owned scalar
`fitness` field.

## Observation and statistical analysis

E1–E7 provide concrete consumers for scientific measurement without justifying a
broad statistics framework. Future repeated experiment patterns may earn reusable
statistical contracts only after multiple concrete consumers show what actually
repeats.

Preserve:

```text
committed state/events
        ↓
pure scenario-specific measurements
        ↓
replicate outcomes / treatment comparisons
        ↓
experiment-level inference/reporting
        ↓
presentation
```

Undefined post-extinction quantities remain undefined rather than becoming zero.
Presentation remains a consumer, not an authoritative calculator.

## Future native execution backend

A Rust/C++ backend remains evidence-driven future work. If profiling eventually
justifies it, preserve Python modeling/configuration and compile a validated stable
subset to a backend execution boundary with Python remaining a reference backend.
Do not create that abstraction before measured need and a stable execution subset
exist.

## Architectural constraints that should survive future work

- Preserve the frozen transactional kernel unless a true generic deficiency is
  demonstrated.
- Preserve simulation-owned RNG and materialize-before-apply semantics.
- Preserve domain-neutral general-evolution vocabulary.
- Keep chromosome structure, pairing, recombination, and segregation separate.
- Keep reproduction participants, investors, contributors, and production sources
  separate.
- Keep genetic expression, development, environment, and current state separate.
- Keep scientific measurement downstream of committed evidence and upstream of
  reporting/presentation.
- Keep presentation downstream of scientific meaning; interpolation is never
  evidence.
- Keep run/seed as the current experimental replicate unless a later concrete design
  justifies another unit.
- Keep Workbench above existing typed/scenario composition and lower
  validation/preflight.
- Keep persisted Workbench values separate from mutable recorder/spec/runtime graphs.
- Preserve scenario origin separately from validated scenario identity.
- Preserve semantic factor identity separately from implementation paths and
  counterbalancing metadata.
- Normalize inapplicable authoring state before persistence.
- Keep Workbench scientific manifests renderer-neutral.
- Keep QML behind curated Qt properties/signals/slots/item models; do not expose
  arbitrary mutable scientific object graphs.
- Keep PySide6 optional and downstream of the core engine.
- Allow UI/cinematic to consume Workbench downstream while preventing reverse
  dependencies.
- Prefer readable maintainable architecture over micro-optimization.
- Require evidence before performance/backend work.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier work changed assumptions in this roadmap;
3. start from a concrete modeled, scientific, or product/presentation use case;
4. settle consequential public architecture in Chat when needed;
5. create one focused Issue with boundaries, traps, acceptance criteria, tests, and
   manual verification where material;
6. apply `docs/development/validation_workflow.md` rather than milestone-local stale
   validation instructions;
7. update this roadmap only when ordering or architectural direction materially
   changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change
it.
