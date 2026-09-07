# Evolution Experiment Workbench Architecture

The Evolution Experiment Workbench is a **scientific-study authoring layer over the
existing engine**. It does not define a second simulation model and it does not sit
between biological composition and the generic kernel.

WB1 establishes the first intentionally narrow vertical using the controlled clonal
locomotion system.

## Dependency direction

The durable dependency direction is:

```text
Workbench scientific study
        ↓
bounded recipe adapter
        ↓
existing preset / experiment composition
        ↓
BiologicalSimulationSpec
        ↓
SimulationSpec
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

Nothing new is introduced between `BiologicalSimulationSpec` and
`SimulationSpec`. Lower engine/domain packages must not import
`evo_engine.workbench`.

## Bounded recipe identity

The first supported recipe has stable scientific identity:

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

These IDs are persisted scientific identity. Python module paths, class names, and
object graphs are not scientific identity.

WB1 directly exposes one bounded adapter. There is no reflection-based discovery,
global recipe registry, generic policy descriptor system, composition graph,
configuration DSL, or capability solver. If later Workbench recipes earn a shared
composition root, that root should list supported recipes explicitly.

## Supported authoring surface

WB1 deliberately supports only the scientific surface already characterized by E3.
Resource geography is one of:

- `local_resource`;
- `separated_corridor`.

The Workbench-supported `max_speed` range is `1..10`, matching E3's characterized
speed grid. The underlying controlled-locomotion preset remains engine/domain-valid
for `0..20`.

Keep these concepts distinct:

```text
engine-valid range
        ≠
Workbench-supported range
        ≠
experiment-declared factor levels
```

The Workbench range is a support/product contract for this recipe version, not a
new biological invariant.

## Explicit intent and resolved manifest

`ControlledLocomotionIntent` persists the human-visible choices that can be edited.
It is an immutable value and may temporarily be incomplete while authoring.

Resolution creates a separate immutable `ControlledLocomotionManifest`. The
manifest stores:

- recipe/compiler identity and versions;
- engine distribution/version compatibility identity;
- normalized explicit semantic slot values;
- recipe-owned scientifically meaningful derived assumptions.

The controlled-locomotion derived assumptions make the fixed composition visible:
one inherited focal `max_speed`, controlled one-locus genetics, clonal inheritance,
mutation off, perfect full-world sensing, nearest-resource targeting, fixed body
mass and nonfocal feeding/reproduction settings, and absence of mate search,
predation, metabolism, growth, aging, and renewable resource generation. Resource
layout is derived through the existing E3 treatment builder rather than copied into
Workbench code.

The manifest is not editable authoring state and does not serialize a
`BiologicalSimulationSpec`, `SimulationSpec`, process graph, or runtime object
graph. Editing intent creates a new resolved manifest.

Compilation verifies that persisted derived values still match the pinned recipe
and compiler semantics. A stale or tampered manifest fails explicitly rather than
silently compiling into different science.

## Evidence plan and authoritative preflight

Evidence intent is persisted separately from simulation intent. WB1 supports the
existing concrete evidence streams:

```text
controlled-locomotion.population-focal-trait
    ↓ fresh PopulationRecorder(max_speed)

controlled-locomotion.committed-events
    ↓ fresh EventRecorder
```

Fresh mutable recorder instances are reconstructed for each compile/run. Recorder
runtime state is never persisted as configuration.

The recorders are supplied to `build_controlled_locomotion_spec()` **before**
`BiologicalSimulationSpec.compile()`. Their requirements therefore participate in
existing biological dependency collection and generic `SimulationSpec` preflight.
Workbench support checks do not replace that authority.

The event stream remains authoritative committed evidence for E1's pure locomotion
measurement. No evidence registry, metric registry, statistics DSL, or generic
evidence solver is introduced.

## Readiness versus validation authority

WB1 has only three user-facing readiness states:

- `draft` — required semantic selections/evidence are incomplete;
- `blocked` — a supplied value or evidence request is outside this recipe's support;
- `ready` — the bounded Workbench surface is complete and supported.

These checks belong to the authoring layer. Genetics, biological invariants,
dependency satisfaction, and executable simulation validity remain lower-layer
responsibilities. Unexpected authoritative lower-layer failures remain
lower-layer failures; Workbench does not parse exception strings into synthetic
diagnostics.

## Exact save/load semantics

`StudyRevision` is an immutable saved revision containing:

- semantic authoring intent;
- the exact resolved manifest;
- evidence plan;
- revision identity and optional parent revision identity;
- references tying completed runs to the revision and exact manifest.

The study file stores the manifest itself. Loading a saved revision deserializes
that stored manifest; it does **not** re-resolve historical intent with current
defaults and call the result exact reproduction.

Manifest compilation also requires compatible recipe/compiler/engine identity.
Migration and upgrading of historical manifests are outside WB1. Unsupported old
formats fail explicitly.

## Run provenance

Workbench run provenance and E1 scientific provenance answer different questions.

`ScientificRunProvenance` identifies the scientific experiment/treatment/seed and
remains the provenance carried by E1 measurements. `WorkbenchRunProvenance` adds
study-authoring identity:

```text
run ID
    ↓
