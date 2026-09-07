# Evolution Experiment Workbench Architecture

The Evolution Experiment Workbench is a **scientific-study authoring layer over the
existing engine**. It does not define a second simulation model and it does not sit
between biological composition and the generic kernel.

WB1 established the first intentionally narrow controlled-locomotion vertical. WB2
pressure-tested those contracts against the richer confirmed B3 flagship and added
the first trusted curated-scenario workflow. WB3 then added two concrete controlled-
experiment authoring patterns without turning those concrete needs into a universal
experiment language.

## Dependency direction

The durable dependency direction is:

```text
Workbench scientific study / curated scenario / experiment definition
        ↓
bounded recipe adapter or concrete experiment-pattern expansion
        ↓
existing preset / experiment / scenario composition
        ↓
authoritative scientific validation and biological/generic preflight
        ↓
frozen kernel
```

For WB1 specifically:

```text
ControlledLocomotionIntent
        ↓
controlled-clonal-locomotion recipe resolution
        ↓
immutable ControlledLocomotionManifest
        ↓
existing E3 treatment composition
        ↓
ControlledLocomotionConfig
        ↓
build_controlled_locomotion_spec()
        ↓
BiologicalSimulationSpec.compile()
        ↓
SimulationSpec.compile()
```

For WB2 specifically:

```text
trusted B3 scenario
        ↓
B3CuratedIntent
        ↓
immutable B3CuratedManifest
        ↓
existing B3 flagship specification builders
        ↓
authoritative B3 treatment-integrity validation
        ↓
existing B3 evidence / summary contracts
        ↓
ordinary reference-ecology execution
```

For WB3 specifically:

```text
concrete experiment definition
        ↓
stable semantic factor identity
        ↓
deterministic treatment expansion
        ↓
WB1 manifest or existing E4 treatment specification
        ↓
existing E3/E4 treatment-integrity authority
        ↓
existing E3/E4 execution and result contracts
```

Nothing new is introduced inside the frozen kernel. Lower engine/domain packages
must not import `evo_engine.workbench`.

## Bounded recipe identity

WB1's first supported recipe has stable scientific identity:

- recipe ID: `controlled-clonal-locomotion`;
- recipe version: `1`;
- compiler ID: `workbench.controlled-clonal-locomotion`;
- compiler version: `1`.

Its explicit recipe-scoped semantic slots are:

```text
controlled-locomotion.max-speed
controlled-locomotion.resource-geography
controlled-locomotion.seed
```

WB2 adds a second explicit bounded recipe:

- recipe ID: `curated-b3-flagship`;
- recipe version: `1`;
- compiler ID: `workbench.curated-b3-flagship`;
- compiler version: `1`.

Its only editable scientific slot is the pre-existing B3 geometry sensitivity:

```text
b3.resource-geography.treatment-radius
```

The canonical validated value is radius `1`; WB2 supports only the authoritative
B3 radius-`2` sensitivity as a scientific fork. The remaining B3 assumptions are
inspectable frozen resolved values rather than a giant editable form.

These IDs are persisted scientific identity. Python module paths, class names, and
object graphs are not scientific identity.

There is no reflection-based discovery, global recipe registry, generic policy
descriptor system, composition graph, configuration DSL, or capability solver.

## Supported authoring surfaces

WB1 deliberately supports only the scientific surface already characterized by E3.
Resource geography is one of:

- `local_resource`;
- `separated_corridor`.

The Workbench-supported `max_speed` range is `1..10`, matching E3's characterized
speed grid. The underlying controlled-locomotion preset remains engine/domain-valid
for its existing broader range.

WB2 is deliberately different: canonical B3 is a trusted curated study, not a
general reference-ecology editor. Its assumptions are frozen by the confirmed B3
contract. The only supported edit is radius `1 → 2`, because that exact sensitivity
already exists in authoritative B3 science.

WB3 is different again: it authors two concrete experimental designs over already
settled science rather than exposing arbitrary configuration. Keep these concepts
distinct:

```text
engine-valid range
        ≠
Workbench-supported range
        ≠
experiment-declared factor levels
        ≠
curated-scenario frozen assumptions
```

Workbench support is a product/recipe contract, not a new biological invariant.

## Explicit intent and resolved manifests

