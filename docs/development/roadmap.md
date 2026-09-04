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
6. performance/native-backend work begins only from measured need.

The kernel is not the development frontier. New modeled behavior normally belongs
above it unless a genuine generic deficiency is demonstrated.

## v0.1.0 portfolio baseline

The first portfolio sequence is complete as an architectural direction:

```text
nonbiological evolution proof
        |
        v
transmissible-state normalization
        |
        v
reproduction boundary hardening
        |
        v
explicit chromosome transmission responsibilities
        |
        v
committed spatial observation
        |
        v
Streamlit / Plotly dashboard
        |
        v
adaptive curated configuration
        |
        v
renderer-neutral Manim cinematic
        |
        v
reproducible flagship evolutionary demonstration
        |
        v
v0.1.0 release baseline
```

The durable presentation boundary is broader than the current renderer choices:

```text
simulation/domain layers
        |
        v
committed scientific evidence
        |
        v
scenario-specific scientific encoding
        |
        +-------------------------+
        |                         |
        v                         v
interactive presentation     cinematic presentation
```

Current Streamlit/Plotly and Manim implementations remain valid baseline
consumers, but future presentation work may replace renderer technologies without
moving scientific truth or modeled behavior into the renderer. Committed
observation/result contracts do not contain Plotly, Streamlit, Manim, Blender,
frame, timing, interpolation, camera, or other renderer-owned concepts.

Visual primitives are a shared conceptual vocabulary rather than a requirement for
a universal runtime scene graph. Scenario-specific scientific encoding may become
a small shared immutable value once repeated concrete scenarios establish stable
fields; do not create a broad speculative presentation schema first.

The flagship `max_intake_rate` scenario remains an illustrative evidence-backed
demonstration, not a calibrated ecological prediction.

## Post-v0.1 dependency shape

The current phase has two coordinated but architecturally separate fronts, now
joined by concrete scenario evidence rather than hypothetical capability work:

```text
                         v0.1.0 baseline
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
      modeled-domain/scenario             presentation refinement
             |                                   |
      +------+-------+                           |
      |              |                           |
      v              v                           |
B1 patchy        B2 heritable                     |
resources        max_speed tradeoff               |
      |              |                           |
      +-------+------+                           |
              |                                  |
              v                                  |
       B3 scenario discovery                     |
              |                                  |
              +---------------+------------------+
                              |
                              v
                   committed scientific evidence
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             interactive V2       cinematic V3
```

A selective per-organism genetic-phenotype observation seam supports focal-trait
replay without broadening spatial snapshots. B3 can specify which scientific
variables matter; V2 and V3 consume the same committed evidence and scientific
meaning while independently implementing interaction, layout, camera, timing,
and choreography.

Presentation work may proceed in parallel when it consumes already-settled
configuration, observation, experiment, or export contracts. It must not invent
simulation semantics merely to improve rendering. When presentation exposes a
real shared-data gap, settle the smallest scientifically named observation/domain
contract before renderer-specific use.

The modeled-domain fronts are also intentionally partially independent. Richer
genetic expression, mating systems, chromosome transmission, development/G×E,
and ecology need not serialize behind one another when their public boundaries are
already settled.

## Near-term integrated evolutionary scenario

Static spatial resource heterogeneity and a concrete heritable performance/cost
axis are now available separately:

```text
B1
uniform or weighted patchy resource placement
        +
B2
balanced standing variation at existing max_speed
with farther target reach and higher maintenance cost
        |
        v
B3
find the simplest robust environment-dependent selection scenario
```

B3 should determine whether those mechanisms compose into a causally legible,
reproducible evolutionary demonstration. It should prefer the simplest successful
scenario and validate fixed-seed visual legibility separately from multi-seed
robustness.

The scenario layer owns scientific questions, treatment/control semantics, focal
variables, relevant events, key metrics, canonical runs, robustness evidence, and
claim boundaries. It does not own renderer colors, materials, camera paths, or UI
layout.

Static placement and temporal change remain separate responsibilities. Temporal
or seasonal landscape behavior should be added only if B3 or a later concrete
scenario demonstrates that static heterogeneity cannot answer the intended
question.

