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

The project should continue toward a simulation engine in which:

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
7. Workbench foundation growth is incremental, while application integration builds
   concrete product workflows over those settled contracts;
8. performance/native-backend work begins only from measured need.

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
   +----+----+
   |         |
   v         v
interactive  cinematic
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
region. This bounds the earlier E3–E6 result: favorable performance, selection, and
invasion when a strategy already exists do not imply that distant populations can
reach it through mutation within a finite ecological/reproductive regime.

Future science should preserve this result rather than post-hoc retuning E7 until
convergence appears.

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

### What is now settled

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
- WB6 audited the complete implementation and found the foundation stable. It
  promoted only one genuinely repeated responsibility: a small Workbench-owned
  diagnostic value with code, severity, optional semantic context, message, and
  remediation.

The final review is in `docs/workbench_architecture_review.md`.

## Workbench direction after WB6

The Workbench foundation is now in **maintenance-and-extension mode**.

Future foundation changes should normally begin from a real scientific/product use
case and take one of these forms:

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
reproduction/lifecycle/development composition Extension/Internal. WB6 performs no
support promotion merely because lower engine validators allow broader values.

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

## Workbench UI integration sequence

WU1 establishes the concrete Streamlit product shell over the completed backend:

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

The shell uses explicit dispatch over existing concrete persisted artifacts rather
than a universal Study schema. Canonical B3, controlled single-run, E3 max-speed
sweep, E4 environment-selection comparison, and bounded Reference Ecology share the
same product frame while retaining their existing serializers/loaders, readiness,
manifest meaning, and revision semantics. The prior world workspace stays available
for later integration. See `docs/workbench_ui.md`.

WU2 fills the Simulation section with concrete authoring instead of a generic form
system. Controlled single-run Studies expose only their stable max-speed,
resource-geography, and seed slots. Reference Ecology consumes the existing WB4
Guided/Advanced metadata, applicability, normalization, and readiness contracts;
Advanced is disclosure over the same intent, Expert remains empty, and
Extension/Internal capabilities remain outside official authoring. The page keeps
explicit authoring intent visibly separate from derived and frozen recipe meaning.

WU2 also makes existing scientific revision semantics visible. A private UI draft
never mutates the active saved revision; Save creates a child through the existing
concrete fork API. Controlled/reference/B3 differences are rendered through their
existing recipe-scoped semantic-diff contracts. Canonical B3 remains curated and
read-only except for the explicit supported radius-2 sensitivity fork, whose child
preserves B3 origin while losing the validated radius-1 identity.

WU3 completes the first end-to-end scientific execution path through that shell.
Evidence authoring consumes only the existing controlled/reference evidence-plan
contracts and leaves frozen/experiment-required B3/E3/E4 evidence read-only.
Reference spatial-history guidance remains a non-blocking backend-owned advisory.
E3 and E4 expose only their existing concrete experiment choices; their displayed
run matrices come from authoritative expansion, while B3 case counts come from
curated compilation.

WU3 also activates the global Run action without creating a second execution model.
Existing Workbench readiness remains the authoring authority; Run first opens a plan
derived from the exact artifact, then delegates synchronously to the owning concrete
Workbench runner. Pending revision-backed Simulation/Evidence changes receive one
immutable child owner before execution, while E3/E4 keep their existing immutable
experiment-definition semantics. Successful revision-owned runs attach returned
provenance using existing `.with_run(...)` behavior, and authoritative result objects
remain session-owned. Compile/preflight failure does not mutate the saved artifact or
become fabricated Workbench diagnostics.

The next product front is downstream **Results/world/presentation integration** over
this now-concrete execution/result-ownership seam. It should reuse WB5 result
navigation and existing V2/V3 presentation adapters, add concrete analysis or Run
Explorer workflows only where current result/evidence contracts support them, and
keep Presentation downstream of authoritative scientific meaning. The focused Issue
for that work should establish its exact WU milestone identity against current
`main`; this roadmap does not invent a generic Results framework or universal next
schema in advance.

Future WU work must continue to preserve the existing distinctions among simulation
intent, evidence plan, factor/treatment design, replicate planning, authoritative
lower preflight, committed results, and presentation. It must not create a generic
experiment DSL, statistics framework, universal Study schema, or duplicate scientific
validation merely to simplify UI orchestration.

## Controlled-science direction after E7

E7 closes the first planned E-series causal sequence. There is no automatic E8.
The next controlled-science milestone should be chosen only after reassessing the
new unresolved mechanism rather than assuming the previous hypothesis was supposed
to succeed.

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

WB5 provides the architecture seam for Workbench→V2/V3, and WU3 now supplies
concrete application execution/result ownership. Later WU work can integrate those
consumers through the persistent Study shell while preserving:

- exact Study/run/treatment/replicate identity;
- B3 control/treatment semantics;
- fixed shared scientific trait scales;
- matched committed timestep convention;
- primary versus mechanism versus diagnostic evidence;
- representative storytelling versus multi-seed robustness;
- bounded claim/nonclaim status.

Renderer-specific controls, layout, charts, selection, accessibility, animation,
camera, timing, and export remain presentation responsibilities.

The B3 cinematic director remains concrete. Do not generalize it into a camera DSL,
universal storyboard, scene graph, or broad `ScenarioPresentationSpec` without
multiple future scenarios demonstrating a repeated responsibility.

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
- Keep run/seed as the current experimental replicate unless a later concrete
  design justifies another unit.
- Keep Workbench above existing typed/scenario composition and lower
  validation/preflight.
- Keep persisted Workbench values separate from mutable recorder/spec/runtime
  graphs.
- Preserve scenario origin separately from validated scenario identity.
- Preserve semantic factor identity separately from implementation paths and
  counterbalancing metadata.
- Normalize inapplicable authoring state before persistence.
- Keep Workbench scientific manifests renderer-neutral.
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
6. update this roadmap only when ordering or architectural direction materially
   changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change
it.