Editable semantic intent and immutable resolved scientific meaning remain separate.

`ControlledLocomotionIntent` persists WB1's human-visible choices. Resolution
creates a separate immutable `ControlledLocomotionManifest` containing stable
recipe/compiler identity, engine compatibility identity, normalized explicit slot
values, and scientifically meaningful fixed assumptions.

The controlled-locomotion derived assumptions make the fixed composition visible:
one inherited focal `max_speed`, controlled one-locus genetics, clonal inheritance,
mutation off, perfect full-world sensing, nearest-resource targeting, fixed body
mass and nonfocal feeding/reproduction settings, and absence of mate search,
predation, metabolism, growth, aging, and renewable resource generation. Resource
layout is derived through the existing E3 treatment builder rather than copied into
Workbench code.

WB2 follows the same principle with `B3CuratedIntent` and `B3CuratedManifest`, but
B3 requires a much richer resolved manifest. It makes inspectable the frozen matched
study design, uniform versus patch resource geography, patch centers/radius/weights,
treatment-integrity semantics, blocked-by-seed RNG interpretation, focal trait and
balanced founder construction, standard versus swapped founder-assignment roles,
discovery/confirmation/counterbalance seeds, primary step-30 readout, explicit
reference-ecology configuration, mutation/recombination, ordinary reference sexual
inheritance, expected renewable-resource generation, and the authority/claim
semantics needed to avoid treating a derived fork as validated B3.

Those B3 values are derived from `build_b3_flagship_specification()` and the frozen
B3 constants at resolution time rather than copied into a second scientific
implementation. Compilation reconstructs the expected values through the compatible
pinned recipe/compiler and rejects a stale or tampered manifest if they no longer
match.

A manifest is not editable authoring state and does not serialize a
`BiologicalSimulationSpec`, `SimulationSpec`, process graph, recorder state,
renderer object, or runtime object graph. Editing intent creates a new manifest.

## Evidence plan and authoritative validation

Evidence intent remains separate from scientific simulation intent.

WB1 supports the existing concrete evidence streams:

```text
controlled-locomotion.population-focal-trait
    ↓ fresh PopulationRecorder(max_speed)

controlled-locomotion.committed-events
    ↓ fresh EventRecorder
```

Fresh mutable recorder instances are reconstructed for each compile/run and supplied
before lower preflight. Recorder runtime state is never persisted as configuration.
The committed event stream remains authoritative for E1 locomotion measurement.

B3 already owns a richer fixed evidence surface: population, genetic composition,
spatial state, individual focal-trait records, committed events, and pedigree/life-
history evidence. WB2 persists those existing evidence requirements as the curated
B3 evidence plan and executes through the existing B3 runner. It does not invent or
recalculate allele/genotype summaries, founder reproductive contribution, resource-
geography audits, mechanism episodes, representative-run selection, robustness
analysis, or claim boundaries.

Workbench readiness remains small and user-facing. Genetics, biological invariants,
dependency satisfaction, B3 treatment integrity, and executable simulation validity
remain authoritative in their existing lower/scenario-specific layers.

No evidence registry, metric registry, statistics DSL, or generic evidence solver
is introduced.

## Exact save/load and reproduction semantics

WB1 `StudyRevision` is an immutable saved revision containing semantic intent, the
exact resolved manifest, evidence plan, revision/parent identity, and references
tying completed runs to the exact manifest.

WB2 uses a B3-specific `B3StudyRevision` because one additional concrete consumer
did not justify replacing WB1's recipe-specific persisted shape with a universal
study schema. It persists the exact B3 manifest plus scenario origin, validated
scenario identity, parent lineage, evidence intent, and run provenance.

Saved Workbench revisions persist the resolved manifest itself. Loading deserializes
that exact stored manifest; it does **not** re-resolve historical intent with modern
defaults and call the result exact reproduction.

Exact reproduction requires compatible persisted recipe/compiler/software identity.
Compilation reconstructs existing typed/scenario composition from the saved
manifest and checks its stored resolved assumptions against the compatible current
implementation. If compatibility cannot be honored, loading/compilation fails
explicitly.

WB2 specifically persists enough resolved B3 assumptions that canonical B3 does not
silently inherit future `ReferenceEcologyConfig` defaults. The authoritative B3
builder is already fully explicit; Workbench additionally stores the resulting
scientific meaning and verifies it during exact compilation.

