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
7. performance/native-backend work begins only from measured need.

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

The richer B-series flagship established a robust environment-dependent selection
story without kernel changes or scalar fitness:

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

Canonical B3 compares uniform renewable-resource placement with two equal-weight
radius-1 patches at `(2, 5)` and `(9, 5)` while keeping nonfocal biology, founder
construction, resource quantity, sexual inheritance, and horizon matched. Founders
begin with balanced homozygous `max_speed = 1 / 4` standing variation.

Independent confirmation uses seeds `5, 17, 29, 43, 61, 79, 97, 113`. Compact
treatment exceeds matched uniform control in all eight seeds at the predeclared
step-30 high-speed allele-frequency readout. Founder reproductive contribution,
founder-label counterbalancing, and radius-2 geometry sensitivity support and bound
the interpretation. Representative seed 5 and its real committed mechanism
episodes are chosen by B3 science, not by presentation code.

The old `max_intake_rate` v0.1 example remains a secondary historical
regression/integration path.

## Completed E1–E6 controlled-science sequence

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
```

- **E1** established exact event/state alignment, scientific provenance,
  fixed-horizon censoring, thin treatment-integrity checks, and pure measurements
  from committed evidence without a universal metrics/statistics framework.
- **E2** validated capacity-limited targeted movement, locomotion-use cost,
  endpoint feeding, scarce-resource competition, exact clonal propagation, and
  known grid anisotropy in a minimal one-locus system.
- **E3** independently confirmed local-resource speed neutrality and an interior
  speed-3 corridor performance maximum; removing locomotion cost removes the
  canonical high-speed penalty.
- **E4** independently confirmed that the corridor increases speed-3 frequency
  from `1/3` to `2/3` from equal standing variation while the local arm remains
  neutral; complete focal composition and strategy-specific mechanism evidence are
  preserved, with founder-order counterbalancing kept separate from treatment.
- **E5** showed neutral frequency-change spread contracting with founder count and
  weak 3-vs-4 selection reversing in some small-population runs. Unobserved
  loss/fixation/extinction remains right-censored.
- **E6** uses exact resident-state/RNG forking and matched rare external admission.
  Speed-3 mutants can reproduce and expand against speed-4 residents while
  reciprocal speed-4 mutants do not expand. The claim remains bounded to candidate
  invasion stability against reciprocal speed 4.

E1–E6 remain separate from B3. The controlled sequence isolates causal mechanics;
B3 remains the richer integrated reference-ecology flagship.

## Experiment Workbench product sequence

WB1–WB5 now establish the first complete concrete Workbench Study workflow:

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

### WB1 — Controlled Locomotion Study Core

WB1 established bounded semantic authoring, stable scientific IDs, explicit versus
derived manifest meaning, EvidencePlan persistence, exact compatibility-aware
save/load, fresh runtime reconstruction, run-to-manifest provenance, immutable fork
lineage, and recipe-scoped semantic diff over the characterized E3 locomotion
surface.

### WB2 — Curated B3 Study, Exact Reproduction, and Fork Lineage

WB2 represented the confirmed B3 flagship as a trusted frozen Workbench Study with
a rich resolved manifest and existing B3 science as authority. It established:

```text
scenario identity = exact validated frozen scenario
scenario origin   = scientific lineage from that scenario
```

The supported radius-2 sensitivity fork retains B3 origin but loses canonical
radius-1 validated identity and does not automatically inherit the original
headline claim or representative-story semantics. Exact reproduction loads the
stored resolved manifest rather than re-resolving modern defaults.

### WB3 — Controlled Experiment Authoring

WB3 added two concrete persisted experiment patterns without a generic experiment
DSL:

- E3-style one-factor max-speed sweep using stable factor identity
  `controlled-locomotion.max-speed`;
- E4-style matched environment comparison using stable factor identity
  `controlled-locomotion.resource-geography` while keeping founder-order
  counterbalancing separate from primary factor meaning.

Treatment expansion occurs before compilation. One run/seed remains a replicate.
Existing E3/E4 treatment-integrity checks, outcomes, summaries, and evidence remain
authoritative.

### WB4 — Bounded Reference-Ecology Custom Study

WB4 added `bounded-reference-ecology` v1 over existing reference composition.
Guided authoring covers the stable core; Advanced authoring covers selected richer
movement/resource/mutation/recombination controls; Expert remains deliberately
empty. Arbitrary policy graphs, genetics, inheritance, reproduction, lifecycle,
and development/G×E stay Extension/Internal.

Conditional state is recipe-local and inactive values are normalized out before
persistence. Exact manifests include stable semantic identity plus compatibility
fingerprinting for non-editable scientific assumptions. Population, event,
pedigree, genetic-composition, and spatial evidence reuse existing recorders;
spatial replay is opt-in with a volume advisory.

### WB5 — Scientific Results and Presentation Integration

WB5 establishes the post-execution Study boundary without creating a universal
Results object or presentation framework.

`workbench.results` organizes existing WB1, E3, E4, WB4, and B3 artifacts by exact
Study revision, manifest, EvidencePlan, treatment/factor, seed/replicate, and
counterbalance identity. Missing evidence is reported as unavailable rather than
reconstructed. Existing scientific outcomes pass through unchanged.

Downstream adapters integrate with existing media:

- V2 builds existing `WorldPresentationFrame` values from recorded WB4/B3 evidence
  while preserving exact Workbench run/seed/arm context;
- V3 accepts validated canonical B3 Workbench results into the existing B3-specific
  cinematic director;
- a B3 radius-2 derived fork remains inspectable but cannot inherit the canonical
  headline/story cinematic handoff merely from scenario origin.

WB5 confirms that the WD2 labels `Study / Simulation / Evidence / Experiment /
Results / Presentation` are a **product/navigation model**, not a one-class-per-
section architecture. Persisted scientific identity remains recipe/pattern-specific;
Results is mainly a view over existing artifacts; Presentation remains downstream.
No new universal renderer-neutral presentation abstraction is earned beyond the
existing `ContinuousTraitEncoding` and concrete scientific handoffs.

See `docs/wb5_results_presentation.md`.

## Next Workbench milestone: WB6

### WB6 — Diagnostics and Support-Envelope Hardening

WB6 should improve only diagnostics and support behavior demonstrated by WB1–WB5.
The concrete pressure now includes:

- incomplete and unsupported authoring choices;
- irrelevant conditional parameters and normalized stale state;
- missing evidence with explicit rerun remediation;
- loss of validated scenario identity while retaining scenario origin;
- exact-reproduction compatibility failures;
- experiment-specific factor/treatment-integrity failures;
- distinction between blocking readiness and advisory conditions;
- support-tier promotion only where real usage demonstrates stable semantics.

The Workbench must not parse arbitrary Python exception prose to invent scientific
remediation. Lower biological, generic dependency, and scientific validators remain
authoritative.

WB6 is **not** a generic Workbench-framework milestone. Do not introduce a
capability graph, reflection-based form system, evidence solver, plugin registry,
universal Study/Result schema, migration framework, claim inference engine, or
statistics DSL merely because five Workbench milestones now exist.

See `docs/development/wb6_workbench_handoff.md`.

## Presentation continuation

WB5 implements the architectural integration seam for Workbench→V2/V3, while the
concrete user-facing interactive B3 matched-comparison experience can continue to
improve on top of it.

Preserve across media:

- B3 control/treatment semantics;
- fixed shared `max_speed` scientific scale;
- matched committed timestep convention;
- exact Study/run/treatment/replicate identity;
- primary versus mechanism versus diagnostic evidence;
- representative storytelling versus multi-seed robustness;
- bounded claim/nonclaim status.

Renderer-specific controls, layout, charts, selection, animation rate,
accessibility, camera, timing, and export quality remain presentation
responsibilities.

The B3 cinematic director remains concrete. Do not generalize it into a camera DSL,
universal storyboard, or `ScenarioPresentationSpec` without multiple future films
demonstrating a repeated responsibility.

## Next controlled-science milestone: E7

### E7 — Mutation-Driven Adaptation and Convergence

E7 is sequential after E6 and orthogonal to WB6. Its central question is whether
independent populations with **focal-only `max_speed` mutation** converge toward the
performance/selection/invasion region identified by E3–E6.

Use multiple predeclared low/near/high starting conditions, multiple independent
seeds, an explicit mutation rate and step distribution, a legal speed range wider
than the expected adaptive region, and full trait-distribution evidence. Distinguish
convergence from stationary variation, persistent polymorphism, directional
change, extinction, and boundary accumulation. A pile-up at a configured boundary
is not an optimum.

Do not enable mutation across the richer reference genome merely for convenience.
E7 should remain above the frozen kernel and should not acquire Workbench
dependencies merely because both tracks exist.

## Longer-term modeled fronts

### Front A — richer genetic expression

Extend current copy-count-aware, multi-locus expression only through concrete
biological consumers: incomplete dominance, codominance, epistasis,
dosage-sensitive expression, or richer quantitative architectures where earned.
Preserve:

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

Do not collapse these layers into a catch-all phenotype object.

### Front B — richer chromosome pairing and recombination

Current responsibilities already separate chromosome-copy structure, pairing,
recombination eligibility, segregation, and gamete formation. Future biology may
earn higher-copy pairing, preferential/random bivalents, multivalents,
chromosome-specific crossover behavior, or multiple crossovers. Keep meiosis
vocabulary out of the kernel/general propagation contracts.

### Front C — richer mating systems

Shared reproduction already separates participants, investors, genetic
contributors, and production sources. Future cases may explore ordered/asymmetric
roles, multi-participant groups, hermaphroditic systems, role-sensitive choice, or
contributor/investor subsets. Keep mating-system composition separate from
low-level inheritance.

### Front D — richer development and G×E

Possible directions include nonlinear reaction norms, developmental history/stages,
richer developmental stochasticity, and reversible adult plasticity distinct from
lifetime developmental targets. Preserve inheritance, expression, development,
environment, and current mutable state as separate responsibilities.

### Front E — richer evolutionary ecology

Possible directions include richer resource competition, movement/behavior
tradeoffs, predation/prey coevolution, life-history tradeoffs, spatial population
structure, and fluctuating or heterogeneous selection. Selection should continue to
emerge from differential persistence/propagation rather than a kernel-owned scalar
`fitness` field.

## Observation and statistical analysis

E1–E6 provide concrete consumers for scientific measurement without justifying a
broad statistics framework. Repeated future experiment patterns may earn reusable
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
- Keep reproduction participant/investor/contributor/production-source roles
  separate.
- Keep chromosome structure, pairing, recombination, and segregation separate.
- Keep genetic expression, development, environment, and current state separate.
- Keep scientific measurement downstream of committed evidence and upstream of
  reporting/presentation.
- Keep presentation downstream of scientific meaning; presentation interpolation
  is never evidence.
- Keep run/seed as the current experimental replicate unless a later concrete
  design justifies another unit.
- Keep Workbench authoring above existing typed/scenario composition and lower
  validation/preflight.
- Keep persisted Workbench values separate from mutable recorder/spec/runtime
  graphs; reconstruct runtime values afresh.
- Preserve scenario origin separately from validated scenario identity.
- Preserve semantic factor identity separately from implementation field paths and
  counterbalancing metadata.
- Normalize inapplicable Workbench authoring state before persistence.
- Keep Workbench scientific manifests renderer-neutral.
- Allow UI/cinematic to consume Workbench downstream while preventing Workbench or
  model/science from importing renderer packages.
- Prefer readable maintainable architecture over micro-optimization.
- Require evidence before performance/backend work.

## ChatGPT versus Codex allocation

Use ChatGPT primarily for architecture-heavy work, consequential public contracts,
tightly scoped sequential implementation, roadmap sequencing, and independent
review/merge decisions.

Use Codex selectively for execution-heavy work behind settled contracts, broad
analogous migrations, repetitive test expansion, validation/debug cycles, and
independently parallelizable repository iteration.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier work changed assumptions in this roadmap;
3. start from a concrete modeled or product/presentation use case;
4. settle consequential public architecture in Chat when needed;
5. create one focused Issue with boundaries, traps, acceptance criteria, tests, and
   manual verification where material;
6. update this roadmap in the same PR only when ordering or architectural direction
   materially changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change
it.