saved StudyRevision ID
    ↓
SHA-256 digest of the exact resolved manifest
    ↓
requested evidence IDs
    ↓
produced evidence/result references
```

This keeps the saved-study origin of a run explicit without changing E1's
scientific replicate semantics.

WB1 keeps produced evidence/results in the returned run value and persists stable
references from the study revision. A future storage layer may provide durable
artifact locations without changing the scientific manifest contract.

## Fork and semantic diff

Forking creates a new immutable `StudyRevision` with `parent_revision_id` pointing
to its parent. The parent is not mutated and completed-run references are not
silently inherited into the child.

Semantic diff compares only the stable recipe-owned scientific IDs. It reports two
sets separately:

```text
explicit authoring changes
        ↓
derived scientific consequences
```

For example, changing `max_speed` from `3` to `4` changes
`controlled-locomotion.max-speed` explicitly and changes the derived initial focal
speed. Fixed clonal inheritance does not appear as a change. Changing resource
geography changes the explicit geography slot and the derived resource-deposit
layout obtained from E3 composition.

This is a bounded recipe diff, not a generic configuration-diff language.

## Settled contracts for WB2/WB3/WB4

Later Workbench milestones should treat the following WB1 contracts as settled
unless repository evidence demonstrates a concrete deficiency:

1. Workbench remains above existing preset/domain builders; it is never inserted
   between `BiologicalSimulationSpec` and `SimulationSpec`.
2. Scientific persistence uses stable semantic IDs, not Python paths.
3. Editable authoring intent and immutable resolved manifest remain distinct.
4. Exact saved-revision reproduction uses the stored manifest; no silent
   re-resolution or migration occurs.
5. Recipe adapters are bounded and explicit. They may own support ranges,
   applicability, visible derivation, and mapping into existing typed builders,
   but lower biological validation remains authoritative.
6. Evidence intent is separate from simulation intent and reconstructs existing
   concrete recorders before authoritative preflight.
7. Runtime recorders are fresh mutable objects; manifests, evidence plans, and
   study revisions are immutable values.
8. Workbench readiness remains small and user-facing rather than becoming a
   universal diagnostics framework.
9. Runs carry exact saved-manifest/revision provenance in addition to existing
   scientific provenance.
10. Forking is immutable and semantic diff reports stable scientific meaning,
    separating explicit changes from derived consequences.
11. Engine-valid ranges, Workbench-supported ranges, and experiment-declared factor
    levels remain separate concepts.
12. New recipe breadth must be earned by concrete studies; WB1 does not authorize
    generic simulation configuration, plugin systems, registries, arbitrary
    genetics, generic experiments, or generic statistics.

## WB3 controlled experiment authoring

WB3 adds experiment authoring **above** the settled WB1 recipe and existing E3/E4
science. It does not add a universal `Experiment` class, a factor registry, a
configuration-diff language, or a statistics framework.

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

Both patterns use the versioned experiment-definition envelope:

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

The responsibilities now genuinely shared across the two implemented patterns are
small:

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

### Contract available to WB5

A later results/presentation milestone may rely on WB3 to provide:

- stable experiment pattern and factor IDs suitable for labels and provenance;
- deterministic expanded treatment order;
- per-treatment seed, factor level, and E4 counterbalance metadata;
- unchanged typed E3/E4 replicate outcomes;
- unchanged typed E3/E4 treatment/environment summaries;
- explicit separation between primary outcome, mechanism evidence, diagnostics,
  replicate-level values, and summaries inherited from E3/E4.

WB5 should present those scientific result distinctions rather than flattening them
into a scalar fitness value or inventing a generic metric/statistics layer.