Migration or "recompile old authoring intent under current software" remains a
separate future operation. WB1/WB2 do not implement a migration framework, and such
an operation must create a new manifest/revision rather than masquerading as exact
reproduction.

## Scenario identity versus scenario origin

WB2 establishes a distinction required by trusted curated studies:

```text
scenario identity
    = this exact saved revision is the validated frozen B3 scientific scenario

scenario origin
    = this study descends scientifically from B3
```

Canonical B3 persists both:

```text
origin   = confirmed B3 flagship
identity = exact validated radius-1 B3 scenario
```

A supported radius-2 fork persists B3 origin but has no validated B3 scenario
identity. It is a B3-derived custom study, not the exact validated flagship.

Scenario lineage therefore cannot be used as a proxy for validation or claim
status. WB2 does not create generic claim inference or a universal scenario-
certification framework.

## Run provenance

`WorkbenchRunProvenance` adds saved-study identity around existing scientific
provenance/evidence contracts:

```text
run ID
    ↓
saved revision ID
    ↓
SHA-256 digest of the exact resolved manifest
    ↓
requested evidence IDs
    ↓
produced evidence/result references
```

WB1 can additionally carry E1 `ScientificRunProvenance` on locomotion measurements.
WB2 returns existing B3 `B3RunEvidence`, `B3RunSummary`, and
`B3MatchedPairSummary` artifacts while attaching Workbench saved-revision/manifest
provenance around the study execution.

The Workbench does not become the owner of those scientific results. A future
storage layer may provide durable artifact locations without changing the manifest
contract.

## Fork and semantic diff

Forking creates a new immutable saved revision with its parent revision ID. Parent
science and completed-run references are not mutated or silently inherited.

Semantic diff compares stable recipe-owned scientific IDs rather than Python object
graphs. It separates:

```text
explicit authoring changes
        ↓
derived scientific consequences
        ↓
scenario identity change, where relevant
```

WB1 reports controlled-locomotion explicit versus derived changes.

WB2's supported canonical B3 fork reports approximately:

```text
Origin:
    confirmed B3 flagship

Explicit change:
    treatment resource-patch radius 1 → 2

Current study:
    B3-derived custom study

Lost identity:
    exact validated radius-1 B3 scenario

Derived consequences:
    broad geometry becomes primary treatment
    the original representative-story semantics are not inherited
    the original B3 headline claim does not automatically transfer
```

Unchanged frozen scientific slots can also be surfaced to show that mutation,
standing variation, seed roles, counterbalance design, ordinary inheritance, and
other frozen assumptions were not edited.

The diff remains bounded to stable recipe semantics. It is not a generic
configuration-diff or claim-reasoning language.

## Presentation boundary

Workbench scientific manifests stop at scientific study meaning. They do not
contain camera, Manim, Plotly, Streamlit, Blender, CSS, material, timing, easing, or
renderer implementation objects.

The B3 path remains:

```text
B3 scientific evidence/results
        ↓
renderer-neutral B3 scientific meaning
        ↓
interactive or cinematic presentation
```

The representative seed remains authoritative in the existing B3 scientific
handoff. WB2 records that authority/rule boundary but does not hardcode the selected
seed into the curated scientific manifest as Workbench-owned science.

## What WB2 proved

B3 did not require redesigning the central WB1 architecture. It demonstrated that:

1. a rich trusted scenario can remain an explicit bounded recipe rather than
   requiring a generic experiment DSL or registry;
2. exact-reproduction manifests must be rich enough to expose frozen scenario
   assumptions, not merely the small editable intent surface;
3. scenario identity and scenario origin are distinct concepts for curated studies;
4. a scientifically justified fork can preserve origin while losing validated
   scenario identity;
5. semantic diff can remain stable and scientific even for a richer multi-run
   study;
6. existing scenario-specific evidence, analysis, robustness, representative-run,
   and claim contracts can remain authoritative below the Workbench;
7. renderer-neutral scientific persistence can remain clean despite existing
   interactive and cinematic consumers.

The concrete pressure exposed by B3 is persistence shape: WB1's first
`StudyRevision` is intentionally controlled-locomotion-specific, so WB2 uses a
B3-specific saved revision rather than prematurely generalizing the container into
a universal study schema.