## Near-term presentation refinement

Presentation refinement should proceed from a world-first product experience while
preserving the evidence boundary.

The generic interactive front may develop configuration/workspace mode switching,
world playback, selection, timelines, and scientific inspection before the final
B3 handoff. B3-specific individual encoding should consume the selective
per-organism genetic-trait observation rather than live organisms or enlarged
spatial snapshots.

The cinematic front may independently test a higher-quality renderer against the
current Manim baseline. Any replacement must remain deterministic, scriptable,
reproducible from committed data, and independent of interactive renderer
implementation.

For both media, scientific presentation follows:

```text
committed evidence
        ↓
scenario-specific scientific meaning
        ↓
renderer-owned primitives/choreography
```

Matched experimental comparisons must preserve scientific channel mappings,
trait scales, legends, time conventions, and geometry/camera scale where
appropriate. Presentation interpolation never becomes scientific evidence.

## Front A — Richer genetic expression

**Goal:** extend the existing copy-count-aware, multi-locus expression framework
with additional explicit biological expression policies.

Potential cases include:

- incomplete dominance;
- codominance;
- epistasis and other locus interactions;
- dosage-sensitive expression;
- richer quantitative architectures.

Preserve the boundary:

```text
genome
  |
  v
genetic expression
  |
  v
genetic phenotype
  |
  v
development / environment-dependent realization
  |
  v
current mutable physiological state
```

Do not collapse those layers into one catch-all phenotype object.

**Implementation mode:** use ChatGPT for public-model semantics and representative
implementation. Settled independent policy/test matrices are good Codex work.

## Front B — Richer chromosome pairing and recombination

**Current foundation:** chromosome-copy structure, pairing, recombination
eligibility, segregation, and gamete formation are already separate public
responsibilities. `Genome` remains permissive inherited-state data and there is no
foundational organism-wide ploidy scalar.

**Goal:** add richer biological transmission only when a concrete case requires it.
Candidate directions include:

- production higher-copy pairing policies;
- preferential versus random bivalent formation;
- multivalent models;
- chromosome-specific pairing behavior;
- chromosome-specific or multiple-crossover recombination;
- role/mating-type/lifecycle-sensitive gamete formation;
- sex-chromosome or homeolog semantics when same-name grouping is insufficient.

Do not add these merely to enumerate biological possibilities. A future milestone
should choose one discriminating use case and exercise the settled boundaries.
General `PropagationModel` and the frozen kernel do not need meiosis vocabulary.

## Front C — Richer mating systems

**Current foundation:** shared reproduction already supports arbitrary nonempty
participant groups and separates participant, investor, genetic-contributor, and
production-source responsibilities. Current clonal/biparental behavior is concrete
policy, not universal orchestration.

**Goal:** use those contracts for richer systems such as:

- asymmetric or ordered reproductive roles;
- multi-participant reproductive groups;
- hermaphroditic systems;
- role-sensitive mate choice;
- contributor/investor policies that choose real subsets;
- lifecycle-specific production sources where biology requires them.

Mating-system composition should remain separate from low-level inheritance.
External hosts/caregivers/resource contributors should broaden the current
participant-subset boundary only with explicit lifecycle and conflict semantics.

## Front D — Richer development and G×E

**Goal:** extend environmental and G×E realization while preserving distinctions
among inheritance, genetic expression, development, environment, and current
physiological/behavioral state.

Potential directions include:

- nonlinear reaction norms;
- developmental timing/stages;
- environmental history;
- richer developmental stochasticity;
- reversible adult plasticity distinct from lifetime developmental targets.

Do not turn the existing frozen `DevelopmentalProfile` into a catch-all mutable
phenotype merely to accommodate plasticity.

## Front E — Richer evolutionary ecology

**Goal:** use the stable biological boundaries to model more consequential
selection pressures and interactions while keeping ecology out of the kernel and
general evolution layer.