WB3 strengthens that conclusion rather than weakening it: its concrete experiment
definitions have a different persistence responsibility from a saved curated
scenario. Repeated needs across future recipes/studies/experiments should determine
what shared root, if any, is actually warranted.

## Settled contracts after WB2

Later Workbench milestones should treat these contracts as settled unless repository
evidence demonstrates a concrete deficiency:

1. Workbench remains above existing preset/domain/scenario builders; it is never
   inserted into the frozen kernel or settled lower composition layers.
2. Scientific persistence uses stable semantic IDs, not Python paths or object
   identity.
3. Editable semantic authoring intent and immutable resolved manifest remain
   distinct.
4. Exact saved-revision reproduction uses the stored resolved manifest; no silent
   re-resolution, default inheritance, or migration occurs.
5. Recipe adapters are bounded and explicit. New breadth must be earned by concrete
   studies rather than reflection, registries, or speculative schemas.
6. Evidence intent is separate from scientific simulation intent and reuses existing
   authoritative evidence/recorders/results.
7. Mutable runtime objects are reconstructed afresh; manifests, evidence plans, and
   saved revisions are immutable values.
8. Workbench readiness remains small and user-facing rather than becoming universal
   validation/diagnostics.
9. Runs carry exact saved-manifest/revision provenance in addition to existing
   scenario/scientific provenance.
10. Forking is immutable and semantic diff reports stable scientific meaning,
    separating explicit changes, derived consequences, and validated scenario
    identity changes where applicable.
11. Scenario origin is not scenario identity. A derived study may retain scientific
    lineage without retaining validation/claim status.
12. Curated studies may expose frozen assumptions without making them generally
    editable.
13. Engine-valid ranges, Workbench-supported ranges, experiment factor levels, and
    curated frozen assumptions remain separate concepts.
14. Scientific manifests remain renderer-neutral.
15. These milestones do not authorize generic simulation configuration, plugin
    systems, capability solvers, arbitrary genetics, migration, generic sensitivity
    analysis, claim inference, universal statistics, or a universal presentation
    specification.

## WB3 controlled experiment authoring

WB3 adds experiment authoring **above** the settled WB1 recipe and existing E3/E4
science. It does not add a universal `Experiment` class, factor registry,
configuration-diff language, or statistics framework.

The common sequencing is:

```text
base semantic study intent / concrete experimental design
        +
concrete experiment pattern
        ↓
stable semantic factor ID
        ↓
treatment expansion
        ↓
concrete treatment-specific manifest/specification
        ↓
experiment-owned integrity validation
        ↓
existing evidence + execution + measurements
```

Expansion happens before each run reaches typed biological compilation. Compiled
Python objects are never patched after the fact.

### E3-style max-speed sweep

`MaxSpeedSweepDefinition` is the concrete one-factor sweep pattern. Its stable
pattern identity is:

```text
controlled-locomotion.max-speed-sweep
```

Its only manipulable factor is:

```text
controlled-locomotion.max-speed
```

The definition owns declared factor levels, unique replicate seeds, run role, and
evidence intent. The base `ControlledLocomotionIntent` must leave both `max_speed`
and `seed` unresolved: experiment expansion supplies the factor level and replicate
seed while keeping the base resource geography fixed.

For every `(level, seed)` pair, WB3 resolves a fresh exact
`ControlledLocomotionManifest` **before execution**. Same-seed manifests are checked
to ensure their explicit semantic difference is exactly the max-speed slot. The
existing E3 `validate_e3_speed_treatment_integrity()` remains the scientific
integrity authority; WB3 does not replace it with a generic diff mechanism.

The sweep requires the existing population focal-trait and committed-event evidence
needed by E3 analysis. Execution delegates to `run_e3_replicate()` and
`summarize_e3_treatment()`, so replicate outcomes, primary cumulative-birth outcome,
mechanism measurements, extinction semantics, and treatment summaries remain the
existing E3 values rather than Workbench-specific reinterpretations.

One run/seed remains one experimental replicate. Organisms are not promoted to
replicate status.

### E4-style matched environment comparison

`EnvironmentSelectionComparisonDefinition` is the concrete standing-variation
comparison pattern. Its stable pattern identity is:

```text
controlled-locomotion.environment-selection-comparison
```

Its only primary factor is:

```text
controlled-locomotion.resource-geography
```

The frozen control/treatment meaning remains:

```text
control:   local_resource
treatment: separated_corridor
```

The full focal standing composition remains exactly `(1, 3, 9)`. WB3 intentionally
does **not** widen the monomorphic WB1 recipe into an arbitrary founder-composition
manifest just to make E4 look like E3. E4 treatment expansion therefore reuses the
existing concrete `E4TreatmentSpecification` and E4 execution path.

Founder-ID counterbalancing is persisted by the stable scheme identity:

```text
e4-founder-id-cyclic-orders-v1
```

For each declared seed index, `founder_order_for_replicate()` supplies the existing
predeclared cyclic speed-to-founder-ID assignment. Matched local/corridor arms use
the same seed and founder order. `founder_speed_order` is exposed as counterbalance
metadata on the expanded treatment; it is not the primary evolutionary factor.

The existing `validate_e4_environment_treatment_integrity()` remains the matched-arm
integrity authority. The Workbench does not introduce an allowed-path diff or
factorial-treatment normalizer.

E4 requires three concrete evidence meanings:

```text
controlled-locomotion.individual-focal-trait
controlled-locomotion.population-focal-trait
controlled-locomotion.committed-events
```

`EvidencePlan` is shared only as the immutable request carrier. Evidence support and
resolution remain pattern-owned. The E4 individual focal-trait requirement is
satisfied through E4's existing `IndividualGeneticTraitRecorder` path; WB3 does not
widen `compile_controlled_locomotion()` to pretend that WB1's monomorphic manifest
can represent E4's polymorphic founders.

Execution delegates to `run_e4_replicate()` and `summarize_e4_environment()`. Full
focal composition, frequency change, strategy-attributed mechanism evidence,
energy audits, and extinction semantics therefore remain authoritative E4 results.
Population mean speed is not substituted for focal composition.

### Experiment-definition persistence

Both WB3 patterns use the versioned experiment-definition envelope:

```text
format ID:      evolution-experiment-workbench-experiment
format version: 1
```

Stored definitions preserve stable pattern/factor identity, factor levels or
control/treatment meaning, ordered unique seeds, evidence intent, run role, and the
E4 counterbalance identity/focal composition needed to preserve scientific meaning.
They do not persist Python field paths as factor identity.

Loading validates the stored pattern/factor/counterbalance identities and rebuilds
the same concrete expansion. No migration or generic experiment language is
introduced.

### What WB3 actually shares

The responsibilities now genuinely shared across the two WB3 patterns are small:

- persisted factor identity uses stable Workbench semantic slot IDs;
- factor/replicate design is expanded before per-run compilation;
- `EvidencePlan` carries immutable requested evidence IDs;
- unique seed values preserve E1's one-run/seed replicate semantics;
- experiment definitions are immutable, canonically versioned persisted values;
- execution returns existing experiment-owned replicate outcomes and summaries.

The following remain deliberately concrete:

- which semantic slot is a scientifically valid factor;
- factor levels and control/treatment interpretation;
- E3 monomorphic base intent and exact WB1 manifests;
- E4 standing focal composition;
- E4 founder-ID counterbalancing;
- treatment-integrity normalization;
- evidence sufficiency and recorder meaning;
- E3/E4 measurement and summary logic.

Two consumers did not earn a generic factor hierarchy, experiment DSL, treatment
normalizer, evidence solver, metric registry, or statistics registry.

### Contract available to later results/presentation work

A later results/presentation milestone may rely on WB2/WB3 to provide:

- scenario origin and validated scenario identity where a curated study has them;
- stable experiment pattern and factor IDs suitable for labels and provenance;
- deterministic expanded treatment order;
- per-treatment seed, factor level, and E4 counterbalance metadata;
- unchanged typed B3/E3/E4 evidence, replicate outcomes, and summaries;
- explicit separation between primary outcome, mechanism evidence, diagnostics,
  replicate-level values, summaries, scenario validation status, and presentation
  meaning.

Later presentation should preserve those scientific distinctions rather than
flattening them into scalar fitness or inventing a generic metric/statistics layer.