The current ecological foundation includes explicit spatial resource-placement
policy: renewable-resource quantity/cadence remains process responsibility, while
an immutable ecology policy chooses each deposit location from the
simulation-owned RNG. Uniform placement remains the simple baseline; patchy
placement supplies static spatial heterogeneity. Committed world resources remain
the authoritative state observed by downstream spatial recorders.

The reference biology also demonstrates `max_speed` as an existing inherited
performance/cost tradeoff. This is a concrete input to ecological scenario design,
not a generic strategy or fitness abstraction.

Possible continuing fronts include:

- richer resource competition;
- movement/behavior tradeoffs;
- predation/prey coevolution;
- life-history tradeoffs;
- environment-dependent reproductive outcomes;
- spatial/biogeographic structure;
- fluctuating or heterogeneous selection regimes.

Selection should continue to emerge from differential persistence and propagation
rather than becoming a generic scalar `fitness` field imposed by the kernel.

Ecology should drive requests for richer genetics, mating, or development where
possible. That keeps abstractions attached to real modeled behavior instead of
speculative biological completeness.

## Future native execution backend

A Rust/C++ backend is a separate evidence-driven architectural front, not part of
the v0.1 release and not an excuse to redesign the kernel now.

The desirable long-term shape, if performance measurements justify it, is roughly:

```text
Python modeling / configuration
        |
        v
validated static typed simulation plan
        |
        v
backend execution boundary
        |
        +----------------------+
        |                      |
        v                      v
Python reference backend   native backend
        |                      |
        +----------+-----------+
                   |
                   v
        committed result values
```

Do not create that plan/backend abstraction until real execution-heavy workloads
show that Python is the limiting factor and the stable subset worth compiling is
known. Python should remain the ergonomic modeling/composition layer.

When that front becomes concrete, require:

- measured performance evidence;
- deterministic parity requirements;
- explicit ownership/mutability semantics;
- serialization/versioning rules for any compiled plan;
- cross-backend conformance tests;
- clear fallback/reference behavior;
- no renderer concepts in the backend contract.

## Cross-cutting fronts

The following concerns continue alongside modeled-domain milestones when concrete
need appears:

- evolutionary observation and statistical analysis;
- reproducible experiment composition/export;
- checkpoint/resume guarantees;
- documentation and examples;
- evidence-based performance measurement;
- portfolio maintenance and presentation refinement above stable production
  contracts.

Do not turn them into foundational redesigns merely because they are
cross-cutting.

## Architectural constraints that should survive future work

- Preserve the frozen transactional kernel unless a true generic deficiency is
  demonstrated.
- Preserve simulation-owned RNG and materialize-before-apply semantics.
- Preserve domain-neutral general-evolution vocabulary.
- Keep reproduction participant/investor/contributor/production-source roles
  separate.
- Keep chromosome structure, pairing, recombination, and segregation separate.
- Keep genetic expression, development, and current state separate.
- Keep presentation downstream of committed evidence even when presentation work
  proceeds in parallel with domain enrichment.
- Share scenario-level scientific meaning across presentation media without
  forcing renderer implementation or choreography into a universal abstraction.
- Keep spatial observation focused; add selective sibling scientific records when
  a real per-individual data need appears.
- Prefer readable maintainable architecture over micro-optimization.
- Require evidence before performance/backend work.

## ChatGPT versus Codex allocation

Use ChatGPT Chat primarily for:

- architecture-heavy work;
- consequential public-contract decisions;
- tightly scoped sequential implementation;
- roadmap sequencing and tradeoffs;
- independent architectural review/merge decisions.

Use Codex selectively for:

- execution-heavy work behind settled contracts;
- broad analogous migrations;
- repetitive test expansion;
- validation/debug-cycle intensive work;
- independently parallelizable repository iteration.

Optimize for total time and attention required to reach a correct merged change,
not for a blanket preference for one implementation agent.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier work changed assumptions in this roadmap;
3. start from a concrete modeled use case rather than a feature taxonomy;
4. settle consequential public architecture in Chat when needed;
5. create one focused Issue with boundaries, traps, acceptance criteria, automated
   tests, and manual verification where material;
6. update this roadmap in the same PR only when ordering or architectural direction
   materially changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change
it.
